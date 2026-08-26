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


def courbes_pour(sexe):
    return {"poids": serie_poids_age(sexe), "taille": serie_taille_age(sexe)}
