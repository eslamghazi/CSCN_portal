"""Backup / restore / full export (superadmin). Restore requires a server restart."""
import os
import tempfile

from fastapi import APIRouter, Depends, UploadFile, File

from api.permissions import require_role
from api.responses import file_download

router = APIRouter(prefix="/api/backup", tags=["backup"])
ZIP_MEDIA = "application/zip"
DB_MEDIA = "application/octet-stream"


@router.get("/db")
def backup_db(user=Depends(require_role())):
    from application.services.backup_service import BackupService
    path = BackupService().backup_db()
    return file_download(path, os.path.basename(path), DB_MEDIA)


@router.get("/export")
def export_all(user=Depends(require_role())):
    from datetime import datetime
    from application.services.backup_service import BackupService
    dest = os.path.join(tempfile.gettempdir(),
                        f"CSCN_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip")
    BackupService().export_all(dest)
    return file_download(dest, os.path.basename(dest), ZIP_MEDIA)


@router.post("/restore-db")
async def restore_db(file: UploadFile = File(...), user=Depends(require_role())):
    from application.services.backup_service import BackupService
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
    tmp.write(await file.read())
    tmp.close()
    try:
        BackupService().restore_db(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return {"success": True, "message": "تمت الاستعادة. أعد تشغيل الخادم لتطبيق التغييرات."}


@router.post("/restore-full")
async def restore_full(file: UploadFile = File(...), user=Depends(require_role())):
    from application.services.backup_service import BackupService
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".zip")
    tmp.write(await file.read())
    tmp.close()
    try:
        BackupService().restore_full(tmp.name)
    finally:
        try:
            os.unlink(tmp.name)
        except OSError:
            pass
    return {"success": True, "message": "تمت الاستعادة الكاملة. أعد تشغيل الخادم لتطبيق التغييرات."}
