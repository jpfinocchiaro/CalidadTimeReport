from datetime import date

from models import TimeEntry


def test_list_hours_empty(client):
    assert client.get("/hours").status_code == 200


def test_new_hours_redirects_when_no_active_projects(client, app, make_project):
    make_project(name="Inactivo", active=False)
    response = client.get("/hours/new", follow_redirects=False)
    assert response.status_code == 302
    assert "/projects" in response.headers["Location"]


def test_new_hours_form_get(client, make_project):
    make_project(name="P1")
    assert client.get("/hours/new").status_code == 200


def test_create_hours_ok(client, app, make_project):
    p = make_project(name="P1")
    client.post(
        "/hours/new",
        data={
            "entry_date": "2026-01-15",
            "hours": "4.5",
            "description": "tarea",
            "person": "Juan",
            "project_id": str(p.id),
        },
        follow_redirects=True,
    )
    with app.app_context():
        e = TimeEntry.query.first()
        assert e is not None
        assert e.hours == 4.5
        assert e.entry_date == date(2026, 1, 15)
        assert e.person == "Juan"


def test_create_hours_accepts_comma_decimal(client, app, make_project):
    p = make_project(name="P1")
    client.post(
        "/hours/new",
        data={
            "entry_date": "2026-01-15",
            "hours": "3,25",
            "person": "Ana",
            "project_id": str(p.id),
        },
    )
    with app.app_context():
        assert TimeEntry.query.first().hours == 3.25


def test_create_hours_rejects_invalid_date(client, app, make_project):
    p = make_project()
    client.post(
        "/hours/new",
        data={"entry_date": "no-fecha", "hours": "1", "person": "Juan", "project_id": str(p.id)},
    )
    with app.app_context():
        assert TimeEntry.query.count() == 0


def test_create_hours_rejects_non_numeric_hours(client, app, make_project):
    p = make_project()
    client.post(
        "/hours/new",
        data={"entry_date": "2026-01-15", "hours": "abc", "person": "Juan", "project_id": str(p.id)},
    )
    with app.app_context():
        assert TimeEntry.query.count() == 0


def test_create_hours_rejects_zero_or_negative(client, app, make_project):
    p = make_project()
    for bad in ("0", "-1.5"):
        client.post(
            "/hours/new",
            data={"entry_date": "2026-01-15", "hours": bad, "person": "Juan", "project_id": str(p.id)},
        )
    with app.app_context():
        assert TimeEntry.query.count() == 0


def test_create_hours_requires_person(client, app, make_project):
    p = make_project()
    client.post(
        "/hours/new",
        data={"entry_date": "2026-01-15", "hours": "1", "person": "  ", "project_id": str(p.id)},
    )
    with app.app_context():
        assert TimeEntry.query.count() == 0


def test_create_hours_rejects_unknown_project(client, app, make_project):
    make_project()
    client.post(
        "/hours/new",
        data={"entry_date": "2026-01-15", "hours": "1", "person": "X", "project_id": "9999"},
    )
    with app.app_context():
        assert TimeEntry.query.count() == 0


def test_edit_hours_updates(client, app, make_entry):
    e = make_entry(hours=2.0, person="Antes")
    client.post(
        f"/hours/{e.id}/edit",
        data={
            "entry_date": "2026-02-01",
            "hours": "8",
            "person": "Despues",
            "project_id": str(e.project_id),
        },
        follow_redirects=True,
    )
    with app.app_context():
        refreshed = TimeEntry.query.get(e.id)
        assert refreshed.hours == 8
        assert refreshed.person == "Despues"
        assert refreshed.entry_date == date(2026, 2, 1)


def test_edit_hours_404(client):
    assert client.get("/hours/9999/edit").status_code == 404


def test_delete_hours(client, app, make_entry):
    e = make_entry()
    client.post(f"/hours/{e.id}/delete", follow_redirects=True)
    with app.app_context():
        assert TimeEntry.query.get(e.id) is None
