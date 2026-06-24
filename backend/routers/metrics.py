from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from database import get_db
from models.user import Usuario
from models.session import Sesion
from models.metrics import ResultadoD1, ResultadoD2, ResultadoD3
from utils.auth import get_current_user, require_docente

router = APIRouter(prefix="/metrics", tags=["metrics"])


def _score_global(d1, d2, d3):
    if d1 and d2 and d3:
        from services.scoring import calc_score_global
        return calc_score_global(
            score_d1=d1.score_d1 or 0.0,
            score_d2=d2.score_d2 or 0.0,
            score_d3=d3.score_d3 or 0.0,
        )["score_global"]
    return None


def _serializar(sesiones):
    items = []
    for s in sesiones:
        d1, d2, d3 = s.resultado_d1, s.resultado_d2, s.resultado_d3
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
            "score_global": _score_global(d1, d2, d3),
        })
    return items


@router.get("/historial")
def historial(current_user: Usuario = Depends(get_current_user), db: Session = Depends(get_db)):
    sesiones = (
        db.query(Sesion)
        .filter(Sesion.usuario_id == current_user.id)
        .order_by(Sesion.created_at.desc())
        .limit(20)
        .all()
    )
    return _serializar(sesiones)


@router.get("/docente/alumnos")
def docente_alumnos(current_user: Usuario = Depends(require_docente), db: Session = Depends(get_db)):
    """Lista de alumnos con su resumen (nº prácticas, promedio global, última práctica)."""
    alumnos = (
        db.query(Usuario)
        .filter(Usuario.rol == "alumno")
        .order_by(Usuario.apellido, Usuario.nombre)
        .all()
    )
    out = []
    for a in alumnos:
        sesiones = db.query(Sesion).filter(Sesion.usuario_id == a.id).all()
        scores = [g for g in (_score_global(s.resultado_d1, s.resultado_d2, s.resultado_d3) for s in sesiones) if g is not None]
        out.append({
            "id":        a.id,
            "nombre":    a.nombre,
            "apellido":  a.apellido,
            "grado":     a.grado,
            "seccion":   a.seccion,
            "practicas": len(sesiones),
            "promedio":  round(sum(scores) / len(scores)) if scores else None,
            "ultima":    max((s.created_at for s in sesiones), default=None).isoformat() if sesiones else None,
        })
    return out


@router.get("/docente/alumno/{alumno_id}")
def docente_alumno_detalle(
    alumno_id: int,
    current_user: Usuario = Depends(require_docente),
    db: Session = Depends(get_db),
):
    """Historial de prácticas de un alumno (para el panel del docente)."""
    alumno = db.query(Usuario).filter(Usuario.id == alumno_id).first()
    if not alumno:
        raise HTTPException(status_code=404, detail="Alumno no encontrado")
    sesiones = (
        db.query(Sesion)
        .filter(Sesion.usuario_id == alumno_id)
        .order_by(Sesion.created_at.desc())
        .limit(50)
        .all()
    )
    return {
        "alumno": {
            "id": alumno.id, "nombre": alumno.nombre, "apellido": alumno.apellido,
            "grado": alumno.grado, "seccion": alumno.seccion,
        },
        "sesiones": _serializar(sesiones),
    }


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


@router.get("/reporte/{sesion_id}")
def reporte_pdf(
    sesion_id: int,
    current_user: Usuario = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """Genera y descarga el reporte PDF de una sesión. El docente puede ver cualquiera;
    el alumno solo las suyas."""
    sesion = db.query(Sesion).filter(Sesion.id == sesion_id).first()
    if not sesion:
        raise HTTPException(status_code=404, detail="Sesion no encontrada")
    if current_user.rol != "docente" and sesion.usuario_id != current_user.id:
        raise HTTPException(status_code=403, detail="No autorizado")

    d1, d2, d3 = sesion.resultado_d1, sesion.resultado_d2, sesion.resultado_d3
    usuario = sesion.usuario

    score_global = None
    if d1 and d2 and d3:
        from services.scoring import calc_score_global
        score_global = calc_score_global(
            score_d1=d1.score_d1 or 0.0,
            score_d2=d2.score_d2 or 0.0,
            score_d3=d3.score_d3 or 0.0,
        )["score_global"]

    from services.report_pdf import build_session_report
    pdf = build_session_report(sesion, d1, d2, d3, usuario, score_global)
    return Response(
        content=pdf,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="reporte_sesion_{sesion_id}.pdf"'},
    )
