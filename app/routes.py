# routes.py – FastAPI endpoints for ROSIVault

from fastapi import APIRouter
from app.graph.query_engine import Neo4jQueryEngine

router = APIRouter()
engine = Neo4jQueryEngine()

@router.get("/health")
def health_check():
    return {"status": "ok"}

@router.get("/capabilities")
def get_all_capabilities():
    return engine.get_all_capabilities()

@router.get("/capabilities/red-high-rosi")
def get_risky_but_valuable():
    return engine.get_red_high_rosi_capabilities()
