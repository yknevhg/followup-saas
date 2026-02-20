from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)

    email = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

    smtp_email = db.Column(db.String(150))
    smtp_host = db.Column(db.String(150))
    smtp_port = db.Column(db.Integer)
    smtp_password = db.Column(db.LargeBinary)
    smtp_tls = db.Column(db.Boolean, default=True)
    smtp_verified = db.Column(db.Boolean, default=False)

class Client(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    name = db.Column(db.String(100))
    email = db.Column(db.String(150))
    followup_date = db.Column(db.Date, index=True)

    sent = db.Column(db.Boolean, default=False)
    sent_at = db.Column(db.DateTime)
    attempt_count = db.Column(db.Integer, default=0)
    last_error = db.Column(db.Text)

    user = db.relationship("User", backref="clients")