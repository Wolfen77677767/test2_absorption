from flask import Blueprint, request, send_file
from core.report import create_report

api_bp = Blueprint('api', __name__)

@api_bp.route("/download_report")
def download_report():

    y0 = float(request.args.get("y0", 0))
    x0 = float(request.args.get("x0", 0))
    ytarget = float(request.args.get("ytarget", 0))
    G = float(request.args.get("G", 0))
    L = float(request.args.get("L", 0))
    m = float(request.args.get("m", 0))
    mode = request.args.get("mode")
    stages = int(request.args.get("stages", 0))
    ratio = float(request.args.get("ratio", 0))

    report_path = create_report(
        stages,
        y0,
        ytarget,
        x0=x0,
        G=G,
        L=L,
        m=m,
        mode=mode,
        ratio=ratio
    )

    return send_file(
        report_path,
        as_attachment=True,
        download_name="absorption_report.pdf"
    )