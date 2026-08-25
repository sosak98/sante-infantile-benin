"""
Données de référence (seed) - vaccins PEV Bénin + conseils nutritionnels.

Ces listes sont utilisées par la commande `python manage.py seed`.
Le seed est idempotent : il n'ajoute les données que si les tables sont vides,
donc il peut être relancé à chaque déploiement sans écraser les données.
"""

VACCINS = [
    # Naissance
    {"nom": "BCG", "age_affichage": "Naissance", "age_min_mois": 0, "age_max_mois": None, "description": "Protection contre la tuberculose", "obligatoire": True},
    {"nom": "VPO 0 (Polio oral)", "age_affichage": "Naissance", "age_min_mois": 0, "age_max_mois": None, "description": "1ère dose vaccin contre la poliomyélite", "obligatoire": True},
    {"nom": "Hépatite B", "age_affichage": "Naissance", "age_min_mois": 0, "age_max_mois": None, "description": "1ère dose protection contre l'hépatite B", "obligatoire": True},

    # 6 semaines
    {"nom": "Pentavalent 1", "age_affichage": "6 semaines", "age_min_mois": 2, "age_max_mois": None, "description": "Diphtérie, Tétanos, Coqueluche, Hépatite B, Hib - 1ère dose", "obligatoire": True},
    {"nom": "VPO 1", "age_affichage": "6 semaines", "age_min_mois": 2, "age_max_mois": None, "description": "2ème dose vaccin polio oral", "obligatoire": True},
    {"nom": "Pneumocoque 1 (PCV)", "age_affichage": "6 semaines", "age_min_mois": 2, "age_max_mois": None, "description": "Protection contre les pneumonies et méningites - 1ère dose", "obligatoire": True},

    # 10 semaines
    {"nom": "Pentavalent 2", "age_affichage": "10 semaines", "age_min_mois": 3, "age_max_mois": None, "description": "Diphtérie, Tétanos, Coqueluche, Hépatite B, Hib - 2ème dose", "obligatoire": True},
    {"nom": "VPO 2", "age_affichage": "10 semaines", "age_min_mois": 3, "age_max_mois": None, "description": "3ème dose vaccin polio oral", "obligatoire": True},
    {"nom": "Pneumocoque 2 (PCV)", "age_affichage": "10 semaines", "age_min_mois": 3, "age_max_mois": None, "description": "Protection contre les pneumonies - 2ème dose", "obligatoire": True},

    # 14 semaines
    {"nom": "Pentavalent 3", "age_affichage": "14 semaines", "age_min_mois": 4, "age_max_mois": None, "description": "Diphtérie, Tétanos, Coqueluche, Hépatite B, Hib - 3ème dose", "obligatoire": True},
    {"nom": "VPO 3", "age_affichage": "14 semaines", "age_min_mois": 4, "age_max_mois": None, "description": "4ème dose vaccin polio oral", "obligatoire": True},
    {"nom": "Pneumocoque 3 (PCV)", "age_affichage": "14 semaines", "age_min_mois": 4, "age_max_mois": None, "description": "Protection contre les pneumonies - 3ème dose", "obligatoire": True},

    # 6-7 mois
    {"nom": "Vaccin Antipaludique 1 (RTS,S)", "age_affichage": "6 mois", "age_min_mois": 6, "age_max_mois": None, "description": "1ère dose vaccin contre le paludisme - introduit au Bénin en 2024", "obligatoire": True},
    {"nom": "Vaccin Antipaludique 2 (RTS,S)", "age_affichage": "7 mois", "age_min_mois": 7, "age_max_mois": None, "description": "2ème dose vaccin contre le paludisme", "obligatoire": True},

    # 9 mois
    {"nom": "VAR (Rougeole-Rubéole)", "age_affichage": "9 mois", "age_min_mois": 9, "age_max_mois": None, "description": "Protection contre la rougeole et la rubéole", "obligatoire": True},
    {"nom": "VAA (Fièvre jaune)", "age_affichage": "9 mois", "age_min_mois": 9, "age_max_mois": None, "description": "Protection contre la fièvre jaune - obligatoire au Bénin", "obligatoire": True},
    {"nom": "MenA (Méningite A)", "age_affichage": "9 mois", "age_min_mois": 9, "age_max_mois": None, "description": "Protection contre la méningite à méningocoque A", "obligatoire": True},
    {"nom": "Vaccin Antipaludique 3 (RTS,S)", "age_affichage": "9 mois", "age_min_mois": 9, "age_max_mois": None, "description": "3ème dose vaccin contre le paludisme", "obligatoire": True},

    # 18 mois et plus
    {"nom": "Vaccin Antipaludique 4 (RTS,S)", "age_affichage": "18-23 mois", "age_min_mois": 18, "age_max_mois": 23, "description": "4ème et dernière dose vaccin contre le paludisme", "obligatoire": True},
    {"nom": "VAR 2 (Rappel Rougeole)", "age_affichage": "18 mois", "age_min_mois": 18, "age_max_mois": None, "description": "Rappel vaccin rougeole-rubéole", "obligatoire": True},
]


