"""Pruebas de control de acceso por rol (RBAC) y panel del docente."""


def _registrar_docente(client):
    client.post("/auth/register", json={
        "nombre": "Carlos", "apellido": "Ruiz", "username": "prof_carlos",
        "password": "clave12345", "rol": "docente",
    })
    r = client.post("/auth/login", json={"username": "prof_carlos", "password": "clave12345"})
    return {"Authorization": f"Bearer {r.json()['access_token']}"}


def test_registro_docente_devuelve_rol(client):
    r = client.post("/auth/register", json={
        "nombre": "Carlos", "apellido": "Ruiz", "username": "prof_carlos",
        "password": "clave12345", "rol": "docente",
    })
    assert r.status_code == 201
    assert r.json()["user"]["rol"] == "docente"


def test_alumno_no_accede_a_panel_docente(client, auth_headers):
    # auth_headers es un alumno → debe recibir 403
    r = client.get("/metrics/docente/alumnos", headers=auth_headers)
    assert r.status_code == 403


def test_docente_ve_lista_de_alumnos(client, auth_headers):
    # auth_headers crea el alumno "Ana Perez"; el docente debe verlo en su lista
    headers_doc = _registrar_docente(client)
    r = client.get("/metrics/docente/alumnos", headers=headers_doc)
    assert r.status_code == 200
    nombres = [a["nombre"] for a in r.json()]
    assert "Ana" in nombres


def test_rol_invalido_rechazado(client):
    r = client.post("/auth/register", json={
        "nombre": "Test", "apellido": "User", "username": "test_rol",
        "password": "clave12345", "rol": "admin",
    })
    assert r.status_code == 422
