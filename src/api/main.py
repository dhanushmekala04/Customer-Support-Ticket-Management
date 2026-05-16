"""
FastAPI REST API for the Customer Support Ticket Management System.
Every processed ticket is stored in MongoDB for full traceability.
"""

import logging
import uuid
from datetime import datetime
from typing import Optional, List

from pymongo import MongoClient
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, ConfigDict

from src.workflow import app as workflow_app
from src.config import config
from src.utils.logger import setup_logging
from src.utils.metrics import TicketMetrics

setup_logging()
logger = logging.getLogger(__name__)

api_app = FastAPI(
    title="Customer Support Ticket Management System",
    description="Multi-Agent AI System for automating customer support ticket processing",
    version="1.0.0"
)

api_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

metrics = TicketMetrics()

# =====================================================
# MONGODB
# =====================================================

import certifi
from pymongo import MongoClient

try:
    _mongo_client = MongoClient(
        config.MONGO_URI,
        tls=True,
        tlsCAFile=certifi.where(),
        serverSelectionTimeoutMS=30000
    )

    _mongo_client.admin.command("ping")

    logger.info("MongoDB connected successfully")

except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")
    _mongo_client = None

def get_tickets_collection():
    """Return the tickets collection."""
    return _mongo_client[config.MONGO_DB_NAME][config.TICKETS_COLLECTION]


def save_ticket(result: dict, processing_time: float) -> None:
    """Persist the full ticket state to MongoDB."""
    try:
        collection = get_tickets_collection()
        doc = {
            "ticket_id":            result["ticket_id"],
            "customer_query":       result["customer_query"],
            "customer_email":       result.get("customer_email"),
            "category":             result["category"],
            "priority":             result["priority"],
            "faq_match":            result.get("faq_match", ""),
            "resolution":           result.get("resolution", ""),
            "needs_escalation":     result["needs_escalation"],
            "final_response":       result["final_response"],
            "conversation_history": result.get("conversation_history", []),
            "metadata":             result.get("metadata", {}),
            "processing_time_sec":  round(processing_time, 3),
            "created_at":           result.get("timestamp", datetime.now().isoformat()),
            "saved_at":             datetime.now().isoformat(),
        }
        collection.insert_one(doc)
        logger.info(f"Ticket {result['ticket_id']} saved to MongoDB")
    except Exception as e:
        logger.error(f"Failed to save ticket {result.get('ticket_id')}: {e}")


# =====================================================
# REQUEST / RESPONSE MODELS
# =====================================================

class TicketRequest(BaseModel):
    customer_query: str = Field(..., description="Customer's support query")
    customer_email: Optional[str] = Field(None, description="Customer email address")
    ticket_id: Optional[str] = Field(None, description="Optional custom ticket ID")

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "customer_query": "My application crashes when I try to upload large files",
                "customer_email": "customer@example.com"
            }
        }
    )


class TicketResponse(BaseModel):
    ticket_id: str
    category: str
    final_response: str
    needs_escalation: bool
    priority: str
    timestamp: str
    conversation_history: Optional[List[str]] = None


class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str


class MetricsResponse(BaseModel):
    total_tickets: int
    escalated_tickets: int
    automation_rate: float
    average_response_time: float
    category_distribution: dict


# =====================================================
# ENDPOINTS
# =====================================================

@api_app.get("/", response_model=dict)
async def root():
    return {
        "message": "Customer Support Ticket Management System API",
        "version": "1.0.0",
        "endpoints": {
            "process_ticket": "/api/v1/tickets/process",
            "get_ticket":     "/api/v1/tickets/{ticket_id}",
            "list_tickets":   "/api/v1/tickets",
            "health":         "/health",
            "metrics":        "/api/v1/metrics",
        }
    }


@api_app.get("/health", response_model=HealthResponse)
async def health_check():
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        timestamp=datetime.now().isoformat()
    )


@api_app.post("/api/v1/tickets/process", response_model=TicketResponse)
async def process_ticket(request: TicketRequest):
    """
    Process a support ticket through the multi-agent workflow
    and persist the full conversation to MongoDB.
    """
    try:
        ticket_id = request.ticket_id or f"{config.TICKET_ID_PREFIX}-{uuid.uuid4().hex[:8].upper()}"
        logger.info(f"Processing new ticket: {ticket_id}")

        initial_state = {
            "customer_query":       request.customer_query,
            "ticket_id":            ticket_id,
            "category":             "",
            "faq_match":            "",
            "resolution":           "",
            "needs_escalation":     False,
            "final_response":       "",
            "conversation_history": [],
            "customer_email":       request.customer_email,
            "priority":             "medium",
            "timestamp":            datetime.now().isoformat(),
            "metadata":             {}
        }

        start_time = datetime.now()
        result = workflow_app.invoke(initial_state)
        processing_time = (datetime.now() - start_time).total_seconds()

        # ── Save to MongoDB ──
        save_ticket(result, processing_time)

        # ── Update in-memory metrics ──
        metrics.record_ticket(
            category=result["category"],
            escalated=result["needs_escalation"],
            response_time=processing_time
        )

        logger.info(
            f"Ticket {ticket_id} processed — "
            f"category={result['category']}, "
            f"escalated={result['needs_escalation']}, "
            f"time={processing_time:.2f}s"
        )

        return TicketResponse(
            ticket_id=result["ticket_id"],
            category=result["category"],
            final_response=result["final_response"],
            needs_escalation=result["needs_escalation"],
            priority=result["priority"],
            timestamp=result["timestamp"],
            conversation_history=result["conversation_history"]
        )

    except Exception as e:
        logger.error(f"Error processing ticket: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing ticket: {e}")


@api_app.get("/api/v1/tickets/{ticket_id}")
async def get_ticket(ticket_id: str):
    """Retrieve a single ticket by ID from MongoDB."""
    try:
        collection = get_tickets_collection()
        doc = collection.find_one({"ticket_id": ticket_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail=f"Ticket {ticket_id} not found")
        return doc
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_app.get("/api/v1/tickets")
async def list_tickets(
    limit: int = 20,
    category: Optional[str] = None,
    escalated: Optional[bool] = None,
):
    """
    List recent tickets from MongoDB.
    Optional filters: category (TECHNICAL/BILLING/GENERAL), escalated (true/false).
    """
    try:
        collection = get_tickets_collection()
        query = {}
        if category:
            query["category"] = category.upper()
        if escalated is not None:
            query["needs_escalation"] = escalated

        docs = list(
            collection.find(query, {"_id": 0})
            .sort("saved_at", -1)
            .limit(limit)
        )
        return {"total": len(docs), "tickets": docs}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_app.get("/api/v1/metrics", response_model=MetricsResponse)
async def get_metrics():
    try:
        data = metrics.get_metrics()
        return MetricsResponse(
            total_tickets=data["total_tickets"],
            escalated_tickets=data["escalated_tickets"],
            automation_rate=data["automation_rate"],
            average_response_time=data["average_response_time"],
            category_distribution=data["category_distribution"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@api_app.post("/api/v1/metrics/reset")
async def reset_metrics():
    try:
        metrics.reset()
        return {"message": "Metrics reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =====================================================
# ENTRYPOINT
# =====================================================

if __name__ == "__main__":
    import uvicorn
    config.validate()
    uvicorn.run(
        "src.api.main:api_app",
        host=config.API_HOST,
        port=config.API_PORT,
        reload=True,
        log_level=config.LOG_LEVEL.lower()
    )

from mangum import Mangum
handler = Mangum(api_app)