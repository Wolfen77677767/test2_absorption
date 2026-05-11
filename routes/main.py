from flask import Blueprint, render_template, request, redirect, url_for, session, flash, send_file
import os
import time
import tracemalloc
import numpy as np
import plotly.graph_objs as go
import plotly
import json
import logging
from config import Config
from core.absorption_solver import solve_absorption, sensitivity_analysis
from core.desorption_solver import solve_desorption
from models.calculation import get_user_calculation_history, save_calculation_record
from models.user import User
from services.unit_operations_service import UnitOperationsService
from services.unit_visualization_service import UnitVisualizationService

main_bp = Blueprint('main', __name__)
logger = logging.getLogger(__name__)


def get_current_session_user():
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

    logger.info(
        "[CALC HISTORY] session username=%s session user_id=%s resolved user_id=%s",
        session.get("user"),
        session.get("user_id"),
        current_user.id if current_user else None,
    )

    return current_user


def save_current_user_calculation(process_type, mode, parameters, result_summary):
    current_user = get_current_session_user()
    if not current_user:
        logger.warning("[CALC HISTORY] No logged-in user could be resolved. Skipping calculation save.")
        return None

    calculation = save_calculation_record(
        user_id=current_user.id,
        process_type=process_type,
        mode=mode,
        parameters=parameters,
        result_summary=result_summary,
    )

    logger.info(
        "[CALC HISTORY] Calculation save succeeded=%s for user_id=%s",
        bool(calculation),
        current_user.id,
    )

    return calculation

@main_bp.route("/")
def home():
    return render_template("home.html")


@main_bp.route("/theory")
def theory():
    return render_template("theory.html")


@main_bp.route("/about")
def about():
    return render_template("about.html")


@main_bp.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    """Backward compatibility - redirects to appropriate dashboard based on role"""
    if "user" not in session:
        return redirect(url_for("auth.login"))

    username = session["user"]
    user = User.query.filter_by(username=username).first()
    
    if user and user.is_admin():
        return redirect(url_for("admin.admin_dashboard"))
    else:
        return redirect(url_for("main.user_dashboard"))


@main_bp.route("/dashboard/user", methods=["GET", "POST"])
def user_dashboard():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    username = session["user"]
    user_dir = os.path.join(Config.UPLOAD_DIR, username)
    os.makedirs(user_dir, exist_ok=True)

    if request.method == "POST":
        uploaded = request.files.get("graph_image")
        if uploaded and uploaded.filename:
            ext = os.path.splitext(uploaded.filename)[1].lower()
            if ext not in [".png", ".jpg", ".jpeg", ".gif"]:
                flash("Format d'image non supporté. PNG/JPG/GIF seulement.", "danger")
            else:
                file_path = os.path.join(user_dir, uploaded.filename)
                uploaded.save(file_path)
                flash("Image sauvegardée.", "success")
        else:
            flash("Aucune image sélectionnée.", "warning")

    user_images = []
    for f in os.listdir(user_dir):
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".gif")):
            user_images.append(url_for("static", filename=f"user_uploads/{username}/{f}"))

    return render_template("user_dashboard.html", username=username, name=session.get("name"), images=user_images)


@main_bp.route("/billing")
def billing():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "billing.html",
        paypal_client_id=Config.PAYPAL_CLIENT_ID,
        monthly_plan_id=Config.PAYPAL_PLAN_ID_MONTHLY,
        yearly_plan_id=Config.PAYPAL_PLAN_ID_YEARLY,
        paypal_configured=bool(
            Config.PAYPAL_CLIENT_ID and Config.PAYPAL_PLAN_ID_MONTHLY and Config.PAYPAL_PLAN_ID_YEARLY
        ),
    )


@main_bp.route("/billing/success")
def billing_success():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    plan = request.args.get("plan", "subscription")
    subscription_id = request.args.get("subscription_id")

    return render_template(
        "billing_success.html",
        plan=plan,
        subscription_id=subscription_id,
    )


@main_bp.route("/historique")
def historique():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    current_user = get_current_session_user()
    if not current_user:
        flash("User not found.", "danger")
        return redirect(url_for("auth.login"))

    activities = [calculation.to_history_item() for calculation in get_user_calculation_history(current_user.id)]
    logger.info(
        "[CALC HISTORY] Found %s history row(s) for user_id=%s",
        len(activities),
        current_user.id,
    )

    return render_template(
        "historique.html",
        username=current_user.username,
        name=session.get("name"),
        activities=activities
    )


