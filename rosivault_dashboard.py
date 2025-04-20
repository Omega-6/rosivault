# rosivault_dashboard.py

import streamlit as st
from app.llm.langchain_agent import ask_question
from langchain_openai import ChatOpenAI
from langchain.schema import SystemMessage, HumanMessage
from neo4j.exceptions import Neo4jError
from app.graph.query_engine import Neo4jQueryEngine
import pandas as pd
import matplotlib.pyplot as plt
import math
import plotly.graph_objects as go
from collections import defaultdict

# Page config
st.set_page_config(page_title="ROSIVault AI", layout="wide", page_icon="🔐")

# === Sidebar navigation with grouped expanders ===
st.sidebar.title("📂 ROSIVault Navigation")
view = None

with st.sidebar.expander("🔍 Overview & Drill", expanded=True):
    ov_opts = ["Select view", "🏠 Home", "🔍 Deep Dive", "💬 Ask AI",
               "📌 ES&F Domain View", "📊 Domain Maturity Radar",
               "💡 Investment Opportunities", "🚨 Alert Dashboard"]
    ov = st.radio("", ov_opts, index=0, key="ov")
    if ov != "Select view":
        view = ov

with st.sidebar.expander("🗺️ Coverage & Mapping"):
    cov_opts = ["Select view", "⚖️ Risk Appetite Statements", "🚀 End-to-End Roadmap",
                "🌉 ERM Sankey Flow", "🗺️ Control Coverage Heatmap",
                "🏗️ Pattern Coverage", "☁️ Cloud Deployment", "🏷️ Vendor License Costs"]
    cov = st.radio("", cov_opts, index=0, key="cov")
    if cov != "Select view":
        view = cov

with st.sidebar.expander("🛠️ What‑If & Predictive"):
    pred_opts = ["Select view", "📈 KPI Trend Forecasting", "🔮 ROSI Projection Model",
                 "🚨 Incident Likelihood Scoring", "⚙️ Control Effectiveness Simulator",
                 "🛠️ Tool Impact Analyzer", "🏗️ Architecture Gap Predictor",
                 "💸 Investment Need Estimator", "🔗 Dependency Disruption Forecaster",
                 "👥 Skill & Staffing Planner", "🌐 Attack Surface Growth Estimator",
                 "💡 What‑If Budget Scenarios"]
    pr = st.radio("", pred_opts, index=0, key="pred")
    if pr != "Select view":
        view = pr

with st.sidebar.expander("🧠 Graphical & Explorer"):
    gr_opts = ["Select view", "🧠 Capability Graph View"]
    gr = st.radio("", gr_opts, index=0, key="gr")
    if gr != "Select view":
        view = gr

if view is None:
    view = "💬 Ask AI"

st.title("🔐 ROSIVault: AI Security Investment Assistant")

# persist drill selection
if "selected_domain" not in st.session_state:
    st.session_state.selected_domain = None

# chat state
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "new_question" not in st.session_state:
    st.session_state.new_question = ""
if "run_immediately" not in st.session_state:
    st.session_state.run_immediately = False

sugg_llm     = ChatOpenAI(model="gpt-4", temperature=0.7)
fallback_llm = ChatOpenAI(model="gpt-4", temperature=0.7)

def run_query(question: str) -> str:
    with st.spinner("Gimme a sec…"):
        convo = "".join(f"Q: {h['q']}\nA: {h['a']}\n" for h in st.session_state.chat_history)
        convo += f"Q: {question}\nA:"
        try:
            resp = ask_question(convo)
            return resp.get("output", "No response.")
        except Neo4jError:
            fb = fallback_llm([
                SystemMessage(content="You are an AI assistant that provides strategic recommendations."),
                HumanMessage(content=question)
            ])
            return fb.content

