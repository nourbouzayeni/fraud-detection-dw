from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_SIMULATED = ROOT / "data" / "simulated"
DATA_STAGING = ROOT / "data" / "staging"
DATA_PROCESSED = ROOT / "data" / "processed"

REPORTS_EXPLORATION = ROOT / "reports" / "exploration"
REPORTS_QUALITY = ROOT / "reports" / "data_quality"
IEEE_TRANSACTION = DATA_RAW / "ieee_cis" / "train_transaction.csv"
IEEE_IDENTITY = DATA_RAW / "ieee_cis" / "train_identity.csv"