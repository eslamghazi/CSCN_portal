import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../auth/AuthContext";
import { PageHeader } from "../components/PageHeader";
import { Tabs } from "../components/Tabs";
import { SubTable } from "../components/SubTable";

interface Item { id: number; name: string; description: string; }

const KINDS = [
  { key: "standard-categories", label: "تصنيفات المعايير" },
  { key: "document-categories", label: "تصنيفات الوثائق" },
  { key: "record-types", label: "أنواع السجلات" },
  { key: "positions", label: "المناصب الوظيفية" },
];

function LookupSection({ kind }: { kind: string }) {
  const { rows, reload } = useResource<Item>(`/api/lookups/${kind}`);
  const { can } = useAuth();
  // Lookups are admin/superadmin only; the page is already role-gated, so allow edit.
  return (
    <SubTable<Item>
      title="" rows={rows} canEdit reload={reload}
      addLabel="إضافة عنصر"
      columns={[
        { key: "name", label: "الاسم", sortable: true },
        { key: "description", label: "الوصف", render: (r) => r.description || "-" },
      ]}
      fields={[
        { name: "name", label: "الاسم", required: true },
        { name: "description", label: "الوصف", type: "textarea", colSpan: 2 },
      ]}
      toForm={(r) => ({ name: r.name, description: r.description })}
      onCreate={(p) => api.post(`/api/lookups/${kind}`, p)}
      onUpdate={(id, p) => api.put(`/api/lookups/${kind}/${id}`, p)}
      onDelete={(id) => api.del(`/api/lookups/${kind}/${id}`)}
    />
  );
}

export default function Lookups() {
  return (
    <div>
      <PageHeader title="البيانات المرجعية"
        subtitle="إدارة القوائم المنسدلة: تصنيفات المعايير والوثائق وأنواع السجلات والمناصب." />
      <div className="card p-5">
        <Tabs tabs={KINDS.map((k) => ({ key: k.key, label: k.label, content: <LookupSection kind={k.key} /> }))} />
      </div>
    </div>
  );
}
