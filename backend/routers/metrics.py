from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy import func
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
    """Lista de alumnos con su resumen (nº prácticas, promedio global, última práctica).

    Optimizado: una sola consulta agregada (JOIN + GROUP BY) calcula el conteo, el promedio
    del puntaje global y la última práctica directamente en la base de datos, evitando el
    problema N+1 (cientos de consultas) que hacía lento el panel del docente.
    """
    # Puntaje global por sesión (mismos pesos que calc_score_global). Si falta alguna
    # dimensión, la expresión es NULL y AVG la ignora automáticamente.
    gscore = (0.40 * ResultadoD1.score_d1 + 0.35 * ResultadoD2.score_d2 + 0.25 * ResultadoD3.score_d3)

    filas = (
        db.query(
            Usuario.id, Usuario.nombre, Usuario.apellido, Usuario.grado, Usuario.seccion,
            func.count(Sesion.id).label("practicas"),
            func.avg(gscore).label("promedio"),
            func.max(Sesion.created_at).label("ultima"),
        )
        .outerjoin(Sesion, Sesion.usuario_id == Usuario.id)
        .outerjoin(ResultadoD1, ResultadoD1.sesion_id == Sesion.id)
        .outerjoin(ResultadoD2, ResultadoD2.sesion_id == Sesion.id)
        .outerjoin(ResultadoD3, ResultadoD3.sesion_id == Sesion.id)
        .filter(Usuario.rol == "alumno")
        .group_by(Usuario.id, Usuario.nombre, Usuario.apellido, Usuario.grado, Usuario.seccion)
        .order_by(Usuario.apellido, Usuario.nombre)
        .all()
    )
    return [
        {
            "id":        f.id,
            "nombre":    f.nombre,
            "apellido":  f.apellido,
            "grado":     f.grado,
            "seccion":   f.seccion,
            "practicas": f.practicas,
            "promedio":  round(f.promedio) if f.promedio is not None else None,
            "ultima":    f.ultima.isoformat() if f.ultima else None,
        }
        for f in filas
    ]


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
