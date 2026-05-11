import json
import logging
from datetime import datetime

from models.user import db

logger = logging.getLogger(__name__)


def _serialize_payload(payload):
    return json.dumps(payload or {}, ensure_ascii=False, default=str)


def _deserialize_payload(payload):
    if not payload:
        return {}

    try:
        return json.loads(payload)
    except (TypeError, json.JSONDecodeError):
        return {}


def _format_number(value):
    if isinstance(value, float):
        return f"{value:.4f}"
    return value


class Calculation(db.Model):
    __tablename__ = "calculations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    process_type = db.Column(db.String(20), nullable=False)
    mode = db.Column(db.String(20), nullable=True)
    parameters_json = db.Column(db.Text, nullable=False, default="{}")
    result_json = db.Column(db.Text, nullable=False, default="{}")
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    user = db.relationship("User", backref=db.backref("calculations", lazy="dynamic"))

    @property
    def parameters(self):
        return _deserialize_payload(self.parameters_json)

    @property
    def result(self):
        return _deserialize_payload(self.result_json)

    def to_history_item(self):
        parameters = self.parameters
        result = self.result
        timestamp = self.created_at.strftime("%Y-%m-%d %H:%M:%S") if self.created_at else ""
        mode_label = (self.mode or "unknown").capitalize()

        if self.process_type == "desorption":
            detail = (
                f"{mode_label} desorption with x0={_format_number(parameters.get('x0'))}, "
                f"G={_format_number(parameters.get('G'))}, L={_format_number(parameters.get('L'))}, "
                f"m={_format_number(parameters.get('m'))}, stages={_format_number(result.get('stages'))}, "
                f"final x={_format_number(result.get('final_x'))}"
            )
        else:
            detail = (
                f"{mode_label} absorption with y0={_format_number(parameters.get('y0'))}, "
                f"x0={_format_number(parameters.get('x0'))}, ytarget={_format_number(parameters.get('ytarget'))}, "
                f"G={_format_number(parameters.get('G'))}, L={_format_number(parameters.get('L'))}, "
                f"m={_format_number(parameters.get('m'))}, stages={_format_number(result.get('stages'))}, "
                f"L/G={_format_number(result.get('ratio'))}"
            )

        return {
            "type": f"{self.process_type.capitalize()} calculation",
            "timestamp": timestamp,
            "detail": detail,
        }


def save_calculation_record(user_id, process_type, mode, parameters, result_summary):
    try:
        calculation = Calculation(
            user_id=user_id,
            process_type=process_type,
            mode=mode,
            parameters_json=_serialize_payload(parameters),
            result_json=_serialize_payload(result_summary),
        )
        db.session.add(calculation)
        db.session.commit()
        logger.info(
            "[CALC HISTORY] Saved calculation id=%s for user_id=%s process_type=%s",
            calculation.id,
            user_id,
            process_type,
        )
        return calculation
    except Exception:
        db.session.rollback()
        logger.exception(
            "[CALC HISTORY] Failed to save calculation for user_id=%s process_type=%s",
            user_id,
            process_type,
        )
        return None


def get_user_calculation_history(user_id):
    return Calculation.query.filter_by(user_id=user_id).order_by(Calculation.created_at.desc()).all()
