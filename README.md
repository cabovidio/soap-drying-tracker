# soap-drying-tracker
Streamlit app for QA tracking of soap weight using Google Sheets

# 🧼 Soap Drying Tracker

A lightweight Streamlit app for tracking the drying process of soap batches over time.  
Log daily weights, calculate retained weight %, visualize drying curves, and manage all your data through Google Sheets.

---

## 🚀 Features

- 📋 Create new soap batches with optional size/dimension data
- ➕ Log daily weight readings per batch
- 📉 View retained weight charts (% over time) with error bands
- 🔍 Browse individual soap details (batch info, drying history, graph)
- ❌ Delete soaps (with confirmation)
- 📊 Compare multiple soaps by name or category (type)
- 🧠 Surface area and drying metrics calculated automatically

---

## 🗂 Google Sheets Structure

### 1. **Soap Batches Sheet**
| Soap Name | Batch # | Type | Height | Width | Thickness | Surface Area | Notes | Initial Weight | Initial Date |
|-----------|----------|------|--------|-------|-----------|----------------|-------|------------------|--------------|

### 2. **Weight Readings Sheet**
| Soap Name | Batch # | Date | Weight (g) |
|-----------|----------|------|-------------|

> ✅ Be sure to share your Google Sheet with your service account email so it can be accessed from the app.

---

## ⚙️ Setup & Running the App

### 1. Clone the Repository
git clone https://github.com/yourusername/soap-drying-tracker.git
cd soap-drying-tracker

### 2. Install Requirements
pip install -r requirements.txt

### 3. Add Your Google API Credentials
Create a file at .streamlit/secrets.toml and paste your Google service account credentials like this:
[gcp_service_account]
type = "service_account"
project_id = "your-project"
private_key_id = "your-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n"
client_email = "your-service-account@your-project.iam.gserviceaccount.com"
client_id = "..."
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/..."
🔐 Your .streamlit/secrets.toml is used by Streamlit to authenticate with Google Sheets.

### 4. Run the App
streamlit run app.py
