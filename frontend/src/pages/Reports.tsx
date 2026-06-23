import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { Icon } from "../components/icons";

interface Report { key: string; label: string; }

export default function Reports() {
  const toast = useToast();
  const [reports, setReports] = useState<Report[]>([]);
  const [sel, setSel] = useState("");
  const [fmt, setFmt] = useState("excel");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/api/reports").then((r) => { setReports(r); if (r[0]) setSel(r[0].key); }).catch(() => {});
  }, []);

  async function generate() {
    if (!sel) return;
    setBusy(true);
    try { await api.download(`/api/reports/${sel}?fmt=${fmt}`); toast.success("تم توليد التقرير"); }
    catch (e: any) { toast.error(e?.detail || "تعذّر توليد التقرير"); }
    finally { setBusy(false); }
  }

  return (
    <div>
      <PageHeader title="التقارير والإحصائيات" subtitle="اختر التقرير والصيغة ثم نزّله." />
      <div className="card max-w-2xl p-6">
        <label className="label">التقرير</label>
        <select className="input mb-4" value={sel} onChange={(e) => setSel(e.target.value)}>
          {reports.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}
        </select>
        <label className="label">الصيغة</label>
        <select className="input mb-6" value={fmt} onChange={(e) => setFmt(e.target.value)}>
          <option value="excel">Excel (.xlsx)</option>
          <option value="pdf">PDF (.pdf)</option>
        </select>
        <button className="btn-primary" onClick={generate} disabled={busy || !sel}>
          <Icon name="download" size={16} /> {busy ? "جاري التوليد..." : "توليد وتنزيل"}
        </button>
      </div>
    </div>
  );
}
