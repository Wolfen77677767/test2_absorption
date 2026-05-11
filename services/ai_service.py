"""
AI Assistant Service
Provides general AI assistance with app context awareness.
Supports OpenAI API integration and local fallback responses.

To enable OpenAI API integration:
1. Install openai package: pip install openai
2. Add OPENAI_API_KEY to your .env file: OPENAI_API_KEY=your_api_key_here
3. The service will automatically use OpenAI when available, fallback to local responses otherwise
"""

import logging
import os
import random
from typing import Dict, List, Any, Optional

from services.unit_ai_service import UnitOperationsAIService

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

logger = logging.getLogger(__name__)

class AIAssistantService:
    """AI service for general assistance with app context awareness"""

    # App context information
    APP_CONTEXT = {
        "absorption_solver": {
            "name": "Absorption Gas-Liquid Solver",
            "description": "Complete McCabe-Thiele absorption calculations with stage optimization, detailed process analysis, and interactive diagrams.",
            "features": ["McCabe-Thiele diagrams", "Stage number calculations", "Sensitivity analysis", "Process optimization", "Interactive plots"],
            "formulas": ["y = (L/X) * (x_out - x_in) + y_in", "N = (ln(R+1)) / ln(α)", "η = (yin - yout) / yin * 100"]
        },
        "unit_operations": {
            "name": "Unit Operations Calculators",
            "description": "Comprehensive collection of 23+ professional unit operation calculators covering separation, heat transfer, mass transfer, and mechanical processes.",
            "count": 23,
            "categories": ["Separation", "Heat Transfer", "Mass Transfer", "Mechanical", "Reaction"]
        },
        "psychrometric_calculator": {
            "name": "Psychrometric Calculator",
            "description": "Automatic calculation of all moist air properties from two known parameters.",
            "properties": ["Dry bulb temperature", "Wet bulb temperature", "Dew point", "Relative humidity", "Humidity ratio", "Enthalpy", "Specific volume"]
        },
        "drying_calculator": {
            "name": "Drying Calculator",
            "description": "Drying process calculations including psychrometric properties and drying kinetics.",
            "features": ["Drying rate calculations", "Psychrometric analysis", "Process optimization"]
        },
        "distillation_calculator": {
            "name": "Distillation Calculator",
            "description": "Distillation column design and analysis with McCabe-Thiele method.",
            "features": ["Stage calculations", "Reflux ratio optimization", "Interactive diagrams"]
        },
        "reactors": {
            "name": "Chemical Reactors",
            "description": "Reactor design and analysis for various reaction types.",
            "types": ["Batch reactors", "Continuous stirred tank reactors", "Plug flow reactors"]
        },
        "profile_system": {
            "name": "User Profile System",
            "description": "User account management, calculation history, and personal dashboard.",
            "features": ["Calculation history", "PDF export", "Archive management", "User preferences"]
        }
    }

    # General knowledge responses for fallback
    GENERAL_RESPONSES = {
        "greeting": [
            "Bonjour ! Je suis votre assistant AI. Je peux répondre à des questions générales et vous aider avec les calculs de l'application.",
            "Salut ! Je suis là pour aider sur des questions générales, des opérations unitaires et l'utilisation de l'application.",
            "Bonjour, je peux vous aider avec des explications claires sur l'application et les concepts de génie chimique."
        ],
        "capabilities": [
            "Je peux répondre à des questions générales, expliquer des concepts de génie chimique, aider avec l'absorption, la distillation, la psychrométrie, le séchage, les réacteurs et l'utilisation de l'application.",
            "Je peux aider avec les calculs, les concepts d'opérations unitaires, les erreurs de saisie et l'utilisation des fonctions de l'application."
        ]
    }

    @classmethod
    def _get_openai_response(cls, user_message: str) -> Optional[str]:
        """Get response from OpenAI API if available and configured."""
        if not OPENAI_AVAILABLE:
            return None

        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            return None

        try:
            client = openai.OpenAI(api_key=api_key)

            system_prompt = """You are an intelligent assistant. You must always try to answer the user question clearly, even without external AI APIs.

You are integrated into a Flask chemical engineering application. You can answer general questions and also help with gas absorption, unit operations, drying, psychrometrics, calculations, and app usage.

App Context:
- Absorption Solver: McCabe-Thiele method for gas-liquid absorption design
- Unit Operations: 23+ calculators for separation, heat transfer, mass transfer, mechanical processes
- Psychrometric Calculator: Moist air properties calculations
- Drying Calculator: Drying kinetics with psychrometric analysis
- Distillation Calculator: Column design with McCabe-Thiele diagrams
- Chemical Reactors: Batch, CSTR, PFR design and analysis
- User System: Profile, history, PDF export, archive management

When answering:
- Be helpful and accurate
- Explain calculations clearly with formulas and steps
- Provide context about app features when relevant
- Answer general questions normally
- Use French for chemical engineering and app questions when possible
- Keep answers short, clairs, and utiles"""

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_message}
                ],
                max_tokens=500,
                temperature=0.7
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            return None

    @classmethod
    def _get_fallback_response(cls, user_message: str) -> str:
        """Generate fallback response using local logic."""
        topic = UnitOperationsAIService.detect_topic(user_message)
        if topic:
            response = UnitOperationsAIService.get_topic_response(topic)
            if response:
                return response

        message_lower = user_message.lower()

        # Greeting responses
        if any(word in message_lower for word in ["hello", "hi", "bonjour", "salut", "hey"]):
            return random.choice(cls.GENERAL_RESPONSES["greeting"])

        # Capability questions
        if any(word in message_lower for word in ["what can you do", "capabilities", "help", "que peux-tu faire", "aide"]):
            return random.choice(cls.GENERAL_RESPONSES["capabilities"])

        # Adsorption
        if any(word in message_lower for word in ["adsorption", "c est quoi adsorption", "c'est quoi adsorption", "adsorber"]):
            return (
                "Adsorption est une opération unitaire où des molécules d’un fluide (gaz ou liquide) se fixent à la surface d’un solide appelé adsorbant.\n\n"
                "Elle est utilisée pour:\n"
                "- purifier un gaz\n"
                "- éliminer des polluants\n"
                "- séparer certains composants\n\n"
                "Exemple: charbon actif utilisé pour filtrer l’air ou l’eau.\n\n"
                "Formule typique (Langmuir): q = (qmax * K * C) / (1 + K*C)"
            )

        # Absorption
        if any(word in message_lower for word in ["absorption", "absorber", "absorption solver"]):
            return (
                "L’absorption est le transfert d’un composant gazeux vers un liquide.\n"
                "Elle est utilisée pour éliminer des gaz solubles comme le CO2 ou le SO2.\n\n"
                "Dans l’application, le solveur calcule le nombre d’étages et trace le diagramme McCabe-Thiele.\n"
                "Formule utile: η = (yin - yout) / yin * 100"
            )

        # Distillation
        if any(word in message_lower for word in ["distillation", "distiller"]):
            return (
                "La distillation sépare des liquides par vaporisation et condensation.\n"
                "On utilise souvent la méthode McCabe-Thiele pour déterminer le nombre d’étages nécessaires.\n\n"
                "Formule simple: R = L/D (rapport de reflux)."
            )

        # Psychrometric
        if any(word in message_lower for word in ["psychrometric", "psychrométrie", "air humide", "humidité relative", "point de rosée"]):
            return (
                "Le calcul psychrométrique permet de trouver les propriétés de l’air humide à partir de deux paramètres connus.\n"
                "Exemples de formules: Y = 0.62198 * Pv / (P - Pv), h = 1.006*Ts + Y*(2501 + 1.86*Ts)."
            )

        # Drying
        if any(word in message_lower for word in ["drying", "séchage", "sécheur"]):
            return (
                "Le séchage consiste à évaporer l’eau d’un solide en utilisant de l’air chaud.\n"
                "On calcule le temps de séchage avec la chaleur disponible et la perte d’eau.\n\n"
                "Formule type: t = m * λ / (h * A * ΔT)."
            )

        # Reactors
        if any(word in message_lower for word in ["reactor", "réacteur", "pfr", "cstr", "batch"]):
            return (
                "Un réacteur chimique est un équipement où a lieu une réaction.\n"
                "Pour un réacteur discontinu (batch): X = (C_A0 - C_A) / C_A0.\n"
                "Pour un PFR: τ = V / v0. Pour un CSTR: -r_A = k * C_A^n."
            )

        # App usage questions
        if any(word in message_lower for word in ["profil", "historique", "dashboard", "archive", "pdf", "export"]):
            return (
                "La page Profil permet de gérer votre compte et vos préférences.\n"
                "L’Historique liste les calculs effectués.\n"
                "L’Archive stocke les rapports/PDF et permet de retrouver des résultats anciens."
            )

        if any(word in message_lower for word in ["solv", "calculate", "calculateur", "unit operations", "unité", "opération unitaire"]):
            return (
                "Utilisez l’outil adapté: l’Absorption Solver pour les colonnes d’absorption, l’onglet Unit Operations pour les autres opérations unitaires, et le calculateur psychrométrique pour les propriétés de l’air humide."
            )

        # Error/help questions
        if any(word in message_lower for word in ["error", "erreur", "problem", "problème", "bug", "planté", "ne fonctionne pas"]):
            return (
                "Vérifiez d’abord les unités et les valeurs d’entrée.\n"
                "Par exemple, les fractions doivent être entre 0 et 1, les débits ne doivent pas être nuls, et les paramètres doivent être cohérents."
            )

        # General engineering assistance
        if any(word in message_lower for word in ["génie chimique", "processus", "process", "opération unitaire", "formule", "formules"]):
            return (
                "Le génie chimique traite de la conception et de l’optimisation des procédés.\n"
                "Commencez toujours par identifier les variables connues, choisir la formule adaptée, et contrôler les unités."
            )

        # General questions that can be answered locally
        if "capitale" in message_lower and "france" in message_lower:
            return "La capitale de la France est Paris."

        if any(word in message_lower for word in ["qui es-tu", "qui es tu", "qui êtes", "qui etes"]):
            return (
                "Je suis un assistant intelligent intégré à cette application Flask.\n"
                "Je peux répondre à des questions générales et aider avec l’absorption, les opérations unitaires et l’utilisation de l’application."
            )

        if any(word in message_lower for word in ["comment ça va", "ça va", "how are you"]):
            return "Je vais bien, merci. Comment puis-je vous aider aujourd’hui ?"

        # Default unknown answer
        return (
            "Je ne suis pas sûr, mais voici une explication générale :\n"
            "Commencez par clarifier le sujet et les données disponibles, puis appliquez la formule qui correspond à l’opération ou à la propriété recherchée.\n"
            "Si vous souhaitez, précisez votre question pour une réponse plus ciblée."
        )

    @classmethod
    def get_ai_response(cls, user_message: str) -> str:
        """
        Generate AI response with app context awareness.
        Uses OpenAI API if available, otherwise local fallback.
        """
        try:
            # Try OpenAI first
            openai_response = cls._get_openai_response(user_message)
            if openai_response:
                return openai_response

            # Fall back to local logic
            return cls._get_fallback_response(user_message)

        except Exception as e:
            logger.exception("Error generating AI response")
            return "Désolé, je n'ai pas pu traiter votre question. Pouvez-vous reformuler ?"