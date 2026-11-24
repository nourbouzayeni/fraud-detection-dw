import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.engine import URL

# Racine du projet : src/utils/db_connection.py -> on remonte de 2 niveaux
ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")

VARIABLES = ("DB_HOST", "DB_PORT", "DB_NAME", "DB_USER", "DB_PASSWORD")


def get_engine():
    """Retourne un moteur SQLAlchemy connecté à la base PostgreSQL du projet."""
    manquantes = [v for v in VARIABLES if not os.getenv(v)]
    if manquantes:
        raise RuntimeError(
            f"Variables manquantes dans {ROOT / '.env'} : {', '.join(manquantes)}"
        )

    url = URL.create(
        drivername="postgresql+psycopg2",
        username=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        database=os.getenv("DB_NAME"),
    )
    return create_engine(url)


if __name__ == "_main_":
    with get_engine().connect() as conn:
        print("Connexion OK")
        print(conn.execute(text("SELECT version()")).scalar())