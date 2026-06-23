import { useCallback, useEffect, useState } from "react";
import { api } from "../api/client";

// Generic list-resource hook: loads a list endpoint and exposes reload + the
// CRUD verbs against the same base path. Each screen wires its own form/columns.
export function useResource<T = any>(listUrl: string) {
  const [rows, setRows] = useState<T[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await api.get(listUrl);
      setRows(Array.isArray(data) ? data : (data.items ?? []));
    } catch (e: any) {
      setError(e?.detail || "تعذّر تحميل البيانات");
      setRows([]);
    } finally {
      setLoading(false);
    }
  }, [listUrl]);

  useEffect(() => { reload(); }, [reload]);

  return { rows, loading, error, reload, setRows };
}
