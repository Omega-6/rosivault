from neo4j import GraphDatabase
import os
from dotenv import load_dotenv

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")

driver = GraphDatabase.driver(uri, auth=(username, password))

def print_capability_domain_links():
    query = """
    MATCH (c:Capability)-[:BELONGS_TO]->(d:Domain)
    RETURN c.name AS Capability, d.name AS Domain
    ORDER BY Domain, Capability
    """

    with driver.session() as session:
        result = session.run(query)
        rows = result.data()

        if not rows:
            print("🚫 No capabilities linked to domains.")
        else:
            print("✅ Capability to Domain Links:\n")
            for row in rows:
                print(f"📁 {row['Domain']} → 🔹 {row['Capability']}")

if __name__ == "__main__":
    print_capability_domain_links()
    driver.close()
