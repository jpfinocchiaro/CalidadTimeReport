from datetime import date
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


project_consultants = db.Table(
    "project_consultants",
    db.Column("project_id", db.Integer, db.ForeignKey("projects.id"), primary_key=True),
    db.Column(
        "consultant_id", db.Integer, db.ForeignKey("consultants.id"), primary_key=True
    ),
)


class Client(db.Model):
    __tablename__ = "clients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    contact = db.Column(db.String(120))
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True, nullable=False)

    projects = db.relationship(
        "Project", backref="client", cascade="all, delete-orphan", lazy=True
    )


class Consultant(db.Model):
    __tablename__ = "consultants"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False, unique=True)
    email = db.Column(db.String(120))
    role = db.Column(db.String(120))
    notes = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True, nullable=False)

    projects = db.relationship(
        "Project", secondary=project_consultants, back_populates="consultants"
    )


class Project(db.Model):
    __tablename__ = "projects"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    code = db.Column(db.String(40))
    description = db.Column(db.Text)
    active = db.Column(db.Boolean, default=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey("clients.id"), nullable=False)

    time_entries = db.relationship(
        "TimeEntry", backref="project", cascade="all, delete-orphan", lazy=True
    )
    consultants = db.relationship(
        "Consultant", secondary=project_consultants, back_populates="projects"
    )


class TimeEntry(db.Model):
    __tablename__ = "time_entries"
    id = db.Column(db.Integer, primary_key=True)
    entry_date = db.Column(db.Date, nullable=False, default=date.today)
    hours = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    person = db.Column(db.String(120), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey("projects.id"), nullable=False)
