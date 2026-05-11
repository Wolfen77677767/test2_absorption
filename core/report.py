from reportlab.pdfgen import canvas
import os

def create_report(stages, y0, ytarget, x0=None, G=None, L=None, m=None, mode=None, ratio=None):
    filename = "report.pdf"
    c = canvas.Canvas(filename)

    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 780, "Absorption Calculation Report")

    c.setFont("Helvetica", 12)
    c.drawString(100, 750, f"Inputs:")
    c.drawString(120, 730, f"y0 (gas inlet) = {y0}")
    c.drawString(120, 710, f"x0 (liquid inlet) = {x0}")
    c.drawString(120, 690, f"ytarget (gas outlet) = {ytarget}")
    c.drawString(120, 670, f"G' = {G}  L' = {L}  m = {m}")
    c.drawString(120, 650, f"Mode = {mode}  L/G = {ratio:.4f}" if ratio is not None else f"Mode = {mode}")

    c.drawString(100, 640, f"Theoretical stages = {stages}")

    c.drawString(100, 600, "(Graph image cannot be embedded in this basic report.)")

    c.save()
    return os.path.abspath(filename)