from sqlalchemy import Column, Integer, Float, Text, ForeignKey, JSON
from sqlalchemy.orm import relationship
from database import Base


class ResultadoD1(Base):
    __tablename__ = "resultados_d1"

    id                = Column(Integer, primary_key=True, index=True)
    sesion_id         = Column(Integer, ForeignKey("sesiones.id"), unique=True, nullable=False)
    transcripcion     = Column(Text)
    ppm               = Column(Float)
    word_count        = Column(Integer)
    speech_duration_s = Column(Float)
    total_pauses      = Column(Integer)
    long_pauses       = Column(Integer)
    avg_pause_s       = Column(Float)
    f0_mean_hz        = Column(Float, nullable=True)
    f0_std_hz         = Column(Float, nullable=True)
    jitter_pct        = Column(Float, nullable=True)
    shimmer_db        = Column(Float, nullable=True)
    hnr_db            = Column(Float, nullable=True)
    intensity_mean_db = Column(Float, nullable=True)
    estrellas         = Column(Integer)
    score_d1          = Column(Float, nullable=True)
    feedback_json     = Column(JSON)

    sesion = relationship("Sesion", back_populates="resultado_d1")


class ResultadoD2(Base):
    __tablename__ = "resultados_d2"

    id                = Column(Integer, primary_key=True, index=True)
    sesion_id         = Column(Integer, ForeignKey("sesiones.id"), unique=True, nullable=False)
    muletillas_count  = Column(Integer, default=0)
    muletillas_tasa   = Column(Float,   default=0.0)
    muletillas_tipos  = Column(JSON,    nullable=True)   # lista de tipos detectados
    ttr_score         = Column(Float,   nullable=True)
    unique_words      = Column(Integer, nullable=True)
    coherencia_score  = Column(Float,   nullable=True)
    score_d2          = Column(Float,   nullable=True)
    estrellas         = Column(Integer, nullable=True)
    feedback_json     = Column(JSON,    nullable=True)

    sesion = relationship("Sesion", back_populates="resultado_d2")


class ResultadoD3(Base):
    __tablename__ = "resultados_d3"

    id                   = Column(Integer, primary_key=True, index=True)
    sesion_id            = Column(Integer, ForeignKey("sesiones.id"), unique=True, nullable=False)
    variacion_tonal_pts  = Column(Float, nullable=True)
    calidad_hnr_pts      = Column(Float, nullable=True)
    volumen_pts          = Column(Float, nullable=True)
    score_d3             = Column(Float, nullable=True)
    estrellas            = Column(Integer, nullable=True)
    feedback_json        = Column(JSON, nullable=True)

    sesion = relationship("Sesion", back_populates="resultado_d3")
