from datetime import date


def test_reports_ok_empty(client):
    assert client.get("/reports").status_code == 200


def test_reports_filter_by_date_range(client, app, make_project, make_entry):
    p = make_project(name="P1")
    make_entry(project=p, entry_date=date(2026, 1, 1), hours=2, person="A")
    make_entry(project=p, entry_date=date(2026, 6, 1), hours=5, person="A")
    make_entry(project=p, entry_date=date(2026, 12, 1), hours=3, person="A")

    response = client.get("/reports?from=2026-05-01&to=2026-12-31")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    # debería ver 5 + 3 = 8 (no 2)
    assert "8" in body


def test_reports_filter_by_client(client, app, make_client, make_project, make_entry):
    c1 = make_client(name="C1")
    c2 = make_client(name="C2")
    p1 = make_project(name="P1", client=c1)
    p2 = make_project(name="P2", client=c2)
    make_entry(project=p1, hours=10, person="A")
    make_entry(project=p2, hours=20, person="B")

    response = client.get(f"/reports?client_id={c1.id}")
    assert response.status_code == 200
    body = response.get_data(as_text=True)
    assert "C1" in body
    assert "10" in body


def test_reports_grand_total(client, app, make_project, make_entry):
    p = make_project(name="P1")
    make_entry(project=p, hours=1.5, person="A")
    make_entry(project=p, hours=2.5, person="B")
    response = client.get("/reports")
    body = response.get_data(as_text=True)
    assert "4" in body  # 1.5 + 2.5 = 4.0
