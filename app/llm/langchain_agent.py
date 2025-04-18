# langchain_agent.py — LangChain interface for ROSIVault

from langchain_community.graphs import Neo4jGraph
from langchain_community.chains.graph_qa.cypher import GraphCypherQAChain
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from dotenv import load_dotenv
import os

load_dotenv()

# Set up Neo4j connection
graph = Neo4jGraph()

# Use GPT-4 model
llm = ChatOpenAI(model="gpt-4", temperature=0)

# Custom prompt template for generating Cypher queries
cypher_prompt = PromptTemplate.from_template("""
You are an expert in cybersecurity investment strategy. Based on the user's query and the provided schema, generate a Cypher query **only**, without any explanation or preamble.

Schema:
{schema}

Query:
{query}
""")

# Create the Cypher QA chain with required flags
cypher_agent = GraphCypherQAChain.from_llm(
    graph=graph,
    llm=llm,
    cypher_prompt=cypher_prompt,
    return_intermediate_steps=True,
    verbose=True,
    top_k=10,
    allow_dangerous_requests=True
)

def ask_question(question: str):
    result = cypher_agent.invoke({"query": question})

    # Handle different response types
    if isinstance(result, str):
        return {"output": result}

    if isinstance(result, dict):
        answer = result.get("result", "No output.")
        intermediate = result.get("intermediate_steps", [])

        # Parse rows if available in context
        rows = intermediate[-1] if intermediate else []
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            # Compute metrics for dashboard
            kpi_summary = {"Red": 0, "Yellow": 0, "Green": 0}
            total_rosi = 0
            count_rosi = 0
            domain_caps = {}

            for row in rows:
                status = row.get("status") or row.get("status_color", "").capitalize()
                if status in kpi_summary:
                    kpi_summary[status] += 1
                try:
                    rosi = float(str(row.get("rosi") or row.get("ROSI") or 0).rstrip("."))
                    total_rosi += rosi
                    count_rosi += 1
                except:
                    pass

                domain = row.get("domain", "Unknown")
                cap = row.get("capability") or row.get("Capability")
                if domain not in domain_caps:
                    domain_caps[domain] = []
                domain_caps[domain].append(cap)

            return {
                "output": answer,
                "capabilities": rows,
                "Red": kpi_summary["Red"],
                "Yellow": kpi_summary["Yellow"],
                "Green": kpi_summary["Green"],
                "TotalCapabilities": len(rows),
                "AverageROSI": round(total_rosi / count_rosi, 2) if count_rosi > 0 else None,
                "DomainCapabilities": domain_caps
            }

        return {"output": answer}

    return {"output": "Unexpected format."}
