import { ReactNode, useEffect, useState } from "react";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "./Toast";
import { PageHeader } from "./PageHeader";
import { DataTable, Column, FilterDef } from "./DataTable";
import { Modal } from "./Modal";
import { Field, FieldGrid, FieldDef } from "./Form";
import { ConfirmDialog } from "./ConfirmDialog";
import { ActionButton } from "./RowActions";

interface CrudPageProps<T extends { id: number }> {
  title: string;
  subtitle?: string;
  module: string;
  endpoint: string;                 // base path, e.g. /api/records
  columns: Column<T>[];
  fields: FieldDef[];
  getSearchText?: (row: T) => string;
  filters?: FilterDef[];
  getFilterValue?: (row: T, key: string) => string;
  toForm?: (row: T) => any;
  buildPayload?: (form: any) => any;
  defaults?: any;
  addLabel?: string;
  deleteMessage?: string;
  hasExport?: boolean;
  hasImport?: boolean;
  hasTemplate?: boolean;
  extraRowActions?: (row: T) => ReactNode;
  importLabel?: string;
}

export function CrudPage<T extends { id: number }>(props: CrudPageProps<T>) {
  const {
    title, subtitle, module, endpoint, columns, fields, getSearchText, filters, getFilterValue,
    toForm, buildPayload, defaults = {}, addLabel = "إضافة", deleteMessage = "هل تريد حذف هذا العنصر؟",
    hasExport, hasImport, hasTemplate, extraRowActions,
  } = props;
  const { rows, loading, reload } = useResource<T>(endpoint);
  const { can } = useAuth();
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<T | null>(null);
  const [form, setForm] = useState<any>({});
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [delId, setDelId] = useState<number | null>(null);

  function openAdd() { setEditing(null); setForm({ ...defaults }); setErrors({}); setOpen(true); }
  function openEdit(r: T) { setEditing(r); setForm(toForm ? toForm(r) : { ...r }); setErrors({}); setOpen(true); }

  async function save() {
    const req = fields.filter((f) => f.required && !String(form[f.name] ?? "").trim());
    if (req.length) { setErrors(Object.fromEntries(req.map((f) => [f.name, "مطلوب"]))); return; }
    const payload = buildPayload ? buildPayload(form) : form;
    try {
      if (editing) await api.put(`${endpoint}/${editing.id}`, payload);
      else await api.post(endpoint, payload);
      setOpen(false); toast.success(editing ? "تم التعديل بنجاح" : "تمت الإضافة بنجاح"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }
  async function doDelete() {
    if (delId == null) return;
    try { await api.del(`${endpoint}/${delId}`); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDelId(null); }
  }
  async function onExport(fmt: "excel" | "pdf") {
    try { await api.download(`${endpoint}/export?fmt=${fmt}`); } catch { toast.error("تعذّر التصدير"); }
  }
  async function onTemplate() {
    try { await api.download(`${endpoint}/template`); } catch { toast.error("تعذّر تنزيل القالب"); }
  }
  async function onImport(file: File) {
    try { const r = await api.upload(`${endpoint}/import`, file); toast.success(`تم استيراد ${r.imported}`); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الاستيراد"); }
  }

  return (
    <div>
      <PageHeader title={title} subtitle={subtitle} />
      <DataTable
        columns={columns} rows={rows} loading={loading}
        getSearchText={getSearchText} filters={filters} getFilterValue={getFilterValue}
        onAdd={can(module, "create") ? openAdd : undefined} addLabel={addLabel}
        onRefresh={reload}
        onExport={hasExport ? onExport : undefined}
        onImport={hasImport && can(module, "create") ? onImport : undefined}
        onTemplate={hasTemplate && can(module, "create") ? onTemplate : undefined}
        rowActions={(r) => (
          <>
            {extraRowActions?.(r)}
            {can(module, "edit") && <ActionButton icon="edit" title="تعديل" variant="primary" onClick={() => openEdit(r)} />}
            {can(module, "delete") && <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDelId(r.id)} />}
          </>
        )}
      />
      <Modal open={open} title={editing ? `تعديل - ${title}` : `${addLabel}`} onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button>
          <button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>
          {fields.map((f) => (
            <Field key={f.name} field={f} value={form[f.name]} error={errors[f.name]}
              onChange={(n, v) => setForm((s: any) => ({ ...s, [n]: v }))} />
          ))}
        </FieldGrid>
      </Modal>
      <ConfirmDialog open={delId != null} message={deleteMessage}
        onConfirm={doDelete} onCancel={() => setDelId(null)} />
    </div>
  );
}
