"""TRANSFORM : fusion, nettoyage, construction des dimensions et de la table de faits (cles naturelles)."""
import logging

import pandas as pd

log = logging.getLogger("etl")

INCONNU = "inconnu"


def _txt(serie, taille, minuscules=False):
    """Texte propre : manquant/vide -> 'inconnu', espaces retires, tronque a la taille de la colonne SQL."""
    s = serie.astype("string").str.strip()
    if minuscules:
        s = s.str.lower()
    s = s.str.slice(0, taille)
    return s.fillna(INCONNU).replace("", INCONNU).astype(str)


def _num(serie):
    """Numerique : manquant -> -1."""
    return serie.fillna(-1).round().astype("int64")


def transform(tr, idt):
    n_avant = len(tr)
    df = tr.merge(idt, on="TransactionID", how="left", validate="one_to_one")
    if len(df) != n_avant:
        raise ValueError(f"La jointure a change le nombre de lignes : {n_avant} -> {len(df)}")
    log.info("Transform : jointure OK (%s lignes, %.1f %% avec identite)",
             f"{len(df):,}", 100 * df["DeviceType"].notna().mean() if "DeviceType" in df else 0)

    # --- temps (relatif : aucune date reelle inventee) ---
    jour = df["TransactionDT"] // 86400
    heure = (df["TransactionDT"] // 3600) % 24

    f = pd.DataFrame({
        "transaction_id": df["TransactionID"].astype("int64"),
        "transaction_dt": df["TransactionDT"].astype("int64"),
        "date_id": (jour * 24 + heure).astype("int64"),
        "product_cd": _txt(df["ProductCD"], 5),
        "card1": _num(df["card1"]), "card2": _num(df["card2"]), "card3": _num(df["card3"]),
        "card4": _txt(df["card4"], 30), "card5": _num(df["card5"]), "card6": _txt(df["card6"], 30),
        "device_type": _txt(df["DeviceType"], 20, minuscules=True),
        "device_info": _txt(df["DeviceInfo"], 255),
        "p_emaildomain": _txt(df["P_emaildomain"], 50, minuscules=True),
        "r_emaildomain": _txt(df["R_emaildomain"], 50, minuscules=True),
        "id_12": _txt(df["id_12"], 20), "id_15": _txt(df["id_15"], 20),
        "id_16": _txt(df["id_16"], 20), "id_28": _txt(df["id_28"], 20),
        "id_29": _txt(df["id_29"], 20), "id_31": _txt(df["id_31"], 50),
        "id_35": _txt(df["id_35"], 10), "id_36": _txt(df["id_36"], 10),
        "id_37": _txt(df["id_37"], 10), "id_38": _txt(df["id_38"], 10),
        "transaction_amt": df["TransactionAmt"].astype("float64").round(2),
        "is_fraud": df["isFraud"].astype("int16"),
    })

    if (f["transaction_amt"] < 0).any():
        raise ValueError("Montants negatifs detectes")

    # --- dimensions (combinaisons distinctes des cles naturelles) ---
    dims = {}
    t = f[["date_id"]].drop_duplicates().copy()
    t["jour_relatif"] = t["date_id"] // 24
    t["semaine_relative"] = t["jour_relatif"] // 7
    t["heure"] = t["date_id"] % 24
    dims["dim_temps"] = t[["date_id", "jour_relatif", "semaine_relative", "heure"]]
    dims["dim_produit"] = f[["product_cd"]].drop_duplicates()
    dims["dim_carte"] = f[["card1", "card2", "card3", "card4", "card5", "card6"]].drop_duplicates()
    dims["dim_appareil"] = f[["device_type", "device_info"]].drop_duplicates()
    dims["dim_email"] = f[["p_emaildomain", "r_emaildomain"]].drop_duplicates()
    dims["dim_identite"] = f[["id_12", "id_15", "id_16", "id_28", "id_29", "id_31",
                              "id_35", "id_36", "id_37", "id_38"]].drop_duplicates()

    for nom, d in dims.items():
        log.info("Transform : %-13s %s lignes distinctes", nom, f"{len(d):,}")
    return dims, f