@main_bp.route("/archive")
def archive():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    return render_template(
        "archive.html",
        username=session.get("user"),
        name=session.get("name"),
        archived_items=[]
    )


@main_bp.route("/quick-solver")
def quick_solver():
    if "user" not in session:
        return redirect(url_for("auth.login"))
    
    return render_template("quick_solver.html")


@main_bp.route("/unit-operations")
def unit_operations():
    operations = UnitOperationsService.get_operations()
    categories = list(UnitOperationsService.CATEGORY_META.keys())
    return render_template(
        "unit_operations.html",
        operations=operations,
        categories=categories,
    )


@main_bp.route("/unit-operation-calculator")
def unit_operation_calculator():
    operation = UnitOperationsService.get_operations()[0]
    visualization = UnitVisualizationService.generate_visualization(operation, {}, None)
    return render_template(
        "unit_operation_calculator.html",
        operation=operation,
        result=None,
        form_values={},
        psychrometric_operation=UnitOperationsService.get_operation("psychrometric"),
        psychrometric_result=None,
        psychrometric_form_values={"P": "101.325"},
        visualization=visualization,
    )


@main_bp.route("/calculate", methods=["GET", "POST"])
def calculate():
    if "user" not in session:
        return redirect(url_for("auth.login"))

    # Check if this is accessed from unit operations
    from_unit_ops = request.args.get('from_unit_ops', 'false').lower() == 'true'
    page_title = "Absorption Gas-Liquid Solver" if from_unit_ops else "Solver Configuration"

    if request.method == "POST":

        try:
            process_type = request.form.get("process_type", "absorption")
            
            x0 = float(request.form.get("x0", 0.0))
            G = float(request.form.get("G", 150))
            L = float(request.form.get("L", 200))
            m = float(request.form.get("m", 0.5))
            show_steps = request.form.get("show_steps") == "on"

            if process_type == "desorption":
                n_stages = int(request.form.get("n_stages", 3))
                mode = request.form.get("mode", "cross")
                
                # Start measurement
                tracemalloc.start()
                start_time = time.time()
                
                stage_details, x_values, y_plot, S, Gi, stages = solve_desorption(x0, G, L, m, n_stages, mode=mode)
                
                # Stop measurement
                end_time = time.time()
                current, peak = tracemalloc.get_traced_memory()
                tracemalloc.stop()
                
                computation_time = round(end_time - start_time, 4)
                memory_used_kb = peak / 1024
                if memory_used_kb > 1024:
                    memory_used = round(memory_used_kb / 1024, 2)
                    memory_unit = "MB"
                else:
                    memory_used = round(memory_used_kb, 2)
                    memory_unit = "KB"
                
                table = [(step["stage"], step["x_in"], step["y_out"]) for step in stage_details]
                final_x = x_values[-1] if len(x_values) > 0 else x0
                
                # -------- Desorption Graph --------
                stages_arr = list(range(stages + 1))

                fig_des_x = go.Figure()
                fig_des_x.add_trace(go.Scatter(
                    x=stages_arr,
                    y=x_values,
                    mode="lines+markers",
                    name="Liquid Comp. (x)",
                    line=dict(color="#00CFFF", width=3)
                ))
                fig_des_x.update_layout(
                    title="Desorption Liquid Composition",
                    xaxis_title="Stage Number",
                    yaxis_title="Liquid Mole Fraction",
                    template="plotly_dark",
                    paper_bgcolor="#001128",
                    plot_bgcolor="#001128",
                    font=dict(color="#E9F4FF")
                )

                fig_des_y = go.Figure()
                fig_des_y.add_trace(go.Scatter(
                    x=stages_arr,
                    y=y_plot,
                    mode="lines+markers",
                    name="Gas Comp. (y)",
                    line=dict(color="#FF4500", width=3)
                ))
                fig_des_y.update_layout(
                    title="Desorption Gas Composition",
                    xaxis_title="Stage Number",
                    yaxis_title="Gas Mole Fraction",
                    template="plotly_dark",
                    paper_bgcolor="#001128",
                    plot_bgcolor="#001128",
                    font=dict(color="#E9F4FF")
                )

                graphJSON_x = json.dumps(fig_des_x, cls=plotly.utils.PlotlyJSONEncoder)
                graphJSON_y = json.dumps(fig_des_y, cls=plotly.utils.PlotlyJSONEncoder)

                save_current_user_calculation(
                    process_type="desorption",
                    mode=mode,
                    parameters={
                        "x0": x0,
                        "G": G,
                        "L": L,
                        "m": m,
                        "n_stages": n_stages,
                        "show_steps": show_steps,
                    },
                    result_summary={
                        "stages": stages,
                        "final_x": final_x,
                        "ratio": (L / G) if G else None,
                        "computation_time": computation_time,
                        "memory_used": memory_used,
                        "memory_unit": memory_unit,
                    },
                )

                return render_template(
                    "results.html",
                    process_type="desorption",
                    stages=stages,
                    x0=x0,
                    G=G,
                    L=L,
                    m=m,
                    S=S,
                    Gi=Gi,
                    final_x=final_x,
                    table=table,
                    stage_details=stage_details,
                    show_steps=show_steps,
                    ratio=L/G,
                    mode=mode,
                    y0=0, ytarget=0, absorption_rate=0,
                    graphJSON_x=graphJSON_x,
                    graphJSON_y=graphJSON_y,
                    stage_sens_JSON="{}",
                    computation_time=computation_time,
                    memory_used=memory_used,
                    memory_unit=memory_unit
                )

            y0 = float(request.form.get("y0", 0.06))
            ytarget = float(request.form.get("ytarget", 0.004))
            mode = request.form.get("mode", "cross")

            # -------- solve absorption --------
            # Start measurement
            tracemalloc.start()
            start_time = time.time()
            
            eq_x, eq_y, op_x, op_y, stair_x, stair_y, stages, stage_details, ratio = solve_absorption(
                y0=y0,
                x0=x0,
                G=G,
                L=L,
                m=m,
                ytarget=ytarget,
                mode=mode
            )
            
            # Stop measurement
            end_time = time.time()
            current, peak = tracemalloc.get_traced_memory()
            tracemalloc.stop()
            
            computation_time = round(end_time - start_time, 4)
            memory_used_kb = peak / 1024
            if memory_used_kb > 1024:
                memory_used = round(memory_used_kb / 1024, 2)
                memory_unit = "MB"
            else:
                memory_used = round(memory_used_kb, 2)
                memory_unit = "KB"
        except ValueError as e:
            return render_template("calculate.html", error_message=str(e), page_title=page_title)



        # -------- absorption rate --------
        Y0 = y0 / (1 - y0)
        Ytarget = ytarget / (1 - ytarget)

        absorption_rate = ((Y0 - Ytarget) / Y0) * 100

        # -------- McCabe Thiele Graph --------
        # dynamic range based on actual computed staircase values
        stage_x_points = [step["X"] for step in stage_details] if stage_details else []
        stage_y_points = [step["Y"] for step in stage_details] if stage_details else []

        x_data_max = max(stage_x_points + [x0, 0.01])
        y_data_max = max(stage_y_points + [Y0, 0.01])

        x_plot_max = max(x_data_max * 1.2, 0.01)
        y_plot_max = max(y_data_max * 1.2, 0.01)

        eq_x = np.linspace(0, x_plot_max, 200)
        eq_y = m * eq_x

        if mode == "counter":
            op_y = ratio * eq_x + Ytarget
        elif mode == "co":
            op_y = ratio * eq_x + Y0
        elif mode == "cross":
            op_y = Y0 - ratio * eq_x
        else:
            op_y = ratio * eq_x + Ytarget

        op_x = eq_x

        fig = go.Figure()

        # Équilibre
        fig.add_trace(go.Scatter(
            x=eq_x,
            y=eq_y,
            mode="lines",
            name="Équilibre Y = mX",
            line=dict(color="#00CFFF", dash="dash", width=3)
        ))

        # Droite opératoire (pour tous modes; cross-profile via op_x, op_y)
        fig.add_trace(go.Scatter(
            x=op_x,
            y=op_y,
            mode="lines",
            name="Droite opératoire",
            line=dict(color="#00FF00", dash="dot", width=2)
        ))

        # Escaliers McCabe-Thiele (même logique que plot_mccabe)
        staircase_x = []
        staircase_y = []
        current_Y = Y0

        for step in stage_details:
            stage_X = step["X"]
            stage_Y = step["Y"]
            eq_X = current_Y / m

            # horizontal depuis l'équilibre vers le point d'étape
            staircase_x += [eq_X, stage_X, None]
            staircase_y += [current_Y, current_Y, None]

            # vertical vers le point suivant
            staircase_x += [stage_X, stage_X, None]
            staircase_y += [current_Y, stage_Y, None]

            current_Y = stage_Y

        fig.add_trace(go.Scatter(
            x=staircase_x,
            y=staircase_y,
            mode="lines",
            name="Étages (escalier)",
            line=dict(color="#FF4500", width=3)
        ))

        # Try to zoom on relevant stage range, especially for cross-flow where equilibrium X is far higher.
        stage_x_points = [step["X"] for step in stage_details] if stage_details else []
        stage_y_points = [step["Y"] for step in stage_details] if stage_details else []
        max_stage_x = max(stage_x_points + [x0], default=0)
        max_stage_y = max(stage_y_points + [Y0], default=0)

        fig.update_layout(
            title="McCabe-Thiele Diagram",
            xaxis_title="X (liquid molar ratio)",
            yaxis_title="Y (gas molar ratio)",
            template="plotly_dark",
            paper_bgcolor="#001128",
            plot_bgcolor="#001128",
            font=dict(color="#E9F4FF"),
            xaxis=dict(
                gridcolor="#1F4B7A",
                zerolinecolor="#1F4B7A",
                linecolor="#4EA4FF",
                tickcolor="#4EA4FF"
            ),
            yaxis=dict(
                gridcolor="#1F4B7A",
                zerolinecolor="#1F4B7A",
                linecolor="#4EA4FF",
                tickcolor="#4EA4FF"
            ),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            hovermode="closest"
        )

        # x/y axes are based on actual staircase range, with a small minimum for visibility.
        fig.update_xaxes(range=[0, x_plot_max])
        fig.update_yaxes(range=[0, y_plot_max])

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)

        # -------- sensitivity analysis --------
        ratio_range, stage_curve = sensitivity_analysis(
            y0=y0,
            ytarget=ytarget,
            m=m,
            mode=mode
        )

        sens_fig = go.Figure()

        sens_fig.add_trace(go.Scatter(
            x=ratio_range,
            y=stage_curve,
            mode="lines+markers",
            name="Stages vs L/G"
        ))

        sens_fig.update_layout(
            title="Sensitivity Analysis (L/G vs Stages)",
            xaxis_title="L/G",
            yaxis_title="Number of Stages",
            template="plotly_dark"
        )

        stage_sens_JSON = json.dumps(
            sens_fig,
            cls=plotly.utils.PlotlyJSONEncoder
        )

        # -------- matplotlib pour tracer très proche du code fourni --------
        from core.absorption_solver import plot_mccabe
        try:
            plot_mccabe(G=G, L=L, m=m, y0=y0, N=stages, stage_details=stage_details, output_path="static/mccabe.png")
        except Exception as e:
            # ne bloque pas le calcul principal
            print('Erreur plot_mccabe:', e)

        # -------- table --------
        table = [(step["stage"], step["X"], step["Y"]) for step in stage_details]

        save_current_user_calculation(
            process_type="absorption",
            mode=mode,
            parameters={
                "y0": y0,
                "x0": x0,
                "ytarget": ytarget,
                "G": G,
                "L": L,
                "m": m,
                "show_steps": show_steps,
            },
            result_summary={
                "stages": stages,
                "ratio": ratio,
                "absorption_rate": absorption_rate,
                "computation_time": computation_time,
                "memory_used": memory_used,
                "memory_unit": memory_unit,
            },
        )

        return render_template(
            "results.html",
            process_type="absorption",
            graphJSON=graphJSON,
            stage_sens_JSON=stage_sens_JSON,
            table=table,
            stages=stages,
            y0=y0,
            x0=x0,
            ytarget=ytarget,
            G=G,
            L=L,
            m=m,
            ratio=ratio,
            mode=mode,
            show_steps=show_steps,
            stage_details=stage_details,
            absorption_rate=absorption_rate,
            computation_time=computation_time,
            memory_used=memory_used,
            memory_unit=memory_unit
        )

    return render_template("calculate.html", page_title=page_title)

