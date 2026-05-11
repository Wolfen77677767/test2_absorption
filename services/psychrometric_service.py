"""
Psychrometric calculations service.

This module computes a psychrometric state numerically from two known
properties, replacing manual use of the psychrometric chart.
"""

from __future__ import annotations

import math
from typing import Any, Dict, List, Optional, Tuple


class PsychrometricService:
    """Service for moist-air psychrometric calculations."""

    P_ATM_DEFAULT = 101.325
    R_AIR = 0.287042
    EPS = 1e-9

    PARAMETER_OPTIONS = [
        {"value": "Ts", "label": "Dry bulb temperature Ts (°C)"},
        {"value": "Th", "label": "Wet bulb temperature Th (°C)"},
        {"value": "Tr", "label": "Dew point Tr (°C)"},
        {"value": "HR", "label": "Relative humidity HR (%)"},
        {"value": "w", "label": "Humidity ratio w (kg/kg dry air)"},
        {"value": "w_g", "label": "Humidity ratio w_g (g/kg dry air)"},
        {"value": "h", "label": "Enthalpy h (kJ/kg dry air)"},
        {"value": "Vs", "label": "Specific volume Vs (m³/kg dry air)"},
        {"value": "Pv", "label": "Vapor partial pressure Pv (kPa)"},
        {"value": "Psat", "label": "Saturation pressure Psat (kPa)"},
        {"value": "rho", "label": "Humid air density rho (kg/m³)"},
    ]

    @staticmethod
    def _fmt(value: float, digits: int = 6) -> str:
        return f"{value:.{digits}f}".rstrip("0").rstrip(".")

    @classmethod
    def get_parameter_options(cls) -> List[Dict[str, str]]:
        return cls.PARAMETER_OPTIONS

    @staticmethod
    def saturation_pressure_tetens(temp_c: float) -> float:
        if temp_c < -80 or temp_c > 120:
            raise ValueError("Temperature is outside the supported range for this saturation-pressure correlation.")
        return 0.61078 * math.exp((17.27 * temp_c) / (temp_c + 237.3))

    @staticmethod
    def dew_point_from_vapor_pressure(vapor_pressure: float) -> float:
        if vapor_pressure <= 0:
            raise ValueError("Pv must be positive.")
        gamma = math.log(vapor_pressure / 0.61078)
        return (237.3 * gamma) / (17.27 - gamma)

    @staticmethod
    def humidity_ratio_from_vapor_pressure(vapor_pressure: float, pressure: float) -> float:
        if pressure <= 0:
            raise ValueError("P must be positive.")
        if vapor_pressure <= 0:
            raise ValueError("Pv must be positive.")
        if vapor_pressure >= pressure:
            raise ValueError("Pv must remain below total pressure P.")
        return 0.62198 * vapor_pressure / (pressure - vapor_pressure)

    @staticmethod
    def vapor_pressure_from_humidity_ratio(humidity_ratio: float, pressure: float) -> float:
        if pressure <= 0:
            raise ValueError("P must be positive.")
        if humidity_ratio < 0:
            raise ValueError("w cannot be negative.")
        return humidity_ratio * pressure / (0.62198 + humidity_ratio)

    @staticmethod
    def enthalpy(temp_c: float, humidity_ratio: float) -> float:
        return 1.006 * temp_c + humidity_ratio * (2501 + 1.86 * temp_c)

    @classmethod
    def specific_volume(cls, temp_c: float, humidity_ratio: float, pressure: float) -> float:
        if pressure <= 0:
            raise ValueError("P must be positive.")
        return cls.R_AIR * (temp_c + 273.15) * (1 + 1.607858 * humidity_ratio) / pressure

    @classmethod
    def density(cls, temp_c: float, humidity_ratio: float, pressure: float) -> float:
        volume = cls.specific_volume(temp_c, humidity_ratio, pressure)
        if volume <= 0:
            raise ValueError("Specific volume must be positive.")
        return (1 + humidity_ratio) / volume

    @classmethod
    def relative_humidity(cls, temp_c: float, vapor_pressure: float) -> float:
        psat = cls.saturation_pressure_tetens(temp_c)
        return vapor_pressure / psat * 100

    @classmethod
    def humidity_ratio_from_wet_bulb_saturation(cls, wet_bulb_temp: float, pressure: float) -> float:
        psat = cls.saturation_pressure_tetens(wet_bulb_temp)
        if psat >= pressure:
            psat = pressure * 0.999
        return cls.humidity_ratio_from_vapor_pressure(psat, pressure)

    @classmethod
    def saturated_enthalpy(cls, wet_bulb_temp: float, pressure: float) -> float:
        humidity_ratio = cls.humidity_ratio_from_wet_bulb_saturation(wet_bulb_temp, pressure)
        return cls.enthalpy(wet_bulb_temp, humidity_ratio)

    @classmethod
    def estimate_wet_bulb(cls, temp_dry: float, humidity_ratio: float, pressure: float) -> Tuple[Optional[float], Optional[str]]:
        enthalpy_actual = cls.enthalpy(temp_dry, humidity_ratio)
        low = min(-20.0, temp_dry)
        high = temp_dry

        try:
            h_low = cls.saturated_enthalpy(low, pressure)
            h_high = cls.saturated_enthalpy(high, pressure)
        except Exception:
            return None, "Unable to evaluate wet-bulb search bounds."

        if enthalpy_actual < h_low - 1e-6 or enthalpy_actual > h_high + 1e-6:
            return None, "Wet-bulb temperature could not be estimated reliably from the current state."

        for _ in range(80):
            mid = (low + high) / 2
            h_mid = cls.saturated_enthalpy(mid, pressure)
            if abs(h_mid - enthalpy_actual) < 1e-5:
                return mid, None
            if h_mid > enthalpy_actual:
                high = mid
            else:
                low = mid

        estimate = (low + high) / 2
        if estimate > temp_dry:
            return None, "Estimated wet-bulb temperature exceeded dry-bulb temperature."
        return estimate, None

    @classmethod
    def inverse_saturation_pressure(cls, target_psat: float) -> float:
        if target_psat <= 0:
            raise ValueError("Psat must be positive.")
        low = -80.0
        high = 120.0
        for _ in range(100):
            mid = (low + high) / 2
            value = cls.saturation_pressure_tetens(mid)
            if value > target_psat:
                high = mid
            else:
                low = mid
        return (low + high) / 2

    @classmethod
    def _normalize_inputs(cls, inputs: Dict[str, Any]) -> Tuple[Dict[str, float], float]:
        known: Dict[str, float] = {}
        pressure = cls.P_ATM_DEFAULT

        for raw_key, raw_value in inputs.items():
            if raw_value in (None, ""):
                continue
            key = str(raw_key).strip()
            if not key:
                continue
            try:
                value = float(raw_value)
            except (TypeError, ValueError) as exc:
                raise ValueError(f"Invalid numeric value for {key}.") from exc

            if key == "P":
                pressure = value
                continue
            if key == "Y":
                key = "w"
            if key == "Yg":
                key = "w_g"
            known[key] = value

        if "w_g" in known and "w" not in known:
            known["w"] = known["w_g"] / 1000.0
            del known["w_g"]

        return known, pressure

    @classmethod
    def _state_from_ts_w(cls, temp_dry: float, humidity_ratio: float, pressure: float) -> Tuple[Dict[str, float], List[str]]:
        if pressure <= 0:
            raise ValueError("P must be positive.")
        if humidity_ratio < 0:
            raise ValueError("w cannot be negative.")

        vapor_pressure = cls.vapor_pressure_from_humidity_ratio(humidity_ratio, pressure)
        psat = cls.saturation_pressure_tetens(temp_dry)
        if vapor_pressure >= pressure:
            raise ValueError("Pv must remain below P.")
        if vapor_pressure > psat + 1e-8:
            raise ValueError("The state is physically impossible because Pv exceeds Psat(Ts).")

        relative_humidity = cls.relative_humidity(temp_dry, vapor_pressure)
        dew_point = cls.dew_point_from_vapor_pressure(vapor_pressure)
        enthalpy_value = cls.enthalpy(temp_dry, humidity_ratio)
        specific_volume = cls.specific_volume(temp_dry, humidity_ratio, pressure)
        density_value = cls.density(temp_dry, humidity_ratio, pressure)
        wet_bulb, wet_bulb_warning = cls.estimate_wet_bulb(temp_dry, humidity_ratio, pressure)

        warnings: List[str] = []
        if wet_bulb_warning:
            warnings.append(wet_bulb_warning)
        if wet_bulb is not None and wet_bulb > temp_dry + 1e-6:
            raise ValueError("Estimated wet-bulb temperature is higher than dry-bulb temperature.")
        if dew_point > temp_dry + 1e-6:
            raise ValueError("Dew point cannot exceed dry-bulb temperature.")

        return (
            {
                "Ts": temp_dry,
                "Th": wet_bulb,
                "Tr": dew_point,
                "HR": relative_humidity,
                "w": humidity_ratio,
                "w_g": humidity_ratio * 1000,
                "h": enthalpy_value,
                "Vs": specific_volume,
                "Pv": vapor_pressure,
                "Psat": psat,
                "rho": density_value,
                "P": pressure,
            },
            warnings,
        )

    @classmethod
    def _temperature_from_h_and_w(cls, enthalpy_value: float, humidity_ratio: float) -> float:
        denominator = 1.006 + 1.86 * humidity_ratio
        if abs(denominator) < cls.EPS:
            raise ValueError("Cannot recover Ts from h and w.")
        return (enthalpy_value - 2501 * humidity_ratio) / denominator

    @classmethod
    def _temperature_from_vs_and_w(cls, specific_volume: float, humidity_ratio: float, pressure: float) -> float:
        denominator = cls.R_AIR * (1 + 1.607858 * humidity_ratio)
        if abs(denominator) < cls.EPS:
            raise ValueError("Cannot recover Ts from Vs and w.")
        return specific_volume * pressure / denominator - 273.15

    @classmethod
    def _humidity_ratio_from_vs(cls, temp_dry: float, specific_volume: float, pressure: float) -> float:
        numerator = specific_volume * pressure / (cls.R_AIR * (temp_dry + 273.15)) - 1
        return numerator / 1.607858

    @classmethod
    def _humidity_ratio_from_rho(cls, temp_dry: float, density_value: float, pressure: float) -> float:
        if density_value <= 0:
            raise ValueError("rho must be positive.")
        a_value = density_value * cls.R_AIR * (temp_dry + 273.15) / pressure
        denominator = 1.607858 * a_value - 1
        if abs(denominator) < cls.EPS:
            raise ValueError("Cannot recover w from Ts and rho.")
        return (1 - a_value) / denominator

    @classmethod
    def _property_value(cls, key: str, temp_dry: float, humidity_ratio: float, pressure: float) -> float:
        state, _ = cls._state_from_ts_w(temp_dry, humidity_ratio, pressure)
        value = state.get(key)
        if value is None:
            raise ValueError(f"Property {key} is unavailable for the current state.")
        return value

    @classmethod
    def _residuals(
        cls,
        pair: List[Tuple[str, float]],
        temp_dry: float,
        humidity_ratio: float,
        pressure: float,
    ) -> Tuple[float, float]:
        residual_values = []
        for key, target in pair:
            current = cls._property_value(key, temp_dry, humidity_ratio, pressure)
            scale = max(abs(target), 1.0)
            residual_values.append((current - target) / scale)
        return residual_values[0], residual_values[1]

    @classmethod
    def _newton_solve(
        cls,
        pair: List[Tuple[str, float]],
        pressure: float,
        temp_seed: float,
        humidity_seed: float,
    ) -> Optional[Tuple[float, float]]:
        temp_dry = temp_seed
        humidity_ratio = max(0.0, humidity_seed)

        for _ in range(30):
            try:
                r1, r2 = cls._residuals(pair, temp_dry, humidity_ratio, pressure)
            except Exception:
                return None

            if max(abs(r1), abs(r2)) < 1e-7:
                return temp_dry, humidity_ratio

            dt = max(1e-4, abs(temp_dry) * 1e-4)
            dw = max(1e-6, max(humidity_ratio, 1e-3) * 1e-4)

            try:
                r1_t, r2_t = cls._residuals(pair, temp_dry + dt, humidity_ratio, pressure)
                r1_w, r2_w = cls._residuals(pair, temp_dry, humidity_ratio + dw, pressure)
            except Exception:
                return None

            j11 = (r1_t - r1) / dt
            j21 = (r2_t - r2) / dt
            j12 = (r1_w - r1) / dw
            j22 = (r2_w - r2) / dw
            determinant = j11 * j22 - j12 * j21
            if abs(determinant) < 1e-12:
                return None

            delta_t = (-r1 * j22 + r2 * j12) / determinant
            delta_w = (-j11 * r2 + j21 * r1) / determinant

            improved = False
            current_norm = max(abs(r1), abs(r2))
            for damping in [1.0, 0.5, 0.25, 0.1, 0.05]:
                trial_t = temp_dry + damping * delta_t
                trial_w = max(0.0, humidity_ratio + damping * delta_w)
                try:
                    tr1, tr2 = cls._residuals(pair, trial_t, trial_w, pressure)
                    trial_norm = max(abs(tr1), abs(tr2))
                except Exception:
                    continue
                if trial_norm < current_norm:
                    temp_dry = trial_t
                    humidity_ratio = trial_w
                    improved = True
                    break

            if not improved:
                return None

        return None

    @classmethod
    def _solve_generic(cls, known: Dict[str, float], pressure: float) -> Optional[Tuple[float, float]]:
        pair = list(known.items())
        temp_seeds: List[float] = []
        humidity_seeds: List[float] = []

        if "Ts" in known:
            temp_seeds.append(known["Ts"])
        if "Psat" in known:
            temp_seeds.append(cls.inverse_saturation_pressure(known["Psat"]))
        if "Tr" in known:
            temp_seeds.extend([known["Tr"], known["Tr"] + 5.0, known["Tr"] + 15.0])
        if "Th" in known:
            temp_seeds.extend([known["Th"], known["Th"] + 5.0, known["Th"] + 15.0])
        temp_seeds.extend([0.0, 10.0, 25.0, 40.0, 60.0])

        if "w" in known:
            humidity_seeds.append(known["w"])
        if "w_g" in known:
            humidity_seeds.append(known["w_g"] / 1000.0)
        if "Pv" in known:
            humidity_seeds.append(cls.humidity_ratio_from_vapor_pressure(known["Pv"], pressure))
        if "Tr" in known:
            dew_pv = cls.saturation_pressure_tetens(known["Tr"])
            humidity_seeds.append(cls.humidity_ratio_from_vapor_pressure(dew_pv, pressure))
        humidity_seeds.extend([0.001, 0.005, 0.01, 0.02])

        dedup_t: List[float] = []
        for seed in temp_seeds:
            if not any(abs(seed - existing) < 1e-6 for existing in dedup_t):
                dedup_t.append(seed)

        dedup_w: List[float] = []
        for seed in humidity_seeds:
            if seed < 0:
                continue
            if not any(abs(seed - existing) < 1e-8 for existing in dedup_w):
                dedup_w.append(seed)

        for temp_seed in dedup_t:
            for humidity_seed in dedup_w:
                solution = cls._newton_solve(pair, pressure, temp_seed, humidity_seed)
                if solution is not None:
                    return solution
        return None

    @classmethod
    def _direct_solution(cls, known: Dict[str, float], pressure: float) -> Optional[Tuple[float, float, List[str]]]:
        steps: List[str] = []

        if "Ts" in known and "w" in known:
            return known["Ts"], known["w"], steps

        if "Ts" in known and "w_g" in known:
            humidity_ratio = known["w_g"] / 1000.0
            steps.append(f"w = w_g / 1000 = {cls._fmt(known['w_g'])} / 1000 = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "Pv" in known:
            humidity_ratio = cls.humidity_ratio_from_vapor_pressure(known["Pv"], pressure)
            steps.append(f"w = 0.62198 * Pv / (P - Pv) = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "HR" in known:
            if known["HR"] < 0 or known["HR"] > 100:
                raise ValueError("HR must remain between 0 and 100%.")
            psat = cls.saturation_pressure_tetens(known["Ts"])
            vapor_pressure = known["HR"] / 100.0 * psat
            humidity_ratio = cls.humidity_ratio_from_vapor_pressure(vapor_pressure, pressure)
            steps.append(f"Psat(Ts) = {cls._fmt(psat)} kPa")
            steps.append(f"Pv = HR/100 * Psat = {cls._fmt(vapor_pressure)} kPa")
            steps.append(f"w = 0.62198 * Pv / (P - Pv) = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "Tr" in known:
            vapor_pressure = cls.saturation_pressure_tetens(known["Tr"])
            humidity_ratio = cls.humidity_ratio_from_vapor_pressure(vapor_pressure, pressure)
            steps.append(f"Pv = Psat(Tr) = {cls._fmt(vapor_pressure)} kPa")
            steps.append(f"w = 0.62198 * Pv / (P - Pv) = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "h" in known:
            humidity_ratio = (known["h"] - 1.006 * known["Ts"]) / (2501 + 1.86 * known["Ts"])
            steps.append(f"w = (h - 1.006*Ts) / (2501 + 1.86*Ts) = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "Vs" in known:
            humidity_ratio = cls._humidity_ratio_from_vs(known["Ts"], known["Vs"], pressure)
            steps.append(f"w = (Vs * P / (0.287042*(Ts + 273.15)) - 1) / 1.607858 = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "Th" in known:
            wet_bulb = known["Th"]
            if wet_bulb > known["Ts"]:
                raise ValueError("Th must be less than or equal to Ts.")
            target_h = cls.saturated_enthalpy(wet_bulb, pressure)
            humidity_ratio = (target_h - 1.006 * known["Ts"]) / (2501 + 1.86 * known["Ts"])
            steps.append(f"h_saturated(Th) = {cls._fmt(target_h)} kJ/kg dry air")
            steps.append(f"w = (h_saturated(Th) - 1.006*Ts) / (2501 + 1.86*Ts) = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "Ts" in known and "rho" in known:
            humidity_ratio = cls._humidity_ratio_from_rho(known["Ts"], known["rho"], pressure)
            steps.append(f"w solved from rho = (1 + w) / Vs = {cls._fmt(humidity_ratio)} kg/kg dry air")
            return known["Ts"], humidity_ratio, steps

        if "w" in known and "h" in known:
            temp_dry = cls._temperature_from_h_and_w(known["h"], known["w"])
            steps.append(f"Ts = (h - 2501*w) / (1.006 + 1.86*w) = {cls._fmt(temp_dry)} °C")
            return temp_dry, known["w"], steps

        if "w_g" in known and "h" in known:
            humidity_ratio = known["w_g"] / 1000.0
            temp_dry = cls._temperature_from_h_and_w(known["h"], humidity_ratio)
            steps.append(f"w = {cls._fmt(known['w_g'])} / 1000 = {cls._fmt(humidity_ratio)} kg/kg dry air")
            steps.append(f"Ts = (h - 2501*w) / (1.006 + 1.86*w) = {cls._fmt(temp_dry)} °C")
            return temp_dry, humidity_ratio, steps

        if "w" in known and "Vs" in known:
            temp_dry = cls._temperature_from_vs_and_w(known["Vs"], known["w"], pressure)
            steps.append(f"Ts = Vs * P / (0.287042*(1 + 1.607858*w)) - 273.15 = {cls._fmt(temp_dry)} °C")
            return temp_dry, known["w"], steps

        if "w" in known and "Pv" in known:
            target_w = cls.humidity_ratio_from_vapor_pressure(known["Pv"], pressure)
            if abs(target_w - known["w"]) > 1e-6:
                raise ValueError("The provided w and Pv are inconsistent.")
            return None

        if "w" in known and "Tr" in known:
            vapor_pressure = cls.saturation_pressure_tetens(known["Tr"])
            target_w = cls.humidity_ratio_from_vapor_pressure(vapor_pressure, pressure)
            if abs(target_w - known["w"]) > 1e-6:
                raise ValueError("The provided w and Tr are inconsistent.")
            return None

        if "HR" in known and "w" in known:
            vapor_pressure = cls.vapor_pressure_from_humidity_ratio(known["w"], pressure)
            psat = vapor_pressure / (known["HR"] / 100.0)
            temp_dry = cls.inverse_saturation_pressure(psat)
            steps.append(f"Pv from w = {cls._fmt(vapor_pressure)} kPa")
            steps.append(f"Psat = Pv / (HR/100) = {cls._fmt(psat)} kPa")
            steps.append(f"Ts from Psat(Ts) = {cls._fmt(temp_dry)} °C")
            return temp_dry, known["w"], steps

        if "HR" in known and "w_g" in known:
            humidity_ratio = known["w_g"] / 1000.0
            vapor_pressure = cls.vapor_pressure_from_humidity_ratio(humidity_ratio, pressure)
            psat = vapor_pressure / (known["HR"] / 100.0)
            temp_dry = cls.inverse_saturation_pressure(psat)
            steps.append(f"w = {cls._fmt(humidity_ratio)} kg/kg dry air")
            steps.append(f"Pv from w = {cls._fmt(vapor_pressure)} kPa")
            steps.append(f"Ts from Psat(Ts) = {cls._fmt(temp_dry)} °C")
            return temp_dry, humidity_ratio, steps

        if "h" in known and "Pv" in known:
            humidity_ratio = cls.humidity_ratio_from_vapor_pressure(known["Pv"], pressure)
            temp_dry = cls._temperature_from_h_and_w(known["h"], humidity_ratio)
            steps.append(f"w from Pv = {cls._fmt(humidity_ratio)} kg/kg dry air")
            steps.append(f"Ts from h and w = {cls._fmt(temp_dry)} °C")
            return temp_dry, humidity_ratio, steps

        if "h" in known and "Tr" in known:
            vapor_pressure = cls.saturation_pressure_tetens(known["Tr"])
            humidity_ratio = cls.humidity_ratio_from_vapor_pressure(vapor_pressure, pressure)
            temp_dry = cls._temperature_from_h_and_w(known["h"], humidity_ratio)
            steps.append(f"Pv = Psat(Tr) = {cls._fmt(vapor_pressure)} kPa")
            steps.append(f"w from Pv = {cls._fmt(humidity_ratio)} kg/kg dry air")
            steps.append(f"Ts from h and w = {cls._fmt(temp_dry)} °C")
            return temp_dry, humidity_ratio, steps

        return None

    @classmethod
    def calculate_psychrometric_properties(cls, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        try:
            if args and isinstance(args[0], dict):
                raw_inputs = dict(args[0])
            else:
                if len(args) < 4:
                    raise ValueError("Expected either an inputs dict or two parameter/value pairs.")
                raw_inputs = {
                    str(args[0]): args[1],
                    str(args[2]): args[3],
                }
                raw_inputs["P"] = args[4] if len(args) > 4 else kwargs.get("pressure", cls.P_ATM_DEFAULT)

            input_used_w_g = "w_g" in raw_inputs or "Yg" in raw_inputs
            known, pressure = cls._normalize_inputs(raw_inputs)
            if pressure <= 0:
                return {"error": "P must be positive."}
            if len(known) != 2:
                return {"error": "Please provide exactly two known psychrometric properties."}

            direct = cls._direct_solution(known, pressure)
            steps: List[str] = []
            if direct is not None:
                temp_dry, humidity_ratio, steps = direct
            else:
                solution = cls._solve_generic(known, pressure)
                if solution is None:
                    return {
                        "error": "Unable to determine a unique psychrometric state from the selected pair. Try another physically independent combination."
                    }
                temp_dry, humidity_ratio = solution
                steps.append("Ts and w were obtained by numerical resolution from the two selected known properties.")

            state, warnings = cls._state_from_ts_w(temp_dry, humidity_ratio, pressure)
            if state["HR"] < -1e-6 or state["HR"] > 100 + 1e-6:
                return {"error": "Computed HR is physically impossible."}
            if state["Pv"] <= 0:
                return {"error": "Computed Pv is physically impossible."}
            if state["Pv"] >= pressure:
                return {"error": "Computed Pv must remain below total pressure P."}
            if state["Th"] is not None and state["Th"] > state["Ts"] + 1e-6:
                return {"error": "Computed Th cannot exceed Ts."}
            if state["Tr"] > state["Ts"] + 1e-6:
                return {"error": "Computed Tr cannot exceed Ts."}

            formulas = [
                "Psat(T) = 0.61078 * exp((17.27*T)/(T + 237.3))",
                "Pv = HR/100 * Psat(Ts)",
                "w = 0.62198 * Pv / (P - Pv)",
                "w_g = w * 1000",
                "h = 1.006*Ts + w*(2501 + 1.86*Ts)",
                "Vs = 0.287042*(Ts + 273.15)*(1 + 1.607858*w)/P",
                "gamma = ln(Pv / 0.61078)",
                "Tr = (237.3 * gamma) / (17.27 - gamma)",
                "rho = (1 + w) / Vs",
                "Th solved numerically from h_actual ≈ h_saturated(Th)",
            ]

            known_labels = {
                "Ts": "Ts",
                "Th": "Th",
                "Tr": "Tr",
                "HR": "HR",
                "w": "w",
                "w_g": "w_g",
                "h": "h",
                "Vs": "Vs",
                "Pv": "Pv",
                "Psat": "Psat",
                "rho": "rho",
            }

            inputs = [
                {"label": known_labels[key], "value": cls._fmt(value), "unit": ""}
                for key, value in known.items()
            ]
            inputs.append({"label": "P", "value": cls._fmt(pressure), "unit": "kPa"})

            if input_used_w_g:
                warnings.append("w_g input was converted internally to w in kg/kg dry air.")

            results = [
                {"label": "Ts", "value": cls._fmt(state["Ts"]), "unit": "°C", "formula": "Dry bulb temperature"},
                {"label": "Th", "value": cls._fmt(state["Th"]) if state["Th"] is not None else "Unavailable", "unit": "°C" if state["Th"] is not None else "", "formula": "Solved from h_actual ≈ h_saturated(Th)"},
                {"label": "Tr", "value": cls._fmt(state["Tr"]), "unit": "°C", "formula": "Tr = (237.3 * gamma) / (17.27 - gamma)"},
                {"label": "HR", "value": cls._fmt(state["HR"]), "unit": "%", "formula": "HR = Pv / Psat * 100"},
                {"label": "w", "value": cls._fmt(state["w"]), "unit": "kg/kg dry air", "formula": "w = 0.62198 * Pv / (P - Pv)"},
                {"label": "w_g", "value": cls._fmt(state["w_g"]), "unit": "g/kg dry air", "formula": "w_g = w * 1000"},
                {"label": "h", "value": cls._fmt(state["h"]), "unit": "kJ/kg dry air", "formula": "h = 1.006*Ts + w*(2501 + 1.86*Ts)"},
                {"label": "Vs", "value": cls._fmt(state["Vs"]), "unit": "m³/kg dry air", "formula": "Vs = 0.287042*(Ts + 273.15)*(1 + 1.607858*w)/P"},
                {"label": "Pv", "value": cls._fmt(state["Pv"]), "unit": "kPa", "formula": "Derived vapor partial pressure"},
                {"label": "Psat", "value": cls._fmt(state["Psat"]), "unit": "kPa", "formula": "Psat(Ts)"},
                {"label": "rho", "value": cls._fmt(state["rho"]), "unit": "kg/m³", "formula": "rho = (1 + w) / Vs"},
            ]

            response: Dict[str, Any] = {
                "success": True,
                "inputs": inputs,
                "steps": steps,
                "warnings": warnings,
                "results": results,
                "formulas_used": formulas,
                "properties": state,
            }
            response.update(state)
            return response
        except (ValueError, ZeroDivisionError, OverflowError) as exc:
            return {"error": str(exc)}
