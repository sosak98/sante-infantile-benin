"""
WHO Child Growth Standards — tables LMS officielles
(package anthro, OMS / World Health Organization).

Z = ((X/M)**L - 1) / (L*S)   si L ≠ 0
Z = ln(X/M) / S              si L = 0
"""
from pathlib import Path
import math

DATA = Path(__file__).resolve().parent / "data" / "oms"


def _zscore(x, L, M, S):
    if x <= 0 or M <= 0 or S <= 0:
        return None
    if abs(L) < 1e-8:
        return math.log(x / M) / S
    return ((x / M) ** L - 1.0) / (L * S)


def _x_at_z(L, M, S, z):
    if abs(L) < 1e-8:
        return M * math.exp(S * z)
    return M * ((1.0 + L * S * z) ** (1.0 / L))


def _load_age(path):
    """sex (1=M,2=F), age en jours -> (L,M,S)"""
    rows = {}
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines()[1:]:
        parts = line.replace("\r", "").split("\t")
        if len(parts) < 5:
            continue
        sex, age = int(float(parts[0])), int(float(parts[1]))
        L, M, S = float(parts[2]), float(parts[3]), float(parts[4])
        rows[(sex, age)] = (L, M, S)
    return rows


def _load_len(path, key_name="length"):
    """sex, length/height cm (peut être .5) -> (L,M,S)"""
    rows = {}
    text = Path(path).read_text(encoding="utf-8", errors="replace")
    for line in text.splitlines()[1:]:
        parts = line.replace("\r", "").split("\t")
        if len(parts) < 5:
            continue
        sex = int(float(parts[0]))
        cm = round(float(parts[1]) * 2) / 2.0
        L, M, S = float(parts[2]), float(parts[3]), float(parts[4])
        rows[(sex, cm)] = (L, M, S)
    return rows


WFA = _load_age(DATA / "weianthro.txt")
HFA = _load_age(DATA / "lenanthro.txt")
WFL = _load_len(DATA / "wflanthro.txt")
WFH = _load_len(DATA / "wfhanthro.txt")


def _sex_code(sexe):
    return 1 if sexe == "M" else 2


def _age_days(age_mois):
    return int(round(max(0, min(60, age_mois)) * 30.4375))


def _nearest(table, sex, key, max_delta):
    if (sex, key) in table:
        return table[(sex, key)]
    best, bd = None, 1e9
    for (s, k), v in table.items():
        if s != sex:
            continue
        d = abs(k - key)
        if d < bd:
            bd, best = d, v
    if bd <= max_delta:
        return best
    return None


def lms_poids_age(sexe, age_mois):
    return _nearest(WFA, _sex_code(sexe), _age_days(age_mois), 20)


def lms_taille_age(sexe, age_mois):
    return _nearest(HFA, _sex_code(sexe), _age_days(age_mois), 20)


def lms_poids_taille(sexe, taille_cm, age_mois):
    sex = _sex_code(sexe)
    cm = round(float(taille_cm) * 2) / 2.0
    if age_mois < 24:
        return _nearest(WFL, sex, cm, 1.0)
    return _nearest(WFH, sex, cm, 1.0) or _nearest(WFL, sex, cm, 1.0)


def z_poids_age(poids, sexe, age_mois):
    t = lms_poids_age(sexe, age_mois)
    return _zscore(poids, *t) if t else None


def z_taille_age(taille, sexe, age_mois):
    t = lms_taille_age(sexe, age_mois)
    return _zscore(taille, *t) if t else None


def z_poids_taille(poids, taille, sexe, age_mois):
    t = lms_poids_taille(sexe, taille, age_mois)
    return _zscore(poids, *t) if t else None


def serie_poids_age(sexe):
    ages, z3, z2, med, p2 = [], [], [], [], []
    for m in range(0, 61):
        t = lms_poids_age(sexe, m)
        if not t:
            continue
        ages.append(m)
        z3.append(round(_x_at_z(*t, -3), 2))
        z2.append(round(_x_at_z(*t, -2), 2))
        med.append(round(_x_at_z(*t, 0), 2))
        p2.append(round(_x_at_z(*t, 2), 2))
    return {"ages": ages, "z3": z3, "z2": z2, "median": med, "p2": p2}


