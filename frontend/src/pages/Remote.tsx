import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { Tabs } from "../components/Tabs";
import { DataTable, Column } from "../components/DataTable";
import { Icon } from "../components/icons";

function ServerTab() {
  const toast = useToast();
  const [info, setInfo] = useState<any>(null);
  useEffect(() => { api.get("/api/remote/server-info").then(setInfo).catch(() => {}); }, []);
  if (!info) return <div className="text-ink-muted">جاري التحميل...</div>;

  const primaryUrl = (info.web_urls && info.web_urls[0]) || `http://${info.primary_ip}:${info.web_port}/`;
  const conn = `IP: ${info.primary_ip} | المنفذ: ${info.peer_port} | الرمز: ${info.token}`;
  async function firewall() {
    try { const r = await api.post("/api/remote/firewall"); r.success ? toast.success(r.message) : toast.error(r.message); }
    catch { toast.error("تعذّر طلب فتح المنفذ"); }
  }
  return (
    <div className="max-w-2xl space-y-5">
      {/* Browser access for other PCs on the LAN */}
      <div>
        <p className="mb-2 text-sm font-semibold text-ink">الدخول من أجهزة أخرى على الشبكة (عبر المتصفح):</p>
        <p className="mb-2 text-sm text-ink-secondary">افتح أحد العناوين التالية من متصفح أي جهاز على نفس الشبكة:</p>
        <div className="space-y-2">
          {(info.web_urls || [primaryUrl]).map((u: string) => (
            <div key={u} className="flex items-center justify-between rounded-lg border border-primary/30 bg-primary-soft px-4 py-2.5">
              <span dir="ltr" className="font-mono text-sm font-semibold text-primary">{u}</span>
              <button className="icon-btn h-8 w-8" title="نسخ"
                onClick={() => { navigator.clipboard.writeText(u); toast.success("تم النسخ"); }}>
                <Icon name="documents" size={15} />
              </button>
            </div>
          ))}
        </div>
        {info.is_windows && (
          <button className="btn-secondary mt-3" onClick={firewall}>
            <Icon name="admin" size={16} /> السماح عبر جدار الحماية (لتمكين الوصول من الشبكة)
          </button>
        )}
        <p className="mt-2 text-xs text-ink-muted">
          ملاحظة: يجب أن يكون الجهاز الآخر على نفس الشبكة المحلية، وأن يكون جدار الحماية يسمح بالمنفذ {info.web_port}.
        </p>
      </div>

      {/* Peer data-sync info */}
      <div className="border-t border-border pt-4">
        <p className="mb-2 text-sm font-semibold text-ink">بيانات مزامنة البيانات (للإدارة عن بُعد):</p>
        <div className="rounded-lg border border-border bg-surface-alt p-4 text-sm">
          <div className="mb-1"><span className="text-ink-muted">عنوان IP:</span> <span dir="ltr">{info.primary_ip}</span></div>
          {info.ips.length > 1 && <div className="mb-1 text-xs text-ink-muted">عناوين أخرى: <span dir="ltr">{info.ips.slice(1).join(", ")}</span></div>}
          <div className="mb-1"><span className="text-ink-muted">منفذ المزامنة:</span> <span dir="ltr">{info.peer_port}</span></div>
          <div><span className="text-ink-muted">رمز الوصول:</span> <span dir="ltr">{info.token}</span></div>
        </div>
        <button className="btn-secondary mt-2" onClick={() => { navigator.clipboard.writeText(conn); toast.success("تم النسخ"); }}>
          <Icon name="documents" size={16} /> نسخ بيانات المزامنة
        </button>
      </div>
    </div>
  );
}

function ClientTab() {
  const toast = useToast();
  const [host, setHost] = useState("");
  const [port, setPort] = useState(50525);
  const [token, setToken] = useState("");
  const [status, setStatus] = useState("");
  const [logs, setLogs] = useState<any[]>([]);

  async function ping() {
    setStatus("...جاري الاتصال");
    try { const r = await api.post("/api/remote/ping", { host, port, token }); setStatus(r.connected ? `متصل ✓ (${r.info?.app || ""})` : `غير متصل ✗`); }
    catch { setStatus("غير متصل ✗"); }
  }
  async function fetchLogs() {
    try { const r = await api.post("/api/remote/logs", { host, port, token }); setLogs(r.logs); toast.success(`تم جلب ${r.logs.length} سجل`); }
    catch (e: any) { toast.error(e?.detail || "تعذّر جلب السجلات"); }
  }
  async function download() {
    try { await api.download("/api/remote/download"); } catch (e: any) { toast.error("تعذّر التنزيل — استخدم زر جلب السجلات أولاً للتأكد من الاتصال"); }
  }

  const columns: Column<any>[] = [
    { key: "timestamp", label: "التاريخ" }, { key: "user", label: "المستخدم" },
    { key: "module", label: "الوحدة" }, { key: "action", label: "الإجراء" }, { key: "entity", label: "الكيان" },
  ];

  return (
    <div>
      <div className="mb-4 grid max-w-2xl grid-cols-1 gap-3 sm:grid-cols-3">
        <div><label className="label">عنوان IP</label><input className="input" dir="ltr" value={host} onChange={(e) => setHost(e.target.value)} placeholder="10.0.0.5" /></div>
        <div><label className="label">المنفذ</label><input className="input" dir="ltr" type="number" value={port} onChange={(e) => setPort(Number(e.target.value))} /></div>
        <div><label className="label">رمز الوصول</label><input className="input" dir="ltr" value={token} onChange={(e) => setToken(e.target.value)} placeholder="cscn-internal" /></div>
      </div>
      <div className="mb-2 flex flex-wrap gap-2">
        <button className="btn-primary" onClick={ping}><Icon name="remote" size={16} /> اختبار الاتصال</button>
        <button className="btn-secondary" onClick={fetchLogs}><Icon name="list" size={16} /> عرض السجلات</button>
        <button className="btn-secondary" onClick={download}><Icon name="download" size={16} /> تنزيل كل البيانات</button>
        {status && <span className="self-center text-sm font-medium">{status}</span>}
      </div>
      {logs.length > 0 && <DataTable columns={columns} rows={logs.map((l, i) => ({ id: i, ...l }))} pageSize={10} />}
    </div>
  );
}

export default function Remote() {
  return (
    <div>
      <PageHeader title="البوابات والإدارة عن بُعد" subtitle="مشاركة بيانات هذا الجهاز أو الاتصال بجهاز آخر على الشبكة." />
      <div className="card p-5">
        <Tabs tabs={[
          { key: "server", label: "هذا الجهاز (مصدر البيانات)", content: <ServerTab /> },
          { key: "client", label: "الاتصال بجهاز آخر", content: <ClientTab /> },
        ]} />
      </div>
    </div>
  );
}
