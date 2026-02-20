from datetime import date, datetime
from app import app
from models import Client, User, db
from emailer import send_followup


def run_scheduler():
    with app.app_context():
        today = date.today()

        clients = Client.query.join(User).filter(
            Client.followup_date == today,
            Client.sent == False,
            User.smtp_verified == True
        ).all()

        for client in clients:
            try:
                send_followup(client.user, client)

                client.sent = True
                client.sent_at = datetime.utcnow()
                db.session.commit()

            except Exception as e:
                client.attempt_count += 1
                client.last_error = str(e)
                db.session.commit()


if __name__ == "__main__":
    run_scheduler()