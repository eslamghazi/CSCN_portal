// Sidebar navigation. `module` gates by permission (module/view); `roles` gates
// purely by role. Items the user can't see are filtered out in the Layout.
export interface NavItem {
  key: string;
  label: string;
  icon: string;
  path: string;
  module?: string;       // requires has_permission(module, "view")
  roles?: string[];      // requires role in this set (superadmin always allowed)
}

export const NAV: NavItem[] = [
  { key: "dashboard", label: "لوحة القيادة", icon: "dashboard", path: "/" },
  { key: "standards", label: "إدارة المعايير", icon: "standards", path: "/standards", module: "quality" },
  { key: "documents", label: "نظام الوثائق", icon: "documents", path: "/documents", module: "documents" },
  { key: "records", label: "السجلات والمحفوظات", icon: "records", path: "/records", module: "records" },
  { key: "training", label: "البرامج التدريبية", icon: "training", path: "/training", module: "training" },
  { key: "hr", label: "شؤون العاملين", icon: "hr", path: "/hr", module: "hr" },
  { key: "financial", label: "المالية والشراكات", icon: "financial", path: "/financial", module: "financial" },
  { key: "reports", label: "التقارير والإحصائيات", icon: "reports", path: "/reports", module: "reports" },
  { key: "lookups", label: "البيانات المرجعية", icon: "lookups", path: "/lookups", roles: ["admin"] },
  { key: "admin", label: "إدارة النظام", icon: "admin", path: "/admin", roles: [] },
  { key: "backup", label: "النسخ الاحتياطي", icon: "backup", path: "/backup", roles: [] },
  { key: "remote", label: "الإدارة عن بُعد", icon: "remote", path: "/remote", roles: [] },
  { key: "settings", label: "إعدادات الحساب", icon: "settings", path: "/settings" },
];
