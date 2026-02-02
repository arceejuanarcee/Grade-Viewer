import re
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Grades Viewer", page_icon="📘", layout="centered")

# ----------------------------
# Helpers
# ----------------------------
def _require_secret(key: str):
    if key not in st.secrets:
        raise RuntimeError(f"Missing secret: '{key}'. Please set it in secrets.toml.")

def build_csv_export_url(sheet_url: str) -> str:
    """
    Converts a standard Google Sheets URL into a CSV export URL.
    Requires the sheet/tab to be accessible (e.g., 'Anyone with the link: Viewer').
    """
    sheet_url = sheet_url.strip()

    m = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if not m:
        raise ValueError("Could not find SHEET_ID in the provided sheet_url.")
    sheet_id = m.group(1)

    gid_match = re.search(r"gid=([0-9]+)", sheet_url)
    gid = gid_match.group(1) if gid_match else "0"

    return f"https://docs.google.com/spreadsheets/d/{sheet_id}/export?format=csv&gid={gid}"

@st.cache_data(ttl=60)
def load_sheet(csv_url: str) -> pd.DataFrame:
    # Load the sheet tab as CSV
    df = pd.read_csv(csv_url)

    # Normalize column names
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_student_row(df: pd.DataFrame, id_col: str, last6: str) -> pd.DataFrame:
    ids = df[id_col].astype(str).str.replace(".0", "", regex=False).str.strip()
    return df[ids.str[-6:] == last6].copy()

# ----------------------------
# Load config from secrets
# ----------------------------
_require_secret("sheet_url")
_require_secret("id_column")
_require_secret("grade_columns")

SHEET_URL = st.secrets["sheet_url"]
ID_COL = st.secrets["id_column"]

# This is a dict like {"Quiz #1": "Quiz 1 Scores", ...}
GRADE_COLUMNS = dict(st.secrets["grade_columns"])

# ----------------------------
# UI
# ----------------------------
st.title("📘 Grades Viewer")

st.caption(
    "Enter the **last 6 digits** of your ID Number, then choose which grade item to view."
)

grade_labels = list(GRADE_COLUMNS.keys())

with st.form("lookup_form"):
    last6 = st.text_input("Last 6 digits of ID", max_chars=6, placeholder="e.g., 123456")
    selected_label = st.selectbox("Select grade item", grade_labels, index=0)
    submitted = st.form_submit_button("View Grade")

if submitted:
    last6 = (last6 or "").strip()
    if not (last6.isdigit() and len(last6) == 6):
        st.error("Please enter exactly **6 digits** (numbers only).")
        st.stop()

    # Build CSV URL + load sheet
    try:
        csv_url = build_csv_export_url(SHEET_URL)
        df = load_sheet(csv_url)
    except Exception as e:
        st.error("Could not load the Google Sheet. Make sure it is viewable via link.")
        st.exception(e)
        st.stop()

    # Validate columns exist
    if ID_COL not in df.columns:
        st.error(f"ID column '{ID_COL}' was not found in the sheet.")
        st.write("Columns found:", list(df.columns))
        st.stop()

    target_col = GRADE_COLUMNS[selected_label]
    if target_col not in df.columns:
        st.error(f"Configured grade column '{target_col}' was not found in the sheet.")
        st.write("Columns found:", list(df.columns))
        st.stop()

    # Find student
    matches = find_student_row(df, ID_COL, last6)

    if matches.empty:
        st.warning("No record found for that ID (last 6 digits). Please double-check.")
        st.stop()

    if len(matches) > 1:
        st.warning(
            "Multiple records matched that last-6 ID pattern. "
            "Please contact your instructor/admin to fix duplicates."
        )
        st.stop()

    row = matches.iloc[0]
    value = row.get(target_col, "")

    st.success("Record found ✅")
    st.metric(label=selected_label, value=str(value))

    # Optional: show only the selected value + ID (privacy-safe)
    with st.expander("Details"):
        safe_df = matches[[ID_COL, target_col]].copy()
        safe_df.columns = ["ID Number", selected_label]
        st.dataframe(safe_df, hide_index=True)
