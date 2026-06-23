import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useResource } from "../../hooks/useResource";
import { useAuth } from "../../auth/AuthContext";
import { useToast } from "../../components/Toast";
import { DataTable, Column } from "../../components/DataTable";
import { Modal } from "../../components/Modal";
import { Field, FieldGrid, FieldDef } from "../../components/Form";
import { ConfirmDialog } from "../../components/ConfirmDialog";
import { ActionButton } from "../../components/RowActions";
import { SubTable } from "../../components/SubTable";

interface Partner { id: number; name: string; contact_person: string | null; email: string | null; phone: string | null; address: string | null; }
interface Agr { id: number; title: string; agreement_type: string; start_date: string | null; end_date: string | null; status: string; }

function AgreementsModal({ partner, onClose }: { partner: Partner; onClose: () => void }) {
  const { can } = useAuth();
  const [rows, setRows] = useState<Agr[]>([]);
  async function load() { setRows(await api.get(`/api/partnerships/${partner.id}/agreements`)); }
  useEffect(() => { load(); }, [partner.id]);
  return (
    <Modal open title={`اتفاقيات: ${partner.name}`} onClose={onClose} width="max-w-3xl">
      <SubTable<Agr>
        title="" rows={rows} canEdit={can("partnership", "edit")} reload={load} addLabel="إضافة اتفاقية" hideEdit
        columns={[
          { key: "title", label: "العنوان" },
          { key: "agreement_type", label: "النوع" },
          { key: "start_date", label: "من", render: (r) => r.start_date || "-" },
          { key: "end_date", label: "إلى", render: (r) => r.end_date || "-" },
        ]}
        fields={[
          { name: "title", label: "عنوان الاتفاقية", required: true },
          { name: "agreement_type", label: "النوع", type: "select", options: [{ value: "agreement", label: "اتفاقية" }, { value: "protocol", label: "بروتوكول" }, { value: "mou", label: "مذكرة تفاهم" }] },
          { name: "start_date", label: "تاريخ البداية", type: "date" },
          { name: "end_date", label: "تاريخ النهاية", type: "date" },
        ]}
        toForm={(r) => ({ ...r })}
        onCreate={(p) => api.post(`/api/partnerships/${partner.id}/agreements`, p)}
        onUpdate={() => Promise.resolve()}
        onDelete={(id) => api.del(`/api/partnerships/agreements/${id}`)}
      />
    </Modal>
  );
}

export default function Partnerships() {
  const { rows, loading, reload } = useResource<Partner>("/api/partnerships");
  const { can } = useAuth();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Partner | null>(null);
  const [form, setForm] = useState<any>({});
  const [delId, setDelId] = useState<number | null>(null);
  const [agrPartner, setAgrPartner] = useState<Partner | null>(null);

  const fields: FieldDef[] = [
    { name: "name", label: "اسم الجهة", required: true, colSpan: 2 },
    { name: "contact_person", label: "مسؤول التواصل" },
    { name: "phone", label: "رقم الهاتف", type: "tel" },
    { name: "email", label: "البريد الإلكتروني", type: "email" },
    { name: "address", label: "العنوان", colSpan: 2 },
  ];
  const columns: Column<Partner>[] = [
    { key: "name", label: "اسم الجهة", sortable: true },
    { key: "contact_person", label: "مسؤول التواصل", render: (r) => r.contact_person || "-" },
    { key: "email", label: "البريد", render: (r) => r.email || "-" },
    { key: "phone", label: "الهاتف", render: (r) => r.phone || "-" },
  ];

  function openAdd() { setEditing(null); setForm({}); setOpen(true); }
  function openEdit(p: Partner) { setEditing(p); setForm({ ...p }); setOpen(true); }
  async function save() {
    if (!form.name?.trim()) { toast.error("اسم الجهة مطلوب"); return; }
    try {
      if (editing) await api.put(`/api/partnerships/${editing.id}`, form);
      else await api.post("/api/partnerships", form);
      setOpen(false); toast.success(editing ? "تم التعديل" : "تمت الإضافة"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }
  async function doDelete() {
    if (delId == null) return;
    try { await api.del(`/api/partnerships/${delId}`); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDelId(null); }
  }

  return (
    <div>
      <DataTable
        columns={columns} rows={rows} loading={loading}
        getSearchText={(r) => `${r.name} ${r.contact_person || ""} ${r.email || ""}`}
        onAdd={can("partnership", "create") ? openAdd : undefined} addLabel="إضافة شريك"
        onRefresh={reload} onExport={(f) => api.download(`/api/partnerships/export?fmt=${f}`)}
        onImport={can("partnership", "create") ? async (file) => { try { const r = await api.upload("/api/partnerships/import", file); toast.success(`تم استيراد ${r.imported}`); reload(); } catch (e: any) { toast.error(e?.detail || "تعذّر الاستيراد"); } } : undefined}
        onTemplate={can("partnership", "create") ? () => api.download("/api/partnerships/template") : undefined}
        rowActions={(r) => (
          <>
            <ActionButton icon="list" title="الاتفاقيات" onClick={() => setAgrPartner(r)} />
            {can("partnership", "edit") && <ActionButton icon="edit" title="تعديل" variant="primary" onClick={() => openEdit(r)} />}
            {can("partnership", "delete") && <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDelId(r.id)} />}
          </>
        )}
      />
      <Modal open={open} title={editing ? "تعديل شريك" : "إضافة شريك"} onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button><button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>{fields.map((f) => <Field key={f.name} field={f} value={form[f.name]} onChange={(n, v) => setForm((s: any) => ({ ...s, [n]: v }))} />)}</FieldGrid>
      </Modal>
      <ConfirmDialog open={delId != null} message="هل تريد حذف هذا الشريك؟" onConfirm={doDelete} onCancel={() => setDelId(null)} />
      {agrPartner && <AgreementsModal partner={agrPartner} onClose={() => setAgrPartner(null)} />}
    </div>
  );
}
