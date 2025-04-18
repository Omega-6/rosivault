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
You are an expert in cybersecurity investment strategy. Given a question and graph schema, generate a Cypher query to retrieve the relevant data.
Use property keys like 'name', 'status_color', 'value', 'risk_score', and relationship types such as HAS_KPI, HAS_ROSI, USED_BY, PROVIDED_BY, LACKS_CONTROL, BELONGS_TO.

Question: {question}
Schema: {schema}
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
    try:
        result = cypher_agent.invoke({"question": question})

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
                for row in rows:
                    status = row.get("status") or row.get("status_color", "").capitalize()
                    if status in kpi_summary:
                        kpi_summary[status] += 1
                    try:
                        rosi = float(row.get("rosi") or row.get("ROSI") or 0)
                        total_rosi += rosi
                        count_rosi += 1
                    except:
                        pass

                return {
                    "output": answer,
                    "capabilities": rows,
                    "Red": kpi_summary["Red"],
                    "Yellow": kpi_summary["Yellow"],
                    "Green": kpi_summary["Green"],
                    "TotalCapabilities": len(rows),
                    "AverageROSI": round(total_rosi / count_rosi, 2) if count_rosi > 0 else None
                }

            return {"output": answer}

        return {"output": "Unexpected format."}
    except Exception as e:
        return {"output": f"Error occurred: {e}"}
