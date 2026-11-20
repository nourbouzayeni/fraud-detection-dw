from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

DATA_RAW = ROOT / "data" / "raw"
DATA_SIMULATED = ROOT / "data" / "simulated"
DATA_STAGING = ROOT / "data" / "staging"
DATA_PROCESSED = ROOT / "data" / "processed"

REPORTS_EXPLORATION = ROOT / "reports" / "exploration"
REPORTS_QUALITY = ROOT / "reports" / "data_quality"

PAYSIM_FILE = DATA_RAW / "paysim" / "PS_20174392719_1491204439457_log.csv"
ULB_FILE = DATA_RAW / "ulb_creditcard" / "creditcard.csv"