# --- 1) Home ---
if view == "🏠 Home":
    st.subheader("🏠 Home: Domain Summary")
    st.info("Click a card to drill into that domain’s capabilities.")

    engine = Neo4jQueryEngine()
    try:
        # a) investment by domain
        df_inv = pd.DataFrame(engine.get_investment_by_domain())
        # rename if get_investment_by_domain returns 'name'
        if "name" in df_inv.columns and "domain" not in df_inv.columns:
            df_inv = df_inv.rename(columns={"name": "domain"})
        if "domain" not in df_inv.columns:
            st.error("Investment query did not return a 'domain' column.")
            st.stop()

        # b) KPI summary by domain
        df_io = pd.DataFrame(engine.run_query("""
            MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability)-[:HAS_KPI]->(k:KPI)
            RETURN
              d.name AS domain,
              sum(CASE WHEN k.status_color='red' THEN 1 ELSE 0 END) AS red_kpis,
              avg(CASE k.status_color WHEN 'green' THEN 1 WHEN 'yellow' THEN 0.5 ELSE 0 END) AS health_score
        """))
        # rename if needed
        if "name" in df_io.columns and "domain" not in df_io.columns:
            df_io = df_io.rename(columns={"name": "domain"})
        # if still no domain column, fill zeros for all domains in df_inv
        if "domain" not in df_io.columns:
            df_io = pd.DataFrame({
                "domain": df_inv["domain"],
                "red_kpis": 0,
                "health_score": 0.0
            })
    finally:
        engine.close()

    # c) merge and display cards
    df = df_inv.merge(df_io, on="domain", how="outer").fillna(0)
    cards = df.to_dict("records")
    cols = st.columns(len(cards))
    for col, r in zip(cols, cards):
        with col:
            if st.button(r["domain"]):
                st.session_state.selected_domain = r["domain"]
            st.metric("Investment", f"${int(r['total_investment']):,}")
            st.metric("Health", f"{r['health_score']:.2f}")
            st.metric("Red KPIs", int(r["red_kpis"]))

# --- 2) Deep Dive ---
elif view == "🔍 Deep Dive":
    dom = st.session_state.selected_domain
    if not dom:
        st.warning("Please click a domain card on the Home view first.")
        st.stop()

    st.subheader(f"🔍 Deep Dive: {dom}")
    st.info("List of capabilities under this domain.")

    engine = Neo4jQueryEngine()
    try:
        rows = engine.run_query("""
            MATCH (d:Domain {name:$dom})<-[:BELONGS_TO]-(c:Capability)
            OPTIONAL MATCH (c)-[:HAS_KPI]->(k:KPI)
            RETURN c.name AS capability, k.status_color AS status
            ORDER BY c.name
        """, {"dom": dom})
    finally:
        engine.close()

    if not rows:
        st.warning("No capabilities found for this domain.")
    else:
        emojis = {"green":"🟢","yellow":"🟡","red":"🔴",None:"⚪"}
        table = [
            {"Badge": emojis.get(r["status"]),
             "Capability": r["capability"],
             "Status": (r["status"] or "Unknown").capitalize()}
            for r in rows
        ]
        st.dataframe(pd.DataFrame(table), use_container_width=True)

# --- 3) Ask AI ---
elif view == "💬 Ask AI":
    st.subheader("💬 Ask ROSIVault AI")
    for pair in st.session_state.chat_history:
        st.markdown(f"**You:** {pair['q']}")
        st.markdown(f"**AI:** {pair['a']}")
    q = st.text_input("Ask me about your security investments…",
                      value=st.session_state.new_question, key="new_question")
    if st.button("Run Query"):
        st.session_state.run_immediately = True
    if st.session_state.run_immediately and q:
        st.session_state.run_immediately = False
        ans = run_query(q)
        st.session_state.chat_history.append({"q": q, "a": ans})
        st.markdown("**AI:**")
        st.write(ans)
        prompt = f"User asked: {q}\nAI answered: {ans}\nSuggest 3 concise follow‑up questions."
        resp = sugg_llm([
            SystemMessage(content="You are a helpful assistant that suggests follow‑up questions."),
            HumanMessage(content=prompt)
        ])
        sug = [line.strip("- ").strip() for line in resp.content.splitlines() if line.strip()]
        if sug:
            st.markdown("**Suggested follow‑up questions:**")
            for i, fq in enumerate(sug):
                c1, c2 = st.columns([4,1])
                with c1:
                    st.write(f"{i+1}. {fq}")
                with c2:
                    if st.button("Ask", key=f"fu_{i}"):
                        st.session_state.new_question = fq
                        st.session_state.run_immediately = True

