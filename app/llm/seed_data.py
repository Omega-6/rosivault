# seed_data.py — Seeds ROSIVault graph data into Neo4j

from neo4j import GraphDatabase
from dotenv import load_dotenv
import os

load_dotenv()

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

def seed(tx):
    # Clear existing data
    tx.run("MATCH (n) DETACH DELETE n")

    # Domains
    tx.run("""
    CREATE (:Domain {id: 'd1', name: 'Security Operations'}),
           (:Domain {id: 'd2', name: 'Risk Management'}),
           (:Domain {id: 'd3', name: 'Identity & Access'})
    """)

    # Capabilities, KPIs, ROSI
    tx.run("""
    CREATE (c1:Capability {id: 'c1', name: 'Threat Detection'}),
           (k1:KPI {id: 'k1', status_color: 'green'}),
           (r1:ROSI {id: 'r1', value: 8.7}),
           (c2:Capability {id: 'c2', name: 'Vendor Risk'}),
           (k2:KPI {id: 'k2', status_color: 'red'}),
           (r2:ROSI {id: 'r2', value: 4.2}),
           (c3:Capability {id: 'c3', name: 'Access Control'}),
           (k3:KPI {id: 'k3', status_color: 'yellow'}),
           (r3:ROSI {id: 'r3', value: 6.1})
    """)

    tx.run("""
    MATCH (c1:Capability {id: 'c1'}), (k1:KPI {id: 'k1'}), (r1:ROSI {id: 'r1'}), (d1:Domain {id: 'd1'})
    CREATE (c1)-[:HAS_KPI]->(k1),
           (c1)-[:HAS_ROSI]->(r1),
           (c1)-[:BELONGS_TO]->(d1)
    WITH *
    MATCH (c2:Capability {id: 'c2'}), (k2:KPI {id: 'k2'}), (r2:ROSI {id: 'r2'}), (d2:Domain {id: 'd2'})
    CREATE (c2)-[:HAS_KPI]->(k2),
           (c2)-[:HAS_ROSI]->(r2),
           (c2)-[:BELONGS_TO]->(d2)
    WITH *
    MATCH (c3:Capability {id: 'c3'}), (k3:KPI {id: 'k3'}), (r3:ROSI {id: 'r3'}), (d3:Domain {id: 'd3'})
    CREATE (c3)-[:HAS_KPI]->(k3),
           (c3)-[:HAS_ROSI]->(r3),
           (c3)-[:BELONGS_TO]->(d3)
    """)

    # Tools and Vendors
    tx.run("""
    CREATE (:Tool {id: 't1', name: 'Splunk', cost: 50000}),
           (:Tool {id: 't2', name: 'Nessus', cost: 20000}),
           (:Tool {id: 't3', name: 'Okta', cost: 30000}),
           (:Vendor {id: 'v1', name: 'CyberX', risk_score: 8.9}),
           (:Vendor {id: 'v2', name: 'ShieldCorp', risk_score: 5.2})
    """)

    tx.run("""
    MATCH (t1:Tool {id: 't1'}), (v1:Vendor {id: 'v1'})
    CREATE (t1)-[:PROVIDED_BY]->(v1)
    WITH *
    MATCH (t2:Tool {id: 't2'}), (v2:Vendor {id: 'v2'})
    CREATE (t2)-[:PROVIDED_BY]->(v2)
    WITH *
    MATCH (t3:Tool {id: 't3'}), (v2:Vendor {id: 'v2'})
    CREATE (t3)-[:PROVIDED_BY]->(v2)
    WITH *
    MATCH (t1:Tool {id: 't1'}), (t2:Tool {id: 't2'}), (t3:Tool {id: 't3'}),
          (c1:Capability {id: 'c1'}), (c2:Capability {id: 'c2'}), (c3:Capability {id: 'c3'})
    CREATE (t1)-[:USED_BY]->(c1),
           (t2)-[:USED_BY]->(c2),
           (t3)-[:USED_BY]->(c3)
    """)

    # Controls
    tx.run("""
    CREATE (:Control {id: 'ctrl1', name: 'Firewall'}),
           (:Control {id: 'ctrl2', name: 'MFA'}),
           (:Control {id: 'ctrl3', name: 'Vendor Assessment'})
    """)

    tx.run("""
    MATCH (c2:Capability {id: 'c2'}), (ctrl3:Control {id: 'ctrl3'})
    CREATE (c2)-[:LACKS_CONTROL]->(ctrl3)
    WITH *
    MATCH (c3:Capability {id: 'c3'}), (ctrl2:Control {id: 'ctrl2'})
    CREATE (c3)-[:LACKS_CONTROL]->(ctrl2)
    """)

with driver.session() as session:
    session.execute_write(seed)

print("🌱 Data successfully seeded into Neo4j!")