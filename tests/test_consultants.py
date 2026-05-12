from models import Consultant


def test_list_consultants_empty(client):
    response = client.get("/consultants")
    assert response.status_code == 200


def test_new_consultant_form_get(client):
    response = client.get("/consultants/new")
    assert response.status_code == 200


def test_create_consultant_ok(client, app):
    client.post(
        "/consultants/new",
        data={"name": "Ada", "email": "ada@x.com", "role": "Dev", "active": "on"},
        follow_redirects=True,
    )
    with app.app_context():
        created = Consultant.query.filter_by(name="Ada").first()
        assert created is not None
        assert created.email == "ada@x.com"
        assert created.role == "Dev"
        assert created.active is True


def test_create_consultant_requires_name(client, app):
    client.post("/consultants/new", data={"name": ""})
    with app.app_context():
        assert Consultant.query.count() == 0


def test_create_consultant_rejects_name_too_long(client, app):
    client.post("/consultants/new", data={"name": "n" * 121})
    with app.app_context():
        assert Consultant.query.count() == 0


def test_create_consultant_rejects_duplicate(client, app, make_consultant):
    make_consultant(name="Grace")
    client.post("/consultants/new", data={"name": "Grace"})
    with app.app_context():
        assert Consultant.query.filter_by(name="Grace").count() == 1


def test_edit_consultant_updates(client, app, make_consultant):
    c = make_consultant(name="Antes")
    client.post(
        f"/consultants/{c.id}/edit",
        data={"name": "Despues", "email": "d@d.com", "active": "on"},
        follow_redirects=True,
    )
    with app.app_context():
        updated = Consultant.query.get(c.id)
        assert updated.name == "Despues"
        assert updated.email == "d@d.com"


def test_edit_consultant_rejects_duplicate(client, app, make_consultant):
    make_consultant(name="A")
    b = make_consultant(name="B")
    client.post(f"/consultants/{b.id}/edit", data={"name": "A"})
    with app.app_context():
        assert Consultant.query.get(b.id).name == "B"


def test_edit_consultant_404(client):
    assert client.get("/consultants/9999/edit").status_code == 404


def test_delete_consultant(client, app, make_consultant):
    c = make_consultant(name="ParaBorrar")
    client.post(f"/consultants/{c.id}/delete", follow_redirects=True)
    with app.app_context():
        assert Consultant.query.get(c.id) is None
