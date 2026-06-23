"""Financial: transactions (revenue/expense), fiscal years, budget items."""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from api.deps import get_services, require_perm
from api.responses import export_response
from application.services.financial_service import TransactionDTO, FiscalYearDTO, BudgetItemDTO

router = APIRouter(prefix="/api/financial", tags=["financial"])
MODULE = "financial"


def _d(s):
    from datetime import date
    if not s:
        return None
    try:
        return date.fromisoformat(s)
    except ValueError:
        return None


# --------------------------------------------------------------- transactions
@router.get("/summary")
def summary(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return services["financial"].get_financial_summary()


@router.get("/transactions")
def list_transactions(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    out = []
    for t in services["financial"].get_all_transactions():
        out.append({
            "id": t.id,
            "transaction_type": t.transaction_type,
            "type_label": "إيراد" if t.transaction_type == "revenue" else "مصروف",
            "amount": float(t.amount),
            "date": t.date.isoformat() if t.date else None,
            "category": getattr(t, "category", None),
            "description": t.description,
        })
    return out


class TxnBody(BaseModel):
    transaction_type: str
    amount: float
    date: str
    description: str
    source: Optional[str] = None
    category: Optional[str] = None
    reference_number: Optional[str] = None
    budget_id: Optional[int] = None


@router.post("/transactions")
def add_transaction(body: TxnBody, user=Depends(require_perm(MODULE, "create")),
                    services=Depends(get_services)):
    if body.transaction_type not in ("revenue", "expense"):
        raise HTTPException(422, "نوع المعاملة غير صحيح")
    dto = TransactionDTO(transaction_type=body.transaction_type, amount=body.amount,
                         date=_d(body.date), description=body.description,
                         source=body.source, category=body.category,
                         reference_number=body.reference_number, budget_id=body.budget_id)
    tx = services["financial"].add_transaction(dto)
    return {"id": tx.id}


@router.delete("/transactions/{kind}/{tid}")
def delete_transaction(kind: str, tid: int, user=Depends(require_perm(MODULE, "delete")),
                       services=Depends(get_services)):
    if kind == "revenue":
        services["financial"].delete_revenue(tid)
    elif kind == "expense":
        services["financial"].delete_expense(tid)
    else:
        raise HTTPException(404, "نوع غير معروف")
    return {"success": True}


@router.get("/transactions/export")
def export_transactions(fmt: str = "excel", user=Depends(require_perm(MODULE, "view")),
                        services=Depends(get_services)):
    headers = ["التاريخ", "النوع", "المبلغ", "التصنيف", "البيان"]
    rows = [[t.date.isoformat() if t.date else "-",
             "إيراد" if t.transaction_type == "revenue" else "مصروف",
             float(t.amount), getattr(t, "category", "-") or "-", t.description or "-"]
            for t in services["financial"].get_all_transactions()]
    return export_response(services["report"], fmt, "transactions", headers, rows, "المعاملات المالية")


# --------------------------------------------------------------- fiscal years
class FiscalYearBody(BaseModel):
    name: str
    start_date: str
    end_date: str
    status: str = "active"


@router.get("/fiscal-years")
def list_fy(user=Depends(require_perm(MODULE, "view")), services=Depends(get_services)):
    return [{"id": f.id, "name": f.name,
             "start_date": f.start_date.isoformat() if f.start_date else None,
             "end_date": f.end_date.isoformat() if f.end_date else None,
             "status": f.status} for f in services["financial"].list_fiscal_years()]


@router.post("/fiscal-years")
def create_fy(body: FiscalYearBody, user=Depends(require_perm(MODULE, "create")),
              services=Depends(get_services)):
    f = services["financial"].create_fiscal_year(FiscalYearDTO(
        name=body.name, start_date=_d(body.start_date), end_date=_d(body.end_date), status=body.status))
    return {"id": f.id}


@router.put("/fiscal-years/{fid}")
def update_fy(fid: int, body: FiscalYearBody, user=Depends(require_perm(MODULE, "edit")),
              services=Depends(get_services)):
    services["financial"].update_fiscal_year(FiscalYearDTO(
        id=fid, name=body.name, start_date=_d(body.start_date), end_date=_d(body.end_date), status=body.status))
    return {"success": True}


@router.delete("/fiscal-years/{fid}")
def delete_fy(fid: int, user=Depends(require_perm(MODULE, "delete")), services=Depends(get_services)):
    services["financial"].delete_fiscal_year(fid)
    return {"success": True}


# --------------------------------------------------------------- budget items
class BudgetBody(BaseModel):
    fiscal_year_id: int
    name: str
    allocated_amount: float = 0.0
    description: Optional[str] = None


@router.get("/budget-items")
def list_budget(fiscal_year_id: int, user=Depends(require_perm(MODULE, "view")),
                services=Depends(get_services)):
    fin = services["financial"]
    return [{"id": b.id, "name": b.name, "allocated_amount": float(b.allocated_amount or 0),
             "used": fin.budget_item_used(b.id), "description": b.description}
            for b in fin.list_budget_items(fiscal_year_id)]


@router.post("/budget-items")
def create_budget(body: BudgetBody, user=Depends(require_perm(MODULE, "create")),
                  services=Depends(get_services)):
    b = services["financial"].create_budget_item(BudgetItemDTO(**body.model_dump()))
    return {"id": b.id}


@router.put("/budget-items/{bid}")
def update_budget(bid: int, body: BudgetBody, user=Depends(require_perm(MODULE, "edit")),
                  services=Depends(get_services)):
    services["financial"].update_budget_item(BudgetItemDTO(id=bid, **body.model_dump()))
    return {"success": True}


@router.delete("/budget-items/{bid}")
def delete_budget(bid: int, user=Depends(require_perm(MODULE, "delete")),
                  services=Depends(get_services)):
    services["financial"].delete_budget_item(bid)
    return {"success": True}
