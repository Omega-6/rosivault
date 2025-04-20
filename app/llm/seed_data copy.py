# seed_data.py — Modular Neo4j data seeding for ROSIVault (Unified Dataset)

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os
import random

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
driver = GraphDatabase.driver(uri, auth=(username, password))

def delete_all_data(tx):
    tx.run("MATCH (n) DETACH DELETE n")

def seed_domains_and_capabilities(tx):
    domain_map = {
        "Identity & Access": [
            "Identity Inventory", "User Access Management", "Password Mgmt.", "Segregation of Duties",
            "Authentication", "Authorization", "Privileged Access Management"
        ],
        "Cyber Security": [
            "Infrastructure & Virtualization Sec", "Application & Interface Sec", "Data Security & Information Lifecycle",
            "Governance, Risk & Compliance", "Threat & Vulnerability Management", "Logging & Monitoring",
            "Security Incident Mgmt.", "Cryptography, Encryption & Key Mgmt.", "Data Center Security", "Physical Security"
        ],
        "Fraud": [
            "Govern", "Identify", "Protect & Prevent", "Detect", "Respond", "Recover"
        ]
    }

    status_options = ["green", "yellow", "red"]

    for domain, capabilities in domain_map.items():
        tx.run("MERGE (d:Domain {name: $name})", name=domain)
        for i, cap in enumerate(capabilities):
            cap_id = f"cap_{domain[0]}_{i}"
            kpi_id = f"kpi_{cap_id}"
            rosi_id = f"rosi_{cap_id}"
            status = random.choice(status_options)
            rosi_val = round(random.uniform(3.0, 10.0), 2)

            tx.run("""
                MERGE (c:Capability {id: $cid, name: $cname})
                MERGE (k:KPI {id: $kid, status_color: $status})
                MERGE (r:ROSI {id: $rid, value: $rosi})
                MERGE (d:Domain {name: $domain})
                MERGE (c)-[:HAS_KPI]->(k)
                MERGE (c)-[:HAS_ROSI]->(r)
                MERGE (c)-[:BELONGS_TO]->(d)
            """, cid=cap_id, cname=cap, kid=kpi_id, status=status, rid=rosi_id, rosi=rosi_val, domain=domain)

def seed_graph_relationships(tx):
    for i in range(1, 21):
        tx.run("""
            MERGE (f:Function {name: $function})
            MERGE (dc:DomainContext {name: $domain_context})
            MERGE (ml:MaturityLevel {level: $maturity})
            MERGE (v:Vendor {name: $vendor})
            MERGE (vt:VendorTool {name: $vendor_tool})
            MERGE (cc:CustomTool {name: $custom_tool})
            MERGE (ft:FTE {id: $fte_id, count: $fte_count})
            MERGE (cp:CloudProvider {name: $cloud_provider})
            MERGE (crew:Crew {name: $crew})
            MERGE (arch:ArchitecturePattern {name: $arch_pattern})
            MERGE (mitre:MITREAttack {id: $mitre_id})
            MERGE (nist:NISTControl {id: $nist_id})
            MERGE (nistFam:NISTFamily {name: $nist_family})

            MERGE (c:Capability {name: $cap})
            MERGE (c)-[:SupportedBy]->(ml)
            MERGE (c)-[:Has]->(v)
            MERGE (vt)-[:SoldBy]->(v)
            MERGE (vt)-[:Costs]->(:LicenseCost {amount: $cost})
            MERGE (vt)-[:In]->(:Lifecycle {phase: 'Production'})
            MERGE (vt)-[:StaffedBy]->(crew)
            MERGE (cc)-[:Costs]->(:LicenseCost {amount: $custom_cost})
            MERGE (ft)-[:Costs]->(:LicenseCost {amount: $fte_cost})
            MERGE (c)-[:RunsOn]->(cp)
            MERGE (c)-[:IncludedIn]->(arch)
            MERGE (c)-[:DefendsAgainst]->(mitre)
            MERGE (dc)-[:Contains]->(f)
            MERGE (dc)-[:CompliesWith]->(nist)
            MERGE (nist)-[:BelongsTo]->(nistFam)
        """, function=f"Function {i}", domain_context=f"Context {i}", maturity="Medium",
             vendor=f"Vendor {i}", vendor_tool=f"Tool {i}", custom_tool=f"CustomTool {i}",
             fte_id=f"fte{i}", fte_count=random.randint(1, 5), cloud_provider="AWS",
             crew=f"Team {i}", arch_pattern="Zero Trust", mitre_id=f"T{i:04d}",
             nist_id=f"AC-{i}", nist_family="Access Control", cap=f"Capability {i}",
             cost=random.randint(1000, 5000), custom_cost=random.randint(2000, 6000),
             fte_cost=random.randint(3000, 10000))

def run_all_seeds():
    with driver.session() as session:
        session.execute_write(delete_all_data)
        session.execute_write(seed_domains_and_capabilities)
        session.execute_write(seed_graph_relationships)
        print("✅ Seeded cleaned domains, capabilities, and graph relationships.")

if __name__ == "__main__":
    run_all_seeds()
    driver.close()