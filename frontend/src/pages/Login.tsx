import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { Icon } from "../components/icons";

export default function Login() {
  const { login } = useAuth();
  const nav = useNavigate();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [remember, setRemember] = useState(false);
  const [show, setShow] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (!username.trim() || !password) { setError("أدخل اسم المستخدم وكلمة المرور."); return; }
    setBusy(true);
    const err = await login(username.trim(), password, remember);
    setBusy(false);
    if (err) { setError(err); setPassword(""); }
    else nav("/", { replace: true });
  }

  return (
    <div className="flex min-h-full items-center justify-center bg-gradient-to-br from-sidebar-top to-primary p-4">
      <form onSubmit={submit} className="card w-full max-w-md p-8">
        <div className="mb-6 text-center">
          <div className="mx-auto mb-3 flex h-14 w-14 items-center justify-center rounded-2xl bg-primary-soft text-primary">
            <Icon name="lock" size={28} />
          </div>
          <h1 className="text-xl font-extrabold text-ink">تسجيل الدخول</h1>
          <p className="mt-1 text-sm text-ink-secondary">مركز الخدمة المجتمعية بكلية التمريض — جامعة كفر الشيخ</p>
        </div>

        {error && <div className="mb-4 rounded-lg bg-danger-bg px-3 py-2 text-sm text-danger-text">{error}</div>}

        <label className="label">اسم المستخدم</label>
        <input className="input mb-4" value={username} onChange={(e) => setUsername(e.target.value)} autoFocus />

        <label className="label">كلمة المرور</label>
        <div className="relative mb-3">
          <input className="input pl-10" type={show ? "text" : "password"} value={password}
            onChange={(e) => setPassword(e.target.value)} />
          <button type="button" onClick={() => setShow((s) => !s)}
            className="absolute left-2 top-1/2 -translate-y-1/2 text-ink-muted hover:text-primary" tabIndex={-1}>
            <Icon name="eye" size={18} />
          </button>
        </div>

        <label className="mb-5 flex items-center gap-2 text-sm text-ink-secondary">
          <input type="checkbox" checked={remember} onChange={(e) => setRemember(e.target.checked)} />
          إبقاء تسجيل الدخول
        </label>

        <button className="btn-primary w-full py-2.5" disabled={busy}>
          {busy ? "جاري الدخول..." : "تسجيل الدخول"}
        </button>
      </form>
    </div>
  );
}
