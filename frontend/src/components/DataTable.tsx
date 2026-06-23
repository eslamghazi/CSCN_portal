import { ReactNode, useMemo, useRef, useState } from "react";
import { Icon } from "./icons";

export interface Column<T> {
  key: string;
  label: string;
  sortable?: boolean;
  render?: (row: T) => ReactNode;
  sortValue?: (row: T) => string | number;
  className?: string;
}

export interface FilterDef {
  key: string;
  label: string;
  options: { value: string; label: string }[];
}

interface DataTableProps<T> {
  columns: Column<T>[];
  rows: T[];
  loading?: boolean;
  getSearchText?: (row: T) => string;
  rowActions?: (row: T) => ReactNode;
  filters?: FilterDef[];
  getFilterValue?: (row: T, key: string) => string;
  // Toolbar
  title?: string;
  onAdd?: () => void;
  addLabel?: string;
  onRefresh?: () => void;
  onExport?: (fmt: "excel" | "pdf") => void;
  onImport?: (file: File) => void;
  onTemplate?: () => void;
  pageSize?: number;
  emptyText?: string;
}

export function DataTable<T extends Record<string, any>>(props: DataTableProps<T>) {
  const {
    columns, rows, loading, getSearchText, rowActions, filters, getFilterValue,
    onAdd, addLabel = "إضافة", onRefresh, onExport, onImport, onTemplate,
    pageSize = 12, emptyText = "لا توجد بيانات",
  } = props;

  const [q, setQ] = useState("");
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortDir, setSortDir] = useState<"asc" | "desc">("asc");
  const [page, setPage] = useState(1);
  const [filterVals, setFilterVals] = useState<Record<string, string>>({});
  const fileRef = useRef<HTMLInputElement>(null);

  const filtered = useMemo(() => {
    let data = rows;
    if (q.trim() && getSearchText) {
      const needle = q.trim().toLowerCase();
      data = data.filter((r) => getSearchText(r).toLowerCase().includes(needle));
    }
    for (const [k, v] of Object.entries(filterVals)) {
      if (v && getFilterValue) data = data.filter((r) => getFilterValue(r, k) === v);
    }
    if (sortKey) {
      const col = columns.find((c) => c.key === sortKey);
      const val = (r: T) => (col?.sortValue ? col.sortValue(r) : r[sortKey] ?? "");
      data = [...data].sort((a, b) => {
        const av = val(a), bv = val(b);
        if (av < bv) return sortDir === "asc" ? -1 : 1;
        if (av > bv) return sortDir === "asc" ? 1 : -1;
        return 0;
      });
    }
    return data;
  }, [rows, q, filterVals, sortKey, sortDir, columns, getSearchText, getFilterValue]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const curPage = Math.min(page, totalPages);
  const pageRows = filtered.slice((curPage - 1) * pageSize, curPage * pageSize);

  function toggleSort(key: string) {
    if (sortKey === key) setSortDir((d) => (d === "asc" ? "desc" : "asc"));
    else { setSortKey(key); setSortDir("asc"); }
  }

  return (
    <div className="card overflow-hidden">
      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-2 border-b border-border p-3">
        {getSearchText && (
          <div className="relative">
            <span className="pointer-events-none absolute right-2.5 top-1/2 -translate-y-1/2 text-ink-muted">
              <Icon name="search" size={16} />
            </span>
            <input className="input w-56 pr-8" placeholder="بحث..." value={q}
              onChange={(e) => { setQ(e.target.value); setPage(1); }} />
          </div>
        )}
        {filters?.map((f) => (
          <select key={f.key} className="input w-auto"
            value={filterVals[f.key] || ""}
            onChange={(e) => { setFilterVals((s) => ({ ...s, [f.key]: e.target.value })); setPage(1); }}>
            <option value="">{f.label}: الكل</option>
            {f.options.map((o) => <option key={o.value} value={o.value}>{o.label}</option>)}
          </select>
        ))}
        <div className="flex-1" />
        {onTemplate && (
          <button className="btn-secondary" onClick={onTemplate} title="تنزيل قالب Excel">
            <Icon name="download" size={16} /> قالب
          </button>
        )}
        {onImport && (
          <>
            <input ref={fileRef} type="file" accept=".xlsx" className="hidden"
              onChange={(e) => { const f = e.target.files?.[0]; if (f) onImport(f); e.target.value = ""; }} />
            <button className="btn-secondary" onClick={() => fileRef.current?.click()}>
              <Icon name="upload" size={16} /> استيراد
            </button>
          </>
        )}
        {onExport && (
          <>
            <button className="btn-secondary" onClick={() => onExport("excel")}>
              <Icon name="download" size={16} /> Excel
            </button>
            <button className="btn-secondary" onClick={() => onExport("pdf")}>
              <Icon name="download" size={16} /> PDF
            </button>
          </>
        )}
        {onRefresh && (
          <button className="icon-btn" onClick={onRefresh} title="تحديث"><Icon name="refresh" size={16} /></button>
        )}
        {onAdd && (
          <button className="btn-primary" onClick={onAdd}><Icon name="add" size={16} /> {addLabel}</button>
        )}
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="w-full text-right text-sm">
          <thead>
            <tr className="border-b border-border bg-surface-alt text-ink-secondary">
              {columns.map((c) => (
                <th key={c.key}
                  className={`whitespace-nowrap px-4 py-3 font-semibold ${c.sortable ? "cursor-pointer select-none" : ""} ${c.className || ""}`}
                  onClick={() => c.sortable && toggleSort(c.key)}>
                  <span className="inline-flex items-center gap-1">
                    {c.label}
                    {c.sortable && sortKey === c.key && (
                      <span className="text-primary">{sortDir === "asc" ? "▲" : "▼"}</span>
                    )}
                  </span>
                </th>
              ))}
              {rowActions && <th className="px-4 py-3 font-semibold">إجراءات</th>}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-ink-muted">جاري التحميل...</td></tr>
            ) : pageRows.length === 0 ? (
              <tr><td colSpan={columns.length + 1} className="px-4 py-12 text-center text-ink-muted">{emptyText}</td></tr>
            ) : (
              pageRows.map((row, i) => (
                <tr key={row.id ?? i} className="border-b border-border last:border-0 hover:bg-surface-alt/60">
                  {columns.map((c) => (
                    <td key={c.key} className={`px-4 py-3 ${c.className || ""}`}>
                      {c.render ? c.render(row) : (row[c.key] ?? "-")}
                    </td>
                  ))}
                  {rowActions && <td className="px-4 py-2"><div className="flex items-center gap-1.5">{rowActions(row)}</div></td>}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      {totalPages > 1 && (
        <div className="flex items-center justify-between border-t border-border px-4 py-3 text-sm text-ink-secondary">
          <span>{filtered.length} سجل</span>
          <div className="flex items-center gap-1">
            <button className="icon-btn h-8 w-8" disabled={curPage <= 1} onClick={() => setPage(curPage - 1)}>‹</button>
            <span className="px-2">{curPage} / {totalPages}</span>
            <button className="icon-btn h-8 w-8" disabled={curPage >= totalPages} onClick={() => setPage(curPage + 1)}>›</button>
          </div>
        </div>
      )}
    </div>
  );
}
