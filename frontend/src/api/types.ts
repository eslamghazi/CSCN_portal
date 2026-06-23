export type PermissionMap = Record<string, Record<string, boolean>>;

export interface CurrentUser {
  id: number;
  username: string;
  full_name: string | null;
  email: string | null;
  phone: string | null;
  role_name: string | null;
  permissions: PermissionMap;
}

export interface Kpi {
  key: string;
  module: string;
  title: string;
  accent: "blue" | "green" | "amber" | "purple";
  value: number;
}
