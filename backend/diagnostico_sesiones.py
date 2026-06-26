"""
Diagnóstico de SOLO LECTURA del histórico de sesiones.

Cuenta cuántas sesiones ya guardadas serían inválidas según el criterio actual
(< MIN_PALABRAS palabras o < MIN_DURACION_HABLA_S segundos de habla) y muestra
el puntaje inflado que recibieron. NO modifica ni borra absolutamente nada.

Ejecutar:  python diagnostico_sesiones.py
"""
from database import SessionLocal
from models.session import Sesion
from models.metrics import ResultadoD1, ResultadoD2, ResultadoD3
from services.validation import es_sesion_valida, MIN_PALABRAS, MIN_DURACION_HABLA_S


def main():
    db = SessionLocal()
    try:
        d1s = db.query(ResultadoD1).all()
        total = len(d1s)
        if total == 0:
            print("No hay sesiones registradas.")
            return

        invalidas = []
        for d1 in d1s:
            wc = d1.word_count or 0
            dur = d1.speech_duration_s or 0.0
            if not es_sesion_valida(wc, dur):
                d2 = db.query(ResultadoD2).filter_by(sesion_id=d1.sesion_id).first()
                d3 = db.query(ResultadoD3).filter_by(sesion_id=d1.sesion_id).first()
                ses = db.query(Sesion).filter_by(id=d1.sesion_id).first()
                invalidas.append({
                    "sesion_id": d1.sesion_id,
                    "usuario_id": ses.usuario_id if ses else None,
                    "fecha": ses.created_at if ses else None,
                    "palabras": wc,
                    "habla_s": round(dur, 1),
                    "d1": d1.score_d1,
                    "d2": d2.score_d2 if d2 else None,
                    "d3": d3.score_d3 if d3 else None,
                })

        print(f"Criterio de validez: >= {MIN_PALABRAS} palabras Y >= {MIN_DURACION_HABLA_S:.0f}s de habla\n")
        print(f"Total de sesiones:        {total}")
        print(f"Sesiones INVÁLIDAS:       {len(invalidas)}  ({len(invalidas)*100//total}%)")
        print(f"Sesiones válidas:         {total - len(invalidas)}\n")

        if invalidas:
            print("Detalle de sesiones inválidas (puntaje inflado que recibieron):")
            print(f"  {'sesion':>7} {'user':>5} {'palabras':>9} {'habla_s':>8} {'D1':>6} {'D2':>6} {'D3':>6}")
            for x in invalidas:
                print(f"  {x['sesion_id']:>7} {str(x['usuario_id']):>5} "
                      f"{x['palabras']:>9} {x['habla_s']:>8} "
                      f"{str(x['d1']):>6} {str(x['d2']):>6} {str(x['d3']):>6}")

        print("\n(Este script NO modificó ni borró nada. Solo lectura.)")
    finally:
        db.close()


if __name__ == "__main__":
    main()
