"""
Unit operations routes.
"""

from flask import Blueprint, flash, redirect, render_template, request, url_for

from services.unit_operations_service import UnitOperationsService
from services.unit_visualization_service import UnitVisualizationService


unit_ops_bp = Blueprint("unit_ops", __name__)


def get_current_session_user():
    """Resolve the current user from session when available."""
    from flask import session
    from models.user import User

    if "user" not in session:
        return None

    session_user_id = session.get("user_id")
    current_user = None

    if session_user_id:
        current_user = User.query.filter_by(id=session_user_id).first()
        if current_user and current_user.username != session.get("user"):
            current_user = None

    if not current_user:
        current_user = User.query.filter_by(username=session.get("user")).first()
        if current_user:
            session["user_id"] = current_user.id

    return current_user


def save_current_user_calculation(process_type, mode, parameters, result_summary):
    """Persist calculation history without interrupting the UI on failure."""
    current_user = get_current_session_user()
    if not current_user:
        return

    try:
        from models.calculation import save_calculation_record

        save_calculation_record(
            user_id=current_user.id,
            process_type=process_type,
            mode=mode,
            parameters=dict(parameters),
            result_summary=result_summary,
        )
    except Exception:
        return


@unit_ops_bp.route("/unit-operations")
def unit_operations_index():
    operations = UnitOperationsService.get_operations()
    categories = list(UnitOperationsService.CATEGORY_META.keys())
    return render_template(
        "unit_operations.html",
        operations=operations,
        categories=categories,
    )


@unit_ops_bp.route("/unit-operations/<operation_slug>", methods=["GET", "POST"])
def unit_operation_calculator(operation_slug):
    # Special handling for absorption - redirect to the full absorption solver
    if operation_slug == "absorption":
        return redirect(url_for("main.calculate", from_unit_ops="true"))
    
    operation = UnitOperationsService.get_operation(operation_slug)
    if not operation:
        flash("Opération inconnue.", "danger")
        return redirect(url_for("unit_ops.unit_operations_index"))

    result = None
    psychrometric_result = None
    form_values = {}
    psychrometric_form_values = {"P": "101.325"}
    psychrometric_operation = UnitOperationsService.get_operation("psychrometric")

    if request.method == "POST":
        submitted_values = request.form.to_dict(flat=True)
        calculator_context = submitted_values.get("calculator_context", "primary")

        if calculator_context == "psychrometric":
            psychrometric_form_values = submitted_values
            psychrometric_result = UnitOperationsService.calculate_operation("psychrometric", psychrometric_form_values)
            if psychrometric_result and not psychrometric_result.get("error"):
                save_current_user_calculation(
                    process_type="unit_operation",
                    mode="psychrometric_calculator",
                    parameters=psychrometric_form_values,
                    result_summary=psychrometric_result,
                )
        else:
            form_values = submitted_values
            result = UnitOperationsService.calculate_operation(operation_slug, form_values)
            if result and not result.get("error"):
                save_current_user_calculation(
                    process_type="unit_operation",
                    mode=operation["key"],
                    parameters=form_values,
                    result_summary=result,
                )

    visualization = UnitVisualizationService.generate_visualization(
        operation,
        form_values,
        result,
        psychrometric_result=psychrometric_result,
        psychrometric_form_values=psychrometric_form_values,
    )

    return render_template(
        "unit_operation_calculator.html",
        operation=operation,
        result=result,
        form_values=form_values,
        psychrometric_operation=psychrometric_operation,
        psychrometric_result=psychrometric_result,
        psychrometric_form_values=psychrometric_form_values,
        visualization=visualization,
    )
