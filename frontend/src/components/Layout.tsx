import { NavLink, useLocation } from "react-router-dom";
import { useAuth } from "../auth/AuthContext";
import { NAV, NavItem } from "../nav";
import { Icon } from "./icons";

function visible(item: NavItem, user: any, can: (m: string, a: string) => boolean): boolean {
  if (item.roles) {
    // roles=[] means superadmin-only; otherwise role must be in the set.
    const role = user?.role_name || "";
    if (role === "superadmin") return true;
    return item.roles.includes(role);
  }
  if (item.module) return can(item.module, "view");
  return true;
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, can, logout } = useAuth();
  const loc = useLocation();
  const items = NAV.filter((i) => visible(i, user, can));
  const today = new Date().toISOString().slice(0, 10);
  const active = NAV.find((i) => i.path === loc.pathname)?.label || "";

  return (
    <div className="flex h-full">
      {/* Sidebar */}
      <aside className="flex w-64 flex-shrink-0 flex-col bg-gradient-to-b from-sidebar-top to-sidebar-bottom text-white">
        <div className="px-5 py-5 text-center">
          <div className="mx-auto mb-2 flex h-12 w-12 items-center justify-center rounded-xl bg-white/15">
            <Icon name="hr" size={26} />
          </div>
          <p className="text-[13px] font-bold leading-5">مركز الخدمة المجتمعية بكلية التمريض</p>
          <p className="text-[11px] text-white/60">جامعة كفر الشيخ</p>
        </div>
        <nav className="flex-1 overflow-y-auto px-3 py-2">
          {items.map((item) => (
            <NavLink key={item.key} to={item.path} end={item.path === "/"}
              className={({ isActive }) =>
                `relative mb-1 flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm transition ${
                  isActive ? "bg-white/15 font-semibold" : "text-white/85 hover:bg-white/10"
                }`}>
              {({ isActive }) => (
                <>
                  {isActive && <span className="absolute inset-y-1.5 right-0 w-1 rounded-full bg-sidebar-active" />}
                  <Icon name={item.icon} size={18} />
                  <span>{item.label}</span>
                </>
              )}
            </NavLink>
          ))}
        </nav>
        <button onClick={logout}
          className="m-3 flex items-center justify-center gap-2 rounded-lg bg-white/10 px-3 py-2.5 text-sm text-red-200 hover:bg-white/15">
          <Icon name="logout" size={18} /> تسجيل الخروج
        </button>
        <p className="pb-3 text-center text-[10px] text-white/40">v1.1.0</p>
      </aside>

      {/* Main */}
      <div className="flex flex-1 flex-col overflow-hidden">
        <header className="flex h-16 flex-shrink-0 items-center justify-between border-b border-border bg-surface px-6">
          <h2 className="text-lg font-bold text-ink">{active}</h2>
          <div className="flex items-center gap-4">
            <span dir="ltr" className="text-sm text-ink-muted">{today}</span>
            <div className="flex items-center gap-2">
              <span className="text-sm font-medium text-ink">{user?.full_name || user?.username}</span>
              <span className="flex h-9 w-9 items-center justify-center rounded-full bg-primary-soft text-primary">
                <Icon name="user" size={18} />
              </span>
            </div>
          </div>
        </header>
        <main className="flex-1 overflow-y-auto p-6">{children}</main>
      </div>
    </div>
  );
}
