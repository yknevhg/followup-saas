from flask import Flask, render_template, redirect, request, abort
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta, date
import os

from models import db, User, Client
from crypto import encrypt

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

database_url = os.environ.get("DATABASE_URL")

if database_url:
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    basedir = os.path.abspath(os.path.dirname(__file__))
    app.config["SQLALCHEMY_DATABASE_URI"] = (
        "sqlite:///" + os.path.join(basedir, "database.db")
    )

app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# ----------------------------------------

# ---------------- INIT ----------------
db.init_app(app)

with app.app_context():
    db.create_all()

login_manager = LoginManager()
login_manager.login_view = "login"
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("home.html")


# ---------------- AUTH ----------------

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(email=request.form["email"]).first()
        if user and check_password_hash(user.password, request.form["password"]):
            login_user(user)
            return redirect("/dashboard")

    return render_template("login.html")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        email = request.form["email"]

        if User.query.filter_by(email=email).first():
            return "Account already exists. Please login instead."

        hashed = generate_password_hash(request.form["password"])
        user = User(email=email, password=hashed)

        db.session.add(user)
        db.session.commit()
        return redirect("/login")

    return render_template("signup.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/")


# ---------------- DASHBOARD ----------------

@app.route("/dashboard")
@login_required
def dashboard():
    clients = Client.query.filter_by(user_id=current_user.id).all()
    today = date.today()

    dashboard_clients = []
    for client in clients:
        days_remaining = (client.followup_date - today).days

        dashboard_clients.append({
            "id": client.id,
            "name": client.name,
            "email": client.email,
            "followup_date": client.followup_date,
            "sent": client.sent,
            "days_remaining": days_remaining,
        })

    return render_template(
    "dashboard.html",
    clients=dashboard_clients,
    smtp_verified=current_user.smtp_verified
)


# ---------------- ADD CLIENT ----------------

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_client():
    if request.method == "POST":
        delay = request.form.get("delay")
        date_input = request.form.get("date")

        if delay:
            followup_date = date.today() + timedelta(days=int(delay))
        else:
            followup_date = datetime.strptime(date_input, "%Y-%m-%d").date()

        client = Client(
            user_id=current_user.id,
            name=request.form["name"],
            email=request.form["email"],
            followup_date=followup_date,
        )

        db.session.add(client)
        db.session.commit()
        return redirect("/dashboard")

    return render_template("add_client.html")


# ---------------- EDIT CLIENT ----------------

@app.route("/edit/<int:client_id>", methods=["GET", "POST"])
@login_required
def edit_client(client_id):
    client = Client.query.filter_by(
        id=client_id, user_id=current_user.id
    ).first()

    if not client:
        abort(404)

    if request.method == "POST":
        client.name = request.form["name"]
        client.email = request.form["email"]
        client.followup_date = datetime.strptime(
            request.form["date"], "%Y-%m-%d"
        ).date()

        db.session.commit()
        return redirect("/dashboard")

    return render_template("edit_client.html", client=client)


# ---------------- DELETE CLIENT ----------------

@app.route("/delete/<int:client_id>", methods=["POST"])
@login_required
def delete_client(client_id):
    client = Client.query.filter_by(
        id=client_id, user_id=current_user.id
    ).first()

    if not client:
        abort(404)

    db.session.delete(client)
    db.session.commit()
    return redirect("/dashboard")


# ---------------- EMAIL SETTINGS ----------------

@app.route("/email-settings", methods=["GET", "POST"])
@login_required
def email_settings():
    if request.method == "POST":
        current_user.smtp_email = request.form.get("smtp_email")
        current_user.smtp_host = request.form.get("smtp_host")
        current_user.smtp_port = int(request.form.get("smtp_port"))
        current_user.smtp_tls = True if request.form.get("smtp_tls") else False
        current_user.smtp_password = encrypt(request.form.get("smtp_password"))
        current_user.smtp_verified = False

        db.session.commit()
        return redirect("/dashboard")

    return render_template("email_settings.html")


# ---------------- LOCAL RUN ----------------

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)