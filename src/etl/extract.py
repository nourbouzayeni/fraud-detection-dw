"""EXTRACT : lecture des CSV IEEE-CIS (colonnes utiles uniquement) et controles de base."""
import logging
import sys
from pathlib import Path

import pandas as pd

sys.path.append(str(Path(__file__).resolve().parents[1]))
from config import IEEE_IDENTITY, IEEE_TRANSACTION

log = logging.getLogger("etl")

TRANSACTION_COLS = [
    "TransactionID", "TransactionDT", "TransactionAmt", "ProductCD",
    "card1", "card2", "card3", "card4", "card5", "card6",
    "P_emaildomain", "R_emaildomain", "isFraud",
]
IDENTITY_COLS = [
    "TransactionID", "DeviceType", "DeviceInfo",
    "id_12", "id_15", "id_16", "id_28", "id_29", "id_31",
    "id_35", "id_36", "id_37", "id_38",
]


def extract(nrows=None):
    """Retourne (transactions, identites). nrows : nombre de transactions a lire (mode test)."""
    tr = pd.read_csv(IEEE_TRANSACTION, usecols=TRANSACTION_COLS, nrows=nrows)

    # Les fichiers train utilisent "id_12", les fichiers test "id-12" : on accepte les deux.
    idt = pd.read_csv(IEEE_IDENTITY, usecols=lambda c: c.replace("-", "_") in IDENTITY_COLS)
    idt.columns = idt.columns.str.replace("-", "_")

    for nom, df in (("transaction", tr), ("identity", idt)):
        doublons = df["TransactionID"].duplicated().sum()
        if doublons:
            raise ValueError(f"{doublons} TransactionID en double dans {nom}")

    log.info("Extract : %s transactions, %s identites lues", f"{len(tr):,}", f"{len(idt):,}")
    return tr, idt
