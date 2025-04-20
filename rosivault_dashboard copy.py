# rosivault_dashboard.py — Streamlit dashboard for ROSIVault

import streamlit as st
from app.llm.langchain_agent import ask_question
import pandas as pd
import matplotlib.pyplot as plt
import re
from collections import defaultdict

st.set_page_config(page_title="ROSIVault AI", layout="wide", page_icon="🔐")

st.sidebar.title("📂 ROSIVault Navigation")
view = st.sidebar.radio("Go to", [
    "💬 Ask AI",
    "📊 KPI Dashboard",
    "🔍 ROSI Insights",
    "🛠️ Tools & Vendors",
    "📌 ES&F Domain View",
    "🧠 Capability Graph View"
])

st.title("🔐 ROSIVault: AI Security Investment Assistant")

if view == "📌 ES&F Domain View":
    st.subheader("ES&F Domain View - Strategic Capabilities")
    question = "Return all domains and their capabilities grouped"
    response = ask_question(question)

    domain_caps = defaultdict(list)
    output = response.get("output", "")

    # Parse structured output manually
    matches = re.findall(r"\d+\.\s+(.*?):\s+The capabilities include (.*?)(?:\n\n|\Z)", output, re.DOTALL)

    for domain, caps_string in matches:
        caps = [c.strip().strip('.') for c in caps_string.split(',')]
        domain_caps[domain.strip()] = caps

    if domain_caps:
        st.markdown("### 🧭 Domain Dashboard Overview")
        columns = st.columns(3)
        display_domains = ["Identity & Access", "Fraud", "Cyber Security", "Third-Party Risk"]

        def normalize(text):
            return text.lower().replace("&", "and").replace(" ", "").strip()

        norm_lookup = {normalize(k): (k, v) for k, v in domain_caps.items()}

        for i, domain in enumerate(display_domains):
            if i % 3 == 0 and i != 0:
                columns = st.columns(3)
            col = columns[i % 3]
            with col:
                norm_key = normalize(domain)
                original_name, capabilities = norm_lookup.get(norm_key, (domain, []))
                st.markdown(f"### 📁 {domain}")
                st.metric("Total Capabilities", len(capabilities))
                if capabilities:
                    df = pd.DataFrame({"Capability": capabilities})
                    st.dataframe(df, use_container_width=True)

        all_data = []
        for domain, caps in domain_caps.items():
            for cap in caps:
                all_data.append({"Domain": domain, "Capability": cap})

        df_all = pd.DataFrame(all_data)
        st.download_button("📤 Export All Domains as CSV", df_all.to_csv(index=False), file_name="esf_domain_capabilities.csv")
    else:
        st.warning("No domain capabilities found.")
