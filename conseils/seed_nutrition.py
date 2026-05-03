import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'santeinfantile.settings')
django.setup()

from conseils.models import ConseilNutritionnel

ConseilNutritionnel.objects.all().delete()

conseils = [
    # 0-6 mois
    {"titre": "Allaitement maternel exclusif", "age_min_mois": 0, "age_max_mois": 6, "categorie": "aliment", "contenu": "L'OMS recommande l'allaitement maternel exclusif pendant les 6 premiers mois. Le lait maternel contient tous les nutriments necessaires et protege contre les infections. Aucun autre aliment ni liquide n'est necessaire.", "mots_cles": "allaitement, lait maternel, nouveau-ne"},
    {"titre": "Colostrum - premier lait precieux", "age_min_mois": 0, "age_max_mois": 1, "categorie": "aliment", "contenu": "Le colostrum est le premier lait produit apres l'accouchement. Jaune et epais, il est riche en anticorps et nutriments. Il protege le nouveau-ne contre les infections et favorise son immunite. Ne jamais le jeter.", "mots_cles": "colostrum, nouveau-ne, immunite"},
    {"titre": "Frequence des tetees", "age_min_mois": 0, "age_max_mois": 6, "categorie": "aliment", "contenu": "Allaiter a la demande, au moins 8 a 12 fois par 24 heures. Ne pas imposer un horaire fixe. Plus l'enfant tete, plus la production de lait augmente. Les tetees nocturnes sont importantes.", "mots_cles": "allaitement, tetee, frequence"},
    {"titre": "Diarrhee chez le nourrisson", "age_min_mois": 0, "age_max_mois": 6, "categorie": "probleme", "contenu": "En cas de diarrhee, continuer l'allaitement maternel. Donner des SRO. Consulter immediatement si la diarrhee dure plus de 3 jours ou si l'enfant presente des signes de deshydratation.", "mots_cles": "diarrhee, SRO, rehydratation"},
    {"titre": "Fievre chez le nourrisson", "age_min_mois": 0, "age_max_mois": 6, "categorie": "probleme", "contenu": "En cas de fievre, augmenter les tetees. Consulter immediatement si la fievre depasse 38.5 degres chez un nourrisson de moins de 3 mois. Ne jamais donner d'aspirine a un nourrisson.", "mots_cles": "fievre, nourrisson, urgence"},

    # 6-12 mois
    {"titre": "Introduction des aliments complementaires", "age_min_mois": 6, "age_max_mois": 12, "categorie": "aliment", "contenu": "A partir de 6 mois, introduire progressivement des aliments complementaires tout en continuant l'allaitement. Commencer par des purees lisses de legumes, cereales et fruits. Un seul aliment nouveau a la fois, attendre 3 jours avant d'en introduire un autre.", "mots_cles": "diversification, puree, introduction aliments"},
    {"titre": "Aliments riches en fer a 6 mois", "age_min_mois": 6, "age_max_mois": 12, "categorie": "aliment", "contenu": "Les reserves en fer du nourrisson s'epuisent vers 6 mois. Introduire des aliments riches en fer : viande mixee, foie de volaille, haricots, lentilles, legumes verts. La carence en fer cause l'anemie.", "mots_cles": "fer, anemie, viande, legumineuses"},
    {"titre": "Texture des aliments selon l'age", "age_min_mois": 6, "age_max_mois": 12, "categorie": "aliment", "contenu": "6-7 mois : purees tres lisses. 7-8 mois : purees avec petits morceaux. 8-10 mois : aliments ecrases a la fourchette. 10-12 mois : petits morceaux tendres.", "mots_cles": "texture, puree, morceaux"},
    {"titre": "Diarrhee et diversification", "age_min_mois": 6, "age_max_mois": 12, "categorie": "probleme", "contenu": "Si l'enfant fait de la diarrhee apres introduction d'un nouvel aliment, arreter cet aliment et reessayer plus tard. Continuer l'allaitement. Donner des SRO si necessaire.", "mots_cles": "diarrhee, allergie, diversification"},
    {"titre": "Signes de bonne alimentation", "age_min_mois": 6, "age_max_mois": 12, "categorie": "probleme", "contenu": "Un enfant bien nourri : prend du poids regulierement, est actif et eveille, a des urines claires, dort bien. Si l'enfant est apathique ou ne prend pas de poids, consultez un professionnel.", "mots_cles": "croissance, poids, developpement"},

    # 12-24 mois
    {"titre": "Alimentation a 12-24 mois", "age_min_mois": 12, "age_max_mois": 24, "categorie": "aliment", "contenu": "L'enfant mange 3 repas par jour plus 2 collations. Continuer l'allaitement. Proposer : cereales, legumineuses, legumes varies, fruits, viande ou poisson ou oeufs. Eviter le sel ajoute et le sucre rafine.", "mots_cles": "repas, cereales, legumineuses"},
    {"titre": "Continuer l'allaitement jusqu'a 2 ans", "age_min_mois": 12, "age_max_mois": 24, "categorie": "aliment", "contenu": "L'OMS recommande de continuer l'allaitement jusqu'a 2 ans et au-dela, en complement des aliments solides. Le lait maternel reste une source importante de nutriments et d'anticorps.", "mots_cles": "allaitement, 2 ans, complement"},
    {"titre": "Malnutrition - signes d'alerte 12-24 mois", "age_min_mois": 12, "age_max_mois": 24, "categorie": "probleme", "contenu": "Signes de malnutrition : poids insuffisant, oedemes aux pieds, cheveux roux et cassants, ventre gonfle, enfant apathique, MUAC inferieur a 11.5 cm. Consulter immediatement un centre de sante.", "mots_cles": "malnutrition, kwashiorkor, MUAC"},
    {"titre": "Hydratation de l'enfant", "age_min_mois": 12, "age_max_mois": 24, "categorie": "aliment", "contenu": "Donner de l'eau potable a l'enfant. Eviter les sodas et jus industriels. L'eau reste la meilleure boisson. En saison chaude, augmenter les apports en liquides.", "mots_cles": "eau, hydratation, boisson"},

    # 24-60 mois
    {"titre": "Alimentation equilibree 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "aliment", "contenu": "3 repas principaux plus 1 a 2 collations par jour. Chaque repas doit contenir une source d'energie (cereales), une source de proteines (viande, poisson, oeufs, legumineuses), des legumes et fruits varies.", "mots_cles": "equilibre alimentaire, repas, proteines"},
    {"titre": "Vitamine A - importance cruciale 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "aliment", "contenu": "La carence en vitamine A est frequente au Benin. Sources : huile de palme rouge, patate douce orange, mangue, papaye, feuilles vertes, foie. La supplementation en vitamine A est recommandee tous les 6 mois.", "mots_cles": "vitamine A, cecite, huile de palme"},
    {"titre": "Parasitoses intestinales 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "probleme", "contenu": "Les vers intestinaux causent malnutrition et anemie. Prevention : se laver les mains avant de manger et apres les toilettes, boire de l'eau potable, cuire les aliments. Deparasitage recommande tous les 6 mois.", "mots_cles": "vers, parasites, deparasitage, hygiene"},
    {"titre": "Aliments locaux nutritifs au Benin 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "aliment", "contenu": "Privilegier les aliments locaux : gari, akassa, ablo (energie), haricots et niebe (proteines), feuilles de moringa (vitamines et fer), huile de palme rouge (vitamine A), poisson fume (proteines et omega-3).", "mots_cles": "aliments locaux, Benin, moringa, niebe"},
    {"titre": "Obesite et surpoids 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "probleme", "contenu": "L'obesite infantile est en augmentation en Afrique. Limiter les aliments ultra-transformes et sucres, encourager l'activite physique, privilegier les repas faits maison.", "mots_cles": "obesite, surpoids, sucre, activite physique"},

    # 60-120 mois
    {"titre": "Alimentation scolaire 5-10 ans", "age_min_mois": 60, "age_max_mois": 120, "categorie": "aliment", "contenu": "L'enfant d'age scolaire a besoin d'un petit-dejeuner complet pour se concentrer a l'ecole. 3 repas equilibres par jour. Limiter les biscuits industriels et sodas. Privilegier les fruits locaux comme collation.", "mots_cles": "ecole, petit-dejeuner, collation, concentration"},
    {"titre": "Anemie chez l'enfant scolarise", "age_min_mois": 60, "age_max_mois": 120, "categorie": "probleme", "contenu": "L'anemie touche de nombreux enfants scolarises au Benin. Signes : fatigue, paleur des conjonctives, difficultes de concentration. Causes : carence en fer, parasites, paludisme. Alimentation riche en fer et vitamine C.", "mots_cles": "anemie, fer, paleur, fatigue, ecole"},
    {"titre": "Aliments locaux nutritifs 5-10 ans", "age_min_mois": 60, "age_max_mois": 120, "categorie": "aliment", "contenu": "Privilegier les aliments locaux : igname, manioc, mais, mil pour l'energie. Haricots, niebe, arachides pour les proteines. Legumes feuilles, tomates, carottes pour les vitamines. Poisson et viande 2 a 3 fois par semaine.", "mots_cles": "aliments locaux, igname, manioc, proteines"},
    {"titre": "Parasitoses intestinales 5-10 ans", "age_min_mois": 60, "age_max_mois": 120, "categorie": "probleme", "contenu": "Les vers intestinaux restent frequents chez les enfants scolarises. Deparasitage tous les 6 mois. Hygiene des mains essentielle avant les repas et apres les toilettes. Porter des chaussures pour eviter les ankylostomes.", "mots_cles": "vers, deparasitage, hygiene, chaussures"},
]

for c in conseils:
    ConseilNutritionnel.objects.create(**c)

print(f"{len(conseils)} conseils nutritionnels ajoutes avec succes !")
