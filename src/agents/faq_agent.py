"""
FAQ Lookup Agent - Searches MongoDB for matching FAQs
before routing to specialized support agents.

Also doubles as a CLI to manage the FAQ database
(replaces scripts/add_faq.py):

    python -m src.agents.faq_agent              # interactive add
    python -m src.agents.faq_agent list         # list all FAQs
    python -m src.agents.faq_agent add          # interactive add
    python -m src.agents.faq_agent add <CATEGORY> <question> <answer>
"""

import logging
import sys
from difflib import SequenceMatcher
from pymongo import MongoClient

from src.config import config
from src.models.state import TicketState

logger = logging.getLogger(__name__)


# =====================================================
# DB HELPER
# =====================================================

# Lazy client — created on first use, not at import time
_client = None


def _get_client() -> MongoClient:
    """Return a reusable MongoClient, creating it on first call."""
    global _client
    if _client is None:
        _client = MongoClient(config.MONGO_URI)
    return _client


def _get_faq_collection():
    """Return the MongoDB FAQ collection."""
    return _get_client()[config.MONGO_DB_NAME][config.FAQ_COLLECTION]


# =====================================================
# AGENT
# =====================================================

def _similarity(a: str, b: str) -> float:
    """Return a 0-1 similarity score between two strings."""
    return SequenceMatcher(
        None,
        a.lower().strip(),
        b.lower().strip()
    ).ratio()


def faq_lookup_agent(state: TicketState) -> TicketState:
    """
    Search MongoDB FAQs for a match to the customer query.

    Sets state['faq_match'] if a match above the similarity
    threshold is found; leaves it empty so the workflow
    routes to the classifier otherwise.
    """
    query = state.get("customer_query", "").strip()
    ticket_id = state.get("ticket_id", "unknown")

    logger.info(f"[{ticket_id}] FAQ lookup for: {query!r}")

    state["faq_match"] = ""  # default: no match

    if not query:
        logger.warning(f"[{ticket_id}] Empty query — skipping FAQ lookup")
        return state

    try:
        collection = _get_faq_collection()
        faqs = list(collection.find({}, {"_id": 0}))
    except Exception as e:
        logger.error(f"[{ticket_id}] MongoDB error during FAQ lookup: {e}")
        return state

    if not faqs:
        logger.info(f"[{ticket_id}] FAQ collection is empty")
        return state

    best_score = 0.0
    best_faq = None

    for faq in faqs:
        score = _similarity(query, faq.get("question", ""))
        if score > best_score:
            best_score = score
            best_faq = faq

    threshold = config.FAQ_SIMILARITY_THRESHOLD

    if best_faq and best_score >= threshold:
        logger.info(
            f"[{ticket_id}] FAQ match found "
            f"(id={best_faq['id']}, score={best_score:.2f}): "
            f"{best_faq['question']!r}"
        )
        state["faq_match"] = best_faq["answer"]
        state["category"] = best_faq.get("category", "GENERAL")
    else:
        logger.info(
            f"[{ticket_id}] No FAQ match "
            f"(best score={best_score:.2f}, threshold={threshold})"
        )

    return state


# =====================================================
# FAQ MANAGEMENT (CLI)
# =====================================================

def add_faq_entry(category: str, question: str, answer: str) -> bool:
    """Insert a new FAQ document into MongoDB."""
    try:
        collection = _get_faq_collection()
        last = collection.find_one(sort=[("id", -1)])
        new_id = (last["id"] + 1) if last else 1

        collection.insert_one({
            "id": new_id,
            "category": category.upper(),
            "question": question,
            "answer": answer
        })

        print(f"\n✅ Successfully added FAQ #{new_id}")
        print(f"   Category : {category.upper()}")
        print(f"   Question : {question}")
        print(f"   Answer   : {answer}\n")
        return True

    except Exception as e:
        print(f"❌ Failed to add FAQ: {e}")
        return False


def list_faqs() -> None:
    """Print all FAQs from MongoDB."""
    try:
        collection = _get_faq_collection()
        faqs = list(collection.find({}, {"_id": 0}).sort("id", 1))
    except Exception as e:
        print(f"❌ MongoDB error: {e}")
        return

    print("\n" + "=" * 80)
    print(f"FAQ DATABASE — {len(faqs)} entries")
    print("=" * 80 + "\n")

    for faq in faqs:
        preview = (
            faq["answer"][:100] + "..."
            if len(faq["answer"]) > 100
            else faq["answer"]
        )
        print(f"[{faq['id']}] {faq['category']}")
        print(f"  Q: {faq['question']}")
        print(f"  A: {preview}")
        print()


def interactive_add() -> bool:
    """Prompt the user to fill in a new FAQ entry."""
    print("\n" + "=" * 80)
    print("ADD FAQ ENTRY — INTERACTIVE MODE")
    print("=" * 80 + "\n")

    category_map = {"1": "TECHNICAL", "2": "BILLING", "3": "GENERAL"}

    print("Select category:")
    for k, v in category_map.items():
        print(f"  {k}. {v}")

    while True:
        choice = input("\nEnter choice (1-3): ").strip()
        if choice in category_map:
            category = category_map[choice]
            break
        print("  Invalid — please enter 1, 2, or 3.")

    question = input(f"\n[{category}] Question: ").strip()
    answer   = input(f"[{category}] Answer  : ").strip()

    print("\n" + "-" * 80)
    print("Preview:")
    print("-" * 80)
    print(f"  Category : {category}")
    print(f"  Question : {question}")
    print(f"  Answer   : {answer}")
    print("-" * 80)

    if input("\nAdd this FAQ entry? (y/n): ").strip().lower() == "y":
        return add_faq_entry(category, question, answer)

    print("❌ Cancelled")
    return False


# =====================================================
# CLI ENTRY POINT
# =====================================================
