"""
Unit operation visualization service.

Generates SVG equipment schematics and Plotly charts for unit-operation pages.
"""

from __future__ import annotations

import json
import math
from typing import Any, Dict, List, Optional

import plotly
import plotly.graph_objs as go
from plotly.subplots import make_subplots

from services.psychrometric_service import PsychrometricService


class UnitVisualizationService:
    """Visualization helper for schematics and interactive curves."""

    VISUAL_CONFIGS: Dict[str, Dict[str, Any]] = {
        "decantation": {
            "shape": "settling_tank",
            "streams": [
                {"label": "Feed", "side": "left", "y": 128, "value_key": "Q"},
                {"label": "Clarified liquid", "side": "right", "y": 88},
                {"label": "Sludge", "side": "bottom", "x": 385},
            ],
            "plot_title": "Settling velocity vs particle diameter",
        },
        "centrifugation": {
            "shape": "centrifuge",
            "streams": [
                {"label": "Feed", "side": "left", "y": 128, "value_key": "N"},
                {"label": "Light phase", "side": "right", "y": 92},
                {"label": "Heavy phase / solids", "side": "bottom", "x": 385},
            ],
            "plot_title": "Centrifugal factor and settling enhancement",
        },
        "filtration": {
            "shape": "filter_press",
            "streams": [
                {"label": "Suspension", "side": "left", "y": 120},
                {"label": "Filtrate", "side": "right", "y": 102},
                {"label": "Cake", "side": "top", "x": 385},
            ],
            "plot_title": "Filtration curves",
        },
        "distillation": {
            "shape": "distillation_column",
            "streams": [
                {"label": "Feed F", "side": "left", "y": 144, "value_key": "F"},
                {"label": "Distillate D", "side": "top", "x": 468, "value_key": "D"},
                {"label": "Bottoms W", "side": "bottom", "x": 300, "value_key": "W"},
                {"label": "Reflux L", "side": "top", "x": 282, "value_key": "R"},
            ],
            "plot_title": "McCabe-Thiele style equilibrium view",
        },
        "extraction-liquide-liquide": {
            "shape": "mixer_settler",
            "streams": [
                {"label": "Feed F", "side": "left", "y": 120, "value_key": "F"},
                {"label": "Solvent S", "side": "top", "x": 320, "value_key": "S0"},
                {"label": "Extract E", "side": "right", "y": 92},
                {"label": "Raffinate R", "side": "right", "y": 164},
            ],
            "plot_title": "Mass balance mixing point",
        },
        "extraction-solide-liquide": {
            "shape": "leaching_tank",
            "streams": [
                {"label": "Solid feed", "side": "left", "y": 156},
                {"label": "Solvent in", "side": "top", "x": 385},
                {"label": "Extract out", "side": "right", "y": 94},
                {"label": "Exhausted solid", "side": "bottom", "x": 385},
            ],
            "plot_title": "Extraction yield evolution",
        },
        "evaporation": {
            "shape": "evaporator",
            "streams": [
                {"label": "Feed A", "side": "left", "y": 124, "value_key": "A_feed"},
                {"label": "Vapor V", "side": "top", "x": 402},
                {"label": "Concentrate B", "side": "right", "y": 142},
                {"label": "Heating steam", "side": "left", "y": 188},
            ],
            "plot_title": "Evaporation mass and concentration profile",
        },
        "sechage": {
            "shape": "dryer",
            "streams": [
                {"label": "Wet product in", "side": "left", "y": 154},
                {"label": "Dry product out", "side": "right", "y": 154},
                {"label": "Hot air in", "side": "top", "x": 318},
                {"label": "Moist air out", "side": "top", "x": 452},
            ],
            "plot_title": "Drying curves",
        },
        "psychrometric": {
            "shape": "air_handling",
            "streams": [
                {"label": "Air state in", "side": "left", "y": 128},
                {"label": "Computed point", "side": "right", "y": 128},
            ],
            "plot_title": "Simplified psychrometric chart",
        },
        "cristallisation": {
            "shape": "crystallizer",
            "streams": [
                {"label": "Feed solution", "side": "left", "y": 124},
                {"label": "Cooling / heating", "side": "top", "x": 385},
                {"label": "Crystals", "side": "bottom", "x": 340},
                {"label": "Mother liquor", "side": "right", "y": 150},
            ],
            "plot_title": "Solubility and supersaturation curves",
        },
        "reacteurs-chimiques": {
            "shape": "reactor_train",
            "streams": [
                {"label": "Feed FA0", "side": "left", "y": 128, "value_key": "FA0"},
                {"label": "Product FA", "side": "right", "y": 128, "value_key": "FA"},
            ],
            "plot_title": "Conversion profiles for reactors",
        },
        "adsorption": {
            "shape": "adsorption_column",
            "streams": [
                {"label": "Feed", "side": "left", "y": 128},
                {"label": "Clean outlet", "side": "right", "y": 96},
                {"label": "Spent adsorbent zone", "side": "bottom", "x": 385},
            ],
            "plot_title": "Adsorption isotherms and breakthrough behavior",
        },
        "absorption": {
            "shape": "absorption_column",
            "streams": [
                {"label": "Gas in", "side": "bottom", "x": 320},
                {"label": "Gas out", "side": "top", "x": 320},
                {"label": "Liquid in", "side": "top", "x": 452},
                {"label": "Liquid out", "side": "bottom", "x": 452},
            ],
            "plot_title": "Absorption equilibrium and operating line",
        },
        "membranes": {
            "shape": "membrane_module",
            "streams": [
                {"label": "Feed", "side": "left", "y": 128},
                {"label": "Permeate", "side": "top", "x": 450},
                {"label": "Retentate", "side": "right", "y": 158},
            ],
            "plot_title": "Membrane flux and permeate response",
        },
        "echange-thermique": {
            "shape": "heat_exchanger",
            "streams": [
                {"label": "Hot in", "side": "left", "y": 92},
                {"label": "Hot out", "side": "right", "y": 92},
                {"label": "Cold in", "side": "right", "y": 168},
                {"label": "Cold out", "side": "left", "y": 168},
            ],
            "plot_title": "Heat exchanger temperature profiles",
        },
        "melange-agitation": {
            "shape": "agitated_tank",
            "streams": [
                {"label": "Feed", "side": "left", "y": 128},
                {"label": "Mixed outlet", "side": "right", "y": 128},
                {"label": "Impeller speed N", "side": "top", "x": 385, "value_key": "N"},
            ],
            "plot_title": "Agitator power and Reynolds curves",
        },
        "broyage": {
            "shape": "crusher",
            "streams": [
                {"label": "Feed particles", "side": "left", "y": 128},
                {"label": "Product particles", "side": "right", "y": 128},
            ],
            "plot_title": "Size reduction energy",
        },
        "tamisage": {
            "shape": "sieve_stack",
            "streams": [
                {"label": "Feed", "side": "top", "x": 385},
                {"label": "Retained fractions", "side": "right", "y": 128},
                {"label": "Passing fraction", "side": "bottom", "x": 385},
            ],
            "plot_title": "Granulometric cumulative passing curve",
        },
        "fluidisation": {
            "shape": "fluidized_bed",
            "streams": [
                {"label": "Gas upflow", "side": "bottom", "x": 385, "value_key": "Q"},
                {"label": "Particles", "side": "left", "y": 156},
                {"label": "Expanded bed", "side": "right", "y": 96},
            ],
            "plot_title": "Fluidization pressure drop curve",
        },
        "transport-fluides": {
            "shape": "pipeline",
            "streams": [
                {"label": "Inlet", "side": "left", "y": 128},
                {"label": "Outlet", "side": "right", "y": 128},
                {"label": "Flow direction", "side": "top", "x": 385, "value_key": "v"},
            ],
            "plot_title": "Flow and pressure-drop relationships",
        },
        "pompes": {
            "shape": "pump",
            "streams": [
                {"label": "Suction", "side": "left", "y": 142, "value_key": "Q"},
                {"label": "Discharge", "side": "right", "y": 102, "value_key": "H"},
            ],
            "plot_title": "Pump power and head characteristics",
        },
        "cyclones": {
            "shape": "cyclone",
            "streams": [
                {"label": "Dusty gas in", "side": "left", "y": 94, "value_key": "Q"},
                {"label": "Clean gas out", "side": "top", "x": 450},
                {"label": "Solids down", "side": "bottom", "x": 350},
            ],
            "plot_title": "Cyclone efficiency and pressure drop",
        },
        "humidification": {
            "shape": "humidifier",
            "streams": [
                {"label": "Air in", "side": "left", "y": 128},
                {"label": "Air out", "side": "right", "y": 128},
                {"label": "Water added/removed", "side": "top", "x": 385},
            ],
            "plot_title": "Humidity change process path",
        },
    }

    @classmethod
    def generate_visualization(
        cls,
        operation: Dict[str, Any],
        form_data: Optional[Dict[str, Any]],
        result: Optional[Dict[str, Any]],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        form_data = form_data or {}
        result = result or {}
        config = cls.VISUAL_CONFIGS.get(operation["slug"], {})

        figure = cls._build_figure(operation["slug"], form_data, result, **kwargs)
        chart_json = json.dumps(figure, cls=plotly.utils.PlotlyJSONEncoder)
        schematic_html = cls._build_equipment_svg(operation, config, form_data)
        highlights = cls._collect_highlights(result, operation)

        has_inputs = any(str(value).strip() for key, value in form_data.items() if key != "calculator_context")
        return {
            "schematic_html": schematic_html,
            "chart_json": chart_json,
            "chart_title": config.get("plot_title", "Interactive process curve"),
            "plot_hint": "Enter values to update the curve." if not has_inputs else "Interactive curve updated from the current form values.",
            "highlights": highlights,
        }

    @classmethod
    def _collect_highlights(cls, result: Dict[str, Any], operation: Dict[str, Any]) -> List[Dict[str, str]]:
        if result and result.get("results"):
            highlights = []
            for item in result["results"][:3]:
                highlights.append(
                    {
                        "label": item.get("label", "Result"),
                        "value": f"{item.get('value', '--')} {item.get('unit', '')}".strip(),
                    }
                )
            return highlights

        return [
            {"label": "Diagram status", "value": "Ready"},
            {"label": "Curve mode", "value": "Interactive"},
            {"label": "Update", "value": "Submit values"},
        ]

    @classmethod
    def _build_figure(cls, slug: str, form_data: Dict[str, Any], result: Dict[str, Any], **kwargs: Any) -> go.Figure:
        builder_map = {
            "decantation": cls._plot_decantation,
            "centrifugation": cls._plot_centrifugation,
            "filtration": cls._plot_filtration,
            "distillation": cls._plot_distillation,
            "extraction-liquide-liquide": cls._plot_extraction_ll,
            "extraction-solide-liquide": cls._plot_extraction_sl,
            "evaporation": cls._plot_evaporation,
            "sechage": cls._plot_drying,
            "psychrometric": cls._plot_psychrometric,
            "cristallisation": cls._plot_crystallization,
            "reacteurs-chimiques": cls._plot_reactors,
            "adsorption": cls._plot_adsorption,
            "absorption": cls._plot_absorption,
            "membranes": cls._plot_membranes,
            "echange-thermique": cls._plot_heat_exchange,
            "melange-agitation": cls._plot_mixing,
            "broyage": cls._plot_grinding,
            "tamisage": cls._plot_screening,
            "fluidisation": cls._plot_fluidization,
            "transport-fluides": cls._plot_fluid_transport,
            "pompes": cls._plot_pumps,
            "cyclones": cls._plot_cyclones,
            "humidification": cls._plot_humidification,
        }
        builder = builder_map.get(slug, cls._plot_placeholder)
        figure = builder(form_data, result, **kwargs)
        figure.update_layout(
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.75)",
            font={"color": "#e8eefc"},
            margin={"l": 50, "r": 25, "t": 50, "b": 45},
            legend={"orientation": "h", "yanchor": "bottom", "y": 1.02, "x": 0},
        )
        return figure

    @staticmethod
    def _num(form_data: Dict[str, Any], key: str, default: float) -> float:
        value = form_data.get(key, default)
        try:
            if value in (None, ""):
                return float(default)
            text = str(value).strip().replace(",", ".")
            return float(text)
        except (TypeError, ValueError):
            return float(default)

    @staticmethod
    def _result_num(result: Dict[str, Any], label_contains: str) -> Optional[float]:
        for item in result.get("results", []):
            if label_contains.lower() in item.get("label", "").lower():
                try:
                    return float(str(item.get("value", "")).replace(",", "."))
                except ValueError:
                    return None
        return None

    @classmethod
    def _build_equipment_svg(cls, operation: Dict[str, Any], config: Dict[str, Any], form_data: Dict[str, Any]) -> str:
        shape = config.get("shape", "generic")
        shape_svg = cls._shape_svg(shape)
        stream_svg = "".join(cls._stream_svg(stream, form_data) for stream in config.get("streams", []))
        return f"""
        <div class="uov-schematic-wrap">
            <svg class="uov-schematic" viewBox="0 0 760 260" role="img" aria-label="{operation['name']} schematic">
                <defs>
                    <marker id="uov-arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="8" markerHeight="8" orient="auto-start-reverse">
                        <path d="M 0 0 L 10 5 L 0 10 z" fill="#4fc3ff"></path>
                    </marker>
                </defs>
                <rect x="10" y="10" width="740" height="240" rx="28" fill="rgba(10,13,25,0.48)" stroke="rgba(255,255,255,0.06)" />
                {shape_svg}
                {stream_svg}
                <text x="380" y="228" text-anchor="middle" fill="#eef5ff" font-size="18" font-weight="700">{operation['name']}</text>
            </svg>
        </div>
        """

    @classmethod
    def _stream_svg(cls, stream: Dict[str, Any], form_data: Dict[str, Any]) -> str:
        side = stream.get("side", "left")
        label = stream["label"]
        value_key = stream.get("value_key")
        suffix = ""
        if value_key and form_data.get(value_key):
            suffix = f" ({form_data.get(value_key)})"

        if side == "left":
            y = stream.get("y", 128)
            return f"""
                <line x1="42" y1="{y}" x2="250" y2="{y}" stroke="#4fc3ff" stroke-width="4" marker-end="url(#uov-arrow)" />
                <text x="46" y="{y - 12}" fill="#cfe6ff" font-size="14">{label}{suffix}</text>
            """
        if side == "right":
            y = stream.get("y", 128)
            return f"""
                <line x1="510" y1="{y}" x2="718" y2="{y}" stroke="#4fc3ff" stroke-width="4" marker-end="url(#uov-arrow)" />
                <text x="532" y="{y - 12}" fill="#cfe6ff" font-size="14">{label}{suffix}</text>
            """
        if side == "top":
            x = stream.get("x", 380)
            return f"""
                <line x1="{x}" y1="42" x2="{x}" y2="86" stroke="#60f0b5" stroke-width="4" marker-end="url(#uov-arrow)" />
                <text x="{x}" y="34" text-anchor="middle" fill="#d6f8eb" font-size="14">{label}{suffix}</text>
            """
        x = stream.get("x", 380)
        return f"""
            <line x1="{x}" y1="174" x2="{x}" y2="220" stroke="#ffb45c" stroke-width="4" marker-end="url(#uov-arrow)" />
            <text x="{x}" y="244" text-anchor="middle" fill="#ffe1ba" font-size="14">{label}{suffix}</text>
        """

    @classmethod
    def _shape_svg(cls, shape: str) -> str:
        """Generate professional chemical engineering equipment SVG diagrams."""
        mapping = {
            "settling_tank": """
                <!-- Professional Settling Tank -->
                <g transform="translate(250,88)">
                    <!-- Tank body with proper proportions -->
                    <rect x="0" y="0" width="260" height="86" rx="8" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Inlet weir -->
                    <rect x="-15" y="20" width="20" height="46" fill="rgba(79,195,255,0.3)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Outlet weir -->
                    <rect x="255" y="20" width="20" height="46" fill="rgba(79,195,255,0.3)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Clarified liquid outlet -->
                    <rect x="255" y="35" width="30" height="16" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Sludge collection zone -->
                    <rect x="0" y="60" width="260" height="26" fill="rgba(255,179,102,0.25)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Sludge outlet -->
                    <rect x="115" y="86" width="30" height="15" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Internal baffles -->
                    <line x1="80" y1="0" x2="80" y2="86" stroke="#93b8ff" stroke-width="1" stroke-dasharray="3,3"/>
                    <line x1="180" y1="0" x2="180" y2="86" stroke="#93b8ff" stroke-width="1" stroke-dasharray="3,3"/>
                    <!-- Flow direction arrows -->
                    <path d="M 40 30 L 50 25 L 50 35 Z" fill="#4fc3ff"/>
                    <path d="M 220 30 L 210 25 L 210 35 Z" fill="#4fc3ff"/>
                </g>
            """,
            "centrifuge": """
                <!-- Professional Centrifuge -->
                <g transform="translate(314,62)">
                    <!-- Bowl housing -->
                    <ellipse cx="66" cy="66" rx="66" ry="40" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Internal bowl -->
                    <ellipse cx="66" cy="66" rx="50" ry="30" fill="rgba(79,195,255,0.15)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Drive shaft -->
                    <rect x="60" y="26" width="12" height="80" fill="rgba(255,179,102,0.6)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Liquid discharge ports -->
                    <circle cx="40" cy="40" r="4" fill="#60f0b5"/>
                    <circle cx="92" cy="40" r="4" fill="#60f0b5"/>
                    <!-- Solids discharge -->
                    <rect x="58" y="96" width="16" height="12" fill="rgba(255,211,127,0.6)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Rotation indicator -->
                    <path d="M 66 26 L 76 16 L 86 26" stroke="#ff8d6b" stroke-width="2" fill="none"/>
                </g>
            """,
            "filter_press": """
                <!-- Professional Filter Press -->
                <g transform="translate(255,90)">
                    <!-- Frame -->
                    <rect x="0" y="0" width="250" height="76" rx="6" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Filter plates (stacked) -->
                    <rect x="15" y="8" width="8" height="60" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <rect x="28" y="8" width="8" height="60" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <rect x="41" y="8" width="8" height="60" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <rect x="54" y="8" width="8" height="60" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <rect x="67" y="8" width="8" height="60" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Filter cloths -->
                    <rect x="20" y="8" width="4" height="60" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="33" y="8" width="4" height="60" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="46" y="8" width="4" height="60" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="59" y="8" width="4" height="60" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="72" y="8" width="4" height="60" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <!-- Feed port -->
                    <rect x="85" y="25" width="20" height="26" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Filtrate collection -->
                    <rect x="110" y="8" width="135" height="60" fill="rgba(96,240,181,0.2)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Filtrate outlet -->
                    <rect x="230" y="25" width="20" height="26" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Hydraulic closure system -->
                    <circle cx="125" cy="35" r="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <path d="M 117 35 L 133 35 M 125 27 L 125 43" stroke="#ff8d6b" stroke-width="1"/>
                </g>
            """,
            "distillation_column": """
                <!-- Professional Distillation Column -->
                <g transform="translate(280,26)">
                    <!-- Column shell -->
                    <rect x="30" y="18" width="140" height="152" rx="20" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="85" width="35" height="20" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Tray support rings -->
                    <circle cx="100" cy="45" r="60" fill="none" stroke="#93b8ff" stroke-width="1" stroke-dasharray="2,2"/>
                    <circle cx="100" cy="75" r="60" fill="none" stroke="#93b8ff" stroke-width="1" stroke-dasharray="2,2"/>
                    <circle cx="100" cy="105" r="60" fill="none" stroke="#93b8ff" stroke-width="1" stroke-dasharray="2,2"/>
                    <circle cx="100" cy="135" r="60" fill="none" stroke="#93b8ff" stroke-width="1" stroke-dasharray="2,2"/>
                    <circle cx="100" cy="165" r="60" fill="none" stroke="#93b8ff" stroke-width="1" stroke-dasharray="2,2"/>
                    <!-- Trays (simplified representation) -->
                    <rect x="45" y="38" width="110" height="4" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="45" y="68" width="110" height="4" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="45" y="98" width="110" height="4" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="45" y="128" width="110" height="4" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="45" y="158" width="110" height="4" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <!-- Tray perforations -->
                    <circle cx="60" cy="40" r="1" fill="#4fc3ff"/><circle cx="80" cy="40" r="1" fill="#4fc3ff"/>
                    <circle cx="100" cy="40" r="1" fill="#4fc3ff"/><circle cx="120" cy="40" r="1" fill="#4fc3ff"/><circle cx="140" cy="40" r="1" fill="#4fc3ff"/>
                    <!-- Condenser -->
                    <rect x="15" y="0" width="170" height="24" rx="8" fill="rgba(79,195,255,0.3)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Condenser tubes -->
                    <rect x="25" y="4" width="140" height="2" fill="rgba(79,195,255,0.5)"/>
                    <rect x="25" y="8" width="140" height="2" fill="rgba(79,195,255,0.5)"/>
                    <rect x="25" y="12" width="140" height="2" fill="rgba(79,195,255,0.5)"/>
                    <rect x="25" y="16" width="140" height="2" fill="rgba(79,195,255,0.5)"/>
                    <rect x="25" y="20" width="140" height="2" fill="rgba(79,195,255,0.5)"/>
                    <!-- Cooling water in/out -->
                    <rect x="0" y="4" width="20" height="16" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <rect x="175" y="4" width="20" height="16" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Distillate accumulator -->
                    <rect x="60" y="180" width="80" height="20" rx="6" fill="rgba(96,240,181,0.3)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Distillate outlet -->
                    <rect x="125" y="185" width="20" height="10" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Reflux line -->
                    <path d="M 100 180 L 100 170 L 100 18" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Reboiler -->
                    <rect x="10" y="196" width="180" height="26" rx="8" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Reboiler tubes -->
                    <rect x="20" y="200" width="160" height="2" fill="rgba(255,141,107,0.5)"/>
                    <rect x="20" y="204" width="160" height="2" fill="rgba(255,141,107,0.5)"/>
                    <rect x="20" y="208" width="160" height="2" fill="rgba(255,141,107,0.5)"/>
                    <rect x="20" y="212" width="160" height="2" fill="rgba(255,141,107,0.5)"/>
                    <rect x="20" y="216" width="160" height="2" fill="rgba(255,141,107,0.5)"/>
                    <!-- Steam in/out -->
                    <rect x="0" y="200" width="15" height="18" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="185" y="200" width="15" height="18" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Bottoms outlet -->
                    <rect x="75" y="222" width="50" height="15" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                </g>
            """,
            "absorption_column": """
                <!-- Professional Absorption Column -->
                <g transform="translate(322,44)">
                    <!-- Column shell -->
                    <rect x="0" y="0" width="116" height="156" rx="16" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Packing material -->
                    <rect x="8" y="8" width="100" height="140" fill="rgba(255,179,102,0.2)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Packing elements (simplified) -->
                    <path d="M 15 20 Q 25 15 35 20 T 55 20 Q 65 15 75 20 T 95 20" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <path d="M 15 40 Q 25 35 35 40 T 55 40 Q 65 35 75 40 T 95 40" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <path d="M 15 60 Q 25 55 35 60 T 55 60 Q 65 55 75 60 T 95 60" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <path d="M 15 80 Q 25 75 35 80 T 55 80 Q 65 75 75 80 T 95 80" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <path d="M 15 100 Q 25 95 35 100 T 55 100 Q 65 95 75 100 T 95 100" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <path d="M 15 120 Q 25 115 35 120 T 55 120 Q 65 115 75 120 T 95 120" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <path d="M 15 140 Q 25 135 35 140 T 55 140 Q 65 135 75 140 T 95 140" stroke="#ffb45c" stroke-width="1" fill="none"/>
                    <!-- Gas inlet (bottom) -->
                    <rect x="35" y="150" width="46" height="16" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Gas outlet (top) -->
                    <rect x="35" y="-10" width="46" height="16" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Liquid inlet (top) -->
                    <rect x="0" y="20" width="15" height="30" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Liquid outlet (bottom) -->
                    <rect x="101" y="106" width="15" height="30" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Liquid distributor -->
                    <rect x="8" y="25" width="100" height="4" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Liquid collector -->
                    <rect x="8" y="127" width="100" height="4" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Flow direction arrows indicating counter-current flow -->
                    <path d="M 58 25 L 58 35" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 58 125 L 58 135" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 58 135 L 58 125" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 58 35 L 58 25" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                </g>
            """,
            "adsorption_column": """
                <!-- Professional Adsorption Column -->
                <g transform="translate(318,54)">
                    <!-- Column shell -->
                    <rect x="0" y="0" width="124" height="142" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Adsorbent bed -->
                    <rect x="8" y="8" width="108" height="126" fill="rgba(255,179,102,0.25)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Adsorbent particles (simplified) -->
                    <circle cx="25" cy="25" r="3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="45" cy="20" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="65" cy="28" r="3.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="85" cy="22" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="105" cy="26" r="3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="35" cy="45" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="55" cy="42" r="3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="75" cy="48" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="95" cy="44" r="3.5" fill="rgba(255,211,127,0.6)"/>
                    <!-- Breakthrough curve zone (darker area) -->
                    <rect x="8" y="80" width="108" height="54" fill="rgba(255,141,107,0.15)" stroke="#ff8d6b" stroke-width="1" stroke-dasharray="3,3"/>
                    <!-- Feed inlet -->
                    <rect x="40" y="-8" width="44" height="12" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Clean outlet -->
                    <rect x="40" y="140" width="44" height="12" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Spent adsorbent regeneration port -->
                    <rect x="0" y="60" width="12" height="22" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Support grid -->
                    <rect x="8" y="130" width="108" height="4" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <!-- Flow direction indicators -->
                    <path d="M 62 10 L 62 20" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 62 130 L 62 140" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                </g>
            """,
            "dryer": """
                <!-- Professional Dryer -->
                <g transform="translate(248,84)">
                    <!-- Dryer chamber -->
                    <rect x="0" y="0" width="264" height="86" rx="12" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Heating coils/air ducts -->
                    <rect x="20" y="15" width="224" height="8" rx="4" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="20" y="30" width="224" height="8" rx="4" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="20" y="45" width="224" height="8" rx="4" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="20" y="60" width="224" height="8" rx="4" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Wet product inlet -->
                    <rect x="0" y="30" width="25" height="26" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Dry product outlet -->
                    <rect x="239" y="30" width="25" height="26" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Hot air inlet -->
                    <rect x="100" y="-8" width="30" height="12" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Moist air outlet -->
                    <rect x="130" y="78" width="30" height="12" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Product bed -->
                    <rect x="30" y="65" width="204" height="16" fill="rgba(255,211,127,0.25)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Product particles -->
                    <circle cx="50" cy="73" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="70" cy="70" r="1.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="90" cy="75" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="110" cy="72" r="1.8" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="130" cy="74" r="2.2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="150" cy="71" r="1.6" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="170" cy="76" r="2.3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="190" cy="73" r="1.9" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="210" cy="75" r="2.1" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="230" cy="72" r="1.7" fill="rgba(255,211,127,0.6)"/>
                    <!-- Air flow arrows -->
                    <path d="M 115 5 L 115 15" stroke="#ff8d6b" stroke-width="2" marker-end="url(#arrow-orange)"/>
                    <path d="M 145 70 L 145 80" stroke="#ff8d6b" stroke-width="2" marker-end="url(#arrow-orange)"/>
                    <!-- Product flow arrows -->
                    <path d="M 15 43 L 25 43" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 239 43 L 249 43" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                </g>
            """,
            "reactor_train": """
                <!-- Professional Reactor Train -->
                <g transform="translate(292,92)">
                    <!-- CSTR Reactor 1 -->
                    <circle cx="36" cy="36" r="36" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Agitator -->
                    <line x1="36" y1="0" x2="36" y2="72" stroke="#93b8ff" stroke-width="2"/>
                    <path d="M 24 72 L 36 60 L 48 72" stroke="#60f0b5" stroke-width="3" fill="none"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="25" width="15" height="22" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Product outlet -->
                    <rect x="57" y="25" width="15" height="22" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Reactor label -->
                    <text x="36" y="38" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="bold">CSTR</text>
                    <!-- PFR Reactor 2 -->
                    <rect x="108" y="0" width="110" height="52" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Catalyst bed -->
                    <rect x="118" y="8" width="90" height="36" fill="rgba(255,179,102,0.25)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Catalyst particles -->
                    <circle cx="135" cy="20" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="155" cy="18" r="1.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="175" cy="22" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="195" cy="19" r="1.8" fill="rgba(255,211,127,0.6)"/>
                    <!-- PFR label -->
                    <text x="163" y="42" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="bold">PFR</text>
                    <!-- Staged Reactor 3 -->
                    <rect x="242" y="-4" width="120" height="64" rx="32" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Internal stages -->
                    <line x1="272" y1="0" x2="272" y2="60" stroke="#93b8ff" stroke-width="1" stroke-dasharray="3,3"/>
                    <line x1="332" y1="0" x2="332" y2="60" stroke="#93b8ff" stroke-width="1" stroke-dasharray="3,3"/>
                    <!-- Stage agitators -->
                    <circle cx="302" cy="15" r="8" fill="rgba(79,195,255,0.2)" stroke="#4fc3ff" stroke-width="1"/>
                    <circle cx="362" cy="15" r="8" fill="rgba(79,195,255,0.2)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Staged label -->
                    <text x="302" y="50" text-anchor="middle" fill="#ffffff" font-size="10" font-weight="bold">STAGED</text>
                    <!-- Flow connections -->
                    <path d="M 72 36 L 108 26" stroke="#60f0b5" stroke-width="3"/>
                    <path d="M 218 26 L 242 26" stroke="#60f0b5" stroke-width="3"/>
                </g>
            """,

            "mixer_settler": """
                <!-- Professional Mixer-Settler -->
                <g transform="translate(246,88)">
                    <!-- Mixer compartment -->
                    <rect x="0" y="0" width="126" height="76" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Agitator in mixer -->
                    <line x1="63" y1="8" x2="63" y2="68" stroke="#93b8ff" stroke-width="2"/>
                    <path d="M 51 68 L 63 56 L 75 68" stroke="#60f0b5" stroke-width="3" fill="none"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="25" width="15" height="26" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Solvent inlet -->
                    <rect x="55" y="-8" width="16" height="12" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Mixer outlet to settler -->
                    <rect x="111" y="25" width="15" height="26" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Settler compartment -->
                    <rect x="144" y="0" width="126" height="76" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Interface level -->
                    <line x1="144" y1="38" x2="270" y2="38" stroke="#93b8ff" stroke-width="1" stroke-dasharray="3,3"/>
                    <!-- Organic phase outlet -->
                    <rect x="255" y="8" width="15" height="26" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Aqueous phase outlet -->
                    <rect x="255" y="42" width="15" height="26" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 15 38 L 25 38" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 63 5 L 63 15" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 126 38 L 144 38" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 255 21 L 265 21" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 255 55 L 265 55" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                </g>
            """,
            "leaching_tank": """
                <!-- Professional Leaching Tank -->
                <g transform="translate(270,78)">
                    <!-- Tank body -->
                    <rect x="0" y="0" width="220" height="96" rx="22" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Solid bed -->
                    <rect x="10" y="50" width="200" height="36" fill="rgba(255,211,127,0.25)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Solid particles -->
                    <circle cx="30" cy="68" r="3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="60" cy="65" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="90" cy="70" r="3.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="120" cy="67" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="150" cy="69" r="3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="180" cy="66" r="2.8" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="210" cy="71" r="2.2" fill="rgba(255,211,127,0.6)"/>
                    <!-- Solvent inlet -->
                    <rect x="0" y="35" width="15" height="26" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Leached solids outlet -->
                    <rect x="205" y="50" width="15" height="36" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Pregnant leach solution outlet -->
                    <rect x="95" y="96" width="30" height="15" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Agitator -->
                    <line x1="110" y1="10" x2="110" y2="86" stroke="#93b8ff" stroke-width="2"/>
                    <path d="M 98 86 L 110 74 L 122 86" stroke="#60f0b5" stroke-width="3" fill="none"/>
                    <!-- Flow arrows -->
                    <path d="M 15 48 L 25 48" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 110 96 L 110 106" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 220 68 L 230 68" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                </g>
            """,
            "evaporator": """
                <!-- Professional Evaporator -->
                <g transform="translate(292,66)">
                    <!-- Heating section -->
                    <ellipse cx="88" cy="32" rx="88" ry="32" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Heating coils -->
                    <rect x="10" y="26" width="156" height="12" rx="6" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Vapor space -->
                    <rect x="4" y="4" width="168" height="28" fill="rgba(0,217,255,0.15)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Liquid section -->
                    <rect x="4" y="32" width="168" height="66" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Liquid level -->
                    <rect x="4" y="80" width="168" height="18" fill="rgba(96,240,181,0.25)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Vapor outlet -->
                    <rect x="76" y="0" width="24" height="8" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="45" width="12" height="26" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Product outlet -->
                    <rect x="160" y="45" width="12" height="26" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Condensate outlet -->
                    <rect x="76" y="98" width="24" height="8" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Heating steam inlet -->
                    <rect x="40" y="32" width="16" height="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Heating steam condensate outlet -->
                    <rect x="120" y="32" width="16" height="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 12 58 L 22 58" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 160 58 L 170 58" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 88 8 L 88 18" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 88 90 L 88 100" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                </g>
            """,
            "air_handling": """
                <!-- Professional Air Handling Unit -->
                <g transform="translate(270,94)">
                    <!-- AHU housing -->
                    <rect x="0" y="0" width="220" height="72" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Supply fan -->
                    <circle cx="56" cy="36" r="22" fill="rgba(79,195,255,0.2)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Fan blades -->
                    <path d="M 56 14 L 56 58 M 34 36 L 78 36 M 42 22 L 70 50 M 70 22 L 42 50" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Return fan -->
                    <circle cx="164" cy="36" r="18" fill="rgba(96,240,181,0.2)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Return fan blades -->
                    <path d="M 164 18 L 164 54 M 146 36 L 182 36 M 152 24 L 176 48 M 176 24 L 152 48" stroke="#60f0b5" stroke-width="2"/>
                    <!-- Filters -->
                    <rect x="90" y="8" width="4" height="56" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <rect x="100" y="8" width="4" height="56" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Heating coil -->
                    <rect x="110" y="15" width="40" height="8" rx="4" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Cooling coil -->
                    <rect x="110" y="30" width="40" height="8" rx="4" fill="rgba(0,217,255,0.3)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Humidifier -->
                    <rect x="110" y="45" width="40" height="8" rx="4" fill="rgba(96,240,181,0.3)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Outside air inlet -->
                    <rect x="0" y="25" width="15" height="22" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Return air inlet -->
                    <rect x="205" y="25" width="15" height="22" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Supply air outlet -->
                    <rect x="75" y="25" width="15" height="22" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Exhaust air outlet -->
                    <rect x="130" y="25" width="15" height="22" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 15 36 L 25 36" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 205 36 L 215 36" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 75 36 L 85 36" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 130 36 L 140 36" stroke="#ff8d6b" stroke-width="2" marker-end="url(#arrow-orange)"/>
                </g>
            """,
            "crystallizer": """
                <!-- Professional Crystallizer -->
                <g transform="translate(274,78)">
                    <!-- Crystallizer body -->
                    <rect x="0" y="0" width="212" height="96" rx="26" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Solution volume -->
                    <rect x="6" y="40" width="200" height="50" fill="rgba(96,240,181,0.2)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Crystals -->
                    <polygon points="30,154 44,128 58,154" fill="rgba(255,255,255,0.8)" stroke="#ffffff" stroke-width="0.5"/>
                    <polygon points="80,160 95,132 110,160" fill="rgba(255,255,255,0.8)" stroke="#ffffff" stroke-width="0.5"/>
                    <polygon points="125,154 138,130 152,154" fill="rgba(255,255,255,0.8)" stroke="#ffffff" stroke-width="0.5"/>
                    <polygon points="175,158 188,134 202,158" fill="rgba(255,255,255,0.8)" stroke="#ffffff" stroke-width="0.5"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="35" width="15" height="26" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Mother liquor outlet -->
                    <rect x="197" y="35" width="15" height="26" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Crystal slurry outlet -->
                    <rect x="95" y="96" width="22" height="15" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Cooling coils -->
                    <rect x="20" y="15" width="172" height="8" rx="4" fill="rgba(0,217,255,0.3)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Agitator -->
                    <line x1="106" y1="10" x2="106" y2="86" stroke="#93b8ff" stroke-width="2"/>
                    <path d="M 94 86 L 106 74 L 118 86" stroke="#60f0b5" stroke-width="3" fill="none"/>
                    <!-- Cooling water in/out -->
                    <rect x="0" y="15" width="20" height="8" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <rect x="192" y="15" width="20" height="8" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 15 48 L 25 48" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 197 48 L 207 48" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 106 96 L 106 106" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                </g>
            """,
            "membrane_module": """
                <!-- Professional Membrane Module -->
                <g transform="translate(274,86)">
                    <!-- Module housing -->
                    <rect x="0" y="0" width="212" height="84" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Membrane elements -->
                    <line x1="106" y1="6" x2="106" y2="78" stroke="#60f0b5" stroke-width="4" stroke-dasharray="7,5"/>
                    <line x1="85" y1="6" x2="85" y2="78" stroke="#60f0b5" stroke-width="4" stroke-dasharray="7,5"/>
                    <line x1="127" y1="6" x2="127" y2="78" stroke="#60f0b5" stroke-width="4" stroke-dasharray="7,5"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="30" width="15" height="24" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Permeate outlet -->
                    <rect x="197" y="15" width="15" height="24" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Concentrate outlet -->
                    <rect x="197" y="45" width="15" height="24" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Pressure indication -->
                    <circle cx="50" cy="20" r="8" fill="rgba(255,141,107,0.2)" stroke="#ff8d6b" stroke-width="1"/>
                    <text x="50" y="24" text-anchor="middle" fill="#ff8d6b" font-size="8">P</text>
                    <!-- Flow arrows -->
                    <path d="M 15 42 L 25 42" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 197 27 L 207 27" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 197 57 L 207 57" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                </g>
            """,
            "heat_exchanger": """
                <!-- Professional Heat Exchanger -->
                <g transform="translate(246,84)">
                    <!-- Shell -->
                    <rect x="0" y="0" width="268" height="84" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Tube bundle -->
                    <rect x="20" y="12" width="228" height="60" fill="rgba(255,179,102,0.2)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Tube rows -->
                    <rect x="30" y="20" width="208" height="4" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="0.5"/>
                    <rect x="30" y="30" width="208" height="4" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="0.5"/>
                    <rect x="30" y="40" width="208" height="4" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="0.5"/>
                    <rect x="30" y="50" width="208" height="4" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="0.5"/>
                    <rect x="30" y="60" width="208" height="4" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="0.5"/>
                    <!-- Hot fluid inlet -->
                    <rect x="0" y="15" width="20" height="24" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Hot fluid outlet -->
                    <rect x="248" y="15" width="20" height="24" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Cold fluid inlet -->
                    <rect x="0" y="45" width="20" height="24" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Cold fluid outlet -->
                    <rect x="248" y="45" width="20" height="24" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Hot fluid path (shell side) -->
                    <path d="M 20 27 C 68 27, 86 63, 134 63 S 200 27, 248 27" stroke="#ff8d6b" stroke-width="4" fill="none"/>
                    <!-- Cold fluid path (tube side) -->
                    <path d="M 248 57 C 200 57, 182 21, 134 21 S 68 57, 20 57" stroke="#00d9ff" stroke-width="4" fill="none"/>
                    <!-- Flow arrows -->
                    <path d="M 20 27 L 30 27" stroke="#ff8d6b" stroke-width="2" marker-end="url(#arrow-orange)"/>
                    <path d="M 248 27 L 258 27" stroke="#ff8d6b" stroke-width="2" marker-end="url(#arrow-orange)"/>
                    <path d="M 20 57 L 30 57" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 248 57 L 258 57" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                </g>
            """,
            "agitated_tank": """
                <!-- Professional Agitated Tank -->
                <g transform="translate(292,80)">
                    <!-- Tank body -->
                    <rect x="0" y="0" width="176" height="94" rx="22" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Liquid level -->
                    <rect x="4" y="60" width="168" height="30" fill="rgba(96,240,181,0.2)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Agitator shaft -->
                    <line x1="88" y1="4" x2="88" y2="90" stroke="#93b8ff" stroke-width="3"/>
                    <!-- Impeller -->
                    <path d="M 68 90 L 88 76 L 108 90" stroke="#60f0b5" stroke-width="4" fill="none"/>
                    <!-- Baffles -->
                    <rect x="10" y="10" width="4" height="74" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <rect x="162" y="10" width="4" height="74" fill="rgba(255,255,255,0.3)" stroke="#ffffff" stroke-width="0.5"/>
                    <!-- Feed inlet -->
                    <rect x="0" y="35" width="15" height="24" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Product outlet -->
                    <rect x="161" y="35" width="15" height="24" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Heating/cooling jacket -->
                    <rect x="-8" y="10" width="8" height="74" fill="rgba(255,141,107,0.2)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="176" y="10" width="8" height="74" fill="rgba(255,141,107,0.2)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Jacket inlet/outlet -->
                    <rect x="-8" y="35" width="8" height="24" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="176" y="35" width="8" height="24" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 15 47 L 25 47" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 161 47 L 171 47" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                </g>
            """,
            "crusher": """
                <!-- Professional Crusher -->
                <g transform="translate(292,80)">
                    <!-- Crusher housing -->
                    <polygon points="0,0 176,0 138,94 38,94" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Fixed jaw -->
                    <rect x="20" y="10" width="12" height="74" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Moving jaw -->
                    <rect x="144" y="10" width="12" height="74" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Feed hopper -->
                    <polygon points="60,-10 116,-10 106,0 70,0" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Feed inlet -->
                    <rect x="78" y="-10" width="20" height="10" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Discharge chute -->
                    <rect x="70" y="94" width="48" height="15" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Crushing zone particles -->
                    <circle cx="58" cy="30" r="4" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="118" cy="30" r="3" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="58" cy="74" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="82" cy="78" r="1.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="108" cy="76" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="132" cy="80" r="1.8" fill="rgba(255,211,127,0.6)"/>
                    <!-- Drive mechanism -->
                    <circle cx="88" cy="20" r="8" fill="rgba(255,141,107,0.2)" stroke="#ff8d6b" stroke-width="1"/>
                    <path d="M 80 20 L 96 20 M 88 12 L 88 28" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Motion arrows -->
                    <path d="M 144 47 L 134 47" stroke="#ffb45c" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 32 47 L 22 47" stroke="#ffb45c" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <!-- Flow arrows -->
                    <path d="M 88 -5 L 88 5" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 88 94 L 88 104" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                </g>
            """,
            "sieve_stack": """
                <!-- Professional Sieve Stack -->
                <g transform="translate(318,60)">
                    <!-- Top sieve -->
                    <rect x="0" y="0" width="124" height="24" rx="10" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Sieve mesh -->
                    <rect x="6" y="6" width="112" height="12" fill="rgba(255,179,102,0.2)" stroke="#ffb45c" stroke-width="0.5"/>
                    <!-- Mesh pattern -->
                    <line x1="6" y1="12" x2="118" y2="12" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="18" y1="6" x2="18" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="30" y1="6" x2="30" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="42" y1="6" x2="42" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="54" y1="6" x2="54" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="66" y1="6" x2="66" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="78" y1="6" x2="78" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="90" y1="6" x2="90" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="102" y1="6" x2="102" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="114" y1="6" x2="114" y2="18" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Middle sieve -->
                    <rect x="10" y="38" width="104" height="20" rx="10" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Sieve mesh -->
                    <rect x="16" y="44" width="92" height="8" fill="rgba(255,179,102,0.2)" stroke="#ffb45c" stroke-width="0.5"/>
                    <!-- Mesh pattern -->
                    <line x1="16" y1="48" x2="108" y2="48" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="24" y1="44" x2="24" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="32" y1="44" x2="32" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="40" y1="44" x2="40" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="48" y1="44" x2="48" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="56" y1="44" x2="56" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="64" y1="44" x2="64" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="72" y1="44" x2="72" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="80" y1="44" x2="80" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="88" y1="44" x2="88" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="96" y1="44" x2="96" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="104" y1="44" x2="104" y2="52" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Bottom sieve -->
                    <rect x="20" y="72" width="84" height="18" rx="9" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Sieve mesh -->
                    <rect x="26" y="78" width="72" height="6" fill="rgba(255,179,102,0.2)" stroke="#ffb45c" stroke-width="0.5"/>
                    <!-- Mesh pattern -->
                    <line x1="26" y1="81" x2="98" y2="81" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="32" y1="78" x2="32" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="38" y1="78" x2="38" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="44" y1="78" x2="44" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="50" y1="78" x2="50" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="56" y1="78" x2="56" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="62" y1="78" x2="62" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="68" y1="78" x2="68" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="74" y1="78" x2="74" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="80" y1="78" x2="80" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="86" y1="78" x2="86" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <line x1="92" y1="78" x2="92" y2="84" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Feed inlet -->
                    <rect x="50" y="0" width="24" height="8" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Oversize outlet -->
                    <rect x="0" y="16" width="15" height="8" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Product outlets -->
                    <rect x="109" y="54" width="15" height="8" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <rect x="89" y="88" width="15" height="8" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 62 4 L 62 14" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 15 20 L 5 20" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 109 58 L 119 58" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 89 92 L 99 92" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                </g>
            """,
            "fluidized_bed": """
                <!-- Professional Fluidized Bed -->
                <g transform="translate(314,46)">
                    <!-- Bed vessel -->
                    <rect x="0" y="0" width="132" height="154" rx="24" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Fluidized bed -->
                    <rect x="6" y="100" width="120" height="48" fill="rgba(255,211,127,0.25)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Particles in fluidization -->
                    <circle cx="24" cy="148" r="2" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="60" cy="142" r="1.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="96" cy="146" r="2.5" fill="rgba(255,211,127,0.6)"/>
                    <circle cx="132" cy="140" r="1.8" fill="rgba(255,211,127,0.6)"/>
                    <!-- Distributor plate -->
                    <rect x="6" y="96" width="120" height="8" fill="rgba(255,179,102,0.4)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Distributor holes -->
                    <circle cx="18" cy="100" r="1" fill="#ffb45c"/>
                    <circle cx="36" cy="100" r="1" fill="#ffb45c"/>
                    <circle cx="54" cy="100" r="1" fill="#ffb45c"/>
                    <circle cx="72" cy="100" r="1" fill="#ffb45c"/>
                    <circle cx="90" cy="100" r="1" fill="#ffb45c"/>
                    <circle cx="108" cy="100" r="1" fill="#ffb45c"/>
                    <circle cx="126" cy="100" r="1" fill="#ffb45c"/>
                    <!-- Freeboard zone -->
                    <rect x="6" y="6" width="120" height="90" fill="rgba(0,217,255,0.1)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Gas inlet -->
                    <rect x="54" y="150" width="24" height="12" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Solids inlet -->
                    <rect x="0" y="60" width="15" height="24" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Solids outlet -->
                    <rect x="117" y="60" width="15" height="24" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Gas outlet -->
                    <rect x="54" y="0" width="24" height="10" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Fluidization arrows -->
                    <path d="M 24 150 L 24 140" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 60 150 L 60 140" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 96 150 L 96 140" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 132 150 L 132 140" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <!-- Flow arrows -->
                    <path d="M 15 72 L 25 72" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 117 72 L 127 72" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                    <path d="M 66 10 L 66 0" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                </g>
            """,
            "pipeline": """
                <!-- Professional Pipeline -->
                <g transform="translate(232,112)">
                    <!-- Pipeline segment -->
                    <rect x="0" y="0" width="296" height="32" rx="16" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Flow indicator -->
                    <circle cx="42" cy="16" r="10" fill="rgba(79,195,255,0.3)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Flow arrow -->
                    <path d="M 32 16 L 52 16" stroke="#4fc3ff" stroke-width="3"/>
                    <path d="M 42 6 L 52 16 L 42 26" stroke="#4fc3ff" stroke-width="3" fill="none"/>
                    <!-- Pressure taps -->
                    <rect x="80" y="-4" width="8" height="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="208" y="-4" width="8" height="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="80" y="28" width="8" height="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <rect x="208" y="28" width="8" height="8" fill="rgba(255,141,107,0.4)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Insulation -->
                    <rect x="0" y="-6" width="296" height="6" fill="rgba(255,179,102,0.3)" stroke="#ffb45c" stroke-width="1"/>
                    <rect x="0" y="32" width="296" height="6" fill="rgba(255,179,102,0.3)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Flow direction arrow -->
                    <path d="M 280 16 L 290 16" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                </g>
            """,
            "pump": """
                <!-- Professional Pump -->
                <g transform="translate(294,110)">
                    <!-- Pump casing -->
                    <circle cx="58" cy="24" r="40" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Impeller -->
                    <path d="M 58 24 L 74 8 L 84 36 z" fill="rgba(60,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Drive shaft -->
                    <rect x="56" y="-8" width="4" height="32" fill="rgba(255,179,102,0.6)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Motor -->
                    <rect x="46" y="-32" width="24" height="24" rx="6" fill="rgba(255,141,107,0.3)" stroke="#ff8d6b" stroke-width="1"/>
                    <!-- Suction inlet -->
                    <rect x="18" y="10" width="20" height="28" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Discharge outlet -->
                    <rect x="78" y="10" width="20" height="28" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Base plate -->
                    <rect x="18" y="38" width="100" height="12" rx="6" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Flow arrows -->
                    <path d="M 18 24 L 28 24" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 78 24 L 88 24" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                </g>
            """,
            "cyclone": """
                <!-- Professional Cyclone -->
                <g transform="translate(328,54)">
                    <!-- Cyclone body -->
                    <path d="M 0 0 H 142 V 38 L 102 86 V 136 H 40 V 86 L 0 38 Z" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Vortex finder -->
                    <rect x="61" y="0" width="20" height="15" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Inlet duct -->
                    <rect x="0" y="10" width="25" height="28" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Solids outlet -->
                    <rect x="61" y="136" width="20" height="15" fill="rgba(255,211,127,0.4)" stroke="#ffd37f" stroke-width="1"/>
                    <!-- Vortex path -->
                    <path d="M 25 24 Q 71 46 71 86" stroke="#4fc3ff" stroke-width="3" fill="none"/>
                    <!-- Flow arrows -->
                    <path d="M 25 24 L 35 24" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 71 10 L 71 0" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 71 136 L 71 146" stroke="#ffd37f" stroke-width="2" marker-end="url(#arrow-amber)"/>
                </g>
            """,
            "humidifier": """
                <!-- Professional Humidifier -->
                <g transform="translate(264,86)">
                    <!-- Humidifier chamber -->
                    <rect x="0" y="0" width="232" height="84" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Water reservoir -->
                    <rect x="6" y="60" width="220" height="18" fill="rgba(96,240,181,0.25)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Water level -->
                    <line x1="6" y1="69" x2="226" y2="69" stroke="#60f0b5" stroke-width="1" stroke-dasharray="3,3"/>
                    <!-- Spray nozzles -->
                    <line x1="38" y1="8" x2="38" y2="52" stroke="#60f0b5" stroke-width="2"/>
                    <line x1="76" y1="8" x2="76" y2="52" stroke="#60f0b5" stroke-width="2"/>
                    <line x1="114" y1="8" x2="114" y2="52" stroke="#60f0b5" stroke-width="2"/>
                    <line x1="152" y1="8" x2="152" y2="52" stroke="#60f0b5" stroke-width="2"/>
                    <line x1="190" y1="8" x2="190" y2="52" stroke="#60f0b5" stroke-width="2"/>
                    <!-- Nozzle heads -->
                    <circle cx="38" cy="8" r="3" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <circle cx="76" cy="8" r="3" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <circle cx="114" cy="8" r="3" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <circle cx="152" cy="8" r="3" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <circle cx="190" cy="8" r="3" fill="rgba(96,240,181,0.6)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Air inlet -->
                    <rect x="0" y="25" width="15" height="34" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Humidified air outlet -->
                    <rect x="217" y="25" width="15" height="34" fill="rgba(0,217,255,0.4)" stroke="#00d9ff" stroke-width="1"/>
                    <!-- Water inlet -->
                    <rect x="100" y="78" width="16" height="10" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Water drain -->
                    <rect x="120" y="78" width="16" height="10" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Mist droplets -->
                    <circle cx="48" cy="28" r="1.5" fill="rgba(96,240,181,0.7)"/>
                    <circle cx="86" cy="32" r="1" fill="rgba(96,240,181,0.7)"/>
                    <circle cx="124" cy="26" r="1.2" fill="rgba(96,240,181,0.7)"/>
                    <circle cx="162" cy="30" r="1.8" fill="rgba(96,240,181,0.7)"/>
                    <circle cx="200" cy="28" r="1.3" fill="rgba(96,240,181,0.7)"/>
                    <!-- Flow arrows -->
                    <path d="M 15 42 L 25 42" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 217 42 L 227 42" stroke="#00d9ff" stroke-width="2" marker-end="url(#arrow-cyan)"/>
                    <path d="M 108 78 L 108 88" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                    <path d="M 128 78 L 128 88" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                </g>
            """,
            "generic": """
                <!-- Professional Generic Equipment -->
                <g transform="translate(272,88)">
                    <!-- Equipment body -->
                    <rect x="0" y="0" width="216" height="82" rx="18" fill="rgba(31,54,91,0.85)" stroke="#4fc3ff" stroke-width="2"/>
                    <!-- Internal components -->
                    <circle cx="50" cy="41" r="12" fill="rgba(79,195,255,0.2)" stroke="#4fc3ff" stroke-width="1"/>
                    <circle cx="108" cy="41" r="12" fill="rgba(96,240,181,0.2)" stroke="#60f0b5" stroke-width="1"/>
                    <circle cx="166" cy="41" r="12" fill="rgba(255,179,102,0.2)" stroke="#ffb45c" stroke-width="1"/>
                    <!-- Inlet -->
                    <rect x="0" y="30" width="15" height="22" fill="rgba(79,195,255,0.4)" stroke="#4fc3ff" stroke-width="1"/>
                    <!-- Outlet -->
                    <rect x="201" y="30" width="15" height="22" fill="rgba(96,240,181,0.4)" stroke="#60f0b5" stroke-width="1"/>
                    <!-- Flow arrows -->
                    <path d="M 15 41 L 25 41" stroke="#4fc3ff" stroke-width="2" marker-end="url(#arrow-blue)"/>
                    <path d="M 201 41 L 211 41" stroke="#60f0b5" stroke-width="2" marker-end="url(#arrow-teal)"/>
                </g>
            """,
        }
        return mapping.get(shape, mapping["generic"])

    @classmethod
    def _base_line_figure(cls, x_title="x", y_title="y", title=None):
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.update_layout(
            title=title or "",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.65)",
            font=dict(color="#e5e7eb"),
            margin=dict(l=45, r=25, t=45, b=45),
            xaxis=dict(
                title=x_title,
                gridcolor="rgba(148,163,184,0.18)",
                zerolinecolor="rgba(148,163,184,0.25)"
            ),
            yaxis=dict(
                title=y_title,
                gridcolor="rgba(148,163,184,0.18)",
                zerolinecolor="rgba(148,163,184,0.25)"
            ),
            legend=dict(
                bgcolor="rgba(15,23,42,0.4)",
                bordercolor="rgba(148,163,184,0.25)",
                borderwidth=1
            )
        )
        return fig

    @classmethod
    def _base_bar_figure(cls, x_title="x", y_title="y", title=None):
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.update_layout(
            title=title or "",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.65)",
            font=dict(color="#e5e7eb"),
            margin=dict(l=45, r=25, t=45, b=45),
            xaxis=dict(
                title=x_title,
                gridcolor="rgba(148,163,184,0.18)",
                zerolinecolor="rgba(148,163,184,0.25)"
            ),
            yaxis=dict(
                title=y_title,
                gridcolor="rgba(148,163,184,0.18)",
                zerolinecolor="rgba(148,163,184,0.25)"
            ),
            legend=dict(
                bgcolor="rgba(15,23,42,0.4)",
                bordercolor="rgba(148,163,184,0.25)",
                borderwidth=1
            )
        )
        return fig

    @classmethod
    def _base_scatter_figure(cls, x_title="x", y_title="y", title=None):
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.update_layout(
            title=title or "",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.65)",
            font=dict(color="#e5e7eb"),
            margin=dict(l=45, r=25, t=45, b=45),
            xaxis=dict(
                title=x_title,
                gridcolor="rgba(148,163,184,0.18)",
                zerolinecolor="rgba(148,163,184,0.25)"
            ),
            yaxis=dict(
                title=y_title,
                gridcolor="rgba(148,163,184,0.18)",
                zerolinecolor="rgba(148,163,184,0.25)"
            ),
            legend=dict(
                bgcolor="rgba(15,23,42,0.4)",
                bordercolor="rgba(148,163,184,0.25)",
                borderwidth=1
            )
        )
        return fig

    @classmethod
    def _empty_figure(cls, title="Visualization unavailable for this operation."):
        import plotly.graph_objects as go

        fig = go.Figure()
        fig.update_layout(
            title=title,
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(15,23,42,0.65)",
            font=dict(color="#e5e7eb"),
            margin=dict(l=45, r=25, t=45, b=45),
            xaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
            yaxis=dict(showgrid=False, showticklabels=False, zeroline=False),
        )
        return fig

    @classmethod
    def _safe_float(cls, value, default=0.0):
        """Safely convert value to float, returning default if conversion fails."""
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    @classmethod
    def _to_plot_html(cls, fig):
        """Convert Plotly figure to HTML with error handling."""
        try:
            return plotly.offline.plot(fig, output_type='div', include_plotlyjs=False)
        except Exception as e:
            # Return empty figure HTML if conversion fails
            fallback_fig = cls._empty_figure(f"Visualization error: {str(e)}")
            return plotly.offline.plot(fallback_fig, output_type='div', include_plotlyjs=False)

    @classmethod
    def _plot_decantation(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        rho_l = cls._num(form_data, "rho_l", 1000)
        rho_s = cls._num(form_data, "rho_s", 2500)
        mu = cls._num(form_data, "mu", 0.001)
        diameters = [d / 1e6 for d in range(20, 520, 20)]
        velocities = [9.81 * d ** 2 * max(rho_s - rho_l, 1) / (18 * mu) for d in diameters]
        fig = cls._base_line_figure("Particle diameter (µm)", "Settling velocity (m/s)")
        fig.add_trace(go.Scatter(x=[d * 1e6 for d in diameters], y=velocities, mode="lines", name="Stokes velocity", line={"color": "#4fc3ff", "width": 4}))
        smin = cls._result_num(result, "Surface minimale")
        if smin is not None:
            fig.add_annotation(text=f"Smin = {smin:.3f} m²", x=diameters[-1] * 1e6, y=max(velocities), showarrow=False, bgcolor="rgba(0,102,255,0.18)")
        return fig

    @classmethod
    def _plot_centrifugation(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        radius = cls._num(form_data, "r", 0.12)
        vcl = cls._num(form_data, "vCL", 0.0012)
        speeds = list(range(500, 6500, 250))
        omega = [2 * math.pi * n / 60 for n in speeds]
        k_values = [w ** 2 * radius / 9.81 for w in omega]
        vsc = [vcl * k for k in k_values]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("K vs rotation speed", "vSC vs rotation speed"))
        fig.add_trace(go.Scatter(x=speeds, y=k_values, mode="lines", name="K factor", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=speeds, y=vsc, mode="lines", name="vSC", line={"color": "#60f0b5", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="N (rpm)", row=1, col=1)
        fig.update_xaxes(title="N (rpm)", row=1, col=2)
        fig.update_yaxes(title="K", row=1, col=1)
        fig.update_yaxes(title="vSC (m/s)", row=1, col=2)
        return fig

    @classmethod
    def _plot_filtration(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        a_coef = cls._num(form_data, "A_coef", 10)
        b_coef = cls._num(form_data, "B_coef", 2)
        volumes = [i / 10 for i in range(1, 31)]
        times = [a_coef * v ** 2 + b_coef * v for v in volumes]
        t_values = list(range(0, 61, 3))
        delta_p = [a_coef * t + b_coef for t in t_values]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Constant pressure", "Constant flow"))
        fig.add_trace(go.Scatter(x=volumes, y=times, mode="lines", name="t(V)", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=t_values, y=delta_p, mode="lines", name="ΔP(t)", line={"color": "#ffb45c", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Filtered volume V", row=1, col=1)
        fig.update_yaxes(title="Time t", row=1, col=1)
        fig.update_xaxes(title="Time t", row=1, col=2)
        fig.update_yaxes(title="Pressure drop ΔP", row=1, col=2)
        return fig

    @classmethod
    def _plot_distillation(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        alpha = cls._num(form_data, "alpha", 2.4)
        reflux = cls._num(form_data, "R", 2.0)
        x_d = cls._num(form_data, "xD", 0.92)
        x_f = cls._num(form_data, "xF", 0.45)
        x_w = cls._num(form_data, "xW", 0.08)
        x_values = [i / 100 for i in range(0, 101)]
        y_eq = [alpha * x / (1 + (alpha - 1) * x) for x in x_values]
        y_rect = [reflux / (reflux + 1) * x + x_d / (reflux + 1) for x in x_values]
        y_strip = [x_w + (x - x_w) * max((x_f - x_w) / max((x_f - x_w), 1e-6), 0.8) for x in x_values]
        fig = cls._base_line_figure("x", "y")
        fig.add_trace(go.Scatter(x=x_values, y=y_eq, mode="lines", name="Equilibrium", line={"color": "#4fc3ff", "width": 4}))
        fig.add_trace(go.Scatter(x=x_values, y=x_values, mode="lines", name="y = x", line={"color": "#8ea4c8", "dash": "dash"}))
        fig.add_trace(go.Scatter(x=x_values, y=y_rect, mode="lines", name="Rectifying line", line={"color": "#60f0b5", "width": 3}))
        fig.add_trace(go.Scatter(x=x_values, y=y_strip, mode="lines", name="Stripping line", line={"color": "#ffb45c", "width": 3}))
        return fig

    @classmethod
    def _plot_extraction_ll(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        feed = cls._num(form_data, "F", 100)
        solvent = cls._num(form_data, "S0", 60)
        x_f = cls._num(form_data, "xF", 0.35)
        y0 = cls._num(form_data, "y0", 0.05)
        x_m1 = (feed * x_f + solvent * y0) / max(feed + solvent, 1e-6)
        fig = cls._base_line_figure("Liquid phase composition x", "Solvent phase composition y")
        fig.add_trace(go.Scatter(x=[0, x_f], y=[0, x_f * 0.8], mode="lines", name="Tie-line guide", line={"color": "#4fc3ff"}))
        fig.add_trace(go.Scatter(x=[x_f], y=[y0], mode="markers", name="Feed / solvent", marker={"size": 12, "color": "#60f0b5"}))
        fig.add_trace(go.Scatter(x=[x_m1], y=[x_m1], mode="markers+text", name="M1", text=["M1"], textposition="top center", marker={"size": 14, "color": "#ffb45c"}))
        return fig

    @classmethod
    def _plot_extraction_sl(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        actual_yield = cls._result_num(result, "Rendement") or 68
        ratios = [0.5, 1, 1.5, 2, 2.5, 3, 4, 5]
        yields = [100 * (1 - math.exp(-0.7 * r)) for r in ratios]
        fig = cls._base_line_figure("Solvent / solid ratio", "Extraction yield (%)")
        fig.add_trace(go.Scatter(x=ratios, y=yields, mode="lines+markers", name="Yield curve", line={"color": "#4fc3ff", "width": 3}))
        fig.add_trace(go.Scatter(x=[2.5], y=[actual_yield], mode="markers", name="Current result", marker={"size": 14, "color": "#ffb45c"}))
        return fig

    @classmethod
    def _plot_evaporation(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        feed = cls._num(form_data, "A_feed", 1000)
        xa = cls._num(form_data, "XA", 0.12)
        xb = max(cls._num(form_data, "XB", 0.45), 0.01)
        concentrate = xa * feed / xb
        vapor = max(feed - concentrate, 0)
        evap = [i * vapor / 10 for i in range(11)]
        concentration = [xa + (xb - xa) * (e / max(vapor, 1e-6)) for e in evap]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Concentration vs evaporated water", "Mass balance split"))
        fig.add_trace(go.Scatter(x=evap, y=concentration, mode="lines", name="XB trend", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Bar(x=["Feed A", "Concentrate B", "Vapor V"], y=[feed, concentrate, vapor], marker_color=["#4fc3ff", "#60f0b5", "#ffb45c"], name="Mass flows"), row=1, col=2)
        fig.update_xaxes(title="Evaporated water", row=1, col=1)
        fig.update_yaxes(title="Concentration", row=1, col=1)
        fig.update_yaxes(title="Flow", row=1, col=2)
        return fig

    @classmethod
    def _plot_drying(cls, form_data: Dict[str, Any], result: Dict[str, Any], **kwargs: Any) -> go.Figure:
        x_i = cls._num(form_data, "Xi", 0.35)
        x_f = cls._num(form_data, "Xf", 0.08)
        duration = max(cls._result_num(result, "Temps de séchage estimé") or 6 * 3600, 1)
        times = [duration * i / 10 for i in range(11)]
        moistures = [x_i - (x_i - x_f) * (i / 10) ** 0.85 for i in range(11)]
        rates = [max((moistures[i] - moistures[i + 1]) / max((times[i + 1] - times[i]), 1e-6), 0) for i in range(len(times) - 1)]
        avg_m = [(moistures[i] + moistures[i + 1]) / 2 for i in range(len(rates))]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Moisture content vs time", "Drying rate vs moisture"))
        fig.add_trace(go.Scatter(x=times, y=moistures, mode="lines+markers", name="X(t)", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=avg_m, y=rates, mode="lines+markers", name="Drying rate", line={"color": "#ffb45c", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Time", row=1, col=1)
        fig.update_yaxes(title="Moisture X", row=1, col=1)
        fig.update_xaxes(title="Moisture X", row=1, col=2)
        fig.update_yaxes(title="Rate", row=1, col=2)
        return fig

    @classmethod
    def _plot_psychrometric(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        pressure = cls._num(form_data, "P", 101.325)
        temp_range = list(range(0, 56, 2))
        fig = cls._base_line_figure("Dry bulb temperature Ts (°C)", "Humidity ratio w_g (g/kg dry air)")
        saturation = []
        for temp in temp_range:
            psat = PsychrometricService.saturation_pressure_tetens(temp)
            if psat >= pressure:
                saturation.append(None)
            else:
                saturation.append(PsychrometricService.humidity_ratio_from_vapor_pressure(psat, pressure) * 1000)
        fig.add_trace(go.Scatter(x=temp_range, y=saturation, mode="lines", name="Saturation 100%", line={"color": "#4fc3ff", "width": 4}))

        for hr in range(10, 100, 10):
            curve = []
            for temp in temp_range:
                psat = PsychrometricService.saturation_pressure_tetens(temp)
                pv = psat * hr / 100
                curve.append(PsychrometricService.humidity_ratio_from_vapor_pressure(pv, pressure) * 1000)
            fig.add_trace(go.Scatter(x=temp_range, y=curve, mode="lines", name=f"{hr}% RH", line={"width": 1}))

        ts = result.get("Ts")
        w_g = result.get("w_g")
        if ts is None and form_data.get("param1_type") == "Ts":
            ts = cls._num(form_data, "param1_value", 25)
        if ts is not None and w_g is not None:
            fig.add_trace(go.Scatter(x=[ts], y=[w_g], mode="markers+text", text=["A"], textposition="top center", name="Current point", marker={"size": 14, "color": "#ffb45c"}))
            fig.add_shape(type="line", x0=ts, x1=ts, y0=0, y1=w_g, line={"color": "rgba(255,180,92,0.55)", "dash": "dot"})
            fig.add_shape(type="line", x0=min(temp_range), x1=ts, y0=w_g, y1=w_g, line={"color": "rgba(255,180,92,0.55)", "dash": "dot"})
        return fig

    @classmethod
    def _plot_crystallization(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        c0 = cls._num(form_data, "C0", 120)
        ce = cls._num(form_data, "Ce", 80)
        delta_c = max(c0 - ce, 0)
        temps = list(range(10, 91, 10))
        solubility = [30 + 0.9 * t for t in temps]
        delta_range = [i for i in range(0, int(max(delta_c, 40)) + 5, 5)]
        jp = [0.02 * (d ** 1.6) for d in delta_range]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Solubility curve", "Nucleation rate vs supersaturation"))
        fig.add_trace(go.Scatter(x=temps, y=solubility, mode="lines", name="Csat(T)", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=[40], y=[c0], mode="markers", name="Current concentration", marker={"size": 14, "color": "#ffb45c"}), row=1, col=1)
        fig.add_trace(go.Scatter(x=delta_range, y=jp, mode="lines", name="Jp", line={"color": "#60f0b5", "width": 3}), row=1, col=2)
        fig.add_trace(go.Scatter(x=[delta_c], y=[0.02 * (delta_c ** 1.6) if delta_c > 0 else 0], mode="markers", name="Current ΔC", marker={"size": 12, "color": "#ff8d6b"}), row=1, col=2)
        fig.update_xaxes(title="Temperature", row=1, col=1)
        fig.update_yaxes(title="Solubility", row=1, col=1)
        fig.update_xaxes(title="ΔC", row=1, col=2)
        fig.update_yaxes(title="Nucleation rate", row=1, col=2)
        return fig

    @classmethod
    def _plot_reactors(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        xa = cls._result_num(result, "Conversion continue") or cls._result_num(result, "Conversion batch") or 0.6
        times = list(range(0, 11))
        batch = [xa * (1 - math.exp(-0.35 * t)) / (1 - math.exp(-0.35 * 10)) for t in times]
        volumes = [i for i in range(0, 51, 5)]
        pfr = [min(xa, xa * v / 50) for v in volumes]
        cstr = [xa * (1 - math.exp(-0.09 * v)) / (1 - math.exp(-0.09 * 50)) for v in volumes]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Batch XA vs time", "Continuous XA vs reactor volume"))
        fig.add_trace(go.Scatter(x=times, y=batch, mode="lines+markers", name="Batch", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=volumes, y=cstr, mode="lines", name="CSTR", line={"color": "#60f0b5", "width": 3}), row=1, col=2)
        fig.add_trace(go.Scatter(x=volumes, y=pfr, mode="lines", name="PFR", line={"color": "#ffb45c", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Time", row=1, col=1)
        fig.update_yaxes(title="XA", row=1, col=1)
        fig.update_xaxes(title="Volume", row=1, col=2)
        fig.update_yaxes(title="XA", row=1, col=2)
        return fig

    @classmethod
    def _plot_adsorption(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        qmax = cls._num(form_data, "qmax", 4)
        k_value = cls._num(form_data, "K", 0.8)
        kf = cls._num(form_data, "Kf", 2.2)
        n_value = max(cls._num(form_data, "n", 2), 0.2)
        concentrations = [i / 10 for i in range(1, 51)]
        langmuir = [(qmax * k_value * c) / (1 + k_value * c) for c in concentrations]
        freundlich = [kf * (c ** (1 / n_value)) for c in concentrations]
        times = list(range(0, 31))
        breakthrough = [1 / (1 + math.exp(-(t - 16) / 2.2)) for t in times]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Isotherms q vs C", "Breakthrough curve"))
        fig.add_trace(go.Scatter(x=concentrations, y=langmuir, mode="lines", name="Langmuir", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=concentrations, y=freundlich, mode="lines", name="Freundlich", line={"color": "#60f0b5", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=times, y=breakthrough, mode="lines", name="Cout/Cin", line={"color": "#ffb45c", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Concentration C", row=1, col=1)
        fig.update_yaxes(title="Adsorbed amount q", row=1, col=1)
        fig.update_xaxes(title="Time", row=1, col=2)
        fig.update_yaxes(title="Cout/Cin", row=1, col=2)
        return fig

    @classmethod
    def _plot_absorption(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        henry = cls._num(form_data, "H", 1.5)
        yin = cls._num(form_data, "yin", 0.18)
        yout = cls._num(form_data, "yout", 0.05)
        x_vals = [i / 100 for i in range(0, 31)]
        equilibrium = [henry * x for x in x_vals]
        operating = [yout + (yin - yout) * (1 - x / max(x_vals[-1], 1e-6)) for x in x_vals]
        fig = cls._base_line_figure("Liquid composition x", "Gas composition y")
        fig.add_trace(go.Scatter(x=x_vals, y=equilibrium, mode="lines", name="Equilibrium line", line={"color": "#4fc3ff", "width": 3}))
        fig.add_trace(go.Scatter(x=x_vals, y=operating, mode="lines", name="Operating line", line={"color": "#ffb45c", "width": 3}))
        return fig

    @classmethod
    def _plot_membranes(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        permeability = cls._num(form_data, "Pm", 2e-7)
        thickness = max(cls._num(form_data, "e", 0.0002), 1e-8)
        area = cls._num(form_data, "A", 40)
        delta_p = [i * 10000 for i in range(1, 11)]
        flux = [permeability * dp / thickness for dp in delta_p]
        areas = [i * 5 for i in range(1, 11)]
        q_permeate = [(permeability * cls._num(form_data, "deltaP", 50000) / thickness) * a for a in areas]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Flux J vs ΔP", "Permeate flow vs area"))
        fig.add_trace(go.Scatter(x=delta_p, y=flux, mode="lines", name="J", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=areas, y=q_permeate, mode="lines", name="Qp", line={"color": "#60f0b5", "width": 3}), row=1, col=2)
        fig.add_trace(go.Scatter(x=[area], y=[(permeability * cls._num(form_data, "deltaP", 50000) / thickness) * area], mode="markers", name="Current Qp", marker={"size": 12, "color": "#ffb45c"}), row=1, col=2)
        fig.update_xaxes(title="ΔP", row=1, col=1)
        fig.update_yaxes(title="J", row=1, col=1)
        fig.update_xaxes(title="Area", row=1, col=2)
        fig.update_yaxes(title="Qp", row=1, col=2)
        return fig

    @classmethod
    def _plot_heat_exchange(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        delta_t1 = cls._num(form_data, "deltaT1", 50)
        delta_t2 = cls._num(form_data, "deltaT2", 20)
        length = [i / 10 for i in range(11)]
        hot = [120 - 45 * x for x in length]
        cold_counter = [35 + 55 * x for x in reversed(length)]
        cold_co = [35 + 55 * x for x in length]
        fig = cls._base_line_figure("Normalized exchanger length", "Temperature")
        fig.add_trace(go.Scatter(x=length, y=hot, mode="lines", name="Hot stream", line={"color": "#ff8d6b", "width": 4}))
        fig.add_trace(go.Scatter(x=length, y=cold_counter, mode="lines", name="Cold stream counter-current", line={"color": "#4fc3ff", "width": 4}))
        fig.add_trace(go.Scatter(x=length, y=cold_co, mode="lines", name="Cold stream co-current", line={"color": "#60f0b5", "dash": "dash"}))
        lmtd = (delta_t1 - delta_t2) / math.log(delta_t1 / delta_t2) if delta_t1 != delta_t2 else delta_t1
        mid = (hot[5] + cold_counter[5]) / 2
        fig.add_annotation(text=f"LMTD ≈ {lmtd:.2f}", x=0.55, y=mid, showarrow=False, bgcolor="rgba(0,102,255,0.18)")
        return fig

    @classmethod
    def _plot_mixing(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        rho = cls._num(form_data, "rho", 1000)
        diameter = cls._num(form_data, "D", 0.4)
        mu = cls._num(form_data, "mu", 0.002)
        np_value = cls._num(form_data, "Np", 4.5)
        speeds = [i / 10 for i in range(1, 31)]
        re_vals = [rho * n * diameter ** 2 / mu for n in speeds]
        power = [np_value * rho * n ** 3 * diameter ** 5 for n in speeds]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Power vs N", "Agitator Reynolds vs N"))
        fig.add_trace(go.Scatter(x=speeds, y=power, mode="lines", name="Power", line={"color": "#ffb45c", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=speeds, y=re_vals, mode="lines", name="Re", line={"color": "#4fc3ff", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="N (s⁻¹)", row=1, col=1)
        fig.update_yaxes(title="Power", row=1, col=1)
        fig.update_xaxes(title="N (s⁻¹)", row=1, col=2)
        fig.update_yaxes(title="Re", row=1, col=2)
        return fig

    @classmethod
    def _plot_grinding(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        wi = cls._num(form_data, "Wi", 12)
        f80 = max(cls._num(form_data, "F80", 1500), 1)
        p80_values = list(range(100, int(f80), 100))
        energies = [wi * (10 / math.sqrt(p) - 10 / math.sqrt(f80)) for p in p80_values]
        current_p80 = cls._num(form_data, "P80", 400)
        current_energy = wi * (10 / math.sqrt(current_p80) - 10 / math.sqrt(f80))
        fig = cls._base_line_figure("Product size P80", "Energy E")
        fig.add_trace(go.Scatter(x=p80_values, y=energies, mode="lines", name="Bond law", line={"color": "#4fc3ff", "width": 3}))
        fig.add_trace(go.Scatter(x=[current_p80], y=[current_energy], mode="markers", name="Current point", marker={"size": 14, "color": "#ffb45c"}))
        return fig

    @classmethod
    def _plot_screening(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        rows = result.get("table_rows") or []
        if rows:
            sizes = [float(row["size"]) for row in rows]
            passing = [float(row["cumulative_passing"]) for row in rows]
        else:
            sizes = [4, 2, 1, 0.5, 0.25, 0.125]
            passing = [100, 84, 61, 38, 17, 5]
        fig = cls._base_line_figure("Sieve size", "Cumulative passing (%)")
        fig.add_trace(go.Scatter(x=sizes, y=passing, mode="lines+markers", name="Cumulative passing", line={"color": "#4fc3ff", "width": 3}))
        fig.update_xaxes(type="log")
        return fig

    @classmethod
    def _plot_fluidization(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        umf = cls._num(form_data, "umf", 0.35)
        rho_s = cls._num(form_data, "rho_s", 2400)
        rho_f = cls._num(form_data, "rho_f", 1.2)
        epsilon = cls._num(form_data, "epsilon", 0.42)
        height = cls._num(form_data, "H", 1.5)
        velocities = [i / 20 for i in range(1, 31)]
        delta_plateau = (rho_s - rho_f) * (1 - epsilon) * 9.81 * height
        delta_p = [delta_plateau * min(v / max(umf, 1e-6), 1) for v in velocities]
        fig = cls._base_line_figure("Gas velocity u", "Pressure drop ΔP")
        fig.add_trace(go.Scatter(x=velocities, y=delta_p, mode="lines", name="ΔP(u)", line={"color": "#4fc3ff", "width": 3}))
        fig.add_vline(x=umf, line_dash="dash", line_color="#ffb45c", annotation_text="umf")
        return fig

    @classmethod
    def _plot_fluid_transport(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        rho = cls._num(form_data, "rho", 998)
        diameter = cls._num(form_data, "D", 0.08)
        mu = cls._num(form_data, "mu", 0.001)
        length = cls._num(form_data, "L", 25)
        f_value = cls._num(form_data, "f", 0.03)
        velocities = [i / 5 for i in range(1, 21)]
        area = math.pi * diameter ** 2 / 4
        flow_rates = [v * area for v in velocities]
        pressure_drop = [f_value * (length / diameter) * (rho * v ** 2 / 2) for v in velocities]
        reynolds = [rho * v * diameter / mu for v in velocities]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Pressure drop vs flow rate", "Reynolds vs flow rate"))
        fig.add_trace(go.Scatter(x=flow_rates, y=pressure_drop, mode="lines", name="ΔP", line={"color": "#4fc3ff", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=flow_rates, y=reynolds, mode="lines", name="Re", line={"color": "#ffb45c", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Flow rate Q", row=1, col=1)
        fig.update_yaxes(title="ΔP", row=1, col=1)
        fig.update_xaxes(title="Flow rate Q", row=1, col=2)
        fig.update_yaxes(title="Re", row=1, col=2)
        return fig

    @classmethod
    def _plot_pumps(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        rho = cls._num(form_data, "rho", 1000)
        head = cls._num(form_data, "H", 25)
        eta = max(cls._num(form_data, "eta", 0.72), 0.05)
        flows = [i / 100 for i in range(1, 21)]
        power = [rho * 9.81 * q * head / eta for q in flows]
        h_curve = [head * (1 - 0.55 * (q / max(flows))) for q in flows]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Pump power vs flow rate", "Placeholder H-Q curve"))
        fig.add_trace(go.Scatter(x=flows, y=power, mode="lines", name="Power", line={"color": "#ffb45c", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=flows, y=h_curve, mode="lines", name="Head", line={"color": "#4fc3ff", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Q", row=1, col=1)
        fig.update_yaxes(title="Power", row=1, col=1)
        fig.update_xaxes(title="Q", row=1, col=2)
        fig.update_yaxes(title="Head", row=1, col=2)
        return fig

    @classmethod
    def _plot_cyclones(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        rho = cls._num(form_data, "rho", 1.2)
        coefficient = cls._num(form_data, "K", 6)
        velocities = [i for i in range(5, 31, 2)]
        delta_p = [coefficient * (rho * v ** 2 / 2) for v in velocities]
        diameters = [1, 2, 3, 5, 8, 12, 20, 30, 45, 60]
        efficiency = [1 - math.exp(-0.04 * d) for d in diameters]
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Efficiency vs particle diameter", "Pressure drop vs inlet velocity"))
        fig.add_trace(go.Scatter(x=diameters, y=efficiency, mode="lines+markers", name="Efficiency", line={"color": "#60f0b5", "width": 3}), row=1, col=1)
        fig.add_trace(go.Scatter(x=velocities, y=delta_p, mode="lines", name="ΔP", line={"color": "#4fc3ff", "width": 3}), row=1, col=2)
        fig.update_xaxes(title="Particle diameter", row=1, col=1)
        fig.update_yaxes(title="Efficiency", row=1, col=1)
        fig.update_xaxes(title="Inlet velocity", row=1, col=2)
        fig.update_yaxes(title="ΔP", row=1, col=2)
        return fig

    @classmethod
    def _plot_humidification(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        yin = cls._num(form_data, "Yin", 0.007)
        yout = cls._num(form_data, "Yout", 0.013)
        h_in = cls._num(form_data, "hin", 28)
        h_out = cls._num(form_data, "hout", 44)
        fig = make_subplots(rows=1, cols=2, subplot_titles=("Humidity ratio before / after", "Process path in h-w space"))
        fig.add_trace(go.Bar(x=["Inlet", "Outlet"], y=[yin * 1000, yout * 1000], marker_color=["#4fc3ff", "#60f0b5"], name="w_g"), row=1, col=1)
        fig.add_trace(go.Scatter(x=[yin * 1000, yout * 1000], y=[h_in, h_out], mode="lines+markers+text", text=["In", "Out"], textposition="top center", name="Process path", line={"color": "#ffb45c", "width": 3}), row=1, col=2)
        fig.update_yaxes(title="w_g", row=1, col=1)
        fig.update_xaxes(title="State", row=1, col=1)
        fig.update_xaxes(title="w_g", row=1, col=2)
        fig.update_yaxes(title="h", row=1, col=2)
        return fig

    @classmethod
    def _plot_placeholder(cls, form_data: Dict[str, Any], result: Dict[str, Any], **_: Any) -> go.Figure:
        fig = cls._base_line_figure("Input", "Output")
        fig.add_trace(go.Scatter(x=[0, 1, 2], y=[0, 1, 1.5], mode="lines", line={"color": "#4fc3ff", "width": 3}, name="Placeholder"))
        return fig
