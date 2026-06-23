import { useEffect, useState } from "react";
import { api } from "../../api/client";
import { useResource } from "../../hooks/useResource";
import { useAuth } from "../../auth/AuthContext";
import { SubTable } from "../../components/SubTable";

interface FY { id: number; name: string; start_date: string | null; end_date: string | null; status: string; }
interface BItem { id: number; name: string; allocated_amount: number; used: number; description: string | null; }

export default function Budget() {
  const { rows: years, reload: reloadYears } = useResource<FY>("/api/financial/fiscal-years");
  const { can } = useAuth();
  const canEdit = can("financial", "edit") || can("financial", "create");
  const [fyId, setFyId] = useState<number | null>(null);
  const [items, setItems] = useState<BItem[]>([]);

  useEffect(() => { if (fyId == null && years.length) setFyId(years[0].id); }, [years]);
  async function loadItems() {
    if (fyId == null) { setItems([]); return; }
    setItems(await api.get(`/api/financial/budget-items?fiscal_year_id=${fyId}`));
  }
  useEffect(() => { loadItems(); }, [fyId]);

  return (
    <div className="space-y-6">
      <div>
        <SubTable<FY>
          title="السنوات المالية" rows={years} canEdit={canEdit} reload={reloadYears} addLabel="إضافة سنة مالية"
          columns={[
            { key: "name", label: "السنة" },
            { key: "start_date", label: "من", render: (r) => r.start_date || "-" },
            { key: "end_date", label: "إلى", render: (r) => r.end_date || "-" },
            { key: "status", label: "الحالة" },
          ]}
          fields={[
            { name: "name", label: "اسم السنة المالية", required: true },
            { name: "start_date", label: "تاريخ البداية", type: "date", required: true },
            { name: "end_date", label: "تاريخ النهاية", type: "date", required: true },
            { name: "status", label: "الحالة", type: "select", options: [{ value: "active", label: "نشطة" }, { value: "closed", label: "مغلقة" }] },
          ]}
          toForm={(r) => ({ name: r.name, start_date: r.start_date, end_date: r.end_date, status: r.status })}
          onCreate={(p) => api.post("/api/financial/fiscal-years", p)}
          onUpdate={(id, p) => api.put(`/api/financial/fiscal-years/${id}`, p)}
          onDelete={(id) => api.del(`/api/financial/fiscal-years/${id}`)}
        />
      </div>

      <div>
        <div className="mb-3 flex items-center gap-3">
          <span className="text-sm font-medium text-ink-secondary">بنود السنة المالية:</span>
          <select className="input w-auto" value={fyId ?? ""} onChange={(e) => setFyId(Number(e.target.value))}>
            {years.map((y) => <option key={y.id} value={y.id}>{y.name}</option>)}
          </select>
        </div>
        <SubTable<BItem>
          title="بنود الميزانية" rows={items} canEdit={canEdit && fyId != null} reload={loadItems} addLabel="إضافة بند"
          columns={[
            { key: "name", label: "البند" },
            { key: "allocated_amount", label: "المخصص", render: (r) => r.allocated_amount.toLocaleString("ar-EG") },
            { key: "used", label: "المنصرف", render: (r) => r.used.toLocaleString("ar-EG") },
            { key: "description", label: "الوصف", render: (r) => r.description || "-" },
          ]}
          fields={[
            { name: "name", label: "اسم البند", required: true },
            { name: "allocated_amount", label: "المبلغ المخصص", type: "number" },
            { name: "description", label: "الوصف", type: "textarea", colSpan: 2 },
          ]}
          toForm={(r) => ({ name: r.name, allocated_amount: r.allocated_amount, description: r.description })}
          onCreate={(p) => api.post("/api/financial/budget-items", { ...p, fiscal_year_id: fyId, allocated_amount: Number(p.allocated_amount || 0) })}
          onUpdate={(id, p) => api.put(`/api/financial/budget-items/${id}`, { ...p, fiscal_year_id: fyId, allocated_amount: Number(p.allocated_amount || 0) })}
          onDelete={(id) => api.del(`/api/financial/budget-items/${id}`)}
        />
      </div>
    </div>
  );
}
