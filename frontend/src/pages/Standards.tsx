import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CrudPage } from "../components/CrudPage";
import { Column } from "../components/DataTable";
import { FieldDef } from "../components/Form";
import { Badge } from "../components/Badge";
import { Modal } from "../components/Modal";
import { SubTable } from "../components/SubTable";
import { ActionButton } from "../components/RowActions";
import { useAuth } from "../auth/AuthContext";

interface Std {
  id: number; code: string; name: string; description: string | null;
  category_id: number | null; category: string | null; status: string; compliance: number | null;
}
interface Ind { id: number; code: string; name: string; description: string | null; weight: number | null; status: string; sort_order: number; }

function IndicatorsModal({ standard, onClose }: { standard: Std; onClose: () => void }) {
  const { can } = useAuth();
  const [rows, setRows] = useState<Ind[]>([]);
  async function load() { setRows(await api.get(`/api/standards/${standard.id}/indicators`)); }
  useEffect(() => { load(); }, [standard.id]);
  return (
    <Modal open title={`مؤشرات المعيار: ${standard.name}`} onClose={onClose} width="max-w-3xl">
      <SubTable<Ind>
        title="" rows={rows} canEdit={can("quality", "edit")} reload={load} addLabel="إضافة مؤشر"
        columns={[
          { key: "code", label: "الكود" },
          { key: "name", label: "المؤشر" },
          { key: "weight", label: "الوزن", render: (r) => r.weight ?? "-" },
          { key: "status", label: "الحالة" },
        ]}
        fields={[
          { name: "code", label: "الكود", required: true },
          { name: "name", label: "المؤشر", required: true },
          { name: "weight", label: "الوزن", type: "number" },
          { name: "status", label: "الحالة", type: "select",
            options: [{ value: "active", label: "نشط" }, { value: "compliant", label: "مطابق" }, { value: "non_compliant", label: "غير مطابق" }] },
          { name: "description", label: "الوصف", type: "textarea", colSpan: 2 },
        ]}
        toForm={(r) => ({ code: r.code, name: r.name, weight: r.weight ?? "", status: r.status })}
        onCreate={(p) => api.post(`/api/standards/${standard.id}/indicators`, normW(p))}
        onUpdate={(id, p) => api.put(`/api/standards/indicators/${id}`, normW(p))}
        onDelete={(id) => api.del(`/api/standards/indicators/${id}`)}
      />
    </Modal>
  );
}
function normW(p: any) { return { ...p, weight: p.weight !== "" && p.weight != null ? Number(p.weight) : null, status: p.status || "active" }; }

export default function Standards() {
  const [cats, setCats] = useState<{ value: number; label: string }[]>([]);
  const [indStd, setIndStd] = useState<Std | null>(null);
  useEffect(() => { api.get("/api/standards/categories").then(setCats).catch(() => {}); }, []);

  const columns: Column<Std>[] = [
    { key: "code", label: "الكود", sortable: true },
    { key: "name", label: "اسم المعيار", sortable: true },
    { key: "category", label: "التصنيف", render: (r) => r.category || "-" },
    { key: "status", label: "الحالة", sortable: true,
      render: (r) => <Badge text={r.status === "active" ? "نشط" : "غير نشط"} tone={r.status === "active" ? "success" : "muted"} /> },
    { key: "compliance", label: "نسبة الإنجاز", sortable: true,
      render: (r) => (
        <div className="flex items-center gap-2">
          <div className="h-2 w-24 overflow-hidden rounded bg-surface-sunken">
            <div className="h-full bg-primary" style={{ width: `${r.compliance ?? 0}%` }} />
          </div>
          <span className="text-xs text-ink-secondary">{r.compliance ?? 0}%</span>
        </div>
      ) },
  ];
  const fields: FieldDef[] = [
    { name: "code", label: "الكود", required: true },
    { name: "name", label: "اسم المعيار", required: true },
    { name: "category_id", label: "التصنيف", type: "select", options: cats },
    { name: "status", label: "الحالة", type: "select",
      options: [{ value: "active", label: "نشط" }, { value: "inactive", label: "غير نشط" }] },
    { name: "description", label: "الوصف", type: "textarea", colSpan: 2 },
  ];

  return (
    <>
      <CrudPage<Std>
        title="إدارة معايير الجودة" subtitle="المعايير ومؤشرات المطابقة ونِسب الإنجاز."
        module="quality" endpoint="/api/standards" columns={columns} fields={fields}
        defaults={{ status: "active" }} addLabel="إضافة معيار"
        getSearchText={(r) => `${r.code} ${r.name} ${r.category || ""}`}
        filters={[{ key: "status", label: "الحالة", options: [{ value: "active", label: "نشط" }, { value: "inactive", label: "غير نشط" }] }]}
        getFilterValue={(r, k) => (k === "status" ? r.status : "")}
        toForm={(r) => ({ code: r.code, name: r.name, category_id: r.category_id ?? "", status: r.status, description: r.description ?? "" })}
        buildPayload={(f) => ({ ...f, category_id: f.category_id ? Number(f.category_id) : null })}
        hasExport
        extraRowActions={(r) => <ActionButton icon="list" title="المؤشرات" onClick={() => setIndStd(r)} />}
      />
      {indStd && <IndicatorsModal standard={indStd} onClose={() => setIndStd(null)} />}
    </>
  );
}