def serie_taille_age(sexe):
    ages, z3, z2, med, p2 = [], [], [], [], []
    for m in range(0, 61):
        t = lms_taille_age(sexe, m)
        if not t:
            continue
        ages.append(m)
        z3.append(round(_x_at_z(*t, -3), 1))
        z2.append(round(_x_at_z(*t, -2), 1))
        med.append(round(_x_at_z(*t, 0), 1))
        p2.append(round(_x_at_z(*t, 2), 1))
    return {"ages": ages, "z3": z3, "z2": z2, "median": med, "p2": p2}


def serie_poids_taille(sexe, age_mois):
    """X = taille (cm), Y = poids (kg)."""
    xs, z3, z2, med, p2 = [], [], [], [], []
    start, end = (45, 110) if age_mois < 24 else (65, 120)
    for cm in range(int(start), int(end) + 1, 2):
        t = lms_poids_taille(sexe, cm, age_mois)
        if not t:
            continue
        xs.append(cm)
        z3.append(round(_x_at_z(*t, -3), 2))
        z2.append(round(_x_at_z(*t, -2), 2))
        med.append(round(_x_at_z(*t, 0), 2))
        p2.append(round(_x_at_z(*t, 2), 2))
    return {"ages": xs, "z3": z3, "z2": z2, "median": med, "p2": p2}


def svg_courbe(pack, point_x, point_y, titre, unite_x, unite_y="kg"):
    """Petit SVG autonome (pas de Chart.js)."""
    w, h, pad_l, pad_r, pad_t, pad_b = 640, 260, 48, 16, 28, 36
    ages, med, z2, z3, p2 = pack["ages"], pack["median"], pack["z2"], pack["z3"], pack["p2"]
    if not ages:
        return ""
    ys = z3 + z2 + med + p2 + ([point_y] if point_y else [])
    ymin, ymax = min(ys), max(ys)
    span = (ymax - ymin) or 1
    ymin -= span * 0.08
    ymax += span * 0.08

    def x(a):
        return pad_l + (a - ages[0]) / (ages[-1] - ages[0] or 1) * (w - pad_l - pad_r)

    def y(v):
        return pad_t + (1 - (v - ymin) / (ymax - ymin)) * (h - pad_t - pad_b)

    def path(vals):
        return " ".join(
            ("M" if i == 0 else "L") + f"{x(ages[i]):.1f},{y(v):.1f}"
            for i, v in enumerate(vals)
        )

    px = x(max(ages[0], min(ages[-1], point_x)))
    py = y(point_y)
    return f'''<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="{titre}">
      <text x="{pad_l}" y="16" font-size="13" font-weight="700" fill="#0a3d36">{titre}</text>
      <path d="{path(z3)}" fill="none" stroke="#c62828" stroke-width="1"/>
      <path d="{path(z2)}" fill="none" stroke="#e0a000" stroke-width="1.4"/>
      <path d="{path(med)}" fill="none" stroke="#00796b" stroke-width="2"/>
      <path d="{path(p2)}" fill="none" stroke="#1565c0" stroke-width="1"/>
      <circle cx="{px:.1f}" cy="{py:.1f}" r="6" fill="#c2182b" stroke="#fff" stroke-width="2"/>
      <text x="{w/2}" y="{h-8}" font-size="11" text-anchor="middle" fill="#5b7a75">{unite_x} · {unite_y}</text>
    </svg>'''


def courbes_pour(sexe):
    return {"poids": serie_poids_age(sexe), "taille": serie_taille_age(sexe)}


def courbes_svg(sexe, age_mois, poids, taille):
    c = courbes_pour(sexe)
    wfl = serie_poids_taille(sexe, age_mois)
    return {
        "poids": svg_courbe(c["poids"], age_mois, poids, "Poids pour l'âge (OMS)", "Âge (mois)", "kg"),
        "taille": svg_courbe(c["taille"], age_mois, taille, "Taille pour l'âge (OMS)", "Âge (mois)", "cm"),
        "poids_taille": svg_courbe(wfl, taille, poids, "Poids pour la taille (OMS)", "Taille (cm)", "kg"),
    }
