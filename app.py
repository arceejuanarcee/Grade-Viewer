import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials

st.set_page_config(page_title="Grades Viewer", page_icon="📘", layout="centered")

def require_secret(key: str):
    if key not in st.secrets:
        # Safe debug: show only available keys, not values
        available = sorted(list(st.secrets.keys()))
        raise RuntimeError(
            f"Missing secret: '{key}'. Available top-level keys: {available}. "
            "Check spelling, top-level placement, and TOML syntax."
        )

# ---- REQUIRED secrets
require_secret("sheet_id")
require_secret("id_column")
require_secret("grade_columns")
require_secret("gcp_service_account")

SHEET_ID = st.secrets["sheet_id"]
ID_COL = st.secrets["id_column"]
GRADE_COLUMNS = dict(st.secrets["grade_columns"])  # label -> column header
WORKSHEET_NAME = st.secrets.get("worksheet_name", None)

# OPTIONAL secret (you will configure this):
# [grade_details]
# "Prelim Grade" = ["Prelim SW (20%)", "Prelim Q (30%)", "Prelim Exam (50%)"]
GRADE_DETAILS = dict(st.secrets.get("grade_details", {}))

def get_gspread_client() -> gspread.Client:
    sa_info = dict(st.secrets["gcp_service_account"])

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets.readonly",
        "https://www.googleapis.com/auth/drive.readonly",
    ]
    creds = Credentials.from_service_account_info(sa_info, scopes=scopes)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_sheet() -> pd.DataFrame:
    gc = get_gspread_client()
    sh = gc.open_by_key(SHEET_ID)

    ws = sh.worksheet(WORKSHEET_NAME) if WORKSHEET_NAME else sh.get_worksheet(0)

    records = ws.get_all_records()  # expects header row
    df = pd.DataFrame(records)
    df.columns = [str(c).strip() for c in df.columns]
    return df

def find_student(df: pd.DataFrame, last6: str) -> pd.DataFrame:
    ids = df[ID_COL].astype(str).str.replace(".0", "", regex=False).str.strip()
    return df[ids.str[-6:] == last6].copy()

# ---- UI
st.title("ASE 4256 Grades Viewer")
st.caption("Enter the **last 6 digits** of your ID Number and select what you want to view.")

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

    try:
        df = load_sheet()
    except Exception as e:
        st.error("Could not load the Google Sheet using the service account.")
        st.exception(e)
        st.stop()

    # Validate columns exist
    if ID_COL not in df.columns:
        st.error(f"ID column '{ID_COL}' not found.")
        st.write("Columns found:", list(df.columns))
        st.stop()

    target_col = GRADE_COLUMNS[selected_label]
    if target_col not in df.columns:
        st.error(f"Grade column '{target_col}' not found (configured as '{selected_label}').")
        st.write("Columns found:", list(df.columns))
        st.stop()

    matches = find_student(df, last6)

    if matches.empty:
        st.warning("No record found for that ID (last 6 digits). Please double-check.")
        st.stop()

    if len(matches) > 1:
        st.warning("Multiple records matched that last-6 ID pattern. Please contact your instructor.")
        st.stop()

    row = matches.iloc[0]
    value = row.get(target_col, "")

    st.success("Record found ✅")
    st.metric(label=selected_label, value=str(value))

    # ---- Policy note (shown only for Prelim Grade)
    if selected_label.lower() == "prelim grade":
        st.info(
        "📌 **Important:** The Prelim Grade shown is based strictly on the computed "
        "values in the grading sheet. **No rounding up or manual adjustment** "
        "has been applied."
        )


    # ---- Transparency feature (no computation): show precomputed breakdown columns
    detail_cols = GRADE_DETAILS.get(selected_label, [])
    if detail_cols:
        st.subheader("Breakdown (precomputed)")

        missing = [c for c in detail_cols if c not in df.columns]
        if missing:
            st.warning(f"Some breakdown columns are missing in the sheet: {missing}")

        present_cols = [c for c in detail_cols if c in df.columns]

        # Show as metrics (quick to read)
        for c in present_cols:
            st.metric(label=c, value=str(row.get(c, "")))

        # Show as a table (optional)
        with st.expander("View breakdown as table"):
            show_cols = [ID_COL, target_col] + present_cols
            safe_df = matches[show_cols].copy()

            # Rename for display
            rename_map = {target_col: selected_label}
            safe_df = safe_df.rename(columns=rename_map)

            st.dataframe(safe_df, hide_index=True)

    # ---- Original details (kept)
    with st.expander("Details"):
        safe_df = matches[[ID_COL, target_col]].copy()
        safe_df.columns = ["ID Number", selected_label]
        st.dataframe(safe_df, hide_index=True)
