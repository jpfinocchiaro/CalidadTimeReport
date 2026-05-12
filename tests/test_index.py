from datetime import date

from models import db, TimeEntry


def test_index_ok_empty(client):
    response = client.get("/")
    assert response.status_code == 200


def test_index_totals_count_records(client, make_client, make_consultant, make_project, make_entry):
    make_client(name="A")
    make_client(name="B")
    make_consultant(name="Ada")
    project = make_project(name="P1")
    make_entry(project=project, hours=3.5)
    make_entry(project=project, hours=4.0)

    response = client.get("/")
    body = response.get_data(as_text=True)

    assert response.status_code == 200
    # Total acumulado = 7.5 horas
    total_hours = db.session.query(TimeEntry).count()
    assert total_hours == 2
