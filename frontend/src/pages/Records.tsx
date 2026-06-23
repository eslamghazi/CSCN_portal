import { useEffect, useState } from "react";
import { api } from "../api/client";
import { CrudPage } from "../components/CrudPage";
import { Column } from "../components/DataTable";
import { FieldDef } from "../components/Form";
import { Badge } from "../components/Badge";

interface Rec {
  id: number; record_number: string; title: string; record_type_id: number | null;
  record_type: string | null; storage_location: string | null;
  retention_period_months: number | null; disposal_method: string | null; status: string; notes: string | null;
}

export default function Records() {
  const [types, setTypes] = useState<{ value: number; label: string }[]>([]);
  useEffect(() => { api.get("/api/records/types").then(setTypes).catch(() => {}); }, []);

  const columns: Column<Rec>[] = [
    { key: "record_number", label: "رقم السجل", sortable: true },
    { key: "title", label: "عنوان السجل", sortable: true },
    { key: "record_type", label: "النوع", sortable: true, render: (r) => r.record_type || "-" },
    { key: "storage_location", label: "مكان الحفظ", render: (r) => r.storage_location || "-" },
    { key: "status", label: "الحالة", sortable: true,
      render: (r) => <Badge text={r.status === "active" ? "نشط" : "مؤرشف"} tone={r.status === "active" ? "success" : "muted"} /> },
  ];

  const fields: FieldDef[] = [
    { name: "record_number", label: "رقم السجل", required: true },
    { name: "title", label: "عنوان السجل", required: true },
    { name: "record_type_id", label: "النوع", type: "select", options: types },
    { name: "storage_location", label: "مكان الحفظ" },
    { name: "retention_period_months", label: "مدة الحفظ (شهور)", type: "number" },
    { name: "disposal_method", label: "طريقة التخلص" },
    { name: "status", label: "الحالة", type: "select",
      options: [{ value: "active", label: "نشط" }, { value: "archived", label: "مؤرشف" }] },
    { name: "notes", label: "ملاحظات", type: "textarea", colSpan: 2 },
  ];

  return (
    <CrudPage<Rec>
      title="السجلات والمحفوظات"
      subtitle="إدارة السجلات ومدد الحفظ وطرق التخلص."
      module="records"
      endpoint="/api/records"
      columns={columns}
      fields={fields}
      defaults={{ status: "active" }}
      addLabel="إضافة سجل"
      getSearchText={(r) => `${r.record_number} ${r.title} ${r.record_type || ""}`}
      filters={[{ key: "status", label: "الحالة", options: [{ value: "active", label: "نشط" }, { value: "archived", label: "مؤرشف" }] }]}
      getFilterValue={(r, k) => (k === "status" ? r.status : "")}
      toForm={(r) => ({ ...r, record_type_id: r.record_type_id ?? "" })}
      buildPayload={(f) => ({ ...f, record_type_id: f.record_type_id ? Number(f.record_type_id) : null,
        retention_period_months: f.retention_period_months ? Number(f.retention_period_months) : null })}
      hasExport
    />
  );
}
