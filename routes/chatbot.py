"""
AI Chatbot Assistant Route
Handles chat messages and returns AI-generated responses.
"""

import logging
import os

from flask import Blueprint, jsonify, request

from services.ai_service import AIAssistantService

logger = logging.getLogger(__name__)

chatbot_bp = Blueprint("chatbot", __name__, url_prefix="/chatbot")


def get_ai_response(user_message):
    """
    Generate a response using AI assistant service.
    """
    return AIAssistantService.get_ai_response(user_message)


@chatbot_bp.route("/message", methods=["POST"])
def send_message():
    """
    Accept a user message via AJAX and return an AI-generated response.
    """
    try:
        data = request.get_json(silent=True) or {}
        user_message = data.get("message", "").strip()

        if not user_message:
            return jsonify({
                "success": False,
                "response": "Please enter a message.",
                "type": "error",
            }), 400

        logger.info("Chatbot message received: %s", user_message[:100])

        ai_response = get_ai_response(user_message)

        return jsonify({
            "success": True,
            "response": ai_response,
            "type": "ai",
        }), 200

    except RuntimeError as exc:
        logger.error("Chatbot configuration error: %s", exc)
        return jsonify({
            "success": False,
            "response": str(exc),
            "type": "error",
        }), 500

    except Exception as exc:
        logger.exception("Chatbot API error: %s", exc)
        return jsonify({
            "success": False,
            "response": "Sorry, the AI assistant is temporarily unavailable. Please try again.",
            "type": "error",
        }), 500


@chatbot_bp.route("/welcome", methods=["GET"])
def welcome_message():
    """
    Get a welcome message when the chat is first opened.
    """
    return jsonify({
        "welcome": True,
        "message": "Hello! I'm your AI assistant. I can help with general questions and also assist with absorption calculations, unit operations, and app features.",
    }), 200
