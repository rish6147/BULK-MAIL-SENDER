import hashlib
import hmac
import json
import os
import re
import secrets
import ssl
import smtplib
import threading
import time
from datetime import datetime, date, time as dt_time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import pandas as pd
import requests
import streamlit as st


# ============================================================
# APP CONFIG
# ============================================================
st.set_page_config(
    page_title="Professor Mailer",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded",
)

REQUIRED_COLS = ["email", "name", "department", "university", "interest"]
DATA_DIR = "mailer_data"
ATTACH_DIR = "attachments"
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(ATTACH_DIR, exist_ok=True)

DEFAULT_PROFESSORS = [
    {
        "email": "professor@example.edu",
        "name": "Prof. Sample",
        "department": "Computer Science",
        "university": "Example University",
        "interest": "Computer Vision and Edge AI",
    }
]
DEFAULT_SUBJECT = "Research Internship Inquiry – {interest}"
DEFAULT_BODY = """<p>Dear <b>{name}</b>,</p>
<p>My name is [Your Name], and I am a [Your Degree / University] student.
I am writing to express my interest in your research group at
<b>{university}</b>, within the <b>{department}</b>.</p>
<p>Your work in <b>{interest}</b> closely aligns with my academic interests
and experience. I would be grateful to know whether you may have an
opportunity for a research intern.</p>
<p>I have attached my CV and supporting documents for your consideration.</p>
<p>Sincerely,<br>[Your Name]<br>[Your University]</p>"""


# ============================================================
# PASSWORD HASHING (PBKDF2-HMAC-SHA256)
# ============================================================
def hash_password(password: str, salt_hex: str | None = None) -> tuple[str, str]:
    salt = bytes.fromhex(salt_hex) if salt_hex else secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 120_000)
    return digest.hex(), salt.hex()


def verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    if not stored_hash or not salt_hex:
        return False
    candidate_hash, _ = hash_password(password, salt_hex)
    return hmac.compare_digest(candidate_hash, stored_hash)


# ============================================================
# USER-SCOPED CLOUD STORAGE (FIRESTORE REST + LOCAL FALLBACK)
# ============================================================
def safe_user_key(email: str) -> str:
    return re.sub(r"[^a-zA-Z0-9._-]", "_", email.strip().lower())


def _get_firestore_config():
    try:
        fb = st.secrets.get("firebase", {})
        project_id = (fb.get("project_id") or "").strip()
        api_key = (fb.get("api_key") or "").strip()
        if project_id and api_key:
            return project_id, api_key
    except Exception:
        pass
    return None, None


def _firestore_doc_url(project_id: str, api_key: str, doc_path: str) -> str:
    return f"https://firestore.googleapis.com/v1/projects/{project_id}/databases/(default)/documents/{doc_path}?key={api_key}"


def _to_fs_value(val):
    if val is None:
        return {"nullValue": None}
    if isinstance(val, bool):
        return {"booleanValue": val}
    if isinstance(val, int) and not isinstance(val, bool):
        return {"integerValue": str(val)}
    if isinstance(val, float):
        return {"doubleValue": val}
    if isinstance(val, list):
        return {"arrayValue": {"values": [_to_fs_value(x) for x in val]}}
    if isinstance(val, dict):
        return {"mapValue": {"fields": {str(k): _to_fs_value(v) for k, v in val.items()}}}
    return {"stringValue": str(val)}


def _from_fs_value(fs_val: dict):
    if "nullValue" in fs_val:
        return None
    if "booleanValue" in fs_val:
        return fs_val["booleanValue"]
    if "integerValue" in fs_val:
        return int(fs_val["integerValue"])
    if "doubleValue" in fs_val:
        return float(fs_val["doubleValue"])
    if "stringValue" in fs_val:
        return fs_val["stringValue"]
    if "arrayValue" in fs_val:
        return [_from_fs_value(x) for x in fs_val["arrayValue"].get("values", [])]
    if "mapValue" in fs_val:
        return {k: _from_fs_value(v) for k, v in fs_val["mapValue"].get("fields", {}).items()}
    return None


def _user_store_path(user_email: str, filename: str) -> str:
    ukey = safe_user_key(user_email)
    udir = os.path.join(DATA_DIR, "cloud_users", ukey)
    os.makedirs(udir, exist_ok=True)
    return os.path.join(udir, filename)


def load_json(path, default):
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return default


def save_json(path, value):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(value, f, indent=2, ensure_ascii=False)


def cloud_load_json(user_email: str, name: str, default):
    ukey = safe_user_key(user_email)
    project_id, api_key = _get_firestore_config()
    if project_id and api_key:
        try:
            url = _firestore_doc_url(project_id, api_key, f"users/{ukey}/state/{name}")
            resp = requests.get(url, timeout=10)
            if resp.status_code == 200:
                fields = resp.json().get("fields", {})
                if "payload" in fields:
                    return _from_fs_value(fields["payload"])
            elif resp.status_code == 404:
                return default
        except Exception:
            pass
    return load_json(_user_store_path(user_email, f"{name}.json"), default)


def cloud_save_json(user_email: str, name: str, value):
    save_json(_user_store_path(user_email, f"{name}.json"), value)
    ukey = safe_user_key(user_email)
    project_id, api_key = _get_firestore_config()
    if project_id and api_key:
        try:
            url = _firestore_doc_url(project_id, api_key, f"users/{ukey}/state/{name}")
            body = {"fields": {"payload": _to_fs_value(value)}}
            requests.patch(url, json=body, timeout=10)
        except Exception:
            pass


def cloud_delete_json(user_email: str, name: str):
    path = _user_store_path(user_email, f"{name}.json")
    if os.path.exists(path):
        os.remove(path)
    ukey = safe_user_key(user_email)
    project_id, api_key = _get_firestore_config()
    if project_id and api_key:
        try:
            url = _firestore_doc_url(project_id, api_key, f"users/{ukey}/state/{name}")
            requests.delete(url, timeout=10)
        except Exception:
            pass


def list_all_cloud_users() -> list[str]:
    base = os.path.join(DATA_DIR, "cloud_users")
    if not os.path.exists(base):
        return []
    users = []
    for entry in sorted(os.listdir(base)):
        prof_path = os.path.join(base, entry, "profile.json")
        if os.path.exists(prof_path):
            data = load_json(prof_path, {})
            if data.get("email"):
                users.append(data["email"])
    return users


