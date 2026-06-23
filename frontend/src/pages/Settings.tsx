import { useEffect, useState } from "react";
import { api } from "../api/client";
import { useAuth } from "../auth/AuthContext";
import { useToast } from "../components/Toast";
import { PageHeader } from "../components/PageHeader";

export default function Settings() {
  const { refresh } = useAuth();
  const toast = useToast();
  const [profile, setProfile] = useState<any>(null);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    api.get("/api/settings/profile").then((p) => { setProfile(p); setUsername(p.username); }).catch(() => {});
  }, []);

  async function save() {
    if (!username.trim()) { toast.error("اسم المستخدم مطلوب"); return; }
    setBusy(true);
    try {
      await api.put("/api/settings/profile", { username: username.trim(), password: password || null });
      toast.success("تم حفظ التغييرات"); setPassword(""); refresh();
    } catch (e: any) { toast.error(e?.detail || "تعذّر الحفظ"); }
    finally { setBusy(false); }
  }

  if (!profile) return <div className="card flex h-48 items-center justify-center text-ink-muted">جاري التحميل...</div>;

  return (
    <div>
      <PageHeader title="إعدادات الحساب" subtitle="تعديل اسم المستخدم وكلمة المرور." />
      <div className="card max-w-xl p-6">
        <div className="mb-4 grid grid-cols-2 gap-4 text-sm">
          <div><span className="text-ink-muted">الاسم:</span> {profile.full_name}</div>
          <div><span className="text-ink-muted">الصلاحية:</span> {profile.role_name}</div>
        </div>
        <label className="label">اسم المستخدم</label>
        <input className="input mb-4" value={username} onChange={(e) => setUsername(e.target.value)} />
        <label className="label">كلمة مرور جديدة (اتركها فارغة للإبقاء على الحالية)</label>
        <input className="input mb-6" type="password" value={password} onChange={(e) => setPassword(e.target.value)} />
        <button className="btn-primary" onClick={save} disabled={busy}>حفظ التغييرات</button>
      </div>
    </div>
  );
}
