"""Standalone audit logging service."""

from typing import Optional

from src.data.database import Database, get_database
from src.models.update_proposal import AuditLogEntry, ChangeSource, EntityType


class AuditService:
    """Service for recording and querying audit log entries."""

    def __init__(self, db: Database | None = None):
        self.db = db or get_database()

    def log_change(
        self,
        entity_type: EntityType,
        entity_id: int,
        field_name: str,
        old_value: Optional[str],
        new_value: Optional[str],
        change_source: ChangeSource,
        changed_by: str = "user",
        proposal_id: Optional[int] = None,
    ) -> int:
        """Record a single field change in the audit log. Returns entry ID."""
        entry = AuditLogEntry(
            entity_type=entity_type,
            entity_id=entity_id,
            field_name=field_name,
            old_value=old_value,
            new_value=new_value,
            change_source=change_source,
            changed_by=changed_by,
            proposal_id=proposal_id,
        )
        return self.save_entry(entry)

    def save_entry(self, entry: AuditLogEntry) -> int:
        """Save an audit log entry to the database."""
        data = entry.to_db_dict()
        cursor = self.db.execute(
            """INSERT INTO audit_log
               (entity_type, entity_id, field_name, old_value, new_value,
                change_source, changed_at, changed_by, proposal_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                data["entity_type"],
                data["entity_id"],
                data["field_name"],
                data["old_value"],
                data["new_value"],
                data["change_source"],
                data["changed_at"],
                data["changed_by"],
                data["proposal_id"],
            ),
        )
        self.db.commit()
        return cursor.lastrowid

    def get_log(
        self,
        entity_type: Optional[EntityType] = None,
        entity_id: Optional[int] = None,
        limit: int = 100,
    ) -> list[AuditLogEntry]:
        """Query audit log entries with optional filters."""
        query = "SELECT * FROM audit_log WHERE 1=1"
        params: list = []

        if entity_type:
            query += " AND entity_type = ?"
            params.append(entity_type.value)

        if entity_id:
            query += " AND entity_id = ?"
            params.append(entity_id)

        query += " ORDER BY changed_at DESC LIMIT ?"
        params.append(limit)

        cursor = self.db.execute(query, tuple(params))
        return [AuditLogEntry.from_db_row(dict(row)) for row in cursor.fetchall()]
