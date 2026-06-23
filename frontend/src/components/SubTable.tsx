import { useState } from "react";
import { DataTable, Column } from "./DataTable";
import { Modal } from "./Modal";
import { Field, FieldGrid, FieldDef } from "./Form";
import { ConfirmDialog } from "./ConfirmDialog";
import { ActionButton } from "./RowActions";
import { useToast } from "./Toast";

interface SubTableProps<T extends { id: number }> {
  title: string;
  columns: Column<T>[];
  rows: T[];
  fields: FieldDef[];
  canEdit: boolean;
  toForm: (row: T) => any;
  onCreate: (payload: any) => Promise<void>;
  onUpdate: (id: number, payload: any) => Promise<void>;
  onDelete: (id: number) => Promise<void>;
  reload: () => void;
  addLabel?: string;
  hideEdit?: boolean;
}

export function SubTable<T extends { id: number }>(props: SubTableProps<T>) {
  const { title, columns, rows, fields, canEdit, toForm, onCreate, onUpdate, onDelete, reload, addLabel = "إضافة", hideEdit } = props;
  const toast = useToast();
  const [open, setOpen] = useState(false);
  const [editing, setEditing] = useState<T | null>(null);
  const [form, setForm] = useState<any>({});
  const [delId, setDelId] = useState<number | null>(null);

  function add() { setEditing(null); setForm({}); setOpen(true); }
  function edit(r: T) { setEditing(r); setForm(toForm(r)); setOpen(true); }

  async function save() {
    try {
      if (editing) await onUpdate(editing.id, form);
      else await onCreate(form);
      setOpen(false); toast.success(editing ? "تم التعديل" : "تمت الإضافة"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }
  async function remove() {
    if (delId == null) return;
    try { await onDelete(delId); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDelId(null); }
  }

  return (
    <div>
      <div className="mb-3 flex items-center justify-between">
        <h3 className="font-bold text-ink">{title}</h3>
        {canEdit && <button className="btn-primary" onClick={add}>{addLabel}</button>}
      </div>
      <DataTable
        columns={columns}
        rows={rows}
        rowActions={canEdit ? (r) => (
          <>
            {!hideEdit && <ActionButton icon="edit" title="تعديل" variant="primary" onClick={() => edit(r)} />}
            <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDelId(r.id)} />
          </>
        ) : undefined}
        pageSize={6}
      />
      <Modal open={open} title={editing ? `تعديل - ${title}` : `إضافة - ${title}`} onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button>
          <button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>
          {fields.map((f) => (
            <Field key={f.name} field={f} value={form[f.name]} onChange={(n, v) => setForm((s: any) => ({ ...s, [n]: v }))} />
          ))}
        </FieldGrid>
      </Modal>
      <ConfirmDialog open={delId != null} message="هل تريد حذف هذا العنصر؟"
        onConfirm={remove} onCancel={() => setDelId(null)} />
    </div>
  );
}
