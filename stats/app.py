import base64
import io
import os
import smtplib
from email.message import EmailMessage

import matplotlib.pyplot as plt
import psycopg2
from flask import Flask, redirect, render_template, request, url_for


app = Flask(__name__)


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


def admin_token_configured():
    token = os.getenv("ADMIN_TOKEN", "")
    return token and token != "change_this_admin_token"


def authorized():
    expected = os.getenv("ADMIN_TOKEN", "")
    if not admin_token_configured():
        return True
    provided = request.headers.get("X-Admin-Token") or request.values.get("token")
    return provided == expected


def fetch_rows(query):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(query)
            return cur.fetchall()


def fetch_statistics():
    total = fetch_rows("SELECT COUNT(*) FROM registrations;")[0][0]
    by_commune = fetch_rows(
        """
        SELECT commune, COUNT(*) AS total
        FROM registrations
        GROUP BY commune
        ORDER BY commune;
        """
    )
    by_program = fetch_rows(
        """
        SELECT program, COUNT(*) AS total
        FROM registrations
        GROUP BY program
        ORDER BY total DESC, program;
        """
    )
    by_commune_program = fetch_rows(
        """
        SELECT commune, program, COUNT(*) AS total
        FROM registrations
        GROUP BY commune, program
        ORDER BY commune, program;
        """
    )
    recent = fetch_rows(
        """
        SELECT id, name, commune, program, language, entry_at, served_by
        FROM registrations
        ORDER BY id DESC
        LIMIT 10;
        """
    )
    return {
        "total": total,
        "by_commune": by_commune,
        "by_program": by_program,
        "by_commune_program": by_commune_program,
        "recent": recent,
    }


def make_bar_chart(rows, title, x_label, y_label):
    labels = [str(row[0]) for row in rows] or ["No data"]
    values = [int(row[1]) for row in rows] or [0]

    fig, ax = plt.subplots(figsize=(9, 4.8))
    ax.bar(labels, values, color="#1f6f8b")
    ax.set_title(title)
    ax.set_xlabel(x_label)
    ax.set_ylabel(y_label)
    ax.tick_params(axis="x", rotation=30)
    ax.grid(axis="y", alpha=0.25)
    fig.tight_layout()

    output = io.BytesIO()
    fig.savefig(output, format="png", dpi=140)
    plt.close(fig)
    png_bytes = output.getvalue()
    encoded = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{encoded}", png_bytes


def render_report(message=None, error=None):
    if not authorized():
        return "Unauthorized", 401

    stats = fetch_statistics()
    commune_chart, commune_png = make_bar_chart(
        stats["by_commune"],
        "Total de usuarios por comuna",
        "Comuna",
        "Usuarios",
    )
    program_chart, program_png = make_bar_chart(
        stats["by_program"],
        "Total de usuarios por carrera",
        "Carrera",
        "Usuarios",
    )

    return render_template(
        "stats.html",
        stats=stats,
        commune_chart=commune_chart,
        program_chart=program_chart,
        token=request.values.get("token", ""),
        admin_token_enabled=admin_token_configured(),
        message=message,
        error=error,
        attachments={"commune": commune_png, "program": program_png},
    )


def build_email(stats, commune_png, program_png):
    smtp_from = os.getenv("SMTP_FROM") or os.getenv("SMTP_USER") or "noreply@example.com"
    smtp_to = os.getenv("SMTP_TO", "ialondonoo@eafit.edu.co")

    msg = EmailMessage()
    msg["Subject"] = "Estadisticas acumuladas - Proyecto Telematica"
    msg["From"] = smtp_from
    msg["To"] = smtp_to

    lines = [
        "Reporte acumulado de registros",
        "",
        f"Total de usuarios: {stats['total']}",
        "",
        "Usuarios por comuna:",
    ]
    lines.extend(f"- {commune}: {total}" for commune, total in stats["by_commune"])
    lines.append("")
    lines.append("Usuarios por comuna y carrera:")
    lines.extend(
        f"- {commune} / {program}: {total}"
        for commune, program, total in stats["by_commune_program"]
    )
    lines.append("")
    lines.append("Trabajo realizado por: Laura Indabur García y Athina Cappelletti Garcia")

    msg.set_content("\n".join(lines))
    msg.add_attachment(
        commune_png,
        maintype="image",
        subtype="png",
        filename="usuarios-por-comuna.png",
    )
    msg.add_attachment(
        program_png,
        maintype="image",
        subtype="png",
        filename="usuarios-por-carrera.png",
    )
    return msg


def send_email(stats, commune_png, program_png):
    host = os.getenv("SMTP_HOST", "").strip()
    port = int(os.getenv("SMTP_PORT", "587"))
    user = os.getenv("SMTP_USER", "").strip()
    password = os.getenv("SMTP_PASSWORD", "").strip()
    smtp_from = os.getenv("SMTP_FROM", "").strip() or user
    smtp_to_str = os.getenv("SMTP_TO", "ialondonoo@eafit.edu.co").strip()
    smtp_to_list = [email.strip() for email in smtp_to_str.split(",") if email.strip()]

    missing = []
    if not host:
        missing.append("SMTP_HOST")
    if not smtp_from:
        missing.append("SMTP_FROM or SMTP_USER")
    if not smtp_to_list:
        missing.append("SMTP_TO")
    if user and not password:
        missing.append("SMTP_PASSWORD")
    if missing:
        return False, "SMTP is not fully configured: " + ", ".join(missing)

    msg = build_email(stats, commune_png, program_png)

    if port == 465:
        server = smtplib.SMTP_SSL(host, port, timeout=25)
    else:
        server = smtplib.SMTP(host, port, timeout=25)

    with server:
        if port != 465:
            server.starttls()
        if user:
            server.login(user, password)
        server.send_message(msg, to_addrs=smtp_to_list)

    return True, f"Report sent to {', '.join(smtp_to_list)}."


@app.get("/")
def root():
    return redirect(url_for("stats_page"))


@app.get("/health")
def health():
    return {"status": "ok", "service": "stats"}


@app.get("/admin/stats")
def stats_page():
    return render_report()


@app.post("/admin/send-email")
def send_statistics_email():
    if not authorized():
        return "Unauthorized", 401

    stats = fetch_statistics()
    _, commune_png = make_bar_chart(
        stats["by_commune"],
        "Total de usuarios por comuna",
        "Comuna",
        "Usuarios",
    )
    _, program_png = make_bar_chart(
        stats["by_program"],
        "Total de usuarios por carrera",
        "Carrera",
        "Usuarios",
    )

    try:
        ok, detail = send_email(stats, commune_png, program_png)
    except Exception as exc:
        return render_report(error=f"Email error: {exc}")

    if ok:
        return render_report(message=detail)
    return render_report(error=detail)
