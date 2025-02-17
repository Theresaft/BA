from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import text
db = SQLAlchemy()

def create_cleanup_event():
    """Erstellt ein MySQL-Event zum regelmäßigen Löschen abgelaufener Sessions."""
    with db.engine.connect() as connection:
        connection.execute(text("""
            CREATE EVENT IF NOT EXISTS delete_old_sessions
            ON SCHEDULE EVERY 5 MINUTE
            DO
            DELETE FROM sessions WHERE expires_at < NOW();
        """))
        connection.commit()