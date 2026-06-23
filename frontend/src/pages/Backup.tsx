import { useRef, useState } from "react";
import { api } from "../api/client";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { Icon } from "../components/icons";

export default function Backup() {
  const toast = useToast();
  const dbRef = useRef<HTMLInputElement>(null);
  const zipRef = useRef<HTMLInputElement>(null);
  const [pending, setPending] = useState<{ kind: "db" | "full"; file: File } | null>(null);

  async function backupDb() { try { await api.download("/api/backup/db"); toast.success("تم إنشاء النسخة"); } catch { toast.error("تعذّر إنشاء النسخة"); } }
  async function exportAll() { try { await api.download("/api/backup/export"); toast.success("تم تصدير النسخة الكاملة"); } catch { toast.error("تعذّر التصدير"); } }

  async function doRestore() {
    if (!pending) return;
    const url = pending.kind === "db" ? "/api/backup/restore-db" : "/api/backup/restore-full";
    try {
      const r = await api.upload(url, pending.file);
      toast.success(r.message || "تمت الاستعادة. أعد تشغيل الخادم.");
    } catch (e: any) { toast.error(e?.detail || "تعذّر الاستعادة"); }
    finally { setPending(null); }
  }

  return (
    <div>
      <PageHeader title="النسخ الاحتياطي والاستعادة" subtitle="إنشاء نسخة احتياطية أو استعادة البيانات." />
      <div className="grid grid-cols-1 gap-5 lg:grid-cols-2">
        <div className="card p-6">
          <h3 className="mb-4 font-bold text-ink">النسخ والتصدير</h3>
          <button className="btn-primary mb-3 w-full" onClick={backupDb}><Icon name="backup" size={16} /> نسخة احتياطية لقاعدة البيانات</button>
          <button className="btn-secondary w-full" onClick={exportAll}><Icon name="download" size={16} /> تصدير نسخة كاملة (قاعدة البيانات + الملفات)</button>
        </div>
        <div className="card p-6">
          <h3 className="mb-2 font-bold text-danger">الاستعادة</h3>
          <p className="mb-4 text-sm text-ink-secondary">تحذير: الاستعادة تستبدل البيانات الحالية وتتطلب إعادة تشغيل الخادم.</p>
          <input ref={dbRef} type="file" accept=".db" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) setPending({ kind: "db", file: f }); e.target.value = ""; }} />
          <input ref={zipRef} type="file" accept=".zip" className="hidden" onChange={(e) => { const f = e.target.files?.[0]; if (f) setPending({ kind: "full", file: f }); e.target.value = ""; }} />
          <button className="btn-secondary mb-3 w-full" onClick={() => dbRef.current?.click()}><Icon name="upload" size={16} /> استعادة قاعدة بيانات (.db)</button>
          <button className="btn-secondary w-full" onClick={() => zipRef.current?.click()}><Icon name="upload" size={16} /> استعادة نسخة كاملة (.zip)</button>
        </div>
      </div>
      <ConfirmDialog open={pending != null}
        message="هل تريد استعادة البيانات؟ سيتم استبدال جميع البيانات الحالية ويجب إعادة تشغيل الخادم بعدها."
        onConfirm={doRestore} onCancel={() => setPending(null)} />
    </div>
  );
}
