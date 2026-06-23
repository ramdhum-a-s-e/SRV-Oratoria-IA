"""Pruebas de integración — /audio/analizar (pipeline de IA mockeado)"""

FILES = {"file": ("audio.webm", b"fakebytes", "audio/webm")}


def test_analizar_requiere_auth(client):
    r = client.post("/audio/analizar", data={"modo": "libre"}, files=FILES)
    assert r.status_code == 401


def test_analizar_modo_libre(client, auth_headers, mock_pipeline):
    mock_pipeline("hola yo soy ana y me gusta leer cuentos")
    r = client.post("/audio/analizar", data={"modo": "libre"}, files=FILES, headers=auth_headers)
    assert r.status_code == 200
    body = r.json()
    for clave in ("sesion_id", "transcripcion", "ppm", "pausas", "d2", "d3", "score_global"):
        assert clave in body
    # en modo libre no se calcula fidelidad de lectura
    assert body["lectura"] is None


def test_analizar_modo_lectura_fidelidad(client, auth_headers, db_session, mock_pipeline):
    from models.session import TextoLectura
    texto = TextoLectura(titulo="Prueba", contenido="el gato corre en el parque")
    db_session.add(texto)
    db_session.commit()
    tid = texto.id

    # el alumno "lee" exactamente el texto → fidelidad 100%
    mock_pipeline("el gato corre en el parque")
    r = client.post(
        "/audio/analizar",
        data={"modo": "lectura", "texto_id": str(tid)},
        files=FILES, headers=auth_headers,
    )
    assert r.status_code == 200
    lectura = r.json()["lectura"]
    assert lectura is not None
    assert lectura["fidelidad_score"] == 100.0
    assert lectura["nivel"] == "excelente"
