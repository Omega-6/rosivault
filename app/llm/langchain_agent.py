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
You are a Cypher-only assistant. Based on the user's query and the provided schema, respond ONLY with a Cypher query. Do not include any explanations, commentary, or natural language — just the valid Cypher query.

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

    if isinstance(result, str):
        return {"output": result}

    if isinstance(result, dict):
        output = result.get("result", "No output.")
        steps = result.get("intermediate_steps", [])

        # Search for structured domain-capability list in intermediate steps
        for step in steps:
            if isinstance(step, list) and step and isinstance(step[0], dict):
                for item in step:
                    if "domain" in item and "capabilities" in item:
                        if isinstance(item["capabilities"], list):
                            return {
                                "output": output,
                                "capabilities": step,
                                "intermediate_steps": steps
                            }

        return {"output": output, "capabilities": []}

    return {"output": "Unexpected format."}