# --- 4) ES&F Domain View ---
elif view == "📌 ES&F Domain View":
    st.subheader("📌 ES&F Domain View - Strategic Capabilities")
    engine = Neo4jQueryEngine()
    try:
        stats = engine.run_query("""
            CALL { MATCH (d:Domain) RETURN count(d) AS domains }
            CALL { MATCH (c:Capability) RETURN count(c) AS capabilities }
            RETURN domains, capabilities
        """)
        rows = engine.run_query("""
            MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability)
            OPTIONAL MATCH (c)-[:HAS_KPI]->(k:KPI)
            RETURN d.name AS domain, c.name AS capability, k.status_color AS status
            ORDER BY domain, capability
        """)
    finally:
        engine.close()

    if stats:
        st.markdown(f"**Graph contains:** {stats[0]['domains']} domains and {stats[0]['capabilities']} capabilities.")
    if not rows:
        st.warning("⚠️ No capabilities found.")
        st.stop()

    domain_caps = defaultdict(list)
    emojis = {"green":"🟢","yellow":"🟡","red":"🔴",None:"⚪"}
    for r in rows:
        domain_caps[r["domain"]].append({
            "Badge": emojis.get(r["status"]),
            "Capability": r["capability"],
            "Status": (r["status"] or "Unknown").capitalize()
        })
    for d, caps in domain_caps.items():
        st.markdown(f"### 📁 {d}")
        st.metric("Total Capabilities", len(caps))
        st.dataframe(pd.DataFrame(caps)[["Badge","Capability","Status"]], hide_index=True)
    all_rows = [{"Domain":d, **row} for d,caps in domain_caps.items() for row in caps]
    st.download_button("📤 Export All Domains as CSV",
                       pd.DataFrame(all_rows).to_csv(index=False),
                       file_name="esf_domain_capabilities.csv")

# --- 5) Domain Maturity Radar ---
elif view == "📊 Domain Maturity Radar":
    st.subheader("📊 Domain Maturity Radar")
    st.info("Radar chart of domain maturity, risk, and investment.")
    engine = Neo4jQueryEngine()
    try:
        df_mat = pd.DataFrame(engine.run_query(
            "MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability) WHERE c.maturity IS NOT NULL "
            "RETURN d.name AS domain, avg(CASE c.maturity "
            "WHEN 'Initial' THEN 1 WHEN 'Managed' THEN 2 WHEN 'Defined' THEN 3 "
            "WHEN 'Quantitatively Managed' THEN 4 WHEN 'Optimizing' THEN 5 END) AS avg_maturity"
        ))
        df_risk = pd.DataFrame(engine.run_query(
            "MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability)-[:HAS_KPI]->(k:KPI) "
            "RETURN d.name AS domain, toFloat(sum(CASE WHEN k.status_color='red' THEN 1 ELSE 0 END))/count(k)*100 AS pct_red"
        ))
        df_inv = pd.DataFrame(engine.get_investment_by_domain())
        if "name" in df_inv.columns:
            df_inv = df_inv.rename(columns={"name":"domain"})
    finally:
        engine.close()

    if {'domain'} <= set(df_mat.columns) and {'domain'} <= set(df_risk.columns) and 'domain' in df_inv.columns:
        df = df_mat.merge(df_risk, on='domain').merge(df_inv, on='domain')
        df['maturity_norm'] = (df['avg_maturity'] -1)/4
        df['risk_norm']     = df['pct_red']/100
        max_inv = df['total_investment'].max() or 1
        df['inv_norm']      = df['total_investment']/max_inv

        labels = ['Maturity','Risk','Investment']
        angles = [n/len(labels)*2*math.pi for n in range(len(labels))] + [0]
        fig, ax = plt.subplots(subplot_kw=dict(polar=True), figsize=(6,6))
        for _, r in df.iterrows():
            vals = [r['maturity_norm'],r['risk_norm'],r['inv_norm'],r['maturity_norm']]
            ax.plot(angles, vals, label=r['domain'])
            ax.fill(angles, vals, alpha=0.1)
        ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels)
        ax.set_yticks([0.25,0.5,0.75,1.0]); ax.set_yticklabels(['25%','50%','75%','100%'])
        ax.legend(bbox_to_anchor=(1.3,1.1)); ax.set_title('Domain Maturity vs Risk vs Investment')
        st.pyplot(fig)
    else:
        st.write("Insufficient data to render radar.")

