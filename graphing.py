import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import math

def plot_retained_weight_from_gs(readings_sheet, batches_sheet):
    st.subheader("📉 Retained Weight Curves by Soap Batch")

    # Load data
    readings_df = pd.DataFrame(readings_sheet.get_all_records())
    batches_df = pd.DataFrame(batches_sheet.get_all_records())

    if readings_df.empty or batches_df.empty:
        st.info("No readings or batch info available.")
        return

    readings_df["Date"] = pd.to_datetime(readings_df["Date"], dayfirst=True)
    readings_df["Weight (g)"] = pd.to_numeric(readings_df["Weight (g)"], errors="coerce")

    # Safe merge, allow missing batch/type
    batches_df["Type"] = batches_df.get("Type", "Uncategorized")
    df = pd.merge(readings_df, batches_df[["Soap Name", "Batch #", "Type"]],
                  on=["Soap Name", "Batch #"], how="left")

    df["Type"] = df["Type"].fillna("Uncategorized")

    # Build a label column that tolerates missing values
    def make_label(row):
        name = row["Soap Name"]
        batch = row.get("Batch #", "").strip()
        typ = row.get("Type", "Uncategorized").strip()
        label = name
        if batch:
            label += f" (Batch {batch})"
        if typ:
            label += f" – {typ}"
        return label

    df["Label"] = df.apply(make_label, axis=1)

    # Filter UI
    st.markdown("### Filters")
    all_types = sorted(df["Type"].dropna().unique())
    selected_type = st.selectbox("📂 Filter by soap type/category", ["All"] + all_types)
    search = st.text_input("🔍 Filter by soap name (optional)")

    # Apply filters
    if selected_type != "All":
        df = df[df["Type"] == selected_type]
    if search:
        df = df[df["Soap Name"].str.lower().str.contains(search.lower())]

    if df.empty:
        st.warning("No data matches your filters.")
        return

    # Start plotting
    fig, ax = plt.subplots()
    max_day = 0
    min_retained = 1

    for label in df["Label"].unique():
        soap_df = df[df["Label"] == label].copy()
        soap_df = soap_df.sort_values("Date")

        if soap_df.empty or soap_df.shape[0] < 2:
            continue

        baseline_weight = soap_df.iloc[0]["Weight (g)"]
        if pd.isna(baseline_weight) or baseline_weight == 0:
            continue

        soap_df["Days Since Baseline"] = (soap_df["Date"] - soap_df["Date"].iloc[0]).dt.days
        soap_df["Total Loss (%)"] = (baseline_weight - soap_df["Weight (g)"]) / baseline_weight
        soap_df["Retained (%)"] = 1 - soap_df["Total Loss (%)"]

        if 0 not in soap_df["Days Since Baseline"].values:
            soap_df = pd.concat([
                pd.DataFrame({
                    "Days Since Baseline": [0],
                    "Retained (%)": [1.0]
                }),
                soap_df[["Days Since Baseline", "Retained (%)"]]
            ], ignore_index=True)

        soap_df = soap_df.sort_values("Days Since Baseline")
        max_day = max(max_day, soap_df["Days Since Baseline"].max())
        min_retained = min(min_retained, soap_df["Retained (%)"].min())

        line, = ax.plot(
            soap_df["Days Since Baseline"],
            soap_df["Retained (%)"],
            marker="o",
            label=label
        )

        error_pct = 0.1 / baseline_weight
        ax.fill_between(
            soap_df["Days Since Baseline"],
            soap_df["Retained (%)"] - error_pct,
            soap_df["Retained (%)"] + error_pct,
            color=line.get_color(),
            alpha=0.2,
            linewidth=0
        )

    # Final formatting
    max_x = max(10, math.ceil(max_day))
    y_min = min(0.9, min_retained)

    ax.set_xlim(0, max_x)
    ax.set_ylim(y_min, 1)
    ax.xaxis.get_major_locator().set_params(integer=True)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{int(y * 100)}%"))
    ax.set_xlabel("Days Since Baseline")
    ax.set_ylabel("Retained Weight (%)")
    ax.set_title("Soap Retained Weight Over Time")
    ax.grid(True)
    ax.legend()
    st.pyplot(fig)
