"""Pruebas de integración — /auth"""


def test_register_ok(client):
    r = client.post("/auth/register", json={
        "nombre": "Luis", "apellido": "Gomez", "username": "luis1",
        "password": "clave12345", "grado": "1", "seccion": "B",
    })
    assert r.status_code == 201
    body = r.json()
    assert "access_token" in body
    assert body["user"]["username"] == "luis1"
    # nunca debe exponer la contraseña
    assert "password" not in body["user"]
    assert "password_hash" not in body["user"]


def test_register_username_duplicado(client):
    payload = {"nombre": "A", "apellido": "B", "username": "dup", "password": "clave12345"}
    assert client.post("/auth/register", json=payload).status_code == 201
    assert client.post("/auth/register", json=payload).status_code == 400


def test_login_ok(client):
    client.post("/auth/register", json={"nombre": "A", "apellido": "B", "username": "log1", "password": "clave12345"})
    r = client.post("/auth/login", json={"username": "log1", "password": "clave12345"})
    assert r.status_code == 200
    assert "access_token" in r.json()


def test_login_password_incorrecta(client):
    client.post("/auth/register", json={"nombre": "A", "apellido": "B", "username": "log2", "password": "clave12345"})
    r = client.post("/auth/login", json={"username": "log2", "password": "incorrecta"})
    assert r.status_code == 401


def test_me_requiere_token(client):
    assert client.get("/auth/me").status_code == 401


def test_me_con_token(client, auth_headers):
    r = client.get("/auth/me", headers=auth_headers)
    assert r.status_code == 200
    assert r.json()["username"] == "ana_test"
