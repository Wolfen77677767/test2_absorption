# McCabe-Thiele Absorption Solver (Flask)

## Description

Flask application for solving gas absorption exercises using the McCabe–Thiele method.

Features:
- Equilibrium relation (y = m x)
- Operating line (L'/G' + y0)
- Automatic McCabe-Thiele staircase generation
- Minimum theoretical stages
- Absorption and desorption modes support (cross-flow, counter-current, co-current)
- Computation time and peak memory usage metrics in results
- Interactive Plotly chart (equilibrium + operating + staircase)
- Export PNG, CSV, PDF
- Pedagogical mode (step-by-step)
- L'/G' sensitivity analysis (slider + curve)
- Predefined exercises (Benzene, SO2)
- Bootstrap UI, dark scientific style, responsive

## Structure du projet

- `app.py` : routes Flask (`/`, `/theory`, `/calculate`, `/download_report`)
- `calculations/absorption_solver.py` : calcul scientifique
- `calculations/report.py` : création PDF (ReportLab)
- `templates/` : pages Jinja2
- `static/style.css` : CSS custom
- `static/script.js` : logique JS (usage local)

## Installation

1. Create a Python virtual environment

```bash
python -m venv env
env\Scripts\activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

3. Start the app

```bash
python app.py
```

4. Open in browser

`http://127.0.0.1:5000/calculate`

## Usage

1. Select a predefined exercise in `Predefined exercise`, or enter values manually: y0, G', L', m, ytarget.
2. Choose `Mode` (cross/counter) and enable `Show step-by-step` if needed.
3. Click `Solve` to view results.
4. Export options:
   - `Download PDF Report`
   - `Download CSV`
   - `Export Graph PNG`

## Validation et tests

1. Vérifier la génération de graphique : points d'intersection ligne d'opération / équilibre.
2. Vérifier `Stages` pour différents ratios L/G (
   - L/G élevé → moins d'étages
   - L/G faible → plus d'étages
   )
3. Vérifier `show step-by-step` affiche les étapes
4. Vérifier `Sensitivity graph` avec slider (dynamique)
5. Vérifier export PDF (dans le dossier racine) et CSV

## Développement

- Modifie `calculations/absorption_solver.py` pour ajuster la physique.
- Modifie `templates/results.html` pour UX.
- Ajoute tests unitaires dans `tests/` (recommandé) :
  - `from calculations.absorption_solver import solve_absorption`
  - tests du nombre d'étages, logique opératoire.

## Notes

- `report.pdf` is generated as a static file (overwritten on each generation). For multi-user deployments, use `tempfile.NamedTemporaryFile`.
- Plotly chart is rendered in the browser.

---

### Useful commands

- `python -m py_compile app.py calculations/absorption_solver.py calculations/report.py`
- `pip show reportlab` (check reportlab install)
- `flask run --reload` if needed (set `FLASK_APP=app.py` in the environment)
