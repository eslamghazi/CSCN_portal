// Thin fetch wrapper. Same-origin cookies carry the session, so every request
// includes credentials. JSON in / JSON out, with file download + upload helpers.

export class ApiError extends Error {
  status: number;
  detail: string;
  constructor(status: number, detail: string) {
    super(detail);
    this.status = status;
    this.detail = detail;
  }
}

async function parse(res: Response): Promise<any> {
  const text = await res.text();
  let data: any = null;
  if (text) {
    try { data = JSON.parse(text); } catch { data = text; }
  }
  if (!res.ok) {
    const detail = (data && data.detail) || (typeof data === "string" ? data : "حدث خطأ");
    throw new ApiError(res.status, detail);
  }
  return data;
}

const baseOpts: RequestInit = {
  credentials: "include",
  headers: { "Content-Type": "application/json" },
};

export const api = {
  get: (url: string) => fetch(url, { ...baseOpts, method: "GET" }).then(parse),
  post: (url: string, body?: any) =>
    fetch(url, { ...baseOpts, method: "POST", body: JSON.stringify(body ?? {}) }).then(parse),
  put: (url: string, body?: any) =>
    fetch(url, { ...baseOpts, method: "PUT", body: JSON.stringify(body ?? {}) }).then(parse),
  del: (url: string) => fetch(url, { ...baseOpts, method: "DELETE" }).then(parse),

  // Trigger a browser download for an export/file endpoint.
  download: async (url: string) => {
    const res = await fetch(url, { credentials: "include" });
    if (!res.ok) throw new ApiError(res.status, "تعذّر التنزيل");
    const blob = await res.blob();
    const cd = res.headers.get("Content-Disposition") || "";
    let filename = "download";
    const star = cd.match(/filename\*=UTF-8''([^;]+)/i);
    const plain = cd.match(/filename="?([^";]+)"?/i);
    if (star) filename = decodeURIComponent(star[1]);
    else if (plain) filename = plain[1];
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(link.href);
  },

  // Multipart upload (xlsx import, document upload). `fields` are extra form fields.
  upload: async (url: string, file: File, fields?: Record<string, string>) => {
    const fd = new FormData();
    fd.append("file", file);
    if (fields) for (const [k, v] of Object.entries(fields)) fd.append(k, v);
    return fetch(url, { method: "POST", credentials: "include", body: fd }).then(parse);
  },
};