# --- 6) Investment Opportunities ---
elif view == "💡 Investment Opportunities":
    st.subheader("💡 Investment Opportunities")
    st.info("Where to allocate next to close top risks and gaps.")
    engine = Neo4jQueryEngine()
    try:
        df = pd.DataFrame(engine.run_query(
            "MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability)-[:HAS_KPI]->(k:KPI) "
            "RETURN d.name AS domain, count(CASE WHEN k.status_color='red' THEN 1 END) AS red_kpis, "
            "avg(CASE k.status_color WHEN 'green' THEN 1 WHEN 'yellow' THEN 0.5 ELSE 0 END) AS health_score "
            "ORDER BY red_kpis DESC"
        ))
    finally:
        engine.close()
    if not df.empty:
        st.table(df.style.format({"health_score":"{:.2f}"}))
        st.bar_chart(df.set_index('domain')['red_kpis'])

# --- 7) Alert Dashboard ---
elif view == "🚨 Alert Dashboard":
    st.subheader("🚨 Alert Dashboard")
    st.info("Red‑flagged KPIs & capabilities missing controls.")
    engine = Neo4jQueryEngine()
    try:
        red = pd.DataFrame(engine.run_query(
            "MATCH (c:Capability)-[:HAS_KPI]->(k:KPI) WHERE k.status_color='red' "
            "RETURN c.name AS Capability, k.id AS KPI_ID"
        ))
        miss = pd.DataFrame(engine.run_query(
            "MATCH (c:Capability) OPTIONAL MATCH (c)-[:HAS_CONTROL]->(ctrl) "
            "WITH c.name AS capability, collect(ctrl.name) AS ctrls WHERE size(ctrls)=0 "
            "RETURN capability, ctrls AS missing_controls"
        ))
    finally:
        engine.close()
    if not red.empty:
        st.markdown("### 🔴 Red‑flagged KPIs"); st.dataframe(red)
    if not miss.empty:
        st.markdown("### ⚠️ Missing Controls"); st.dataframe(miss)

# --- 8) Risk Appetite Statements ---
elif view == "⚖️ Risk Appetite Statements":
    st.subheader("⚖️ Risk Appetite Statements")
    st.info("Domain risk appetite definitions.")
    stm = {
        'Identity & Access': '≤1.5% deviation in identity anomalies',
        'Cyber Security':     '≤2 major unpatched vulns',
        'Fraud':              '≤0.1% fraud loss of volume'
    }
    st.table(pd.DataFrame([{'Domain': d, 'Statement': s} for d, s in stm.items()]))

# --- 9) End‑to‑End Roadmap ---
elif view == "🚀 End-to-End Roadmap":
    st.subheader("🚀 End-to-End Roadmap")
    st.info("5‑step ES&F program progress.")
    steps = [
        'Map to CCM Framework',
        'Establish Risk Appetite',
        'Define KRIs/PLA',
        'Measure ROSI & Diminishing Returns',
        'Identify New Investments'
    ]
    for i, step in enumerate(steps, 1):
        st.write(f"{i}. {step}")
        st.progress(int(i/len(steps)*100))

# --- 10) ERM Sankey ---
elif view == "🌉 ERM Sankey Flow":
    st.subheader("🌉 ERM → Technology Universe → ES&F Sankey Flow")
    st.info("Trace ERMCategory → TechDomain → ES&F Domain.")
    engine = Neo4jQueryEngine()
    try:
        rows = engine.run_query("""
            MATCH (e:ERMCategory)-[:IMPACTS]->(t:TechDomain)-[:MAPS_TO]->(d:Domain)
            RETURN e.name AS source, t.name AS mid, d.name AS target, count(*) AS weight
        """)
    finally:
        engine.close()
    df_sankey = pd.DataFrame(rows)
    if df_sankey.empty:
        st.write("No Sankey data available.")
    else:
        labels = list(pd.concat([df_sankey.source, df_sankey.mid, df_sankey.target]).unique())
        src = df_sankey.source.map(labels.index).tolist()
        mid = df_sankey.mid.map(labels.index).tolist()
        tgt = df_sankey.target.map(labels.index).tolist()
        w   = df_sankey.weight.tolist()
        link= dict(source=src+mid, target=mid+tgt, value=w+w)
        fig = go.Figure(go.Sankey(node=dict(label=labels,pad=15,thickness=20), link=link))
        fig.update_layout(margin=dict(l=0,r=0,t=30,b=0))
        st.plotly_chart(fig, use_container_width=True)