def load_credentials(user_email: str):
    data = cloud_load_json(user_email, "credentials", {})
    return {
        "sender_email": data.get("sender_email", user_email),
        "sender_password": data.get("sender_password", ""),
        "remember": bool(data.get("remember", False)),
    }


def save_credentials(user_email: str, email: str, password: str, remember: bool):
    if remember:
        cloud_save_json(user_email, "credentials", {
            "sender_email": email.strip(),
            "sender_password": password.strip(),
            "remember": True,
        })
    else:
        cloud_delete_json(user_email, "credentials")


def load_saved_professors(user_email: str):
    rows = cloud_load_json(user_email, "contacts", None)
    if isinstance(rows, list):
        df = pd.DataFrame(rows).fillna("")
        df.columns = [str(c).strip().lower() for c in df.columns]
        for col in REQUIRED_COLS:
            if col not in df.columns:
                df[col] = ""
        return df[REQUIRED_COLS]
    return pd.DataFrame(DEFAULT_PROFESSORS, columns=REQUIRED_COLS)


def save_professors(user_email: str, df: pd.DataFrame):
    df = df.copy()
    for col in REQUIRED_COLS:
        if col not in df:
            df[col] = ""
    records = df[REQUIRED_COLS].fillna("").to_dict(orient="records")
    cloud_save_json(user_email, "contacts", records)


def load_template(user_email: str):
    data = cloud_load_json(user_email, "template", {})
    return {
        "subject": data.get("subject", DEFAULT_SUBJECT),
        "body": data.get("body", DEFAULT_BODY),
    }


def save_template(user_email: str, subject: str, body: str):
    cloud_save_json(user_email, "template", {"subject": subject, "body": body})


def load_history(user_email: str):
    rows = cloud_load_json(user_email, "history", [])
    if isinstance(rows, list) and rows:
        return pd.DataFrame(rows).fillna("")
    return pd.DataFrame(columns=[
        "timestamp", "email", "name", "university", "status", "detail"
    ])


def append_history(user_email: str, email: str, name: str, university: str, status: str, detail: str):
    rows = cloud_load_json(user_email, "history", [])
    if not isinstance(rows, list):
        rows = []
    rows.append({
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "email": email,
        "name": name,
        "university": university,
        "status": status,
        "detail": detail,
    })
    cloud_save_json(user_email, "history", rows)


def load_schedule(user_email: str):
    return cloud_load_json(user_email, "schedule_job", None)


def save_schedule(user_email: str, job: dict):
    cloud_save_json(user_email, "schedule_job", job)


def clear_schedule(user_email: str):
    cloud_delete_json(user_email, "schedule_job")


# ============================================================
# DATA + EMAIL HELPERS
# ============================================================
def load_uploaded_table(uploaded_file):
    name = uploaded_file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(uploaded_file)
    if name.endswith(".xlsx"):
        return pd.read_excel(uploaded_file, engine="openpyxl")
    if name.endswith(".xls"):
        return pd.read_excel(uploaded_file)
    raise ValueError("Please upload a CSV or Excel file.")


def clean_cell(value, fallback=""):
    if value is None or pd.isna(value):
        return fallback
    value = str(value).strip()
    return value if value else fallback


def is_valid_email(value):
    return bool(re.fullmatch(
        r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}",
        str(value).strip()
    ))


def render_template(template, values):
    return re.sub(
        r"\{([^{}]+)\}",
        lambda match: str(values.get(match.group(1).strip(), match.group(0))),
        template,
    )


def prepare_recipients(df):
    recipients, invalid, duplicates = [], [], []
    seen = set()

    for _, row in df.iterrows():
        email = clean_cell(row.get("email"))
        if not email:
            continue
        if not is_valid_email(email):
            invalid.append(email)
            continue
        key = email.lower()
        if key in seen:
            duplicates.append(email)
            continue
        seen.add(key)
        recipients.append({
            "email": email,
            "name": clean_cell(row.get("name"), "Professor"),
            "department": clean_cell(row.get("department"), "your department"),
            "university": clean_cell(row.get("university"), "your university"),
            "interest": clean_cell(row.get("interest"), "your research area"),
        })
    return recipients, invalid, duplicates


def get_saved_pdfs(user_email: str):
    udir = os.path.join(ATTACH_DIR, safe_user_key(user_email))
    os.makedirs(udir, exist_ok=True)
    files = []
    for filename in sorted(os.listdir(udir)):
        if filename.lower().endswith(".pdf"):
            path = os.path.join(udir, filename)
            with open(path, "rb") as f:
                files.append((filename, f.read()))
    return files


def make_message(sender, recipient, subject_template, body_template, attachments):
    subject = render_template(subject_template, recipient)
    body = render_template(body_template, recipient)

    msg = MIMEMultipart()
    msg["From"] = sender
    msg["To"] = recipient["email"]
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html", "utf-8"))

    for filename, content in attachments:
        part = MIMEBase("application", "pdf")
        part.set_payload(content)
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment", filename=filename)
        msg.attach(part)
    return msg


