from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from database import get_db
from models.user import Usuario
from schemas.auth import RegisterRequest, LoginRequest, TokenResponse, UserResponse
from utils.auth import hash_password, verify_password, create_token, get_current_user

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(body: RegisterRequest, db: Session = Depends(get_db)):
    if db.query(Usuario).filter(Usuario.username == body.username).first():
        raise HTTPException(status_code=400, detail="El nombre de usuario ya existe")

    user = Usuario(
        nombre=body.nombre,
        apellido=body.apellido,
        username=body.username,
        password_hash=hash_password(body.password),
        rol=body.rol or "alumno",
        grado=body.grado,
        seccion=body.seccion,
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    return TokenResponse(
        access_token=create_token(user.id, user.rol),
        user=UserResponse.model_validate(user),
    )


@router.post("/login", response_model=TokenResponse)
def login(body: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(Usuario).filter(Usuario.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Usuario o contrasena incorrectos")

    return TokenResponse(
        access_token=create_token(user.id, user.rol),
        user=UserResponse.model_validate(user),
    )


@router.get("/me", response_model=UserResponse)
def me(current_user: Usuario = Depends(get_current_user)):
    return current_user
