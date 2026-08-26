from django.shortcuts import render
import json
from .oms_lms import (
    courbes_svg,
    z_poids_age,
    z_taille_age,
    z_poids_taille,
)


def _ligne(nom, z):
    if z is None:
        return {"indicateur": nom, "statut": "Mesure hors table OMS", "couleur": "info", "z": None}
    z_r = round(z, 2)
    if z < -3:
        return {"indicateur": nom, "statut": "Sévère (z < −3) — centre aujourd'hui", "couleur": "danger", "z": z_r}
    if z < -2:
        return {"indicateur": nom, "statut": "Modéré (z < −2) — contrôle rapide", "couleur": "warning", "z": z_r}
    if z < -1:
        return {"indicateur": nom, "statut": "À surveiller", "couleur": "info", "z": z_r}
    if z > 2:
        return {"indicateur": nom, "statut": "Au-dessus de +2 ET — à interpréter au centre", "couleur": "info", "z": z_r}
    return {"indicateur": nom, "statut": "Zone habituelle OMS", "couleur": "success", "z": z_r}


def evaluer_malnutrition(poids, taille, age_mois, sexe, muac=None):
    resultats = [
        _ligne("Poids pour l'âge (OMS LMS)", z_poids_age(poids, sexe, age_mois)),
        _ligne("Taille pour l'âge (OMS LMS)", z_taille_age(taille, sexe, age_mois)),
        _ligne("Poids pour la taille (OMS LMS)", z_poids_taille(poids, taille, sexe, age_mois)),
    ]
    if muac:
        if muac < 11.5:
            resultats.append({"indicateur": "MUAC (OMS / UNICEF)", "statut": "Sévère (< 11,5 cm)", "couleur": "danger", "z": None})
        elif muac < 12.5:
            resultats.append({"indicateur": "MUAC (OMS / UNICEF)", "statut": "Modéré (11,5–12,5 cm)", "couleur": "warning", "z": None})
        else:
            resultats.append({"indicateur": "MUAC (OMS / UNICEF)", "statut": "Habituel (≥ 12,5 cm)", "couleur": "success", "z": None})
    return resultats


def detection_malnutrition(request):
    resultats = None
    courbes = None
    if request.method == "POST":
        try:
            prenom = request.POST.get("prenom")
            sexe = request.POST.get("sexe")
            age_mois = int(request.POST.get("age_mois"))
            poids = float(request.POST.get("poids"))
            taille = float(request.POST.get("taille"))
            muac_val = request.POST.get("muac")
            muac = float(muac_val) if muac_val else None
            ev = evaluer_malnutrition(poids, taille, age_mois, sexe, muac)
            ordre = {"danger": 0, "warning": 1, "info": 2, "success": 3}
            pire = min((ordre.get(e["couleur"], 3) for e in ev), default=3)
            if pire == 0:
                synthese = "Allez dans un centre de santé aujourd'hui. Ne vous fiez pas seulement à cet écran."
            elif pire == 1:
                synthese = "Il faut montrer l'enfant à un soignant bientôt (aujourd'hui ou demain)."
            elif pire == 2:
                synthese = "Ce n'est pas une urgence d'après cet outil, mais parlez-en à la prochaine visite."
            else:
                synthese = "Pour l'instant, les mesures sont dans la zone habituelle. Ce n'est pas un diagnostic."
            resultats = {
                "prenom": prenom,
                "sexe": sexe,
                "age_mois": age_mois,
                "poids": poids,
                "taille": taille,
                "muac": muac,
                "evaluations": ev,
                "synthese": synthese,
                "niveau": ("danger", "warning", "info", "success")[pire],
            }
            courbes = courbes_pour(sexe)
        except Exception as e:
            resultats = {"erreur": str(e)}

    return render(request, "enfants/malnutrition.html", {
        "resultats": resultats,
        "svg_poids": courbes["poids"] if courbes else "",
        "svg_taille": courbes["taille"] if courbes else "",
        "courbes_json": "null",
    })
