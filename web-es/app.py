import os
from datetime import datetime

import psycopg2
from flask import Flask, render_template, request


app = Flask(__name__)

COMMUNES = [f"Comuna {number}" for number in range(1, 11)]
PROGRAMS = ["Medicina", "Ingeniería", "Abogacía", "Licenciatura"]
SERVED_BY = os.getenv("SERVED_BY", "Atendido por Web Server 2 - Espanol")
LANGUAGE = os.getenv("APP_LANGUAGE", "Espanol")


def db_config():
    return {
        "host": os.getenv("DB_HOST", "db"),
        "port": int(os.getenv("DB_PORT", "5432")),
        "dbname": os.getenv("DB_NAME", "telematica"),
        "user": os.getenv("DB_USER", "telematica_user"),
        "password": os.getenv("DB_PASSWORD", "change_me_in_production"),
    }


def get_connection():
    return psycopg2.connect(**db_config())


def default_entry_at():
    return datetime.now().strftime("%Y-%m-%dT%H:%M")


def parse_entry_at(value):
    if not value:
        return datetime.now()
    return datetime.strptime(value, "%Y-%m-%dT%H:%M")


def client_ip():
    forwarded_for = request.headers.get("X-Forwarded-For", "")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.remote_addr or ""


@app.get("/health")
def health():
    return {"status": "ok", "served_by": SERVED_BY}


@app.route("/", methods=["GET", "POST"])
def index():
    errors = []
    form_data = {
        "name": "",
        "commune": COMMUNES[0],
        "program": PROGRAMS[0],
        "entry_at": default_entry_at(),
    }
    success = None

    if request.method == "POST":
        form_data = {
            "name": request.form.get("name", "").strip(),
            "commune": request.form.get("commune", "").strip(),
            "program": request.form.get("program", "").strip(),
            "entry_at": request.form.get("entry_at", "").strip(),
        }

        if len(form_data["name"]) < 2:
            errors.append("El nombre debe tener al menos dos caracteres.")
        if form_data["commune"] not in COMMUNES:
            errors.append("Seleccione una comuna valida.")
        if form_data["program"] not in PROGRAMS:
            errors.append("Seleccione una carrera valida.")

        try:
            entry_at = parse_entry_at(form_data["entry_at"])
        except ValueError:
            errors.append("Seleccione una fecha de ingreso valida.")
            entry_at = datetime.now()

        if not errors:
            try:
                with get_connection() as conn:
                    with conn.cursor() as cur:
                        cur.execute(
                            """
                            INSERT INTO registrations
                                (name, commune, program, language, entry_at, served_by, client_ip)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)
                            RETURNING id;
                            """,
                            (
                                form_data["name"],
                                form_data["commune"],
                                form_data["program"],
                                LANGUAGE,
                                entry_at,
                                SERVED_BY,
                                client_ip(),
                            ),
                        )
                        registration_id = cur.fetchone()[0]
                success = {
                    "id": registration_id,
                    "name": form_data["name"],
                    "commune": form_data["commune"],
                    "program": form_data["program"],
                    "entry_at": entry_at.strftime("%Y-%m-%d %H:%M"),
                }
                form_data["name"] = ""
                form_data["entry_at"] = default_entry_at()
            except psycopg2.Error as exc:
                errors.append(f"Error de base de datos: {exc.pgerror or exc}")

    return render_template(
        "index.html",
        communes=COMMUNES,
        programs=PROGRAMS,
        served_by=SERVED_BY,
        form_data=form_data,
        errors=errors,
        success=success,
    )
