# query_engine.py – Neo4j data access for ROSIVault

from neo4j import GraphDatabase
import os

class Neo4jQueryEngine:
    def __init__(self):
        uri = os.getenv("NEO4J_URI", "bolt://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "test1234")
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def run_query(self, cypher, params=None):
        with self.driver.session() as session:
            result = session.run(cypher, params or {})
            return [record.data() for record in result]

    def get_high_value_red_capabilities(self):
        cypher = """
        MATCH (c:Capability)-[:HAS_KPI]->(k:KPI),
              (c)-[:HAS_ROSI]->(r:ROSI)
        WHERE k.status_color = 'Red' AND r.value > 70
        RETURN c.name AS capability, k.status_color AS status, r.value AS rosi
        ORDER BY r.value DESC
        """
        return self.run_query(cypher)

    def get_kpi_status_counts(self):
        cypher = """
        MATCH (:Capability)-[:HAS_KPI]->(k:KPI)
        RETURN k.status_color AS status, count(*) AS count
        """
        return self.run_query(cypher)

    def get_vendors_with_high_tool_risk(self):
        cypher = """
        MATCH (v:Vendor)<-[:USES]-(t:Tool)
        WHERE t.cost > 50000
        RETURN v.name AS vendor, COUNT(t) AS risky_tools
        ORDER BY risky_tools DESC
        LIMIT 5
        """
        return self.run_query(cypher)

    def get_capabilities_low_maturity_high_cost(self):
        cypher = """
        MATCH (c:Capability)-[:HAS_KPI]->(k:KPI),
              (c)<-[:SUPPORTS]-(t:Tool)
        WHERE k.status_color = 'Red' AND t.cost > 50000
        RETURN c.name AS capability, k.status_color AS kpi_status, t.cost AS tool_cost
        ORDER BY tool_cost DESC
        """
        return self.run_query(cypher)

    def get_investment_by_domain(self):
        cypher = """
        MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability)<-[:SUPPORTS]-(t:Tool)
        RETURN d.name AS domain, SUM(t.cost) AS total_investment
        ORDER BY total_investment DESC
        """
        return self.run_query(cypher)

    def get_capabilities_lacking_controls(self):
        cypher = """
        MATCH (c:Capability)
        WHERE NOT (c)-[:HAS_CONTROL]->(:CSAControl)
        RETURN c.name AS capability
        """
        return self.run_query(cypher)

    def get_investment_by_domain_sorted_by_rosi(self):
        cypher = """
        MATCH (d:Domain)<-[:BELONGS_TO]-(c:Capability)-[:HAS_ROSI]->(r:ROSI),
              (c)<-[:SUPPORTS]-(t:Tool)
        RETURN d.name AS domain, SUM(t.cost) AS total_investment, AVG(r.value) AS avg_rosi
        ORDER BY avg_rosi DESC
        """
        return self.run_query(cypher)
