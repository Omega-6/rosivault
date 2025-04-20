 # seed_data.py — Expanded Neo4j data seeding for ROSIVault with ≥50 rows per entity
from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import random

load_dotenv()

# Neo4j connection parameters
uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
username = os.getenv("NEO4J_USERNAME", "neo4j")
password = os.getenv("NEO4J_PASSWORD", "test1234")
driver = GraphDatabase.driver(uri, auth=(username, password))

# --- Utility ---
def delete_all_data(tx):
    tx.run("MATCH (n) DETACH DELETE n")

# --- Seed Domains & Capabilities (incl. 50+ misc) ---
def seed_domains_and_capabilities(tx):
    domain_map = {
        "Identity & Access": [
            "Identity Inventory", "User Access Management", "Password Mgmt.",
            "Segregation of Duties", "Authentication", "Authorization",
            "Privileged Access Management"
        ],
        "Cyber Security": [
            "Infrastructure & Virtualization Sec", "Application & Interface Sec",
            "Data Security & Information Lifecycle", "Governance, Risk & Compliance",
            "Threat & Vulnerability Management", "Logging & Monitoring",
            "Security Incident Mgmt.", "Cryptography, Encryption & Key Mgmt.",
            "Data Center Security", "Physical Security"
        ],
        "Fraud": ["Govern", "Identify", "Protect & Prevent", "Detect", "Respond", "Recover"],
        "Third-Party Risk": [
            "Vendor Risk Mgmt.", "TPRM Process Oversight", "Third-Party Inventory",
            "Risk Assessment", "Due Diligence", "Contractual Security Clauses",
            "Ongoing Monitoring", "Offboarding Procedures", "TP Reporting",
            "Vendor Tiering"
        ]
    }
    # add one domain with 50+ synthetic capabilities
    misc_caps = [f"Misc Capability {i}" for i in range(1, 51)]
    domain_map["Miscellaneous"] = misc_caps

    status_options = ["green", "yellow", "red"]
    maturity_levels = [
        "Initial", "Managed", "Defined",
        "Quantitatively Managed", "Optimizing"
    ]

    for domain, caps in domain_map.items():
        tx.run("MERGE (d:Domain {name:$domain})", domain=domain)
        for i, cap in enumerate(caps):
            cap_id = f"cap_{domain[0].lower()}_{i}"
            kpi_id = f"kpi_{cap_id}"
            rosi_id = f"rosi_{cap_id}"
            status   = random.choice(status_options)
            rosi_val = round(random.uniform(3.0, 10.0), 2)
            maturity = random.choice(maturity_levels)

            tx.run(
                """
                MERGE (c:Capability {id:$cid, name:$cname})
                SET c.maturity = $maturity
                MERGE (k:KPI {id:$kid, status_color:$status})
                MERGE (r:ROSI {id:$rid, value:$rosi})
                WITH c
                MATCH (d:Domain {name:$domain})
                MERGE (c)-[:HAS_KPI]->(k)
                MERGE (c)-[:HAS_ROSI]->(r)
                MERGE (c)-[:BELONGS_TO]->(d)
                """,
                cid=cap_id, cname=cap,
                maturity=maturity,
                kid=kpi_id, status=status,
                rid=rosi_id, rosi=rosi_val,
                domain=domain
            )

# --- Seed Tools, Vendors, FTE, Crew (50+ each) ---
def seed_tools_and_staff(tx):
    domains = ["Identity & Access", "Cyber Security", "Fraud", "Third-Party Risk", "Miscellaneous"]
    counts  = [7, 10, 6, 10, 50]
    all_cap_ids = [f"cap_{d[0].lower()}_{i}" for d, cnt in zip(domains, counts) for i in range(cnt)]

    for j in range(1, 51):
        tname = f"SynthTool_{j}"
        cost  = random.randint(10_000, 200_000)
        tx.run("MERGE (t:Tool {name:$tname}) SET t.cost=$cost", tname=tname, cost=cost)

        crew = f"Crew_{random.randint(1,50)}"
        fte  = f"FTE_{random.randint(1,50)}"
        tx.run("MERGE (:Crew {name:$crew})", crew=crew)
        tx.run("MERGE (:FTE  {name:$fte})",  fte=fte)
        tx.run(
            """
            MATCH (t:Tool {name:$tname}), (cr:Crew {name:$crew}), (f:FTE {name:$fte})
            MERGE (t)-[:IN]->(cr)
            MERGE (t)-[:STAFFED_BY]->(f)
            """,
            tname=tname, crew=crew, fte=fte
        )

        # link to 2 random capabilities
        for _ in range(2):
            cid = random.choice(all_cap_ids)
            tx.run(
                "MATCH (t:Tool {name:$tname}), (c:Capability {id:$cid}) MERGE (t)-[:SUPPORTS]->(c)",
                tname=tname, cid=cid
            )

