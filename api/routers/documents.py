"""Documents: list, upload (multipart), edit metadata, approve, download, delete."""
import os
import tempfile
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response, file_download
from application.services.document_service import DocumentDTO

router = APIRouter(prefix="/api/documents", tags=["documents"])
MODULE = "documents"


def _doc(d) -> dict:
    return {
        "id": d.id, "title": d.title, "doc_type": d.doc_type,
        "category_id": d.category_id, "category": d.category.name if d.category else None,
        "current_version": d.current_version,
        "effective_date": d.effective_date.isoformat() if d.effective_date else None,
        "status": d.status,
    }


def _date(s):
    from datetime import date
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


@router.get("/categories")
def categories(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [{"value": c.id, "label": c.name} for c in services["document"].get_categories()]


@router.get("")
def list_documents(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [_doc(d) for d in services["document"].get_all_documents()]


@router.post("")
async def upload_document(
    title: str = Form(...), doc_type: str = Form(""), category_id: Optional[str] = Form(None),
    status: str = Form("draft"), effective_date: Optional[str] = Form(None),
    file: UploadFile = File(...),
    user=Depends(require_perm(MODULE, "create")), services=Depends(get_services),
):
    if not title.strip():
        raise HTTPException(422, "العنوان مطلوب")
    suffix = os.path.splitext(file.filename or "")[1]
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    try:
        tmp.write(await file.read())
        tmp.close()
        dto = DocumentDTO(title=title.strip(), doc_type=doc_type or "policy",
                          category_id=int(category_id) if category_id else None,
                          status=status or "draft", effective_date=_date(effective_date))
        d = services["document"].upload_document(dto, tmp.name)
        return _doc(d)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass


class DocMetaBody(BaseModel):
    title: str
    doc_type: str = "policy"
    category_id: Optional[int] = None
    status: str = "draft"
    effective_date: Optional[str] = None


@router.put("/{doc_id}")
def update_document(doc_id: int, body: DocMetaBody, user=Depends(require_perm(MODULE, "edit")),
                    services=Depends(get_services)):
    d = services["document"].update_document(DocumentDTO(
        id=doc_id, title=body.title.strip(), doc_type=body.doc_type or "policy",
        category_id=body.category_id, status=body.status or "draft",
        effective_date=_date(body.effective_date)))
    if not d:
        raise HTTPException(404, "الوثيقة غير موجودة")
    return _doc(d)


@router.post("/{doc_id}/approve")
def approve_document(doc_id: int, user=Depends(require_perm(MODULE, "edit")),
                     services=Depends(get_services)):
    if not services["document"].approve_document(doc_id):
        raise HTTPException(404, "الوثيقة غير موجودة")
    return {"success": True}


@router.get("/{doc_id}/download")
def download_document(doc_id: int, user=Depends(require_perm(MODULE, "view")),
                      services=Depends(get_services)):
    path = services["document"].get_document_file_path(doc_id)
    if not path or not os.path.isfile(path):
        raise HTTPException(404, "لا يوجد ملف مرفق")
    filename = os.path.basename(path)
    import mimetypes
    media = mimetypes.guess_type(path)[0] or "application/octet-stream"
    return file_download(path, filename, media)


@router.delete("/{doc_id}")
def delete_document(doc_id: int, user=Depends(require_perm(MODULE, "delete")),
                    services=Depends(get_services)):
    services["document"].delete_document(doc_id)
    return {"success": True}


@router.get("/export")
def export_documents(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                     services=Depends(get_services)):
    headers = ["العنوان", "النوع", "التصنيف", "الإصدار", "تاريخ السريان", "الحالة"]
    rows = [[d.title, d.doc_type, (d.category.name if d.category else "-"),
             d.current_version, d.effective_date.isoformat() if d.effective_date else "-",
             "معتمد" if d.status == "approved" else "مسودة"]
            for d in services["document"].get_all_documents()]
    return export_response(services["report"], fmt, "documents", headers, rows, "الوثائق")
