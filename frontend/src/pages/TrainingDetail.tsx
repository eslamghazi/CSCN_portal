import { useCallback, useEffect, useState } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { useResource } from "../hooks/useResource";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { Tabs } from "../components/Tabs";
import { SubTable } from "../components/SubTable";
import { DataTable } from "../components/DataTable";
import { Modal } from "../components/Modal";
import { Field, FieldGrid } from "../components/Form";
import { Icon } from "../components/icons";

interface Trainee { id: number; full_name: string; organization: string | null; phone: string | null; email: string | null; }

function TraineesTab() {
  const { rows, reload } = useResource<Trainee>("/api/training/trainees");
  const { can } = useAuth();
  const toast = useToast();
  const [bulkOpen, setBulkOpen] = useState(false);
  const [bulk, setBulk] = useState<any>({ prefix: "طالب", count: 10, start: 1 });

  async function doBulk() {
    if (!bulk.count || Number(bulk.count) <= 0) { toast.error("أدخل عدداً صحيحاً"); return; }
    try {
      const r = await api.post("/api/training/trainees/bulk", {
        prefix: bulk.prefix || "طالب", count: Number(bulk.count), start: Number(bulk.start || 1),
        organization: bulk.organization || null, fee: bulk.fee ? Number(bulk.fee) : null });
      toast.success(`تمت إضافة ${r.created} متدرب${r.revenue ? ` وتسجيل إيراد ${r.revenue}` : ""}`);
      setBulkOpen(false); reload();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الإضافة"); }
  }
  async function onImport(file: File) {
    try { const r = await api.upload("/api/training/trainees/import", file); toast.success(`تم استيراد ${r.imported}`); reload(); }
    catch (e: any) { toast.error(e?.detail || "تعذّر الاستيراد"); }
  }

  return (
    <div>
      {can("training", "create") && (
        <div className="mb-3 flex justify-end gap-2">
          <button className="btn-secondary" onClick={() => setBulkOpen(true)}><Icon name="add" size={16} /> إضافة مجموعة</button>
        </div>
      )}
      <SubTable<Trainee>
        title="" rows={rows} canEdit={false} reload={reload}
        columns={[
          { key: "id", label: "الرقم" },
          { key: "full_name", label: "الاسم" },
          { key: "organization", label: "الجهة", render: (r) => r.organization || "-" },
          { key: "phone", label: "الهاتف", render: (r) => r.phone || "-" },
        ]}
        fields={[]} toForm={() => ({})}
        onCreate={() => Promise.resolve()} onUpdate={() => Promise.resolve()} onDelete={() => Promise.resolve()}
      />
      <div className="mt-2 flex gap-2">
        {can("training", "create") && <>
          <button className="btn-secondary" onClick={() => api.download("/api/training/trainees/template")}><Icon name="download" size={16} /> قالب</button>
          <label className="btn-secondary cursor-pointer">
            <Icon name="upload" size={16} /> استيراد
            <input type="file" accept=".xlsx" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) onImport(f); e.currentTarget.value = ""; }} />
          </label>
        </>}
      </div>

      <Modal open={bulkOpen} title="إضافة مجموعة متدربين" onClose={() => setBulkOpen(false)}
        footer={<><button className="btn-primary" onClick={doBulk}>إضافة</button><button className="btn-secondary" onClick={() => setBulkOpen(false)}>إلغاء</button></>}>
        <FieldGrid>
          <Field field={{ name: "prefix", label: "بادئة الاسم (مثال: طالب)" }} value={bulk.prefix} onChange={(n, v) => setBulk((s: any) => ({ ...s, [n]: v }))} />
          <Field field={{ name: "count", label: "العدد", type: "number", required: true }} value={bulk.count} onChange={(n, v) => setBulk((s: any) => ({ ...s, [n]: v }))} />
          <Field field={{ name: "start", label: "يبدأ الترقيم من", type: "number" }} value={bulk.start} onChange={(n, v) => setBulk((s: any) => ({ ...s, [n]: v }))} />
          <Field field={{ name: "organization", label: "الجهة" }} value={bulk.organization} onChange={(n, v) => setBulk((s: any) => ({ ...s, [n]: v }))} />
          <Field field={{ name: "fee", label: "رسوم الاشتراك للفرد (تُسجّل كإيراد)", type: "number", colSpan: 2 }} value={bulk.fee} onChange={(n, v) => setBulk((s: any) => ({ ...s, [n]: v }))} />
        </FieldGrid>
      </Modal>
    </div>
  );
}