# --- 11) Control Coverage Heatmap ---
elif view == "🗺️ Control Coverage Heatmap":
    st.subheader("🗺️ Control Coverage Heatmap")
    st.info("Matrix of ES&F capabilities vs. control families (✓ count).")
    engine = Neo4jQueryEngine()
    try:
        rows = engine.run_query("""
            MATCH (c:Capability)-[:HAS_CONTROL]->(ctrl)
            RETURN c.name AS capability, ctrl.family AS control_family
        """)
    finally:
        engine.close()
    df_heat = pd.DataFrame(rows)
    if df_heat.empty:
        st.write("No control‑coverage data available.")
    else:
        pivot = df_heat.pivot_table(index='capability', columns='control_family',
                                    aggfunc='size', fill_value=0)
        st.dataframe(pivot.style.bar(axis=1), use_container_width=True)

# --- 12) Pattern Coverage ---
elif view == "🏗️ Pattern Coverage":
    st.subheader("🏗️ Architecture Pattern Coverage")
    st.info("How many capabilities each pattern includes.")
    engine = Neo4jQueryEngine()
    try:
        rows = engine.run_query("""
            MATCH (p:ArchitecturePattern)<-[:INCLUDED_IN]-(c:Capability)
            RETURN p.name AS pattern, count(c) AS cap_count ORDER BY cap_count DESC
        """)
    finally:
        engine.close()
    df = pd.DataFrame(rows)
    if df.empty:
        st.write("No pattern data available.")
    else:
        st.bar_chart(df.set_index("pattern")["cap_count"])

# --- 13) Cloud Deployment ---
elif view == "☁️ Cloud Deployment":
    st.subheader("☁️ Cloud Provider Deployment")
    st.info("Patterns & tools by cloud provider.")
    engine = Neo4jQueryEngine()
    try:
        pat   = engine.run_query("MATCH (p:ArchitecturePattern)-[:RUNS_ON]->(c:CloudProvider) RETURN c.name AS cloud, count(p) AS patterns")
        tools = engine.run_query("MATCH (t:Tool)-[:DEPLOYED_ON]->(c:CloudProvider) RETURN c.name AS cloud, count(t) AS tools")
    finally:
        engine.close()
    df_pat   = pd.DataFrame(pat).set_index("cloud")
    df_tools = pd.DataFrame(tools).set_index("cloud")
    df_all   = df_pat.join(df_tools, how="outer").fillna(0)
    if df_all.empty:
        st.write("No cloud deployment data available.")
    else:
        st.table(df_all)
        st.area_chart(df_all)

# --- 14) Vendor License Costs ---
elif view == "🏷️ Vendor License Costs":
    st.subheader("🏷️ Vendor License Cost Breakdown")
    st.info("Total license spend by vendor and tool.")
    engine = Neo4jQueryEngine()
    try:
        rows = engine.run_query("""
            MATCH (v:Vendor)-[:SUPPLIES]->(t:Tool)
            WHERE exists(t.licenseCost)
            RETURN v.name AS vendor, sum(t.licenseCost) AS total_license_cost
            ORDER BY total_license_cost DESC
        """)
    finally:
        engine.close()
    df = pd.DataFrame(rows)
    if df.empty:
        st.write("No vendor license data available.")
    else:
        st.bar_chart(df.set_index("vendor")["total_license_cost"])

# --- 15) Capability Graph View ---
elif view == "🧠 Capability Graph View":
    st.subheader("🧠 Capability Graph View")
    st.info("Interactive graph of capability relationships.")
    engine = Neo4jQueryEngine()
    try:
        opts = engine.run_query("MATCH (c:Capability) RETURN c.name AS name ORDER BY name")
        cap_list = [r['name'] for r in opts]
    finally:
        engine.close()
    sel = st.selectbox("Select a capability", cap_list)
    if sel:
        engine = Neo4jQueryEngine()
        try:
            rels = engine.run_query(
                "MATCH (c:Capability {name:$n})-[r]-(x) RETURN type(r) AS rel, x.name AS neighbor",
                {"n": sel}
            )
        finally:
            engine.close()
        dot = f'graph G {{\n"{sel}" [shape=box,color=lightblue];\n'
        for r in rels:
            dot += f'"{sel}" -- "{r["neighbor"]}" [label="{r["rel"]}"];\n'
        dot += "}"
        st.graphviz_chart(dot)

# --- 16) Control Effectiveness Simulator (stub) & Tool Impact Analyzer stub, predictive stubs ---
elif view in pred_opts[1:]:
    st.subheader(view)
    st.info("This predictive view is on our roadmap—coming soon! 🚀")

else:
    st.write("Select a view from the sidebar above.")