# --- Seed ERM → TechDomain → ES&F mapping for Sankey ---
def seed_erm_and_tech(tx):
    erm_list = [
        "Financial","Operational","Regulatory","Reputational",
        "Extended Enterprise","Strategic","Technology","Investment"
    ]
    for name in erm_list:
        tx.run("MERGE (e:ERMCategory {name:$name})", name=name)

    tech_list = [
        "Technology Strategy & Execution","Software Delivery",
        "Service Delivery & Operations","Technology Resiliency",
        "Technology Asset Management","Third Party Management",
        "Data Management","AI Management","Cyber Security",
        "Identity & Access"
    ]
    for name in tech_list:
        tx.run("MERGE (t:TechDomain {name:$name})", name=name)

    impacts = {
        "Financial":    ["Technology Asset Management","Data Management"],
        "Operational":  ["Service Delivery & Operations","Technology Resiliency"],
        "Regulatory":   ["Cyber Security","Identity & Access"],
        "Reputational": ["Cyber Security","Identity & Access"],
        "Technology":   ["Software Delivery","AI Management"],
        "Strategic":    ["Technology Strategy & Execution"],
        "Investment":   ["Technology Asset Management"],
    }
    for erm, techs in impacts.items():
        for t in techs:
            tx.run(
                """
                MATCH (e:ERMCategory {name:$erm}), (t:TechDomain {name:$tech})
                MERGE (e)-[:IMPACTS]->(t)
                """,
                erm=erm, tech=t
            )

    maps = {
        "Cyber Security":    "Cyber Security",
        "Identity & Access": "Identity & Access",
    }
    for tech, esf in maps.items():
        tx.run(
            """
            MATCH (t:TechDomain {name:$tech}), (d:Domain {name:$esf})
            MERGE (t)-[:MAPS_TO]->(d)
            """,
            tech=tech, esf=esf
        )

# --- Seed Controls & Compliance Mapping ---
def seed_controls(tx):
    csa_map = {
        "Access Control":            ["User Authentication","Least Privilege"],
        "Audit & Accountability":    ["Log Management","Audit Trails"],
        "Configuration Management":  ["Baseline Config","Change Control"]
    }
    nist_map = {
        "PR.AC": ["Identity Management","Credentials"],
        "DE.CM": ["Anomaly Detection","Continuous Monitoring"],
        "CM-2":  ["Baseline Configuration","Config Change Control"]
    }

    for fam, ctrls in csa_map.items():
        for name in ctrls:
            tx.run("MERGE (ctrl:CSAControl {name:$name, family:$fam})", name=name, fam=fam)
    for fam, ctrls in nist_map.items():
        for name in ctrls:
            tx.run("MERGE (ctrl:NISTControl {name:$name, family:$fam})", name=name, fam=fam)

    result = tx.run("MATCH (c:Capability) RETURN c.id AS cid")
    cap_ids = [rec["cid"] for rec in result]
    all_controls = []
    for label in ("CSAControl","NISTControl"):
        res = tx.run(f"MATCH (ctrl:{label}) RETURN ctrl.name AS name")
        all_controls += [(label, rec["name"]) for rec in res]

    for cid in cap_ids:
        for label, name in random.sample(all_controls, k=random.randint(2,4)):
            tx.run(
                f"""
                MATCH (c:Capability {{id:$cid}})
                MATCH (ctrl:{label} {{name:$name}})
                MERGE (c)-[:HAS_CONTROL]->(ctrl)
                """,
                cid=cid, name=name
            )

# --- Seed Architecture Patterns ---
def seed_arch_patterns(tx):
    patterns = ["Zero Trust","Micro-segmentation","Secure SDLC","Immutable Infra"]
    tx.run("UNWIND $patterns AS name MERGE (:ArchitecturePattern {name:name})", patterns=patterns)

    result = tx.run("MATCH (c:Capability) RETURN c.id AS cid")
    cap_ids = [rec["cid"] for rec in result]
    for cid in cap_ids:
        for pat in random.sample(patterns, k=random.randint(1,2)):
            tx.run(
                """
                MATCH (c:Capability {id:$cid}), (p:ArchitecturePattern {name:$pat})
                MERGE (c)-[:INCLUDED_IN]->(p)
                """,
                cid=cid, pat=pat
            )

# --- Seed Cloud Providers ---
def seed_cloud_providers(tx):
    clouds = ["AWS","Azure","GCP","On-Prem"]
    tx.run("UNWIND $clouds AS name MERGE (:CloudProvider {name:name})", clouds=clouds)

    # assign each ArchitecturePattern and Tool to a random cloud
    for label, rel in [("ArchitecturePattern","RUNS_ON"),("Tool","DEPLOYED_ON")]:
        rows = tx.run(f"MATCH (n:{label}) RETURN n.name AS name")
        for rec in rows:
            cp = random.choice(clouds)
            tx.run(
                f"""
                MATCH (n:{label} {{name:$name}}), (c:CloudProvider {{name:$cp}})
                MERGE (n)-[:{rel}]->(c)
                """,
                name=rec["name"], cp=cp
            )

# --- Seed Vendors & License Costs ---
def seed_vendors_and_licenses(tx):
    vendors = ["Okta","Palo Alto","CyberArk","Splunk","Auth0"]
    tx.run("UNWIND $vendors AS name MERGE (:Vendor {name:name})", vendors=vendors)

    rows = tx.run("MATCH (t:Tool) RETURN t.name AS tname")
    for rec in rows:
        vendor = random.choice(vendors)
        lic    = random.randint(5_000,50_000)
        tx.run(
            """
            MATCH (v:Vendor {name:$vendor}), (t:Tool {name:$tname})
            MERGE (v)-[:SUPPLIES]->(t)
            SET t.licenseCost = $lic
            """,
            vendor=vendor, tname=rec["tname"], lic=lic
        )

# --- Run All Seeds ---
def run_all_seeds():
    with driver.session() as session:
        session.execute_write(delete_all_data)
        session.execute_write(seed_domains_and_capabilities)
        session.execute_write(seed_tools_and_staff)
        session.execute_write(seed_erm_and_tech)
        session.execute_write(seed_controls)
        session.execute_write(seed_arch_patterns)
        session.execute_write(seed_cloud_providers)
        session.execute_write(seed_vendors_and_licenses)
    driver.close()
    print("✅ Seeded all data: Domains, Capabilities, Tools, Staff, ERM mappings, Controls, Patterns, Clouds, Vendors & Licenses.")

if __name__ == "__main__":
    run_all_seeds()
