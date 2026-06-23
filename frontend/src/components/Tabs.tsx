import { ReactNode, useState } from "react";

export interface TabDef { key: string; label: string; content: ReactNode; }

export function Tabs({ tabs }: { tabs: TabDef[] }) {
  const [active, setActive] = useState(tabs[0]?.key);
  return (
    <div>
      <div className="mb-4 flex gap-1 border-b border-border">
        {tabs.map((t) => (
          <button key={t.key} onClick={() => setActive(t.key)}
            className={`-mb-px border-b-2 px-4 py-2.5 text-sm font-semibold transition ${
              active === t.key ? "border-primary text-primary" : "border-transparent text-ink-secondary hover:text-ink"
            }`}>
            {t.label}
          </button>
        ))}
      </div>
      <div>{tabs.find((t) => t.key === active)?.content}</div>
    </div>
  );
}
