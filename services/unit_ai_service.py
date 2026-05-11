"""
Unit Operations AI Service
Provides explanations and AI assistance for unit operations.
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)

class UnitOperationsAIService:
    """AI service for unit operations explanations and assistance"""

    UNIT_OPERATIONS = {
        "decantation": {
            "name": "Décantation",
            "description": "Séparation gravitationnelle des phases liquides immiscibles ou solides en suspension",
            "formulas": ["v = (ρ_p - ρ_f) * g * d² / (18 * μ)", "t = h / v"],
            "applications": "Séparation huile-eau, clarification, sédimentation"
        },
        "centrifugation": {
            "name": "Centrifugation",
            "description": "Séparation accélérée par force centrifuge",
            "formulas": ["ω = 2πn", "F_c = mω²r", "Σ = ω²r / g"],
            "applications": "Séparation cellules, protéines, particules fines"
        },
        "filtration": {
            "name": "Filtration",
            "description": "Séparation solide-liquide par passage à travers un milieu poreux",
            "formulas": ["ΔP = μ * v * R", "J = ΔP / (μ * R_total)"],
            "applications": "Clarification, stérilisation, récupération de solides"
        },
        "distillation": {
            "name": "Distillation",
            "description": "Séparation de mélanges liquides par évaporation et condensation",
            "formulas": ["y = αx / (1 + (α-1)x)", "R = L/D", "N = (ln(R+1)) / ln(α)"],
            "applications": "Purification, séparation azeotropes, récupération solvants"
        },
        "extraction_liquid_liquid": {
            "name": "Extraction liquide-liquide",
            "description": "Transfert sélectif d'un soluté entre deux phases liquides immiscibles",
            "formulas": ["K = y/x", "E = K * (V_org/V_aq)", "N = ln(E+1) / ln(E)"],
            "applications": "Extraction métalloïdes, purification, récupération"
        },
        "extraction_solid_liquid": {
            "name": "Extraction solide-liquide",
            "description": "Extraction de composés solubles depuis une matrice solide",
            "formulas": ["C = C₀ * exp(-kt)", "m = V * (C₀ - C)"],
            "applications": "Thé, café, pharmacie, analyse chimique"
        },
        "evaporation": {
            "name": "Évaporation",
            "description": "Concentration de solutions par vaporisation du solvant",
            "formulas": ["Q = m * λ", "A = Q / (U * ΔT)", "t = V * ρ / Q"],
            "applications": "Concentration jus, lait, produits chimiques"
        },
        "drying": {
            "name": "Séchage",
            "description": "Élimination de l'humidité des solides par évaporation. Inclut le calcul psychrométrique pour les propriétés de l'air humide.",
            "formulas": [
                "N = k * A * (P_v - P_a)",  # Drying rate
                "t = m * λ / (h * A * ΔT)",  # Drying time
                "P_sat = 0.61078 * exp((17.27*T)/(T+237.3))",  # Tetens equation
                "Y = 0.62198 * Pv / (P - Pv)",  # Humidity ratio
                "h = 1.006*Ts + Y*(2501 + 1.86*Ts)",  # Enthalpy
                "Vs = 0.287042*(Ts+273.15)*(1+1.607858*Y)/P",  # Specific volume
                "γ = ln(Pv/0.61078); Tr = (237.3*γ)/(17.27-γ)"  # Dew point
            ],
            "psychrometric_properties": {
                "Ts": "Température sèche (Dry Bulb Temperature) - température de l'air (°C)",
                "Th": "Température humide (Wet Bulb Temperature) - température d'équilibre avec l'eau (°C)",
                "Tr": "Température de rosée (Dew Point Temperature) - température où la condensation commence (°C)",
                "HR": "Humidité relative (Relative Humidity) - rapport Pv/Psat (%)",
                "Y": "Humidité spécifique/absolue (Humidity Ratio) - masse eau/masse air sec (kg/kg ou g/kg)",
                "h": "Enthalpie spécifique (Specific Enthalpy) - énergie totale par kg air sec (kJ/kg)",
                "Vs": "Volume spécifique (Specific Volume) - volume par kg air sec (m³/kg)",
                "Pv": "Pression partielle vapeur (Vapor Pressure) (kPa)",
                "Psat": "Pression de vapeur saturante (Saturation Vapor Pressure) (kPa)"
            },
            "applications": "Aliments, produits chimiques, bois, textiles. Calculs psychrométriques pour dimensionnement des sécheurs."
        },
        "psychrometric_calculator": {
            "name": "Calculateur Psychrométrique",
            "description": "Calcul automatique de toutes les propriétés de l'air humide à partir de deux paramètres connus",
            "formulas": [
                "P_sat = 0.61078 * exp((17.27*T)/(T+237.3))",  # Tetens
                "Y = 0.62198 * Pv / (P - Pv)",  # Humidity ratio
                "h = 1.006*Ts + Y*(2501 + 1.86*Ts)",  # Enthalpy
                "Vs = 0.287042*(Ts+273.15)*(1+1.607858*Y)/P",  # Specific volume
                "γ = ln(Pv/0.61078); Tr = (237.3*γ)/(17.27-γ)"  # Dew point
            ],
            "applications": "Dimensionnement de sécheurs, conditionnement d'air, calculs de propriétés de l'air humide"
        },
        "crystallization": {
            "name": "Cristallisation",
            "description": "Formation de cristaux solides à partir d'une solution sursaturée",
            "formulas": ["S = C / C*", "G = k * (S-1)^g", "L = k_b * G^b"],
            "applications": "Sucres, sels, produits pharmaceutiques"
        },
        "chemical_reactors": {
            "name": "Réacteurs chimiques",
            "description": "Vases où se déroulent les réactions chimiques",
            "formulas": ["-r_A = k * C_A^n", "X = (C_A0 - C_A) / C_A0", "τ = V / v0"],
            "applications": "Synthèse organique, pétrochimie, biochimie"
        },
        "adsorption": {
            "name": "Adsorption",
            "description": "Fixation de molécules sur une surface solide",
            "formulas": ["q = (qmax * K * C) / (1 + K*C)", "q = Kf * C^(1/n)"],
            "applications": "Traitement eau, purification air, chromatographie"
        },
        "absorption_gas_liquid": {
            "name": "Absorption gaz-liquide",
            "description": "Transfert de gaz soluble dans un liquide",
            "formulas": ["C = H * P", "N_OG = (k_L * a) * H", "y = (L/X) * (x_out - x_in) + y_in"],
            "applications": "Désulfuration, décarbonatation, absorption CO2"
        },
        "membrane_separation": {
            "name": "Séparation par membranes",
            "description": "Séparation par différence de perméabilité membranaire",
            "formulas": ["J = Pm * (ΔP / e)", "α = PA / PB", "R = 1 - (Cp/Cf)"],
            "applications": "Osmose inverse, nanofiltration, dialyse"
        },
        "heat_exchange": {
            "name": "Échange thermique",
            "description": "Transfert de chaleur entre deux fluides",
            "formulas": ["Q = m * Cp * ΔT", "Q = U * A * ΔT_lm", "ΔT_lm = (ΔT1 - ΔT2) / ln(ΔT1/ΔT2)"],
            "applications": "Chauffage, refroidissement, récupération chaleur"
        },
        "mixing_agitation": {
            "name": "Mélange et agitation",
            "description": "Homogénéisation de mélanges par agitation mécanique",
            "formulas": ["P = Np * ρ * N³ * D⁵", "Re = ρ * N * D² / μ", "t_mix = k * (μ/ρ) * (D²/N) * f"],
            "applications": "Réactions chimiques, suspensions, émulsions"
        },
        "size_reduction": {
            "name": "Broyage / réduction de taille",
            "description": "Réduction de la taille des particules solides",
            "formulas": ["E = Wi * (10/√P80 - 10/√F80)", "R = D_i / D_f"],
            "applications": "Préparation échantillons, libération produits, amélioration propriétés"
        },
        "sieving": {
            "name": "Tamisage / classification",
            "description": "Séparation granulométrique par tamisage",
            "formulas": ["d50 = Σ (xi * di)", "σ = √[Σ ((di - d50)² * xi)]"],
            "applications": "Contrôle qualité, classification produits, analyse granulométrie"
        },
        "fluidization": {
            "name": "Fluidisation",
            "description": "Suspension de particules solides dans un écoulement fluide ascendant",
            "formulas": ["u = Q / A", "ΔP = (ρ_s - ρ_f) * (1-ε) * g * H"],
            "applications": "Réacteurs catalytiques, séchage, transport pneumatique"
        },
        "fluid_transport": {
            "name": "Transport des fluides",
            "description": "Écoulement de fluides dans conduites avec pertes de charge",
            "formulas": ["Re = ρ * v * D / μ", "ΔP = f * (L/D) * (ρ * v² / 2)", "Q = v * A"],
            "applications": "Réseaux de distribution, pompage, ventilation"
        },
        "pumping": {
            "name": "Pompes",
            "description": "Machines pour le déplacement de fluides",
            "formulas": ["Ph = ρ * g * Q * H", "P = Ph / η", "NPSH = (P_vap + P_stat - P_vap_loss) / (ρ * g)"],
            "applications": "Circulation, transfert, pressurisation"
        },
        "cyclones": {
            "name": "Cyclones / séparation gaz-solide",
            "description": "Séparation de particules solides en suspension dans un gaz par force centrifuge",
            "formulas": ["v = Q / A", "η = 1 - exp(-k * (Q/μ)^a)", "ΔP = k * ρ * v²"],
            "applications": "Dépoussiérage, classification particules, protection filtres"
        },
        "humidification_dehumidification": {
            "name": "Humidification / déshumidification",
            "description": "Contrôle de l'humidité de l'air",
            "formulas": ["Y = m_v / m_s", "φ = P_v / P_sat", "m_eau = m_air * (Y_out - Y_in)"],
            "applications": "Conditionnement air, séchage, confort, procédés industriels"
        }
    }

    UNIT_OPERATIONS_KB = {
        "adsorption": {
            "definition": "Adsorption est une opération unitaire où des molécules d’un fluide se fixent sur la surface d’un solide appelé adsorbant.",
            "applications": "Purification de gaz, traitement d'eau, séparation de polluants.",
            "formula": "q = (qmax * K * C) / (1 + K*C)"
        },
        "absorption": {
            "definition": "Absorption est le transfert d'un composant gazeux vers un liquide, souvent utilisé pour enlever des gaz solubles.",
            "applications": "Désulfuration, élimination de CO2, lavage de gaz.",
            "formula": "η = (yin - yout) / yin * 100"
        },
        "distillation": {
            "definition": "Distillation est une séparation de liquides par vaporisation et condensation sur une colonne.",
            "applications": "Séparation de solvants, purification, fractionnement de mélanges.",
            "formula": "R = L / D"
        },
        "extraction": {
            "definition": "Extraction est une séparation où un soluté passe d'une phase à une autre, souvent liquide-liquide ou solide-liquide.",
            "applications": "Industrie pharmaceutique, traitement des eaux, récupération de composants.",
            "formula": "M1 = F + S ; xM1 = (F*xF + S*y0) / (F + S)"
        },
        "filtration": {
            "definition": "Filtration est une séparation solide-liquide où le fluide passe à travers un milieu poreux pour retenir les solides.",
            "applications": "Clarification, stérilisation, séparation de boues.",
            "formula": "ΔP = μ * v * R"
        },
        "evaporation": {
            "definition": "Évaporation est la concentration d'une solution par vaporisation du solvant.",
            "applications": "Concentration de produits chimiques, aliments, solutions.",
            "formula": "Q = m * λ"
        },
        "sechage": {
            "definition": "Séchage est l'élimination de l'humidité d'un solide par l'action de l'air ou de la chaleur.",
            "applications": "Produits alimentaires, bois, pharmaceutique, textiles.",
            "formula": "t = m * λ / (h * A * ΔT)"
        },
        "cristallisation": {
            "definition": "Cristallisation est la formation de cristaux solides à partir d'une solution sursaturée.",
            "applications": "Production de sels, sucres, produits pharmaceutiques.",
            "formula": "S = C / C*"
        },
        "reacteur": {
            "definition": "Réacteur est un équipement où se déroule une réaction chimique contrôlée.",
            "applications": "Synthèse chimique, production en continu, transformation de matières premières.",
            "formula": "τ = V / v0"
        }
    }

    @classmethod
    def detect_topic(cls, message: str) -> str:
        """Detect a known unit operation topic from user message."""
        message = message.lower()
        if "adsorption" in message:
            return "adsorption"
        if "absorption" in message or "absorber" in message:
            return "absorption"
        if "distillation" in message or "distiller" in message:
            return "distillation"
        if "extraction" in message:
            return "extraction"
        if "filtration" in message or "filtrer" in message:
            return "filtration"
        if "évaporation" in message or "evaporation" in message:
            return "evaporation"
        if "séchage" in message or "sechage" in message:
            return "sechage"
        if "cristallisation" in message or "cristal" in message:
            return "cristallisation"
        if "réacteur" in message or "reacteur" in message or "pfr" in message or "cstr" in message or "batch" in message:
            return "reacteur"
        return ""

    @classmethod
    def get_topic_response(cls, topic: str) -> str:
        """Format a structured response for a known topic."""
        data = cls.UNIT_OPERATIONS_KB.get(topic)
        if not data:
            return ""

        return (
            f"{data['definition']}\n\n"
            f"Applications:\n- {data['applications']}\n\n"
            f"Formule simple: {data['formula']}"
        )

    @classmethod
    def get_operation_info(cls, operation_key: str) -> Dict[str, Any]:
        """Get information about a specific unit operation"""
        return cls.UNIT_OPERATIONS.get(operation_key, {})

    @classmethod
    def get_all_operations(cls) -> List[Dict[str, Any]]:
        """Get list of all unit operations"""
        operations = []
        for key, info in cls.UNIT_OPERATIONS.items():
            operations.append({
                "key": key,
                "name": info["name"],
                "description": info["description"],
                "formulas": info["formulas"],
                "applications": info["applications"]
            })
        return operations

    @classmethod
    def get_ai_response(cls, user_message: str) -> str:
        """
        Generate AI response specialized in unit operations.
        This is a simple implementation - in production, integrate with actual AI API.
        """
        try:
            # First check the structured knowledge base for known topics
            topic = cls.detect_topic(user_message)
            if topic:
                response = cls.get_topic_response(topic)
                if response:
                    return response

            # Simple keyword-based responses for unit operations
            message_lower = user_message.lower()

            # Check for specific operations
            for key, info in cls.UNIT_OPERATIONS.items():
                if key.replace("_", " ") in message_lower or info["name"].lower() in message_lower:
                    response = f"À propos de {info['name']}: {info['description']}\n\nApplications: {info['applications']}\n\nFormules principales: {', '.join(info['formulas'])}"

                    # Add psychrometric properties explanation for drying
                    if key == "drying" and "psychrometric" in info:
                        response += f"\n\nPropriétés psychrométriques:\n"
                        for prop, desc in info["psychrometric_properties"].items():
                            response += f"- {prop}: {desc}\n"

                    return response

            # Psychrometric-specific questions
            if "psychrometric" in message_lower or "diagramme psychrométrique" in message_lower:
                return """Le diagramme psychrométrique représente les propriétés de l'air humide. Il permet de calculer toutes les propriétés de l'air à partir de deux paramètres connus.

