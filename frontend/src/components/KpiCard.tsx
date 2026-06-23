import { Icon } from "./icons";

const accentMap: Record<string, string> = {
  blue: "text-kpi-blue bg-info-bg",
  green: "text-kpi-green bg-success-bg",
  amber: "text-kpi-amber bg-warning-bg",
  purple: "text-kpi-purple bg-accent-soft",
};
const barMap: Record<string, string> = {
  blue: "bg-kpi-blue", green: "bg-kpi-green", amber: "bg-kpi-amber", purple: "bg-kpi-purple",
};

interface KpiCardProps {
  title: string;
  value: number | string;
  icon: string;
  accent: string;
  onClick?: () => void;
}

export function KpiCard({ title, value, icon, accent, onClick }: KpiCardProps) {
  return (
    <button
      onClick={onClick}
      className="card relative flex items-center gap-4 overflow-hidden p-5 text-right transition hover:shadow-soft disabled:cursor-default"
      disabled={!onClick}
    >
      <span className={`absolute inset-y-0 right-0 w-1.5 ${barMap[accent] || "bg-primary"}`} />
      <span className={`flex h-12 w-12 items-center justify-center rounded-xl ${accentMap[accent] || ""}`}>
        <Icon name={icon} size={24} />
      </span>
      <span className="flex flex-col">
        <span className="text-2xl font-extrabold text-ink">{value}</span>
        <span className="text-sm text-ink-secondary">{title}</span>
      </span>
    </button>
  );
}
