from sqlalchemy.orm import Session
from app.core.exceptions.types import InvoiceParsingError
from app.db.models.accounts import Account
from app.db.models.service import AccountService, ServiceCredential
from app.db.session import SessionLocal
from app.services.admin.schemas import CredentialOut
from sqlalchemy import func


def get_credentials_for_user(user_id: int) -> list[CredentialOut]:
    db: Session = SessionLocal()
    try:
        encrypted_credentials = (
            db.query(ServiceCredential)
            .join(AccountService)
            .join(Account)
            .filter(Account.user_id == user_id)
            .order_by(ServiceCredential.account_service_id.asc())
            .all()
        )
        return [CredentialOut.from_orm_safe(c) for c in encrypted_credentials]
    finally:
        db.close()


def get_credential_by_key(user_id: int, key: str) -> CredentialOut:
    key = key.strip().lower()
    db: Session = SessionLocal()
    try:
        credential = (
            db.query(ServiceCredential)
            .join(AccountService)
            .join(Account)
            .filter(
                Account.user_id == user_id,
                func.lower(func.trim(ServiceCredential.key)) == key,
            )
            .order_by(ServiceCredential.account_service_id.asc())
            .first()
        )

        if not credential:
            raise InvoiceParsingError(
                message=f"No se encontró la credencial con clave '{key}'",
                status_code=404,
            )

        return CredentialOut.from_orm_safe(credential)

    finally:
        db.close()
