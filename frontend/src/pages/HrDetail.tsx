import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { PageHeader } from "../components/PageHeader";
import { Tabs } from "../components/Tabs";
import { SubTable } from "../components/SubTable";
import { Icon } from "../components/icons";

export default function HrDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { can } = useAuth();
  const canEdit = can("hr", "edit");
  const [data, setData] = useState<any>(null);

  const load = useCallback(async () => {
    try { setData(await api.get(`/api/hr/employees/${id}`)); } catch { setData(null); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  if (!data) return <div className="card flex h-64 items-center justify-center text-ink-muted">جاري التحميل...</div>;
  const emp = data.employee;

  return (
    <div>
      <PageHeader title={emp.full_name} subtitle={emp.position || "بدون منصب"}
        actions={<button className="btn-secondary" onClick={() => nav("/hr")}><Icon name="list" size={16} /> رجوع</button>} />

      <div className="mb-5 card p-5">
        <Tabs tabs={[
          {
            key: "quals", label: "المؤهلات العلمية",
            content: <SubTable
              title="المؤهلات" rows={data.qualifications} canEdit={canEdit} reload={load}
              columns={[
                { key: "degree", label: "المؤهل" },
                { key: "institution", label: "الجهة" },
                { key: "year_obtained", label: "سنة الحصول" },
              ]}
              fields={[
                { name: "degree", label: "المؤهل", required: true },
                { name: "institution", label: "الجهة", required: true },
                { name: "year_obtained", label: "سنة الحصول", type: "number" },
              ]}
              toForm={(r) => ({ degree: r.degree, institution: r.institution, year_obtained: r.year_obtained })}
              onCreate={(p) => api.post(`/api/hr/employees/${id}/qualifications`, normYear(p))}
              onUpdate={(qid, p) => api.put(`/api/hr/qualifications/${qid}`, normYear(p))}
              onDelete={(qid) => api.del(`/api/hr/qualifications/${qid}`)}
            />,
          },
          {
            key: "exp", label: "الخبرات",
            content: <SubTable
              title="الخبرات" rows={data.experience} canEdit={canEdit} reload={load}
              columns={[
                { key: "job_title", label: "المسمى الوظيفي" },
                { key: "company", label: "جهة العمل" },
                { key: "start_date", label: "من" },
                { key: "end_date", label: "إلى" },
              ]}
              fields={[
                { name: "job_title", label: "المسمى الوظيفي", required: true },
                { name: "company", label: "جهة العمل", required: true },
                { name: "start_date", label: "من", type: "date" },
                { name: "end_date", label: "إلى", type: "date" },
                { name: "description", label: "الوصف", type: "textarea", colSpan: 2 },
              ]}
              toForm={(r) => ({ ...r })}
              onCreate={(p) => api.post(`/api/hr/employees/${id}/experience`, p)}
              onUpdate={(xid, p) => api.put(`/api/hr/experience/${xid}`, p)}
              onDelete={(xid) => api.del(`/api/hr/experience/${xid}`)}
            />,
          },
          {
            key: "eval", label: "التقييمات",
            content: <SubTable
              title="التقييمات" rows={data.evaluations} canEdit={canEdit} reload={load}
              columns={[
                { key: "evaluation_date", label: "تاريخ التقييم" },
                { key: "score", label: "الدرجة" },
                { key: "notes", label: "ملاحظات" },
              ]}
              fields={[
                { name: "evaluation_date", label: "تاريخ التقييم", type: "date", required: true },
                { name: "score", label: "الدرجة", type: "number" },
                { name: "notes", label: "ملاحظات", type: "textarea", colSpan: 2 },
              ]}
              toForm={(r) => ({ ...r })}
              onCreate={(p) => api.post(`/api/hr/employees/${id}/evaluations`, normScore(p))}
              onUpdate={(vid, p) => api.put(`/api/hr/evaluations/${vid}`, normScore(p))}
              onDelete={(vid) => api.del(`/api/hr/evaluations/${vid}`)}
            />,
          },
        ]} />
      </div>
    </div>
  );
}

function normYear(p: any) { return { ...p, year_obtained: p.year_obtained ? Number(p.year_obtained) : null }; }
function normScore(p: any) { return { ...p, score: p.score !== "" && p.score != null ? Number(p.score) : null }; }
