from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from models.user import Usuario
from models.session import Sesion
from models.metrics import ResultadoD1, ResultadoD2, ResultadoD3
from utils.auth import get_current_user

router = APIRouter(prefix="/metrics", tags=["metrics"])


@router.get("/historial")
def historial(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    sesiones = (
        db.query(Sesion)
        .filter(Sesion.usuario_id == current_user.id)
        .order_by(Sesion.created_at.desc())
        .limit(20)
        .all()
    )
    items = []
    for s in sesiones:
        d1 = s.resultado_d1
        d2 = s.resultado_d2
        d3 = s.resultado_d3
        # Recalcular score global si existen los tres
        score_global = None
        if d1 and d2 and d3:
            from services.scoring import calc_score_global
            sg = calc_score_global(
                score_d1=d1.score_d1 or 0.0,
                score_d2=d2.score_d2 or 0.0,
                score_d3=d3.score_d3 or 0.0,
            )
            score_global = sg["score_global"]
        items.append({
            "id":           s.id,
            "modo":         s.modo,
            "created_at":   s.created_at.isoformat(),
            "estrellas":    d1.estrellas if d1 else None,
            "ppm":          d1.ppm       if d1 else None,
            "long_pauses":  d1.long_pauses if d1 else None,
            "score_d1":     d1.score_d1  if d1 else None,
            "score_d2":     d2.score_d2  if d2 else None,
            "score_d3":     d3.score_d3  if d3 else None,
            "score_global": score_global,
        })
    return items


@router.get("/sesion/{sesion_id}")
def detalle_sesion(
    sesion_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    sesion = (
        db.query(Sesion)
        .filter(Sesion.id == sesion_id, Sesion.usuario_id == current_user.id)
        .first()
    )
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    d1 = sesion.resultado_d1
    d2 = sesion.resultado_d2
    d3 = sesion.resultado_d3
    return {
        "sesion_id": sesion_id,
        "d1": d1.feedback_json if d1 else None,
        "d2": d2.feedback_json if d2 else None,
        "d3": d3.feedback_json if d3 else None,
    }
