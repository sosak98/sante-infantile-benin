from django.shortcuts import render
import json
from .oms_lms import (
    courbes_svg,
    z_poids_age,
    z_taille_age,
    z_poids_taille,
)


MUAC_AGE_MIN_MOIS = 6
MUAC_AGE_MAX_MOIS = 59


def _ligne(nom, z):
    if z is None:
        return {"indicateur": nom, "statut": "Mesure incomplète", "couleur": "info", "z": None}
    z_r = round(z, 2)
    if z < -3:
        return {"indicateur": nom, "statut": "Malnutrition sévère", "couleur": "danger", "z": z_r}
    if z < -2:
        return {"indicateur": nom, "statut": "Malnutrition modérée", "couleur": "warning", "z": z_r}
    return {"indicateur": nom, "statut": "Normale", "couleur": "success", "z": z_r}


def _ligne_muac(muac, age_mois):
    """Interprète le MUAC seulement dans sa tranche d'âge validée."""
    if not MUAC_AGE_MIN_MOIS <= age_mois <= MUAC_AGE_MAX_MOIS:
        return {
            "indicateur": "Tour de bras (MUAC)",
            "statut": "Non interprétable à cet âge",
            "couleur": "info",
            "z": None,
            "note": (
                "Le périmètre brachial n'est utilisable qu'entre 6 et 59 mois. "
                f"À {age_mois} mois, la mesure ne permet aucune conclusion : "
                "fiez-vous au poids et à la taille."
            ),
        }
    if muac < 11.5:
        statut, couleur = "Malnutrition aiguë sévère", "danger"
    elif muac < 12.5:
        statut, couleur = "Malnutrition aiguë modérée", "warning"
    else:
        statut, couleur = "Normale", "success"
    return {
        "indicateur": "Tour de bras (MUAC)",
        "statut": statut,
        "couleur": couleur,
        "z": None,
    }


def evaluer_malnutrition(poids, taille, age_mois, sexe, muac=None, oedemes=False):
    resultats = [
        _ligne("Poids pour l'âge", z_poids_age(poids, sexe, age_mois)),
        _ligne("Taille pour l'âge", z_taille_age(taille, sexe, age_mois)),
        _ligne("Poids pour la taille", z_poids_taille(poids, taille, sexe, age_mois)),
    ]
    if muac is not None:
        resultats.append(_ligne_muac(muac, age_mois))
    if oedemes:
        resultats.insert(0, {
            "indicateur": "Œdèmes bilatéraux",
            "statut": "Malnutrition aiguë sévère",
            "couleur": "danger",
            "z": None,
            "note": (
                "Des œdèmes des deux pieds signent une malnutrition aiguë sévère, "
                "quels que soient le poids et le périmètre brachial. Conduisez "
                "l'enfant au centre de santé aujourd'hui."
            ),
        })
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
            oedemes = request.POST.get("oedemes") == "oui"
            ev = evaluer_malnutrition(poids, taille, age_mois, sexe, muac, oedemes)
            ordre = {"danger": 0, "warning": 1, "info": 2, "success": 3}
            pire = min((ordre.get(e["couleur"], 3) for e in ev), default=3)
            if pire == 0:
                synthese = "Malnutrition sévère. Amenez l'enfant dans un centre de santé aujourd'hui."
            elif pire == 1:
                synthese = "Malnutrition modérée. Montrez-le à un soignant bientôt."
            else:
                synthese = "État nutritionnel normal d'après cet outil. Ce n'est pas un diagnostic."
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
            courbes = courbes_svg(sexe, age_mois, poids, taille)
        except Exception as e:
            resultats = {"erreur": str(e)}

    return render(request, "enfants/malnutrition.html", {
        "resultats": resultats,
        "svg_poids": courbes["poids"] if courbes else "",
        "svg_taille": courbes["taille"] if courbes else "",
        "svg_poids_taille": courbes.get("poids_taille", "") if courbes else "",
    })