export default function TrainingDetail() {
  const { id } = useParams();
  const nav = useNavigate();
  const { can } = useAuth();
  const canEdit = can("training", "edit");
  const [data, setData] = useState<any>(null);

  const load = useCallback(async () => {
    try { setData(await api.get(`/api/training/programs/${id}/detail`)); } catch { setData(null); }
  }, [id]);
  useEffect(() => { load(); }, [load]);

  if (!data) return <div className="card flex h-64 items-center justify-center text-ink-muted">جاري التحميل...</div>;

  return (
    <div>
      <PageHeader title={data.program.name} subtitle="الدورات والورش والجلسات والمتدربين"
        actions={<button className="btn-secondary" onClick={() => nav("/training")}><Icon name="list" size={16} /> رجوع</button>} />
      <div className="card p-5">
        <Tabs tabs={[
          { key: "courses", label: "الدورات", content: (
            <SubTable title="" rows={data.courses} canEdit={canEdit} reload={load} hideEdit addLabel="إضافة دورة"
              columns={[{ key: "name", label: "اسم الدورة" }, { key: "description", label: "الوصف", render: (r: any) => r.description || "-" }]}
              fields={[{ name: "name", label: "اسم الدورة", required: true }, { name: "description", label: "الوصف", type: "textarea", colSpan: 2 }]}
              toForm={(r: any) => ({ ...r })}
              onCreate={(p) => api.post(`/api/training/programs/${id}/courses`, p)} onUpdate={() => Promise.resolve()}
              onDelete={(cid) => api.del(`/api/training/courses/${cid}`)} />
          ) },
          { key: "workshops", label: "الورش", content: (
            <SubTable title="" rows={data.workshops} canEdit={canEdit} reload={load} hideEdit addLabel="إضافة ورشة"
              columns={[{ key: "name", label: "اسم الورشة" }, { key: "description", label: "الوصف", render: (r: any) => r.description || "-" }]}
              fields={[{ name: "name", label: "اسم الورشة", required: true }, { name: "description", label: "الوصف", type: "textarea", colSpan: 2 }]}
              toForm={(r: any) => ({ ...r })}
              onCreate={(p) => api.post(`/api/training/programs/${id}/workshops`, p)} onUpdate={() => Promise.resolve()}
              onDelete={(wid) => api.del(`/api/training/workshops/${wid}`)} />
          ) },
          { key: "sessions", label: "الجلسات", content: (
            <SubTable title="" rows={data.sessions} canEdit={canEdit} reload={load} addLabel="إضافة جلسة"
              columns={[
                { key: "session_date", label: "التاريخ", render: (r: any) => r.session_date || "-" },
                { key: "duration_hours", label: "المدة (ساعات)" },
                { key: "topic", label: "الموضوع", render: (r: any) => r.topic || "-" },
              ]}
              fields={[
                { name: "session_date", label: "التاريخ", type: "date", required: true },
                { name: "duration_hours", label: "المدة بالساعات", type: "number" },
                { name: "topic", label: "الموضوع", colSpan: 2 },
              ]}
              toForm={(r: any) => ({ session_date: r.session_date, duration_hours: r.duration_hours, topic: r.topic })}
              onCreate={(p) => api.post(`/api/training/programs/${id}/sessions`, { ...p, duration_hours: Number(p.duration_hours || 1) })}
              onUpdate={(sid, p) => api.put(`/api/training/sessions/${sid}`, { ...p, duration_hours: Number(p.duration_hours || 1) })}
              onDelete={(sid) => api.del(`/api/training/sessions/${sid}`)} />
          ) },
          { key: "trainees", label: "المتدربون", content: <TraineesTab /> },
        ]} />
      </div>
    </div>
  );
}
