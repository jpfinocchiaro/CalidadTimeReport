import sys
from pathlib import Path

import pytest
from flask import Flask

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from models import db, Client, Consultant, Project, TimeEntry  # noqa: E402
from app import register_routes  # noqa: E402


@pytest.fixture
def app():
    test_app = Flask(
        __name__,
        template_folder=str(REPO_ROOT / "templates"),
        static_folder=str(REPO_ROOT / "static"),
    )
    test_app.config.update(
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        SECRET_KEY="test",
        TESTING=True,
        WTF_CSRF_ENABLED=False,
    )

    db.init_app(test_app)
    with test_app.app_context():
        db.create_all()
        register_routes(test_app)
        yield test_app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def make_client(app):
    def _make(name="ACME", contact=None, notes=None, active=True):
        c = Client(name=name, contact=contact, notes=notes, active=active)
        db.session.add(c)
        db.session.commit()
        return c
    return _make


@pytest.fixture
def make_consultant(app):
    def _make(name="Ada Lovelace", email=None, role=None, active=True):
        c = Consultant(name=name, email=email, role=role, active=active)
        db.session.add(c)
        db.session.commit()
        return c
    return _make


@pytest.fixture
def make_project(app, make_client):
    def _make(name="Proyecto X", client=None, active=True, consultants=None):
        client = client or make_client()
        p = Project(name=name, client_id=client.id, active=active)
        if consultants:
            p.consultants = consultants
        db.session.add(p)
        db.session.commit()
        return p
    return _make


@pytest.fixture
def make_entry(app, make_project):
    from datetime import date

    def _make(project=None, entry_date=None, hours=8.0, person="Juan"):
        project = project or make_project()
        e = TimeEntry(
            project_id=project.id,
            entry_date=entry_date or date.today(),
            hours=hours,
            person=person,
        )
        db.session.add(e)
        db.session.commit()
        return e
    return _make
