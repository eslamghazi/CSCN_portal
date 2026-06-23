import { useEffect, useRef, useState } from "react";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { DataTable, Column } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { Field, FieldGrid, FieldDef } from "../components/Form";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ActionButton } from "../components/RowActions";
import { Badge } from "../components/Badge";

interface Doc {
  id: number; title: string; doc_type: string; category_id: number | null;
  category: string | null; current_version: string;
  effective_date: string | null; status: string;
}

const DOC_TYPES = [
  { value: "policy", label: "سياسة" }, { value: "procedure", label: "إجراء" },
  { value: "form", label: "نموذج" }, { value: "manual", label: "دليل" },
];

export default function Documents() {
  const { rows, loading, reload } = useResource<Doc>("/api/documents");
  const { can } = useAuth();
  const toast = useToast();
  const [cats, setCats] = useState<{ value: number; label: string }[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<Doc | null>(null);
  const [form, setForm] = useState<any>({});
  const [file, setFile] = useState<File | null>(null);
  const [delId, setDelId] = useState<number | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { api.get("/api/documents/categories").then(setCats).catch(() => {}); }, []);

  const fields: FieldDef[] = [
    { name: "title", label: "عنوان الوثيقة", required: true, colSpan: 2 },
    { name: "doc_type", label: "النوع", type: "select", options: DOC_TYPES },
    { name: "category_id", label: "التصنيف", type: "select", options: cats },
    { name: "effective_date", label: "تاريخ السريان", type: "date" },
    { name: "status", label: "الحالة", type: "select",
      options: [{ value: "draft", label: "مسودة" }, { value: "approved", label: "معتمد" }] },
  ];

  const columns: Column<Doc>[] = [
    { key: "title", label: "عنوان الوثيقة", sortable: true },
    { key: "doc_type", label: "النوع", render: (r) => DOC_TYPES.find((t) => t.value === r.doc_type)?.label || r.doc_type },
    { key: "category", label: "التصنيف", render: (r) => r.category || "-" },
    { key: "current_version", label: "الإصدار" },
    { key: "effective_date", label: "تاريخ السريان", render: (r) => r.effective_date || "-" },
    { key: "status", label: "الحالة", sortable: true,
      render: (r) => <Badge text={r.status === "approved" ? "معتمد" : "مسودة"} tone={r.status === "approved" ? "success" : "warning"} /> },
  ];

  function openAdd() { setEditing(null); setForm({ doc_type: "policy", status: "draft" }); setFile(null); setOpen(true); }
  function openEdit(d: Doc) {
    setEditing(d);
    setForm({ title: d.title, doc_type: d.doc_type, category_id: d.category_id ?? "",
      effective_date: d.effective_date ?? "", status: d.status });
    setFile(null); setOpen(true);
  }

  async function save() {
    if (!form.title?.trim()) { toast.error("العنوان مطلوب"); return; }
    try {
      if (editing) {
        await api.put(`/api/documents/${editing.id}`, {
          title: form.title, doc_type: form.doc_type || "policy",
          category_id: form.category_id ? Number(form.category_id) : null,
          status: form.status || "draft", effective_date: form.effective_date || null });
      } else {
        if (!file) { toast.error("اختر ملف الوثيقة"); return; }
        await api.upload("/api/documents", file, {
          title: form.title, doc_type: form.doc_type || "policy",
          category_id: form.category_id ? String(form.category_id) : "",
          status: form.status || "draft", effective_date: form.effective_date || "" });
      }
      setOpen(false); toast.success(editing ? "تم التعديل" : "تم رفع الوثيقة"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }
  async function approve(d: Doc) {
    try { await api.post(`/api/documents/${d.id}/approve`); toast.success("تم الاعتماد"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الاعتماد"); }
  }
  async function download(d: Doc) {
    try { await api.download(`/api/documents/${d.id}/download`); }
    catch { toast.error("لا يوجد ملف مرفق"); }
  }
  async function doDelete() {
    if (delId == null) return;
    try { await api.del(`/api/documents/${delId}`); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDelId(null); }
  }

  return (
    <div>
      <PageHeader title="نظام الوثائق" subtitle="رفع واعتماد السياسات والإجراءات والنماذج." />
      <DataTable
        columns={columns} rows={rows} loading={loading}
        getSearchText={(r) => `${r.title} ${r.doc_type} ${r.category || ""}`}
        filters={[{ key: "status", label: "الحالة", options: [{ value: "approved", label: "معتمد" }, { value: "draft", label: "مسودة" }] }]}
        getFilterValue={(r, k) => (k === "status" ? r.status : "")}
        onAdd={can("documents", "create") ? openAdd : undefined} addLabel="رفع وثيقة"
        onRefresh={reload} onExport={(f) => api.download(`/api/documents/export?fmt=${f}`)}
        rowActions={(r) => (
          <>
            <ActionButton icon="download" title="تنزيل" onClick={() => download(r)} />
            {can("documents", "edit") && r.status !== "approved" &&
              <ActionButton icon="check" title="اعتماد" variant="primary" onClick={() => approve(r)} />}
            {can("documents", "edit") && <ActionButton icon="edit" title="تعديل" variant="primary" onClick={() => openEdit(r)} />}
            {can("documents", "delete") && <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDelId(r.id)} />}
          </>
        )}
      />
      <Modal open={open} title={editing ? "تعديل وثيقة" : "رفع وثيقة جديدة"} onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button>
          <button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>
          {fields.map((f) => (
            <Field key={f.name} field={f} value={form[f.name]} onChange={(n, v) => setForm((s: any) => ({ ...s, [n]: v }))} />
          ))}
        </FieldGrid>
        {!editing && (
          <div className="mt-4">
            <label className="label">ملف الوثيقة <span className="text-danger">*</span></label>
            <input ref={fileRef} type="file" className="input" onChange={(e) => setFile(e.target.files?.[0] || null)} />
          </div>
        )}
      </Modal>
      <ConfirmDialog open={delId != null} message="هل تريد حذف هذه الوثيقة؟"
        onConfirm={doDelete} onCancel={() => setDelId(null)} />
    </div>
  );
}
