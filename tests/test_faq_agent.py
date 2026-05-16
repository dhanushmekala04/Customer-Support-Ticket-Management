"""
Tests for the FAQ Lookup Agent.

Tests the agent that searches MongoDB for matching FAQs.
"""

import pytest
from unittest.mock import patch, MagicMock
from src.agents.faq_agent import faq_lookup_agent, load_faq_database


class TestFAQAgent:
    """Test suite for FAQ Lookup Agent."""

    def test_faq_agent_finds_match(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent finds a matching answer."""
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        mock_chatgpt("Click 'Forgot Password' on the login page and follow the instructions.")

        result = faq_lookup_agent(general_ticket_state)

        assert result["faq_match"] != ""
        assert "Click 'Forgot Password'" in result["faq_match"]
        assert len(result["conversation_history"]) == 1
        assert "[FAQ] Match found" in result["conversation_history"][0]

    def test_faq_agent_no_match(self, technical_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent handles no match scenario."""
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        mock_chatgpt("NO_MATCH")

        result = faq_lookup_agent(technical_ticket_state)

        assert result["faq_match"] == ""
        assert "[FAQ] No direct match found" in result["conversation_history"][0]

    def test_faq_agent_empty_database(self, base_ticket_state, mock_chatgpt, monkeypatch):
        """Test FAQ agent behavior with empty database."""
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: {"faqs": []}
        )

        result = faq_lookup_agent(base_ticket_state)

        assert result["faq_match"] == "No FAQ entries available"
        assert "[FAQ] No FAQ database found" in result["conversation_history"][0]

    def test_faq_agent_preserves_other_state(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent doesn't modify unrelated state fields."""
        general_ticket_state["priority"] = "high"
        general_ticket_state["metadata"] = {"source": "email"}

        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        mock_chatgpt("Click 'Forgot Password' on the login page.")

        result = faq_lookup_agent(general_ticket_state)

        assert result["priority"] == "high"
        assert result["metadata"]["source"] == "email"
        assert result["ticket_id"] == "TKT-GEN001"

    def test_load_faq_database_success(self, sample_faq_database):
        """Test successful FAQ database loading from MongoDB."""
        mock_collection = MagicMock()
        mock_collection.find.return_value.sort.return_value = sample_faq_database["faqs"]

        with patch("src.agents.faq_agent._get_faq_collection", return_value=mock_collection):
            result = load_faq_database()

        assert "faqs" in result
        assert len(result["faqs"]) == 5
        assert result["faqs"][0]["question"] == "How do I reset my password?"

    def test_load_faq_database_connection_error(self):
        """Test FAQ database loading when MongoDB is unreachable."""
        with patch("src.agents.faq_agent._get_faq_collection", side_effect=Exception("connection refused")):
            result = load_faq_database()

        assert result == {"faqs": []}

    def test_load_faq_database_empty_collection(self):
        """Test FAQ database loading when the collection has no documents."""
        mock_collection = MagicMock()
        mock_collection.find.return_value.sort.return_value = []

        with patch("src.agents.faq_agent._get_faq_collection", return_value=mock_collection):
            result = load_faq_database()

        assert result == {"faqs": []}

    def test_faq_agent_conversation_history_append(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that FAQ agent appends to existing conversation history."""
        general_ticket_state["conversation_history"] = ["[INTAKE] Customer asking about password"]

        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        mock_chatgpt("Click 'Forgot Password' on the login page.")

        result = faq_lookup_agent(general_ticket_state)

        assert len(result["conversation_history"]) == 2
        assert "[INTAKE]" in result["conversation_history"][0]
        assert "[FAQ]" in result["conversation_history"][1]

    def test_faq_agent_truncates_long_match_in_history(self, general_ticket_state, mock_chatgpt, sample_faq_database, monkeypatch):
        """Test that very long FAQ matches are truncated in conversation history."""
        monkeypatch.setattr(
            "src.agents.faq_agent.load_faq_database",
            lambda: sample_faq_database
        )

        long_response = "A" * 200
        mock_chatgpt(long_response)

        result = faq_lookup_agent(general_ticket_state)

        # Full match stored in state
        assert len(result["faq_match"]) == 200

        # History entry truncated to 100 chars + "..."
        history_entry = result["conversation_history"][0]
        assert "..." in history_entry


if __name__ == "__main__":
    pytest.main([__file__, "-v"])