def send_batch(
    user_email: str,
    sender: str,
    password: str,
    recipients: list,
    subject: str,
    body: str,
    attachments: list,
    delay: int,
    skip_sent: bool,
    progress=None,
    pct_status=None,
    status=None,
):
    history = load_history(user_email)
    already_sent = set()
    if not history.empty and {"status", "email"}.issubset(history.columns):
        already_sent = set(
            history.loc[history["status"] == "SENT", "email"]
            .astype(str).str.strip().str.lower()
        )

    sent, failed, skipped = 0, 0, 0
    context = ssl.create_default_context()
    total = len(recipients)

    if pct_status:
        pct_status.markdown("**0% completed** (Connecting to Gmail SMTP...)")
    if progress:
        progress.progress(0)

    with smtplib.SMTP("smtp.gmail.com", 587, timeout=30) as server:
        server.starttls(context=context)
        server.login(sender.strip(), password.replace(" ", "").strip())

        for index, recipient in enumerate(recipients, start=1):
            email_key = recipient["email"].lower()

            if skip_sent and email_key in already_sent:
                skipped += 1
                if status:
                    status.info(f"Skipping {index}/{total}: already sent to {recipient['email']}")
            else:
                if status:
                    status.info(f"Sending {index}/{total} to {recipient['name']} ({recipient['email']})...")
                try:
                    message = make_message(sender, recipient, subject, body, attachments)
                    server.send_message(message)
                    append_history(
                        user_email,
                        recipient["email"], recipient["name"], recipient["university"],
                        "SENT", "Accepted by Gmail SMTP",
                    )
                    already_sent.add(email_key)
                    sent += 1
                except Exception as exc:
                    append_history(
                        user_email,
                        recipient["email"], recipient["name"], recipient["university"],
                        "FAILED", str(exc),
                    )
                    failed += 1

            fraction = index / total
            pct = int(round(fraction * 100))
            if progress:
                progress.progress(fraction)
            if pct_status:
                pct_status.markdown(
                    f"**{pct}% completed** — {index}/{total} processed (Sent: {sent} · Failed: {failed} · Skipped: {skipped})"
                )

            if index < total and delay > 0:
                time.sleep(delay)

    return sent, failed, skipped


# ============================================================
# SCHEDULER
# ============================================================
@st.cache_resource
def start_scheduler():
    def worker():
        while True:
            try:
                for u_email in list_all_cloud_users():
                    job = load_schedule(u_email)
                    if job and job.get("active"):
                        run_at = datetime.fromisoformat(job["run_at"])
                        if datetime.now() >= run_at:
                            job["active"] = False
                            save_schedule(u_email, job)

                            creds = load_credentials(u_email)
                            template = load_template(u_email)
                            df = load_saved_professors(u_email)
                            recipients, invalid, _ = prepare_recipients(df)
                            attachments = get_saved_pdfs(u_email)

                            if (creds["sender_email"] and creds["sender_password"]
                                    and recipients and not invalid):
                                send_batch(
                                    u_email,
                                    creds["sender_email"],
                                    creds["sender_password"],
                                    recipients,
                                    template["subject"],
                                    template["body"],
                                    attachments,
                                    int(job.get("delay_sec", 5)),
                                    bool(job.get("skip_already_sent", True)),
                                )
                            clear_schedule(u_email)
            except Exception:
                pass
            time.sleep(5)

    thread = threading.Thread(target=worker, daemon=True, name="ProfessorMailerScheduler")
    thread.start()
    return True


start_scheduler()


# ============================================================
# VISUAL DESIGN & NAVBAR
# ============================================================
if "ui_theme" not in st.session_state:
    st.session_state.ui_theme = "Dark"
if "auth_mode" not in st.session_state:
    st.session_state.auth_mode = "signin"

active_user = st.session_state.get("google_account_user")
is_light = st.session_state.ui_theme == "Light"

if is_light:
    theme_css = """
    :root { --bg:#f4f6fb; --surface:#ffffff; --surface2:#edf0f7; --line:rgba(22,32,54,.12); --muted:#667085; --text:#172033; }
    .stApp {background:var(--bg)!important;color:var(--text)!important;}
    [data-testid="stSidebar"] {background:#e9edf5!important;border-right:1px solid var(--line)!important;}
    h1,h2,h3,h4,.step-title {color:#172033!important;}
    p,label,.stMarkdown {color:#344054;}
    .hero {background:radial-gradient(circle at 88% 15%,rgba(141,128,255,.16),transparent 30%),linear-gradient(120deg,#ffffff,#eef1fb 70%,#f3efff);border-color:rgba(115,99,220,.2);}
    .hero p,.hero-steps li {color:#475467!important;}
    .hero-steps {background:rgba(255,255,255,.75);border-color:rgba(22,32,54,.10);}
    .hero-steps-title {color:#6255b5!important;}
    .hero-steps b {color:#202a44!important;}
    .brand-mark {color:#172033!important;}
    .nav-user-pill {background:#ffffff!important;color:#172033!important;border:1px solid #d0d5dd!important;}
    div[data-testid="stHorizontalBlock"]:has(.brand-mark) {background:rgba(244,246,251,.97)!important;}
    div[data-testid="stHorizontalBlock"]:has(.brand-mark) .brand-mark {color:#172033!important;}
    div[data-testid="stHorizontalBlock"]:has(.brand-mark) button {background:#ffffff!important;color:#172033!important;border:1px solid #d0d5dd!important;}
    .metric,.panel {background:#fff!important;border-color:var(--line)!important;}
    .metric .number {color:#172033!important;}
    .metric .label,.helper,.step-caption {color:#667085!important;}
    .stTextInput input,.stTextArea textarea,.stDateInput input,.stTimeInput input {background:#fff!important;color:#172033!important;border:1px solid #d0d5dd!important;}
    [data-testid="stFileUploader"] {background:#fff!important;border-color:#c5cada!important;}
    .status-card {background:#fff!important;color:#172033!important;}
    [data-testid="stTabs"] button {color:#344054!important;}
    [data-testid="stTabs"] button[aria-selected="true"] {color:#6255b5!important;}
    [data-testid="stAlert"] {background:#fff!important;}
    """
