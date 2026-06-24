import re
from pydantic import BaseModel, field_validator
from typing import Optional

_RE_NOMBRE   = re.compile(r"^[A-Za-zÁÉÍÓÚáéíóúÑñÜü ]+$")   # letras y espacios (con tildes/ñ)
_RE_USERNAME = re.compile(r"^[A-Za-z0-9._]+$")              # letras, numeros, punto, guion bajo
_RE_GRADO    = re.compile(r"^[A-Za-z0-9°º]+$")
_RE_SECCION  = re.compile(r"^[A-Za-z]{1,2}$")


class RegisterRequest(BaseModel):
    nombre: str
    apellido: str
    username: str
    password: str
    rol: Optional[str] = "alumno"
    grado: Optional[str] = None
    seccion: Optional[str] = None

    @field_validator("rol")
    @classmethod
    def _valida_rol(cls, v: Optional[str]) -> str:
        v = (v or "alumno").strip().lower()
        if v not in ("alumno", "docente"):
            raise ValueError("Rol invalido.")
        return v

    @field_validator("nombre", "apellido")
    @classmethod
    def _valida_nombre(cls, v: str) -> str:
        v = (v or "").strip()
        if not (2 <= len(v) <= 50):
            raise ValueError("El nombre y apellido deben tener entre 2 y 50 caracteres.")
        if not _RE_NOMBRE.match(v):
            raise ValueError("El nombre y apellido solo pueden contener letras y espacios.")
        return v

    @field_validator("username")
    @classmethod
    def _valida_username(cls, v: str) -> str:
        v = (v or "").strip()
        if not (3 <= len(v) <= 30):
            raise ValueError("El usuario debe tener entre 3 y 30 caracteres.")
        if not _RE_USERNAME.match(v):
            raise ValueError("El usuario solo puede contener letras, numeros, punto y guion bajo.")
        return v

    @field_validator("password")
    @classmethod
    def _valida_password(cls, v: str) -> str:
        if not (6 <= len(v or "") <= 128):
            raise ValueError("La contrasena debe tener entre 6 y 128 caracteres.")
        return v

    @field_validator("grado")
    @classmethod
    def _valida_grado(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip()
        if v == "":
            return None
        if len(v) > 10 or not _RE_GRADO.match(v):
            raise ValueError("Grado invalido (maximo 10 caracteres; letras y numeros, ej. 1ro).")
        return v

    @field_validator("seccion")
    @classmethod
    def _valida_seccion(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        v = v.strip().upper()
        if v == "":
            return None
        if not _RE_SECCION.match(v):
            raise ValueError("Seccion invalida (1 o 2 letras, ej. A).")
        return v


class LoginRequest(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    id: int
    nombre: str
    apellido: str
    username: str
    rol: str
    grado: Optional[str]
    seccion: Optional[str]

    class Config:
        from_attributes = True


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse
