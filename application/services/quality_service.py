from typing import List, Optional
from pydantic import BaseModel
from infrastructure.repositories.standard_repository import StandardRepository, StandardCategoryRepository
from infrastructure.repositories.indicator_repository import IndicatorRepository
from domain.entities.standard import Standard, StandardCategory
from domain.entities.indicator import Indicator
from application.services.audit_service import AuditService

class StandardDTO(BaseModel):
    id: Optional[int] = None
    code: str
    name: str
    description: Optional[str] = None
    category_id: Optional[int] = None
    status: str = "active"

class IndicatorDTO(BaseModel):
    id: Optional[int] = None
    code: str
    name: str
    description: Optional[str] = None
    standard_id: Optional[int] = None
    parent_id: Optional[int] = None
    weight: Optional[float] = None
    status: str = "active"
    sort_order: int = 0

class QualityService:
    def __init__(
        self, 
        standard_repo: StandardRepository, 
        category_repo: StandardCategoryRepository,
        indicator_repo: IndicatorRepository,
        audit_service: AuditService
    ):
        self.standard_repo = standard_repo
        self.category_repo = category_repo
        self.indicator_repo = indicator_repo
        self.audit_service = audit_service
        
    def create_standard(self, data: StandardDTO) -> Standard:
        standard = Standard(
            code=data.code,
            name=data.name,
            description=data.description,
            category_id=data.category_id,
            status=data.status
        )
        
        created = self.standard_repo.create(standard)
        
        self.audit_service.log_action(
            module="quality",
            action="create_standard",
            entity_type="Standard",
            entity_id=created.id,
            new_values={"code": created.code, "name": created.name}
        )
        
        return created
        
    def get_all_standards(self) -> List[Standard]:
        return self.standard_repo.get_all()
        
    def get_all_categories(self) -> List[StandardCategory]:
        return self.category_repo.get_all()

    def create_category(self, name: str, description: str = None) -> StandardCategory:
        return self.category_repo.create(
            StandardCategory(name=name, description=description))

    def update_category(self, category_id: int, name: str,
                        description: str = None) -> Optional[StandardCategory]:
        category = self.category_repo.get_by_id(category_id)
        if not category:
            return None
        category.name = name
        category.description = description
        return self.category_repo.update(category)

    def delete_category(self, category_id: int) -> bool:
        return self.category_repo.delete(category_id)
        
    def update_standard(self, data: StandardDTO) -> Optional[Standard]:
        if not data.id:
            return None
            
        standard = self.standard_repo.get_by_id(data.id)
        if not standard:
            return None
            
        old_values = {"code": standard.code, "name": standard.name, "status": standard.status}
        
        standard.code = data.code
        standard.name = data.name
        standard.description = data.description
        standard.category_id = data.category_id
        standard.status = data.status
        
        updated = self.standard_repo.update(standard)
        
        self.audit_service.log_action(
            module="quality",
            action="update_standard",
            entity_type="Standard",
            entity_id=updated.id,
            old_values=old_values,
            new_values={"code": updated.code, "name": updated.name, "status": updated.status}
        )
        
        return updated
        
    def delete_standard(self, standard_id: int) -> bool:
        deleted = self.standard_repo.delete(standard_id)
        if deleted:
            self.audit_service.log_action(
                module="quality", action="delete_standard",
                entity_type="Standard", entity_id=standard_id)
        return deleted

    # ----------------------------------------------------------- indicators
    def get_indicators(self, standard_id: int) -> List[Indicator]:
        """Root indicators for a standard (sub-indicators via .sub_indicators)."""
        return self.indicator_repo.get_by_standard_id(standard_id)

    def get_indicator(self, indicator_id: int) -> Optional[Indicator]:
        return self.indicator_repo.get_by_id(indicator_id)

    def create_indicator(self, data: IndicatorDTO) -> Indicator:
        indicator = Indicator(
            code=data.code, name=data.name, description=data.description,
            standard_id=data.standard_id, parent_id=data.parent_id,
            weight=data.weight, status=data.status, sort_order=data.sort_order,
        )
        created = self.indicator_repo.create(indicator)
        self.audit_service.log_action(
            module="quality", action="create_indicator",
            entity_type="Indicator", entity_id=created.id,
            new_values={"code": created.code})
        return created

    def update_indicator(self, data: IndicatorDTO) -> Optional[Indicator]:
        if not data.id:
            return None
        indicator = self.indicator_repo.get_by_id(data.id)
        if not indicator:
            return None
        indicator.code = data.code
        indicator.name = data.name
        indicator.description = data.description
        indicator.parent_id = data.parent_id
        indicator.weight = data.weight
        indicator.status = data.status
        updated = self.indicator_repo.update(indicator)
        self.audit_service.log_action(
            module="quality", action="update_indicator",
            entity_type="Indicator", entity_id=updated.id)
        return updated

    def delete_indicator(self, indicator_id: int) -> bool:
        deleted = self.indicator_repo.delete(indicator_id)
        if deleted:
            self.audit_service.log_action(
                module="quality", action="delete_indicator",
                entity_type="Indicator", entity_id=indicator_id)
        return deleted

    def calculate_compliance(self, standard_id: int) -> float:
        """
        Calculate compliance percentage for a standard based on its indicators.
        """
        indicators = self.indicator_repo.get_by_standard_id(standard_id)
        if not indicators:
            return 0.0
            
        compliant_count = sum(1 for ind in indicators if ind.status == "compliant")
        return (compliant_count / len(indicators)) * 100.0