else:
    theme_css = """
    :root { --bg:#0c1020; --surface:#151b2d; --surface2:#1b2338; --line:rgba(255,255,255,.085); --muted:#98a3b8; --text:#f4f6fc; }
    """

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap');
:root { --accent:#8d80ff; --accent2:#b1a7ff; --nav-h:64px; }
html, body, [class*="css"] {font-family:'DM Sans',sans-serif;}
.stApp {background:var(--bg); color:var(--text);}
header[data-testid="stHeader"] {background:transparent; z-index:100002 !important; pointer-events:none;}
header[data-testid="stHeader"] button {pointer-events:auto !important;}

[data-testid="stSidebar"] {
  top: var(--nav-h) !important;
  height: calc(100vh - var(--nav-h)) !important;
  background: #111729;
  border-right: 1px solid var(--line);
  z-index: 99990 !important;
}
[data-testid="stSidebar"] .block-container {
  padding: 1.25rem 1.1rem 2rem !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="collapsedControl"] {
  top: 14px !important;
  left: 14px !important;
  z-index: 100005 !important;
  pointer-events: auto !important;
}

.block-container {max-width:1450px; padding:5.75rem 2.6rem 3rem !important;}
h1,h2,h3,h4 {color:var(--text)!important; letter-spacing:-.35px;}
p, label, .stMarkdown {color:#c0c7d7;}
.hero {
 background:radial-gradient(circle at 88% 15%,rgba(141,128,255,.22),transparent 30%),
 linear-gradient(120deg,#202744,#171d32 70%,#24213f);
 border:1px solid rgba(177,167,255,.18); border-radius:22px;
 padding:30px 34px; margin-bottom:22px;
}
.eyebrow {font-size:11px;letter-spacing:2px;font-weight:800;color:#b9afff;}
.hero h1 {font-size:32px!important;margin:9px 0 6px!important;}
.hero p {font-size:14px;color:#b8c1d5;margin:0;max-width:720px;line-height:1.65;}

div[data-testid="stHorizontalBlock"]:has(.brand-mark) {
  position:fixed!important;top:0!important;left:0!important;
  width:100vw!important;max-width:100vw!important;
  height:var(--nav-h)!important;min-height:var(--nav-h)!important;
  z-index:100000!important;box-sizing:border-box!important;
  display:flex!important;align-items:center!important;
  padding:8px 28px 8px 68px!important;margin:0!important;
  background:rgba(12,16,32,.96);backdrop-filter:blur(16px);
  border-bottom:1px solid var(--line);
}
div[data-testid="stHorizontalBlock"]:has(.brand-mark) [data-testid="column"]:last-child {
  display:flex;justify-content:flex-end;align-items:center;
}
div[data-testid="stHorizontalBlock"]:has(.brand-mark) button {
  height:40px;min-height:40px;padding:0 12px;border-radius:11px;
  background:#202944;color:#f4f6fc;border:1px solid var(--line);font-size:14px;
}
.brand-mark {font-size:20px;font-weight:900;letter-spacing:.4px;color:#f4f6fc;text-decoration:none;white-space:nowrap;}
.brand-mark span {color:#a99cff;}
.nav-right-wrap {display:flex;align-items:center;justify-content:flex-end;gap:10px;width:100%;}
.nav-user-pill {
  display:inline-flex;align-items:center;gap:7px;
  padding:7px 13px;border-radius:999px;
  background:#1b2338;color:#f4f6fc;border:1px solid var(--line);
  font-size:13px;font-weight:700;white-space:nowrap;
}
.hero-steps {margin:16px 0 0;padding:13px 16px;border-radius:13px;
 background:rgba(8,12,25,.30);border:1px solid rgba(255,255,255,.09);}
.hero-steps-title {font-size:11px;font-weight:800;letter-spacing:1.2px;color:#c9c2ff;margin-bottom:8px;}
.hero-steps ol {margin:0;padding-left:19px;display:grid;grid-template-columns:1fr 1fr;gap:7px 24px;}
.hero-steps li {font-size:12px;line-height:1.5;color:#d5daea;padding-left:2px;}
.hero-steps b {color:#fff;}
@media(max-width:700px){.hero-steps ol{grid-template-columns:1fr;}}
.hero-chip {display:inline-block;margin:17px 7px 0 0;padding:6px 11px;
 border-radius:30px;background:rgba(141,128,255,.12);color:#d2ccff;
 border:1px solid rgba(141,128,255,.2);font-size:10px;font-weight:700;}
.metric {background:var(--surface);border:1px solid var(--line);
 border-radius:15px;padding:17px 18px;min-height:105px;}
.metric .label {font-size:11px;color:var(--muted);font-weight:700;letter-spacing:.7px;}
.metric .number {font-size:27px;color:#fff;font-weight:800;margin-top:8px;}
.metric .symbol {font-size:18px;margin-bottom:5px;}
.panel {background:var(--surface);border:1px solid var(--line);
 border-radius:16px;padding:19px 20px;}
.helper {font-size:12px;color:var(--muted);line-height:1.6;}
.step-title {font-size:18px;font-weight:800;color:#fff;margin:8px 0 3px;}
.step-caption {font-size:12px;color:var(--muted);margin-bottom:16px;}
div.stButton>button {border-radius:10px;min-height:42px;font-weight:700;}
div.stButton>button[kind="primary"] {background:linear-gradient(100deg,#796bf2,#9a83ff);border:0;color:white;}
div.stButton>button[kind="primary"]:hover {border:0;filter:brightness(1.12);}
.stTextInput input,.stTextArea textarea,.stDateInput input,.stTimeInput input {
 background:#101729;color:#f4f6fc;border:1px solid var(--line);border-radius:9px;
}
[data-testid="stFileUploader"] {background:#101729;border:1px dashed #4b5570;border-radius:12px;padding:9px;}
[data-testid="stDataEditor"] {border:1px solid var(--line);border-radius:12px;overflow:hidden;}
div[data-testid="stTabs"] button {font-weight:700;}
div[data-testid="stTabs"] button[aria-selected="true"] {color:#c6bdff;}
hr {border-color:var(--line);}
.small-note {font-size:11px;color:#8792aa;}
.status-card {background:#111a2c;border:1px solid var(--line);padding:14px 16px;border-radius:12px;}
[data-testid="stAlert"] {border-radius:12px;}
/*THEME_CSS*/
@media(max-width:700px){
  div[data-testid="stHorizontalBlock"]:has(.brand-mark){padding:8px 16px 8px 56px!important;}
  .block-container{padding:5.5rem 1rem 2.5rem!important;}
}
</style>
""".replace("/*THEME_CSS*/", theme_css), unsafe_allow_html=True)

if active_user:
    nav_left, nav_user_col, nav_theme_col = st.columns([6.5, 2.5, 1], vertical_alignment="center")
    with nav_left:
        st.markdown('<div class="brand-mark">Zeeto<span style="color:#a99cff">.ai</span></div>', unsafe_allow_html=True)
    with nav_user_col:
        st.markdown(
            f'<div class="nav-right-wrap"><div class="nav-user-pill">👤 {active_user["name"]}</div></div>',
            unsafe_allow_html=True,
        )
    with nav_theme_col:
        theme_icon = "☀️" if st.session_state.ui_theme == "Dark" else "🌙"
        theme_help = "Switch to light mode" if st.session_state.ui_theme == "Dark" else "Switch to dark mode"
        if st.button(theme_icon, key="theme_toggle", help=theme_help):
            st.session_state.ui_theme = "Light" if st.session_state.ui_theme == "Dark" else "Dark"
            st.rerun()
else:
    nav_left, nav_theme_col = st.columns([8, 1], vertical_alignment="center")
    with nav_left:
        st.markdown('<div class="brand-mark">Zeeto<span style="color:#a99cff">.ai</span></div>', unsafe_allow_html=True)
    with nav_theme_col:
        theme_icon = "☀️" if st.session_state.ui_theme == "Dark" else "🌙"
        theme_help = "Switch to light mode" if st.session_state.ui_theme == "Dark" else "Switch to dark mode"
        if st.button(theme_icon, key="theme_toggle", help=theme_help):
            st.session_state.ui_theme = "Light" if st.session_state.ui_theme == "Dark" else "Dark"
            st.rerun()


# ============================================================
# DEFAULT SIGN-IN (EMAIL + PASSWORD) + BOTTOM SIGN-UP OPTION
# ============================================================
if not active_user:
    _, center_col, _ = st.columns([1.2, 1.8, 1.2])
    with center_col:
        if st.session_state.auth_mode == "signin":
            st.markdown("""
            <div class="hero" style="margin-bottom:16px;">
              <div class="eyebrow">ZEETO.AI · CLOUD OUTREACH WORKSPACE</div>
              <h1 style="font-size:26px!important;">Sign in with your Google Account</h1>
              <p>Apni Gmail ID aur account password daal kar sign in karein. Bina password ke koi aur aapka account access nahi kar sakta.</p>
            </div>
            """, unsafe_allow_html=True)

            si_email = st.text_input("Google / Gmail Address", placeholder="you@gmail.com", key="signin_email")
            si_password = st.text_input("Account Password", type="password", placeholder="Enter your password", key="signin_password")

            if st.button("🔐 Sign In", type="primary", use_container_width=True):
                clean_em = si_email.strip().lower()
                if not is_valid_email(clean_em):
                    st.error("Please enter a valid Google / Gmail address.")
                elif not si_password:
                    st.error("Please enter your password.")
                else:
                    profile = cloud_load_json(clean_em, "profile", None)
                    if not profile or not profile.get("password_hash"):
                        st.warning("Is Google ID se koi account nahi mila. Neeche 'Sign Up' par click karke pehle account banayein.")
                    elif not verify_password(si_password, profile["password_hash"], profile.get("password_salt", "")):
                        st.error("Incorrect email or password.")
                    else:
                        profile["last_login"] = datetime.now().isoformat()
                        cloud_save_json(clean_em, "profile", profile)
                        st.session_state.google_account_user = {
                            "email": clean_em,
                            "name": profile.get("name") or clean_em.split("@")[0],
                        }
                        st.rerun()

            st.divider()
            st.caption("Don't have an account yet?")
            if st.button("Create an account (Sign Up)", use_container_width=True, key="go_to_signup"):
                st.session_state.auth_mode = "signup"
                st.rerun()

        else:
            st.markdown("""
            <div class="hero" style="margin-bottom:16px;">
              <div class="eyebrow">NEW ACCOUNT · ZEETO.AI</div>
              <h1 style="font-size:26px!important;">Sign Up with your Google Account</h1>
              <p>Apna naam, Google / Gmail ID, aur ek strong password set karein. Account banne ke baad Sign In karein.</p>
            </div>
            """, unsafe_allow_html=True)

            su_name = st.text_input("Account Holder Name", placeholder="Enter your full name", key="signup_name")
            su_email = st.text_input("Google / Gmail Address", placeholder="you@gmail.com", key="signup_email")
            su_password = st.text_input("Create Password (min 6 chars)", type="password", placeholder="Create a password", key="signup_password")
            su_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password", key="signup_confirm")

            if st.button("✨ Create Account", type="primary", use_container_width=True):
                clean_em = su_email.strip().lower()
                if not su_name.strip():
                    st.error("Please enter your name.")
                elif not is_valid_email(clean_em):
                    st.error("Please enter a valid Google / Gmail address.")
                elif len(su_password) < 6:
                    st.error("Password must be at least 6 characters long.")
                elif su_password != su_confirm:
                    st.error("Passwords do not match.")
                else:
                    existing = cloud_load_json(clean_em, "profile", None)
                    if existing and existing.get("password_hash"):
                        st.warning("Is email se pehle se account maujood hai. Please Sign In karein.")
                        st.session_state.auth_mode = "signin"
                        st.rerun()
                    else:
                        pw_hash, pw_salt = hash_password(su_password)
                        cloud_save_json(clean_em, "profile", {
                            "email": clean_em,
                            "name": su_name.strip(),
                            "password_hash": pw_hash,
                            "password_salt": pw_salt,
                            "created_at": datetime.now().isoformat(),
                        })
                        st.success("Account created! Ab apne email aur password se Sign In karein.")
                        st.session_state.auth_mode = "signin"
                        st.rerun()

            st.divider()
            st.caption("Already have an account?")
            if st.button("← Back to Sign In", use_container_width=True, key="go_to_signin"):
                st.session_state.auth_mode = "signin"
                st.rerun()

    st.stop()


# ============================================================
# LOAD USER-SCOPED STATE
# ============================================================
user_email = active_user["email"]
user_state_key = f"loaded_user_{safe_user_key(user_email)}"

if not st.session_state.get(user_state_key):
    st.session_state.professor_data = load_saved_professors(user_email)
    saved_tpl = load_template(user_email)
    st.session_state.subject_value = saved_tpl["subject"]
    st.session_state.body_value = saved_tpl["body"]
    st.session_state[user_state_key] = True

saved_creds = load_credentials(user_email)
active_job = load_schedule(user_email)

# Sidebar
with st.sidebar:
    st.markdown(f"""
    <div style="padding:4px 0 12px">
      <div style="font-size:29px">🎓</div>
      <div style="font-size:19px;font-weight:800;color:var(--text)">Professor Mailer</div>
      <div style="font-size:10px;letter-spacing:1.4px;color:var(--muted)">OUTREACH WORKSPACE</div>
    </div>
    """, unsafe_allow_html=True)
    if st.button("🚪 Sign out", use_container_width=True):
        for k in list(st.session_state.keys()):
            if k.startswith("loaded_user_") or k in ("professor_data", "subject_value", "body_value"):
                del st.session_state[k]
        st.session_state.pop("google_account_user", None)
        st.session_state.auth_mode = "signin"
        st.rerun()
    st.divider()
    st.markdown("#### ⚙️ Account settings")
    sender_email = st.text_input(
        "Your Gmail address",
        value=saved_creds["sender_email"],
        placeholder="you@gmail.com",
    )
    sender_password = st.text_input(
        "Gmail app password",
        value=saved_creds["sender_password"],
        type="password",
        help="Use a Google App Password with 2-Step Verification enabled.",
    )
    remember = st.checkbox(
        "Remember credentials in cloud profile",
        value=saved_creds["remember"],
        help="Credentials are stored in your private cloud account profile.",
    )
    if st.button("Save account settings", use_container_width=True):
        save_credentials(user_email, sender_email, sender_password, remember)
        st.success("Account settings saved.")
    st.divider()
    st.markdown("#### Sending preferences")
    delay = st.select_slider(
        "Pause between emails",
        options=[2, 3, 5, 8, 10, 15, 20, 30],
        value=5,
        format_func=lambda x: f"{x} sec",
    )
    skip_already_sent = st.checkbox("Skip recipients emailed before", value=True)
    st.divider()
    st.markdown('<div class="helper">Tip: Keep your professor list and email template saved before scheduling a campaign.</div>', unsafe_allow_html=True)
    if os.path.exists(_user_store_path(user_email, "credentials.json")):
        if st.button("Forget saved credentials", use_container_width=True):
            cloud_delete_json(user_email, "credentials")
            st.rerun()


# ============================================================
# HEADER + TOP-LEVEL SUMMARY (ALL ORIGINAL FEATURES KEPT)
# ============================================================
st.markdown("""
<div class="hero">
  <div class="eyebrow">YOUR ACADEMIC OUTREACH, SIMPLIFIED</div>
  <h1>Reach the right professors.<br>One thoughtful email at a time.</h1>
  <p>Follow these steps to set up and send your professor outreach campaign:</p>
  <div class="hero-steps">
    <div class="hero-steps-title">HOW TO GET STARTED</div>
    <ol>
      <li><b>Connect your Gmail:</b> In Account settings on the left, enter your Gmail address and Google App Password, then click Save account settings. Use an App Password, not your regular Gmail password.</li>
      <li><b>Add professors:</b> Open Contacts to import a CSV/Excel file or enter professor details in the table. Check that each email address is correct.</li>
      <li><b>Prepare your email:</b> Open Email message, write your subject and message, personalize the template, and preview it for each professor.</li>
      <li><b>Attach documents:</b> Add your CV, research statement, or other supporting PDFs in the attachment area.</li>
      <li><b>Send or schedule:</b> Open Send or schedule, review the recipient list and settings, then send immediately or choose a date and time.</li>
      <li><b>Track your campaign:</b> Visit History to check sent and failed emails. Keep this app running for scheduled emails to be processed.</li>
    </ol>
  </div>
  <span class="hero-chip">CONTACTS</span><span class="hero-chip">EMAIL PREVIEW</span>
  <span class="hero-chip">SCHEDULED SENDING</span><span class="hero-chip">SENT HISTORY</span>
</div>
""", unsafe_allow_html=True)

recipients, invalid_emails, duplicate_emails = prepare_recipients(st.session_state.professor_data)
history = load_history(user_email)
sent_total = int((history["status"] == "SENT").sum()) if not history.empty else 0
failed_total = int((history["status"] == "FAILED").sum()) if not history.empty else 0

stats = [
    ("👥", "SAVED CONTACTS", len(recipients)),
    ("✉️", "EMAILS ACCEPTED", sent_total),
    ("⚠️", "INVALID ROWS", len(invalid_emails)),
    ("🗓️", "SCHEDULE", "Active" if active_job and active_job.get("active") else "None"),
]
cols = st.columns(4)
for col, (icon, label, value) in zip(cols, stats):
    with col:
        st.markdown(
            f'<div class="metric"><div class="symbol">{icon}</div>'
            f'<div class="label">{label}</div><div class="number">{value}</div></div>',
            unsafe_allow_html=True,
        )

st.write("")


# ============================================================
# SIMPLE WORKFLOW TABS
# ============================================================
tab_contacts, tab_message, tab_send, tab_history = st.tabs([
    "①  Contacts",
    "②  Email message",
    "③  Send or schedule",
    "④  History",
])


# -------------------- CONTACTS --------------------
with tab_contacts:
    st.markdown('<div class="step-title">Your professor list</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-caption">Add contacts manually or import a spreadsheet. Your changes are saved to your cloud account.</div>', unsafe_allow_html=True)

    import_col, download_col = st.columns([1.35, 1])
    with import_col:
        uploaded_contacts = st.file_uploader(
            "Import contacts (CSV or Excel)",
            type=["csv", "xlsx", "xls"],
            key="contact_import",
            help="Expected columns: email, name, department, university, interest.",
        )
        if uploaded_contacts is not None:
            try:
                incoming = load_uploaded_table(uploaded_contacts)
                incoming.columns = [str(c).strip().lower() for c in incoming.columns]
                for col in REQUIRED_COLS:
                    if col not in incoming.columns:
                        incoming[col] = ""
                st.session_state.professor_data = incoming[REQUIRED_COLS].fillna("")
                save_professors(user_email, st.session_state.professor_data)
                st.success(f"Imported {len(incoming)} contact rows.")
            except Exception as exc:
                st.error(f"Couldn't read that file: {exc}")
    with download_col:
        st.markdown('<div class="panel"><b style="color:var(--text)">New to the app?</b><p class="helper">Download a sample spreadsheet to see which columns are needed. You can fill it in and import it here.</p></div>', unsafe_allow_html=True)
        sample_csv = pd.DataFrame(columns=REQUIRED_COLS).to_csv(index=False).encode("utf-8")
        st.download_button(
            "⬇️ Download spreadsheet template",
            data=sample_csv,
            file_name="professor_contacts_template.csv",
            mime="text/csv",
            use_container_width=True,
        )

    edited_contacts = st.data_editor(
        st.session_state.professor_data,
        num_rows="dynamic",
        use_container_width=True,
        hide_index=True,
        key="contacts_editor",
        column_config={
            "email": st.column_config.TextColumn("Email address", required=True, width="large"),
            "name": st.column_config.TextColumn("Professor name", width="medium"),
            "department": st.column_config.TextColumn("Department", width="medium"),
            "university": st.column_config.TextColumn("University", width="medium"),
            "interest": st.column_config.TextColumn("Research area", width="large"),
        },
    )
    if not edited_contacts.equals(st.session_state.professor_data):
        st.session_state.professor_data = edited_contacts.copy()
        save_professors(user_email, edited_contacts)

    st.markdown("#### Remove saved contacts")
    df_for_delete = st.session_state.professor_data.reset_index(drop=True)
    if not df_for_delete.empty:
        row_options = list(df_for_delete.index)
        to_delete = st.multiselect(
            "Select contacts to remove",
            options=row_options,
            format_func=lambda idx: (
                f"{clean_cell(df_for_delete.loc[idx, 'name'], 'No Name')} "
                f"<{clean_cell(df_for_delete.loc[idx, 'email'], 'No Email')}> "
                f"({clean_cell(df_for_delete.loc[idx, 'university'], '-')})"
            ),
            key="contacts_to_delete",
        )
        del_col1, del_col2 = st.columns([1, 1])
        with del_col1:
            if st.button("🗑️ Remove selected contacts", use_container_width=True, disabled=not to_delete):
                updated_df = df_for_delete.drop(index=to_delete).reset_index(drop=True)
                st.session_state.professor_data = updated_df
                save_professors(user_email, updated_df)
                st.success(f"Removed {len(to_delete)} contact(s) and updated saved list.")
                st.rerun()
        with del_col2:
            if st.button("🧹 Clear all contacts", use_container_width=True):
                empty_df = pd.DataFrame(columns=REQUIRED_COLS)
                st.session_state.professor_data = empty_df
                save_professors(user_email, empty_df)
                st.success("All saved contacts cleared.")
                st.rerun()
    else:
        st.caption("No saved contacts to remove.")

    current_recipients, current_invalid, current_duplicates = prepare_recipients(st.session_state.professor_data)
    feedback_cols = st.columns(3)
    feedback_cols[0].metric("Ready to email", len(current_recipients))
    feedback_cols[1].metric("Invalid email rows", len(current_invalid))
    feedback_cols[2].metric("Duplicate rows", len(current_duplicates))
    if current_invalid:
        st.warning("Please correct these email addresses: " + ", ".join(current_invalid[:8]))
    if current_duplicates:
        st.info("Duplicate addresses are automatically ignored when sending.")
    left, right = st.columns([1, 1])
    with left:
        if st.button("💾 Save contact list", type="primary", use_container_width=True):
            save_professors(user_email, st.session_state.professor_data)
            st.success("Your contact list is saved.")
    with right:
        csv_data = st.session_state.professor_data.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Export my contacts", csv_data, "my_professors.csv", "text/csv", use_container_width=True)


# -------------------- EMAIL MESSAGE --------------------
with tab_message:
    st.markdown('<div class="step-title">Write your email once</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-caption">The app fills in each professor’s name, university, department, and research area automatically.</div>', unsafe_allow_html=True)

    st.info("Keep the message personal and accurate. Replace the sample identity details before sending.")
    subject_value = st.text_input(
        "Email subject",
        value=st.session_state.subject_value,
        key="subject_editor",
        help="You can use {name}, {university}, {department}, {interest}, and {email}.",
    )
    body_value = st.text_area(
        "Email body (HTML supported)",
        value=st.session_state.body_value,
        height=310,
        key="body_editor",
        help="Basic HTML such as <p>, <b>, and <br> is supported.",
    )
    st.session_state.subject_value = subject_value
    st.session_state.body_value = body_value
    if st.button("💾 Save email template", type="primary"):
        save_template(user_email, subject_value, body_value)
        st.success("Email template saved.")

    st.markdown("#### Personalization fields")
    st.caption("Use these exact placeholders in your subject or message:")
    st.code("{name}    {email}    {department}    {university}    {interest}", language="text")

    st.markdown("#### Preview your message")
    preview_list, _invalid, _duplicates = prepare_recipients(st.session_state.professor_data)
    if preview_list:
        chosen = st.selectbox(
            "Preview as",
            options=range(len(preview_list)),
            format_func=lambda i: f"{preview_list[i]['name']} · {preview_list[i]['university']}",
            key="preview_contact",
        )
        sample = preview_list[chosen]
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.markdown(f"**To:** `{sample['email']}`")
        st.markdown(f"**Subject:** {render_template(subject_value, sample)}")
        st.divider()
        st.markdown(render_template(body_value, sample), unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    else:
        st.warning("Add at least one valid professor email in the Contacts tab to preview the message.")


# -------------------- SEND / SCHEDULE --------------------
with tab_send:
    st.markdown('<div class="step-title">Ready to reach out?</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-caption">Choose whether to send your prepared message now or schedule it for later.</div>', unsafe_allow_html=True)

    send_recipients, send_invalid, send_duplicates = prepare_recipients(st.session_state.professor_data)
    live_subject = st.session_state.get("subject_editor", st.session_state.subject_value)
    live_body = st.session_state.get("body_editor", st.session_state.body_value)

    saved_attachments = get_saved_pdfs(user_email)
    uploaded_attachments = st.file_uploader(
        "Attach PDFs to this campaign",
        type=["pdf"],
        accept_multiple_files=True,
        key="campaign_pdfs",
        help="These files are included with this campaign only. Your saved attachments folder is also included.",
    )
    attachments_map = {name: content for name, content in saved_attachments}
    for file in uploaded_attachments or []:
        attachments_map[file.name] = file.getvalue()
    final_attachments = list(attachments_map.items())

    summary_cols = st.columns(3)
    summary_cols[0].metric("Recipients", len(send_recipients))
    summary_cols[1].metric("PDF attachments", len(final_attachments))
    summary_cols[2].metric("Delay", f"{delay} sec")

    with st.expander("Review campaign details", expanded=True):
        st.write("**Sender:**", sender_email or "Not configured")
        st.write("**Subject:**", render_template(live_subject, send_recipients[0]) if send_recipients else live_subject)
        st.write("**Skip previously sent:**", "Yes" if skip_already_sent else "No")
        if final_attachments:
            st.write("**Attachments:**", ", ".join(name for name, _ in final_attachments))
        else:
            st.caption("No PDF attachments selected.")

    if send_invalid:
        st.error("Fix invalid recipient addresses in Contacts before sending.")
    if not sender_email or not sender_password:
        st.warning("Add your Gmail address and App Password in Account settings in the left sidebar.")

    st.markdown("#### Send immediately")
    confirm = st.checkbox(
        f"I reviewed the message and approve sending to {len(send_recipients)} recipient(s).",
        key="confirm_campaign",
    )
    if st.button("✉️ Send campaign now", type="primary", use_container_width=True):
        if not sender_email or not sender_password:
            st.error("Please complete your Gmail account settings in the sidebar.")
        elif not send_recipients:
            st.error("There are no valid recipients. Add contacts first.")
        elif send_invalid:
            st.error("Please fix invalid email addresses before sending.")
        elif not confirm:
            st.warning("Please confirm the campaign before sending.")
        else:
            save_professors(user_email, st.session_state.professor_data)
            save_template(user_email, live_subject, live_body)
            pct_status = st.empty()
            progress = st.progress(0)
            status = st.empty()
            try:
                sent, failed, skipped = send_batch(
                    user_email, sender_email, sender_password, send_recipients,
                    live_subject, live_body, final_attachments,
                    delay, skip_already_sent, progress, pct_status, status,
                )
                pct_status.markdown(f"**100% completed** — Sent: {sent} · Failed: {failed} · Skipped: {skipped}")
                st.success(f"Finished. {sent} accepted by Gmail SMTP · {failed} failed · {skipped} skipped.")
                st.caption("SMTP acceptance is not confirmation that a message reached the recipient’s inbox.")
                time.sleep(1.5)
                st.rerun()
            except Exception as exc:
                st.error(f"Could not start the campaign: {exc}")

    st.divider()
    st.markdown("#### Schedule for later")
    date_col, time_col = st.columns(2)
    with date_col:
        schedule_date = st.date_input("Date", value=date.today(), key="schedule_date")
    with time_col:
        schedule_time = st.time_input("Time", value=dt_time(9, 0), key="schedule_time")

    if st.button("🗓️ Schedule this campaign", use_container_width=True):
        target = datetime.combine(schedule_date, schedule_time)
        if not sender_email or not sender_password:
            st.error("Please configure Gmail in the sidebar first.")
        elif not send_recipients:
            st.error("Add at least one valid recipient first.")
        elif send_invalid:
            st.error("Fix invalid email addresses before scheduling.")
        elif target <= datetime.now():
            st.error("Choose a future date and time.")
        else:
            save_credentials(user_email, sender_email, sender_password, remember)
            save_professors(user_email, st.session_state.professor_data)
            save_template(user_email, live_subject, live_body)
            udir = os.path.join(ATTACH_DIR, safe_user_key(user_email))
            os.makedirs(udir, exist_ok=True)
            for filename, content in final_attachments:
                path = os.path.join(udir, os.path.basename(filename))
                with open(path, "wb") as f:
                    f.write(content)
            save_schedule(user_email, {
                "active": True,
                "run_at": target.isoformat(),
                "delay_sec": delay,
                "skip_already_sent": skip_already_sent,
            })
            st.success(f"Campaign scheduled for {target.strftime('%b %d, %Y at %I:%M %p')}.")
            st.rerun()

    current_job = load_schedule(user_email)
    if current_job and current_job.get("active"):
        run_time = datetime.fromisoformat(current_job["run_at"])
        st.markdown(
            f'<div class="status-card">🟢 <b style="color:var(--text)">Scheduled campaign</b>'
            f'<div class="helper">Will run on {run_time.strftime("%A, %b %d, %Y at %I:%M %p")} '
            f'(server local time).</div></div>',
            unsafe_allow_html=True,
        )
        if st.button("Cancel scheduled campaign"):
            clear_schedule(user_email)
            st.success("Scheduled campaign cancelled.")
            st.rerun()


# -------------------- HISTORY --------------------
with tab_history:
    st.markdown('<div class="step-title">Your sending history</div>', unsafe_allow_html=True)
    st.markdown('<div class="step-caption">A record of email attempts made by this app under your account.</div>', unsafe_allow_html=True)

    history = load_history(user_email)
    if history.empty:
        st.info("Nothing here yet. Once you send a campaign, its activity will appear here.")
    else:
        sent_count = int((history["status"] == "SENT").sum())
        failed_count = int((history["status"] == "FAILED").sum())
        h1, h2, h3 = st.columns(3)
        h1.metric("Accepted by SMTP", sent_count)
        h2.metric("Failed", failed_count)
        h3.metric("Total attempts", len(history))

        filter_col, search_col = st.columns([1, 2])
        with filter_col:
            status_filter = st.selectbox("Show", ["All", "SENT", "FAILED"])
        with search_col:
            search_text = st.text_input("Find a professor or university", placeholder="Type a name, email, or university")

        filtered = history.copy()
        if status_filter != "All":
            filtered = filtered[filtered["status"] == status_filter]
        if search_text:
            mask = filtered.astype(str).apply(
                lambda col: col.str.contains(search_text, case=False, na=False)
            ).any(axis=1)
            filtered = filtered[mask]

        st.dataframe(filtered.iloc[::-1], use_container_width=True, hide_index=True)
        st.download_button(
            "⬇️ Download history (CSV)",
            filtered.to_csv(index=False).encode("utf-8"),
            "professor_mailer_history.csv",
            "text/csv",
        )

st.divider()
st.markdown(
    '<div class="small-note" style="text-align:center">PROFESSOR MAILER · A simpler workspace for thoughtful academic outreach</div>',
    unsafe_allow_html=True,
)