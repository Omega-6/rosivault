# seed_more_data.py – Extended seeder for ROSIVault (Tools, Vendors, KPIs, ROSI, CSA Controls, Domains, Frameworks, Risks)

import csv
from app.graph.query_engine import Neo4jQueryEngine

engine = Neo4jQueryEngine()

# --- Seed Tools ---
def seed_tools(csv_path="data/seed/tools.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            CREATE (t:Tool {
                id: $id,
                name: $name,
                category: $category,
                vendor_id: $vendor_id,
                license_cost: toFloat($license_cost),
                cost: toFloat($cost),
                lifecycle: $lifecycle,
                integration_type: $integration_type,
                is_third_party: $is_third_party
            })
            """
            params = {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "vendor_id": row["vendor_id"],
                "license_cost": row["license_cost"],
                "cost": row["cost"],
                "lifecycle": row["lifecycle"],
                "integration_type": row["integration_type"],
                "is_third_party": row["is_third_party"].lower() == "true"
            }
            engine.run_query(cypher, params)

# --- Seed Vendors ---
def seed_vendors(csv_path="data/seed/vendors.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            CREATE (v:Vendor {
                id: $id,
                name: $name,
                third_party_level: $third_party_level,
                risk_score: toFloat($risk_score)
            })
            """
            params = {
                "id": row["id"],
                "name": row["name"],
                "third_party_level": row["third_party_level"],
                "risk_score": row["risk_score"]
            }
            engine.run_query(cypher, params)

# --- Seed KPI ---
def seed_kpis(csv_path="data/seed/kpis.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MATCH (c:Capability {id: $capability_id})
            CREATE (c)-[:HAS_KPI]->(:KPI {
                id: $id,
                name: $name,
                current_value: toFloat($current_value),
                target_value: toFloat($target_value),
                status_color: $status_color
            })
            """
            params = {
                "id": row["id"],
                "capability_id": row["capability_id"],
                "name": row["name"],
                "current_value": row["current_value"],
                "target_value": row["target_value"],
                "status_color": row["status_color"]
            }
            engine.run_query(cypher, params)

# --- Seed ROSI ---
def seed_rosi(csv_path="data/seed/rosi.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MATCH (c:Capability {id: $capability_id})
            CREATE (c)-[:HAS_ROSI]->(:ROSI {
                id: $id,
                value: toFloat($value),
                tier: $tier,
                recommended_action: $recommended_action
            })
            """
            params = {
                "id": row["id"],
                "capability_id": row["capability_id"],
                "value": row["value"],
                "tier": row["tier"],
                "recommended_action": row["recommended_action"]
            }
            engine.run_query(cypher, params)

# --- Seed CSA Controls ---
def seed_csa_controls(csv_path="data/seed/csa_controls.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MERGE (c:Control {id: $id})
            SET c.name = $name, c.domain = $domain, c.category = $category
            """
            params = {
                "id": row["id"],
                "name": row["name"],
                "domain": row["domain"],
                "category": row["category"]
            }
            engine.run_query(cypher, params)

# --- Seed Domains ---
def seed_domains(csv_path="data/seed/domains.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MERGE (d:Domain {id: $id})
            SET d.name = $name, d.description = $description
            """
            params = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"]
            }
            engine.run_query(cypher, params)

# --- Seed Frameworks ---
def seed_frameworks(csv_path="data/seed/frameworks.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MERGE (f:Framework {id: $id})
            SET f.name = $name, f.description = $description
            """
            params = {
                "id": row["id"],
                "name": row["name"],
                "description": row["description"]
            }
            engine.run_query(cypher, params)

# --- Seed Risks ---
def seed_risks(csv_path="data/seed/risk_types.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            CREATE (r:Risk {
                id: $id,
                name: $name,
                category: $category,
                impact_level: $impact_level
            })
            """
            params = {
                "id": row["id"],
                "name": row["name"],
                "category": row["category"],
                "impact_level": row["impact_level"]
            }
            engine.run_query(cypher, params)

# --- Link Capabilities to Risks ---
def seed_capability_risks(csv_path="data/seed/capability_risks.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MATCH (c:Capability {id: $capability_id})
            MATCH (r:Risk {id: $risk_id})
            MERGE (c)-[:HAS_RISK]->(r)
            """
            params = {
                "capability_id": row["capability_id"],
                "risk_id": row["risk_id"]
            }
            engine.run_query(cypher, params)

# --- Link Capabilities to Controls ---
def seed_capability_control_links(csv_path="data/seed/capability_control_links.csv"):
    with open(csv_path, newline='') as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            cypher = """
            MATCH (c:Capability {id: $capability_id})
            MATCH (ctrl:Control {id: $control_id})
            MERGE (c)-[:COVERED_BY]->(ctrl)
            """
            params = {
                "capability_id": row["capability_id"],
                "control_id": row["control_id"]
            }
            engine.run_query(cypher, params)

if __name__ == "__main__":
    print("Seeding vendors...")
    seed_vendors()
    print("Seeding tools...")
    seed_tools()
    print("Seeding KPIs...")
    seed_kpis()
    print("Seeding ROSI data...")
    seed_rosi()
    print("Seeding CSA Controls...")
    seed_csa_controls()
    print("Seeding Domains...")
    seed_domains()
    print("Seeding Frameworks...")
    seed_frameworks()
    print("Seeding Risks...")
    seed_risks()
    print("Linking Capabilities to Risks...")
    seed_capability_risks()
    print("Linking Capabilities to Controls...")
    seed_capability_control_links()
    print("✅ All data seeded!")
    try:
        engine.close()
    except:
        pass
