"""LOAD : chargement rapide (COPY) dans staging, puis dimensions, puis faits avec resolution des cles."""
import io
import logging

from sqlalchemy import text

log = logging.getLogger("etl")

# Colonnes "cle naturelle" de chaque dimension (dans l'ordre des scripts DDL)
DIMS = {
    "dim_temps": ["date_id", "jour_relatif", "semaine_relative", "heure"],
    "dim_produit": ["product_cd"],
    "dim_carte": ["card1", "card2", "card3", "card4", "card5", "card6"],
    "dim_appareil": ["device_type", "device_info"],
    "dim_email": ["p_emaildomain", "r_emaildomain"],
    "dim_identite": ["id_12", "id_15", "id_16", "id_28", "id_29", "id_31",
                     "id_35", "id_36", "id_37", "id_38"],
}

# Dimension -> (colonne cle de substitution, colonnes de jointure sur la table de staging)
FAIT_JOINTURES = [
    ("dim_carte", "carte_id", DIMS["dim_carte"]),
    ("dim_produit", "produit_id", DIMS["dim_produit"]),
    ("dim_appareil", "appareil_id", DIMS["dim_appareil"]),
    ("dim_email", "email_id", DIMS["dim_email"]),
    ("dim_identite", "identite_id", DIMS["dim_identite"]),
]


def copy_df(engine, df, schema, table, chunk=100_000):
    """Charge un DataFrame avec COPY (beaucoup plus rapide que INSERT)."""
    cols = ", ".join(df.columns)
    raw = engine.raw_connection()
    try:
        cur = raw.cursor()
        for debut in range(0, len(df), chunk):
            buf = io.StringIO()
            df.iloc[debut:debut + chunk].to_csv(buf, index=False, header=False)
            buf.seek(0)
            cur.copy_expert(f"COPY {schema}.{table} ({cols}) FROM STDIN WITH (FORMAT csv)", buf)
        raw.commit()
    except Exception:
        raw.rollback()
        raise
    finally:
        raw.close()


def _vers_staging(engine, df, table):
    df.head(0).to_sql(table, engine, schema="staging", if_exists="replace", index=False)
    copy_df(engine, df, "staging", table)


def load(engine, dims, fait):
    # 1) Dimensions : on n'insere que les nouvelles combinaisons (relancable sans doublons)
    for nom, cols in DIMS.items():
        stg = f"stg_{nom}"
        _vers_staging(engine, dims[nom][cols], stg)
        liste = ", ".join(cols)
        with engine.begin() as conn:
            res = conn.execute(text(
                f"INSERT INTO dw.{nom} ({liste}) SELECT {liste} FROM staging.{stg} ON CONFLICT DO NOTHING"
            ))
        log.info("Load : %-13s %s nouvelles lignes", nom, f"{res.rowcount:,}")

    # 2) Faits : staging (cles naturelles) -> jointure avec les dimensions -> cles de substitution
    _vers_staging(engine, fait, "stg_fait")
    n_stg = len(fait)

    selects, joins = [], []
    for i, (dim, cle, cols) in enumerate(FAIT_JOINTURES):
        a = f"d{i}"
        selects.append(f"{a}.{cle}")
        cond = " AND ".join(f"{a}.{c} = s.{c}" for c in cols)
        joins.append(f"JOIN dw.{dim} {a} ON {cond}")

    sql = f"""
        INSERT INTO dw.fait_transaction
            (transaction_id, transaction_dt, date_id, carte_id, produit_id,
             appareil_id, email_id, identite_id, transaction_amt, is_fraud)
        SELECT s.transaction_id, s.transaction_dt, s.date_id, {', '.join(selects)},
               s.transaction_amt, s.is_fraud
        FROM staging.stg_fait s
        {' '.join(joins)}
        ON CONFLICT (transaction_id) DO NOTHING
    """
    with engine.begin() as conn:
        res = conn.execute(text(sql))
        manquantes = conn.execute(text(
            "SELECT COUNT(*) FROM staging.stg_fait s "
            "WHERE NOT EXISTS (SELECT 1 FROM dw.fait_transaction f WHERE f.transaction_id = s.transaction_id)"
        )).scalar()
        if manquantes:
            raise RuntimeError(f"{manquantes} transactions perdues a la jointure avec les dimensions")
        conn.execute(text("DROP TABLE staging.stg_fait"))
    log.info("Load : fait_transaction %s lignes inserees (sur %s en staging)", f"{res.rowcount:,}", f"{n_stg:,}")
