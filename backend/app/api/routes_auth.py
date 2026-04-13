import re
from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from backend.app.core.database import get_db
from backend.app.core import security
from backend.app.schemas.auth_schema import UserCreate, UserRead, Token
from backend.app.services.user_service import get_user_by_username, create_user

router = APIRouter()


@router.post('/register', response_model=UserRead)
def register(request: Request, user: UserCreate, db: Session = Depends(get_db)):
    # 1. Audit Logging: Who is making the request?
    client_host = request.client.host if request.client else "unknown"
    print(f"[SECURITY_AUDIT] Registration attempt | IP: {client_host} | Username: '{user.username}'")

    # 2. Strict Username Validation (Alphanumeric, 3-20 chars)
    # Prevents injection of scripts or weird characters
    if not re.match(r"^[a-zA-Z0-9_]{3,20}$", user.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username must be 3-20 characters and alphanumeric (underscores allowed)."
        )

    # 3. Password Complexity Check
    if not user.password or len(user.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters long."
        )
    
    # Optional: Prevent extremely common/weak passwords
    if user.password.lower() in ["password123", "qwertyuiop", "admin123"]:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This password is too common. Please choose a more secure one."
        )

    # 4. Idempotency / Duplicate Check
    existing = get_user_by_username(db, user.username)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken."
        )

    try:
        # 5. Secure Hashing (uses bcrypt_sha256 from security.py)
        hashed_pwd = security.hash_password(user.password)
    except Exception as e:
        print(f"[ERROR] Hashing failure: {str(e)}")
        raise HTTPException(status_code=500, detail="Internal server error during account creation.")

    # 6. Database Persistence
    new_user = create_user(db, user.username, hashed_pwd)
    return new_user


@router.post('/token', response_model=Token)
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):

    print(f"DEBUG: Login attempt for username: {form_data.username}")

    user = get_user_by_username(db, form_data.username)
    if not user or not security.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail='Incorrect username or password',
            headers={'WWW-Authenticate': 'Bearer'},
        )

    access_token = security.create_access_token(
        data={'sub': user.username}
    )
    return {'access_token': access_token, 'token_type': 'bearer'}


@router.get('/me', response_model=UserRead)
def read_users_me(current_user=Depends(security.get_current_user)):
    return current_user
