from typing import List, Optional
from domain.entities.record import Record, RecordType
from infrastructure.repositories.record_repository import RecordRepository

class RecordService:
    def __init__(self, record_repository: RecordRepository):
        self.record_repository = record_repository

    def get_all_records(self) -> List[Record]:
        return self.record_repository.get_all()

    def get_record_by_id(self, record_id: int) -> Optional[Record]:
        return self.record_repository.get_by_id(record_id)

    def add_record(self, record_number: str, title: str, record_type_id: int = None,
                   storage_location: str = None, retention_period_months: int = None,
                   disposal_method: str = None, status: str = "active", notes: str = None) -> Record:
        record = Record(
            record_number=record_number,
            title=title,
            record_type_id=record_type_id,
            storage_location=storage_location,
            retention_period_months=retention_period_months,
            disposal_method=disposal_method,
            status=status,
            notes=notes
        )
        return self.record_repository.create(record)

    def update_record(self, record: Record) -> Record:
        return self.record_repository.update(record)

    def delete_record(self, record_id: int) -> bool:
        return self.record_repository.delete(record_id)

    def get_all_record_types(self) -> List[RecordType]:
        return self.record_repository.get_all_record_types()

    def add_record_type(self, name: str, description: str = None) -> RecordType:
        record_type = RecordType(name=name, description=description)
        return self.record_repository.create_record_type(record_type)

    def update_record_type(self, type_id: int, name: str,
                           description: str = None) -> RecordType:
        return self.record_repository.update_record_type(type_id, name, description)

    def delete_record_type(self, type_id: int) -> bool:
        return self.record_repository.delete_record_type(type_id)
