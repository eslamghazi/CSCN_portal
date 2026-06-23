import { useNavigate } from "react-router-dom";
import { CrudPage } from "../components/CrudPage";
import { Column } from "../components/DataTable";
import { FieldDef } from "../components/Form";
import { Badge } from "../components/Badge";
import { ActionButton } from "../components/RowActions";

interface Prog {
  id: number; name: string; description: string | null; program_type: string;
  start_date: string | null; end_date: string | null; total_hours: number | null; status: string;
}

const TYPES = [{ value: "training", label: "تدريب" }, { value: "workshop", label: "ورشة" }, { value: "course", label: "دورة" }];
const STATUSES = [
  { value: "planned", label: "مخطط" }, { value: "active", label: "نشط" },
  { value: "completed", label: "مكتمل" }, { value: "cancelled", label: "ملغى" },
];
const statusTone: Record<string, any> = { planned: "info", active: "success", completed: "muted", cancelled: "danger" };

export default function Training() {
  const nav = useNavigate();
  const columns: Column<Prog>[] = [
    { key: "name", label: "اسم البرنامج", sortable: true },
    { key: "program_type", label: "النوع", render: (r) => TYPES.find((t) => t.value === r.program_type)?.label || r.program_type },
    { key: "total_hours", label: "الساعات", render: (r) => r.total_hours ?? "-" },
    { key: "status", label: "الحالة", sortable: true,
      render: (r) => <Badge text={STATUSES.find((s) => s.value === r.status)?.label || r.status} tone={statusTone[r.status] || "muted"} /> },
  ];
  const fields: FieldDef[] = [
    { name: "name", label: "اسم البرنامج", required: true, colSpan: 2 },
    { name: "program_type", label: "النوع", type: "select", options: TYPES },
    { name: "status", label: "الحالة", type: "select", options: STATUSES },
    { name: "start_date", label: "تاريخ البداية", type: "date" },
    { name: "end_date", label: "تاريخ النهاية", type: "date" },
    { name: "total_hours", label: "إجمالي الساعات", type: "number" },
    { name: "description", label: "الوصف", type: "textarea", colSpan: 2 },
  ];
  return (
    <CrudPage<Prog>
      title="البرامج التدريبية" subtitle="الدورات والورش والبرامج التدريبية وجلساتها ومتدربيها."
      module="training" endpoint="/api/training/programs" columns={columns} fields={fields}
      defaults={{ program_type: "training", status: "active" }} addLabel="إضافة برنامج"
      getSearchText={(r) => `${r.name} ${r.program_type}`}
      filters={[{ key: "status", label: "الحالة", options: STATUSES }]}
      getFilterValue={(r, k) => (k === "status" ? r.status : "")}
      toForm={(r) => ({ name: r.name, program_type: r.program_type, status: r.status,
        start_date: r.start_date ?? "", end_date: r.end_date ?? "", total_hours: r.total_hours ?? "", description: r.description ?? "" })}
      buildPayload={(f) => ({ ...f, total_hours: f.total_hours ? Number(f.total_hours) : null })}
      hasExport
      extraRowActions={(r) => <ActionButton icon="list" title="التفاصيل" onClick={() => nav(`/training/${r.id}`)} />}
    />
  );
}
