from typing import Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.models import AuditLog, generate_uuid

class AuditLogger:
    @staticmethod
    async def log_event(
        db: AsyncSession,
        tenant_id: str,
        actor_id: str,
        actor_type: str,
        action: str,
        resource_type: str,
        resource_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        correlation_id: Optional[str] = None,
        result: str = "SUCCESS",
        metadata: Optional[Dict[str, Any]] = None
    ) -> AuditLog:
        audit_entry = AuditLog(
            id=generate_uuid(),
            tenant_id=tenant_id,
            actor_id=actor_id,
            actor_type=actor_type,
            action=action,
            resource_type=resource_type,
            resource_id=resource_id or generate_uuid(),
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            result=result,
            metadata_json=metadata or {}
        )
        db.add(audit_entry)
        await db.flush()
        return audit_entry