CONSEILS = [
    # 0-6 mois
    {"titre": "Allaitement maternel exclusif", "age_min_mois": 0, "age_max_mois": 6, "categorie": "aliment", "contenu": "L'OMS recommande l'allaitement maternel exclusif pendant les 6 premiers mois. Le lait maternel contient tous les nutriments nécessaires et protège contre les infections. Aucun autre aliment ni liquide n'est nécessaire.", "mots_cles": "allaitement, lait maternel, nouveau-né"},
    {"titre": "Colostrum - premier lait précieux", "age_min_mois": 0, "age_max_mois": 1, "categorie": "aliment", "contenu": "Le colostrum est le premier lait produit après l'accouchement. Jaune et épais, il est riche en anticorps et nutriments. Il protège le nouveau-né contre les infections et favorise son immunité. Ne jamais le jeter.", "mots_cles": "colostrum, nouveau-né, immunité"},
    {"titre": "Fréquence des tétées", "age_min_mois": 0, "age_max_mois": 6, "categorie": "aliment", "contenu": "Allaiter à la demande, au moins 8 à 12 fois par 24 heures. Ne pas imposer un horaire fixe. Plus l'enfant tète, plus la production de lait augmente. Les tétées nocturnes sont importantes.", "mots_cles": "allaitement, tétée, fréquence"},
    {"titre": "Diarrhée chez le nourrisson", "age_min_mois": 0, "age_max_mois": 6, "categorie": "probleme", "contenu": "En cas de diarrhée, continuer l'allaitement maternel. Donner des SRO. Consulter immédiatement si la diarrhée dure plus de 3 jours ou si l'enfant présente des signes de déshydratation.", "mots_cles": "diarrhée, SRO, réhydratation"},
    {"titre": "Fièvre chez le nourrisson", "age_min_mois": 0, "age_max_mois": 6, "categorie": "probleme", "contenu": "En cas de fièvre, augmenter les tétées. Consulter immédiatement si la fièvre dépasse 38,5 degrés chez un nourrisson de moins de 3 mois. Ne jamais donner d'aspirine à un nourrisson.", "mots_cles": "fièvre, nourrisson, urgence"},

    # 6-12 mois
    {"titre": "Introduction des aliments complémentaires", "age_min_mois": 6, "age_max_mois": 12, "categorie": "aliment", "contenu": "À partir de 6 mois, introduire progressivement des aliments complémentaires tout en continuant l'allaitement. Commencer par des purées lisses de légumes, céréales et fruits. Un seul aliment nouveau à la fois, attendre 3 jours avant d'en introduire un autre.", "mots_cles": "diversification, purée, introduction aliments"},
    {"titre": "Aliments riches en fer à 6 mois", "age_min_mois": 6, "age_max_mois": 12, "categorie": "aliment", "contenu": "Les réserves en fer du nourrisson s'épuisent vers 6 mois. Introduire des aliments riches en fer : viande mixée, foie de volaille, haricots, lentilles, légumes verts. La carence en fer cause l'anémie.", "mots_cles": "fer, anémie, viande, légumineuses"},
    {"titre": "Texture des aliments selon l'âge", "age_min_mois": 6, "age_max_mois": 12, "categorie": "aliment", "contenu": "6-7 mois : purées très lisses. 7-8 mois : purées avec petits morceaux. 8-10 mois : aliments écrasés à la fourchette. 10-12 mois : petits morceaux tendres.", "mots_cles": "texture, purée, morceaux"},
    {"titre": "Diarrhée et diversification", "age_min_mois": 6, "age_max_mois": 12, "categorie": "probleme", "contenu": "Si l'enfant fait de la diarrhée après introduction d'un nouvel aliment, arrêter cet aliment et réessayer plus tard. Continuer l'allaitement. Donner des SRO si nécessaire.", "mots_cles": "diarrhée, allergie, diversification"},
    {"titre": "Signes de bonne alimentation", "age_min_mois": 6, "age_max_mois": 12, "categorie": "probleme", "contenu": "Un enfant bien nourri : prend du poids régulièrement, est actif et éveillé, a des urines claires, dort bien. Si l'enfant est apathique ou ne prend pas de poids, consultez un professionnel.", "mots_cles": "croissance, poids, développement"},

    # 12-24 mois
    {"titre": "Alimentation à 12-24 mois", "age_min_mois": 12, "age_max_mois": 24, "categorie": "aliment", "contenu": "L'enfant mange 3 repas par jour plus 2 collations. Continuer l'allaitement. Proposer : céréales, légumineuses, légumes variés, fruits, viande ou poisson ou œufs. Éviter le sel ajouté et le sucre raffiné.", "mots_cles": "repas, céréales, légumineuses"},
    {"titre": "Continuer l'allaitement jusqu'à 2 ans", "age_min_mois": 12, "age_max_mois": 24, "categorie": "aliment", "contenu": "L'OMS recommande de continuer l'allaitement jusqu'à 2 ans et au-delà, en complément des aliments solides. Le lait maternel reste une source importante de nutriments et d'anticorps.", "mots_cles": "allaitement, 2 ans, complément"},
    {"titre": "Malnutrition - signes d'alerte 12-24 mois", "age_min_mois": 12, "age_max_mois": 24, "categorie": "probleme", "contenu": "Signes de malnutrition : poids insuffisant, œdèmes aux pieds, cheveux roux et cassants, ventre gonflé, enfant apathique, MUAC inférieur à 11,5 cm. Consulter immédiatement un centre de santé.", "mots_cles": "malnutrition, kwashiorkor, MUAC"},
    {"titre": "Hydratation de l'enfant", "age_min_mois": 12, "age_max_mois": 24, "categorie": "aliment", "contenu": "Donner de l'eau potable à l'enfant. Éviter les sodas et jus industriels. L'eau reste la meilleure boisson. En saison chaude, augmenter les apports en liquides.", "mots_cles": "eau, hydratation, boisson"},

    # 24-60 mois
    {"titre": "Alimentation équilibrée 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "aliment", "contenu": "3 repas principaux plus 1 à 2 collations par jour. Chaque repas doit contenir une source d'énergie (céréales), une source de protéines (viande, poisson, œufs, légumineuses), des légumes et fruits variés.", "mots_cles": "équilibre alimentaire, repas, protéines"},
    {"titre": "Vitamine A - importance cruciale 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "aliment", "contenu": "La carence en vitamine A est fréquente au Bénin. Sources : huile de palme rouge, patate douce orange, mangue, papaye, feuilles vertes, foie. La supplémentation en vitamine A est recommandée tous les 6 mois.", "mots_cles": "vitamine A, cécité, huile de palme"},
    {"titre": "Parasitoses intestinales 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "probleme", "contenu": "Les vers intestinaux causent malnutrition et anémie. Prévention : se laver les mains avant de manger et après les toilettes, boire de l'eau potable, cuire les aliments. Déparasitage recommandé tous les 6 mois.", "mots_cles": "vers, parasites, déparasitage, hygiène"},
    {"titre": "Aliments locaux nutritifs au Bénin 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "aliment", "contenu": "Privilégier les aliments locaux : gari, akassa, ablo (énergie), haricots et niébé (protéines), feuilles de moringa (vitamines et fer), huile de palme rouge (vitamine A), poisson fumé (protéines et oméga-3).", "mots_cles": "aliments locaux, Bénin, moringa, niébé"},
    {"titre": "Obésité et surpoids 2-5 ans", "age_min_mois": 24, "age_max_mois": 60, "categorie": "probleme", "contenu": "L'obésité infantile est en augmentation en Afrique. Limiter les aliments ultra-transformés et sucrés, encourager l'activité physique, privilégier les repas faits maison.", "mots_cles": "obésité, surpoids, sucre, activité physique"},

    # 60-120 mois
    {"titre": "Alimentation scolaire 5-10 ans", "age_min_mois": 60, "age_max_mois": 120, "categorie": "aliment", "contenu": "L'enfant d'âge scolaire a besoin d'un petit-déjeuner complet pour se concentrer à l'école. 3 repas équilibrés par jour. Limiter les biscuits industriels et sodas. Privilégier les fruits locaux comme collation.", "mots_cles": "école, petit-déjeuner, collation, concentration"},
    {"titre": "Anémie chez l'enfant scolarisé", "age_min_mois": 60, "age_max_mois": 120, "categorie": "probleme", "contenu": "L'anémie touche de nombreux enfants scolarisés au Bénin. Signes : fatigue, pâleur des conjonctives, difficultés de concentration. Causes : carence en fer, parasites, paludisme. Alimentation riche en fer et vitamine C.", "mots_cles": "anémie, fer, pâleur, fatigue, école"},
    {"titre": "Aliments locaux nutritifs 5-10 ans", "age_min_mois": 60, "age_max_mois": 120, "categorie": "aliment", "contenu": "Privilégier les aliments locaux : igname, manioc, maïs, mil pour l'énergie. Haricots, niébé, arachides pour les protéines. Légumes feuilles, tomates, carottes pour les vitamines. Poisson et viande 2 à 3 fois par semaine.", "mots_cles": "aliments locaux, igname, manioc, protéines"},
    {"titre": "Parasitoses intestinales 5-10 ans", "age_min_mois": 60, "age_max_mois": 120, "categorie": "probleme", "contenu": "Les vers intestinaux restent fréquents chez les enfants scolarisés. Déparasitage tous les 6 mois. Hygiène des mains essentielle avant les repas et après les toilettes. Porter des chaussures pour éviter les ankylostomes.", "mots_cles": "vers, déparasitage, hygiène, chaussures"},
]
