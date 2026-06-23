import { useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { DataTable, Column } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { Field, FieldGrid, FieldDef } from "../components/Form";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Badge } from "../components/Badge";
import { ActionButton } from "../components/RowActions";

interface Emp {
  id: number; full_name: string; email: string | null; phone: string | null;
  position_id: number | null; position: string | null; hire_date: string | null; status: string;
}

const BASE = "/api/hr/employees";

export default function Hr() {
  const { rows, loading, reload } = useResource<Emp>(BASE);
  const { can } = useAuth();
  const toast = useToast();
  const nav = useNavigate();
  const [positions, setPositions] = useState<{ value: number; label: string }[]>([]);
  const [editing, setEditing] = useState<Emp | null>(null);
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<any>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [delId, setDelId] = useState<number | null>(null);

  useEffect(() => { api.get("/api/hr/positions").then(setPositions).catch(() => {}); }, []);

  const fields: FieldDef[] = useMemo(() => [
    { name: "full_name", label: "الاسم بالكامل", required: true, colSpan: 2 },
    { name: "position_id", label: "المنصب", type: "select", options: positions },
    { name: "phone", label: "رقم الهاتف", type: "tel" },
    { name: "email", label: "البريد الإلكتروني", type: "email" },
    { name: "hire_date", label: "تاريخ التعيين", type: "date" },
    { name: "status", label: "الحالة", type: "select",
      options: [{ value: "active", label: "نشط" }, { value: "inactive", label: "غير نشط" }] },
  ], [positions]);

  const columns: Column<Emp>[] = [
    { key: "id", label: "الرقم", sortable: true },
    { key: "full_name", label: "الاسم بالكامل", sortable: true },
    { key: "position", label: "المنصب", sortable: true, render: (r) => r.position || "-" },
    { key: "phone", label: "رقم الهاتف", render: (r) => r.phone || "-" },
    { key: "status", label: "الحالة", sortable: true,
      render: (r) => <Badge text={r.status === "active" ? "نشط" : "غير نشط"} tone={r.status === "active" ? "success" : "muted"} /> },
  ];

  function openAdd() {
    setEditing(null); setForm({ status: "active" }); setErrors({}); setOpen(true);
  }
  function openEdit(e: Emp) {
    setEditing(e);
    setForm({ full_name: e.full_name, position_id: e.position_id ?? "", phone: e.phone ?? "",
      email: e.email ?? "", hire_date: e.hire_date ?? "", status: e.status });
    setErrors({}); setOpen(true);
  }
  function setField(name: string, value: any) { setForm((f: any) => ({ ...f, [name]: value })); }

  async function save() {
    if (!form.full_name?.trim()) { setErrors({ full_name: "الاسم مطلوب" }); return; }
    const payload = { ...form, position_id: form.position_id ? Number(form.position_id) : null };
    try {
      if (editing) await api.put(`${BASE}/${editing.id}`, payload);
      else await api.post(BASE, payload);
      setOpen(false); toast.success(editing ? "تم التعديل بنجاح" : "تمت الإضافة بنجاح"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }

  async function doDelete() {
    if (delId == null) return;
    try { await api.del(`${BASE}/${delId}`); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDelId(null); }
  }

  async function onExport(fmt: "excel" | "pdf") {
    try { await api.download(`${BASE}/export?fmt=${fmt}`); } catch { toast.error("تعذّر التصدير"); }
  }
  async function onTemplate() {
    try { await api.download(`${BASE}/template`); } catch { toast.error("تعذّر تنزيل القالب"); }
  }
  async function onImport(file: File) {
    try { const r = await api.upload(`${BASE}/import`, file); toast.success(`تم استيراد ${r.imported} موظف`); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الاستيراد"); }
  }

  return (
    <div>
      <PageHeader title="شؤون العاملين" subtitle="إدارة بيانات الموظفين والمؤهلات والخبرات والتقييمات." />
      <DataTable
        columns={columns}
        rows={rows}
        loading={loading}
        getSearchText={(r) => `${r.id} ${r.full_name} ${r.position || ""} ${r.phone || ""}`}
        filters={[{ key: "status", label: "الحالة", options: [{ value: "active", label: "نشط" }, { value: "inactive", label: "غير نشط" }] }]}
        getFilterValue={(r, k) => (k === "status" ? r.status : "")}
        onAdd={can("hr", "create") ? openAdd : undefined}
        addLabel="إضافة موظف"
        onRefresh={reload}
        onExport={onExport}
        onImport={can("hr", "create") ? onImport : undefined}
        onTemplate={can("hr", "create") ? onTemplate : undefined}
        rowActions={(r) => (
          <>
            <ActionButton icon="list" title="الملف" onClick={() => nav(`/hr/${r.id}`)} />
            {can("hr", "edit") && <ActionButton icon="edit" title="تعديل" variant="primary" onClick={() => openEdit(r)} />}
            {can("hr", "delete") && <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDelId(r.id)} />}
          </>
        )}
      />

      <Modal open={open} title={editing ? "تعديل موظف" : "إضافة موظف"} onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button>
          <button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>
          {fields.map((f) => (
            <Field key={f.name} field={f} value={form[f.name]} error={errors[f.name]} onChange={setField} />
          ))}
        </FieldGrid>
      </Modal>

      <ConfirmDialog open={delId != null} message="هل تريد حذف هذا الموظف؟"
        onConfirm={doDelete} onCancel={() => setDelId(null)} />
    </div>
  );
}
