import numpy as np


def solve_desorption(x0, G, L, m, n_stages=3, mode="cross"):
    """
    Desorption (stripping) solver with simplified flow modes.

    Mode options:
        - cross: cross-flow, gas is split equally per stage
        - counter: counter-current across all stages
        - co: co-current across all stages

    Parameters:
        x0       : initial liquid mole fraction of solute
        G        : total gas flow rate
        L        : liquid flow rate
        m        : Henry equilibrium slope (y* = m * x)
        n_stages : number of ideal stages (default 3)
        mode     : 'cross'|'counter'|'co'

    Returns:
        (stage_details, x_values, y_plot, S, Gi, n_stages)
    """

    # ---- Input validation ----
    if not (0 <= x0 < 1):
        raise ValueError("x0 must be in [0, 1)")
    if G <= 0:
        raise ValueError("G must be positive")
    if L <= 0:
        raise ValueError("L must be positive")
    if m <= 0:
        raise ValueError("m must be positive")
    if n_stages < 1:
        raise ValueError("n_stages must be >= 1")
    if mode not in ("cross", "counter", "co"):
        raise ValueError("mode must be one of: cross, counter, co")

    # ---- Gas and stripping factor based on mode ----
    if mode == "cross":
        Gi = G / n_stages
        S = (m * Gi) / L
    else:
        Gi = G
        # counter-current is usually most efficient, co-current is slightly less
        S = (m * G) / L
        if mode == "co":
            S *= 0.85

    # ---- Stage-by-stage computation ----
    x_values = [x0]
    y_plot = [0.0]
    stage_details = []

    x = x0

    for i in range(1, n_stages + 1):

        x_next = x / (1 + S)
        y_out = m * x_next

        fraction_desorbed = (x0 - x_next) / x0 if x0 > 0 else 0.0

        stage_details.append({
            "stage": i,
            "x_in": round(x, 8),
            "x_out": round(x_next, 8),
            "y_out": round(y_out, 8),
            "fraction_desorbed": round(fraction_desorbed, 6),
            "comment": (
                f"Stage {i} ({mode}): x_in={x:.6e} -> x_out={x_next:.6e}, "
                f"y_out={y_out:.6e}, desorbed={fraction_desorbed:.2%}"
            )
        })

        x_values.append(x_next)
        y_plot.append(y_out)

        x = x_next

    return (
        stage_details,
        x_values,
        y_plot,
        S,
        Gi,
        n_stages
    )


# -------------------------------
# Sensitivity analysis
# -------------------------------

def desorption_sensitivity_analysis(x0, G, L, m, stage_range=None):
    """
    Evaluate final liquid composition as a function of stage count.

    Parameters:
        x0          : initial liquid mole fraction of solute
        G           : total gas flow rate
        L           : liquid flow rate
        m           : Henry equilibrium slope
        stage_range : list of stage counts to evaluate (default 1..10)

    Returns:
        (stage_range, final_x)
    """

    # ---- Input validation ----
    if not (0 <= x0 < 1):
        raise ValueError("x0 must be in [0, 1)")
    if G <= 0:
        raise ValueError("G must be positive")
    if L <= 0:
        raise ValueError("L must be positive")
    if m <= 0:
        raise ValueError("m must be positive")

    if stage_range is None:
        stage_range = list(range(1, 11))

    final_x = []

    for n in stage_range:

        # run the solver for n stages
        result = solve_desorption(x0, G, L, m, n_stages=n)
        # final liquid composition is the last element of x_values
        x_final = result[1][-1]
        final_x.append(x_final)

    return stage_range, final_x