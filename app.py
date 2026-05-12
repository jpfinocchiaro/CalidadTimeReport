from datetime import datetime, date
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, flash, abort
from sqlalchemy import func

from models import db, Client, Project, TimeEntry, Consultant


def create_app():
    app = Flask(__name__)
    db_path = Path(__file__).parent / "timereport.db"
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{db_path}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "dev-secret-change-me"

    db.init_app(app)
    with app.app_context():
        db.create_all()

    register_routes(app)
    return app


def register_routes(app: Flask):
    # ---------- Home ----------
    @app.route("/")
    def index():
        totals = {
            "clients": Client.query.count(),
            "consultants": Consultant.query.count(),
            "projects": Project.query.count(),
            "entries": TimeEntry.query.count(),
            "hours": db.session.query(func.coalesce(func.sum(TimeEntry.hours), 0)).scalar(),
        }
        return render_template("index.html", totals=totals)

    # ---------- Clients ABMC ----------
    @app.route("/clients")
    def clients_list():
        clients = Client.query.order_by(Client.name).all()
        return render_template("clients/list.html", clients=clients)

    @app.route("/clients/new", methods=["GET", "POST"])
    def clients_new():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            contact = request.form.get("contact", "").strip()
            notes = request.form.get("notes", "").strip()
            active = bool(request.form.get("active"))
            if not name:
                flash("El nombre es obligatorio.", "error")
                return render_template("clients/form.html", client=None)
            if len(name) > 120:
                flash("El nombre es demasiado largo.", "error")
                return render_template("clients/form.html", client=None)
            if Client.query.filter_by(name=name).first():
                flash("Ya existe un cliente con ese nombre.", "error")
                return render_template("clients/form.html", client=None)
            client = Client(
                name=name,
                contact=contact or None,
                notes=notes or None,
                active=active,
            )
            db.session.add(client)
            db.session.commit()
            flash("Cliente creado.", "success")
            return redirect(url_for("clients_list"))
        return render_template("clients/form.html", client=None)

    @app.route("/clients/<int:client_id>/edit", methods=["GET", "POST"])
    def clients_edit(client_id):
        client = Client.query.get_or_404(client_id)
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            contact = request.form.get("contact", "").strip()
            notes = request.form.get("notes", "").strip()
            active = bool(request.form.get("active"))
            if not name:
                flash("El nombre es obligatorio.", "error")
                return render_template("clients/form.html", client=client)
            if len(name) > 120:
                flash("El nombre es demasiado largo.", "error")
                return render_template("clients/form.html", client=client)
            dup = Client.query.filter(Client.name == name, Client.id != client.id).first()
            if dup:
                flash("Ya existe otro cliente con ese nombre.", "error")
                return render_template("clients/form.html", client=client)
            client.name = name
            client.contact = contact or None
            client.notes = notes or None
            client.active = active
            db.session.commit()
            flash("Cliente actualizado.", "success")
            return redirect(url_for("clients_list"))
        return render_template("clients/form.html", client=client)

    @app.route("/clients/<int:client_id>/delete", methods=["POST"])
    def clients_delete(client_id):
        client = Client.query.get_or_404(client_id)
        db.session.delete(client)
        db.session.commit()
        flash("Cliente eliminado.", "success")
        return redirect(url_for("clients_list"))

    # ---------- Projects ABMC ----------
    @app.route("/projects")
    def projects_list():
        projects = (
            Project.query.join(Client).order_by(Client.name, Project.name).all()
        )
        return render_template("projects/list.html", projects=projects)

    @app.route("/projects/new", methods=["GET", "POST"])
    def projects_new():
        clients = Client.query.filter_by(active=True).order_by(Client.name).all()
        consultants = Consultant.query.order_by(Consultant.name).all()
        if not clients:
            flash("Primero creá al menos un cliente activo.", "error")
            return redirect(url_for("clients_list"))
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            client_id_raw = request.form.get("client_id")
            error = None
            if not name:
                error = "El nombre del proyecto es obligatorio."
            elif not client_id_raw:
                error = "Tenés que elegir un cliente."
            elif not Client.query.get(int(client_id_raw)):
                error = "El cliente seleccionado no existe."
            selected_ids = {int(v) for v in request.form.getlist("consultant_ids") if v.isdigit()}
            if error:
                flash(error, "error")
                return render_template(
                    "projects/form.html", project=None, clients=clients,
                    consultants=consultants, selected_consultant_ids=selected_ids,
                )
            if selected_ids:
                selected_consultants = Consultant.query.filter(Consultant.id.in_(selected_ids)).all()
            else:
                selected_consultants = []
            project = Project(
                name=name,
                code=request.form.get("code", "").strip() or None,
                description=request.form.get("description", "").strip() or None,
                active=bool(request.form.get("active")),
                client_id=int(client_id_raw),
            )
            project.consultants = selected_consultants
            db.session.add(project)
            db.session.commit()
            flash("Proyecto creado.", "success")
            return redirect(url_for("projects_list"))
        return render_template(
            "projects/form.html", project=None, clients=clients,
            consultants=consultants, selected_consultant_ids=set(),
        )

    @app.route("/projects/<int:project_id>/edit", methods=["GET", "POST"])
    def projects_edit(project_id):
        project = Project.query.get_or_404(project_id)
        clients = Client.query.order_by(Client.name).all()
        consultants = Consultant.query.order_by(Consultant.name).all()
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            client_id_raw = request.form.get("client_id")
            error = None
            if not name:
                error = "El nombre del proyecto es obligatorio."
            elif not client_id_raw:
                error = "Tenés que elegir un cliente."
            elif not Client.query.get(int(client_id_raw)):
                error = "El cliente seleccionado no existe."
            selected_ids = {int(v) for v in request.form.getlist("consultant_ids") if v.isdigit()}
            if error:
                flash(error, "error")
                return render_template(
                    "projects/form.html", project=project, clients=clients,
                    consultants=consultants, selected_consultant_ids=selected_ids,
                )
            if selected_ids:
                selected_consultants = Consultant.query.filter(Consultant.id.in_(selected_ids)).all()
            else:
                selected_consultants = []
            project.name = name
            project.code = request.form.get("code", "").strip() or None
            project.description = request.form.get("description", "").strip() or None
            project.active = bool(request.form.get("active"))
            project.client_id = int(client_id_raw)
            project.consultants = selected_consultants
            db.session.commit()
            flash("Proyecto actualizado.", "success")
            return redirect(url_for("projects_list"))
        return render_template(
            "projects/form.html", project=project, clients=clients,
            consultants=consultants,
            selected_consultant_ids={c.id for c in project.consultants},
        )

    @app.route("/projects/<int:project_id>/delete", methods=["POST"])
    def projects_delete(project_id):
        project = Project.query.get_or_404(project_id)
        db.session.delete(project)
        db.session.commit()
        flash("Proyecto eliminado.", "success")
        return redirect(url_for("projects_list"))

    # ---------- Consultants ABMC ----------
    @app.route("/consultants")
    def consultants_list():
        consultants = Consultant.query.order_by(Consultant.name).all()
        return render_template("consultants/list.html", consultants=consultants)

    @app.route("/consultants/new", methods=["GET", "POST"])
    def consultants_new():
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            role = request.form.get("role", "").strip()
            notes = request.form.get("notes", "").strip()
            active = bool(request.form.get("active"))
            if not name:
                flash("El nombre es obligatorio.", "error")
                return render_template("consultants/form.html", consultant=None)
            if len(name) > 120:
                flash("El nombre es demasiado largo.", "error")
                return render_template("consultants/form.html", consultant=None)
            if Consultant.query.filter_by(name=name).first():
                flash("Ya existe un consultor con ese nombre.", "error")
                return render_template("consultants/form.html", consultant=None)
            consultant = Consultant(
                name=name,
                email=email or None,
                role=role or None,
                notes=notes or None,
                active=active,
            )
            db.session.add(consultant)
            db.session.commit()
            flash("Consultor creado.", "success")
            return redirect(url_for("consultants_list"))
        return render_template("consultants/form.html", consultant=None)

    @app.route("/consultants/<int:consultant_id>/edit", methods=["GET", "POST"])
    def consultants_edit(consultant_id):
        consultant = Consultant.query.get_or_404(consultant_id)
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            email = request.form.get("email", "").strip()
            role = request.form.get("role", "").strip()
            notes = request.form.get("notes", "").strip()
            active = bool(request.form.get("active"))
            if not name:
                flash("El nombre es obligatorio.", "error")
                return render_template("consultants/form.html", consultant=consultant)
            if len(name) > 120:
                flash("El nombre es demasiado largo.", "error")
                return render_template("consultants/form.html", consultant=consultant)
            dup = Consultant.query.filter(
                Consultant.name == name, Consultant.id != consultant.id
            ).first()
            if dup:
                flash("Ya existe otro consultor con ese nombre.", "error")
                return render_template("consultants/form.html", consultant=consultant)
            consultant.name = name
            consultant.email = email or None
            consultant.role = role or None
            consultant.notes = notes or None
            consultant.active = active
            db.session.commit()
            flash("Consultor actualizado.", "success")
            return redirect(url_for("consultants_list"))
        return render_template("consultants/form.html", consultant=consultant)

    @app.route("/consultants/<int:consultant_id>/delete", methods=["POST"])
    def consultants_delete(consultant_id):
        consultant = Consultant.query.get_or_404(consultant_id)
        db.session.delete(consultant)
        db.session.commit()
        flash("Consultor eliminado.", "success")
        return redirect(url_for("consultants_list"))

    # ---------- Time entries (carga de horas) ----------
    @app.route("/hours")
    def hours_list():
        entries = (
            TimeEntry.query.join(Project)
            .join(Client)
            .order_by(TimeEntry.entry_date.desc(), TimeEntry.id.desc())
            .limit(200)
            .all()
        )
        return render_template("hours/list.html", entries=entries)

    @app.route("/hours/new", methods=["GET", "POST"])
    def hours_new():
        projects = _active_projects()
        if not projects:
            flash("No hay proyectos activos. Creá un cliente y un proyecto primero.", "error")
            return redirect(url_for("projects_list"))
        if request.method == "POST":
            form = request.form
            try:
                entry_date = datetime.strptime(form.get("entry_date", ""), "%Y-%m-%d").date()
            except ValueError:
                flash("Fecha inválida (formato YYYY-MM-DD).", "error")
                return render_template(
                    "hours/form.html", entry=None, projects=projects, today=date.today()
                )
            try:
                hours = float(form.get("hours", "").replace(",", "."))
            except ValueError:
                flash("Horas inválidas.", "error")
                return render_template(
                    "hours/form.html", entry=None, projects=projects, today=date.today()
                )
            if hours <= 0:
                flash("Las horas deben ser mayores a 0.", "error")
                return render_template(
                    "hours/form.html", entry=None, projects=projects, today=date.today()
                )
            person = form.get("person", "").strip()
            if not person:
                flash("La persona es obligatoria.", "error")
                return render_template(
                    "hours/form.html", entry=None, projects=projects, today=date.today()
                )
            project_id = form.get("project_id")
            if not project_id or not Project.query.get(int(project_id)):
                flash("Proyecto inválido.", "error")
                return render_template(
                    "hours/form.html", entry=None, projects=projects, today=date.today()
                )
            entry = TimeEntry(
                entry_date=entry_date,
                hours=hours,
                description=form.get("description", "").strip() or None,
                person=person,
                project_id=int(project_id),
            )
            db.session.add(entry)
            db.session.commit()
            flash("Horas cargadas.", "success")
            return redirect(url_for("hours_list"))
        return render_template(
            "hours/form.html", entry=None, projects=projects, today=date.today()
        )

    @app.route("/hours/<int:entry_id>/edit", methods=["GET", "POST"])
    def hours_edit(entry_id):
        entry = TimeEntry.query.get_or_404(entry_id)
        projects = _active_projects(include_id=entry.project_id)
        if request.method == "POST":
            form = request.form
            try:
                entry_date = datetime.strptime(form.get("entry_date", ""), "%Y-%m-%d").date()
            except ValueError:
                flash("Fecha inválida (formato YYYY-MM-DD).", "error")
                return render_template(
                    "hours/form.html", entry=entry, projects=projects, today=date.today()
                )
            try:
                hours = float(form.get("hours", "").replace(",", "."))
            except ValueError:
                flash("Horas inválidas.", "error")
                return render_template(
                    "hours/form.html", entry=entry, projects=projects, today=date.today()
                )
            if hours <= 0:
                flash("Las horas deben ser mayores a 0.", "error")
                return render_template(
                    "hours/form.html", entry=entry, projects=projects, today=date.today()
                )
            person = form.get("person", "").strip()
            if not person:
                flash("La persona es obligatoria.", "error")
                return render_template(
                    "hours/form.html", entry=entry, projects=projects, today=date.today()
                )
            project_id = form.get("project_id")
            if not project_id or not Project.query.get(int(project_id)):
                flash("Proyecto inválido.", "error")
                return render_template(
                    "hours/form.html", entry=entry, projects=projects, today=date.today()
                )
            entry.entry_date = entry_date
            entry.hours = hours
            entry.description = form.get("description", "").strip() or None
            entry.person = person
            entry.project_id = int(project_id)
            db.session.commit()
            flash("Registro actualizado.", "success")
            return redirect(url_for("hours_list"))
        return render_template(
            "hours/form.html", entry=entry, projects=projects, today=date.today()
        )

    @app.route("/hours/<int:entry_id>/delete", methods=["POST"])
    def hours_delete(entry_id):
        entry = TimeEntry.query.get_or_404(entry_id)
        db.session.delete(entry)
        db.session.commit()
        flash("Registro eliminado.", "success")
        return redirect(url_for("hours_list"))

    # ---------- Reportes ----------
    @app.route("/reports")
    def reports():
        date_from = request.args.get("from") or ""
        date_to = request.args.get("to") or ""
        client_id = request.args.get("client_id", type=int)

        q = db.session.query(TimeEntry).join(Project).join(Client)
        if date_from:
            q = q.filter(TimeEntry.entry_date >= datetime.strptime(date_from, "%Y-%m-%d").date())
        if date_to:
            q = q.filter(TimeEntry.entry_date <= datetime.strptime(date_to, "%Y-%m-%d").date())
        if client_id:
            q = q.filter(Client.id == client_id)

        by_client = (
            q.with_entities(Client.name, func.sum(TimeEntry.hours))
            .group_by(Client.id, Client.name)
            .order_by(Client.name)
            .all()
        )
        by_project = (
            q.with_entities(Client.name, Project.name, func.sum(TimeEntry.hours))
            .group_by(Client.id, Client.name, Project.id, Project.name)
            .order_by(Client.name, Project.name)
            .all()
        )
        by_person = (
            q.with_entities(TimeEntry.person, func.sum(TimeEntry.hours))
            .group_by(TimeEntry.person)
            .order_by(TimeEntry.person)
            .all()
        )

        grand_total = sum((row[-1] or 0) for row in by_client)
        clients = Client.query.order_by(Client.name).all()

        return render_template(
            "reports.html",
            by_client=by_client,
            by_project=by_project,
            by_person=by_person,
            grand_total=grand_total,
            clients=clients,
            filters={"from": date_from, "to": date_to, "client_id": client_id},
        )

    # ---------- helpers ----------
    def _active_projects(include_id=None):
        q = Project.query.join(Client).filter(Project.active.is_(True), Client.active.is_(True))
        projects = q.order_by(Client.name, Project.name).all()
        if include_id and not any(p.id == include_id for p in projects):
            extra = Project.query.get(include_id)
            if extra:
                projects.append(extra)
        return projects


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, host="127.0.0.1", port=5000)
