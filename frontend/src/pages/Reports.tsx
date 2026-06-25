import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { Icon } from "../components/icons";

interface Report { key: string; label: string; }
interface ReportData { title: string; headers: string[]; rows: any[][]; count: number; }

export default function Reports() {
  const toast = useToast();
  const [reports, setReports] = useState<Report[]>([]);
  const [sel, setSel] = useState("");
  const [data, setData] = useState<ReportData | null>(null);
  const [loading, setLoading] = useState(false);
  const [exporting, setExporting] = useState("");

  useEffect(() => {
    api.get("/api/reports").then((r) => { setReports(r); if (r[0]) setSel(r[0].key); }).catch(() => {});
  }, []);

  // Load the preview whenever the selected report changes.
  useEffect(() => {
    if (!sel) { setData(null); return; }
    setLoading(true);
    api.get(`/api/reports/${sel}/data`)
      .then(setData)
      .catch((e) => { toast.error(e?.detail || "تعذّر تحميل التقرير"); setData(null); })
      .finally(() => setLoading(false));
  }, [sel]);

  async function exportAs(fmt: "excel" | "pdf") {
    if (!sel) return;
    setExporting(fmt);
    try { await api.download(`/api/reports/${sel}?fmt=${fmt}`); }
    catch (e: any) { toast.error(e?.detail || "تعذّر تصدير التقرير"); }
    finally { setExporting(""); }
  }

  return (
    <div>
      <PageHeader title="التقارير والإحصائيات"
        subtitle="اختر التقرير لعرض بياناته، ثم صدّره إن رغبت (Excel أو PDF)." />

      {/* Controls */}
      <div className="card mb-5 flex flex-wrap items-end gap-3 p-4">
        <div className="min-w-[260px] flex-1">
          <label className="label">التقرير</label>
          <select className="input" value={sel} onChange={(e) => setSel(e.target.value)}>
            {reports.map((r) => <option key={r.key} value={r.key}>{r.label}</option>)}
          </select>
        </div>
        <button className="btn-secondary" onClick={() => exportAs("excel")} disabled={!data || !!exporting}>
          <Icon name="download" size={16} /> {exporting === "excel" ? "..." : "حفظ باسم Excel"}
        </button>
        <button className="btn-secondary" onClick={() => exportAs("pdf")} disabled={!data || !!exporting}>
          <Icon name="download" size={16} /> {exporting === "pdf" ? "..." : "حفظ باسم PDF"}
        </button>
      </div>

      {/* Preview */}
      <div className="card overflow-hidden">
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          <h3 className="font-bold text-ink">{data?.title || "معاينة التقرير"}</h3>
          {data && <span className="text-sm text-ink-secondary">{data.count} سجل</span>}
        </div>
        {loading ? (
          <div className="p-12 text-center text-ink-muted">جاري التحميل...</div>
        ) : !data || data.rows.length === 0 ? (
          <div className="p-12 text-center text-ink-muted">لا توجد بيانات لعرضها</div>
        ) : (
          <div className="max-h-[60vh] overflow-auto">
            <table className="w-full text-right text-sm">
              <thead className="sticky top-0 bg-surface-alt">
                <tr className="border-b border-border text-ink-secondary">
                  {data.headers.map((h, i) => (
                    <th key={i} className="whitespace-nowrap px-4 py-3 font-semibold">{h}</th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {data.rows.map((row, ri) => (
                  <tr key={ri} className="border-b border-border last:border-0 hover:bg-surface-alt/60">
                    {row.map((cell, ci) => (
                      <td key={ci} className="px-4 py-2.5">{cell === null || cell === "" ? "-" : String(cell)}</td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
