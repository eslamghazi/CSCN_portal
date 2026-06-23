import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { api } from "../api/client";
import { Kpi } from "../api/types";
import { KpiCard } from "../components/KpiCard";

const iconFor: Record<string, string> = {
  employees: "hr", standards: "standards", documents: "documents", training: "training",
};
const pathFor: Record<string, string> = {
  hr: "/hr", quality: "/standards", documents: "/documents", training: "/training",
};

export default function Dashboard() {
  const [kpis, setKpis] = useState<Kpi[]>([]);
  const nav = useNavigate();

  useEffect(() => {
    api.get("/api/dashboard/kpis").then((d) => setKpis(d.kpis)).catch(() => setKpis([]));
  }, []);

  return (
    <div>
      <div className="mb-6 rounded-card bg-gradient-to-l from-primary to-accent p-7 text-white">
        <h1 className="text-2xl font-extrabold">مرحباً بك في نظام إدارة مركز الخدمة المجتمعية</h1>
        <p className="mt-1 text-white/80">جامعة كفر الشيخ — يمكن الوصول السريع لجميع الخدمات من القائمة الجانبية.</p>
      </div>
      <h2 className="mb-4 text-lg font-bold text-ink">نظرة عامة</h2>
      <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
        {kpis.map((k) => (
          <KpiCard key={k.key} title={k.title} value={k.value} icon={iconFor[k.key] || "list"}
            accent={k.accent} onClick={pathFor[k.module] ? () => nav(pathFor[k.module]) : undefined} />
        ))}
      </div>
    </div>
  );
}
