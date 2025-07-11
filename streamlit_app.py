import streamlit as st
import pandas as pd
import openai
import os

# Load OpenAI key from Streamlit secrets
from streamlit import secrets

openai.api_key = secrets["OPENAI_API_KEY"]

st.set_page_config(layout="wide")  # <- forces the app to use the full width of the screen

# ** DEBUG **
# st.write("🔑 API key prefix:", openai.api_key[:5], "...", "length:", len(openai.api_key))

# ── Import your three scripts as modules ────────────────────────────────────
from cleaning import clean_csv
from itinerary import generate_itinerary_df
from budget import calculate_budget

# ── Streamlit page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Trip Itinerary & Budget Generator",
    layout="wide",
    initial_sidebar_state="auto"
)

# ── Sidebar with instructions ───────────────────────────────────────────────
with st.sidebar:
    st.title("🏷️ How to use")
    st.markdown("""
    1. Upload your **raw** trip CSV  
    2. Wait while we clean, plan & cost it  
    3. Download **itinerary.csv** & **budget.csv**
    """)

# ── App header ───────────────────────────────────────────────────────────────
st.title("📅 Trip Itinerary & Budget Generator")
st.write("Upload your original CSV below and receive both an LLM-generated itinerary and a detailed budget sheet.")

# ── 1) File uploader ─────────────────────────────────────────────────────────
uploaded = st.file_uploader("🔄 Upload raw trip CSV", type="csv")
if not uploaded:
    st.info("Please upload a CSV to get started.")
    st.stop()

# read raw CSV
raw_df = pd.read_csv(uploaded)
st.success("✅ File uploaded!")

# ── 2) Clean the data ────────────────────────────────────────────────────────
with st.spinner("🧹 Cleaning data…"):
    cleaned_df = clean_csv(raw_df)
st.success("✅ Data cleaned")

# Show a peek
st.subheader("Cleaned Data Preview")
st.dataframe(cleaned_df.head(5),use_container_width=True)

# ── 3) Generate the itinerary ────────────────────────────────────────────────
with st.spinner("✈️ Generating itinerary… (this may take 30–60s)"):
    itin_df = generate_itinerary_df(cleaned_df)
st.success("✅ Itinerary generated")

# Show a peek
st.subheader("Itinerary Preview")
for idx, row in itin_df.iterrows():
    st.markdown(f"**Day {idx + 1}:**<br>{row['itinerary']}", unsafe_allow_html=True)

# ── 4) Calculate the budget ──────────────────────────────────────────────────
with st.spinner("💰 Calculating budget…"):
    budget_df = calculate_budget(itin_df)
st.success("✅ Budget calculated")

# Show
st.subheader("Budget Preview")
st.dataframe(budget_df.head(100),use_container_width=True)
# Get the USD grand total row safely
usd_row = budget_df.loc[budget_df["City/Trip"].astype(str).str.strip() == "GRAND TOTAL"]
if not usd_row.empty and "Total (USD)" in usd_row.columns:
    usd_total = usd_row["Total (USD)"].values[0]
    st.markdown(f"### 🧾 Total Estimated Cost in USD: **${usd_total:,.2f}**")
else:
    st.warning("⚠️ USD total not found in budget.")

# ── 5) Download buttons ──────────────────────────────────────────────────────
st.markdown("---")
col1, col2 = st.columns(2)

csv_itin   = itin_df.to_csv(index=False).encode("utf-8")
csv_budget = budget_df.to_csv(index=False).encode("utf-8")

with col1:
    st.download_button(
        label="📥 Download Itinerary CSV",
        data=csv_itin,
        file_name="itinerary.csv",
        mime="text/csv",
    )

with col2:
    st.download_button(
        label="📥 Download Budget CSV",
        data=csv_budget,
        file_name="budget.csv",
        mime="text/csv",
    )
