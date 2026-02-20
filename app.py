from flask import Flask, render_template, redirect, request
from flask_login import (
    LoginManager,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os

from models import db, User, Client
from crypto import encrypt

app = Flask(__name__)

# ---------------- CONFIG ----------------
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret")

database_url = os.environ.get("DATABASE_URL")

if database_url:
    # Render provides a PostgreSQL database URL
    app.config["SQLALCHEMY_DATABASE_URI"] = database_url
else:
    # Local development fallback (SQLite)
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


# ---------------- AUTH ----------------

@app.route("/", methods=["GET", "POST"])
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
        hashed = generate_password_hash(request.form["password"])
        user = User(
            email=request.form["email"],
            password=hashed,
        )
        db.session.add(user)
        db.session.commit()
        return redirect("/")
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
    return render_template("dashboard.html", clients=clients)


# ---------------- ADD CLIENT ----------------

@app.route("/add", methods=["GET", "POST"])
@login_required
def add_client():
    if request.method == "POST":
        client = Client(
            user_id=current_user.id,
            name=request.form["name"],
            email=request.form["email"],
            followup_date=datetime.strptime(
                request.form["date"], "%Y-%m-%d"
            ).date(),
        )
        db.session.add(client)
        db.session.commit()
        return redirect("/dashboard")

    return render_template("add_client.html")


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


# ---------------- TEST EMAIL ----------------

@app.route("/test-email")
@login_required
def test_email():
    try:
        from emailer import send_test_email

        send_test_email(current_user)
        current_user.smtp_verified = True
        db.session.commit()
        return "Test email sent successfully. SMTP verified."

    except Exception as e:
        return f"Test email failed: {str(e)}"


# IMPORTANT:
# We do NOT call app.run() here.
# Render will use Gunicorn to start the app.