from models import Project


def test_list_projects_empty(client):
    response = client.get("/projects").status_code
    assert response == 200


def test_new_project_redirects_when_no_active_clients(client, app, make_client):
    make_client(name="Inactivo", active=False)
    response = client.get("/projects/new", follow_redirects=False)
    assert response.status_code == 302
    assert "/clients" in response.headers["Location"]


def test_new_project_form_get(client, make_client):
    make_client(name="ACME")
    response = client.get("/projects/new")
    assert response.status_code == 200


def test_create_project_ok(client, app, make_client):
    c = make_client(name="ACME")
    client.post(
        "/projects/new",
        data={
            "name": "Web",
            "code": "WEB-1",
            "description": "Sitio",
            "client_id": str(c.id),
            "active": "on",
        },
        follow_redirects=True,
    )
    with app.app_context():
        p = Project.query.filter_by(name="Web").first()
        assert p is not None
        assert p.client_id == c.id
        assert p.code == "WEB-1"
        assert p.active is True


def test_create_project_assigns_consultants(client, app, make_client, make_consultant):
    c = make_client(name="ACME")
    a = make_consultant(name="Ada")
    g = make_consultant(name="Grace")
    client.post(
        "/projects/new",
        data={
            "name": "P1",
            "client_id": str(c.id),
            "consultant_ids": [str(a.id), str(g.id)],
            "active": "on",
        },
        follow_redirects=True,
    )
    with app.app_context():
        p = Project.query.filter_by(name="P1").first()
        assert {x.name for x in p.consultants} == {"Ada", "Grace"}


def test_create_project_requires_name(client, app, make_client):
    c = make_client()
    client.post("/projects/new", data={"name": "", "client_id": str(c.id)})
    with app.app_context():
        assert Project.query.count() == 0


def test_create_project_requires_client(client, app, make_client):
    make_client(name="A")
    client.post("/projects/new", data={"name": "Sin cliente"})
    with app.app_context():
        assert Project.query.count() == 0


def test_create_project_rejects_unknown_client(client, app, make_client):
    make_client(name="A")
    client.post("/projects/new", data={"name": "Huérfano", "client_id": "9999"})
    with app.app_context():
        assert Project.query.count() == 0


def test_edit_project_updates(client, app, make_project):
    p = make_project(name="Antes")
    client.post(
        f"/projects/{p.id}/edit",
        data={"name": "Despues", "client_id": str(p.client_id), "active": "on"},
        follow_redirects=True,
    )
    with app.app_context():
        assert Project.query.get(p.id).name == "Despues"


def test_edit_project_replaces_consultants(client, app, make_project, make_consultant):
    a = make_consultant(name="Ada")
    g = make_consultant(name="Grace")
    p = make_project(name="P1", consultants=[a])
    client.post(
        f"/projects/{p.id}/edit",
        data={
            "name": "P1",
            "client_id": str(p.client_id),
            "consultant_ids": [str(g.id)],
            "active": "on",
        },
    )
    with app.app_context():
        refreshed = Project.query.get(p.id)
        assert {c.name for c in refreshed.consultants} == {"Grace"}


def test_edit_project_404(client):
    assert client.get("/projects/9999/edit").status_code == 404


def test_delete_project(client, app, make_project):
    p = make_project(name="ParaBorrar")
    client.post(f"/projects/{p.id}/delete", follow_redirects=True)
    with app.app_context():
        assert Project.query.get(p.id) is None
