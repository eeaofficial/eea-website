from app import app
from flask import render_template, request, redirect, url_for, session, flash
from app.config import MASTER_EMAIL, MASTER_PASSWORD, ROLE_NAMES, ROLE_PASSWORDS

@app.after_request
def disable_cache(response):
    response.headers["Cache-Control"] = "no-store"
    return response

# ---------------- PUBLIC PAGES ----------------

@app.route("/")
def home():
    return render_template("home.html")

@app.route("/activities")
def activities():
    return render_template("activities.html")

@app.route("/members")
def members():
    return render_template("members.html")

@app.route("/gallery")
def gallery():
    return render_template("gallery.html")

@app.route("/upcoming-events")
def upcoming_events():
    return render_template("upcoming_events.html")


# ---------------- MASTER LOGIN ----------------

@app.route("/login", methods=["GET", "POST"])
def login():

    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")

        if email == MASTER_EMAIL and password == MASTER_PASSWORD:
            session.clear()
            session["master_authenticated"] = True
            return redirect(url_for("access_level"))

        flash("Invalid email or master password", "error")
        return redirect(url_for("login"))

    return render_template("login.html")


# ---------------- ACCESS LEVEL ----------------

@app.route("/access-level")
def access_level():

    if not session.get("master_authenticated"):
        return redirect(url_for("login"))

    return render_template("access_level.html", roles=ROLE_NAMES)


# ---------------- ROLE PASSWORD ----------------

@app.route("/role-login/<role>", methods=["GET", "POST"])
def role_login(role):

    if not session.get("master_authenticated"):
        return redirect(url_for("login"))

    if role not in ROLE_NAMES:
        return redirect(url_for("access_level"))

    if request.method == "POST":
        entered_password = request.form.get("role_password")

        if entered_password == ROLE_PASSWORDS[role]:
            session["role"] = role
            return redirect(url_for("admin_dashboard"))

        flash("Incorrect role password", "error")
        return redirect(url_for("role_login", role=role))

    return render_template("role_login.html", role_name=ROLE_NAMES[role])


# ---------------- DASHBOARD ----------------

@app.route("/admin/dashboard")
def admin_dashboard():

    role = session.get("role")

    if not role:
        return redirect(url_for("login"))

    return render_template("dashboard.html", role=role)
