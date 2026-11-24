"""Orchestration de l'ETL : extract -> transform -> load -> index -> controle qualite.

Lancement (depuis la racine du projet) :
    python src/etl/run_etl.py --sample 10000     # test rapide sur 10 000 transactions
    python src/etl/run_etl.py                    # chargement complet
Pour repartir de zero : python src/etl/create_schema.py  (vide l'entrepot), puis relancer l'ETL.
"""
import argparse
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

from sqlalchemy import text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from config import ROOT
from etl.extract import extract
from etl.load import load
from etl.transform import transform
from utils.db_connection import get_engine

LOGS = ROOT / "logs"
QUALITE = ROOT / "reports" / "data_quality"
INDEXES_SQL = ROOT / "sql" / "etl" / "10_indexes.sql"


def init_logging(horodatage):
    LOGS.mkdir(exist_ok=True)
    log = logging.getLogger("etl")
    log.setLevel(logging.INFO)
    log.handlers.clear()
    fmt = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s", "%H:%M:%S")
    for h in (logging.StreamHandler(), logging.FileHandler(LOGS / f"etl_{horodatage}.log", encoding="utf-8")):
        h.setFormatter(fmt)
        log.addHandler(h)
    return log


def controle_qualite(engine, n_source, fraudes_source, horodatage, log):
    with engine.connect() as c:
        n_dw = c.execute(text("SELECT COUNT(*) FROM dw.fait_transaction")).scalar()
        fraudes_dw = c.execute(text("SELECT COALESCE(SUM(is_fraud),0) FROM dw.fait_transaction")).scalar()
        sans_identite = c.execute(text("SELECT COUNT(*) FROM dw.fait_transaction WHERE identite_id = 0")).scalar()
        dims = {t: c.execute(text(f"SELECT COUNT(*) FROM dw.{t}")).scalar() for t in
                ["dim_temps", "dim_produit", "dim_carte", "dim_appareil", "dim_email", "dim_identite"]}

    ok_lignes = n_dw == n_source
    ok_fraudes = int(fraudes_dw) == int(fraudes_source)
    lignes = [
        f"# Controle qualite ETL ({horodatage})", "",
        "| Controle | Source | Data Warehouse | Resultat |", "|---|---|---|---|",
        f"| Nombre de transactions | {n_source:,} | {n_dw:,} | {'OK' if ok_lignes else 'ECART'} |",
        f"| Nombre de fraudes | {int(fraudes_source):,} | {int(fraudes_dw):,} | {'OK' if ok_fraudes else 'ECART'} |",
        f"| Taux de fraude | {100 * fraudes_source / n_source:.2f} % | {100 * fraudes_dw / max(n_dw, 1):.2f} % | |",
        f"| Transactions sans identite (identite_id = 0) | | {100 * sans_identite / max(n_dw, 1):.1f} % | |", "",
        "| Dimension | Lignes |", "|---|---|", *[f"| {k} | {v:,} |" for k, v in dims.items()],
    ]
    QUALITE.mkdir(parents=True, exist_ok=True)
    (QUALITE / f"etl_{horodatage}.md").write_text("\n".join(lignes), encoding="utf-8")
    for l in lignes[2:7]:
        log.info(l)
    return ok_lignes and ok_fraudes


def main():
    parser = argparse.ArgumentParser(description="ETL IEEE-CIS -> Data Warehouse PostgreSQL")
    parser.add_argument("--sample", type=int, default=None, help="nombre de transactions a charger (test)")
    args = parser.parse_args()

    horodatage = datetime.now().strftime("%Y%m%d_%H%M%S")
    log = init_logging(horodatage)
    debut = time.time()
    engine = get_engine()

    tr, idt = extract(args.sample)
    n_source, fraudes_source = len(tr), tr["isFraud"].sum()
    dims, fait = transform(tr, idt)
    load(engine, dims, fait)

    with engine.begin() as conn:
        conn.exec_driver_sql(INDEXES_SQL.read_text(encoding="utf-8"))
    log.info("Index crees")

    ok = controle_qualite(engine, n_source, fraudes_source, horodatage, log)
    log.info("Termine en %.1f s : %s", time.time() - debut,
             "CONTROLES OK" if ok else "ATTENTION : ecart avec la source (DW non vide avant le chargement ?)")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
