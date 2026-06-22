from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Enum, Text
from sqlalchemy.orm import relationship
from database import Base


class TextoLectura(Base):
    __tablename__ = "textos_lectura"

    id         = Column(Integer, primary_key=True, index=True)
    titulo     = Column(String(200), nullable=False)
    contenido  = Column(Text, nullable=False)
    nivel      = Column(String(50), default="1ro_primaria")
    created_at = Column(DateTime, default=datetime.utcnow)


class Sesion(Base):
    __tablename__ = "sesiones"

    id          = Column(Integer, primary_key=True, index=True)
    usuario_id  = Column(Integer, ForeignKey("usuarios.id"), nullable=False)
    modo        = Column(Enum("lectura", "libre", name="modo_enum"), nullable=False)
    texto_id    = Column(Integer, ForeignKey("textos_lectura.id"), nullable=True)
    created_at  = Column(DateTime, default=datetime.utcnow)

    usuario      = relationship("Usuario",     back_populates="sesiones")
    resultado_d1 = relationship("ResultadoD1", back_populates="sesion", uselist=False)
    resultado_d2 = relationship("ResultadoD2", back_populates="sesion", uselist=False)
    resultado_d3 = relationship("ResultadoD3", back_populates="sesion", uselist=False)
    texto        = relationship("TextoLectura")
