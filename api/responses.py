"""Shared helpers for building API responses, chiefly file downloads with
Arabic-safe filenames."""
from urllib.parse import quote

from fastapi.responses import FileResponse

XLSX_MEDIA = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
PDF_MEDIA = "application/pdf"


def _content_disposition(filename: str) -> str:
    """RFC 5987 Content-Disposition supporting non-ASCII (Arabic) filenames."""
    ascii_fallback = filename.encode("ascii", "ignore").decode("ascii") or "download"
    return f"attachment; filename=\"{ascii_fallback}\"; filename*=UTF-8''{quote(filename)}"


def file_download(path: str, filename: str, media_type: str) -> FileResponse:
    return FileResponse(
        path, media_type=media_type,
        headers={"Content-Disposition": _content_disposition(filename)},
    )


def export_response(report_engine, fmt: str, module_name: str, headers, rows,
                    title: str, download_name: str = None):
    """Generate an Excel or PDF export via ReportEngine and return it as a
    download. ``fmt`` is 'excel' or 'pdf'. NEVER CSV."""
    fmt = (fmt or "excel").lower()
    if fmt == "pdf":
        path = report_engine.export_to_pdf(module_name, headers, rows, title=title)
        ext, media = "pdf", PDF_MEDIA
    else:
        path = report_engine.export_to_excel(module_name, headers, rows, title=title)
        ext, media = "xlsx", XLSX_MEDIA
    name = download_name or f"{title or module_name}"
    return file_download(path, f"{name}.{ext}", media)
