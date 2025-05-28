import streamlit as st
st.set_page_config(
    page_title="Soap Drying Tracker",
    page_icon="🧼",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Now import everything else
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import altair as alt
from graphing import plot_retained_weight_from_gs
import matplotlib.pyplot as plt
import math
import streamlit.components.v1 as components
import os
import json
from oauth2client.service_account import ServiceAccountCredentials


# Clicks the “☰” menu toggle if it’s visible (collapsed) so it ensures the sidebar is shown on page load
components.html("""
    <script>
    window.onload = function() {
        const sidebar = window.parent.document.querySelector("section[data-testid='stSidebar']");
        if (sidebar) sidebar.style.display = 'block';
        const toggle = window.parent.document.querySelector("button[title='Open sidebar']");
        if (toggle) toggle.click();
    }
    </script>
    <link rel="manifest" href="/public/manifest.json">
    <link rel="icon" type="image/png" sizes="512x512" href="/public/favicon.png">
""", height=0)


scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Load from environment variable and parse JSON
gcp_secret = json.loads(os.environ["GCP_CREDS"])
creds = ServiceAccountCredentials.from_json_keyfile_dict(gcp_secret, scope)

client = gspread.authorize(creds)

# Open spreadsheet
sheet = client.open("Soap Weight Loss Tracker")
batches = sheet.worksheet("Soap Batches")
readings = sheet.worksheet("Weight Readings")

# Sidebar menu
st.sidebar.title("📋 Menu")
page = st.sidebar.radio("Choose an action", [
    "Overview",
    "View Soap Details",
    "Add Weight Reading",
    "Create New Soap",
    "Delete a Soap"
])

# Helper function to get soap labels
def get_soap_labels():
    soap_rows = batches.get_all_records()
    return [f"{row['Soap Name']} (Batch {row['Batch #']})" for row in soap_rows], soap_rows

if page == "Create New Soap":
    st.subheader("🧼 Create New Soap Batch")
    with st.form("create_soap_form"):
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Soap Name (required)")
            batch = st.text_input("Batch Number (optional)")
            category = st.text_input("Soap Type / Category (optional)")
            height = st.number_input("Height (mm)", min_value=0.0, step=1.0, format="%.1f")
            width = st.number_input("Width (mm)", min_value=0.0, step=1.0, format="%.1f")
            thickness = st.number_input("Thickness (mm)", min_value=0.0, step=1.0, format="%.1f")
        with col2:
            notes = st.text_area("Notes (optional)")
            init_weight = st.number_input("Initial Weight (g) (required)", min_value=0.0)
            init_date = st.date_input("Initial Date (required)")

        surface_area = height * width * thickness if height and width and thickness else ""

        submitted = st.form_submit_button("Create Soap")

        if submitted:
            if not name or not init_weight or not init_date:
                st.error("❗ Please provide at least a Soap Name, Initial Weight, and Initial Date.")
            else:
                # Fill missing values with empty strings
                batch = batch or ""
                category = category or ""
                notes = notes or ""
                surface_area = surface_area or ""

                batches.append_row([
                    name, batch, category, height, width, thickness,
                    surface_area, notes, init_weight, init_date.strftime("%Y-%m-%d")
                ])
                readings.append_row([name, batch, init_date.strftime("%Y-%m-%d"), init_weight])
                st.success("✅ Soap batch created and first reading added!")


# Add weight
elif page == "Add Weight Reading":
    st.subheader("➕ Add Daily Weight Reading")
    labels, soap_rows = get_soap_labels()
    if labels:
        selected = st.selectbox("Select Soap", labels)
        name, batch = selected.split(" (Batch ")
        batch = batch.rstrip(")")

        # Load readings into a DataFrame
        reading_df = pd.DataFrame(readings.get_all_records())
        reading_df["Date"] = pd.to_datetime(reading_df["Date"], errors="coerce")
        reading_df["Weight (g)"] = pd.to_numeric(reading_df["Weight (g)"], errors="coerce")

        # Filter readings for the selected soap
        soap_readings = reading_df[
            (reading_df["Soap Name"] == name) & (reading_df["Batch #"] == batch)
        ].sort_values("Date")

        if not soap_readings.empty:
            latest = soap_readings.sort_values("Date", ascending=False).iloc[0]
            last_weight = latest["Weight (g)"]
            last_date = latest["Date"].strftime("%Y-%m-%d")
            st.markdown(f"**📏 Last Recorded Weight**: {last_weight:.1f} g on {last_date}")
        else:
            st.markdown("No previous readings found.")

        date = st.date_input("Reading Date")
        weight = st.number_input("Reading Weight (g)", min_value=0.0)
        if st.button("Add Reading"):
            readings.append_row([name, batch, date.strftime("%Y-%m-%d"), weight])
            st.success("✅ Reading added.")
    else:
        st.info("No soaps found. Create one first.")

# Delete soap
elif page == "Delete a Soap":
    st.subheader("❌ Delete a Soap Batch")
    labels, soap_rows = get_soap_labels()
    if labels:
        selected = st.selectbox("Select Soap to Delete", labels)
        warning = st.checkbox("⚠️ Yes, I really want to delete this soap and all its readings.")
        if warning and st.button("Delete"):
            name, batch = selected.split(" (Batch ")
            batch = batch.rstrip(")")
            # Filter and rewrite batches
            all_batch_rows = batches.get_all_values()
            updated_batch_rows = [row for row in all_batch_rows if not (row[0] == name and row[1] == batch)]
            batches.clear()
            batches.append_rows(updated_batch_rows)
            # Filter and rewrite readings
            all_reading_rows = readings.get_all_values()
            updated_reading_rows = [row for row in all_reading_rows if not (row[0] == name and row[1] == batch)]
            readings.clear()
            readings.append_rows(updated_reading_rows)
            st.success("🗑️ Soap and readings deleted.")
    else:
        st.info("No soaps to delete.")

# View soap
elif page == "View Soap Details":
    st.subheader("🔍 View Soap Details")

    # Load data
    batch_df = pd.DataFrame(batches.get_all_records())
    reading_df = pd.DataFrame(readings.get_all_records())

    if batch_df.empty:
        st.info("No soaps in your database yet.")
    else:
        reading_df["Date"] = pd.to_datetime(reading_df["Date"], dayfirst=True)
        reading_df["Weight (g)"] = pd.to_numeric(reading_df["Weight (g)"], errors="coerce")

        # Calculate last edit date per soap
        reading_df["Label"] = reading_df.apply(
            lambda r: f"{r['Soap Name']} (Batch {r['Batch #']})", axis=1
        )
        last_dates = reading_df.groupby("Label")["Date"].max().sort_values(ascending=False)

        sorted_labels = last_dates.index.tolist()
        selected_label = st.selectbox("📦 Select a soap", sorted_labels)

        soap_name, batch = selected_label.split(" (Batch ")
        batch = batch.rstrip(")")

        batch_row = batch_df[(batch_df["Soap Name"] == soap_name) & (batch_df["Batch #"] == batch)]

        if batch_row.empty:
            st.error("⚠️ Could not find soap batch data.")
        else:
            row = batch_row.iloc[0]
            col1, col2 = st.columns(2)

            with col1:
                st.markdown(f"**Soap Name**: {row['Soap Name']}")
                st.markdown(f"**Batch #**: {row['Batch #']}")
                st.markdown(f"**Type**: {row.get('Type', 'Uncategorized')}")
                st.markdown(f"**Notes**: {row.get('Notes', '-')}")
            with col2:
                st.markdown(f"**Dimensions**: {row['Height']} x {row['Width']} x {row['Thickness']} mm")
                try:
                    sa = row["Surface Area"]
                    if pd.isna(sa) or sa == "":
                        sa = float(row["Height"]) * float(row["Width"]) * float(row["Thickness"])
                        st.markdown(f"**Surface Area**: {sa:.0f} mm³ (calculated)")
                    else:
                        st.markdown(f"**Surface Area**: {sa} mm³")
                except:
                    st.markdown("**Surface Area**: Unknown")
                st.markdown(f"**Baseline Weight**: {row['Initial Weight']} g")
                st.markdown(f"**Initial Date**: {row['Initial Date']}")

            # Readings table
            soap_readings = reading_df[
                (reading_df["Soap Name"] == soap_name) &
                (reading_df["Batch #"] == batch)
            ].sort_values("Date")

            st.markdown("### 📋 Daily Weights")
            st.dataframe(soap_readings[["Date", "Weight (g)"]].reset_index(drop=True))


            st.markdown("### 📈 Weight Loss Over Time")

            # Sort + calculate baseline and days
            soap_readings = soap_readings.copy()
            soap_readings = soap_readings.sort_values("Date")
            baseline_date = soap_readings["Date"].iloc[0]
            baseline_weight = soap_readings["Weight (g)"].iloc[0]
            soap_readings["Days Since Baseline"] = (soap_readings["Date"] - baseline_date).dt.days

            # Determine Y-axis lower limit
            min_weight = soap_readings["Weight (g)"].min()
            y_floor = min(min_weight, baseline_weight * 0.95)

            # Plot
            fig, ax = plt.subplots()

            ax.plot(
                soap_readings["Days Since Baseline"],
                soap_readings["Weight (g)"],
                marker="o",
                label="Weight (g)"
            )

            # Display actual values as data labels
            #for x, y in zip(soap_readings["Days Since Baseline"], soap_readings["Weight (g)"]):
            #    ax.text(x, y, f"{y:.1f}g", fontsize=8, ha='center', va='bottom')

            ax.set_xlabel("Days Since Baseline")
            ax.set_ylabel("Weight (g)")
            ax.set_title("Weight Loss Over Time")
            ax.grid(True)

            # Y starts at dynamic minimum
            ax.set_ylim(bottom=y_floor)

            # X always shows at least 10 days
            max_day = soap_readings["Days Since Baseline"].max()
            ax.set_xlim(0, max(10, math.ceil(max_day)))

            st.pyplot(fig)




# View Graphs
elif page == "Overview":
    st.subheader("📊 Weight Curves")
 
    plot_retained_weight_from_gs(readings,batches)

 
