import { ReactNode } from "react";

export interface FieldDef {
  name: string;
  label: string;
  type?: "text" | "number" | "date" | "email" | "tel" | "textarea" | "select" | "password";
  required?: boolean;
  options?: { value: string | number; label: string }[];
  placeholder?: string;
  colSpan?: 1 | 2;
}

interface FieldProps {
  field: FieldDef;
  value: any;
  error?: string;
  onChange: (name: string, value: any) => void;
}

export function Field({ field, value, error, onChange }: FieldProps) {
  const v = value ?? "";
  const common = "input" + (error ? " border-danger focus:border-danger focus:ring-danger/30" : "");
  return (
    <div className={field.colSpan === 2 ? "sm:col-span-2" : ""}>
      <label className="label">
        {field.label}{field.required && <span className="text-danger"> *</span>}
      </label>
      {field.type === "textarea" ? (
        <textarea className={common} rows={3} value={v} placeholder={field.placeholder}
          onChange={(e) => onChange(field.name, e.target.value)} />
      ) : field.type === "select" ? (
        <select className={common} value={v} onChange={(e) => onChange(field.name, e.target.value)}>
          <option value="">— اختر —</option>
          {field.options?.map((o) => (
            <option key={o.value} value={o.value}>{o.label}</option>
          ))}
        </select>
      ) : (
        <input className={common} type={field.type || "text"} value={v} placeholder={field.placeholder}
          onChange={(e) => onChange(field.name, e.target.value)} />
      )}
      {error && <p className="mt-1 text-xs text-danger">{error}</p>}
    </div>
  );
}

export function FieldGrid({ children }: { children: ReactNode }) {
  return <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">{children}</div>;
}
