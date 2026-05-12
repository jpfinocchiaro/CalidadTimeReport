from models import Client


def test_list_clients_empty(client):
    response = client.get("/clients")
    assert response.status_code == 200


def test_new_client_form_get(client):
    response = client.get("/clients/new")
    assert response.status_code == 200


def test_create_client_ok(client, app):
    response = client.post(
        "/clients/new",
        data={"name": "ACME", "contact": "ana@acme.com", "notes": "vip", "active": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        created = Client.query.filter_by(name="ACME").first()
        assert created is not None
        assert created.contact == "ana@acme.com"
        assert created.active is True


def test_create_client_inactive_when_checkbox_missing(client, app):
    client.post("/clients/new", data={"name": "Inactivo"})
    with app.app_context():
        created = Client.query.filter_by(name="Inactivo").first()
        assert created is not None
        assert created.active is False


def test_create_client_requires_name(client, app):
    response = client.post("/clients/new", data={"name": "   "})
    assert response.status_code == 200
    with app.app_context():
        assert Client.query.count() == 0


def test_create_client_rejects_name_too_long(client, app):
    response = client.post("/clients/new", data={"name": "x" * 121})
    assert response.status_code == 200
    with app.app_context():
        assert Client.query.count() == 0


def test_create_client_rejects_duplicate_name(client, app, make_client):
    make_client(name="Duplicado")
    response = client.post("/clients/new", data={"name": "Duplicado"})
    assert response.status_code == 200
    with app.app_context():
        assert Client.query.filter_by(name="Duplicado").count() == 1


def test_edit_client_404_on_missing(client):
    response = client.get("/clients/9999/edit")
    assert response.status_code == 404


def test_edit_client_updates_fields(client, app, make_client):
    c = make_client(name="Antes", contact="x@x.com")
    response = client.post(
        f"/clients/{c.id}/edit",
        data={"name": "Despues", "contact": "y@y.com", "active": "on"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        updated = Client.query.get(c.id)
        assert updated.name == "Despues"
        assert updated.contact == "y@y.com"


def test_edit_client_rejects_duplicate_name(client, app, make_client):
    make_client(name="A")
    b = make_client(name="B")
    response = client.post(f"/clients/{b.id}/edit", data={"name": "A"})
    assert response.status_code == 200
    with app.app_context():
        assert Client.query.get(b.id).name == "B"


def test_edit_client_keeps_same_name_allowed(client, app, make_client):
    c = make_client(name="Igual", contact="old@x.com")
    response = client.post(
        f"/clients/{c.id}/edit",
        data={"name": "Igual", "contact": "new@x.com"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    with app.app_context():
        assert Client.query.get(c.id).contact == "new@x.com"


def test_delete_client_removes_record(client, app, make_client):
    c = make_client(name="ParaBorrar")
    response = client.post(f"/clients/{c.id}/delete", follow_redirects=True)
    assert response.status_code == 200
    with app.app_context():
        assert Client.query.get(c.id) is None


def test_delete_client_cascades_to_projects(client, app, make_client, make_project):
    from models import Project
    c = make_client(name="ConProyectos")
    make_project(name="P1", client=c)
    make_project(name="P2", client=c)
    client.post(f"/clients/{c.id}/delete")
    with app.app_context():
        assert Project.query.count() == 0


def test_delete_client_404_on_missing(client):
    response = client.post("/clients/9999/delete")
    assert response.status_code == 404
