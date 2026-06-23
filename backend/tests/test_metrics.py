"""Pruebas de integración — /metrics/historial"""

FILES = {"file": ("audio.webm", b"fakebytes", "audio/webm")}


def test_historial_requiere_auth(client):
    assert client.get("/metrics/historial").status_code == 401


def test_historial_vacio(client, auth_headers):
    r = client.get("/metrics/historial", headers=auth_headers)
    assert r.status_code == 200
    assert r.json() == []


def test_historial_refleja_sesion(client, auth_headers, mock_pipeline):
    mock_pipeline("hola soy ana y me gusta leer cuentos en el colegio")
    client.post("/audio/analizar", data={"modo": "libre"}, files=FILES, headers=auth_headers)

    r = client.get("/metrics/historial", headers=auth_headers)
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["modo"] == "libre"
    assert items[0]["ppm"] is not None