Propriétés principales:
• Ts: Température sèche (°C) - température mesurée par thermomètre ordinaire
• Th: Température humide (°C) - température d'équilibre avec l'eau (thermomètre mouillé)
• Tr: Température de rosée (°C) - température où la condensation commence
• HR: Humidité relative (%) - rapport entre pression partielle vapeur et pression saturante
• Y: Humidité spécifique (kg/kg ou g/kg) - masse d'eau par kg d'air sec
• h: Enthalpie spécifique (kJ/kg) - énergie totale par kg d'air sec
• Vs: Volume spécifique (m³/kg) - volume occupé par kg d'air sec

Utilisez notre calculateur psychrométrique pour déterminer automatiquement toutes les propriétés à partir de deux paramètres connus."""

            if any(word in message_lower for word in ["température sèche", "dry bulb", "ts"]):
                return "La température sèche (Ts) est la température de l'air mesurée par un thermomètre ordinaire. Elle est l'un des paramètres fondamentaux du diagramme psychrométrique, utilisée avec un autre paramètre pour calculer toutes les propriétés de l'air humide."

            if any(word in message_lower for word in ["température humide", "wet bulb", "th"]):
                return "La température humide (Th) est la température atteinte par un thermomètre dont le réservoir est entouré d'une mousseline humide. Elle représente la température d'équilibre entre l'air et l'eau, et est utilisée pour mesurer l'humidité de l'air."

            if any(word in message_lower for word in ["point de rosée", "dew point", "tr"]):
                return "Le point de rosée (Tr) est la température à laquelle la vapeur d'eau contenue dans l'air commence à condenser. En dessous de cette température, l'air devient saturé et de la condensation apparaît."

            if any(word in message_lower for word in ["humidité relative", "relative humidity", "hr"]):
                return "L'humidité relative (HR) est le rapport entre la pression partielle de vapeur d'eau dans l'air et la pression de vapeur saturante à la même température, exprimée en pourcentage. Elle varie de 0% (air complètement sec) à 100% (air saturé)."

            if any(word in message_lower for word in ["humidité spécifique", "humidity ratio", "y"]):
                return "L'humidité spécifique (Y) est la masse d'eau contenue dans l'air par kg d'air sec. Elle s'exprime généralement en g/kg ou kg/kg. Contrairement à l'humidité relative, elle ne dépend pas de la température."

            if any(word in message_lower for word in ["enthalpie", "enthalpy", "h"]):
                return "L'enthalpie spécifique (h) représente l'énergie totale contenue dans l'air humide par kg d'air sec. Elle comprend l'énergie sensible (liée à la température) et l'énergie latente (liée à la vapeur d'eau). Formule: h = 1.006×Ts + Y×(2501 + 1.86×Ts)"

            if any(word in message_lower for word in ["volume spécifique", "specific volume", "vs"]):
                return "Le volume spécifique (Vs) est le volume occupé par 1 kg d'air sec humide. Il dépend de la température, de l'humidité et de la pression. Formule: Vs = 0.287042×(Ts+273.15)×(1+1.607858×Y)/P"

            # General unit operations questions
            if "unit operation" in message_lower or "opération unitaire" in message_lower:
                return "Les opérations unitaires sont les étapes fondamentales des procédés chimiques. Elles incluent la séparation, le transfert de matière, le transfert de chaleur, et les réactions. Chaque opération a ses propres principes physiques et formules mathématiques."

            if "calcul" in message_lower or "calculate" in message_lower:
                return "Pour les calculs d'opérations unitaires, utilisez les formules spécifiques à chaque opération. Par exemple, pour l'adsorption, utilisez les isothermes de Langmuir ou Freundlich. Assurez-vous d'avoir toutes les données nécessaires avant de commencer."

            # Default response
            return "Je suis spécialisé dans les opérations unitaires du génie chimique. Je peux vous aider avec des explications sur la distillation, l'absorption, l'extraction, les échangeurs de chaleur, et bien d'autres opérations. Quelle opération vous intéresse ?"

        except Exception as e:
            logger.exception("Error generating AI response")
            return "Désolé, je n'ai pas pu traiter votre question. Pouvez-vous reformuler ?"