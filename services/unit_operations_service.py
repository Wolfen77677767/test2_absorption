"""
Unit operations service.

Provides metadata, form definitions, and calculation logic for the
unit-operations dashboard and calculator pages.
"""

from __future__ import annotations

import math
import re
from copy import deepcopy
from typing import Any, Callable, Dict, List, Optional

from services.psychrometric_service import PsychrometricService


GRAVITY = 9.81


class UnitOperationsService:
    """Service layer for unit-operations pages and calculators."""

    CATEGORY_META = {
        "Separation": {"badge_class": "badge-separation"},
        "Heat Transfer": {"badge_class": "badge-heat-transfer"},
        "Mass Transfer": {"badge_class": "badge-mass-transfer"},
        "Mechanical": {"badge_class": "badge-mechanical"},
        "Reaction": {"badge_class": "badge-reaction"},
    }

    OPERATION_DEFINITIONS: List[Dict[str, Any]] = [
        {
            "slug": "decantation",
            "key": "decantation",
            "name": "Décantation",
            "category": "Separation",
            "icon": "fas fa-layer-group",
            "definition": "Séparation gravitaire de phases liquides immiscibles ou de particules solides en suspension.",
            "description": "Évalue la vitesse de chute, le régime d'écoulement, la surface minimale et les temps caractéristiques d'un décanteur.",
            "applications": "Clarification, séparation huile-eau, épaississement, sédimentation.",
            "formulas": [
                "Re = rho_l * v * d / mu",
                "v = g * d^2 * (rho_s - rho_l) / (18 * mu)",
                "Smin = Q / vc",
                "tsej = S * H / Q",
                "tc = H / vc",
            ],
            "fields": [
                {"name": "rho_l", "label": "Densité du fluide", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "rho_s", "label": "Densité du solide", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "mu", "label": "Viscosité dynamique", "unit": "Pa.s", "required": False, "step": "any"},
                {"name": "d", "label": "Diamètre de particule", "unit": "m", "required": False, "step": "any"},
                {"name": "v", "label": "Vitesse observée", "unit": "m/s", "required": False, "step": "any"},
                {"name": "Q", "label": "Débit volumique", "unit": "m³/s", "required": False, "step": "any"},
                {"name": "vc", "label": "Vitesse critique / clarification", "unit": "m/s", "required": False, "step": "any"},
                {"name": "S", "label": "Surface de décantation", "unit": "m²", "required": False, "step": "any"},
                {"name": "H", "label": "Hauteur de liquide", "unit": "m", "required": False, "step": "any"},
            ],
            "handler": "_calculate_decantation",
        },
        {
            "slug": "centrifugation",
            "key": "centrifugation",
            "name": "Centrifugation",
            "category": "Separation",
            "icon": "fas fa-compact-disc",
            "definition": "Séparation accélérée par champ centrifuge.",
            "description": "Calcule la vitesse angulaire, la force centrifuge, le facteur de séparation et la vitesse de sédimentation centrifuge.",
            "applications": "Séparation de cellules, protéines, boues, particules fines.",
            "formulas": [
                "omega = 2 * pi * N / 60",
                "Fc = m * omega^2 * r",
                "K = omega^2 * r / g",
                "vSC = vCL * K",
            ],
            "fields": [
                {"name": "m", "label": "Masse de particule", "unit": "kg", "required": False, "step": "any"},
                {"name": "N", "label": "Vitesse de rotation", "unit": "tr/min", "required": True, "step": "any"},
                {"name": "r", "label": "Rayon", "unit": "m", "required": True, "step": "any"},
                {"name": "vCL", "label": "Vitesse de Stokes classique", "unit": "m/s", "required": False, "step": "any"},
            ],
            "handler": "_calculate_centrifugation",
        },
        {
            "slug": "filtration",
            "key": "filtration",
            "name": "Filtration",
            "category": "Separation",
            "icon": "fas fa-filter",
            "definition": "Séparation solide-liquide à travers un milieu poreux.",
            "description": "Applique les relations de Darcy, de filtration à pression constante et de filtration à débit constant.",
            "applications": "Clarification, récupération de solides, stérilisation.",
            "formulas": [
                "deltaP = mu * v * (eG + eS) / beta0",
                "t = A * V^2 + B * V",
                "deltaP = A * t + B",
            ],
            "fields": [
                {"name": "mu", "label": "Viscosité", "unit": "Pa.s", "required": False, "step": "any"},
                {"name": "v", "label": "Vitesse de filtration", "unit": "m/s", "required": False, "step": "any"},
                {"name": "eG", "label": "Résistance gâteau", "unit": "-", "required": False, "step": "any"},
                {"name": "eS", "label": "Résistance support", "unit": "-", "required": False, "step": "any"},
                {"name": "beta0", "label": "Perméabilité beta0", "unit": "-", "required": False, "step": "any"},
                {"name": "A_coef", "label": "Coefficient A", "unit": "selon modèle", "required": False, "step": "any"},
                {"name": "B_coef", "label": "Coefficient B", "unit": "selon modèle", "required": False, "step": "any"},
                {"name": "V", "label": "Volume filtré", "unit": "m³", "required": False, "step": "any"},
                {"name": "t", "label": "Temps", "unit": "s", "required": False, "step": "any"},
            ],
            "handler": "_calculate_filtration",
        },
        {
            "slug": "distillation",
            "key": "distillation",
            "name": "Distillation",
            "category": "Separation",
            "icon": "fas fa-flask",
            "definition": "Séparation par différences de volatilité.",
            "description": "Calcule l'équilibre vapeur-liquide, la droite d'enrichissement, le reflux minimum et les bilans matière.",
            "applications": "Purification, récupération de solvants, séparation de mélanges.",
            "formulas": [
                "y = alpha * x / (1 + (alpha - 1) * x)",
                "y = R / (R + 1) * x + xD / (R + 1)",
                "Rmin = (xD - yF) / (yF - xF)",
                "F = D + W ; F * xF = D * xD + W * xW",
            ],
            "fields": [
                {"name": "alpha", "label": "Volatilité relative", "unit": "-", "required": False, "step": "any"},
                {"name": "x", "label": "Fraction molaire liquide x", "unit": "-", "required": False, "step": "any"},
                {"name": "R", "label": "Taux de reflux R", "unit": "-", "required": False, "step": "any"},
                {"name": "xD", "label": "Composition distillat xD", "unit": "-", "required": False, "step": "any"},
                {"name": "yF", "label": "Composition vapeur alimentation yF", "unit": "-", "required": False, "step": "any"},
                {"name": "xF", "label": "Composition alimentation xF", "unit": "-", "required": False, "step": "any"},
                {"name": "F", "label": "Débit alimentation F", "unit": "kmol/h", "required": False, "step": "any"},
                {"name": "D", "label": "Débit distillat D", "unit": "kmol/h", "required": False, "step": "any"},
                {"name": "W", "label": "Débit résidu W", "unit": "kmol/h", "required": False, "step": "any"},
                {"name": "xW", "label": "Composition résidu xW", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_distillation",
        },
        {
            "slug": "extraction-liquide-liquide",
            "key": "extraction_liquid_liquid",
            "name": "Extraction liquide-liquide",
            "category": "Mass Transfer",
            "icon": "fas fa-vials",
            "definition": "Transfert sélectif d'un soluté entre deux phases liquides immiscibles.",
            "description": "Évalue le mélange de contact et les solvants minimum et maximum.",
            "applications": "Purification, récupération de composés, hydrométallurgie.",
            "formulas": [
                "M1 = F + S0",
                "xM1 = (F * xF + S0 * y0) / (F + S0)",
                "S0min = ((xF - xD) / (xD - y0)) * F",
                "S0max = ((xF - yK) / (yK - y0)) * F",
            ],
            "fields": [
                {"name": "F", "label": "Débit alimentation F", "unit": "kg/h", "required": False, "step": "any"},
                {"name": "S0", "label": "Débit solvant S0", "unit": "kg/h", "required": False, "step": "any"},
                {"name": "xF", "label": "Soluté dans l'alimentation xF", "unit": "-", "required": False, "step": "any"},
                {"name": "y0", "label": "Soluté dans le solvant entrant y0", "unit": "-", "required": False, "step": "any"},
                {"name": "xD", "label": "Composition raffinât cible xD", "unit": "-", "required": False, "step": "any"},
                {"name": "yK", "label": "Composition d'équilibre yK", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_extraction_liquid_liquid",
        },
        {
            "slug": "extraction-solide-liquide",
            "key": "extraction_solid_liquid",
            "name": "Extraction solide-liquide",
            "category": "Mass Transfer",
            "icon": "fas fa-seedling",
            "definition": "Extraction d'un soluté d'une matrice solide par un solvant.",
            "description": "Calcule les masses globales et le rendement d'extraction.",
            "applications": "Industries alimentaire, pharmaceutique et analytique.",
            "formulas": [
                "M = A + B + C",
                "L = BL + CL",
                "S = AS + BS + CS",
                "rendement = extracted_solute / initial_solute * 100",
            ],
            "fields": [
                {"name": "A", "label": "Masse A", "unit": "kg", "required": False, "step": "any"},
                {"name": "B", "label": "Masse B", "unit": "kg", "required": False, "step": "any"},
                {"name": "C", "label": "Masse C", "unit": "kg", "required": False, "step": "any"},
                {"name": "BL", "label": "Fraction B dans liquide", "unit": "kg", "required": False, "step": "any"},
                {"name": "CL", "label": "Fraction C dans liquide", "unit": "kg", "required": False, "step": "any"},
                {"name": "AS", "label": "Fraction A dans solide", "unit": "kg", "required": False, "step": "any"},
                {"name": "BS", "label": "Fraction B dans solide", "unit": "kg", "required": False, "step": "any"},
                {"name": "CS", "label": "Fraction C dans solide", "unit": "kg", "required": False, "step": "any"},
                {"name": "extracted_solute", "label": "Soluté extrait", "unit": "kg", "required": False, "step": "any"},
                {"name": "initial_solute", "label": "Soluté initial", "unit": "kg", "required": False, "step": "any"},
            ],
            "handler": "_calculate_extraction_solid_liquid",
        },
        {
            "slug": "evaporation",
            "key": "evaporation",
            "name": "Évaporation",
            "category": "Heat Transfer",
            "icon": "fas fa-cloud",
            "definition": "Concentration d'une solution par vaporisation du solvant.",
            "description": "Calcule les débits liquide et vapeur ainsi que le bilan énergétique global.",
            "applications": "Concentration de sirops, jus, lait et solutions chimiques.",
            "formulas": [
                "A = B + V",
                "XA * A = XB * B",
                "B = XA * A / XB",
                "V = A - B",
                "A * hA + Phi = V * HV + B * hB + losses",
            ],
            "fields": [
                {"name": "A_feed", "label": "Débit alimentation A", "unit": "kg/h", "required": False, "step": "any"},
                {"name": "XA", "label": "Fraction massique soluté XA", "unit": "-", "required": False, "step": "any"},
                {"name": "XB", "label": "Fraction massique soluté XB", "unit": "-", "required": False, "step": "any"},
                {"name": "hA", "label": "Enthalpie alimentation hA", "unit": "kJ/kg", "required": False, "step": "any"},
                {"name": "Phi", "label": "Apport thermique Phi", "unit": "kJ/h", "required": False, "step": "any"},
                {"name": "HV", "label": "Enthalpie vapeur HV", "unit": "kJ/kg", "required": False, "step": "any"},
                {"name": "hB", "label": "Enthalpie concentrat hB", "unit": "kJ/kg", "required": False, "step": "any"},
                {"name": "losses", "label": "Pertes thermiques", "unit": "kJ/h", "required": False, "step": "any"},
            ],
            "handler": "_calculate_evaporation",
        },
        {
            "slug": "sechage",
            "key": "drying",
            "name": "Séchage",
            "category": "Heat Transfer",
            "icon": "fas fa-wind",
            "definition": "Élimination de l'humidité d'un solide par apport de chaleur et transfert de matière.",
            "description": "Calcule l'eau retirée, la chaleur de séchage, la chaleur convective et un temps de séchage indicatif.",
            "applications": "Séchoirs à air chaud, séchage de produits chimiques, aliments, bois et textiles.",
            "formulas": [
                "W = Ms * (Xi - Xf)",
                "Q = W * Lv",
                "Qconv = h * S * (Ta - Tp)",
                "t = Q / (h * S * (Ta - Tp))",
            ],
            "fields": [
                {"name": "Ms", "label": "Masse de solide sec Ms", "unit": "kg", "required": False, "step": "any"},
                {"name": "Xi", "label": "Humidité initiale Xi", "unit": "kg eau/kg solide sec", "required": False, "step": "any"},
                {"name": "Xf", "label": "Humidité finale Xf", "unit": "kg eau/kg solide sec", "required": False, "step": "any"},
                {"name": "Lv", "label": "Chaleur latente Lv", "unit": "kJ/kg", "required": False, "step": "any"},
                {"name": "h", "label": "Coefficient convectif h", "unit": "kW/m².K ou kJ/s.m².K", "required": False, "step": "any"},
                {"name": "S", "label": "Surface d'échange S", "unit": "m²", "required": False, "step": "any"},
                {"name": "Ta", "label": "Température air Ta", "unit": "°C", "required": False, "step": "any"},
                {"name": "Tp", "label": "Température produit Tp", "unit": "°C", "required": False, "step": "any"},
            ],
            "handler": "_calculate_drying",
        },
        {
            "slug": "psychrometric",
            "key": "psychrometric_calculator",
            "name": "Calculateur Psychrométrique",
            "category": "Heat Transfer",
            "icon": "fas fa-temperature-three-quarters",
            "definition": "Détermine numériquement l'état complet de l'air humide à partir de deux propriétés connues.",
            "description": "Remplace l'utilisation manuelle du diagramme psychrométrique par une résolution numérique robuste.",
            "applications": "Dimensionnement de séchoirs, humidification, conditionnement d'air.",
            "formulas": [
                "Psat(T) = 0.61078 * exp((17.27 * T) / (T + 237.3))",
                "Pv = HR / 100 * Psat(Ts)",
                "w = 0.62198 * Pv / (P - Pv)",
                "h = 1.006 * Ts + w * (2501 + 1.86 * Ts)",
                "Vs = 0.287042 * (Ts + 273.15) * (1 + 1.607858 * w) / P",
                "rho = (1 + w) / Vs",
                "gamma = ln(Pv / 0.61078) ; Tr = (237.3 * gamma) / (17.27 - gamma)",
            ],
            "fields": [
                {
                    "name": "param1_type",
                    "label": "Paramètre 1",
                    "type": "select",
                    "required": True,
                    "options": PsychrometricService.get_parameter_options(),
                },
                {"name": "param1_value", "label": "Valeur 1", "unit": "", "required": True, "step": "any"},
                {
                    "name": "param2_type",
                    "label": "Paramètre 2",
                    "type": "select",
                    "required": True,
                    "options": PsychrometricService.get_parameter_options(),
                },
                {"name": "param2_value", "label": "Valeur 2", "unit": "", "required": True, "step": "any"},
                {"name": "P", "label": "Pression totale P", "unit": "kPa", "required": False, "step": "any", "default": "101.325"},
            ],
            "handler": "_calculate_psychrometric",
        },
        {
            "slug": "cristallisation",
            "key": "crystallization",
            "name": "Cristallisation",
            "category": "Separation",
            "icon": "fas fa-gem",
            "definition": "Formation de cristaux à partir d'une solution sursaturée.",
            "description": "Calcule la sursaturation ainsi que les taux de nucléation primaire et secondaire.",
            "applications": "Sucres, sels, API, chimie fine.",
            "formulas": [
                "deltaC = C0 - Ce",
                "Jp = Kp * deltaC^n",
                "Js = Ks * epsilon^h * deltaC^i * MT^j",
            ],
            "fields": [
                {"name": "C0", "label": "Concentration initiale C0", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "Ce", "label": "Concentration à l'équilibre Ce", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "Kp", "label": "Constante de nucléation primaire Kp", "unit": "-", "required": False, "step": "any"},
                {"name": "n_exp", "label": "Exposant n", "unit": "-", "required": False, "step": "any"},
                {"name": "Ks", "label": "Constante de nucléation secondaire Ks", "unit": "-", "required": False, "step": "any"},
                {"name": "epsilon", "label": "Dissipation epsilon", "unit": "-", "required": False, "step": "any"},
                {"name": "h_exp", "label": "Exposant h", "unit": "-", "required": False, "step": "any"},
                {"name": "i_exp", "label": "Exposant i", "unit": "-", "required": False, "step": "any"},
                {"name": "MT", "label": "Masse de cristaux MT", "unit": "kg", "required": False, "step": "any"},
                {"name": "j_exp", "label": "Exposant j", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_crystallization",
        },
        {
            "slug": "reacteurs-chimiques",
            "key": "chemical_reactors",
            "name": "Réacteurs chimiques",
            "category": "Reaction",
            "icon": "fas fa-atom",
            "definition": "Dimensionnement simplifié des réacteurs batch, CSTR et PFR.",
            "description": "Calcule les conversions et estime les volumes de CSTR/PFR avec une vitesse de réaction constante.",
            "applications": "Synthèse, procédés continus, analyses préliminaires.",
            "formulas": [
                "XA = (NA0 - NA) / NA0",
                "XA = (FA0 - FA) / FA0",
                "V_CSTR = FA0 * XA / (-rA)",
                "V_PFR ≈ FA0 * XA / (-rA) si le taux est constant",
            ],
            "fields": [
                {"name": "NA0", "label": "Quantité initiale batch NA0", "unit": "mol", "required": False, "step": "any"},
                {"name": "NA", "label": "Quantité finale batch NA", "unit": "mol", "required": False, "step": "any"},
                {"name": "FA0", "label": "Débit molaire entrant FA0", "unit": "mol/s", "required": False, "step": "any"},
                {"name": "FA", "label": "Débit molaire sortant FA", "unit": "mol/s", "required": False, "step": "any"},
                {"name": "minus_rA", "label": "Vitesse positive (-rA)", "unit": "mol/m³.s", "required": False, "step": "any"},
            ],
            "handler": "_calculate_chemical_reactors",
        },
        {
            "slug": "adsorption",
            "key": "adsorption",
            "name": "Adsorption",
            "category": "Mass Transfer",
            "icon": "fas fa-magnet",
            "definition": "Fixation de molécules à la surface d'un solide adsorbant.",
            "description": "Calcule les isothermes de Langmuir et Freundlich ainsi que la masse d'adsorbant nécessaire.",
            "applications": "Traitement d'eau, purification d'air, chromatographie.",
            "formulas": [
                "q = qmax * K * C / (1 + K * C)",
                "q = Kf * C^(1 / n)",
                "m = amount_adsorbed / q",
            ],
            "fields": [
                {"name": "qmax", "label": "Capacité maximale qmax", "unit": "mol/kg", "required": False, "step": "any"},
                {"name": "K", "label": "Constante Langmuir K", "unit": "L/mol", "required": False, "step": "any"},
                {"name": "C", "label": "Concentration C", "unit": "mol/L", "required": False, "step": "any"},
                {"name": "Kf", "label": "Constante Freundlich Kf", "unit": "-", "required": False, "step": "any"},
                {"name": "n", "label": "Exposant Freundlich n", "unit": "-", "required": False, "step": "any"},
                {"name": "amount_adsorbed", "label": "Quantité à adsorber", "unit": "mol", "required": False, "step": "any"},
            ],
            "handler": "_calculate_adsorption",
        },
        {
            "slug": "absorption",
            "key": "absorption_gas_liquid",
            "name": "Absorption gaz-liquide",
            "category": "Mass Transfer",
            "icon": "fas fa-arrow-down-wide-short",
            "definition": "Transfert d'un gaz soluble vers une phase liquide.",
            "description": "Applique la loi de Henry, le taux d'abattement et la quantité de soluté absorbée.",
            "applications": "CO2, désulfuration, lavage de gaz.",
            "formulas": [
                "C = H * P",
                "eta = (yin - yout) / yin * 100",
                "n = G * (yin - yout)",
            ],
            "fields": [
                {"name": "H", "label": "Constante de Henry H", "unit": "mol/(L.atm) ou cohérent", "required": False, "step": "any"},
                {"name": "P_partial", "label": "Pression partielle du soluté", "unit": "atm", "required": False, "step": "any"},
                {"name": "yin", "label": "Fraction gaz entrant yin", "unit": "-", "required": False, "step": "any"},
                {"name": "yout", "label": "Fraction gaz sortant yout", "unit": "-", "required": False, "step": "any"},
                {"name": "G", "label": "Débit molaire gaz G", "unit": "mol/s", "required": False, "step": "any"},
            ],
            "handler": "_calculate_absorption",
        },
        {
            "slug": "membranes",
            "key": "membrane_separation",
            "name": "Membranes",
            "category": "Separation",
            "icon": "fas fa-border-all",
            "definition": "Séparation par perméabilité sélective d'une membrane.",
            "description": "Calcule le flux, le débit de perméat et la sélectivité.",
            "applications": "RO, UF, NF, séparation de gaz.",
            "formulas": [
                "J = Pm * (deltaP / e)",
                "Qp = J * A",
                "alpha = PA / PB",
            ],
            "fields": [
                {"name": "Pm", "label": "Perméabilité membrane Pm", "unit": "-", "required": False, "step": "any"},
                {"name": "deltaP", "label": "Différence de pression deltaP", "unit": "Pa", "required": False, "step": "any"},
                {"name": "e", "label": "Épaisseur e", "unit": "m", "required": False, "step": "any"},
                {"name": "A", "label": "Surface membranaire A", "unit": "m²", "required": False, "step": "any"},
                {"name": "PA", "label": "Perméabilité composant A", "unit": "-", "required": False, "step": "any"},
                {"name": "PB", "label": "Perméabilité composant B", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_membranes",
        },
        {
            "slug": "echange-thermique",
            "key": "heat_exchange",
            "name": "Échange thermique",
            "category": "Heat Transfer",
            "icon": "fas fa-temperature-arrow-up",
            "definition": "Transfert de chaleur entre fluides ou surfaces.",
            "description": "Calcule la charge thermique, la différence de température logarithmique moyenne et la surface requise.",
            "applications": "Échangeurs, condenseurs, évaporateurs, récupérateurs.",
            "formulas": [
                "Q = m * Cp * deltaT",
                "deltaTlm = (deltaT1 - deltaT2) / ln(deltaT1 / deltaT2)",
                "A = Q / (U * deltaTlm)",
            ],
            "fields": [
                {"name": "m", "label": "Débit massique m", "unit": "kg/s", "required": False, "step": "any"},
                {"name": "Cp", "label": "Capacité thermique Cp", "unit": "kJ/kg.K", "required": False, "step": "any"},
                {"name": "deltaT", "label": "Écart de température deltaT", "unit": "K", "required": False, "step": "any"},
                {"name": "deltaT1", "label": "deltaT1", "unit": "K", "required": False, "step": "any"},
                {"name": "deltaT2", "label": "deltaT2", "unit": "K", "required": False, "step": "any"},
                {"name": "U", "label": "Coefficient global U", "unit": "W/m².K", "required": False, "step": "any"},
            ],
            "handler": "_calculate_heat_exchange",
        },
        {
            "slug": "melange-agitation",
            "key": "mixing_agitation",
            "name": "Mélange / agitation",
            "category": "Mechanical",
            "icon": "fas fa-blender",
            "definition": "Homogénéisation d'un fluide ou d'une suspension par agitation.",
            "description": "Calcule le Reynolds d'agitation et la puissance consommée.",
            "applications": "Réacteurs agités, suspensions, émulsions, mélanges liquides.",
            "formulas": [
                "Re = rho * N * D^2 / mu",
                "P = Np * rho * N^3 * D^5",
            ],
            "fields": [
                {"name": "rho", "label": "Densité rho", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "N", "label": "Vitesse agitateur N", "unit": "s^-1", "required": False, "step": "any"},
                {"name": "D", "label": "Diamètre hélice D", "unit": "m", "required": False, "step": "any"},
                {"name": "mu", "label": "Viscosité mu", "unit": "Pa.s", "required": False, "step": "any"},
                {"name": "Np", "label": "Nombre de puissance Np", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_mixing_agitation",
        },
        {
            "slug": "broyage",
            "key": "size_reduction",
            "name": "Broyage",
            "category": "Mechanical",
            "icon": "fas fa-hammer",
            "definition": "Réduction de taille des particules solides.",
            "description": "Calcule l'énergie de Bond et le rapport de réduction granulométrique.",
            "applications": "Préparation de minerais, poudres, échantillons.",
            "formulas": [
                "E = Wi * (10 / sqrt(P80) - 10 / sqrt(F80))",
                "R = Dinitial / Dfinal",
            ],
            "fields": [
                {"name": "Wi", "label": "Indice de Bond Wi", "unit": "kWh/t", "required": False, "step": "any"},
                {"name": "P80", "label": "P80", "unit": "µm", "required": False, "step": "any"},
                {"name": "F80", "label": "F80", "unit": "µm", "required": False, "step": "any"},
                {"name": "Dinitial", "label": "Diamètre initial", "unit": "mm", "required": False, "step": "any"},
                {"name": "Dfinal", "label": "Diamètre final", "unit": "mm", "required": False, "step": "any"},
            ],
            "handler": "_calculate_broyage",
        },
        {
            "slug": "tamisage",
            "key": "screening",
            "name": "Tamisage",
            "category": "Mechanical",
            "icon": "fas fa-grip-lines",
            "definition": "Analyse granulométrique par rétention sur tamis successifs.",
            "description": "Calcule les pourcentages retenus, les cumuls et estime d50 par interpolation.",
            "applications": "Contrôle qualité, classification de poudres, minéraux, céréales.",
            "formulas": [
                "percent retained = retained_i / total * 100",
                "cumulative retained = somme(percent retained)",
                "cumulative passing = 100 - cumulative retained",
                "d50 par interpolation linéaire",
            ],
            "fields": [
                {
                    "name": "sieve_sizes",
                    "label": "Tailles de tamis",
                    "unit": "mm",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "Exemple: 4; 2; 1; 0.5; 0.25",
                    "help": "Utilisez ';' ou des retours à la ligne entre les valeurs.",
                },
                {
                    "name": "retained_values",
                    "label": "Masses ou pourcentages retenus",
                    "unit": "g ou %",
                    "type": "textarea",
                    "required": True,
                    "placeholder": "Exemple: 5; 18; 35; 28; 14",
                    "help": "Même nombre de valeurs que les tailles de tamis.",
                },
            ],
            "handler": "_calculate_tamisage",
        },
        {
            "slug": "fluidisation",
            "key": "fluidization",
            "name": "Fluidisation",
            "category": "Mechanical",
            "icon": "fas fa-bubbles",
            "definition": "Mise en suspension d'un lit de particules par un fluide ascendant.",
            "description": "Calcule la vitesse superficielle, vérifie la fluidisation minimale et estime la perte de charge.",
            "applications": "Lits fluidisés, séchage, craquage catalytique.",
            "formulas": [
                "u = Q / A",
                "u >= umf",
                "deltaP = (rho_s - rho_f) * (1 - epsilon) * g * H",
            ],
            "fields": [
                {"name": "Q", "label": "Débit Q", "unit": "m³/s", "required": False, "step": "any"},
                {"name": "A", "label": "Section A", "unit": "m²", "required": False, "step": "any"},
                {"name": "umf", "label": "Vitesse minimale umf", "unit": "m/s", "required": False, "step": "any"},
                {"name": "rho_s", "label": "Densité solide rho_s", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "rho_f", "label": "Densité fluide rho_f", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "epsilon", "label": "Porosité epsilon", "unit": "-", "required": False, "step": "any"},
                {"name": "H", "label": "Hauteur du lit H", "unit": "m", "required": False, "step": "any"},
            ],
            "handler": "_calculate_fluidisation",
        },
        {
            "slug": "transport-fluides",
            "key": "fluid_flow",
            "name": "Transport des fluides",
            "category": "Mechanical",
            "icon": "fas fa-water",
            "definition": "Écoulement de fluides dans des conduites.",
            "description": "Calcule la section, le débit, le Reynolds et la perte de charge Darcy-Weisbach.",
            "applications": "Hydraulique, tuyauteries, réseaux industriels.",
            "formulas": [
                "Re = rho * v * D / mu",
                "A = pi * D^2 / 4",
                "Q = v * A",
                "deltaP = f * (L / D) * (rho * v^2 / 2)",
            ],
            "fields": [
                {"name": "rho", "label": "Densité rho", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "v", "label": "Vitesse v", "unit": "m/s", "required": False, "step": "any"},
                {"name": "D", "label": "Diamètre D", "unit": "m", "required": False, "step": "any"},
                {"name": "mu", "label": "Viscosité mu", "unit": "Pa.s", "required": False, "step": "any"},
                {"name": "L", "label": "Longueur L", "unit": "m", "required": False, "step": "any"},
                {"name": "f", "label": "Facteur de friction f", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_transport_fluides",
        },
        {
            "slug": "pompes",
            "key": "pumping",
            "name": "Pompes",
            "category": "Mechanical",
            "icon": "fas fa-fan",
            "definition": "Machines apportant de l'énergie mécanique à un fluide.",
            "description": "Calcule la puissance hydraulique puis la puissance à l'arbre avec rendement.",
            "applications": "Circulation, transfert, pressurisation de fluides.",
            "formulas": [
                "Ph = rho * g * Q * H",
                "P = Ph / eta",
            ],
            "fields": [
                {"name": "rho", "label": "Densité rho", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "Q", "label": "Débit Q", "unit": "m³/s", "required": False, "step": "any"},
                {"name": "H", "label": "Hauteur manométrique H", "unit": "m", "required": False, "step": "any"},
                {"name": "eta", "label": "Rendement eta", "unit": "fraction", "required": False, "step": "any"},
            ],
            "handler": "_calculate_pompes",
        },
        {
            "slug": "cyclones",
            "key": "cyclones",
            "name": "Cyclones",
            "category": "Separation",
            "icon": "fas fa-tornado",
            "definition": "Séparation gaz-solide par effet centrifuge.",
            "description": "Calcule la vitesse d'entrée et la perte de charge à partir d'un coefficient global.",
            "applications": "Dépoussiérage, pré-séparation, protection de filtres.",
            "formulas": [
                "v = Q / A",
                "deltaP = K * (rho * v^2 / 2)",
            ],
            "fields": [
                {"name": "Q", "label": "Débit Q", "unit": "m³/s", "required": False, "step": "any"},
                {"name": "A", "label": "Section d'entrée A", "unit": "m²", "required": False, "step": "any"},
                {"name": "rho", "label": "Densité du gaz rho", "unit": "kg/m³", "required": False, "step": "any"},
                {"name": "K", "label": "Coefficient de perte K", "unit": "-", "required": False, "step": "any"},
            ],
            "handler": "_calculate_cyclones",
        },
        {
            "slug": "humidification",
            "key": "humidification_dehumidification",
            "name": "Humidification / déshumidification",
            "category": "Mass Transfer",
            "icon": "fas fa-cloud-rain",
            "definition": "Ajout ou retrait d'eau dans un courant d'air humide.",
            "description": "Calcule l'eau ajoutée ou retirée et la charge thermique associée.",
            "applications": "Tours de refroidissement, HVAC, séchage, confort.",
            "formulas": [
                "m_water = m_dry_air * (Yout - Yin)",
                "Q = m_dry_air * (hout - hin)",
            ],
            "fields": [
                {"name": "m_dry_air", "label": "Débit d'air sec", "unit": "kg/s", "required": False, "step": "any"},
                {"name": "Yin", "label": "Humidité absolue entrée Yin", "unit": "kg/kg air sec", "required": False, "step": "any"},
                {"name": "Yout", "label": "Humidité absolue sortie Yout", "unit": "kg/kg air sec", "required": False, "step": "any"},
                {"name": "hin", "label": "Enthalpie entrée hin", "unit": "kJ/kg air sec", "required": False, "step": "any"},
                {"name": "hout", "label": "Enthalpie sortie hout", "unit": "kJ/kg air sec", "required": False, "step": "any"},
            ],
            "handler": "_calculate_humidification",
        },
    ]

    OPERATION_MAP = {item["slug"]: item for item in OPERATION_DEFINITIONS}

    @classmethod
    def get_operations(cls) -> List[Dict[str, Any]]:
        """Return all operations with template-friendly metadata."""
        operations = []
        for item in cls.OPERATION_DEFINITIONS:
            operation = deepcopy(item)
            category = operation["category"]
            operation.update(cls.CATEGORY_META.get(category, {}))
            operations.append(operation)
        return operations

    @classmethod
    def get_operation(cls, slug: str) -> Optional[Dict[str, Any]]:
        """Return one operation by slug."""
        operation = cls.OPERATION_MAP.get(slug)
        if not operation:
            return None
        enriched = deepcopy(operation)
        enriched.update(cls.CATEGORY_META.get(enriched["category"], {}))
        return enriched

    @classmethod
    def calculate_operation(cls, slug: str, form_data: Dict[str, Any]) -> Dict[str, Any]:
        """Dispatch calculation to the requested operation handler."""
        operation = cls.get_operation(slug)
        if not operation:
            return {"error": "Opération inconnue."}

        handler = getattr(cls, operation["handler"])
        return handler(operation, form_data)

    @staticmethod
    def _normalize_number(value: Any) -> Optional[float]:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        text = str(value).strip()
        if not text:
            return None
        text = text.replace(" ", "")
        if text.count(",") == 1 and "." not in text:
            text = text.replace(",", ".")
        return float(text)

    @classmethod
    def _get_value(
        cls,
        values: Dict[str, Any],
        key: str,
        *,
        label: str,
        required: bool = False,
        positive: bool = False,
        nonnegative: bool = False,
        minimum: Optional[float] = None,
        maximum: Optional[float] = None,
    ) -> Optional[float]:
        raw = values.get(key)
        if raw is None or str(raw).strip() == "":
            if required:
                raise ValueError(f"Le champ '{label}' est requis.")
            return None

        number = cls._normalize_number(raw)
        if positive and number <= 0:
            raise ValueError(f"Le champ '{label}' doit être strictement positif.")
        if nonnegative and number < 0:
            raise ValueError(f"Le champ '{label}' ne peut pas être négatif.")
        if minimum is not None and number < minimum:
            raise ValueError(f"Le champ '{label}' doit être >= {minimum}.")
        if maximum is not None and number > maximum:
            raise ValueError(f"Le champ '{label}' doit être <= {maximum}.")
        return number

    @staticmethod
    def _fmt(value: float, digits: int = 6) -> str:
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")

    @classmethod
    def _collect_inputs(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> List[Dict[str, str]]:
        inputs = []
        for field in operation["fields"]:
            raw = form_data.get(field["name"])
            if raw is None or str(raw).strip() == "":
                continue
            inputs.append(
                {
                    "label": field["label"],
                    "value": str(raw).strip(),
                    "unit": field.get("unit", ""),
                }
            )
        return inputs

    @staticmethod
    def _result_item(label: str, value: float, unit: str, formula: str = "") -> Dict[str, str]:
        formatted = UnitOperationsService._fmt(value)
        return {"label": label, "value": formatted, "unit": unit, "formula": formula}

    @classmethod
    def _build_success(
        cls,
        operation: Dict[str, Any],
        form_data: Dict[str, Any],
        results: List[Dict[str, str]],
        steps: List[str],
        warnings: Optional[List[str]] = None,
        formulas_used: Optional[List[str]] = None,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        payload = {
            "success": True,
            "inputs": cls._collect_inputs(operation, form_data),
            "results": results,
            "steps": steps,
            "warnings": warnings or [],
            "formulas_used": formulas_used or operation["formulas"],
        }
        if extra:
            payload.update(extra)
        return payload

    @staticmethod
    def _build_error(message: str) -> Dict[str, Any]:
        return {"error": message}

    @staticmethod
    def _ensure_any(results: List[Dict[str, str]]) -> None:
        if not results:
            raise ValueError("Données insuffisantes pour calculer un résultat. Remplissez au moins une combinaison valide.")

    @classmethod
    def _parse_series(cls, raw_value: str, label: str) -> List[float]:
        text = (raw_value or "").strip()
        if not text:
            raise ValueError(f"Le champ '{label}' est requis.")
        separator_pattern = r"[;\n\r]+"
        if not re.search(separator_pattern, text):
            tokens = [part.strip() for part in text.split(",") if part.strip()]
        else:
            tokens = [part.strip() for part in re.split(separator_pattern, text) if part.strip()]
        if not tokens:
            raise ValueError(f"Le champ '{label}' ne contient aucune valeur exploitable.")
        values = []
        for token in tokens:
            token = token.replace(" ", "")
            if token.count(",") == 1 and "." not in token:
                token = token.replace(",", ".")
            values.append(float(token))
        return values

    @staticmethod
    def _flow_regime(reynolds: float) -> str:
        if reynolds < 2100:
            return "laminaire"
        if reynolds < 4000:
            return "transition"
        return "turbulent"

    @classmethod
    def _calculate_decantation(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rho_l = cls._get_value(form_data, "rho_l", label="Densité du fluide", positive=True)
            rho_s = cls._get_value(form_data, "rho_s", label="Densité du solide", positive=True)
            mu = cls._get_value(form_data, "mu", label="Viscosité dynamique", positive=True)
            d = cls._get_value(form_data, "d", label="Diamètre de particule", positive=True)
            v = cls._get_value(form_data, "v", label="Vitesse observée", nonnegative=True)
            q = cls._get_value(form_data, "Q", label="Débit volumique", positive=True)
            vc = cls._get_value(form_data, "vc", label="Vitesse critique", positive=True)
            surface = cls._get_value(form_data, "S", label="Surface", positive=True)
            height = cls._get_value(form_data, "H", label="Hauteur", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            warnings: List[str] = []

            if all(value is not None for value in [rho_l, v, d, mu]):
                reynolds = rho_l * v * d / mu
                results.append(cls._result_item("Nombre de Reynolds", reynolds, "-", "Re = rho_l * v * d / mu"))
                steps.append(f"Re = {cls._fmt(rho_l)} x {cls._fmt(v)} x {cls._fmt(d)} / {cls._fmt(mu)} = {cls._fmt(reynolds)}")

            stokes_velocity = None
            if all(value is not None for value in [rho_l, rho_s, mu, d]):
                stokes_velocity = GRAVITY * d ** 2 * (rho_s - rho_l) / (18 * mu)
                results.append(cls._result_item("Vitesse de Stokes", stokes_velocity, "m/s", "v = g * d^2 * (rho_s - rho_l) / (18 * mu)"))
                steps.append(
                    "v = 9.81 x d^2 x (rho_s - rho_l) / (18 x mu) = "
                    f"{cls._fmt(stokes_velocity)} m/s"
                )
                if stokes_velocity <= 0:
                    warnings.append("La vitesse de Stokes est nulle ou négative. Vérifiez les densités et la viscosité.")

            effective_vc = vc if vc is not None else stokes_velocity
            if q is not None and effective_vc is not None and effective_vc > 0:
                smin = q / effective_vc
                results.append(cls._result_item("Surface minimale", smin, "m²", "Smin = Q / vc"))
                steps.append(f"Smin = {cls._fmt(q)} / {cls._fmt(effective_vc)} = {cls._fmt(smin)} m²")
                if vc is None:
                    warnings.append("La vitesse critique n'était pas fournie. La vitesse de Stokes a été utilisée pour estimer Smin.")

            if all(value is not None for value in [surface, height, q]):
                tsej = surface * height / q
                results.append(cls._result_item("Temps de séjour", tsej, "s", "tsej = S * H / Q"))
                steps.append(f"tsej = {cls._fmt(surface)} x {cls._fmt(height)} / {cls._fmt(q)} = {cls._fmt(tsej)} s")

            if height is not None and effective_vc is not None and effective_vc > 0:
                tc = height / effective_vc
                results.append(cls._result_item("Temps de clarification", tc, "s", "tc = H / vc"))
                steps.append(f"tc = {cls._fmt(height)} / {cls._fmt(effective_vc)} = {cls._fmt(tc)} s")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps, warnings)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_centrifugation(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mass = cls._get_value(form_data, "m", label="Masse de particule", positive=True)
            rpm = cls._get_value(form_data, "N", label="Vitesse de rotation", required=True, positive=True)
            radius = cls._get_value(form_data, "r", label="Rayon", required=True, positive=True)
            vcl = cls._get_value(form_data, "vCL", label="Vitesse de Stokes classique", nonnegative=True)

            omega = 2 * math.pi * rpm / 60
            k_factor = omega ** 2 * radius / GRAVITY

            results = [
                cls._result_item("Vitesse angulaire", omega, "rad/s", "omega = 2 * pi * N / 60"),
                cls._result_item("Facteur de séparation", k_factor, "-", "K = omega^2 * r / g"),
            ]
            steps = [
                f"omega = 2 x pi x {cls._fmt(rpm)} / 60 = {cls._fmt(omega)} rad/s",
                f"K = {cls._fmt(omega)}^2 x {cls._fmt(radius)} / 9.81 = {cls._fmt(k_factor)}",
            ]

            if mass is not None:
                force = mass * omega ** 2 * radius
                results.append(cls._result_item("Force centrifuge", force, "N", "Fc = m * omega^2 * r"))
                steps.append(f"Fc = {cls._fmt(mass)} x {cls._fmt(omega)}^2 x {cls._fmt(radius)} = {cls._fmt(force)} N")

            if vcl is not None:
                vsc = vcl * k_factor
                results.append(cls._result_item("Vitesse centrifuge équivalente", vsc, "m/s", "vSC = vCL * K"))
                steps.append(f"vSC = {cls._fmt(vcl)} x {cls._fmt(k_factor)} = {cls._fmt(vsc)} m/s")

            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_filtration(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mu = cls._get_value(form_data, "mu", label="Viscosité", positive=True)
            velocity = cls._get_value(form_data, "v", label="Vitesse de filtration", nonnegative=True)
            e_g = cls._get_value(form_data, "eG", label="Résistance gâteau", nonnegative=True)
            e_s = cls._get_value(form_data, "eS", label="Résistance support", nonnegative=True)
            beta0 = cls._get_value(form_data, "beta0", label="Perméabilité beta0", positive=True)
            a_coef = cls._get_value(form_data, "A_coef", label="Coefficient A", nonnegative=True)
            b_coef = cls._get_value(form_data, "B_coef", label="Coefficient B")
            volume = cls._get_value(form_data, "V", label="Volume filtré", nonnegative=True)
            time_value = cls._get_value(form_data, "t", label="Temps", nonnegative=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if all(value is not None for value in [mu, velocity, e_g, e_s, beta0]):
                delta_p = mu * velocity * (e_g + e_s) / beta0
                results.append(cls._result_item("Perte de charge Darcy", delta_p, "Pa", "deltaP = mu * v * (eG + eS) / beta0"))
                steps.append(
                    "deltaP = mu x v x (eG + eS) / beta0 = "
                    f"{cls._fmt(delta_p)} Pa"
                )

            if all(value is not None for value in [a_coef, b_coef, volume]):
                t_calc = a_coef * volume ** 2 + b_coef * volume
                results.append(cls._result_item("Temps à pression constante", t_calc, "s", "t = A * V^2 + B * V"))
                steps.append(
                    f"t = {cls._fmt(a_coef)} x {cls._fmt(volume)}^2 + {cls._fmt(b_coef)} x {cls._fmt(volume)} = {cls._fmt(t_calc)} s"
                )

            if all(value is not None for value in [a_coef, b_coef, time_value]):
                delta_p_cf = a_coef * time_value + b_coef
                results.append(cls._result_item("Perte de charge à débit constant", delta_p_cf, "Pa", "deltaP = A * t + B"))
                steps.append(
                    f"deltaP = {cls._fmt(a_coef)} x {cls._fmt(time_value)} + {cls._fmt(b_coef)} = {cls._fmt(delta_p_cf)} Pa"
                )

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_distillation(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            alpha = cls._get_value(form_data, "alpha", label="Volatilité relative", positive=True)
            x = cls._get_value(form_data, "x", label="Fraction molaire liquide x", minimum=0, maximum=1)
            reflux = cls._get_value(form_data, "R", label="Taux de reflux R", nonnegative=True)
            x_d = cls._get_value(form_data, "xD", label="Composition distillat xD", minimum=0, maximum=1)
            y_f = cls._get_value(form_data, "yF", label="Composition vapeur alimentation yF", minimum=0, maximum=1)
            x_f = cls._get_value(form_data, "xF", label="Composition alimentation xF", minimum=0, maximum=1)
            feed = cls._get_value(form_data, "F", label="Débit alimentation F", positive=True)
            distillate = cls._get_value(form_data, "D", label="Débit distillat D", nonnegative=True)
            residue = cls._get_value(form_data, "W", label="Débit résidu W", nonnegative=True)
            x_w = cls._get_value(form_data, "xW", label="Composition résidu xW", minimum=0, maximum=1)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            warnings: List[str] = []

            if alpha is not None and x is not None:
                y_eq = alpha * x / (1 + (alpha - 1) * x)
                results.append(cls._result_item("Équilibre vapeur y", y_eq, "-", "y = alpha * x / (1 + (alpha - 1) * x)"))
                steps.append(f"y = {cls._fmt(alpha)} x {cls._fmt(x)} / (1 + ({cls._fmt(alpha)} - 1) x {cls._fmt(x)}) = {cls._fmt(y_eq)}")

            if all(value is not None for value in [reflux, x, x_d]):
                y_rect = reflux / (reflux + 1) * x + x_d / (reflux + 1)
                results.append(cls._result_item("Droite d'enrichissement y", y_rect, "-", "y = R/(R+1) * x + xD/(R+1)"))
                steps.append(f"y = {cls._fmt(reflux)}/({cls._fmt(reflux)}+1) x {cls._fmt(x)} + {cls._fmt(x_d)}/({cls._fmt(reflux)}+1) = {cls._fmt(y_rect)}")

            if all(value is not None for value in [x_d, y_f, x_f]):
                denominator = y_f - x_f
                if denominator == 0:
                    raise ValueError("Impossible de calculer Rmin car yF - xF = 0.")
                rmin = (x_d - y_f) / denominator
                results.append(cls._result_item("Reflux minimum Rmin", rmin, "-", "Rmin = (xD - yF) / (yF - xF)"))
                steps.append(f"Rmin = ({cls._fmt(x_d)} - {cls._fmt(y_f)}) / ({cls._fmt(y_f)} - {cls._fmt(x_f)}) = {cls._fmt(rmin)}")

            if feed is not None and distillate is not None and residue is None:
                residue = feed - distillate
                results.append(cls._result_item("Débit résidu W", residue, "kmol/h", "W = F - D"))
                steps.append(f"W = {cls._fmt(feed)} - {cls._fmt(distillate)} = {cls._fmt(residue)} kmol/h")

            if feed is not None and residue is not None and distillate is None:
                distillate = feed - residue
                results.append(cls._result_item("Débit distillat D", distillate, "kmol/h", "D = F - W"))
                steps.append(f"D = {cls._fmt(feed)} - {cls._fmt(residue)} = {cls._fmt(distillate)} kmol/h")

            if all(value is not None for value in [feed, x_f, distillate, x_d, x_w]):
                if x_w == 0:
                    raise ValueError("La composition xW ne peut pas être nulle pour le bilan matière.")
                residue_from_component = (feed * x_f - distillate * x_d) / x_w
                results.append(cls._result_item("Résidu via bilan composant", residue_from_component, "kmol/h", "W = (F*xF - D*xD) / xW"))
                steps.append(
                    f"W = ({cls._fmt(feed)} x {cls._fmt(x_f)} - {cls._fmt(distillate)} x {cls._fmt(x_d)}) / {cls._fmt(x_w)} = {cls._fmt(residue_from_component)} kmol/h"
                )
                if residue is not None and abs(residue - residue_from_component) > 1e-6:
                    warnings.append("Le débit W fourni n'est pas cohérent avec le bilan composant calculé.")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps, warnings)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_extraction_liquid_liquid(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            feed = cls._get_value(form_data, "F", label="Débit alimentation F", positive=True)
            solvent = cls._get_value(form_data, "S0", label="Débit solvant S0", positive=True)
            x_f = cls._get_value(form_data, "xF", label="xF", minimum=0)
            y0 = cls._get_value(form_data, "y0", label="y0", minimum=0)
            x_d = cls._get_value(form_data, "xD", label="xD", minimum=0)
            y_k = cls._get_value(form_data, "yK", label="yK", minimum=0)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if feed is not None and solvent is not None:
                m1 = feed + solvent
                results.append(cls._result_item("Débit total M1", m1, "kg/h", "M1 = F + S0"))
                steps.append(f"M1 = {cls._fmt(feed)} + {cls._fmt(solvent)} = {cls._fmt(m1)} kg/h")
                if x_f is not None and y0 is not None:
                    x_m1 = (feed * x_f + solvent * y0) / (feed + solvent)
                    results.append(cls._result_item("Composition du mélange xM1", x_m1, "-", "xM1 = (F*xF + S0*y0) / (F + S0)"))
                    steps.append(f"xM1 = ({cls._fmt(feed)} x {cls._fmt(x_f)} + {cls._fmt(solvent)} x {cls._fmt(y0)}) / ({cls._fmt(feed)} + {cls._fmt(solvent)}) = {cls._fmt(x_m1)}")

            if all(value is not None for value in [feed, x_f, x_d, y0]):
                denominator = x_d - y0
                if denominator == 0:
                    raise ValueError("Impossible de calculer S0min car xD - y0 = 0.")
                s0min = ((x_f - x_d) / denominator) * feed
                results.append(cls._result_item("Solvant minimum S0min", s0min, "kg/h", "S0min = ((xF - xD) / (xD - y0)) * F"))
                steps.append(f"S0min = (({cls._fmt(x_f)} - {cls._fmt(x_d)}) / ({cls._fmt(x_d)} - {cls._fmt(y0)})) x {cls._fmt(feed)} = {cls._fmt(s0min)} kg/h")

            if all(value is not None for value in [feed, x_f, y_k, y0]):
                denominator = y_k - y0
                if denominator == 0:
                    raise ValueError("Impossible de calculer S0max car yK - y0 = 0.")
                s0max = ((x_f - y_k) / denominator) * feed
                results.append(cls._result_item("Solvant maximum S0max", s0max, "kg/h", "S0max = ((xF - yK) / (yK - y0)) * F"))
                steps.append(f"S0max = (({cls._fmt(x_f)} - {cls._fmt(y_k)}) / ({cls._fmt(y_k)} - {cls._fmt(y0)})) x {cls._fmt(feed)} = {cls._fmt(s0max)} kg/h")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_extraction_solid_liquid(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            a_val = cls._get_value(form_data, "A", label="Masse A", nonnegative=True)
            b_val = cls._get_value(form_data, "B", label="Masse B", nonnegative=True)
            c_val = cls._get_value(form_data, "C", label="Masse C", nonnegative=True)
            bl = cls._get_value(form_data, "BL", label="BL", nonnegative=True)
            cl = cls._get_value(form_data, "CL", label="CL", nonnegative=True)
            a_s = cls._get_value(form_data, "AS", label="AS", nonnegative=True)
            b_s = cls._get_value(form_data, "BS", label="BS", nonnegative=True)
            c_s = cls._get_value(form_data, "CS", label="CS", nonnegative=True)
            extracted = cls._get_value(form_data, "extracted_solute", label="Soluté extrait", nonnegative=True)
            initial = cls._get_value(form_data, "initial_solute", label="Soluté initial", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if all(value is not None for value in [a_val, b_val, c_val]):
                total_mass = a_val + b_val + c_val
                results.append(cls._result_item("Masse totale M", total_mass, "kg", "M = A + B + C"))
                steps.append(f"M = {cls._fmt(a_val)} + {cls._fmt(b_val)} + {cls._fmt(c_val)} = {cls._fmt(total_mass)} kg")

            if bl is not None and cl is not None:
                liquid_mass = bl + cl
                results.append(cls._result_item("Masse liquide L", liquid_mass, "kg", "L = BL + CL"))
                steps.append(f"L = {cls._fmt(bl)} + {cls._fmt(cl)} = {cls._fmt(liquid_mass)} kg")

            if all(value is not None for value in [a_s, b_s, c_s]):
                solid_mass = a_s + b_s + c_s
                results.append(cls._result_item("Masse solide S", solid_mass, "kg", "S = AS + BS + CS"))
                steps.append(f"S = {cls._fmt(a_s)} + {cls._fmt(b_s)} + {cls._fmt(c_s)} = {cls._fmt(solid_mass)} kg")

            if extracted is not None and initial is not None:
                yield_value = extracted / initial * 100
                results.append(cls._result_item("Rendement d'extraction", yield_value, "%", "rendement = extracted_solute / initial_solute * 100"))
                steps.append(f"rendement = {cls._fmt(extracted)} / {cls._fmt(initial)} x 100 = {cls._fmt(yield_value)} %")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_evaporation(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            a_feed = cls._get_value(form_data, "A_feed", label="Débit alimentation A", positive=True)
            x_a = cls._get_value(form_data, "XA", label="XA", minimum=0, maximum=1)
            x_b = cls._get_value(form_data, "XB", label="XB", minimum=0, maximum=1)
            h_a = cls._get_value(form_data, "hA", label="hA")
            phi = cls._get_value(form_data, "Phi", label="Phi")
            h_v = cls._get_value(form_data, "HV", label="HV")
            h_b = cls._get_value(form_data, "hB", label="hB")
            losses = cls._get_value(form_data, "losses", label="Pertes")

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            concentrate = None
            vapor = None

            if all(value is not None for value in [a_feed, x_a, x_b]):
                if x_b == 0:
                    raise ValueError("XB ne peut pas être nul.")
                concentrate = x_a * a_feed / x_b
                vapor = a_feed - concentrate
                results.append(cls._result_item("Débit concentrat B", concentrate, "kg/h", "B = XA * A / XB"))
                results.append(cls._result_item("Débit vapeur V", vapor, "kg/h", "V = A - B"))
                steps.append(f"B = {cls._fmt(x_a)} x {cls._fmt(a_feed)} / {cls._fmt(x_b)} = {cls._fmt(concentrate)} kg/h")
                steps.append(f"V = {cls._fmt(a_feed)} - {cls._fmt(concentrate)} = {cls._fmt(vapor)} kg/h")

            if all(value is not None for value in [a_feed, h_a, phi, h_v, h_b, losses]) and concentrate is not None and vapor is not None:
                energy_out = vapor * h_v + concentrate * h_b + losses
                energy_in = a_feed * h_a + phi
                balance = energy_in - energy_out
                results.append(cls._result_item("Énergie entrée", energy_in, "kJ/h", "A*hA + Phi"))
                results.append(cls._result_item("Énergie sortie", energy_out, "kJ/h", "V*HV + B*hB + losses"))
                results.append(cls._result_item("Écart de bilan énergétique", balance, "kJ/h", "A*hA + Phi - (V*HV + B*hB + losses)"))
                steps.append(f"Entrée = {cls._fmt(a_feed)} x {cls._fmt(h_a)} + {cls._fmt(phi)} = {cls._fmt(energy_in)} kJ/h")
                steps.append(f"Sortie = {cls._fmt(vapor)} x {cls._fmt(h_v)} + {cls._fmt(concentrate)} x {cls._fmt(h_b)} + {cls._fmt(losses)} = {cls._fmt(energy_out)} kJ/h")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_drying(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            m_s = cls._get_value(form_data, "Ms", label="Masse de solide sec Ms", positive=True)
            x_i = cls._get_value(form_data, "Xi", label="Humidité initiale Xi", nonnegative=True)
            x_f = cls._get_value(form_data, "Xf", label="Humidité finale Xf", nonnegative=True)
            latent = cls._get_value(form_data, "Lv", label="Chaleur latente Lv", positive=True)
            h_coeff = cls._get_value(form_data, "h", label="Coefficient convectif h", positive=True)
            surface = cls._get_value(form_data, "S", label="Surface S", positive=True)
            temp_air = cls._get_value(form_data, "Ta", label="Température air Ta")
            temp_product = cls._get_value(form_data, "Tp", label="Température produit Tp")

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            warnings: List[str] = []

            water_removed = None
            drying_heat = None
            convective_heat = None

            if all(value is not None for value in [m_s, x_i, x_f]):
                water_removed = m_s * (x_i - x_f)
                results.append(cls._result_item("Eau retirée W", water_removed, "kg", "W = Ms * (Xi - Xf)"))
                steps.append(f"W = {cls._fmt(m_s)} x ({cls._fmt(x_i)} - {cls._fmt(x_f)}) = {cls._fmt(water_removed)} kg")
                if water_removed < 0:
                    warnings.append("Xi est inférieur à Xf. Le résultat indique une humidification et non un séchage.")

            if water_removed is not None and latent is not None:
                drying_heat = water_removed * latent
                results.append(cls._result_item("Chaleur de séchage Q", drying_heat, "kJ", "Q = W * Lv"))
                steps.append(f"Q = {cls._fmt(water_removed)} x {cls._fmt(latent)} = {cls._fmt(drying_heat)} kJ")

            if all(value is not None for value in [h_coeff, surface, temp_air, temp_product]):
                convective_heat = h_coeff * surface * (temp_air - temp_product)
                results.append(cls._result_item("Chaleur convective Qconv", convective_heat, "kJ/s", "Qconv = h * S * (Ta - Tp)"))
                steps.append(f"Qconv = {cls._fmt(h_coeff)} x {cls._fmt(surface)} x ({cls._fmt(temp_air)} - {cls._fmt(temp_product)}) = {cls._fmt(convective_heat)} kJ/s")
                if convective_heat <= 0:
                    warnings.append("Ta doit être supérieure à Tp pour un séchage convectif utile.")

            if drying_heat is not None and convective_heat is not None and convective_heat > 0:
                drying_time = drying_heat / convective_heat
                results.append(cls._result_item("Temps de séchage estimé", drying_time, "s", "t = Q / (h * S * (Ta - Tp))"))
                steps.append(f"t = {cls._fmt(drying_heat)} / {cls._fmt(convective_heat)} = {cls._fmt(drying_time)} s")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps, warnings)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_psychrometric(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        param1_type = (form_data.get("param1_type") or "").strip()
        param2_type = (form_data.get("param2_type") or "").strip()

        if not param1_type or not param2_type:
            return cls._build_error("Sélectionnez deux paramètres psychrométriques.")
        if param1_type == param2_type:
            return cls._build_error("Les deux paramètres doivent être différents.")

        try:
            param1_value = cls._get_value(form_data, "param1_value", label="Valeur 1", required=True)
            param2_value = cls._get_value(form_data, "param2_value", label="Valeur 2", required=True)
            pressure = cls._get_value(form_data, "P", label="Pression totale P", positive=True) or 101.325
            result = PsychrometricService.calculate_psychrometric_properties(
                {
                    param1_type: param1_value,
                    param2_type: param2_value,
                    "P": pressure,
                }
            )
            if result.get("error"):
                return result
            return result
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_crystallization(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            c0 = cls._get_value(form_data, "C0", label="C0", nonnegative=True)
            ce = cls._get_value(form_data, "Ce", label="Ce", nonnegative=True)
            kp = cls._get_value(form_data, "Kp", label="Kp", nonnegative=True)
            n_exp = cls._get_value(form_data, "n_exp", label="n", nonnegative=True)
            ks = cls._get_value(form_data, "Ks", label="Ks", nonnegative=True)
            epsilon = cls._get_value(form_data, "epsilon", label="epsilon", nonnegative=True)
            h_exp = cls._get_value(form_data, "h_exp", label="h", nonnegative=True)
            i_exp = cls._get_value(form_data, "i_exp", label="i", nonnegative=True)
            mt = cls._get_value(form_data, "MT", label="MT", nonnegative=True)
            j_exp = cls._get_value(form_data, "j_exp", label="j", nonnegative=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            delta_c = None

            if c0 is not None and ce is not None:
                delta_c = c0 - ce
                results.append(cls._result_item("Sursaturation deltaC", delta_c, "kg/m³", "deltaC = C0 - Ce"))
                steps.append(f"deltaC = {cls._fmt(c0)} - {cls._fmt(ce)} = {cls._fmt(delta_c)} kg/m³")

            if delta_c is not None and kp is not None and n_exp is not None:
                jp = kp * (delta_c ** n_exp)
                results.append(cls._result_item("Nucléation primaire Jp", jp, "-", "Jp = Kp * deltaC^n"))
                steps.append(f"Jp = {cls._fmt(kp)} x {cls._fmt(delta_c)}^{cls._fmt(n_exp)} = {cls._fmt(jp)}")

            if all(value is not None for value in [delta_c, ks, epsilon, h_exp, i_exp, mt, j_exp]):
                js = ks * (epsilon ** h_exp) * (delta_c ** i_exp) * (mt ** j_exp)
                results.append(cls._result_item("Nucléation secondaire Js", js, "-", "Js = Ks * epsilon^h * deltaC^i * MT^j"))
                steps.append(f"Js = {cls._fmt(ks)} x {cls._fmt(epsilon)}^{cls._fmt(h_exp)} x {cls._fmt(delta_c)}^{cls._fmt(i_exp)} x {cls._fmt(mt)}^{cls._fmt(j_exp)} = {cls._fmt(js)}")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_chemical_reactors(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            na0 = cls._get_value(form_data, "NA0", label="NA0", positive=True)
            na = cls._get_value(form_data, "NA", label="NA", nonnegative=True)
            fa0 = cls._get_value(form_data, "FA0", label="FA0", positive=True)
            fa = cls._get_value(form_data, "FA", label="FA", nonnegative=True)
            minus_ra = cls._get_value(form_data, "minus_rA", label="-rA", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            batch_x = None
            cont_x = None

            if na0 is not None and na is not None:
                batch_x = (na0 - na) / na0
                results.append(cls._result_item("Conversion batch XA", batch_x, "-", "XA = (NA0 - NA) / NA0"))
                steps.append(f"XA = ({cls._fmt(na0)} - {cls._fmt(na)}) / {cls._fmt(na0)} = {cls._fmt(batch_x)}")

            if fa0 is not None and fa is not None:
                cont_x = (fa0 - fa) / fa0
                results.append(cls._result_item("Conversion continue XA", cont_x, "-", "XA = (FA0 - FA) / FA0"))
                steps.append(f"XA = ({cls._fmt(fa0)} - {cls._fmt(fa)}) / {cls._fmt(fa0)} = {cls._fmt(cont_x)}")

            if fa0 is not None and minus_ra is not None:
                conversion = cont_x if cont_x is not None else batch_x
                if conversion is not None:
                    cstr_volume = fa0 * conversion / minus_ra
                    pfr_volume = fa0 * conversion / minus_ra
                    results.append(cls._result_item("Volume CSTR", cstr_volume, "m³", "V = FA0 * XA / (-rA)"))
                    results.append(cls._result_item("Volume PFR approx.", pfr_volume, "m³", "V ≈ FA0 * XA / (-rA)"))
                    steps.append(f"VCSTR = {cls._fmt(fa0)} x {cls._fmt(conversion)} / {cls._fmt(minus_ra)} = {cls._fmt(cstr_volume)} m³")
                    steps.append(f"VPFR ≈ {cls._fmt(fa0)} x {cls._fmt(conversion)} / {cls._fmt(minus_ra)} = {cls._fmt(pfr_volume)} m³")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_adsorption(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            qmax = cls._get_value(form_data, "qmax", label="qmax", positive=True)
            k_langmuir = cls._get_value(form_data, "K", label="K", nonnegative=True)
            concentration = cls._get_value(form_data, "C", label="C", nonnegative=True)
            kf = cls._get_value(form_data, "Kf", label="Kf", positive=True)
            n_exp = cls._get_value(form_data, "n", label="n", positive=True)
            amount_adsorbed = cls._get_value(form_data, "amount_adsorbed", label="Quantité à adsorber", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            q_langmuir = None
            q_freundlich = None

            if all(value is not None for value in [qmax, k_langmuir, concentration]):
                q_langmuir = qmax * k_langmuir * concentration / (1 + k_langmuir * concentration)
                results.append(cls._result_item("Capacité Langmuir q", q_langmuir, "mol/kg", "q = qmax * K * C / (1 + K * C)"))
                steps.append(f"q = {cls._fmt(qmax)} x {cls._fmt(k_langmuir)} x {cls._fmt(concentration)} / (1 + {cls._fmt(k_langmuir)} x {cls._fmt(concentration)}) = {cls._fmt(q_langmuir)} mol/kg")

            if all(value is not None for value in [kf, concentration, n_exp]):
                q_freundlich = kf * concentration ** (1 / n_exp)
                results.append(cls._result_item("Capacité Freundlich q", q_freundlich, "mol/kg", "q = Kf * C^(1 / n)"))
                steps.append(f"q = {cls._fmt(kf)} x {cls._fmt(concentration)}^(1/{cls._fmt(n_exp)}) = {cls._fmt(q_freundlich)} mol/kg")

            if amount_adsorbed is not None:
                if q_langmuir is not None and q_langmuir > 0:
                    mass_langmuir = amount_adsorbed / q_langmuir
                    results.append(cls._result_item("Masse adsorbant (Langmuir)", mass_langmuir, "kg", "m = amount_adsorbed / q"))
                    steps.append(f"m = {cls._fmt(amount_adsorbed)} / {cls._fmt(q_langmuir)} = {cls._fmt(mass_langmuir)} kg")
                if q_freundlich is not None and q_freundlich > 0:
                    mass_freundlich = amount_adsorbed / q_freundlich
                    results.append(cls._result_item("Masse adsorbant (Freundlich)", mass_freundlich, "kg", "m = amount_adsorbed / q"))
                    steps.append(f"m = {cls._fmt(amount_adsorbed)} / {cls._fmt(q_freundlich)} = {cls._fmt(mass_freundlich)} kg")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_absorption(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            henry = cls._get_value(form_data, "H", label="Constante de Henry H", nonnegative=True)
            partial_pressure = cls._get_value(form_data, "P_partial", label="Pression partielle", nonnegative=True)
            y_in = cls._get_value(form_data, "yin", label="yin", minimum=0, maximum=1)
            y_out = cls._get_value(form_data, "yout", label="yout", minimum=0, maximum=1)
            gas_flow = cls._get_value(form_data, "G", label="Débit molaire gaz G", nonnegative=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if henry is not None and partial_pressure is not None:
                concentration = henry * partial_pressure
                results.append(cls._result_item("Concentration dissoute C", concentration, "cohérent", "C = H * P"))
                steps.append(f"C = {cls._fmt(henry)} x {cls._fmt(partial_pressure)} = {cls._fmt(concentration)}")

            if y_in is not None and y_out is not None:
                if y_in == 0:
                    raise ValueError("yin ne peut pas être nul pour calculer l'efficacité.")
                efficiency = (y_in - y_out) / y_in * 100
                results.append(cls._result_item("Efficacité d'abattement", efficiency, "%", "eta = (yin - yout) / yin * 100"))
                steps.append(f"eta = ({cls._fmt(y_in)} - {cls._fmt(y_out)}) / {cls._fmt(y_in)} x 100 = {cls._fmt(efficiency)} %")

            if gas_flow is not None and y_in is not None and y_out is not None:
                absorbed = gas_flow * (y_in - y_out)
                results.append(cls._result_item("Soluté absorbé", absorbed, "mol/s", "n = G * (yin - yout)"))
                steps.append(f"n = {cls._fmt(gas_flow)} x ({cls._fmt(y_in)} - {cls._fmt(y_out)}) = {cls._fmt(absorbed)} mol/s")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_membranes(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            permeability = cls._get_value(form_data, "Pm", label="Perméabilité Pm", positive=True)
            delta_p = cls._get_value(form_data, "deltaP", label="deltaP", positive=True)
            thickness = cls._get_value(form_data, "e", label="Épaisseur e", positive=True)
            area = cls._get_value(form_data, "A", label="Surface A", positive=True)
            p_a = cls._get_value(form_data, "PA", label="PA", positive=True)
            p_b = cls._get_value(form_data, "PB", label="PB", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            flux = None

            if all(value is not None for value in [permeability, delta_p, thickness]):
                flux = permeability * (delta_p / thickness)
                results.append(cls._result_item("Flux membranaire J", flux, "unité cohérente", "J = Pm * (deltaP / e)"))
                steps.append(f"J = {cls._fmt(permeability)} x ({cls._fmt(delta_p)} / {cls._fmt(thickness)}) = {cls._fmt(flux)}")

            if flux is not None and area is not None:
                q_permeate = flux * area
                results.append(cls._result_item("Débit perméat Qp", q_permeate, "unité cohérente", "Qp = J * A"))
                steps.append(f"Qp = {cls._fmt(flux)} x {cls._fmt(area)} = {cls._fmt(q_permeate)}")

            if p_a is not None and p_b is not None:
                alpha = p_a / p_b
                results.append(cls._result_item("Sélectivité alpha", alpha, "-", "alpha = PA / PB"))
                steps.append(f"alpha = {cls._fmt(p_a)} / {cls._fmt(p_b)} = {cls._fmt(alpha)}")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_heat_exchange(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            mass_flow = cls._get_value(form_data, "m", label="Débit massique m", positive=True)
            cp = cls._get_value(form_data, "Cp", label="Capacité thermique Cp", positive=True)
            delta_t = cls._get_value(form_data, "deltaT", label="deltaT")
            delta_t1 = cls._get_value(form_data, "deltaT1", label="deltaT1", positive=True)
            delta_t2 = cls._get_value(form_data, "deltaT2", label="deltaT2", positive=True)
            u_coeff = cls._get_value(form_data, "U", label="Coefficient global U", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            heat_duty = None
            lmtd = None

            if all(value is not None for value in [mass_flow, cp, delta_t]):
                heat_duty = mass_flow * cp * delta_t
                results.append(cls._result_item("Charge thermique Q", heat_duty, "kW ou kJ/s", "Q = m * Cp * deltaT"))
                steps.append(f"Q = {cls._fmt(mass_flow)} x {cls._fmt(cp)} x {cls._fmt(delta_t)} = {cls._fmt(heat_duty)}")

            if delta_t1 is not None and delta_t2 is not None:
                if delta_t1 == delta_t2:
                    lmtd = delta_t1
                else:
                    lmtd = (delta_t1 - delta_t2) / math.log(delta_t1 / delta_t2)
                results.append(cls._result_item("deltaTlm", lmtd, "K", "deltaTlm = (deltaT1 - deltaT2) / ln(deltaT1 / deltaT2)"))
                steps.append(f"deltaTlm = {cls._fmt(lmtd)} K")

            if heat_duty is not None and u_coeff is not None and lmtd is not None:
                area = heat_duty / (u_coeff * lmtd)
                results.append(cls._result_item("Surface requise A", area, "m²", "A = Q / (U * deltaTlm)"))
                steps.append(f"A = {cls._fmt(heat_duty)} / ({cls._fmt(u_coeff)} x {cls._fmt(lmtd)}) = {cls._fmt(area)} m²")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_mixing_agitation(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rho = cls._get_value(form_data, "rho", label="rho", positive=True)
            speed = cls._get_value(form_data, "N", label="N", positive=True)
            diameter = cls._get_value(form_data, "D", label="D", positive=True)
            mu = cls._get_value(form_data, "mu", label="mu", positive=True)
            power_number = cls._get_value(form_data, "Np", label="Np", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if all(value is not None for value in [rho, speed, diameter, mu]):
                reynolds = rho * speed * diameter ** 2 / mu
                regime = "laminaire" if reynolds < 10 else "transition" if reynolds < 10000 else "turbulent"
                results.append(cls._result_item("Reynolds d'agitation", reynolds, "-", "Re = rho * N * D^2 / mu"))
                steps.append(f"Re = {cls._fmt(rho)} x {cls._fmt(speed)} x {cls._fmt(diameter)}^2 / {cls._fmt(mu)} = {cls._fmt(reynolds)} ({regime})")

            if all(value is not None for value in [power_number, rho, speed, diameter]):
                power = power_number * rho * speed ** 3 * diameter ** 5
                results.append(cls._result_item("Puissance d'agitation", power, "W", "P = Np * rho * N^3 * D^5"))
                steps.append(f"P = {cls._fmt(power_number)} x {cls._fmt(rho)} x {cls._fmt(speed)}^3 x {cls._fmt(diameter)}^5 = {cls._fmt(power)} W")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_broyage(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            wi = cls._get_value(form_data, "Wi", label="Wi", positive=True)
            p80 = cls._get_value(form_data, "P80", label="P80", positive=True)
            f80 = cls._get_value(form_data, "F80", label="F80", positive=True)
            d_initial = cls._get_value(form_data, "Dinitial", label="Diamètre initial", positive=True)
            d_final = cls._get_value(form_data, "Dfinal", label="Diamètre final", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if all(value is not None for value in [wi, p80, f80]):
                energy = wi * (10 / math.sqrt(p80) - 10 / math.sqrt(f80))
                results.append(cls._result_item("Énergie de Bond", energy, "kWh/t", "E = Wi * (10 / sqrt(P80) - 10 / sqrt(F80))"))
                steps.append(f"E = {cls._fmt(wi)} x (10/sqrt({cls._fmt(p80)}) - 10/sqrt({cls._fmt(f80)})) = {cls._fmt(energy)} kWh/t")

            if d_initial is not None and d_final is not None:
                reduction_ratio = d_initial / d_final
                results.append(cls._result_item("Rapport de réduction", reduction_ratio, "-", "R = Dinitial / Dfinal"))
                steps.append(f"R = {cls._fmt(d_initial)} / {cls._fmt(d_final)} = {cls._fmt(reduction_ratio)}")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_tamisage(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            sizes = cls._parse_series(form_data.get("sieve_sizes", ""), "Tailles de tamis")
            retained = cls._parse_series(form_data.get("retained_values", ""), "Masses ou pourcentages retenus")
            if len(sizes) != len(retained):
                raise ValueError("Le nombre de tailles de tamis doit être identique au nombre de valeurs retenues.")
            if any(value < 0 for value in retained):
                raise ValueError("Les valeurs retenues ne peuvent pas être négatives.")

            total = sum(retained)
            if total == 0:
                raise ValueError("La somme des masses/percentages retenus ne peut pas être nulle.")

            percent_retained = [value / total * 100 for value in retained]
            cumulative_retained: List[float] = []
            cumulative_passing: List[float] = []
            running = 0.0
            for value in percent_retained:
                running += value
                cumulative_retained.append(running)
                cumulative_passing.append(100 - running)

            table_rows = []
            for size, retained_pct, cum_ret, cum_pass in zip(sizes, percent_retained, cumulative_retained, cumulative_passing):
                table_rows.append(
                    {
                        "size": cls._fmt(size),
                        "retained_percent": cls._fmt(retained_pct),
                        "cumulative_retained": cls._fmt(cum_ret),
                        "cumulative_passing": cls._fmt(cum_pass),
                    }
                )

            d50 = None
            for idx in range(len(sizes) - 1):
                pass_high = cumulative_passing[idx]
                pass_low = cumulative_passing[idx + 1]
                if (pass_high >= 50 >= pass_low) or (pass_low >= 50 >= pass_high):
                    x1, x2 = sizes[idx], sizes[idx + 1]
                    y1, y2 = pass_high, pass_low
                    if y2 == y1:
                        d50 = x1
                    else:
                        d50 = x1 + (50 - y1) * (x2 - x1) / (y2 - y1)
                    break

            results = [
                cls._result_item("Nombre de classes", float(len(sizes)), "-", "Nombre de tamis fournis"),
            ]
            steps = [
                f"Total retenu = {cls._fmt(total)}",
                "Pour chaque tamis: % retenu = valeur / total x 100, puis calcul des cumuls.",
            ]
            if d50 is not None:
                results.append(cls._result_item("d50 interpolé", d50, "mm", "Interpolation à 50% passant"))
                steps.append(f"d50 a été interpolé à {cls._fmt(d50)} mm à partir de la courbe cumulée.")

            extra = {"table_rows": table_rows}
            return cls._build_success(operation, form_data, results, steps, extra=extra)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_fluidisation(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            flow = cls._get_value(form_data, "Q", label="Débit Q", positive=True)
            area = cls._get_value(form_data, "A", label="Section A", positive=True)
            umf = cls._get_value(form_data, "umf", label="Vitesse minimale umf", positive=True)
            rho_s = cls._get_value(form_data, "rho_s", label="rho_s", positive=True)
            rho_f = cls._get_value(form_data, "rho_f", label="rho_f", positive=True)
            epsilon = cls._get_value(form_data, "epsilon", label="epsilon", minimum=0, maximum=1)
            height = cls._get_value(form_data, "H", label="Hauteur H", positive=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            warnings: List[str] = []
            velocity = None

            if flow is not None and area is not None:
                velocity = flow / area
                results.append(cls._result_item("Vitesse superficielle u", velocity, "m/s", "u = Q / A"))
                steps.append(f"u = {cls._fmt(flow)} / {cls._fmt(area)} = {cls._fmt(velocity)} m/s")

            if velocity is not None and umf is not None:
                status = 1.0 if velocity >= umf else 0.0
                label = "Lit fluidisé" if status == 1.0 else "Fluidisation non atteinte"
                results.append(cls._result_item(label, velocity - umf, "m/s", "Vérification u >= umf"))
                steps.append(f"Comparaison: u = {cls._fmt(velocity)} m/s et umf = {cls._fmt(umf)} m/s")
                if velocity < umf:
                    warnings.append("La vitesse superficielle est inférieure à umf.")

            if all(value is not None for value in [rho_s, rho_f, epsilon, height]):
                delta_p = (rho_s - rho_f) * (1 - epsilon) * GRAVITY * height
                results.append(cls._result_item("Perte de charge lit fluidisé", delta_p, "Pa", "deltaP = (rho_s - rho_f) * (1 - epsilon) * g * H"))
                steps.append(f"deltaP = ({cls._fmt(rho_s)} - {cls._fmt(rho_f)}) x (1 - {cls._fmt(epsilon)}) x 9.81 x {cls._fmt(height)} = {cls._fmt(delta_p)} Pa")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps, warnings)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_transport_fluides(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rho = cls._get_value(form_data, "rho", label="rho", positive=True)
            velocity = cls._get_value(form_data, "v", label="v", nonnegative=True)
            diameter = cls._get_value(form_data, "D", label="D", positive=True)
            mu = cls._get_value(form_data, "mu", label="mu", positive=True)
            length = cls._get_value(form_data, "L", label="L", positive=True)
            friction = cls._get_value(form_data, "f", label="f", nonnegative=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            area = None
            if diameter is not None:
                area = math.pi * diameter ** 2 / 4
                results.append(cls._result_item("Section A", area, "m²", "A = pi * D^2 / 4"))
                steps.append(f"A = pi x {cls._fmt(diameter)}^2 / 4 = {cls._fmt(area)} m²")

            if velocity is not None and area is not None:
                flow = velocity * area
                results.append(cls._result_item("Débit Q", flow, "m³/s", "Q = v * A"))
                steps.append(f"Q = {cls._fmt(velocity)} x {cls._fmt(area)} = {cls._fmt(flow)} m³/s")

            if all(value is not None for value in [rho, velocity, diameter, mu]):
                reynolds = rho * velocity * diameter / mu
                results.append(cls._result_item("Nombre de Reynolds", reynolds, "-", "Re = rho * v * D / mu"))
                steps.append(f"Re = {cls._fmt(rho)} x {cls._fmt(velocity)} x {cls._fmt(diameter)} / {cls._fmt(mu)} = {cls._fmt(reynolds)} ({cls._flow_regime(reynolds)})")

            if all(value is not None for value in [friction, length, diameter, rho, velocity]):
                delta_p = friction * (length / diameter) * (rho * velocity ** 2 / 2)
                results.append(cls._result_item("Perte de charge Darcy-Weisbach", delta_p, "Pa", "deltaP = f * (L / D) * (rho * v^2 / 2)"))
                steps.append(f"deltaP = {cls._fmt(friction)} x ({cls._fmt(length)} / {cls._fmt(diameter)}) x ({cls._fmt(rho)} x {cls._fmt(velocity)}^2 / 2) = {cls._fmt(delta_p)} Pa")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_pompes(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            rho = cls._get_value(form_data, "rho", label="rho", positive=True)
            flow = cls._get_value(form_data, "Q", label="Q", nonnegative=True)
            head = cls._get_value(form_data, "H", label="H", nonnegative=True)
            eta = cls._get_value(form_data, "eta", label="eta", minimum=0, maximum=1)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            hydraulic_power = None

            if all(value is not None for value in [rho, flow, head]):
                hydraulic_power = rho * GRAVITY * flow * head
                results.append(cls._result_item("Puissance hydraulique Ph", hydraulic_power, "W", "Ph = rho * g * Q * H"))
                steps.append(f"Ph = {cls._fmt(rho)} x 9.81 x {cls._fmt(flow)} x {cls._fmt(head)} = {cls._fmt(hydraulic_power)} W")

            if hydraulic_power is not None and eta is not None:
                shaft_power = hydraulic_power / eta
                results.append(cls._result_item("Puissance à l'arbre P", shaft_power, "W", "P = Ph / eta"))
                steps.append(f"P = {cls._fmt(hydraulic_power)} / {cls._fmt(eta)} = {cls._fmt(shaft_power)} W")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_cyclones(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            flow = cls._get_value(form_data, "Q", label="Q", positive=True)
            area = cls._get_value(form_data, "A", label="A", positive=True)
            rho = cls._get_value(form_data, "rho", label="rho", positive=True)
            coefficient = cls._get_value(form_data, "K", label="K", nonnegative=True)

            results: List[Dict[str, str]] = []
            steps: List[str] = []
            velocity = None

            if flow is not None and area is not None:
                velocity = flow / area
                results.append(cls._result_item("Vitesse d'entrée", velocity, "m/s", "v = Q / A"))
                steps.append(f"v = {cls._fmt(flow)} / {cls._fmt(area)} = {cls._fmt(velocity)} m/s")

            if velocity is not None and rho is not None and coefficient is not None:
                delta_p = coefficient * (rho * velocity ** 2 / 2)
                results.append(cls._result_item("Perte de charge cyclone", delta_p, "Pa", "deltaP = K * (rho * v^2 / 2)"))
                steps.append(f"deltaP = {cls._fmt(coefficient)} x ({cls._fmt(rho)} x {cls._fmt(velocity)}^2 / 2) = {cls._fmt(delta_p)} Pa")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))

    @classmethod
    def _calculate_humidification(cls, operation: Dict[str, Any], form_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            dry_air = cls._get_value(form_data, "m_dry_air", label="Débit d'air sec", positive=True)
            y_in = cls._get_value(form_data, "Yin", label="Yin", nonnegative=True)
            y_out = cls._get_value(form_data, "Yout", label="Yout", nonnegative=True)
            h_in = cls._get_value(form_data, "hin", label="hin")
            h_out = cls._get_value(form_data, "hout", label="hout")

            results: List[Dict[str, str]] = []
            steps: List[str] = []

            if dry_air is not None and y_in is not None and y_out is not None:
                water = dry_air * (y_out - y_in)
                results.append(cls._result_item("Eau ajoutée / retirée", water, "kg/s", "m_water = m_dry_air * (Yout - Yin)"))
                steps.append(f"m_water = {cls._fmt(dry_air)} x ({cls._fmt(y_out)} - {cls._fmt(y_in)}) = {cls._fmt(water)} kg/s")

            if dry_air is not None and h_in is not None and h_out is not None:
                heat = dry_air * (h_out - h_in)
                results.append(cls._result_item("Charge thermique", heat, "kJ/s", "Q = m_dry_air * (hout - hin)"))
                steps.append(f"Q = {cls._fmt(dry_air)} x ({cls._fmt(h_out)} - {cls._fmt(h_in)}) = {cls._fmt(heat)} kJ/s")

            cls._ensure_any(results)
            return cls._build_success(operation, form_data, results, steps)
        except (ValueError, ZeroDivisionError) as exc:
            return cls._build_error(str(exc))
