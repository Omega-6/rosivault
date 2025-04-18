# main.py – Entry point for the FastAPI backend

from fastapi import FastAPI
from app.routes import router

app = FastAPI(
    title="ROSIVault API",
    version="0.1.0",
    description="AI-powered security investment intelligence platform using FastAPI, Neo4j, and LangChain"
)

app.include_router(router)

@app.get("/")
def root():
    return {"message": "Welcome to ROSIVault"}
