# rosivault_dashboard.py — Streamlit dashboard for ROSIVault

import streamlit as st
from app.llm.langchain_agent import ask_question
import pandas as pd
import matplotlib.pyplot as plt
import re

st.set_page_config(page_title="ROSIVault AI", layout="wide", page_icon="🔐")

st.sidebar.title("📂 ROSIVault Navigation")
view = st.sidebar.radio("Go to", ["💬 Ask AI", "📊 KPI Dashboard", "🔍 ROSI Insights", "🛠️ Tools & Vendors", "📌 ES&F Domain View"])

st.title("🔐 ROSIVault: AI Security Investment Assistant")

if view == "💬 Ask AI":
    if "chat" not in st.session_state:
        st.session_state.chat = []

    user_input = st.chat_input("Ask a question about security investment...")

    if user_input:
        st.session_state.chat.append({"role": "user", "content": user_input})
        response = ask_question(user_input)
        output = response.get("output", "No output.")
        st.session_state.chat.append({"role": "ai", "content": output})

        capabilities = response.get("capabilities", [])

        if not capabilities and isinstance(response.get("output"), str) and "capability" in response["output"].lower():
            st.info("Trying to parse capabilities from output text...")
            matches = re.findall(r"'(.+?)' has a KPI status of (\w+).*?value of ([\d\.]+)", response["output"])
            if matches:
                capabilities = []
                for m in matches:
                    try:
                        rosi_val = float(m[2].rstrip("."))
                        capabilities.append({"capability": m[0], "status": m[1], "rosi": rosi_val})
                    except ValueError:
                        continue

        if capabilities:
            def badge(kpi):
                return {"red": "🔴", "yellow": "🟡", "green": "🟢"}.get(kpi.lower(), kpi)

            df = pd.DataFrame(capabilities)
            df.columns = [col.lower().strip().replace(" ", "_") for col in df.columns]
            st.dataframe(df, use_container_width=True)
            st.download_button("Download CSV", df.to_csv(index=False), file_name="capability_insights.csv")

            kpi_counts = df["status"].value_counts().to_dict()
            if kpi_counts:
                col1, col2 = st.columns(2)
                with col1:
                    fig1, ax1 = plt.subplots()
                    ax1.pie(kpi_counts.values(), labels=kpi_counts.keys(), colors=["red", "gold", "green"][:len(kpi_counts)], autopct="%1.1f%%", startangle=90)
                    ax1.axis("equal")
                    st.pyplot(fig1)

                with col2:
                    fig2, ax2 = plt.subplots()
                    ax2.bar(kpi_counts.keys(), kpi_counts.values(), color=["red", "gold", "green"][:len(kpi_counts)])
                    ax2.set_ylabel("Count")
                    ax2.set_title("KPI Status Distribution")
                    st.pyplot(fig2)

    for msg in st.session_state.chat:
        st.chat_message(msg["role"]).write(msg["content"])

elif view == "📊 KPI Dashboard":
    st.subheader("Key KPI Distribution Overview")
    question = "List all capabilities and their KPI status and ROSI values"
    response = ask_question(question)

    capabilities = response.get("capabilities", [])
    if not capabilities and isinstance(response.get("output"), str) and "capability" in response["output"].lower():
        matches = re.findall(r"'(.+?)' has a KPI status of (\w+).*?value of ([\d\.]+)", response["output"])
        if matches:
            capabilities = []
            for m in matches:
                try:
                    rosi_val = float(m[2].rstrip("."))
                    capabilities.append({"capability": m[0], "status": m[1], "rosi": rosi_val})
                except ValueError:
                    continue

    if capabilities:
        df = pd.DataFrame(capabilities)
        df.columns = [col.lower().replace(" ", "_") for col in df.columns]
        df = df.rename(columns={"kpi_status": "status", "rosi_value": "rosi"})

        if "rosi" in df.columns:
            df["rosi"] = pd.to_numeric(df["rosi"], errors="coerce")
            top_rosi = df.nlargest(3, "rosi")
            df["highlight"] = df["capability"].isin(top_rosi["capability"]).map({True: "⭐", False: ""})
            df["Capability"] = df["highlight"] + " " + df["capability"]
        else:
            df["Capability"] = df["capability"]

        df["Details"] = df["capability"].apply(lambda x: f"[Learn more](https://yourdocsite.com/capability/{x.replace(' ', '_')})")

        filtered_df = st.data_editor(
            df[["Capability", "rosi", "status", "Details"]].rename(columns={"rosi": "ROSI", "status": "KPI"}),
            use_container_width=True,
            num_rows="dynamic"
        )

        if not filtered_df.empty and "KPI" in filtered_df.columns:
            filtered_df["KPI"] = filtered_df["KPI"].fillna("Unknown").astype(str)
            kpi_counts = filtered_df["KPI"].value_counts().to_dict()

            if kpi_counts:
                col1, col2 = st.columns(2)

                with col1:
                    st.markdown("### 📊 KPI Pie Chart")
                    fig, ax = plt.subplots()
                    ax.pie(kpi_counts.values(), labels=kpi_counts.keys(), autopct="%1.1f%%", startangle=90, colors=["red", "gold", "green"][:len(kpi_counts)])
                    ax.axis("equal")
                    st.pyplot(fig)

                with col2:
                    st.markdown("### 📊 KPI Bar Chart")
                    fig2, ax2 = plt.subplots()
                    ax2.bar(kpi_counts.keys(), kpi_counts.values(), color=["red", "gold", "green"][:len(kpi_counts)])
                    ax2.set_ylabel("Count")
                    ax2.set_title("KPI Distribution")
                    st.pyplot(fig2)

        st.download_button("📥 Export CSV", filtered_df.to_csv(index=False), file_name="kpi_dashboard.csv")

elif view == "🔍 ROSI Insights":
    st.subheader("Highest ROSI Capabilities")
    question = "Which capabilities have the highest ROSI?"
    response = ask_question(question)
    st.write(response.get("output", "No ROSI data available."))

elif view == "🛠️ Tools & Vendors":
    st.subheader("Vendor and Tool Usage")
    question = "List vendors and which tools they provide"
    response = ask_question(question)
    st.write(response.get("output", "No vendor/tool data found."))

elif view == "📌 ES&F Domain View":
    st.subheader("ES&F Domain View - Strategic Capabilities")
    question = "Return all domains and their capabilities grouped"
    response = ask_question(question)

    domain_caps = response.get("DomainCapabilities", {})
    output = response.get("output", "")

    if not domain_caps and output:
        matches = re.findall(r"([A-Za-z &]+):\s*(.*?)\s*(?=\n[A-Za-z &]+:|$)", output, re.DOTALL)
        domain_caps = {}
        for domain, caps in matches:
            capabilities = [c.strip() for c in re.split(r",|\n", caps) if c.strip()]
            domain_caps[domain.strip()] = capabilities

    if domain_caps:
        for domain, capabilities in domain_caps.items():
            with st.expander(f"📁 {domain}"):
                cols = st.columns(3)
                for idx, cap in enumerate(capabilities):
                    with cols[idx % 3]:
                        st.markdown(f"✅ **{cap}**")
    else:
        st.warning("No domain capabilities found.")
