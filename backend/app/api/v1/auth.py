from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.core.security import verify_password, get_password_hash, create_access_token
from app.models.models import User, Tenant, UserRole
from app.schemas.schemas import UserLogin, Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: AsyncSession = Depends(get_db)):
    stmt = select(User).where(User.email == credentials.email)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()
    
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
        
    access_token = create_access_token(
        data={"sub": user.id, "role": user.role.value, "tenant_id": user.tenant_id}
    )
    
    return Token(
        access_token=access_token,
        token_type="bearer",
        role=user.role,
        tenant_id=user.tenant_id,
        user_id=user.id
    )

@router.post("/seed-demo-accounts")
async def seed_demo_accounts(db: AsyncSession = Depends(get_db)):
    """Seed initial Tenant and Demo Accounts for Bank Officers and Reviewers"""
    # 1. Create Default Bank Tenant if not exists
    stmt = select(Tenant).where(Tenant.code == "BANK_ABC")
    res = await db.execute(stmt)
    tenant = res.scalar_one_or_none()
    
    if not tenant:
        tenant = Tenant(
            name="Bank ABC International",
            code="BANK_ABC",
            webhook_url="https://webhook.site/demo-bank-abc",
            webhook_secret="sec_bank_abc_98765"
        )
        db.add(tenant)
        await db.flush()

    # 2. Seed Reviewer Account
    stmt_user = select(User).where(User.email == "reviewer@bankabc.com")
    res_user = await db.execute(stmt_user)
    reviewer = res_user.scalar_one_or_none()
    
    if not reviewer:
        reviewer = User(
            tenant_id=tenant.id,
            email="reviewer@bankabc.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Priya Sharma (Senior KYC Officer)",
            role=UserRole.REVIEWER
        )
        db.add(reviewer)

    # 3. Seed Admin Account
    stmt_admin = select(User).where(User.email == "admin@bankabc.com")
    res_admin = await db.execute(stmt_admin)
    admin = res_admin.scalar_one_or_none()
    
    if not admin:
        admin = User(
            tenant_id=tenant.id,
            email="admin@bankabc.com",
            hashed_password=get_password_hash("Password123!"),
            full_name="Rajesh Verma (Head of Compliance)",
            role=UserRole.TENANT_ADMIN
        )
        db.add(admin)
        
    await db.commit()
    return {"message": "Demo tenant and accounts seeded successfully", "tenant_id": tenant.id}
