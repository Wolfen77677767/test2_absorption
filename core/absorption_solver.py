import numpy as np
import math
import os


def solve_absorption(y0, x0, G, L, m, ytarget, mode="cross"): 

    # validation
    if not (0 <= x0 < 1):
        raise ValueError("x0 must be in [0, 1)")
    if not (0 <= y0 < 1):
        raise ValueError("y0 must be in [0, 1)")
    if not (0 <= ytarget < 1):
        raise ValueError("ytarget must be in [0, 1)")
    if ytarget >= y0:
        raise ValueError("ytarget must be less than y0 for absorption")
    if G <= 0 or L <= 0:
        raise ValueError("G and L must be positive")
    if m <= 0:
        raise ValueError("m must be positive")

    ratio = L / G

    # convert to molar ratios
    Y0 = y0 / (1 - y0)
    Ytarget = ytarget / (1 - ytarget)

    # equilibrium line
    X_eq = np.linspace(0, 0.2, 200)
    Y_eq = m * X_eq

    # for cross-flow, use the standard stage reduction formula
    if mode == "cross":
        A = L / (m * G)
        if A <= 0:
            raise ValueError("A (L/(m*G)) must be positive for cross-flow")
        n_stages = math.ceil(math.log(Y0 / Ytarget) / math.log(1 + A))
    else:
        n_stages = None

    # operating line
    X_op = np.linspace(0, 0.2, 200)
    if mode == "counter":
        Y_op = ratio * X_op + Ytarget
    elif mode == "co":
        Y_op = ratio * X_op + Y0
    elif mode == "cross":
        # for cross-flow, each stage has parallel lines with same slope but changing intercept
        Y_op = Y0 - ratio * X_op
    else:
        Y_op = ratio * X_op + Ytarget

    # stage stepping
    stair_x = [x0]
    stair_y = [Y0]

    stage_details = []

    Y = Y0
    stages = 0
    max_stages = 100

    # compute stage steps according to mode
    if mode == "cross":
        # Calcul du nombre théorique d'étages pour cross-flow
        A = L / (m * G)
        n_stages = math.ceil(math.log(Y0 / Ytarget) / math.log(1 + A))

        Y = Y0
        stages = 0

        for i in range(n_stages):
            if Y <= Ytarget:
                break

            Y_next = Y / (1 + A)
            if Y_next < Ytarget:
                Y_next = Ytarget

            X = Y_next / m

            stair_x.append(X)
            stair_y.append(Y_next)

            stage_details.append({
                "stage": i + 1,
                "X": X,
                "Y": Y_next,
                "comment": f"Cross-flow step: Y={Y:.5f} -> {Y_next:.5f}, X={X:.5f}"
            })

            Y = Y_next
            stages += 1

        # Forcer le nombre théorique affiché (3, par exemple) sans ajouter de points supplémentaires
        stages = n_stages
    else:
        while Y > Ytarget and stages < max_stages:

            # horizontal step to equilibrium
            X = Y / m

            stair_x.append(X)
            stair_y.append(Y)

            # vertical step to operating line
            if mode == "co":
                Y_next = ratio * X + Y0
            else:
                Y_next = ratio * X + Ytarget

            if Y_next < Ytarget:
                Y_next = Ytarget

            stair_x.append(X)
            stair_y.append(Y_next)

            stages += 1

            stage_details.append({
                "stage": stages,
                "X": X,
                "Y": Y_next,
                "comment": f"From equilibrium X={X:.5f} to operating line Y={Y_next:.5f}"
            })

            Y = Y_next

    return (
        X_eq,
        Y_eq,
        X_op,
        Y_op,
        stair_x,
        stair_y,
        stages,
        stage_details,
        ratio
    )


# -------------------------------
# Sensitivity analysis
# -------------------------------

def sensitivity_analysis(y0, ytarget, m, mode="cross"):

    if not (0 <= y0 < 1):
        raise ValueError("y0 must be in [0, 1)")
    if not (0 <= ytarget < 1):
        raise ValueError("ytarget must be in [0, 1)")
    if ytarget >= y0:
        raise ValueError("ytarget must be less than y0 for absorption")
    if m <= 0:
        raise ValueError("m must be positive")

    ratio_range = np.linspace(0.2, 5, 60)
    stage_curve = []

    Y0 = y0 / (1 - y0)
    Ytarget = ytarget / (1 - ytarget)

    for ratio in ratio_range:

        Y = Y0
        stages = 0

        while Y > Ytarget and stages < 200:

            X = Y / m
            if mode == "cross":
                Y_next = Y - ratio * X
            elif mode == "co":
                Y_next = ratio * X + Y0
            else:
                Y_next = ratio * X + Ytarget

            # clamp to target (avoid negative or below-target values)
            if Y_next < Ytarget:
                Y_next = Ytarget

            Y = Y_next
            stages += 1
            if Y <= Ytarget:
                break

        stage_curve.append(stages)

    return ratio_range, stage_curve


def plot_mccabe(G, L, m, y0, N, stage_details, output_path="static/mccabe.png"):
    import matplotlib.pyplot as plt

    # Courbe d'équilibre (range dynamique)
    max_stage_x = max([stage["X"] for stage in stage_details], default=0)
    max_stage_y = max([stage["Y"] for stage in stage_details], default=y0 / (1 - y0))

    x_plot_max = max(0.01, max_stage_x * 1.2, y0 / (1 - y0) / m * 1.2)
    y_plot_max = max(0.01, max_stage_y * 1.2, y0 / (1 - y0) * 1.2)

    X_eq = [i / 100 for i in range(101)]
    X_eq = [x * x_plot_max for x in X_eq]
    Y_eq = [m * x for x in X_eq]

    plt.figure(figsize=(7, 7))
    plt.plot(X_eq, Y_eq, label="Équilibre Y*=mX", color="blue")

    # Droite opératoire (pente -L/G), chaque segment par étage
    slope = -L / G
    for i in range(min(N, len(stage_details))):
        Xi = stage_details[i]["X"]
        Yi_prev = stage_details[i - 1]["Y"] if i > 0 else y0 / (1 - y0)
        X_line = [0, Xi]
        Y_line = [Yi_prev, Yi_prev + slope * Xi]
        plt.plot(X_line, Y_line, color="green", linestyle="--", label="Droite opératoire" if i == 0 else "")

    # Escaliers rouges (horizontal jusqu'à l'équilibre, puis vertical)
    Y = y0 / (1 - y0)
    for i in range(min(N, len(stage_details))):
        Xi = stage_details[i]["X"]
        Yi = stage_details[i]["Y"]

        X_eq_point = Y / m
        plt.plot([X_eq_point, Xi], [Y, Y], color="red")
        plt.plot([Xi, Xi], [Y, Yi], color="red")

        Y = Yi

    plt.xlabel("X (liquide)")
    plt.ylabel("Y (gaz)")
    plt.title("Diagramme McCabe-Thiele")
    plt.legend()
    plt.grid(True)

    # Ajustement dynamique des axes
    max_stage_x = max([stage["X"] for stage in stage_details], default=0)
    max_stage_y = max([stage["Y"] for stage in stage_details], default=y0 / (1 - y0))

    # focus on the cross-flow expected small-X region by default
    x_max = max(0.04, max_stage_x * 1.2, 0.05)
    y_max = max(0.02, max_stage_y * 1.2, y0 / (1 - y0))

    plt.xlim(0, x_max)
    plt.ylim(0, y_max)

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    plt.savefig(output_path)
    plt.close()