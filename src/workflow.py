"""
LangGraph Workflow - Orchestrates the multi-agent
ticket management system.
"""

import logging

from langgraph.graph import (
    StateGraph,
    END
)

from src.models.state import TicketState

from src.agents import (
    intake_agent,
    faq_lookup_agent,
    classifier_agent,
    technical_support_agent,
    billing_support_agent,
    general_support_agent,
    escalation_evaluator_agent,
    escalation_response_agent,
    response_generator_agent,
)

logger = logging.getLogger(__name__)


# =====================================================
# FAQ ROUTER
# =====================================================

def faq_router(
    state: TicketState
) -> str:
    """
    Route based on FAQ resolution.

    If FAQ already solved the issue,
    skip classifier + support agents.
    """

    faq_match = (
        state.get("faq_match", "")
        .strip()
    )

    if faq_match:

        logger.info(
            f"FAQ resolved ticket "
            f"{state['ticket_id']}"
        )

        return "response_gen"

    return "classifier"


# =====================================================
# CATEGORY ROUTER
# =====================================================

def route_by_category(
    state: TicketState
) -> str:
    """
    Route ticket to specialized agent
    based on category.
    """

    category = (
        state.get("category", "")
        .strip()
        .upper()
    )

    logger.info(
        f"Routing ticket "
        f"{state['ticket_id']} "
        f"- Category: {category}"
    )

    if "TECHNICAL" in category:

        return "technical_support"

    elif "BILLING" in category:

        return "billing_support"

    return "general_support"


# =====================================================
# ESCALATION ROUTER
# =====================================================

def handle_escalation(
    state: TicketState
) -> str:
    """
    Route based on escalation decision.
    """

    if state.get(
        "needs_escalation",
        False
    ):

        logger.info(
            f"Ticket {state['ticket_id']} "
            f"escalated to human agent"
        )

        return "escalation_response"

    logger.info(
        f"Ticket {state['ticket_id']} "
        f"proceeding to automated response"
    )

    return "response_gen"


# =====================================================
# CREATE WORKFLOW
# =====================================================

def create_workflow():
    """
    Create and configure LangGraph workflow.
    """

    logger.info(
        "Creating workflow graph"
    )

    # ==============================================
    # Initialize Workflow
    # ==============================================

    workflow = StateGraph(
        TicketState
    )

    # ==============================================
    # Add Nodes
    # ==============================================

    workflow.add_node(
        "intake",
        intake_agent
    )

    workflow.add_node(
        "faq_lookup",
        faq_lookup_agent
    )

    workflow.add_node(
        "classifier",
        classifier_agent
    )

    workflow.add_node(
        "technical_support",
        technical_support_agent
    )

    workflow.add_node(
        "billing_support",
        billing_support_agent
    )

    workflow.add_node(
        "general_support",
        general_support_agent
    )

    workflow.add_node(
        "escalation_check",
        escalation_evaluator_agent
    )

    workflow.add_node(
        "escalation_response",
        escalation_response_agent
    )

    workflow.add_node(
        "response_gen",
        response_generator_agent
    )

    # ==============================================
    # Entry Point
    # ==============================================

    workflow.set_entry_point(
        "intake"
    )

    # ==============================================
    # Intake → FAQ Lookup
    # ==============================================

    workflow.add_edge(
        "intake",
        "faq_lookup"
    )

    # ==============================================
    # FAQ Conditional Routing
    # ==============================================

    workflow.add_conditional_edges(

        "faq_lookup",

        faq_router,

        {
            "response_gen":
                "response_gen",

            "classifier":
                "classifier"
        }
    )

    # ==============================================
    # Category Routing
    # ==============================================

    workflow.add_conditional_edges(

        "classifier",

        route_by_category,

        {
            "technical_support":
                "technical_support",

            "billing_support":
                "billing_support",

            "general_support":
                "general_support"
        }
    )

    # ==============================================
    # Specialized Agents
    # → Escalation Check
    # ==============================================

    workflow.add_edge(
        "technical_support",
        "escalation_check"
    )

    workflow.add_edge(
        "billing_support",
        "escalation_check"
    )

    workflow.add_edge(
        "general_support",
        "escalation_check"
    )

    # ==============================================
    # Escalation Routing
    # ==============================================

    workflow.add_conditional_edges(

        "escalation_check",

        handle_escalation,

        {
            "escalation_response":
                "escalation_response",

            "response_gen":
                "response_gen"
        }
    )

    # ==============================================
    # END STATES
    # ==============================================

    workflow.add_edge(
        "escalation_response",
        END
    )

    workflow.add_edge(
        "response_gen",
        END
    )

    logger.info(
        "Workflow graph created successfully"
    )

    # ==============================================
    # Compile Workflow
    # ==============================================

    return workflow.compile()


# =====================================================
# COMPILED APP
# =====================================================

app = create_workflow()