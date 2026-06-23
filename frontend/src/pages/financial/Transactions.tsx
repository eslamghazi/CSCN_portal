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
import { Badge } from "../../components/Badge";

interface Txn { id: number; transaction_type: string; type_label: string; amount: number; date: string | null; category: string | null; description: string; }

function money(n: number) { return new Intl.NumberFormat("ar-EG", { maximumFractionDigits: 2 }).format(n) + " ج.م"; }

export default function Transactions() {
  const { rows, loading, reload } = useResource<Txn>("/api/financial/transactions");
  const { can } = useAuth();
  const toast = useToast();
  const [summary, setSummary] = useState({ total_revenue: 0, total_expense: 0, balance: 0 });
  const [open, setOpen] = useState(false);
  const [form, setForm] = useState<any>({});
  const [del, setDel] = useState<Txn | null>(null);

  async function loadSummary() { try { setSummary(await api.get("/api/financial/summary")); } catch {} }
  useEffect(() => { loadSummary(); }, [rows]);

  const fields: FieldDef[] = [
    { name: "transaction_type", label: "النوع", type: "select", required: true,
      options: [{ value: "revenue", label: "إيراد" }, { value: "expense", label: "مصروف" }] },
    { name: "amount", label: "المبلغ", type: "number", required: true },
    { name: "date", label: "التاريخ", type: "date", required: true },
    { name: "category", label: "التصنيف / المصدر" },
    { name: "description", label: "البيان", type: "textarea", colSpan: 2, required: true },
  ];
  const columns: Column<Txn>[] = [
    { key: "date", label: "التاريخ", sortable: true, render: (r) => r.date || "-" },
    { key: "type_label", label: "النوع", render: (r) => <Badge text={r.type_label} tone={r.transaction_type === "revenue" ? "success" : "danger"} /> },
    { key: "amount", label: "المبلغ", sortable: true, render: (r) => money(r.amount) },
    { key: "category", label: "التصنيف", render: (r) => r.category || "-" },
    { key: "description", label: "البيان" },
  ];

  function openAdd() { setForm({ transaction_type: "revenue", date: new Date().toISOString().slice(0, 10) }); setOpen(true); }
  async function save() {
    if (!form.amount || !form.description?.trim()) { toast.error("المبلغ والبيان مطلوبان"); return; }
    try {
      await api.post("/api/financial/transactions", {
        transaction_type: form.transaction_type, amount: Number(form.amount),
        date: form.date, description: form.description,
        source: form.category || null, category: form.category || null });
      setOpen(false); toast.success("تمت إضافة المعاملة"); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
  }
  async function doDelete() {
    if (!del) return;
    try { await api.del(`/api/financial/transactions/${del.transaction_type}/${del.id}`); toast.success("تم الحذف"); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الحذف"); }
    finally { setDel(null); }
  }

  return (
    <div>
      <div className="mb-5 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div className="card border-r-4 border-success p-4"><p className="text-sm text-ink-secondary">إجمالي الإيرادات</p><p className="text-xl font-extrabold text-success">{money(summary.total_revenue)}</p></div>
        <div className="card border-r-4 border-danger p-4"><p className="text-sm text-ink-secondary">إجمالي المصروفات</p><p className="text-xl font-extrabold text-danger">{money(summary.total_expense)}</p></div>
        <div className="card border-r-4 border-primary p-4"><p className="text-sm text-ink-secondary">الرصيد الحالي</p><p className="text-xl font-extrabold text-primary">{money(summary.balance)}</p></div>
      </div>
      <DataTable
        columns={columns} rows={rows} loading={loading}
        getSearchText={(r) => `${r.description} ${r.category || ""} ${r.type_label}`}
        filters={[{ key: "type", label: "النوع", options: [{ value: "revenue", label: "إيراد" }, { value: "expense", label: "مصروف" }] }]}
        getFilterValue={(r, k) => (k === "type" ? r.transaction_type : "")}
        onAdd={can("financial", "create") ? openAdd : undefined} addLabel="إضافة معاملة"
        onRefresh={reload} onExport={(f) => api.download(`/api/financial/transactions/export?fmt=${f}`)}
        rowActions={can("financial", "delete") ? (r) => (
          <ActionButton icon="delete" title="حذف" variant="danger" onClick={() => setDel(r)} />
        ) : undefined}
      />
      <Modal open={open} title="إضافة معاملة مالية" onClose={() => setOpen(false)}
        footer={<><button className="btn-primary" onClick={save}>حفظ</button><button className="btn-secondary" onClick={() => setOpen(false)}>إلغاء</button></>}>
        <FieldGrid>{fields.map((f) => <Field key={f.name} field={f} value={form[f.name]} onChange={(n, v) => setForm((s: any) => ({ ...s, [n]: v }))} />)}</FieldGrid>
      </Modal>
      <ConfirmDialog open={del != null} message="هل تريد حذف هذه المعاملة؟" onConfirm={doDelete} onCancel={() => setDel(null)} />
    </div>
  );
}
