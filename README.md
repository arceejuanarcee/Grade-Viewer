# 📘 ASE 4256 Grades Viewer

A simple **Streamlit web application** that allows students to securely
view their grades from a Google Sheets grading database by entering the
**last 6 digits of their student ID**.

This application connects to Google Sheets using a **Google Cloud
service account** and displays grades without exposing the entire
grading sheet.

------------------------------------------------------------------------

# Features

-    **Student Lookup**
    -   Students enter the **last 6 digits of their ID** to retrieve
        their grade.
-    **Multiple Grade Items**
    -   Instructor can configure which grade items students can view.
-    **Grade Breakdown**
    -   Optionally display precomputed grading components (e.g.,
        quizzes, seatworks, exams).
-    **Secure Access**
    -   Uses **Google Service Account credentials** stored in
        `st.secrets`.
-    **Fast Loading**
    -   Data is cached using `st.cache_data` for faster performance.

------------------------------------------------------------------------

# Application Interface

Students will:

1.  Enter the **last 6 digits of their ID**
2.  Select the **grade item**
3.  Click **View Grade**

If a record is found, the app will display:

-   The requested grade
-   Optional grade breakdown
-   A detailed record view

------------------------------------------------------------------------

# Project Structure

    grade-viewer/
    │
    ├── app.py
    ├── README.md
    └── .streamlit/
        └── secrets.toml

------------------------------------------------------------------------

# Google Sheet Requirements

Your Google Sheet must contain:

-   A **header row**
-   A column containing **student ID numbers**
-   Grade columns that match the configuration in `secrets.toml`

Example:

  --------------------------------------------------------------------------
  ID Number    Prelim Grade Prelim SW (20%) Prelim Q (30%) Prelim Exam (50%)
  ------------ ------------ --------------- -------------- -----------------
  2023123456   89           90              88             87

  --------------------------------------------------------------------------

------------------------------------------------------------------------

# Streamlit Secrets Configuration

Create:

`.streamlit/secrets.toml`

Example configuration:

    sheet_id = "YOUR_GOOGLE_SHEET_ID"
    id_column = "ID Number"
    worksheet_name = "Sheet1"

    [grade_columns]
    "Prelim Grade" = "Prelim Grade"
    "Midterm Grade" = "Midterm Grade"
    "Final Grade" = "Final Grade"

    [grade_details]
    "Prelim Grade" = ["Prelim SW (20%)", "Prelim Q (30%)", "Prelim Exam (50%)"]

    [gcp_service_account]
    type = "service_account"
    project_id = "your-project-id"
    private_key_id = "xxxx"
    private_key = "-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----\n"
    client_email = "your-service-account@project.iam.gserviceaccount.com"
    client_id = "xxxx"
    auth_uri = "https://accounts.google.com/o/oauth2/auth"
    token_uri = "https://oauth2.googleapis.com/token"
    auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
    client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."

------------------------------------------------------------------------

# Setup Instructions

## 1. Install Dependencies

    pip install streamlit pandas gspread google-auth
    or pip install -r requirements

------------------------------------------------------------------------

## 2. Run the Application

    streamlit run app.py

------------------------------------------------------------------------

# Security Design

The app is designed to protect student data:

-   Students only see **their own record**
-   Lookup is limited to **last 6 digits of ID**
-   Full sheet access is **restricted to the server**
-   Google credentials are stored securely in **Streamlit Secrets**

------------------------------------------------------------------------

# Example Workflow

Student input:

    Last 6 digits of ID: 123456
    Grade Item: Prelim Grade

Output:

    Record found ✅
    Prelim Grade: 89

Breakdown (if enabled):

    Prelim SW (20%): 90
    Prelim Q (30%): 88
    Prelim Exam (50%): 87

------------------------------------------------------------------------

# Notes for Instructors

-   The app **does not compute grades**.
-   It only displays **precomputed values from the Google Sheet**.
-   Any grading adjustments must be done **directly in the sheet**.

------------------------------------------------------------------------

# Author
Arcee T. Juan
Developed for **ASE 4256 -- Systems Dynamics and Vibrations**.
