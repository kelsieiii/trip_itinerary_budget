import streamlit as st
import pandas as pd
import openai
import os

# Load OpenAI key from Streamlit secrets
from streamlit import secrets

openai.api_key = secrets["OPENAI_API_KEY"]

# ** DEBUG **
st.write("🔑 API key prefix:", openai.api_key[:5], "...", 
         "length:", len(openai.api_key))

# ── Import your three scripts as modules ────────────────────────────────────
from cleaning import clean_csv
from itinerary import generate_itinerary_df
from budget import calculate_budget

# ── Streamlit page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Trip Itinerary & Budget Generator",
    layout="centered",
    initial_sidebar_state="auto"
)

# ── Sidebar with instructions ───────────────────────────────────────────────
with st.sidebar:
    st.title("🏷️ Quick Start")
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
st.dataframe(cleaned_df.head(5))

# ── 3) Generate the itinerary ────────────────────────────────────────────────
with st.spinner("✈️ Generating itinerary… (this may take 30–60s)"):
    itin_df = generate_itinerary_df(cleaned_df)
st.success("✅ Itinerary generated")

# Show a peek
st.subheader("Itinerary Preview")
st.dataframe(itin_df.head(5))

# ── 4) Calculate the budget ──────────────────────────────────────────────────
with st.spinner("💰 Calculating budget…"):
    budget_df = calculate_budget(itin_df)
st.success("✅ Budget calculated")

# Show a peek
st.subheader("Budget Preview")
st.dataframe(budget_df.head(5))

# Display the grand‐total right here
grand_total = budget_df["Total (RMB)"].sum()
st.markdown(f"**🎉 Grand Total Budget: RMB {grand_total:,.2f}**")

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
