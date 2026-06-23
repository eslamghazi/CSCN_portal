import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { Tabs } from "../components/Tabs";
import { DataTable, Column } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { Field, FieldGrid, FieldDef } from "../components/Form";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ActionButton } from "../components/RowActions";
import { Badge } from "../components/Badge";

interface User { id: number; username: string; full_name: string; email: string | null; phone: string | null; role_id: number | null; role_name: string | null; is_active: boolean; }

function UsersTab() {
  const { rows, loading, reload } = useResource<User>("/api/admin/users");
  const { user: me } = useAuth();
  const toast = useToast();
  const [roles, setRoles] = useState<{ value: number; label: string }[]>([]);
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<User | null>(null);
  const [form, setForm] = useState<any>({});
  const [delId, setDelId] = useState<number | null>(null);

  useEffect(() => { api.get("/api/admin/roles").then(setRoles).catch(() => {}); }, []);

  const fields: FieldDef[] = [
    { name: "full_name", label: "الاسم بالكامل", required: true },
    { name: "username", label: "اسم المستخدم", required: true },
    { name: "role_id", label: "الصلاحية", type: "select", options: roles },
    { name: "phone", label: "الهاتف", type: "tel" },
    { name: "email", label: "البريد", type: "email" },
    { name: "password", label: editing ? "كلمة مرور جديدة (اختياري)" : "كلمة المرور", type: "password", required: !editing },
    ...(editing ? [{ name: "is_active", label: "الحالة", type: "select" as const,
      options: [{ value: "1", label: "نشط" }, { value: "0", label: "موقوف" }] }] : []),
  ];
  const columns: Column<User>[] = [
    { key: "full_name", label: "الاسم", sortable: true },
    { key: "username", label: "اسم المستخدم", sortable: true },
    { key: "role_name", label: "الصلاحية", render: (r) => r.role_name || "-" },
    { key: "is_active", label: "الحالة", render: (r) => <Badge text={r.is_active ? "نشط" : "موقوف"} tone={r.is_active ? "success" : "danger"} /> },
  ];

  function openAdd() { setEditing(null); setForm({}); setOpen(true); }
  function openEdit(u: User) { setEditing(u); setForm({ ...u, role_id: u.role_id ?? "", is_active: u.is_active ? "1" : "0", password: "" }); setOpen(true); }
  async function save() {
    if (!form.username?.trim() || !form.full_name?.trim()) { toast.error("الاسم واسم المستخدم مطلوبان"); return; }
    const payload: any = { username: form.username, full_name: form.full_name, email: form.email || null,
      phone: form.phone || null, role_id: form.role_id ? Number(form.role_id) : null };
    try {
      if (editing) {
        payload.is_active = form.is_active === "1";
        if (form.password) payload.password = form.password;
        await api.put(`/api/admin/users/${editing.id}`, payload);
      } else {
        if (!form.password) { toast.error("كلمة المرور مطلوبة"); return; }
        payload.password = form.password;
        await api.post("/api/admin/users", payload);
      }
      setOpen(false); toast.success(editing ? "تم التعديل" : "تمت الإضافة"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }
  async function doDelete() {
    if (delId == null) return;
    try { await api.del(`/api/admin/users/${delId}`); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDelId(null); }
  }

  return (
    <div>
      <DataTable columns={columns} rows={rows} loading={loading}
        getSearchText={(r) => `${r.full_name} ${r.username} ${r.role_name || ""}`}
        onAdd={openAdd} addLabel="إضافة مستخدم" onRefresh={reload}
        rowActions={(r) => (
          <>
            <ActionButton icon="edit" title="تعديل" variant="primary" onClick={() => openEdit(r)} />
            {r.id !== me?.id && <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDelId(r.id)} />}
          </>
        )} />
      <Modal open={open} title={editing ? "تعديل مستخدم" : "إضافة مستخدم"} onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button><button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>{fields.map((f) => <Field key={f.name} field={f} value={form[f.name]} onChange={(n, v) => setForm((s: any) => ({ ...s, [n]: v }))} />)}</FieldGrid>
      </Modal>
      <ConfirmDialog open={delId != null} message="هل تريد حذف هذا المستخدم؟" onConfirm={doDelete} onCancel={() => setDelId(null)} />
    </div>
  );
}

function AuditTab() {
  const { rows, loading, reload } = useResource<any>("/api/admin/audit");
  const columns: Column<any>[] = [
    { key: "timestamp", label: "التاريخ والوقت", sortable: true },
    { key: "username", label: "المستخدم", sortable: true },
    { key: "module", label: "الوحدة" },
    { key: "action", label: "الإجراء" },
    { key: "entity_type", label: "الكيان" },
  ];
  return (
    <DataTable columns={columns} rows={rows} loading={loading}
      getSearchText={(r) => `${r.username} ${r.module} ${r.action} ${r.entity_type}`}
      onRefresh={reload} onExport={(f) => api.download(`/api/admin/audit/export?fmt=${f}`)} pageSize={15} />
  );
}

function LogsTab() {
  const [files, setFiles] = useState<{ label: string; path: string }[]>([]);
  const [sel, setSel] = useState("");
  const [content, setContent] = useState("");

  useEffect(() => { api.get("/api/admin/logs/files").then((f) => { setFiles(f); if (f[0]) setSel(f[0].path); }).catch(() => {}); }, []);
  useEffect(() => {
    const url = sel ? `/api/admin/logs/content?path=${encodeURIComponent(sel)}` : "/api/admin/logs/content";
    api.get(url).then((d) => setContent(d.content)).catch(() => setContent(""));
  }, [sel]);

  return (
    <div>
      <div className="mb-3 flex items-center gap-2">
        <select className="input w-auto" value={sel} onChange={(e) => setSel(e.target.value)}>
          {files.map((f) => <option key={f.path} value={f.path}>{f.label}</option>)}
        </select>
        <button className="btn-secondary" onClick={() => api.download(`/api/admin/logs/export?fmt=excel&path=${encodeURIComponent(sel)}`)}>تصدير Excel</button>
        <button className="btn-secondary" onClick={() => api.download(`/api/admin/logs/export?fmt=pdf&path=${encodeURIComponent(sel)}`)}>تصدير PDF</button>
      </div>
      <pre dir="ltr" className="h-[60vh] overflow-auto rounded-lg bg-[#0b1220] p-4 text-xs leading-5 text-emerald-200">{content || "لا يوجد محتوى"}</pre>
    </div>
  );
}

export default function Admin() {
  return (
    <div>
      <PageHeader title="إدارة النظام" subtitle="المستخدمون وسجل العمليات والسجل الكامل." />
      <div className="card p-5">
        <Tabs tabs={[
          { key: "users", label: "المستخدمون", content: <UsersTab /> },
          { key: "audit", label: "سجل العمليات", content: <AuditTab /> },
          { key: "logs", label: "السجل الكامل", content: <LogsTab /> },
        ]} />
      </div>
    </div>
  );
}
