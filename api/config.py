import os
import json
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent
API_DIR = Path(__file__).resolve().parent

if (API_DIR / "fonts").exists():
    FONTS_DIR = API_DIR / "fonts"
else:
    FONTS_DIR = BASE_DIR / "fonts"

STATIC_DIR = BASE_DIR / "static"

FONT_URDU = str(FONTS_DIR / "Jameel_Noori_Nastaleeq_Regular.ttf")
FONT_SINDHI = str(FONTS_DIR / "MB-Lateefi-SKv2_0.ttf")
LOGO_PATH = str(STATIC_DIR / "pscc-logo.jpg")

# Google Sheets Config
DEFAULT_SPREADSHEET_ID = "1x5wykhZlN2-pFqrreCFvQmDZikZkV8_1fr5igQ-6GCk"
SPREADSHEET_ID = os.environ.get("SPREADSHEET_ID", DEFAULT_SPREADSHEET_ID)

WS_TIMETABLE = "Timetable"
WS_SUBJECTS = "Subjects"
WS_TEACHERS = "Teachers"
WS_ENTRIES = "Teaching_Plan_Entries"

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
PERIODS_PER_DAY = {
    "Monday": 7,
    "Tuesday": 7,
    "Wednesday": 7,
    "Thursday": 7,
    "Friday": 6,
    "Saturday": 6
}

def get_service_account_credentials():
    """
    Loads service account info from:
    1. Environment variable GCP_SERVICE_ACCOUNT (JSON string or base64 on Vercel)
    2. Local .streamlit/secrets.toml (for local dev)
    3. Service account JSON file if specified in GCP_SERVICE_ACCOUNT_FILE
    """
    # 1. Direct environment variable (JSON string)
    env_json = os.environ.get("GCP_SERVICE_ACCOUNT")
    if env_json:
        try:
            return json.loads(env_json)
        except Exception:
            import base64
            try:
                decoded = base64.b64decode(env_json).decode("utf-8")
                return json.loads(decoded)
            except Exception as e:
                print(f"Warning: could not parse GCP_SERVICE_ACCOUNT env var: {e}")

    # 2. Local secrets.toml
    secrets_path = BASE_DIR / ".streamlit" / "secrets.toml"
    if secrets_path.exists():
        try:
            import toml
            secrets = toml.load(str(secrets_path))
            if "gcp_service_account" in secrets:
                return secrets["gcp_service_account"]
        except Exception as e:
            print(f"Warning: could not load secrets from {secrets_path}: {e}")

    # 3. Dedicated JSON file
    creds_file = os.environ.get("GCP_SERVICE_ACCOUNT_FILE", "service_account.json")
    file_path = BASE_DIR / creds_file
    if file_path.exists():
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Warning: could not load service account from {file_path}: {e}")

    return None
