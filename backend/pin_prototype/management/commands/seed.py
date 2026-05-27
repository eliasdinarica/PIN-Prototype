"""
Seed command — données réelles pour le canton de Neuchâtel (NE).

Usage:
    python manage.py seed            # additif (get_or_create)
    python manage.py seed --reset    # efface tout puis recrée
"""

from django.core.management.base import BaseCommand
from pin_prototype.models import Audience, Category, Subcategory, Tag, Resource

# ---------------------------------------------------------------------------
# Helpers — construction des corps d'articles (format Editor.js)
# ---------------------------------------------------------------------------

def para(text):
    return {'type': 'paragraph', 'data': {'text': text}}

def h3(text):
    return {'type': 'header', 'data': {'text': text, 'level': 3}}

def ul(*items):
    return {'type': 'list', 'data': {'style': 'unordered', 'items': list(items)}}

def ol(*items):
    return {'type': 'list', 'data': {'style': 'ordered', 'items': list(items)}}

def sec(title, *blocks, width='full'):
    return {'title': title, 'width': width, 'body': {'blocks': list(blocks)}}

def body(*sections):
    return {'sections': list(sections)}


# ---------------------------------------------------------------------------
# Tags
# ---------------------------------------------------------------------------

TAGS = [
    'Formulaire', 'En personne', 'En ligne', 'Hotline',
    'Gratuit', 'Urgence', 'Traduction disponible', 'Interprete', 'Multilingue',
    'Logement', 'Logement urgence', 'Logement social',
    'Droits du locataire', 'Bail', 'Depot de garantie', 'Assurance menage',
    'Sante', 'Sante mentale', 'Medecin', 'Assurance maladie',
    'Reduction de prime', 'Maternite', 'Handicap', 'Vaccination',
    'Travail', 'Recherche emploi', 'Droit du travail',
    'Salaire', 'Independent', 'Chomage', 'CV candidature',
    'Formation', 'Apprentissage', 'Universite',
    'Langue', 'Cours de langue', 'Reconnaissance diplome', 'E-learning',
    'Droits', 'Documents officiels', 'Permis sejour',
    'Naturalisation', 'Asile', 'Aide juridique', 'Regroupement familial', 'Discrimination',
    'Budget', 'Aide sociale', 'Allocation', 'Subvention',
    'Impots', 'Banque', 'Alimentation',
    'Mobilite', 'Transports publics', 'Permis de conduire', 'Velo', 'Transport medical',
    'Famille', 'Enfants', 'Garde enfants', 'Scolarisation',
    'Allocations familiales', 'Soutien scolaire', 'Droits parentaux',
    'Femmes', 'Jeune', 'Senior',
    'Permis N/F/S', 'Permis B', 'Permis C', 'Permis G',
    'Integration', 'Vie sociale', 'Culture',
]

# ---------------------------------------------------------------------------
# Audiences
# ---------------------------------------------------------------------------

AUDIENCES = [
    {
        'name': "Demandeur d'asile",
        'description': "Titulaires d'un permis N, F ou S.",
        'statuses': 'N,F,S', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis N/F/S', 'Asile', 'Droits', 'Aide sociale', 'Urgence', 'Logement urgence', 'Interprete'],
    },
    {
        'name': 'Parents',
        'description': "Personnes ayant des enfants à charge.",
        'statuses': '', 'has_children': True,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Garde enfants', 'Enfants', 'Famille', 'Scolarisation', 'Allocations familiales', 'Soutien scolaire'],
    },
    {
        'name': 'Nouveaux arrivants',
        'description': "Arrivés en Suisse depuis moins d'un an.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': False, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Logement', 'Langue', 'Cours de langue', 'Documents officiels', 'Assurance maladie', 'Banque', 'Traduction disponible'],
    },
    {
        'name': "Établis depuis plus d'un an",
        'description': "En phase d'intégration avancée.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': True, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Formation', 'Reconnaissance diplome', 'Naturalisation', 'Vie sociale'],
    },
    {
        'name': 'Résident long terme',
        'description': "Titulaires d'un permis B ou C.",
        'statuses': 'B,C', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis B', 'Permis C', 'Droits', 'Naturalisation', 'Impots'],
    },
    {
        'name': 'Frontalier',
        'description': "Titulaires d'un permis G.",
        'statuses': 'G', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis G', 'Mobilite', 'Travail', 'Droit du travail', 'Impots'],
    },
    {
        'name': 'Jeune adulte',
        'description': "18 à 30 ans.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': 18, 'max_age': 30,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Formation', 'Jeune', 'Cours de langue', 'Apprentissage', 'Universite', 'CV candidature', 'Recherche emploi'],
    },
    {
        'name': 'Senior',
        'description': "60 ans et plus.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': 60, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Senior', 'Sante', 'Mobilite', 'Transport medical', 'Aide sociale', 'Handicap'],
    },
    {
        'name': 'Femmes',
        'description': "Ressources spécifiquement destinées aux femmes migrantes.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Femmes', 'Sante mentale', 'Aide juridique'],
    },
    {
        'name': 'Avec permis de conduire',
        'description': "Personnes titulaires d'un permis de conduire.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': True, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis de conduire', 'Mobilite', 'Transports publics'],
    },
    {
        'name': 'Compétences numériques de base',
        'description': "Personnes sachant utiliser internet et les services en ligne.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': 'basic', 'min_education_level': '',
        'relevant_tags': ['En ligne', 'E-learning', 'Formulaire'],
    },
    {
        'name': 'Compétences numériques avancées',
        'description': "Personnes à l'aise avec les outils numériques et bureautiques.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': 'advanced', 'min_education_level': '',
        'relevant_tags': ['En ligne', 'E-learning', 'CV candidature', 'Universite'],
    },
    {
        'name': 'Formation supérieure',
        'description': "Personnes avec un diplôme universitaire ou équivalent.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': 'bachelor',
        'relevant_tags': ['Reconnaissance diplome', 'Universite', 'Formation', 'CV candidature'],
    },
]

# ---------------------------------------------------------------------------
# Catégories + Ressources
# ---------------------------------------------------------------------------

CATEGORIES = [

    # -----------------------------------------------------------------------
    {
        'name': 'Work',
        'description': "Trouver un emploi, s'inscrire à l'ORP et préparer son CV suisse.",
        'icon': 'BriefcaseIcon',
        'priority': 10,
        'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an"],
        'resources': [

            {
                'name': "Je cherche du travail, par où commencer ?",
                'description': "Le ONE m'aide à chercher un emploi. Si j'ai cotisé en Suisse, je peux aussi recevoir de l'argent chaque mois pendant ma recherche.",
                'tags': ['Recherche emploi', 'Travail', 'Chomage', 'Formulaire', 'En personne', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Résident long terme'],
                'body': body(
                    sec("À quoi ça sert",
                        para("L'ORP (Office Régional de Placement) s'appelle ONE à Neuchâtel. C'est le service public qui aide les personnes sans emploi à trouver un travail."),
                        para("Si vous avez travaillé en Suisse et cotisé à l'assurance chômage, vous pouvez aussi recevoir des indemnités de chômage — de l'argent chaque mois pendant votre recherche."),
                    ),
                    sec("Qui peut s'inscrire",
                        ul(
                            "Vous avez travaillé en Suisse et cotisé à l'assurance chômage",
                            "Vous avez un permis de séjour valide (B, C, ou parfois L)",
                            "Vous êtes disponible pour travailler immédiatement",
                            "Les ressortissants UE/AELE ont les mêmes droits que les Suisses",
                        ),
                    ),
                    sec("Comment faire",
                        ol(
                            "Inscrivez-vous dès le premier jour sans emploi — ne pas attendre",
                            "En ligne sur <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a> (disponible 24h/24)",
                            "L'ONE vous contacte dans les 24–48 heures pour un rendez-vous",
                            "Inscrivez-vous aussi à une caisse de chômage (CCNAC ou une caisse syndicale)",
                            "Cherchez activement : envoyez 8 à 12 candidatures par mois, gardez une preuve de chaque envoi",
                        ),
                    ),
                    sec("Documents à apporter",
                        ul(
                            "Carte d'identité ou passeport + permis de séjour",
                            "Numéro AVS (votre numéro d'assurance sociale suisse)",
                            "Attestation de votre dernier employeur",
                            "Certificats de travail",
                            "CV à jour",
                        ),
                    ),
                    sec("ONE Neuchâtel (ville)", ul(
                        "<b>Adresse :</b> Avenue Edouard-Dubois 20, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 68 18",
                        "<b>Email :</b> one@ne.ch",
                        "<b>Sur rendez-vous uniquement</b> (pris après inscription en ligne)",
                        "<b>Téléphone :</b> lun–ven 8h–12h / lun–jeu 13h30–17h",
                    ), width='half'),
                    sec("ONE La Chaux-de-Fonds", ul(
                        "<b>Adresse :</b> Espacité 1, 2302 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 889 69 00",
                        "<b>Email :</b> one@ne.ch",
                        "<b>Inscription :</b> <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a>",
                        "<b>Caisse chômage (CCNAC) :</b> Espacité 4, CDF — 032 889 67 90",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux préparer un CV pour trouver du travail en Suisse",
                'description': "Le CV suisse a des règles différentes. Je dois savoir quoi mettre et comment le présenter pour avoir des chances.",
                'tags': ['CV candidature', 'Recherche emploi', 'Travail', 'Formation'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Jeune adulte'],
                'body': body(
                    sec("Le CV suisse — ce qui est différent",
                        ul(
                            "Maximum 2 pages (1 page si moins de 10 ans d'expérience)",
                            "Photo recommandée (professionnelle, fond neutre)",
                            "Pas de mention de l'état civil ni de religion",
                            "Ordre antichronologique : expérience la plus récente en premier",
                            "Langues : indiquez votre niveau (A1 à C2 ou débutant / intermédiaire / avancé / maternel)",
                        ),
                    ),
                    sec("Structure type",
                        ol(
                            "Coordonnées (nom, téléphone, email, adresse)",
                            "Photo",
                            "Résumé professionnel (3–4 lignes)",
                            "Expériences professionnelles (avec dates et lieu)",
                            "Formation et diplômes",
                            "Compétences et langues",
                            "Références (sur demande ou avec noms et contacts)",
                        ),
                    ),
                    sec("Aide gratuite à Neuchâtel",
                        ul(
                            "<b>ONE Neuchâtel :</b> ateliers CV et simulation d'entretien — demandez à votre conseiller",
                            "<b>COSM :</b> accompagnement à la recherche d'emploi — 032 889 74 42",
                            "<b>CNIP :</b> bilan de compétences et réorientation — <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a>",
                            "<b>Offres d'emploi :</b> <a href='https://www.jobs.ch' target='_blank'>jobs.ch</a>, <a href='https://www.indeed.ch' target='_blank'>indeed.ch</a>, <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a>",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux me former ou changer de métier",
                'description': "Le CNIP m'accompagne pour évaluer mes compétences, me former ou faire reconnaître mon expérience professionnelle.",
                'tags': ['Formation', 'Travail', 'Reconnaissance diplome', 'En personne', 'Gratuit'],
                'audiences': ["Établis depuis plus d'un an", 'Formation supérieure'],
                'body': body(
                    sec("Qu'est-ce que le CNIP",
                        para("Le Centre Neuchâtelois d'Intégration Professionnelle (CNIP) aide les adultes à trouver leur place dans le monde du travail suisse. Il s'adresse surtout aux personnes qui ont de l'expérience à l'étranger mais qui ont du mal à la faire reconnaître."),
                    ),
                    sec("Ce qu'ils proposent",
                        ul(
                            "Bilan de compétences pour évaluer vos acquis professionnels",
                            "Aide à la reconnaissance de diplômes étrangers",
                            "Formation professionnelle raccourcie (AFP/CFC pour adultes)",
                            "Coaching pour la recherche d'emploi dans votre domaine",
                            "Mise en relation avec des employeurs neuchâtelois",
                        ),
                    ),
                    sec("Contact CNIP", ul(
                        "<b>Adresse :</b> Site Dubied 12, CP 176, 2108 Couvet (Val-de-Travers)",
                        "<b>Téléphone :</b> 032 889 69 25",
                        "<b>Site :</b> <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a>",
                        "<b>Accès :</b> sur orientation du ONE ou du COSM",
                    ), width='half'),
                    sec("Autres ressources formation", ul(
                        "<b>Formation professionnelle NE :</b> <a href='https://www.ne.ch/formation' target='_blank'>ne.ch/formation</a>",
                        "<b>Reconnaissance diplômes :</b> <a href='https://www.reconnaissance.swiss' target='_blank'>reconnaissance.swiss</a>",
                        "<b>Orientation professionnelle :</b> <a href='https://www.berufsberatung.ch/fr' target='_blank'>berufsberatung.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux travailler à mon compte en Suisse",
                'description': "Je veux créer mon activité indépendante. Voici les étapes à suivre et ce que la loi m'impose.",
                'tags': ['Independent', 'Travail', 'Droits', 'Formulaire', 'Budget', 'Documents officiels'],
                'audiences': ["Établis depuis plus d'un an", 'Résident long terme'],
                'body': body(
                    sec("Avant de commencer",
                        para("En Suisse, travailler à son compte est possible avec un permis B ou C. Avec un permis N ou F, c'est plus compliqué — renseignez-vous d'abord auprès du SMIG (Service des migrations de Neuchâtel)."),
                    ),
                    sec("Les étapes principales",
                        ol(
                            "Choisir votre forme juridique : raison individuelle (la plus simple), Sàrl ou SA",
                            "S'annoncer à la Caisse cantonale neuchâteloise de compensation (CCNC) — obligatoire",
                            "Inscrire votre entreprise au Registre du Commerce si chiffre d'affaires > CHF 100 000/an",
                            "S'immatriculer à la TVA si chiffre d'affaires > CHF 100 000/an",
                        ),
                    ),
                    sec("CCNC — Caisse cantonale", ul(
                        "<b>Adresse :</b> Faubourg de l'Hôpital 28, 2001 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 65 01",
                        "<b>Email :</b> ccnc@ne.ch",
                        "<b>Site :</b> <a href='https://www.caisseavsne.ch' target='_blank'>caisseavsne.ch</a>",
                    ), width='half'),
                    sec("À savoir", ul(
                        "Vous payez vous-même les cotisations AVS/AI/APG (environ 10 % du revenu)",
                        "Pas d'assurance chômage pour les indépendants",
                        "<b>Guide national :</b> <a href='https://www.kmu.admin.ch' target='_blank'>kmu.admin.ch</a>",
                        "<b>Aide gratuite :</b> <a href='https://www.biz.admin.ch' target='_blank'>biz.admin.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux connaître mes droits en tant qu'employé",
                'description': "Mon contrat, mon salaire, mes congés, ma protection si je suis licencié. Voici ce que la loi me garantit.",
                'tags': ['Droit du travail', 'Travail', 'Droits', 'Salaire'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Résident long terme'],
                'body': body(
                    sec("Le contrat de travail",
                        ul(
                            "Tout contrat peut être oral — mais exigez toujours un contrat écrit",
                            "Le contrat doit mentionner : salaire, durée de travail, délai de congé",
                            "Les conventions collectives de travail (CCT) fixent des minimums dans chaque branche",
                            "En Suisse, il n'y a pas de salaire minimum légal national — sauf dans les cantons et branches qui en ont un",
                        ),
                    ),
                    sec("Congés et absences",
                        ul(
                            "<b>Vacances :</b> minimum 4 semaines par an (5 semaines si moins de 20 ans)",
                            "<b>Jours fériés officiels NE :</b> 1er janvier, Vendredi saint, 1er août, Noël — vérifiez la liste complète sur ne.ch",
                            "<b>Maladie :</b> vous avez droit au salaire pendant votre arrêt maladie (selon l'ancienneté)",
                            "<b>Accident :</b> couvert par l'assurance accidents obligatoire (LAA) de votre employeur",
                        ),
                    ),
                    sec("En cas de licenciement",
                        ul(
                            "Délai de congé minimum : 1 mois (1re année), 2 mois (2e–9e année), 3 mois ensuite",
                            "Licenciement immédiat sans cause valable = droit à une indemnité",
                            "Licenciement abusif : recours possible devant le tribunal",
                        ),
                    ),
                    sec("Aide à Neuchâtel", ul(
                        "<b>Unia Neuchâtel :</b> syndicat — conseil juridique gratuit pour les membres — <a href='https://www.unia.ch' target='_blank'>unia.ch</a>",
                        "<b>Syna :</b> syndicat chrétien-social — <a href='https://www.syna.ch' target='_blank'>syna.ch</a>",
                        "<b>FER (Fédération patronale) :</b> pour vérifier les CCT de votre branche — <a href='https://www.fer-ne.ch' target='_blank'>fer-ne.ch</a>",
                        "<b>Guide officiel :</b> <a href='https://www.ch.ch/fr/travail/' target='_blank'>ch.ch/travail</a>",
                    ), width='full'),
                ),
            },

            {
                'name': "Je veux trouver du travail rapidement via une agence",
                'description': "Une agence d'intérim peut me trouver une mission en entreprise rapidement, même sans expérience suisse.",
                'tags': ['Recherche emploi', 'Travail', 'CV candidature', 'En ligne', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Jeune adulte'],
                'body': body(
                    sec("Comment ça fonctionne",
                        para("Une agence d'intérim vous place chez des entreprises pour des missions courtes ou longues. C'est un bon moyen de démarrer en Suisse, de construire une expérience locale et d'être ensuite recruté directement."),
                        ul(
                            "Vous êtes employé par l'agence — elle paie votre salaire et vos cotisations",
                            "Vous travaillez chez une entreprise cliente",
                            "Les missions durent de quelques jours à plusieurs mois",
                            "Vous avez les mêmes droits qu'un employé ordinaire (LAA, LAMal, etc.)",
                        ),
                    ),
                    sec("Agences présentes à Neuchâtel", ul(
                        "<b>Adecco :</b> <a href='https://www.adecco.ch' target='_blank'>adecco.ch</a> — bureau à Neuchâtel et La Chaux-de-Fonds",
                        "<b>Manpower :</b> <a href='https://www.manpower.ch' target='_blank'>manpower.ch</a>",
                        "<b>Randstad :</b> <a href='https://www.randstad.ch' target='_blank'>randstad.ch</a>",
                        "<b>Kelly Services :</b> spécialisé IT et industrie — <a href='https://www.kellyservices.ch' target='_blank'>kellyservices.ch</a>",
                        "<b>Temporis :</b> réseau de franchises locales — <a href='https://www.temporis.ch' target='_blank'>temporis.ch</a>",
                    ), width='half'),
                    sec("Conseils", ul(
                        "Inscrivez-vous dans plusieurs agences en même temps",
                        "Apportez : CV, permis de séjour, certificats de travail",
                        "Précisez votre disponibilité, vos langues et votre secteur",
                        "Les agences sont gratuites pour les candidats — méfiez-vous si on vous demande de l'argent",
                    ), width='half'),
                ),
            },

            {
                'name': "Je ne sais pas si je suis payé correctement",
                'description': "Je veux comprendre ma fiche de salaire et savoir si mon salaire respecte les règles de mon secteur.",
                'tags': ['Salaire', 'Droit du travail', 'Travail', 'Droits'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Résident long terme'],
                'body': body(
                    sec("Le salaire en Suisse",
                        ul(
                            "Il n'y a pas de salaire minimum national légal — mais de nombreux secteurs ont des minimums fixés par des <b>conventions collectives de travail (CCT)</b>",
                            "Le salaire est souvent mensuel, versé fin de mois ou le 25",
                            "Votre fiche de salaire doit détailler : salaire brut, cotisations AVS/AI/AC, impôt à la source, salaire net",
                            "<b>13e salaire :</b> fréquent en Suisse — versé en décembre ou moitié juillet / moitié décembre",
                        ),
                    ),
                    sec("Trouver la CCT de votre secteur",
                        ul(
                            "<b>Hôtellerie-restauration (GAV) :</b> <a href='https://www.l-gav.ch' target='_blank'>l-gav.ch</a> — salaire min. env. CHF 3 600/mois",
                            "<b>Nettoyage :</b> CCT nettoyage — env. CHF 3 700/mois",
                            "<b>Construction :</b> CCT construction — renseignez-vous à Unia",
                            "<b>Toutes les CCT :</b> <a href='https://www.seco.admin.ch/cct' target='_blank'>seco.admin.ch/cct</a>",
                        ),
                    ),
                    sec("Si vous pensez être sous-payé", ul(
                        "<b>Unia Neuchâtel :</b> syndicat — consultation gratuite — <a href='https://www.unia.ch' target='_blank'>unia.ch</a>",
                        "<b>Syna :</b> autre syndicat — <a href='https://www.syna.ch' target='_blank'>syna.ch</a>",
                        "<b>Inspection du travail NE :</b> peut contrôler le respect des CCT — <a href='https://www.ne.ch/inspection-travail' target='_blank'>ne.ch/inspection-travail</a>",
                        "Signalez de manière anonyme si vous avez peur des représailles",
                    ), width='full'),
                ),
            },

            {
                'name': "Je ne sais pas quel métier choisir en Suisse",
                'description': "Un conseiller peut m'aider gratuitement à trouver ma direction professionnelle et à relancer ma carrière.",
                'tags': ['Travail', 'Formation', 'Recherche emploi', 'En personne', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Jeune adulte'],
                'body': body(
                    sec("Le Centre d'orientation (OCOSP)",
                        para("L'Office cantonal de l'orientation scolaire et professionnelle (OCOSP) propose des conseils gratuits pour les adultes qui veulent se réorienter ou progresser dans leur carrière."),
                        ul(
                            "Tests d'aptitudes et de personnalité",
                            "Entretiens individuels avec un conseiller",
                            "Information sur les formations et les métiers",
                            "<b>Neuchâtel :</b> Rue de la Maladière 28 — 032 889 65 50",
                            "<b>La Chaux-de-Fonds :</b> Rue du Commerce 7 — 032 889 64 46",
                        ),
                    ),
                    sec("Autres ressources", ul(
                        "<b>Berufsberatung.ch :</b> base de données de tous les métiers suisses, salaires, formations — <a href='https://www.berufsberatung.ch/fr' target='_blank'>berufsberatung.ch</a>",
                        "<b>CNIP :</b> bilan de compétences pour adultes avec expérience à l'étranger — 032 889 69 25",
                        "<b>ONE (ORP) :</b> votre conseiller ONE peut vous orienter si vous êtes inscrit au chômage",
                    ), width='half'),
                    sec("Tester un métier avant de se lancer", ul(
                        "Demandez à votre ONE un stage d'observation (<i>Schnupperlehre</i>) en entreprise",
                        "Durée : 1 à 5 jours — gratuit — permet de découvrir un métier concrètement",
                        "Le CNIP peut aussi organiser des périodes en entreprise dans le cadre d'une réorientation",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux utiliser LinkedIn pour trouver du travail",
                'description': "En Suisse, beaucoup d'offres ne sont pas publiées. Un bon profil LinkedIn et un réseau solide augmentent vraiment mes chances.",
                'tags': ['Recherche emploi', 'CV candidature', 'Travail', 'En ligne'],
                'audiences': ["Établis depuis plus d'un an", 'Jeune adulte', 'Compétences numériques de base'],
                'body': body(
                    sec("Pourquoi LinkedIn est important en Suisse",
                        para("En Suisse, beaucoup de postes ne sont jamais publiés sur des sites d'emploi — ils sont pourvus par le réseau. LinkedIn est le réseau professionnel le plus utilisé. Un profil complet augmente vraiment vos chances."),
                    ),
                    sec("Créer votre profil",
                        ul(
                            "<b>Photo :</b> professionnelle, fond neutre — obligatoire (profils sans photo sont moins consultés)",
                            "<b>Titre :</b> votre métier ou ce que vous cherchez (ex: 'Infirmière | Cherche poste canton NE')",
                            "<b>Résumé :</b> 3–5 lignes sur votre parcours et ce que vous apportez",
                            "<b>Expériences :</b> même à l'étranger — décrivez vos tâches en français",
                            "<b>Compétences :</b> ajoutez-en au moins 10 — vos connexions peuvent les valider",
                        ),
                    ),
                    sec("Utiliser votre réseau", ul(
                        "Connectez-vous avec vos anciens collègues, voisins, membres d'associations",
                        "Rejoignez des groupes LinkedIn de votre secteur en Suisse romande",
                        "<b>COSM :</b> peut vous mettre en contact avec des personnes de votre communauté travaillant localement",
                        "Demandez des recommandations à vos anciens employeurs ou bénévoles",
                    ), width='half'),
                    sec("Plateformes d'emploi complémentaires", ul(
                        "<a href='https://www.jobs.ch' target='_blank'>jobs.ch</a> — le plus utilisé en Suisse",
                        "<a href='https://www.indeed.ch' target='_blank'>indeed.ch</a>",
                        "<a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a> — portail officiel du SECO",
                        "<a href='https://www.jobup.ch' target='_blank'>jobup.ch</a> — spécialiste Suisse romande",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche un travail saisonnier ou en agriculture",
                'description': "Des emplois saisonniers existent toute l'année en Suisse dans les vendanges, l'hôtellerie ou le tourisme. Voici comment trouver ces postes.",
                'tags': ['Recherche emploi', 'Travail', 'CV candidature', 'En ligne', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Jeune adulte'],
                'body': body(
                    sec("Pourquoi le travail saisonnier",
                        para("Le travail saisonnier est une bonne façon de commencer en Suisse. Il ne demande pas toujours de diplôme, et vous permet de construire une expérience locale et un réseau."),
                    ),
                    sec("Principales saisons et secteurs", ul(
                        "<b>Vendanges (septembre–octobre) :</b> Neuchâtel, Valais, Vaud — pas toujours besoin d'expérience",
                        "<b>Hôtellerie et restauration :</b> toute l'année, surtout été et hiver (stations de ski)",
                        "<b>Agriculture (été) :</b> récolte de fruits et légumes, travaux maraîchers",
                        "<b>Bâtiment :</b> printemps–automne, souvent via agences d'intérim",
                    )),
                    sec("Comment chercher", ul(
                        "<b>Agrijob :</b> plateforme dédiée à l'agriculture — <a href='https://www.agrijob.ch' target='_blank'>agrijob.ch</a>",
                        "<b>Gastrojob :</b> hôtellerie et restauration — <a href='https://www.gastrojob.ch' target='_blank'>gastrojob.ch</a>",
                        "<b>Saisonnier.ch :</b> offres saisonnières toutes régions — <a href='https://www.saisonnier.ch' target='_blank'>saisonnier.ch</a>",
                        "<b>ONE Neuchâtel :</b> votre conseiller peut vous signaler des offres locales — 032 889 68 18",
                        "<b>Agences d'intérim :</b> Adecco, Manpower — souvent des missions courtes dans l'industrie",
                    ), width='half'),
                    sec("Conditions importantes", ul(
                        "Vérifiez que votre permis autorise le travail (permis N : possible après 3 mois sous conditions)",
                        "Le contrat de travail doit être signé avant de commencer — même pour une semaine",
                        "Droit au salaire minimum de la CCT du secteur (restauration : env. CHF 3 600/mois)",
                        "Vous avez les mêmes droits qu'un autre travailleur : assurances, jours de repos, etc.",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux faire du bénévolat pour avoir une première expérience",
                'description': "Le bénévolat me permet de pratiquer le français, de rencontrer des gens et d'ajouter une référence locale à mon CV.",
                'tags': ['Recherche emploi', 'Travail', 'Vie sociale', 'Gratuit', 'CV candidature'],
                'audiences': ['Nouveaux arrivants', 'Jeune adulte', "Demandeur d'asile"],
                'body': body(
                    sec("Pourquoi c'est utile",
                        para("Même sans permis de travail complet, vous pouvez faire du bénévolat. C'est un excellent moyen de construire un réseau, de pratiquer le français et de montrer votre motivation à un futur employeur."),
                    ),
                    sec("Trouver une mission bénévole", ul(
                        "<b>Benevol Neuchâtel :</b> plateforme officielle — <a href='https://www.benevolat-ne.ch' target='_blank'>benevolat-ne.ch</a>",
                        "<b>Croix-Rouge NE :</b> bénévoles toujours recherchés — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Caritas NE :</b> ateliers de français, aide alimentaire — 032 886 80 70",
                        "<b>Maisons de quartier Neuchâtel :</b> activités variées — demandez au COSM",
                    ), width='half'),
                    sec("Ce que vous pouvez mettre sur votre CV", ul(
                        "Le nom de l'organisation",
                        "La durée et la fréquence (ex: 4 heures/semaine depuis 6 mois)",
                        "Vos tâches concrètes et les compétences utilisées",
                        "Un contact de référence dans l'organisation (demandez l'autorisation)",
                    ), width='half'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Health',
        'description': "Assurance maladie, trouver un médecin, santé mentale et urgences.",
        'icon': 'HeartIcon',
        'priority': 9,
        'audiences': [],
        'resources': [

            {
                'name': "Je dois m'assurer contre la maladie",
                'description': "En Suisse, tout le monde doit avoir une assurance maladie. Je dois m'inscrire dans les 3 mois après mon arrivée.",
                'tags': ['Assurance maladie', 'Budget', 'En ligne', 'Multilingue', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Ce que vous devez savoir",
                        para("En Suisse, l'assurance maladie de base s'appelle LAMal. Elle est obligatoire pour tout le monde."),
                        ul(
                            "Vous avez <b>3 mois</b> dès votre arrivée pour vous inscrire",
                            "Si vous vous inscrivez dans ce délai, la couverture commence le jour de votre arrivée",
                            "Si vous dépassez ce délai, vous payez une pénalité",
                            "Toutes les caisses doivent vous accepter — elles ne peuvent pas refuser",
                            "La couverture de base est identique dans toutes les caisses",
                        ),
                    ),
                    sec("Comment choisir et s'inscrire",
                        ol(
                            "Comparez les primes sur <a href='https://www.comparis.ch' target='_blank'>comparis.ch</a> (entrez le canton NE et votre âge)",
                            "Choisissez votre franchise : CHF 300 (prime plus élevée) à CHF 2 500 (prime moins élevée)",
                            "Contactez directement la caisse choisie ou inscrivez-vous en ligne",
                            "Demandez ensuite une réduction de prime si vos revenus sont modestes",
                        ),
                    ),
                    sec("Grandes caisses présentes à Neuchâtel",
                        ul(
                            "<a href='https://www.css.ch' target='_blank'>CSS</a>",
                            "<a href='https://www.concordia.ch' target='_blank'>Concordia</a>",
                            "<a href='https://www.swica.ch' target='_blank'>Swica</a>",
                            "<a href='https://www.groupe-mutuel.ch' target='_blank'>Groupe Mutuel</a>",
                            "<a href='https://www.assura.ch' target='_blank'>Assura</a> (souvent la moins chère)",
                            "Comparer : <a href='https://www.comparis.ch' target='_blank'>comparis.ch</a>",
                        ),
                        width='half',
                    ),
                    sec("Prime moyenne à Neuchâtel (2025)",
                        ul(
                            "<b>Adulte :</b> environ CHF 370–430/mois selon la caisse et la franchise",
                            "<b>Enfant :</b> environ CHF 90–130/mois",
                            "Une réduction de prime est possible si vos revenus sont modestes (voir ressource dédiée)",
                            "<b>Info officielle :</b> <a href='https://www.ne.ch/assurance-maladie' target='_blank'>ne.ch/assurance-maladie</a>",
                        ),
                        width='half',
                    ),
                ),
            },

            {
                'name': "Je veux payer moins cher mon assurance maladie",
                'description': "Si je n'ai pas beaucoup de revenus, l'État peut payer une partie de ma prime d'assurance maladie. Cette aide s'appelle subside.",
                'tags': ['Assurance maladie', 'Reduction de prime', 'Budget', 'Subvention', 'Formulaire', 'Aide sociale'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Résident long terme'],
                'body': body(
                    sec("Ce que c'est",
                        para("Le subside est une aide de l'État cantonal. Il réduit ou supprime votre prime d'assurance maladie si vous n'avez pas beaucoup de revenus."),
                        para("À Neuchâtel, c'est l'OCAB (Office cantonal de l'assurance-maladie et des bourses) qui gère cette aide. Vous faites votre demande via votre GSR (Guichet Social Régional)."),
                    ),
                    sec("Comment faire votre demande",
                        ol(
                            "Allez au GSR de votre commune (pas à l'OCAB directement)",
                            "Apportez vos justificatifs de revenus et de situation familiale",
                            "Le GSR transmet votre dossier à l'OCAB",
                            "L'OCAB calcule le subside et le verse directement à votre caisse maladie",
                        ),
                    ),
                    sec("GSR Neuchâtel-Valangin", ul(
                        "<b>Adresse :</b> Rue Saint-Maurice 4, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 717 74 10",
                        "<b>Email :</b> gsr.neuchatel@ne.ch",
                        "<b>Téléphone :</b> lun–ven 8h30–12h",
                    ), width='half'),
                    sec("GSR La Chaux-de-Fonds", ul(
                        "<b>Adresse :</b> Rue du Collège 11, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 967 67 31",
                        "<b>OCAB (suivi dossier) :</b> Rue de Tivoli 28, 2002 Neuchâtel — 032 889 66 30",
                        "<b>Info :</b> <a href='https://www.ne.ch/subsides-lamal' target='_blank'>ne.ch/subsides-lamal</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche un médecin de famille",
                'description': "Je veux trouver un médecin généraliste qui accepte de nouveaux patients dans le canton de Neuchâtel.",
                'tags': ['Medecin', 'Sante', 'Multilingue', 'Traduction disponible', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Pourquoi c'est important",
                        para("En Suisse, le médecin de famille est votre premier contact pour toute question de santé. Il vous oriente vers des spécialistes si nécessaire."),
                        para("Trouver un médecin peut prendre du temps — commencez dès votre arrivée."),
                    ),
                    sec("Comment chercher",
                        ol(
                            "Cherchez sur <a href='https://doctorfmh.ch/fr/' target='_blank'>doctorfmh.ch</a> — le registre officiel de tous les médecins suisses",
                            "Prenez rendez-vous en ligne sur <a href='https://www.onedoc.ch' target='_blank'>onedoc.ch</a>",
                            "Appelez directement les cabinets proches de chez vous",
                            "Demandez à votre entourage ou au COSM",
                        ),
                    ),
                    sec("Si vous ne trouvez pas de médecin", ul(
                        "<b>HNE — Hôpital Neuchâtelois :</b> consultations sans médecin attitré possible aux urgences",
                        "<b>Urgences HNE Neuchâtel :</b> Rue de la Maladière 45, 2000 Neuchâtel — 032 713 31 31",
                        "<b>Urgences HNE La Chaux-de-Fonds :</b> Rue de Chasseral 20 — 032 967 28 28",
                        "Votre pharmacie peut aussi vous orienter vers un médecin disponible",
                    ), width='half'),
                    sec("Annuaires utiles", ul(
                        "<a href='https://doctorfmh.ch/fr/' target='_blank'>doctorfmh.ch</a> — registre FMH officiel",
                        "<a href='https://www.onedoc.ch' target='_blank'>onedoc.ch</a> — prise de RDV en ligne",
                        "<a href='https://www.comparis.ch/gesundheit/arzt' target='_blank'>comparis.ch</a> — par caisse maladie",
                        "<b>Médecins parlant d'autres langues :</b> demandez au COSM un interprète médical",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai besoin d'aide médicale en urgence",
                'description': "Les numéros d'urgence, les hôpitaux et les permanences de nuit dans le canton de Neuchâtel.",
                'tags': ['Sante', 'Urgence', 'Multilingue', 'Gratuit', 'Hotline'],
                'audiences': [],
                'body': body(
                    sec("Numéros d'urgence",
                        ul(
                            "<b>144</b> — Ambulance. Gratuit, 24h/24",
                            "<b>117</b> — Police. Gratuit, 24h/24",
                            "<b>118</b> — Pompiers. Gratuit, 24h/24",
                            "<b>112</b> — Numéro européen d'urgence",
                            "<b>145</b> — Toxicocentre (empoisonnement). Gratuit, 24h/24",
                            "<b>143</b> — La Main Tendue (soutien psychologique). Gratuit, 24h/24",
                        ),
                    ),
                    sec("Hôpitaux à Neuchâtel (HNE)", ul(
                        "<b>Neuchâtel :</b> Rue de la Maladière 45 — 032 713 31 31",
                        "<b>La Chaux-de-Fonds :</b> Rue de Chasseral 20 — 032 967 28 28",
                        "<b>Pourtalès (Neuchâtel) :</b> Rue de la Maladière 45 — urgences 032 713 31 31",
                        "<b>Site HNE :</b> <a href='https://www.h-ne.ch' target='_blank'>h-ne.ch</a>",
                    ), width='half'),
                    sec("Garde médicale de nuit", ul(
                        "<b>Médecin de garde :</b> appelez le 032 713 31 31 (HNE) pour savoir qui est de garde",
                        "<b>Pharmacies de garde :</b> <a href='https://www.pharmaguard.ch' target='_blank'>pharmaguard.ch</a>",
                        "Votre caisse maladie a un numéro de conseil médical gratuit (24h/24) — vérifiez votre carte d'assuré",
                    ), width='half'),
                ),
            },

            {
                'name': "Je me sens mal et j'ai besoin d'aide psychologique",
                'description': "Des professionnels peuvent m'aider, souvent gratuitement et avec un interprète. Je ne suis pas seul.",
                'tags': ['Sante mentale', 'Sante', 'Gratuit', 'Traduction disponible', 'En personne', 'Interprete'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
                'body': body(
                    sec("Vous n'êtes pas seul",
                        para("Arriver dans un nouveau pays est difficile. Stress, tristesse, anxiété — c'est normal. Des professionnels peuvent vous aider, souvent gratuitement et avec un interprète."),
                    ),
                    sec("Où trouver de l'aide à Neuchâtel", ul(
                        "<b>HNE — Psychiatrie :</b> consultations sur rendez-vous via médecin traitant — <a href='https://www.h-ne.ch' target='_blank'>h-ne.ch</a>",
                        "<b>COSM :</b> peut vous orienter vers un soutien psychosocial et fournir un interprète — 032 889 74 42",
                        "<b>CSP Neuchâtel :</b> accompagnement social pour réfugiés — 032 886 91 00",
                        "<b>Caritas Neuchâtel :</b> soutien et groupes de parole — <a href='https://caritas-regio.ch/neuchatel' target='_blank'>caritas-regio.ch</a>",
                    ), width='half'),
                    sec("Lignes d'écoute", ul(
                        "<b>La Main Tendue :</b> 143 — écoute anonyme, gratuit, 24h/24, en français",
                        "<b>Pro Juventute (jeunes) :</b> 147 — gratuit, 24h/24",
                        "<b>Centre LAVI NE :</b> 032 889 51 00 — victimes de violence",
                        "<b>Dargebotene Hand :</b> 143 — plusieurs langues disponibles",
                    ), width='half'),
                ),
            },

            {
                'name': "Je suis enceinte, que dois-je faire ?",
                'description': "Je veux savoir comment se passe le suivi de grossesse, l'accouchement et le congé maternité en Suisse.",
                'tags': ['Maternite', 'Sante', 'Assurance maladie', 'Femmes', 'Droits parentaux'],
                'audiences': ['Parents', 'Femmes', 'Nouveaux arrivants'],
                'body': body(
                    sec("Prise en charge par la LAMal",
                        ul(
                            "Le suivi de grossesse (gynécologue, sage-femme) est remboursé par la LAMal sans franchise",
                            "L'accouchement à l'hôpital ou à domicile est remboursé",
                            "Les consultations de sage-femme après l'accouchement sont couvertes",
                            "Les vaccins obligatoires du nourrisson sont remboursés",
                        ),
                    ),
                    sec("Congé maternité",
                        ul(
                            "<b>Durée :</b> 14 semaines (98 jours) après l'accouchement",
                            "<b>Montant :</b> 80 % du salaire, maximum CHF 220/jour",
                            "<b>Condition :</b> avoir travaillé au moins 5 mois avant l'accouchement",
                            "<b>Démarches :</b> votre employeur s'en charge via les APG",
                        ),
                    ),
                    sec("À Neuchâtel", ul(
                        "<b>Maternité HNE :</b> Rue de la Maladière 45, 2000 Neuchâtel — 032 713 31 31",
                        "<b>Sages-femmes indépendantes :</b> <a href='https://www.sage-femme.ch' target='_blank'>sage-femme.ch</a>",
                        "<b>PMI / Consultation de nourrissons :</b> renseignez-vous à votre commune",
                        "<b>RECIF (soutien femmes) :</b> Rue de la Cassarde 22, Neuchâtel — <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                    ), width='half'),
                    sec("Infos pratiques", ul(
                        "<b>Congé paternité :</b> 2 semaines (depuis 2021), à prendre dans les 6 mois",
                        "<b>Allocation naissance :</b> certaines communes accordent une prime — renseignez-vous",
                        "<b>Guide officiel :</b> <a href='https://www.ch.ch/maternite' target='_blank'>ch.ch/maternite</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai besoin de soins dentaires",
                'description': "Les soins dentaires ne sont presque pas remboursés par l'assurance maladie. Voici comment trouver un dentiste abordable à Neuchâtel.",
                'tags': ['Sante', 'Budget', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Ce que la LAMal ne couvre pas",
                        para("En Suisse, les soins dentaires ne sont presque pas remboursés par l'assurance maladie de base. Vous devez payer vous-même, sauf cas exceptionnels (accident, maladie grave)."),
                        ul(
                            "<b>Exception :</b> les soins liés à un accident ou à une maladie grave sont pris en charge",
                            "<b>Enfants :</b> certaines communes proposent une aide — renseignez-vous à votre commune",
                            "Vous pouvez souscrire une assurance complémentaire dentaire (env. CHF 20–50/mois)",
                        ),
                    ),
                    sec("Trouver un dentiste à Neuchâtel",
                        ul(
                            "Cherchez sur <a href='https://www.sso.ch/fr/trouvez-un-dentiste' target='_blank'>sso.ch</a> — annuaire officiel de la Société suisse d'odontologie",
                            "Demandez à votre entourage ou au COSM",
                            "<b>HNE :</b> urgences dentaires en dehors des heures de bureau — 032 713 31 31",
                        ),
                    ),
                    sec("Si vous n'avez pas les moyens", ul(
                        "<b>ASLOCA / CSP :</b> peuvent orienter vers des dentistes pratiquant des tarifs sociaux",
                        "<b>Cliniques dentaires des Hautes Écoles :</b> tarifs réduits (HE-Arc Santé à NE)",
                        "<b>GSR :</b> peut parfois aider à financer des soins urgents dans le cadre de l'aide sociale",
                        "<b>Caritas NE :</b> 032 886 80 70 — renseignez-vous sur les aides disponibles",
                    ), width='full'),
                ),
            },

            {
                'name': "Je suis malade mais mon médecin n'est pas disponible",
                'description': "Si je ne peux pas attendre un rendez-vous, une permanence médicale ou un médecin par téléphone peut m'aider rapidement.",
                'tags': ['Medecin', 'Sante', 'Hotline', 'En ligne', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Options rapides sans rendez-vous",
                        ul(
                            "<b>Urgences HNE Neuchâtel :</b> Rue de la Maladière 45 — 032 713 31 31 — pour les cas urgents uniquement",
                            "<b>Permanence médicale :</b> demandez à votre caisse maladie s'il existe une permanence agréée proche de chez vous",
                            "<b>Pharmacie :</b> le pharmacien peut traiter de nombreux problèmes courants (rhume, douleurs légères, pansements) sans RDV",
                        ),
                    ),
                    sec("Consultation téléphonique ou vidéo", ul(
                        "<b>Medi24 :</b> service médical 24h/24 inclus dans certaines caisses maladie — vérifiez votre carte d'assuré",
                        "<b>Medgate :</b> même principe — inclus dans certains modèles d'assurance (Telmed, HMO)",
                        "Ces services peuvent vous prescrire des ordonnances et décider si une visite est nécessaire",
                        "Appelez votre caisse maladie pour savoir quel service vous avez inclus",
                    ), width='half'),
                    sec("Quand aller aux urgences", ul(
                        "<b>Appelez le 144</b> si c'est une urgence vitale (douleur thoracique, accident, perte de connaissance)",
                        "Les urgences hospitalières ne sont pas faites pour les rhumes ou fièvres légères — préférez la permanence ou le télémédecin",
                        "<b>145</b> — Toxicocentre en cas d'ingestion d'un produit dangereux",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux me faire vacciner",
                'description': "Je veux connaître les vaccins recommandés en Suisse et savoir où me faire vacciner à Neuchâtel.",
                'tags': ['Vaccination', 'Sante', 'Enfants', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', 'Parents'],
                'body': body(
                    sec("Vaccins recommandés en Suisse",
                        para("La Suisse a un calendrier vaccinal officiel. Certains vaccins sont recommandés pour tout le monde, d'autres seulement pour les enfants ou les groupes à risque."),
                        ul(
                            "<b>Rougeole, oreillons, rubéole (ROR) :</b> très important — obligatoire pour entrer dans certaines structures",
                            "<b>Tétanos, diphtérie, coqueluche :</b> rappel tous les 10 ans",
                            "<b>Hépatite B :</b> recommandé pour les adolescents et certains adultes",
                            "<b>Grippe :</b> recommandée chaque automne pour les personnes à risque",
                            "<b>COVID-19 :</b> vaccinations disponibles — renseignez-vous sur les recommandations actuelles",
                        ),
                    ),
                    sec("Où se faire vacciner à Neuchâtel", ul(
                        "<b>Votre médecin de famille :</b> la première option",
                        "<b>Pharmacies :</b> certaines vaccinent directement — appelez pour vérifier",
                        "<b>HNE :</b> 032 713 31 31 — consultations vaccinales",
                        "<b>Calendrier officiel :</b> <a href='https://www.ofsp.admin.ch/vaccination' target='_blank'>ofsp.admin.ch/vaccination</a>",
                    ), width='half'),
                    sec("Remboursement", ul(
                        "Les vaccins du calendrier officiel sont remboursés par la LAMal (sans franchise pour les enfants)",
                        "Apportez votre carnet de vaccination à chaque rendez-vous",
                        "Si vous n'avez pas de carnet : votre médecin peut en créer un nouveau",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche des informations sur la contraception ou les IST",
                'description': "Des services gratuits ou à tarif réduit existent à Neuchâtel pour la contraception et les dépistages.",
                'tags': ['Sante', 'Femmes', 'Maternite', 'Gratuit', 'En personne'],
                'audiences': ['Femmes', 'Jeune adulte', 'Nouveaux arrivants'],
                'body': body(
                    sec("Services disponibles à Neuchâtel",
                        ul(
                            "<b>Centre de planning familial NE :</b> consultations gratuites ou à tarif réduit — contraception, grossesse, IST",
                            "<b>Adresse :</b> Rue des Parcs 11, 2000 Neuchâtel — 032 722 95 20",
                            "<b>HNE Gynécologie :</b> consultation sur rendez-vous — 032 713 31 31",
                            "<b>Sages-femmes indépendantes :</b> suivi grossesse, contraception — <a href='https://www.sage-femme.ch' target='_blank'>sage-femme.ch</a>",
                        ),
                    ),
                    sec("Contraception", ul(
                        "La contraception est remboursée par la LAMal jusqu'à 18 ans",
                        "Après 18 ans : à votre charge (pilule env. CHF 15–30/mois)",
                        "Préservatifs disponibles dans toutes les pharmacies",
                        "<b>Contraception d'urgence :</b> disponible en pharmacie sans ordonnance",
                    ), width='half'),
                    sec("Dépistage IST", ul(
                        "<b>Checkpoint NE :</b> dépistage VIH et IST — <a href='https://www.checkpoint-ne.ch' target='_blank'>checkpoint-ne.ch</a>",
                        "Dépistage souvent gratuit ou à prix réduit",
                        "<b>Aide Suisse contre le Sida :</b> <a href='https://www.aids.ch' target='_blank'>aids.ch</a>",
                        "Résultats confidentiels",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai un handicap ou une maladie grave, quelles aides existent ?",
                'description': "L'assurance invalidité (AI) peut m'aider si je ne peux plus travailler à cause d'un problème de santé.",
                'tags': ['Handicap', 'Aide sociale', 'Allocation', 'Formulaire', 'Budget'],
                'audiences': ['Senior', 'Nouveaux arrivants'],
                'body': body(
                    sec("Qu'est-ce que l'AI",
                        para("L'Assurance Invalidité (AI) est le 1er pilier social pour les personnes qui ont un handicap ou une maladie grave qui limite leur capacité de travail."),
                        ul(
                            "Rente AI si vous ne pouvez plus travailler (complète ou partielle)",
                            "Mesures de réintégration professionnelle (reconversion, formation)",
                            "Aide technique (fauteuil roulant, appareils auditifs, etc.)",
                        ),
                    ),
                    sec("Conditions",
                        ul(
                            "Avoir cotisé à l'AVS pendant au moins 3 ans",
                            "Avoir une incapacité de gain d'au moins 40 %",
                            "Les personnes arrivées avec un handicap préexistant ont des droits limités",
                        ),
                    ),
                    sec("Contacts à Neuchâtel", ul(
                        "<b>Office AI NE :</b> Rue Chandigarh 2, 2000 Neuchâtel — 032 889 65 00 — <a href='https://www.iv-ne.ch' target='_blank'>iv-ne.ch</a>",
                        "<b>Pro Infirmis NE :</b> conseil et accompagnement pour les personnes en situation de handicap — <a href='https://www.proinfirmis.ch' target='_blank'>proinfirmis.ch</a>",
                        "<b>Inclusion Handicap :</b> défense des droits — <a href='https://www.inclusion-handicap.ch' target='_blank'>inclusion-handicap.ch</a>",
                    ), width='full'),
                ),
            },

            {
                'name': "J'ai des problèmes avec l'alcool, les drogues ou le jeu",
                'description': "Des professionnels discrets peuvent m'aider, gratuitement et en toute confidentialité.",
                'tags': ['Sante mentale', 'Sante', 'Urgence', 'Gratuit', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Vous n'êtes pas seul",
                        para("Les addictions peuvent toucher tout le monde. Des professionnels discrets et non-jugeants peuvent vous aider, gratuitement et en toute confidentialité."),
                    ),
                    sec("Addiction Neuchâtel", ul(
                        "<b>Adresse Neuchâtel :</b> Rue de la Chapelle 4, 2000 Neuchâtel — 032 725 64 00",
                        "<b>Adresse La Chaux-de-Fonds :</b> Rue du Commerce 10 — 032 913 49 00",
                        "<b>Email :</b> addiction-ne@ne.ch",
                        "<b>Site :</b> <a href='https://www.addiction-ne.ch' target='_blank'>addiction-ne.ch</a>",
                        "Consultation gratuite, sans rendez-vous pour les urgences",
                        "Aide pour alcool, drogues, jeux, écrans",
                    ), width='half'),
                    sec("Lignes d'urgence et autres aides", ul(
                        "<b>Ligne nationale alcool :</b> 0800 040 080 — gratuit, 24h/24",
                        "<b>Narcotics Anonymous :</b> groupes de parole à Neuchâtel — <a href='https://www.na-switzerland.org' target='_blank'>na-switzerland.org</a>",
                        "<b>Alcooliques Anonymes :</b> <a href='https://www.alcooliquesanonymes.ch' target='_blank'>alcooliquesanonymes.ch</a>",
                        "<b>La Main Tendue :</b> 143 — écoute 24h/24",
                    ), width='half'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Money & budget',
        'description': 'Aides financières, aide sociale, banque et gestion du budget.',
        'icon': 'CurrencyDollarIcon',
        'priority': 9,
        'audiences': [],
        'resources': [

            {
                'name': "Je n'ai pas assez d'argent pour vivre",
                'description': "L'aide sociale peut me soutenir si mes revenus ne couvrent pas mes besoins de base. À Neuchâtel, c'est le GSR qui s'en occupe.",
                'tags': ['Aide sociale', 'Budget', 'Allocation', 'Formulaire', 'En personne', 'Traduction disponible'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Qu'est-ce que c'est",
                        para("L'aide sociale est un soutien financier de l'État. Elle couvre les besoins de base : nourriture, logement, santé."),
                        para("À Neuchâtel, c'est le GSR (Guichet Social Régional) de votre commune qui traite les demandes. Ce même guichet gère aussi les subsides LAMal et les bourses d'études — un seul endroit pour plusieurs aides."),
                    ),
                    sec("Qui peut en bénéficier",
                        ul(
                            "Vous habitez légalement dans le canton de Neuchâtel",
                            "Vos revenus ne couvrent pas vos besoins essentiels",
                            "Vous avez épuisé vos autres droits (chômage, rente, etc.)",
                            "Les demandeurs d'asile ont un système géré par le SMIG",
                        ),
                    ),
                    sec("GSR Neuchâtel-Valangin", ul(
                        "<b>Adresse :</b> Rue Saint-Maurice 4, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 717 74 10",
                        "<b>Email :</b> gsr.neuchatel@ne.ch",
                        "<b>Permanence téléphonique :</b> lun–ven 8h30–12h",
                        "<b>Documents :</b> pièce d'identité, permis de séjour, relevés bancaires, contrat de bail, justificatifs de revenus",
                    ), width='half'),
                    sec("GSR La Chaux-de-Fonds", ul(
                        "<b>Adresse :</b> Rue du Collège 11, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 967 67 31",
                        "<b>Heures :</b> 9h–12h / 14h–17h",
                        "<b>Autres GSR :</b> <a href='https://www.ne.ch/gsr' target='_blank'>ne.ch/gsr</a> (liste complète par commune)",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux ouvrir un compte bancaire",
                'description': "Je veux savoir quelle banque choisir, quels documents apporter et quelles options existent selon mon permis de séjour.",
                'tags': ['Banque', 'Budget', 'Documents officiels', 'En personne', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Pourquoi c'est important",
                        para("Un compte bancaire est indispensable en Suisse. Votre salaire y sera versé, et vous en avez besoin pour payer votre loyer et vos factures."),
                    ),
                    sec("Documents généralement demandés",
                        ul(
                            "Passeport ou carte d'identité",
                            "Permis de séjour",
                            "Justificatif de domicile (contrat de bail ou confirmation communale)",
                            "Parfois : attestation de revenus ou d'emploi",
                        ),
                    ),
                    sec("Options selon votre situation",
                        ul(
                            "<b>Permis B ou C :</b> toutes les banques acceptent — comparez sur <a href='https://www.comparis.ch' target='_blank'>comparis.ch</a>",
                            "<b>Permis N ou F :</b> les grandes banques refusent souvent — utilisez une néobanque",
                            "<b>Néobanques :</b> <a href='https://www.neon-free.ch' target='_blank'>Neon</a>, <a href='https://www.yuh.com' target='_blank'>Yuh</a>, <a href='https://www.revolut.com' target='_blank'>Revolut</a> — inscription 100% en ligne",
                            "<b>Banque Cantonale Neuchâteloise (BCN) :</b> présente dans tout le canton — <a href='https://www.bcn.ch' target='_blank'>bcn.ch</a>",
                            "<b>PostFinance :</b> accepte souvent des situations variées",
                        ),
                    ),
                ),
            },

            {
                'name': "J'ai perdu mon emploi et je veux toucher le chômage",
                'description': "Si j'ai travaillé et cotisé en Suisse, je peux recevoir de l'argent chaque mois pendant que je cherche un emploi.",
                'tags': ['Chomage', 'Allocation', 'Budget', 'Travail', 'Formulaire', 'Droits'],
                'audiences': ["Établis depuis plus d'un an", 'Résident long terme', 'Frontalier'],
                'body': body(
                    sec("Conditions pour en bénéficier",
                        ul(
                            "Avoir travaillé et cotisé au moins 12 mois en Suisse durant les 2 dernières années",
                            "Être disponible immédiatement pour travailler",
                            "Chercher activement un emploi",
                            "Avoir un permis de séjour valide (B, C — permis G pour frontaliers sous conditions)",
                        ),
                    ),
                    sec("Combien recevez-vous",
                        ul(
                            "80 % de votre salaire mensuel brut (70 % dans certains cas)",
                            "Durée : 260 à 520 jours selon votre nombre de cotisations",
                        ),
                    ),
                    sec("Comment faire",
                        ol(
                            "S'inscrire au ONE (ORP) dès le premier jour sans emploi",
                            "Choisir et s'inscrire à une caisse de chômage dans les 30 jours",
                            "Envoyer chaque mois un relevé de vos recherches d'emploi",
                        ),
                    ),
                    sec("CCNAC — Caisse neuchâteloise", ul(
                        "<b>Adresse :</b> Espacité 4, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 889 67 90",
                        "<b>Email :</b> ccnac@ne.ch",
                        "<b>Site :</b> <a href='https://ccnac.ch' target='_blank'>ccnac.ch</a>",
                        "<b>Heures :</b> lun–ven 8h30–11h / 13h30–16h",
                    ), width='half'),
                    sec("Plus d'informations", ul(
                        "<b>Guide officiel :</b> <a href='https://www.ch.ch/fr/assurances/assurance-chomage/' target='_blank'>ch.ch/chomage</a>",
                        "Vous pouvez aussi utiliser une caisse syndicale : Unia, Syna — présentes à Neuchâtel",
                    ), width='half'),
                ),
            },

            {
                'name': "Je ne comprends pas comment fonctionnent les impôts",
                'description': "Je veux savoir si mes impôts sont prélevés automatiquement sur mon salaire ou si je dois faire une déclaration.",
                'tags': ['Impots', 'Documents officiels', 'Budget', 'Travail', 'Formulaire'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an", 'Frontalier'],
                'body': body(
                    sec("Imposition à la source",
                        para("Si vous avez un permis B (non-UE) ou N/F, votre employeur retient directement les impôts sur votre salaire. C'est l'imposition à la source."),
                        ul(
                            "Vous ne recevez pas de déclaration fiscale automatiquement",
                            "Votre employeur retient le montant et le verse au fisc",
                            "Vous pouvez demander une rectification si vous avez des déductions à faire valoir",
                        ),
                    ),
                    sec("Déclaration fiscale ordinaire",
                        ul(
                            "Obligatoire si vous avez un permis C ou si vous êtes marié avec un Suisse",
                            "Obligatoire si vous gagnez plus de CHF 120 000/an (même avec permis B)",
                            "Délai habituel : fin mars de l'année suivante (prolongation possible sur demande)",
                        ),
                    ),
                    sec("Service des contributions NE", ul(
                        "<b>Adresse :</b> Rue du Temple-Neuf 2, 2010 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 62 00",
                        "<b>Site :</b> <a href='https://www.ne.ch/impots' target='_blank'>ne.ch/impots</a>",
                        "<b>Déclaration en ligne :</b> <a href='https://www.ne.ch/neotax' target='_blank'>neotax (ne.ch)</a>",
                    ), width='half'),
                    sec("Frontaliers", ul(
                        "Les frontaliers (permis G) sont imposés dans leur pays de résidence en général",
                        "Des conventions fiscales s'appliquent selon le pays",
                        "<b>Info frontaliers :</b> <a href='https://www.ch.ch/fr/impots/frontaliers/' target='_blank'>ch.ch/impots-frontaliers</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux comprendre la retraite en Suisse",
                'description': "Je veux savoir comment fonctionne le système de retraite suisse et ce que je cotise chaque mois.",
                'tags': ['Budget', 'Allocation', 'Droits', 'Formulaire', 'Travail'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an", 'Senior'],
                'body': body(
                    sec("Les 3 piliers",
                        ul(
                            "<b>1er pilier (AVS/AI) :</b> obligatoire pour tous — cotisation automatique sur le salaire (5,3 %). Donne droit à une rente vieillesse.",
                            "<b>2e pilier (LPP / caisse de pension) :</b> obligatoire si vous gagnez plus de CHF 22 050/an. Votre employeur cotise autant que vous.",
                            "<b>3e pilier :</b> épargne volontaire, défiscalisée. Recommandé si vous restez longtemps en Suisse.",
                        ),
                    ),
                    sec("Votre numéro AVS",
                        ul(
                            "Dès votre premier emploi ou inscription en commune, vous recevez un numéro AVS (13 chiffres)",
                            "Ce numéro est permanent et vous suit toute la vie",
                            "Si vous ne l'avez pas : demandez à votre employeur ou à la CCNC",
                        ),
                    ),
                    sec("À la retraite", ul(
                        "<b>Âge de la retraite :</b> 65 ans (hommes et femmes depuis 2025)",
                        "<b>Rente AVS :</b> entre CHF 1 225 et CHF 2 450/mois selon cotisations",
                        "<b>Si la rente est insuffisante :</b> demandez les prestations complémentaires (PC)",
                        "<b>CCNC Neuchâtel :</b> 032 889 65 01 — pour toutes questions AVS",
                    ), width='half'),
                    sec("Si vous quittez la Suisse", ul(
                        "Vous pouvez récupérer votre 2e pilier si vous quittez définitivement la Suisse",
                        "Hors UE/AELE : remboursement total possible",
                        "UE/AELE : remboursement partiel selon conventions",
                        "<b>Info :</b> <a href='https://www.ch.ch/retraite' target='_blank'>ch.ch/retraite</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai des dettes et je ne sais plus quoi faire",
                'description': "Des professionnels peuvent m'aider gratuitement à gérer mes dettes avant que la situation empire.",
                'tags': ['Budget', 'Aide sociale', 'Aide juridique', 'En personne', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Résident long terme'],
                'body': body(
                    sec("Ne pas attendre",
                        para("Les dettes peuvent vite devenir incontrôlables. Plus vous agissez tôt, plus les solutions sont nombreuses. Une consultation gratuite peut changer la situation."),
                    ),
                    sec("Ce qui se passe si vous ne payez pas",
                        ul(
                            "Rappels, puis poursuites officielles (actes de défaut de biens)",
                            "Votre salaire peut être saisi partiellement",
                            "Les poursuites apparaissent dans l'extrait du registre — cela nuit à votre dossier de location",
                        ),
                    ),
                    sec("Aide à Neuchâtel", ul(
                        "<b>Budget Conseil NE :</b> consultation gratuite en gestion des dettes — 032 721 30 30 — <a href='https://www.budgetconseil.ch' target='_blank'>budgetconseil.ch</a>",
                        "<b>CSP Neuchâtel :</b> accompagnement social et conseil juridique — 032 886 91 00",
                        "<b>Caritas NE :</b> aide d'urgence et conseil budget — 032 886 80 70",
                        "<b>GSR :</b> peut orienter vers les bons services",
                    ), width='half'),
                    sec("Démarches utiles", ul(
                        "Faites une liste de toutes vos dettes (montant, créancier, échéance)",
                        "Contactez vos créanciers pour négocier un plan de paiement",
                        "Ne signez rien sous pression — consultez d'abord un conseiller",
                        "<b>Extrait des poursuites gratuit :</b> Office des poursuites de Neuchâtel — 032 889 67 00",
                    ), width='half'),
                ),
            },

            {
                'name': "Ma rente ne suffit pas pour vivre",
                'description': "Si ma rente AVS ou AI est trop petite, j'ai droit à une aide supplémentaire. Ce n'est pas de l'aide sociale, c'est un droit.",
                'tags': ['Aide sociale', 'Allocation', 'Budget', 'Senior', 'Formulaire', 'Handicap'],
                'audiences': ['Senior', 'Résident long terme'],
                'body': body(
                    sec("Qu'est-ce que les PC",
                        para("Les prestations complémentaires (PC) sont une aide de l'État pour les personnes dont la rente AVS ou AI est trop faible pour vivre. Elles ne sont pas une aide sociale ordinaire — c'est un droit légal."),
                    ),
                    sec("Qui peut en bénéficier",
                        ul(
                            "Bénéficiaires d'une rente AVS (retraités) ou AI (invalides)",
                            "Domiciliés en Suisse depuis au moins 10 ans (exceptions possibles)",
                            "Revenus et fortune en dessous d'un certain seuil",
                        ),
                    ),
                    sec("Comment faire une demande", ul(
                        "<b>CCNC Neuchâtel :</b> Faubourg de l'Hôpital 28, 2001 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 65 01",
                        "<b>Email :</b> ccnc@ne.ch",
                        "<b>Documents :</b> relevé de rente, extrait de compte bancaire, bail, primes d'assurance maladie",
                        "<b>Délai :</b> demandez dès que possible — les PC ne sont pas rétroactives",
                    ), width='half'),
                    sec("Ce qui est couvert", ul(
                        "Complément pour atteindre le minimum vital",
                        "Remboursement des primes LAMal (souvent en totalité)",
                        "Frais de maladie et d'invalidité non remboursés",
                        "<b>Info nationale :</b> <a href='https://www.ch.ch/fr/prestations-complementaires/' target='_blank'>ch.ch/PC</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux mieux gérer mon argent",
                'description': "Je veux organiser mes dépenses et éviter les difficultés financières. Des conseils et outils gratuits existent.",
                'tags': ['Budget', 'Formation', 'Aide sociale', 'Gratuit', 'En ligne'],
                'audiences': ['Nouveaux arrivants', 'Jeune adulte', "Demandeur d'asile"],
                'body': body(
                    sec("Les bases d'un budget suisse",
                        ul(
                            "<b>Loyer :</b> ne devrait pas dépasser 30 % de votre revenu",
                            "<b>Assurance maladie :</b> environ CHF 370–430/mois pour un adulte",
                            "<b>Nourriture :</b> environ CHF 400–600/mois pour une personne",
                            "<b>Transports :</b> demi-tarif CFF recommandé (CHF 185/an) si vous vous déplacez souvent",
                            "<b>Épargne :</b> visez 10 % si possible — pour les imprévus",
                        ),
                    ),
                    sec("Outils gratuits", ul(
                        "<b>Budget Conseil NE :</b> conseil personnalisé gratuit — <a href='https://www.budgetconseil.ch' target='_blank'>budgetconseil.ch</a> — 032 721 30 30",
                        "<b>Calculateur de budget :</b> <a href='https://www.comparis.ch/budget' target='_blank'>comparis.ch/budget</a>",
                        "<b>Guide budget famille :</b> <a href='https://www.ksa.ch' target='_blank'>ksa.ch</a> (Conseils suisses aux familles)",
                    ), width='half'),
                    sec("Pièges courants à éviter", ul(
                        "Achats à tempérament / leasing voiture — intérêts très élevés",
                        "Loteries et jeux d'argent en ligne",
                        "Déménager sans extrait de poursuites propre rend très difficile de trouver un logement",
                        "Chèques postaux non payés — entraînent des frais supplémentaires",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai reçu un acte de poursuite, que faire ?",
                'description': "Recevoir un acte de poursuite ne signifie pas qu'on va m'expulser ou m'arrêter. Je veux comprendre ce que c'est et quoi faire.",
                'tags': ['Budget', 'Aide juridique', 'Documents officiels', 'Droits', 'Formulaire'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", "Établis depuis plus d'un an"],
                'body': body(
                    sec("Qu'est-ce qu'une poursuite",
                        para("Une poursuite est une procédure officielle pour récupérer une dette. Elle ne signifie pas que vous serez arrêté ou expulsé. C'est une procédure civile (financière), pas pénale."),
                        ul(
                            "Vous recevez un <b>commandement de payer</b> par lettre recommandée",
                            "Vous avez <b>10 jours</b> pour faire opposition si vous contestez la dette",
                            "Si vous ne payez pas et ne faites pas opposition, la poursuite continue",
                        ),
                    ),
                    sec("Que faire dès réception",
                        ol(
                            "Lisez attentivement le document — quel créancier, quel montant, quelle date",
                            "Si vous contestez la dette : faites opposition immédiatement (dans les 10 jours) — par écrit à l'Office des poursuites",
                            "Si vous ne contestez pas : négociez un plan de paiement avec le créancier",
                            "Ne jetez jamais ce document — gardez-le",
                        ),
                    ),
                    sec("Office des poursuites NE", ul(
                        "<b>Neuchâtel :</b> Rue du Seyon 4 — 032 889 67 00",
                        "<b>La Chaux-de-Fonds :</b> Espacité 4 — 032 889 67 30",
                        "<b>Extrait des poursuites :</b> gratuit — demandez-le pour vérifier votre situation avant de chercher un logement",
                    ), width='half'),
                    sec("Aide gratuite", ul(
                        "<b>Budget Conseil NE :</b> 032 721 30 30 — <a href='https://www.budgetconseil.ch' target='_blank'>budgetconseil.ch</a>",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00 — aide juridique",
                        "<b>Info nationale :</b> <a href='https://www.ch.ch/fr/dettes-et-poursuites/' target='_blank'>ch.ch/dettes-et-poursuites</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je n'ai pas assez à manger",
                'description': "Des associations proposent de la nourriture gratuite ou à prix très réduit pour les personnes dans le besoin.",
                'tags': ['Gratuit', 'En personne', 'Aide sociale', 'Alimentation', 'Urgence', 'Budget'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
                'body': body(
                    sec("Ce que vous pouvez trouver",
                        para("Des associations proposent de la nourriture à prix très réduit ou gratuite aux personnes dans le besoin."),
                    ),
                    sec("À Neuchâtel", ul(
                        "<b>Caritas Neuchâtel :</b> épicerie sociale sur dossier — Vieux-Châtel 4, 2002 Neuchâtel — 032 886 80 70 — <a href='https://caritas-regio.ch/neuchatel' target='_blank'>caritas-regio.ch/neuchatel</a>",
                        "<b>Armée du Salut Neuchâtel :</b> repas et aide alimentaire — <a href='https://armeedusalut.ch' target='_blank'>armeedusalut.ch</a>",
                        "<b>Croix-Rouge Neuchâtel :</b> colis alimentaires — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Banque alimentaire NE :</b> renseignez-vous via votre GSR ou le COSM",
                    ), width='half'),
                    sec("À La Chaux-de-Fonds", ul(
                        "<b>Caritas La Chaux-de-Fonds :</b> aide alimentaire — renseignez-vous via Caritas NE",
                        "<b>Armée du Salut CDF :</b> repas et aide d'urgence",
                        "<b>Annuaire social :</b> demandez au GSR de La Chaux-de-Fonds (032 967 67 31) la liste des ressources locales",
                    ), width='half'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Education',
        'description': "Cours de langue, reconnaissance de diplômes et formation professionnelle.",
        'icon': 'AcademicCapIcon',
        'priority': 8,
        'audiences': ['Nouveaux arrivants', 'Jeune adulte', "Établis depuis plus d'un an", 'Formation supérieure'],
        'resources': [

            {
                'name': "Je veux apprendre le français",
                'description': "Des cours de français gratuits ou peu chers existent pour les adultes migrants dans le canton de Neuchâtel.",
                'tags': ['Cours de langue', 'Langue', 'Gratuit', 'Integration', 'En personne', 'Formation'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Jeune adulte'],
                'body': body(
                    sec("Pourquoi apprendre le français",
                        para("Parler français facilite tout : trouver du travail, comprendre les courriers officiels, parler avec l'école de vos enfants. Des cours gratuits ou très peu chers existent partout dans le canton."),
                    ),
                    sec("COSM — Cours officiels d'intégration", ul(
                        "<b>Adresse :</b> Place de la Gare 6, 2300 La Chaux-de-Fonds (+ permanences à Neuchâtel et Fleurier)",
                        "<b>Téléphone :</b> 032 889 74 42",
                        "<b>Email :</b> cosm@ne.ch",
                        "<b>Site :</b> <a href='https://www.ne.ch/cosm' target='_blank'>ne.ch/cosm</a>",
                        "Cours de français, alphabétisation, informatique, intégration",
                    ), width='half'),
                    sec("Autres organismes", ul(
                        "<b>Caritas NE :</b> ateliers gratuits (bénévoles), 10 groupes à Neuchâtel, 3 à CDF — caritas.ateliers@ne.ch — 032 886 80 70",
                        "<b>RECIF (femmes uniquement) :</b> cours A1 à B1 — Rue de la Cassarde 22, Neuchâtel — <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>Croix-Rouge NE :</b> cours de conversation — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux faire reconnaître mon diplôme étranger en Suisse",
                'description': "Je veux savoir comment faire valider en Suisse le diplôme que j'ai obtenu dans mon pays d'origine.",
                'tags': ['Reconnaissance diplome', 'Documents officiels', 'Formulaire', 'Travail', 'Formation'],
                'audiences': ['Formation supérieure', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Première étape",
                        para("Allez d'abord sur <a href='https://www.reconnaissance.swiss' target='_blank'>reconnaissance.swiss</a>. Ce site officiel vous dit quel organisme traite votre dossier selon votre profession et votre pays d'origine."),
                    ),
                    sec("Médecins — MEBEKO", ul(
                        "<b>Organisme :</b> MEBEKO (Commission des professions médicales)",
                        "<b>Site :</b> <a href='https://www.bag.admin.ch' target='_blank'>bag.admin.ch</a> (chercher MEBEKO)",
                        "<b>Coût :</b> CHF 800–1 000",
                        "<b>Délai :</b> 3 à 4 mois (dossier complet)",
                        "<b>Langue requise :</b> B2 en français, allemand ou italien",
                    ), width='half'),
                    sec("Infirmiers, physios — Croix-Rouge suisse", ul(
                        "<b>Site :</b> <a href='https://www.redcross.ch/reconnaissance' target='_blank'>redcross.ch/reconnaissance</a>",
                        "<b>Commencez par :</b> <a href='https://precheck.ch' target='_blank'>precheck.ch</a> (gratuit, obligatoire)",
                        "<b>Coût :</b> CHF 550–1 000",
                        "<b>Aide à Neuchâtel :</b> CNIP peut accompagner la démarche",
                    ), width='half'),
                    sec("Enseignants (CDIP) et autres (SEFRI)",
                        ul(
                            "<b>Enseignants :</b> CDIP — <a href='https://www.cdip.ch' target='_blank'>cdip.ch</a>",
                            "<b>Autres professions :</b> SEFRI — <a href='https://www.sefri.admin.ch' target='_blank'>sefri.admin.ch</a>",
                            "<b>Aide à Neuchâtel :</b> CNIP — <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a> — 032 889 69 25",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux obtenir un diplôme professionnel suisse",
                'description': "Je peux obtenir un diplôme professionnel suisse en tant qu'adulte, même sans avoir fait d'apprentissage.",
                'tags': ['Formation', 'Apprentissage', 'Travail', 'En personne'],
                'audiences': ["Établis depuis plus d'un an", 'Jeune adulte'],
                'body': body(
                    sec("Les deux diplômes",
                        ul(
                            "<b>AFP (Attestation fédérale) :</b> 2 ans, pour des métiers pratiques",
                            "<b>CFC (Certificat fédéral de capacité) :</b> 3 à 4 ans, reconnu dans toute la Suisse",
                        ),
                    ),
                    sec("Comment y accéder en tant qu'adulte",
                        ol(
                            "Contactez votre conseiller au ONE ou au COSM",
                            "Faites un bilan de compétences (CNIP peut aider)",
                            "Choisissez entre formation complète, raccourcie, ou validation des acquis",
                        ),
                    ),
                    sec("Contacts à Neuchâtel",
                        ul(
                            "<b>Service de la formation professionnelle NE :</b> <a href='https://www.ne.ch/formation-professionnelle' target='_blank'>ne.ch/formation-professionnelle</a>",
                            "<b>CNIP :</b> 032 889 69 25 — <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a>",
                            "<b>Guide national :</b> <a href='https://www.berufsberatung.ch/fr' target='_blank'>berufsberatung.ch</a>",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux apprendre le français depuis chez moi",
                'description': "Des applications, sites et ressources gratuites me permettent de progresser en français depuis chez moi.",
                'tags': ['Cours de langue', 'Langue', 'E-learning', 'Gratuit', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Jeune adulte'],
                'body': body(
                    sec("Applications gratuites",
                        ul(
                            "<b>Duolingo :</b> application ludique, idéale pour débuter — <a href='https://www.duolingo.com' target='_blank'>duolingo.com</a>",
                            "<b>TV5Monde :</b> cours de français avec vidéos — <a href='https://apprendre.tv5monde.com' target='_blank'>apprendre.tv5monde.com</a>",
                            "<b>Français Authentique :</b> YouTube — compréhension orale",
                            "<b>RFI Savoirs :</b> exercices et actualités en français facile — <a href='https://savoirs.rfi.fr' target='_blank'>savoirs.rfi.fr</a>",
                        ),
                    ),
                    sec("Cours en ligne structurés", ul(
                        "<b>Migros Club School :</b> cours en ligne payants mais abordables — <a href='https://www.klubschule.ch' target='_blank'>klubschule.ch</a>",
                        "<b>Coursera / edX :</b> cours FLE de grandes universités, souvent gratuits à l'écoute",
                        "<b>Alliance Française :</b> cours de qualité, en ligne ou à Neuchâtel — <a href='https://www.alliancefrancaise.ch' target='_blank'>alliancefrancaise.ch</a>",
                    ), width='half'),
                    sec("Conseils pour progresser vite", ul(
                        "Pratiquez 15–20 minutes chaque jour plutôt qu'une longue session par semaine",
                        "Regardez des séries françaises avec sous-titres",
                        "Parlez avec vos voisins, collègues, commerçants — même avec des erreurs",
                        "Combinez cours en présentiel (COSM, RECIF) et pratique en ligne",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux certifier mon niveau de français",
                'description': "Le FIDE est le certificat officiel suisse de langue. Il peut être demandé pour mon permis C ou pour la naturalisation.",
                'tags': ['Cours de langue', 'Langue', 'Naturalisation', 'Permis C', 'Formulaire'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Résident long terme'],
                'body': body(
                    sec("Qu'est-ce que FIDE",
                        para("FIDE (<i>français, italiano, deutsch en Suisse</i>) est le cadre officiel suisse pour évaluer le niveau de langue des personnes migrantes. Une attestation FIDE peut être demandée pour le permis C, la naturalisation, ou certains programmes d'intégration."),
                        ul(
                            "Le test évalue l'oral et l'écrit dans des situations de la vie quotidienne",
                            "Niveaux disponibles : A1, A2, B1, B2",
                            "Pour la naturalisation à Neuchâtel : niveau B1 oral minimum requis",
                        ),
                    ),
                    sec("Comment passer le test", ol(
                        "Inscrivez-vous sur <a href='https://www.fide-info.ch' target='_blank'>fide-info.ch</a>",
                        "Choisissez un centre de test agréé à Neuchâtel",
                        "Payez les frais (env. CHF 100–200 selon les modules)",
                        "Recevez votre attestation — valable pour toutes vos démarches officielles",
                    )),
                    sec("Centres de test à Neuchâtel", ul(
                        "<b>COSM :</b> peut orienter vers les centres agréés — 032 889 74 42",
                        "<b>Liste officielle :</b> <a href='https://www.fide-info.ch/fr/test/centres-de-test' target='_blank'>fide-info.ch/centres</a>",
                        "<b>Préparation gratuite :</b> des cours préparatoires existent — demandez au COSM ou à la RECIF",
                    ), width='half'),
                    sec("Se préparer au test", ul(
                        "<b>Exercices gratuits :</b> <a href='https://www.fide-info.ch/fr/apprendre/exercices' target='_blank'>fide-info.ch/exercices</a>",
                        "Pratiquez les situations du quotidien : prendre RDV, comprendre une facture, parler à l'école",
                        "Les cours COSM et RECIF préparent directement au niveau FIDE",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux savoir si l'État peut payer mes cours de langue",
                'description': "À Neuchâtel, le canton peut financer jusqu'à la moitié du coût de mes cours de langue via le chèque-langue.",
                'tags': ['Cours de langue', 'Langue', 'Subvention', 'Budget', 'Formulaire', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", "Établis depuis plus d'un an"],
                'body': body(
                    sec("Ce que c'est",
                        para("Le canton de Neuchâtel propose un soutien financier pour les cours de français destinés aux migrants. Ce système, appelé chèque-langue ou subvention à la formation linguistique, réduit significativement le coût des cours."),
                    ),
                    sec("Qui peut en bénéficier",
                        ul(
                            "Personnes étrangères résidant dans le canton de Neuchâtel",
                            "Niveau de français insuffisant pour l'intégration ou le marché du travail",
                            "En général : permis N, F, S, B récent — vérifiez selon votre situation",
                        ),
                    ),
                    sec("Comment faire la demande", ol(
                        "Prenez contact avec le COSM : 032 889 74 42 — cosm@ne.ch",
                        "Le COSM évalue votre situation et votre niveau de français",
                        "Si éligible, vous recevez un bon ou une prise en charge directe",
                        "Inscrivez-vous dans un organisme de cours agréé",
                    )),
                    sec("Organismes agréés", ul(
                        "<b>COSM :</b> cours propres — Place de la Gare 6, La Chaux-de-Fonds",
                        "<b>RECIF (femmes) :</b> Rue de la Cassarde 22, Neuchâtel — <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>Caritas NE :</b> ateliers gratuits — caritas.ateliers@ne.ch",
                        "<b>Croix-Rouge NE :</b> cours de conversation — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Info officielle :</b> <a href='https://www.ne.ch/integration' target='_blank'>ne.ch/integration</a>",
                    ), width='full'),
                ),
            },

            {
                'name': "Je ne sais pas encore lire ni écrire",
                'description': "Des cours d'alphabétisation pour adultes existent à Neuchâtel. C'est possible à tout âge, dans un cadre bienveillant.",
                'tags': ['Cours de langue', 'Langue', 'Gratuit', 'En personne', 'Integration', 'Formation'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Femmes'],
                'body': body(
                    sec("C'est possible à tout âge",
                        para("Apprendre à lire et à écrire en tant qu'adulte est tout à fait possible. Les cours sont adaptés aux adultes, avancent à votre rythme et se passent dans un environnement bienveillant."),
                    ),
                    sec("Cours d'alphabétisation à Neuchâtel", ul(
                        "<b>COSM :</b> cours d'alphabétisation pour adultes migrants — 032 889 74 42 — premiers cours gratuits",
                        "<b>Caritas NE :</b> ateliers d'alphabétisation en petits groupes avec des bénévoles — 032 886 80 70 — gratuit",
                        "<b>RECIF (femmes) :</b> alphabétisation spécifique pour les femmes — <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>Croix-Rouge NE :</b> cours de base — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                    ), width='half'),
                    sec("Progression typique", ul(
                        "<b>Phase 1 :</b> reconnaissance des lettres et des sons (quelques mois)",
                        "<b>Phase 2 :</b> lecture et écriture simples — lire une pancarte, remplir un formulaire",
                        "<b>Phase 3 :</b> intégration dans un cours de français standard (A1, A2…)",
                        "La durée varie selon chaque personne — il n'y a pas de pression",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche des cours de langue avec des horaires flexibles",
                'description': "Des cours du soir et du week-end existent à Neuchâtel pour progresser rapidement en français.",
                'tags': ['Cours de langue', 'Langue', 'Formation', 'En personne', 'En ligne'],
                'audiences': ["Établis depuis plus d'un an", 'Jeune adulte', 'Compétences numériques de base'],
                'body': body(
                    sec("Pourquoi choisir un cours payant",
                        para("Les cours privés avancent plus vite, proposent des horaires flexibles (soir, week-end) et des formats intensifs. Ils sont adaptés aux personnes qui travaillent et veulent progresser rapidement."),
                    ),
                    sec("Options à Neuchâtel", ul(
                        "<b>Migros Klubschule :</b> cours tous niveaux, soir et week-end — <a href='https://www.klubschule.ch' target='_blank'>klubschule.ch</a> — env. CHF 200–400/semestre",
                        "<b>Alliance Française Neuchâtel :</b> cours officiels avec certification DELF — <a href='https://www.alliancefrancaise.ch' target='_blank'>alliancefrancaise.ch</a>",
                        "<b>Inlingua Neuchâtel :</b> cours intensifs et semi-intensifs — <a href='https://www.inlingua-neuchatel.ch' target='_blank'>inlingua-neuchatel.ch</a>",
                        "<b>Université populaire NE :</b> cours abordables pour adultes — renseignez-vous en mairie",
                    ), width='half'),
                    sec("Certifications officielles", ul(
                        "<b>DELF :</b> diplôme officiel français (A1–B2) — reconnu dans le monde entier — passé à l'Alliance Française",
                        "<b>FIDE :</b> certificat suisse spécifique aux migrants — reconnu pour naturalisation et permis C",
                        "<b>TCF :</b> test de connaissance du français — rapide, peut être passé en ligne",
                        "Ces certifications restent valables même si vous changez de canton",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux me former en ligne pour améliorer mes compétences",
                'description': "Des cours en ligne gratuits ou peu chers me permettent d'apprendre un métier ou de progresser depuis chez moi.",
                'tags': ['E-learning', 'Formation', 'En ligne', 'Gratuit', 'Travail'],
                'audiences': ["Établis depuis plus d'un an", 'Jeune adulte', 'Compétences numériques de base'],
                'body': body(
                    sec("Plateformes gratuites ou quasi-gratuites", ul(
                        "<b>Coursera :</b> cours de grandes universités mondiales — audit gratuit — <a href='https://www.coursera.org' target='_blank'>coursera.org</a>",
                        "<b>edX :</b> MIT, Harvard, etc. — audit gratuit — <a href='https://www.edx.org' target='_blank'>edx.org</a>",
                        "<b>OpenClassrooms :</b> formation professionnalisante en français — <a href='https://openclassrooms.com' target='_blank'>openclassrooms.com</a>",
                        "<b>YouTube :</b> tutoriels gratuits dans tous les domaines",
                        "<b>Khan Academy :</b> maths, sciences, finances — <a href='https://fr.khanacademy.org' target='_blank'>fr.khanacademy.org</a>",
                    ), width='half'),
                    sec("Formations certifiantes suisses", ul(
                        "<b>Migros Klubschule en ligne :</b> cours mixtes présentiel + e-learning — <a href='https://www.klubschule.ch' target='_blank'>klubschule.ch</a>",
                        "<b>SwissSkills :</b> ressources sur les métiers suisses — <a href='https://www.swissskills.ch' target='_blank'>swissskills.ch</a>",
                        "<b>Formation continue UniNE :</b> modules en ligne — <a href='https://www.unine.ch/formcont' target='_blank'>unine.ch/formcont</a>",
                        "<b>LinkedIn Learning :</b> si vous avez un compte LinkedIn Premium — accès via bibliothèques pour certains",
                    ), width='half'),
                    sec("Conseils pour réussir en e-learning",
                        ul(
                            "Fixez-vous un horaire régulier — 30 min/jour vaut mieux que 4h le week-end",
                            "Choisissez un cours avec un certificat — cela motive et valorise votre CV",
                            "Rejoignez les forums et groupes du cours — vous n'êtes pas seul",
                            "Combinez e-learning et pratique réelle (stage, bénévolat)",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux étudier à l'université à Neuchâtel",
                'description': "Je veux savoir comment m'inscrire à l'UniNE ou à la HE-Arc et si des aides financières sont disponibles.",
                'tags': ['Universite', 'Formation', 'Reconnaissance diplome', 'Budget', 'En ligne'],
                'audiences': ['Jeune adulte', "Établis depuis plus d'un an", 'Formation supérieure'],
                'body': body(
                    sec("Université de Neuchâtel (UniNE)",
                        ul(
                            "<b>Site :</b> <a href='https://www.unine.ch' target='_blank'>unine.ch</a>",
                            "<b>Domaines :</b> droit, sciences économiques, lettres, sciences naturelles, théologie",
                            "<b>Écolage :</b> environ CHF 730/semestre pour les résidents suisses",
                            "<b>Admission :</b> maturité suisse ou équivalent reconnu — vérifiez sur unine.ch/admission",
                        ),
                    ),
                    sec("Haute École Arc (HE-Arc)", ul(
                        "<b>Site :</b> <a href='https://www.he-arc.ch' target='_blank'>he-arc.ch</a>",
                        "<b>Domaines :</b> ingénierie, gestion, conservation-restauration, santé",
                        "<b>Sites :</b> Neuchâtel, La Chaux-de-Fonds, Delémont",
                        "<b>Formation :</b> Bachelor et Master, en français",
                    ), width='half'),
                    sec("Bourses et aide financière", ul(
                        "<b>Bourses cantonales NE :</b> demande au OCAB via GSR",
                        "<b>Bourses fédérales :</b> pour les étrangers non-UE — <a href='https://www.sbfi.admin.ch/bourses' target='_blank'>sbfi.admin.ch</a>",
                        "<b>Fonds d'entraide UniNE :</b> aide ponctuelle pour étudiants en difficulté",
                        "<b>Jobroom étudiant :</b> <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a>",
                    ), width='half'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Children & family',
        'description': 'Garde, allocations familiales, scolarisation et droits parentaux.',
        'icon': 'UsersIcon',
        'priority': 6,
        'audiences': ['Parents'],
        'resources': [

            {
                'name': "Je veux recevoir les allocations pour mes enfants",
                'description': "En Suisse, chaque famille avec enfants reçoit des allocations chaque mois. Voici comment les obtenir à Neuchâtel.",
                'tags': ['Allocations familiales', 'Enfants', 'Formulaire', 'Budget', 'Aide sociale'],
                'audiences': ['Parents'],
                'body': body(
                    sec("Ce que vous recevez (Neuchâtel, 2025)",
                        ul(
                            "<b>Enfant de moins de 16 ans :</b> CHF 215/mois minimum (vérifiez le montant actuel — il évolue)",
                            "<b>Enfant de 16 à 25 ans en formation :</b> CHF 268/mois minimum",
                            "Les montants varient selon la caisse d'allocations familiales",
                            "Vous pouvez réclamer jusqu'à 5 ans en arrière si vous ne saviez pas",
                        ),
                    ),
                    sec("Comment les recevoir",
                        ul(
                            "<b>Si vous travaillez :</b> votre employeur fait la demande à votre place — demandez-lui",
                            "<b>Si vous êtes indépendant :</b> demandez à la CCNC (Caisse cantonale)",
                            "<b>Si vous êtes sans emploi :</b> contactez la CCNC directement",
                        ),
                    ),
                    sec("FER-CIAF (salariés)", ul(
                        "<b>Adresse :</b> Avenue du Premier-Mars 18, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 727 37 05",
                        "<b>Email :</b> alfa@cian.ch",
                        "<b>Heures :</b> lun–jeu 8h–11h45 / 13h45–17h; ven 8h–11h45",
                    ), width='half'),
                    sec("CCNC (indépendants et sans emploi)", ul(
                        "<b>Adresse :</b> Faubourg de l'Hôpital 28, 2001 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 65 01",
                        "<b>Email :</b> ccnc@ne.ch",
                        "<b>Site :</b> <a href='https://www.caisseavsne.ch' target='_blank'>caisseavsne.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux inscrire mon enfant à l'école",
                'description': "L'école est gratuite et obligatoire pour tous les enfants. Je veux savoir comment faire la démarche et ce qui se passe.",
                'tags': ['Enfants', 'Scolarisation', 'Integration', 'Gratuit', 'Formulaire'],
                'audiences': ['Parents', 'Nouveaux arrivants'],
                'body': body(
                    sec("Ce que vous devez savoir",
                        ul(
                            "L'école est <b>gratuite et obligatoire</b> pour tous les enfants de 4 à 15 ans",
                            "Tous les enfants ont le droit à l'école, quelle que soit leur situation administrative",
                            "L'année scolaire commence en août",
                            "Les fournitures de base sont souvent fournies gratuitement",
                        ),
                    ),
                    sec("Comment inscrire votre enfant",
                        ol(
                            "Allez au secrétariat communal (mairie) de votre commune",
                            "Apportez : passeports, permis de séjour, et si possible les bulletins scolaires du pays d'origine",
                            "La commune vous indique l'école et, si besoin, oriente vers une classe d'accueil",
                        ),
                    ),
                    sec("Classes d'accueil",
                        para("Si votre enfant ne parle pas encore le français, il sera placé dans une classe d'accueil. Il y apprend le français avant de rejoindre une classe ordinaire. Ce processus dure généralement 6 à 12 mois."),
                        ul(
                            "<b>Service de l'enseignement obligatoire NE :</b> <a href='https://www.ne.ch/enseignement' target='_blank'>ne.ch/enseignement</a>",
                            "<b>COSM :</b> peut vous accompagner dans les démarches — 032 889 74 42",
                        ),
                    ),
                ),
            },

            {
                'name': "Je cherche une place en crèche pour mon enfant",
                'description': "Je veux trouver une place en crèche ou garderie à Neuchâtel et savoir si je peux bénéficier d'une aide financière.",
                'tags': ['Garde enfants', 'Enfants', 'Formulaire', 'En personne', 'Budget', 'Subvention'],
                'audiences': ['Parents'],
                'body': body(
                    sec("L'essentiel",
                        para("Les crèches sont très demandées. Inscrivez votre enfant le plus tôt possible — même avant sa naissance."),
                        para("Les tarifs sont calculés selon vos revenus. Une aide financière du canton peut réduire le coût."),
                    ),
                    sec("Comment trouver une place",
                        ol(
                            "Cherchez sur le site de votre commune — elles listent souvent les structures disponibles",
                            "Inscrivez votre enfant dans plusieurs structures en même temps",
                            "Demandez une subvention cantonale dès que vous avez une place confirmée",
                        ),
                    ),
                    sec("Liens utiles",
                        ul(
                            "<b>Structures d'accueil NE :</b> <a href='https://www.ne.ch/structures-accueil' target='_blank'>ne.ch/structures-accueil</a>",
                            "<b>Subvention garde :</b> renseignez-vous à votre GSR",
                            "<b>Tarifs :</b> environ CHF 30–100/jour selon revenus avant subvention",
                        ),
                    ),
                ),
            },

            {
                'name': "Mon enfant a besoin d'aide pour apprendre le français à l'école",
                'description': "Des cours de rattrapage et des ressources existent pour les enfants qui apprennent le français à l'école.",
                'tags': ['Enfants', 'Soutien scolaire', 'Cours de langue', 'Langue', 'Gratuit', 'Integration'],
                'audiences': ['Parents', 'Nouveaux arrivants'],
                'body': body(
                    sec("Ce qui existe",
                        ul(
                            "<b>Classes d'accueil :</b> pour les enfants nouvellement arrivés, avant de rejoindre une classe normale",
                            "<b>Cours d'appui :</b> certaines communes proposent du soutien gratuit après l'école",
                            "<b>COSM :</b> peut vous renseigner sur les ressources de soutien scolaire disponibles localement",
                            "<b>Bénévoles Caritas :</b> aide aux devoirs gratuite — renseignez-vous à Caritas NE",
                        ),
                    ),
                    sec("Comment accéder à ces aides",
                        ol(
                            "Parlez-en à l'enseignant ou au directeur de l'école",
                            "Contactez le service scolaire de votre commune",
                            "Appelez le COSM : 032 889 74 42",
                        ),
                    ),
                ),
            },

            {
                'name': "Je subis des violences à la maison",
                'description': "Je peux appeler la police ou un service spécialisé. Des professionnels peuvent m'aider en toute confidentialité.",
                'tags': ['Femmes', 'Urgence', 'Aide juridique', 'Droits', 'Sante mentale', 'Gratuit'],
                'audiences': ['Femmes', 'Parents', 'Nouveaux arrivants'],
                'body': body(
                    sec("Appelez si vous êtes en danger",
                        ul(
                            "<b>Police :</b> 117 — intervient immédiatement",
                            "<b>Centre LAVI NE :</b> 032 889 51 00 — soutien psychologique et juridique pour victimes de violence",
                            "<b>La Main Tendue :</b> 143 — écoute anonyme 24h/24",
                        ),
                    ),
                    sec("Aide spécialisée à Neuchâtel", ul(
                        "<b>Centre LAVI NE :</b> Rue du Seyon 1, 2000 Neuchâtel — 032 889 51 00 — lun–ven 8h–12h / 13h30–17h",
                        "<b>SOLIDfemmes (foyer d'accueil) :</b> hébergement d'urgence pour femmes en danger — 032 724 32 20 — disponible 24h/24",
                        "<b>RECIF :</b> soutien et orientation pour femmes migrantes — <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>CSP Neuchâtel :</b> aide juridique — 032 886 91 00",
                    ), width='half'),
                    sec("Ce que la police peut faire", ul(
                        "Expulser l'auteur des violences du logement pour 10 jours",
                        "Prononcer une interdiction de contact",
                        "Vous accompagner en lieu sûr",
                        "<b>Important :</b> la violence conjugale est un délit en Suisse, même dans le mariage",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche une garde pour mes enfants avant ou après l'école",
                'description': "Les structures parascolaires gardent les enfants le matin, le midi et après l'école. Voici comment m'inscrire.",
                'tags': ['Garde enfants', 'Enfants', 'Scolarisation', 'Budget', 'Subvention'],
                'audiences': ['Parents'],
                'body': body(
                    sec("Qu'est-ce que le parascolaire",
                        para("Les structures parascolaires (UAPE — Unité d'Accueil Pour Écoliers) gardent les enfants avant l'école le matin, le midi et après l'école le soir. C'est très utile si vous travaillez."),
                    ),
                    sec("Comment inscrire votre enfant",
                        ol(
                            "Contactez le service scolaire de votre commune dès l'inscription à l'école",
                            "Remplissez le formulaire d'inscription — les places sont limitées",
                            "Les tarifs sont calculés en fonction de votre revenu",
                            "Demandez une réduction de tarif via votre GSR si vos revenus sont modestes",
                        ),
                    ),
                    sec("Liens utiles", ul(
                        "<b>Neuchâtel ville :</b> <a href='https://www.neuchatelville.ch/parascolaire' target='_blank'>neuchatelville.ch</a> — parascolaire",
                        "<b>La Chaux-de-Fonds :</b> renseignez-vous au secrétariat scolaire de votre école",
                        "<b>Tarifs :</b> environ CHF 5–20/jour selon revenus",
                        "<b>Aide financière :</b> via GSR selon situation",
                    ), width='full'),
                ),
            },

            {
                'name': "Je cherche des activités pour mes enfants pendant les vacances",
                'description': "Pendant les vacances scolaires, des colonies, camps et activités à prix réduit existent à Neuchâtel pour les enfants.",
                'tags': ['Enfants', 'Gratuit', 'Budget', 'Integration', 'Vie sociale'],
                'audiences': ['Parents', 'Nouveaux arrivants'],
                'body': body(
                    sec("Pourquoi c'est utile",
                        para("Pendant les vacances scolaires, les enfants ont besoin d'activités. Des structures proposent des camps, colonies et animations à tarif réduit ou gratuit pour les familles à revenus modestes."),
                    ),
                    sec("Activités à Neuchâtel", ul(
                        "<b>Maisons de quartier :</b> animations vacances pour enfants — demandez à votre mairie",
                        "<b>Jeunesse et Sports (J+S) :</b> camps sportifs subventionnés — <a href='https://www.jugendundsport.ch/fr' target='_blank'>jugendundsport.ch</a>",
                        "<b>Camps de Pro Juventute :</b> colonie de vacances à tarif social — <a href='https://www.projuventute.ch' target='_blank'>projuventute.ch</a>",
                        "<b>Croix-Rouge NE :</b> activités ponctuelles — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                    ), width='half'),
                    sec("Aides financières", ul(
                        "<b>GSR :</b> peut parfois financer des camps ou colonies pour les familles à l'aide sociale",
                        "<b>Bourses de loisirs :</b> certaines communes accordent une aide — renseignez-vous à la mairie",
                        "<b>Bibliothèques :</b> gratuites, proposent des animations en période de vacances",
                        "<b>Bois et parcs :</b> les espaces naturels autour de Neuchâtel sont gratuits et accessibles en transports",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux connaître mes droits lors d'une naissance",
                'description': "Je veux savoir à quoi j'ai droit pour le congé maternité, le congé paternité et les allocations pour perte de gain.",
                'tags': ['Droits parentaux', 'Famille', 'Travail', 'Allocation', 'Budget'],
                'audiences': ['Parents', 'Nouveaux arrivants'],
                'body': body(
                    sec("Congé maternité (14 semaines)",
                        ul(
                            "<b>Durée :</b> 98 jours (14 semaines) après l'accouchement",
                            "<b>Montant :</b> 80 % du salaire, max CHF 220/jour",
                            "<b>Condition :</b> avoir travaillé et cotisé à l'AVS pendant 5 mois avant",
                            "<b>Démarches :</b> votre employeur contacte la caisse AVS",
                        ),
                    ),
                    sec("Congé paternité (2 semaines)",
                        ul(
                            "<b>Durée :</b> 10 jours de travail dans les 6 mois après la naissance",
                            "<b>Montant :</b> 80 % du salaire, max CHF 220/jour",
                            "<b>Condition :</b> avoir cotisé à l'AVS pendant 9 mois avant",
                            "<b>À venir :</b> un congé parental étendu est en discussion au Parlement fédéral",
                        ),
                    ),
                    sec("APG — Allocations pour perte de gain", ul(
                        "Système qui verse les indemnités maternité et paternité",
                        "<b>Caisse compétente :</b> CCNC Neuchâtel — 032 889 65 01",
                        "<b>Info :</b> <a href='https://www.ch.ch/maternite' target='_blank'>ch.ch/maternite</a>",
                    ), width='full'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Rights & duties',
        'description': "Permis de séjour, procédure d'asile, aide juridique et regroupement familial.",
        'icon': 'ScaleIcon',
        'priority': 7,
        'audiences': ["Demandeur d'asile", 'Résident long terme', "Établis depuis plus d'un an"],
        'resources': [

            {
                'name': "Je ne comprends pas les différents permis de séjour",
                'description': "Je veux comprendre ce que signifie mon permis et quels droits j'ai selon le type de permis que je possède.",
                'tags': ['Permis sejour', 'Droits', 'Documents officiels', 'Multilingue', 'Permis N/F/S'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Les différents permis",
                        ul(
                            "<b>Permis N :</b> demandeur d'asile en cours de procédure. Travail possible sous conditions.",
                            "<b>Permis F :</b> admis provisoirement. Travail autorisé.",
                            "<b>Permis S :</b> protection temporaire (ex: personnes d'Ukraine). Travail autorisé.",
                            "<b>Permis B :</b> séjour d'un an renouvelable. Travail libre.",
                            "<b>Permis C :</b> établissement permanent (après 5 à 10 ans). Droits proches du citoyen suisse.",
                            "<b>Permis G :</b> frontalier — travaille en Suisse, habite dans un pays voisin.",
                            "<b>Permis L :</b> séjour de courte durée (moins d'un an).",
                        ),
                    ),
                    sec("Renouveler son permis",
                        ul(
                            "Faites la demande <b>au moins 2 semaines avant</b> l'expiration",
                            "À Neuchâtel, contactez le SMIG",
                            "Envoyez les documents par courrier ou prenez rendez-vous au SMIG",
                        ),
                    ),
                    sec("SMIG — Service des migrations NE", ul(
                        "<b>Adresse :</b> Rue de Tivoli 28, 2002 Neuchâtel 2",
                        "<b>Téléphone :</b> 032 889 63 10",
                        "<b>Email :</b> smig@ne.ch",
                        "<b>Heures :</b> lun–ven 8h–12h; mer aussi 13h30–17h",
                        "<b>Site :</b> <a href='https://www.ne.ch/smig' target='_blank'>ne.ch/smig</a>",
                    ), width='half'),
                    sec("SEM — niveau fédéral", ul(
                        "<b>SEM :</b> autorité fédérale qui fixe les règles",
                        "<b>Site :</b> <a href='https://www.sem.admin.ch' target='_blank'>sem.admin.ch</a>",
                        "<b>Infos en plusieurs langues :</b> <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai besoin d'aide juridique gratuite",
                'description': "Des associations peuvent m'aider gratuitement si j'ai des problèmes avec mon permis ou si je ne connais pas mes droits.",
                'tags': ['Aide juridique', 'Droits', 'Gratuit', 'En personne', 'Traduction disponible'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
                'body': body(
                    sec("Pourquoi consulter",
                        para("Des professionnels peuvent vous aider si vous avez des problèmes avec votre permis, une décision négative du SMIG, ou des questions sur vos droits."),
                    ),
                    sec("CSP Neuchâtel — principal organisme", ul(
                        "<b>Neuchâtel :</b> Rue des Parcs 11, 2000 Neuchâtel",
                        "<b>La Chaux-de-Fonds :</b> Rue du Temple-Allemand 23, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 886 91 00",
                        "<b>Email :</b> csp.neuchatel@ne.ch",
                        "<b>Permanences migration :</b> jeudi 13h30–16h à Neuchâtel (sur RDV)",
                        "<b>Site :</b> <a href='https://csp.ch/neuchatel' target='_blank'>csp.ch/neuchatel</a>",
                    ), width='half'),
                    sec("Caritas — Bureau de consultation juridique (BCJ)", ul(
                        "<b>Adresse :</b> Vieux-Châtel 4, 2002 Neuchâtel",
                        "<b>Téléphone :</b> 026 552 50 40",
                        "<b>Email :</b> bcj-fr@caritas.ch",
                        "<b>Sans RDV :</b> mardi 9h–12h",
                        "Spécialisé en droit d'asile et droit des étrangers",
                    ), width='half'),
                    sec("Autres ressources",
                        ul(
                            "<b>OSAR (Conseil suisse des réfugiés) :</b> <a href='https://www.osar.ch' target='_blank'>osar.ch</a>",
                            "<b>Ensemble-ne.ch :</b> infos juridiques en 18 langues — <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>",
                            "<b>Centre LAVI NE :</b> 032 889 51 00 — victimes de violence",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux comprendre la procédure d'asile",
                'description': "Je veux savoir quelles sont les étapes de ma demande d'asile en Suisse et quels sont mes droits pendant la procédure.",
                'tags': ['Asile', 'Permis N/F/S', 'Droits', 'Formulaire', 'Traduction disponible', 'Interprete'],
                'audiences': ["Demandeur d'asile"],
                'body': body(
                    sec("Les grandes étapes",
                        ol(
                            "<b>Dépôt de la demande :</b> dans un centre fédéral d'asile (CFA). Un interprète est présent.",
                            "<b>Audition sur les motifs :</b> vous expliquez pourquoi vous avez quitté votre pays",
                            "<b>Décision du SEM :</b> le Secrétariat d'État aux migrations rend sa décision",
                            "<b>Si positif :</b> statut de réfugié (permis B) ou admission provisoire (permis F)",
                            "<b>Si négatif :</b> 30 jours pour faire recours au Tribunal administratif fédéral",
                        ),
                    ),
                    sec("Vos droits pendant la procédure",
                        ul(
                            "Droit à un représentant juridique gratuit",
                            "Un interprète est fourni pour toutes les auditions",
                            "Hébergement, nourriture et aide médicale de base couverts",
                            "Avec un permis N, travail possible après 3 mois sous conditions",
                        ),
                    ),
                    sec("À Neuchâtel", ul(
                        "<b>SMIG :</b> Rue de Tivoli 28 — 032 889 63 10",
                        "<b>CSP Neuchâtel (aide juridique) :</b> 032 886 91 00",
                        "<b>Caritas BCJ :</b> 026 552 50 40 — mardi 9h–12h sans RDV",
                        "<b>Ensemble-ne.ch :</b> <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a> — infos en 18 langues",
                    ), width='half'),
                    sec("Niveau fédéral", ul(
                        "<b>SEM :</b> <a href='https://www.sem.admin.ch' target='_blank'>sem.admin.ch</a>",
                        "<b>OSAR :</b> <a href='https://www.osar.ch' target='_blank'>osar.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux faire venir ma famille en Suisse",
                'description': "Je veux savoir si je peux faire venir ma famille, quelles conditions je dois remplir et comment faire la demande.",
                'tags': ['Regroupement familial', 'Famille', 'Formulaire', 'Documents officiels', 'Permis B', 'Permis C'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Qui peut faire venir sa famille",
                        ul(
                            "<b>Permis C :</b> conjoint et enfants de moins de 18 ans — droits étendus",
                            "<b>Permis B :</b> conjoint et enfants — sous conditions de revenus et de logement",
                            "<b>Permis F :</b> possible après 3 ans de résidence et intégration démontrée",
                            "<b>Permis N :</b> en principe non autorisé pendant la procédure",
                        ),
                    ),
                    sec("Conditions principales",
                        ul(
                            "Logement suffisamment grand pour toute la famille",
                            "Revenus suffisants (pas de dépendance à l'aide sociale)",
                            "Demande à faire dans les 5 ans (conjoint) ou 12 mois (enfants)",
                        ),
                    ),
                    sec("Comment faire",
                        ol(
                            "Déposez la demande au SMIG : Rue de Tivoli 28, 2002 Neuchâtel — 032 889 63 10",
                            "Votre famille demande un visa à l'ambassade suisse dans son pays",
                            "Documents : acte de mariage/naissance, passeports, preuves de revenus, bail",
                        ),
                    ),
                    sec("Plus d'informations",
                        ul(
                            "<b>SEM :</b> <a href='https://www.sem.admin.ch/regroupement-familial' target='_blank'>sem.admin.ch</a>",
                            "<b>Guide ch.ch :</b> <a href='https://www.ch.ch/fr/migration/regroupement-familial/' target='_blank'>ch.ch/regroupement-familial</a>",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux devenir citoyen suisse",
                'description': "Je veux connaître les conditions pour demander la naturalisation et les démarches à faire dans le canton de Neuchâtel.",
                'tags': ['Naturalisation', 'Integration', 'Documents officiels', 'Formulaire', 'Langue'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Conditions générales",
                        ul(
                            "Résider en Suisse depuis <b>10 ans</b> (les années entre 8 et 18 ans comptent double)",
                            "Avoir un permis C",
                            "Maîtriser une langue nationale (B1 oral minimum)",
                            "Être bien intégré, respecter les lois, ne pas dépendre de l'aide sociale",
                        ),
                    ),
                    sec("À Neuchâtel",
                        ul(
                            "La naturalisation passe par le SMIG (demande cantonale) et votre commune",
                            "Certaines communes organisent une cérémonie ou un entretien",
                            "<b>SMIG :</b> Rue de Tivoli 28, 2002 Neuchâtel — 032 889 63 10 — <a href='https://www.ne.ch/naturalisation' target='_blank'>ne.ch/naturalisation</a>",
                            "<b>Guide SEM :</b> <a href='https://www.sem.admin.ch/naturalisation' target='_blank'>sem.admin.ch/naturalisation</a>",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux passer du permis B au permis C",
                'description': "Je veux savoir quand et comment demander le permis d'établissement après plusieurs années en Suisse.",
                'tags': ['Permis C', 'Permis sejour', 'Documents officiels', 'Formulaire', 'Integration'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Conditions selon l'origine",
                        ul(
                            "<b>Ressortissants UE/AELE :</b> après 5 ans de séjour légal avec permis B",
                            "<b>Ressortissants hors UE/AELE :</b> après 10 ans en Suisse (dont 5 ans avec permis B)",
                            "<b>Condition commune :</b> bonne intégration, respect des lois, pas de dépendance durable à l'aide sociale",
                            "<b>Conjoint(e) de Suisse :</b> conditions assouplies — renseignez-vous au SMIG",
                        ),
                    ),
                    sec("Comment faire la demande",
                        ol(
                            "Contactez le SMIG 3 à 6 mois avant l'échéance de votre permis B",
                            "Apportez : passeport, permis B en cours, justificatifs de revenus et de logement",
                            "Le SMIG vérifie les conditions et transmet au SEM si nécessaire",
                        ),
                    ),
                    sec("SMIG Neuchâtel", ul(
                        "<b>Adresse :</b> Rue de Tivoli 28, 2002 Neuchâtel 2",
                        "<b>Téléphone :</b> 032 889 63 10",
                        "<b>Email :</b> smig@ne.ch",
                        "<b>Site :</b> <a href='https://www.ne.ch/smig' target='_blank'>ne.ch/smig</a>",
                    ), width='full'),
                ),
            },

            {
                'name': "Je veux voter aux élections à Neuchâtel",
                'description': "À Neuchâtel, les étrangers peuvent voter après 5 ans de résidence. Je veux savoir comment m'inscrire.",
                'tags': ['Droits', 'Integration', 'Documents officiels', 'Permis C', 'Permis B'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Le droit de vote cantonal",
                        para("Neuchâtel est le seul canton suisse à accorder le droit de vote et d'éligibilité aux étrangers aux élections cantonales et communales."),
                        ul(
                            "<b>Condition :</b> résider dans le canton depuis au moins 5 ans",
                            "<b>Niveau :</b> élections cantonales et communales (pas fédérales)",
                            "<b>Vous pouvez aussi être élu(e)</b> à certaines fonctions communales",
                        ),
                    ),
                    sec("Comment s'inscrire sur les listes électorales",
                        ol(
                            "Demandez le formulaire d'inscription à votre commune (contrôle des habitants)",
                            "Apportez votre permis de séjour et une preuve de domicile",
                            "Vous recevrez ensuite votre matériel de vote par courrier",
                        ),
                    ),
                    sec("Plus d'informations", ul(
                        "<b>Chancellerie d'État NE :</b> <a href='https://www.ne.ch/elections' target='_blank'>ne.ch/elections</a>",
                        "<b>Votre commune :</b> contrôle des habitants — renseignez-vous directement",
                        "C'est un droit unique en Suisse — profitez-en pour participer à la vie locale",
                    ), width='full'),
                ),
            },

            {
                'name': "Je divorce, est-ce que ça change mon droit de séjour ?",
                'description': "Une séparation peut affecter mon permis de séjour. Je veux savoir ce que ça change selon ma situation.",
                'tags': ['Droits', 'Aide juridique', 'Famille', 'Permis sejour', 'Permis B'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Ce qui change selon votre permis",
                        ul(
                            "<b>Permis C :</b> le divorce n'affecte généralement pas votre droit de séjour",
                            "<b>Permis B (obtenu par regroupement familial) :</b> le divorce peut entraîner le non-renouvellement — il faut démontrer une raison importante de rester (enfants, intégration, durée de séjour)",
                            "<b>Moins de 3 ans de mariage :</b> situation plus précaire — consultez immédiatement un juriste",
                        ),
                    ),
                    sec("Aide juridique d'urgence", ul(
                        "<b>CSP Neuchâtel :</b> 032 886 91 00 — permanence migration jeudi 13h30–16h",
                        "<b>Caritas BCJ :</b> 026 552 50 40 — mardi 9h–12h sans RDV",
                        "<b>Centre LAVI NE :</b> 032 889 51 00 — si séparation liée à des violences",
                    ), width='half'),
                    sec("Démarches au SMIG", ul(
                        "Informez le SMIG du changement de situation dès que possible",
                        "Ne dépassez pas la date d'expiration de votre permis sans avoir déposé une demande",
                        "<b>SMIG :</b> 032 889 63 10 — smig@ne.ch",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai été victime de discrimination",
                'description': "La discrimination est illégale en Suisse. Je veux savoir quoi faire et où m'adresser pour défendre mes droits.",
                'tags': ['Discrimination', 'Droits', 'Aide juridique', 'En personne', 'Gratuit'],
                'audiences': [],
                'body': body(
                    sec("C'est illégal",
                        para("En Suisse, la discrimination à cause de la nationalité, de l'origine, de la religion ou de la couleur de peau est interdite. Vous avez le droit de vous défendre."),
                    ),
                    sec("Que faire",
                        ol(
                            "Notez tout : date, lieu, ce qui s'est passé, témoins éventuels",
                            "Conservez toutes les preuves (emails, refus écrits, photos)",
                            "Contactez une association spécialisée pour vous conseiller",
                            "Portez plainte si un acte discriminatoire constitue une infraction pénale",
                        ),
                    ),
                    sec("Contacts à Neuchâtel", ul(
                        "<b>COSM (Bureau du délégué) :</b> 032 889 74 42 — cosm@ne.ch — peut orienter et soutenir",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00 — aide juridique",
                        "<b>Centre LAVI NE :</b> 032 889 51 00 — si vous avez subi des violences",
                    ), width='half'),
                    sec("Niveau national", ul(
                        "<b>CFR (Commission fédérale contre le racisme) :</b> <a href='https://www.ekr.admin.ch' target='_blank'>ekr.admin.ch</a>",
                        "<b>Humanrights.ch :</b> <a href='https://www.humanrights.ch' target='_blank'>humanrights.ch</a>",
                        "<b>ACOR SOS-Racisme :</b> <a href='https://sos-racisme.ch' target='_blank'>sos-racisme.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je dois obtenir un document d'état civil (acte de naissance, mariage)",
                'description': "Pour certaines démarches en Suisse, on me demande un acte de naissance ou de mariage. Je veux savoir comment l'obtenir depuis mon pays.",
                'tags': ['Documents officiels', 'Permis sejour', 'Formulaire', 'Famille'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Parents'],
                'body': body(
                    sec("Pourquoi ces documents sont demandés",
                        para("Les documents d'état civil (acte de naissance, mariage, divorce) sont souvent nécessaires pour le regroupement familial, la naturalisation, l'inscription à l'école ou certaines démarches administratives."),
                    ),
                    sec("Documents provenant de votre pays d'origine",
                        ol(
                            "Contactez l'ambassade ou le consulat de votre pays en Suisse — ils peuvent parfois obtenir le document pour vous",
                            "Demandez à un membre de votre famille restée dans votre pays de l'obtenir auprès de la mairie locale",
                            "Faites traduire le document par un traducteur assermenté si c'est demandé",
                            "Si votre pays ne délivre plus de documents (guerre, etc.) : signalez-le au SMIG ou à l'avocat qui vous aide",
                        ),
                    ),
                    sec("Documents suisses (si vous êtes né ou marié en Suisse)", ul(
                        "<b>Office de l'état civil NE :</b> Rue du Seyon 4, 2000 Neuchâtel — 032 889 67 87",
                        "<b>En ligne :</b> <a href='https://www.ne.ch/etat-civil' target='_blank'>ne.ch/etat-civil</a>",
                        "Extrait d'acte de naissance ou de mariage disponible sur demande (CHF 30 environ)",
                    ), width='half'),
                    sec("Aide pour les documents étrangers", ul(
                        "<b>COSM :</b> peut vous orienter — 032 889 74 42",
                        "<b>CSP Neuchâtel :</b> aide juridique pour les dossiers complexes — 032 886 91 00",
                        "<b>Traducteurs assermentés :</b> demandez la liste au SMIG ou au COSM",
                        "<b>Info ch.ch :</b> <a href='https://www.ch.ch/fr/etat-civil/' target='_blank'>ch.ch/etat-civil</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je viens d'arriver, je dois m'inscrire à ma commune",
                'description': "Je dois m'annoncer au bureau communal dans les 14 jours après mon arrivée. Voici comment faire et ce que j'obtiens.",
                'tags': ['Documents officiels', 'Droits', 'Formulaire', 'En personne', 'Integration'],
                'audiences': ['Nouveaux arrivants'],
                'body': body(
                    sec("Pourquoi c'est obligatoire",
                        para("En Suisse, toute personne qui s'installe dans une commune doit s'annoncer au Contrôle des habitants (bureau communal) dans les 14 jours. C'est obligatoire, même si vous êtes déjà enregistré au SMIG."),
                    ),
                    sec("Ce que vous obtenez",
                        ul(
                            "Une attestation de domicile — nécessaire pour ouvrir un compte bancaire, inscrire vos enfants à l'école, etc.",
                            "Votre numéro AVS (si c'est votre première inscription)",
                            "Des informations sur votre commune (poubelles, horaires, etc.)",
                        ),
                    ),
                    sec("Documents à apporter",
                        ul(
                            "Passeport ou carte d'identité",
                            "Permis de séjour (ou preuve de demande au SMIG)",
                            "Contrat de bail ou attestation de l'hébergeur",
                            "Acte de naissance ou de mariage si vous avez une famille",
                        ),
                    ),
                    sec("Où aller", ul(
                        "<b>Neuchâtel ville :</b> Hôtel de Ville, Rue de l'Hôpital 1 — 032 717 50 00",
                        "<b>La Chaux-de-Fonds :</b> Administration communale, Espacité 1 — 032 889 60 00",
                        "<b>Autres communes :</b> cherchez 'contrôle des habitants' + nom de votre commune",
                        "<b>Horaires :</b> généralement lun–ven 8h–12h / 13h30–17h",
                    ), width='full'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Housing',
        'description': "Logement urgence, droits du locataire, logement social et recherche d'appartement.",
        'icon': 'HomeIcon',
        'priority': 9,
        'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
        'resources': [

            {
                'name': "Je n'ai pas de logement, j'ai besoin d'aide",
                'description': "Je n'ai nulle part où dormir ce soir. Voici les numéros à appeler et les structures disponibles à Neuchâtel.",
                'tags': ['Logement urgence', 'Urgence', 'En personne', 'Gratuit', 'Aide sociale'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
                'body': body(
                    sec("Appelez d'abord",
                        ul(
                            "<b>SMIG (demandeurs d'asile) :</b> Rue de Tivoli 28, Neuchâtel — 032 889 63 10 — ils orientent vers les hébergements d'asile",
                            "<b>GSR Neuchâtel (personnes domiciliées) :</b> 032 717 74 10 — peut orienter vers des solutions d'urgence",
                            "<b>Armée du Salut :</b> présente à Neuchâtel et La Chaux-de-Fonds — <a href='https://armeedusalut.ch/jai-besoin-dun-hebergement/' target='_blank'>armeedusalut.ch</a>",
                        ),
                    ),
                    sec("Structures d'hébergement pour demandeurs d'asile",
                        ul(
                            "Les demandeurs d'asile sont hébergés dans des centres cantonaux gérés par le SMIG",
                            "Centres à : Tête-de-Ran (Val-de-Ruz), Couvet (Val-de-Travers), Perreux (Boudry)",
                            "Après le premier accueil : logements loués dans les communes du canton",
                        ),
                    ),
                    sec("Pour les autres situations", ul(
                        "<b>Caritas NE :</b> 032 886 80 70 — peut orienter vers des solutions temporaires",
                        "<b>Croix-Rouge NE :</b> <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00 — accompagnement social",
                    ), width='half'),
                    sec("Aide d'urgence (aide de dernier recours)", ul(
                        "Si vous êtes débouté de l'asile, vous avez quand même droit à l'aide d'urgence",
                        "Contactez le SMIG : 032 889 63 10",
                        "Inclut : hébergement, nourriture, soins médicaux urgents",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux connaître mes droits en tant que locataire",
                'description': "Je veux comprendre mon bail, mes droits face à mon propriétaire et ce que je peux faire si j'ai un problème.",
                'tags': ['Droits du locataire', 'Bail', 'Droits', 'Logement', 'Multilingue'],
                'audiences': [],
                'body': body(
                    sec("Ce que vous devez savoir",
                        ul(
                            "Le bail est un contrat légal. Lisez-le attentivement avant de signer.",
                            "L'état des lieux d'entrée est très important — signalez tout défaut immédiatement",
                            "Le loyer ne peut pas être augmenté sans raison valable et préavis",
                            "Le propriétaire ne peut pas entrer chez vous sans votre accord",
                        ),
                    ),
                    sec("Points clés du bail",
                        ul(
                            "<b>Dépôt de garantie :</b> maximum 3 mois de loyer, sur un compte bancaire bloqué à votre nom",
                            "<b>Résiliation :</b> respectez les délais (en général 3 mois avant la fin du trimestre)",
                            "<b>État des lieux de sortie :</b> exigez d'y assister et obtenez une copie signée",
                        ),
                    ),
                    sec("En cas de problème", ul(
                        "<b>Asloca Neuchâtel :</b> association des locataires — conseil juridique — <a href='https://www.asloca.ch' target='_blank'>asloca.ch</a>",
                        "<b>Autorité de conciliation NE :</b> recours gratuit avant tout tribunal",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00 — aide juridique générale",
                    ), width='half'),
                    sec("Ressources utiles", ul(
                        "<b>Formulaires de bail :</b> <a href='https://www.ne.ch/bail' target='_blank'>ne.ch/bail</a>",
                        "<b>Guide national :</b> <a href='https://www.ch.ch/fr/logement/bail/' target='_blank'>ch.ch/bail</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche un appartement à louer",
                'description': "Je veux savoir où chercher, quels documents préparer et comment augmenter mes chances de trouver un logement.",
                'tags': ['Logement', 'En ligne', 'Budget'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Les principales plateformes",
                        ul(
                            "<a href='https://www.homegate.ch' target='_blank'>homegate.ch</a> — le plus utilisé en Suisse",
                            "<a href='https://www.immoscout24.ch' target='_blank'>immoscout24.ch</a> — grand choix",
                            "<a href='https://www.anibis.ch' target='_blank'>anibis.ch</a> — petites annonces, souvent moins cher",
                            "Groupes Facebook locaux : 'appartement Neuchâtel', 'logement La Chaux-de-Fonds'",
                        ),
                    ),
                    sec("Documents à préparer",
                        ul(
                            "Copie de passeport et permis de séjour",
                            "3 dernières fiches de salaire",
                            "Extrait du registre des poursuites (gratuit à l'Office des poursuites de Neuchâtel)",
                            "Lettre de motivation courte",
                        ),
                    ),
                    sec("Conseils pratiques",
                        ul(
                            "Répondez très vite aux annonces — les appartements partent en quelques heures",
                            "Soignez votre présentation lors des visites",
                            "En cas de discrimination : contactez le COSM (032 889 74 42)",
                            "<b>Logement social :</b> renseignez-vous auprès de votre commune ou du GSR",
                        ),
                    ),
                ),
            },

            {
                'name': "Je ne comprends pas le dépôt de garantie",
                'description': "Je veux savoir à quoi sert le dépôt de garantie, comment le payer et comment le récupérer à la fin du bail.",
                'tags': ['Depot de garantie', 'Logement', 'Droits du locataire', 'Bail', 'Budget'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Ce que c'est",
                        para("Le dépôt de garantie est une somme d'argent que vous versez au propriétaire quand vous signez le bail. Il sert à couvrir d'éventuels dommages ou loyers impayés à la fin du contrat."),
                        ul(
                            "Maximum légal : <b>3 mois de loyer net</b>",
                            "Doit être déposé sur un compte bancaire bloqué au nom du locataire — pas remis directement au propriétaire",
                            "L'argent vous appartient — le propriétaire ne peut y accéder qu'en cas de litige",
                        ),
                    ),
                    sec("Comment payer",
                        ul(
                            "Ouvrez un compte de garantie dans une banque (présentez votre bail)",
                            "Alternative : garantie de loyer via une assurance (ex: Firstcaution, SwissCaution) — vous payez une prime annuelle au lieu d'immobiliser l'argent",
                            "<b>Firstcaution :</b> <a href='https://www.firstcaution.ch' target='_blank'>firstcaution.ch</a>",
                            "<b>SwissCaution :</b> <a href='https://www.swisscaution.ch' target='_blank'>swisscaution.ch</a>",
                        ),
                    ),
                    sec("Récupérer son dépôt", ul(
                        "Après l'état des lieux de sortie, le propriétaire a 1 an pour libérer le dépôt",
                        "Si tout est en ordre : remboursement intégral",
                        "En cas de litige : l'Asloca peut vous aider — <a href='https://www.asloca.ch' target='_blank'>asloca.ch</a>",
                    ), width='half'),
                    sec("À savoir", ul(
                        "Exigez toujours un reçu ou la confirmation du compte bancaire créé",
                        "Photographiez chaque pièce lors de l'état des lieux d'entrée",
                        "<b>Asloca NE :</b> conseil gratuit aux locataires — <a href='https://www.asloca.ch' target='_blank'>asloca.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je cherche un logement à loyer réduit",
                'description': "Si mes revenus sont faibles, je peux demander un logement social. Voici où m'inscrire dans le canton de Neuchâtel.",
                'tags': ['Logement social', 'Budget', 'Aide sociale', 'Formulaire', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Senior'],
                'body': body(
                    sec("Qui peut en bénéficier",
                        para("Le logement social s'adresse aux personnes dont les revenus ne permettent pas d'accéder au marché locatif ordinaire. Les listes d'attente peuvent être longues — inscrivez-vous dès que possible."),
                    ),
                    sec("Organismes à contacter", ul(
                        "<b>Neuchâtel ville — Service du logement :</b> 032 717 50 00 — mairie, Rue de l'Hôpital 1",
                        "<b>La Chaux-de-Fonds — Service du logement :</b> 032 889 60 00 — Espacité 1",
                        "<b>GSR :</b> peut vous orienter selon votre situation — 032 717 74 10",
                        "<b>Caritas NE :</b> logements d'urgence ponctuels — 032 886 80 70",
                    ), width='half'),
                    sec("Conseils pratiques", ul(
                        "Inscrivez-vous auprès de plusieurs communes si possible",
                        "Signalez les changements de situation (enfants, revenus) pour rester prioritaire",
                        "En parallèle : cherchez aussi sur le marché privé (anibis.ch, homegate.ch)",
                        "Priorité donnée aux familles, personnes âgées et situations d'urgence",
                    ), width='half'),
                ),
            },

            {
                'name': "Je dois prendre une assurance pour mon appartement",
                'description': "L'assurance ménage est souvent obligatoire pour les locataires. Je veux savoir ce qu'elle couvre et où en souscrire une.",
                'tags': ['Assurance menage', 'Logement', 'Formulaire', 'Budget', 'En ligne'],
                'audiences': ['Nouveaux arrivants'],
                'body': body(
                    sec("Ce que ça couvre",
                        ul(
                            "<b>Assurance ménage (AMén) :</b> vos meubles, habits et objets en cas de vol, incendie ou dégât des eaux",
                            "<b>Responsabilité civile (RC privée) :</b> si vous causez accidentellement un dommage à quelqu'un ou à quelque chose",
                            "Les deux sont souvent vendues ensemble dans le même contrat",
                        ),
                    ),
                    sec("Obligatoire à Neuchâtel ?",
                        para("La RC privée est exigée par la plupart des propriétaires. Sans assurance ménage, votre dossier de candidature sera souvent refusé. Souscrivez-la avant de signer votre bail."),
                    ),
                    sec("Où souscrire", ul(
                        "<b>Comparer :</b> <a href='https://www.comparis.ch/assurances' target='_blank'>comparis.ch/assurances</a>",
                        "<b>Vaudoise :</b> présente à Neuchâtel — <a href='https://www.vaudoise.ch' target='_blank'>vaudoise.ch</a>",
                        "<b>Helvetia :</b> <a href='https://www.helvetia.com/ch/fr' target='_blank'>helvetia.com</a>",
                        "<b>AXA / Zurich :</b> en ligne et en agence",
                        "<b>Coût :</b> environ CHF 100–250/an selon la valeur des biens assurés",
                    ), width='full'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Integration',
        'description': "S'intégrer à Neuchâtel : COSM, associations, soutien pour les femmes et vie sociale.",
        'icon': 'GlobeAltIcon',
        'priority': 5,
        'audiences': ['Nouveaux arrivants'],
        'resources': [

            {
                'name': "Je viens d'arriver, que peut faire le COSM pour moi ?",
                'description': "Le COSM est le service cantonal qui aide les personnes migrantes à s'intégrer. C'est souvent le premier endroit à contacter.",
                'tags': ['Integration', 'Interprete', 'Traduction disponible', 'En personne', 'Multilingue', 'Droits'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Qu'est-ce que le COSM",
                        para("Le COSM (Service de la cohésion multiculturelle) est le service cantonal qui aide les personnes migrantes à s'intégrer dans le canton de Neuchâtel."),
                        para("C'est souvent le premier endroit à contacter quand vous arrivez. Ils peuvent vous orienter vers les bons services selon votre situation."),
                    ),
                    sec("Ce qu'ils proposent",
                        ul(
                            "Entretien d'accueil pour les nouveaux arrivants",
                            "Cours de français et d'alphabétisation",
                            "Interprètes communautaires pour vos rendez-vous médicaux, scolaires, administratifs",
                            "Permanences sociales dans plusieurs localités",
                            "Prévention de la discrimination et médiation",
                        ),
                    ),
                    sec("COSM La Chaux-de-Fonds (siège)", ul(
                        "<b>Adresse :</b> Place de la Gare 6, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 889 74 42",
                        "<b>Email :</b> cosm@ne.ch",
                        "<b>Heures :</b> lun–ven 8h–12h / 13h30–17h",
                        "<b>Site :</b> <a href='https://www.ne.ch/cosm' target='_blank'>ne.ch/cosm</a>",
                    ), width='half'),
                    sec("Permanences à Neuchâtel et Fleurier", ul(
                        "Des permanences du COSM existent aussi à Neuchâtel ville et à Fleurier",
                        "Renseignez-vous par téléphone pour les horaires actuels",
                        "<b>Interprètes :</b> demandez au COSM un interprète communautaire pour vos rendez-vous",
                        "<b>Infos en 18 langues :</b> <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je suis une femme migrante, je cherche du soutien",
                'description': "Le RECIF propose des cours de français, de l'aide administrative et des activités spécifiquement pour les femmes migrantes.",
                'tags': ['Femmes', 'Cours de langue', 'Integration', 'En personne', 'Gratuit', 'Sante mentale'],
                'audiences': ['Nouveaux arrivants', 'Femmes'],
                'body': body(
                    sec("Qu'est-ce que le RECIF",
                        para("Le RECIF (Centre de rencontres et d'échanges interculturels pour femmes) est une association neuchâteloise qui soutient spécifiquement les femmes migrantes."),
                        para("C'est un espace de rencontre, d'apprentissage et de soutien, dans un cadre bienveillant et entre femmes."),
                    ),
                    sec("Ce qu'ils proposent",
                        ul(
                            "Cours de français de l'alphabétisation jusqu'au niveau B1",
                            "Ateliers de conversation et d'échange culturel",
                            "Aide administrative (comprendre les courriers, remplir des formulaires)",
                            "Permanence d'information et d'orientation",
                            "Activités sociales et culturelles",
                            "Présent à Neuchâtel et La Chaux-de-Fonds",
                        ),
                    ),
                    sec("Contact RECIF", ul(
                        "<b>Adresse :</b> Rue de la Cassarde 22, 2000 Neuchâtel",
                        "<b>Site :</b> <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "Contactez via le site pour les horaires et l'inscription",
                        "Ouvert à toutes les femmes migrantes, quelle que soit leur situation",
                    ), width='half'),
                    sec("Pourquoi c'est utile", ul(
                        "Environnement rassurant entre femmes",
                        "Pas besoin de parler français pour commencer",
                        "Accompagnement individuel possible",
                        "Gratuit ou à très faible coût",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux rencontrer des gens et m'intégrer",
                'description': "Je veux rejoindre une association, faire du bénévolat et créer des liens dans le canton de Neuchâtel.",
                'tags': ['Vie sociale', 'Integration', 'Culture', 'Gratuit'],
                'audiences': ["Établis depuis plus d'un an", 'Nouveaux arrivants'],
                'body': body(
                    sec("Pourquoi c'est important",
                        para("Participer à la vie locale aide à apprendre le français, à créer des liens et à se sentir chez soi. Beaucoup d'associations accueillent volontiers de nouveaux membres."),
                    ),
                    sec("Comment trouver",
                        ul(
                            "<b>Bénévolat NE :</b> <a href='https://www.benevolat-ne.ch' target='_blank'>benevolat-ne.ch</a> — cherchez une activité bénévole selon vos intérêts",
                            "<b>Clubs sportifs :</b> demandez à votre commune ou au COSM",
                            "<b>Maisons de quartier :</b> activités culturelles, cours, rencontres — renseignez-vous dans votre quartier",
                            "<b>Bibliothèques municipales :</b> gratuites, proposent des événements ouverts à tous",
                            "<b>Associations culturelles :</b> le COSM peut vous mettre en relation avec des associations de votre communauté d'origine",
                        ),
                    ),
                    sec("À savoir",
                        ul(
                            "Participer à la vie associative est un critère positif pour la naturalisation",
                            "Beaucoup d'associations proposent des activités gratuites ou à prix très réduit",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux comprendre les règles de vie en Suisse",
                'description': "Je veux connaître les habitudes et les règles du quotidien à Neuchâtel pour bien m'entendre avec mes voisins.",
                'tags': ['Integration', 'Vie sociale', 'Culture'],
                'audiences': ['Nouveaux arrivants'],
                'body': body(
                    sec("Règles de bon voisinage",
                        ul(
                            "<b>Bruit :</b> après 22h, le silence est exigé. Évitez aussi le bruit le dimanche toute la journée.",
                            "<b>Buanderie commune :</b> respectez les horaires affichés — c'est pris très au sérieux",
                            "<b>Poubelles :</b> chaque commune a ses règles de tri. Renseignez-vous dès l'arrivée.",
                            "<b>Cave et débarras :</b> ne laissez pas d'affaires dans les parties communes sans autorisation",
                        ),
                    ),
                    sec("Vie quotidienne",
                        ul(
                            "<b>Magasins :</b> fermés le dimanche (sauf gares et certains centres commerciaux)",
                            "<b>Ponctualité :</b> très importante — arrivez à l'heure aux rendez-vous",
                            "<b>Saluer :</b> dites bonjour à vos voisins dans l'ascenseur et les couloirs",
                            "<b>Chaussures :</b> beaucoup de Suisses enlèvent leurs chaussures en entrant — attendez qu'on vous le propose",
                        ),
                    ),
                    sec("Jours fériés à Neuchâtel", ul(
                        "1er janvier (Nouvel An), Vendredi saint, Lundi de Pâques",
                        "1er mai (Fête du travail), Ascension, Lundi de Pentecôte",
                        "1er août (Fête nationale suisse), 25 décembre (Noël)",
                        "<b>Spécifique NE :</b> 26 décembre (Saint-Étienne) et quelques fêtes locales",
                    ), width='full'),
                ),
            },

            {
                'name': "Je ne parle pas encore le français, j'ai besoin d'un interprète",
                'description': "Un interprète communautaire peut m'accompagner à mes rendez-vous médicaux, scolaires ou administratifs.",
                'tags': ['Interprete', 'Traduction disponible', 'Multilingue', 'Integration', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Qu'est-ce qu'un interprète communautaire",
                        para("C'est une personne formée qui traduit pour vous lors de vos rendez-vous médicaux, scolaires ou administratifs. Ce n'est pas simplement un traducteur — il connaît aussi les différences culturelles."),
                    ),
                    sec("Comment en demander un", ul(
                        "<b>COSM :</b> le premier contact — 032 889 74 42 — ils coordonnent les interprètes pour tout le canton",
                        "<b>HNE :</b> l'hôpital dispose d'un service d'interprétariat — demandez lors de la prise de RDV",
                        "<b>Écoles :</b> le COSM peut envoyer un interprète pour les réunions parents-enseignants",
                        "<b>SMIG :</b> un interprète est prévu pour certains rendez-vous officiels",
                    ), width='half'),
                    sec("Plateformes en ligne", ul(
                        "<b>Ensemble-ne.ch :</b> informations officielles en 18 langues — <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>",
                        "<b>ch.ch :</b> guide officiel suisse en plusieurs langues — <a href='https://www.ch.ch' target='_blank'>ch.ch</a>",
                        "<b>Traduction de documents :</b> demandez au COSM pour les documents officiels",
                        "Google Translate peut aider pour les documents simples — mais évitez-le pour les contrats importants",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux apprendre à utiliser un ordinateur ou Internet",
                'description': "Des cours gratuits existent à Neuchâtel pour apprendre les bases de l'informatique et faire des démarches en ligne.",
                'tags': ['Formation', 'E-learning', 'Integration', 'Gratuit', 'En personne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Senior'],
                'body': body(
                    sec("Pourquoi c'est important",
                        para("En Suisse, beaucoup de démarches se font en ligne : s'inscrire au chômage, payer ses factures, remplir sa déclaration d'impôts. Maîtriser les bases de l'informatique facilite énormément la vie."),
                    ),
                    sec("Cours disponibles à Neuchâtel", ul(
                        "<b>COSM :</b> cours d'informatique pour migrants — 032 889 74 42 — renseignez-vous sur les sessions en cours",
                        "<b>Bibliothèques :</b> initiations gratuites à l'informatique — Bibliothèque publique de Neuchâtel — 032 717 69 60",
                        "<b>Croix-Rouge NE :</b> ateliers numériques ponctuels — <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Caritas NE :</b> bénévoles disponibles pour aider — 032 886 80 70",
                    ), width='half'),
                    sec("Ressources gratuites en ligne", ul(
                        "<b>Clé Numérique :</b> cours en ligne gratuits en français — <a href='https://cle-numerique.ch' target='_blank'>cle-numerique.ch</a>",
                        "<b>OpenClassrooms :</b> formation gratuite — <a href='https://openclassrooms.com' target='_blank'>openclassrooms.com</a>",
                        "<b>France Numérique :</b> tutoriels simples — <a href='https://www.numerique.gouv.fr' target='_blank'>numerique.gouv.fr</a>",
                    ), width='half'),
                ),
            },

        ],
    },

    # -----------------------------------------------------------------------
    {
        'name': 'Mobility',
        'description': 'Transports publics, échange de permis de conduire et mobilité quotidienne.',
        'icon': 'TruckIcon',
        'priority': 4,
        'audiences': [],
        'resources': [

            {
                'name': "Je veux utiliser les transports en commun",
                'description': "Je veux savoir comment me déplacer en train et en bus dans le canton de Neuchâtel et économiser sur mes trajets.",
                'tags': ['Transports publics', 'Mobilite', 'Budget', 'Multilingue', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
                'body': body(
                    sec("Les réseaux à Neuchâtel",
                        ul(
                            "<b>CFF :</b> trains entre les villes — <a href='https://www.cff.ch' target='_blank'>cff.ch</a> ou application CFF Mobile",
                            "<b>TRN (Transports Régionaux Neuchâtelois) :</b> bus dans le canton — <a href='https://www.trn.ch' target='_blank'>trn.ch</a>",
                            "<b>TRAVYS :</b> région Yverdon–Val-de-Travers",
                            "<b>CarPostal :</b> cars jaunes pour les villages — <a href='https://www.postauto.ch' target='_blank'>postauto.ch</a>",
                        ),
                    ),
                    sec("Économiser",
                        ul(
                            "<b>Demi-tarif CFF :</b> CHF 185/an — réduit tous vos billets de 50 %",
                            "<b>Abonnement général :</b> voyages illimités sur tout le réseau — environ CHF 3 860/an (2e classe)",
                            "<b>SwissPass :</b> regroupe tous vos abonnements — <a href='https://www.swisspass.ch' target='_blank'>swisspass.ch</a>",
                            "<b>Enfants de moins de 6 ans :</b> gratuits",
                            "<b>Abonnement régional NE :</b> renseignez-vous auprès de TRN pour les tarifs locaux",
                        ),
                    ),
                ),
            },

            {
                'name': "Je veux échanger mon permis de conduire étranger",
                'description': "Je dois échanger mon permis contre un permis suisse dans les 12 mois après mon arrivée. Voici comment faire à Neuchâtel.",
                'tags': ['Permis de conduire', 'Mobilite', 'Formulaire', 'En personne', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Ce que vous devez savoir",
                        ul(
                            "Vous avez <b>12 mois</b> dès votre arrivée pour conduire avec votre permis étranger",
                            "Après 12 mois, vous devez l'échanger contre un permis suisse",
                            "Pays UE/AELE et certains autres : échange direct sans examen",
                            "Autres pays : examen pratique souvent requis",
                        ),
                    ),
                    sec("Comment faire",
                        ol(
                            "Allez au Service des automobiles et de la navigation de Neuchâtel (SAN)",
                            "Apportez : permis de conduire original + traduction si nécessaire, passeport, permis de séjour, photos d'identité",
                            "Payez les frais d'échange",
                            "Si examen requis : inscrivez-vous dans une auto-école",
                        ),
                    ),
                    sec("SAN Neuchâtel", ul(
                        "<b>Adresse :</b> Chemin de la Vuarpillière 29, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 67 67",
                        "<b>Site :</b> <a href='https://www.ne.ch/san' target='_blank'>ne.ch/san</a>",
                        "<b>Sur rendez-vous uniquement</b>",
                        "<b>Pays avec échange direct :</b> <a href='https://www.ch.ch/permis-conduire' target='_blank'>ch.ch/permis-conduire</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux me déplacer à vélo à Neuchâtel",
                'description': "Neuchâtel est une ville cyclable. Je veux connaître les pistes, les vélos partagés et les règles à respecter.",
                'tags': ['Velo', 'Mobilite', 'Gratuit', 'Budget'],
                'audiences': ['Nouveaux arrivants', 'Jeune adulte'],
                'body': body(
                    sec("Pourquoi le vélo",
                        para("Neuchâtel est une ville cyclable. Le vélo est rapide, gratuit et bon pour la santé. Plusieurs pistes cyclables relient les quartiers et les communes du lac."),
                    ),
                    sec("PubliBike — vélos partagés", ul(
                        "<b>Comment ça marche :</b> louez un vélo (normal ou électrique) à la station, rendez-le n'importe où",
                        "<b>Prix :</b> CHF 3/30 min (vélo normal), CHF 5/30 min (e-bike) — abonnement annuel disponible",
                        "<b>App :</b> téléchargez 'PubliBike' — <a href='https://www.publibike.ch' target='_blank'>publibike.ch</a>",
                        "<b>Stations :</b> gare, centre-ville, quartiers principaux de Neuchâtel",
                    ), width='half'),
                    sec("Règles et sécurité", ul(
                        "<b>Casque :</b> obligatoire pour les e-bikes, fortement recommandé pour tous",
                        "<b>Lumières :</b> obligatoires de nuit",
                        "<b>Alcool :</b> limite légale à 0,5‰ — même à vélo",
                        "<b>Cartes des pistes :</b> <a href='https://www.schweizmobil.ch' target='_blank'>schweizmobil.ch</a>",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai du mal à me déplacer pour mes rendez-vous médicaux",
                'description': "Si je ne peux pas me déplacer seul pour aller chez le médecin, il existe des solutions à Neuchâtel.",
                'tags': ['Transport medical', 'Sante', 'Mobilite', 'Assurance maladie', 'Senior'],
                'audiences': ['Senior', "Demandeur d'asile", 'Nouveaux arrivants'],
                'body': body(
                    sec("Qui a droit au transport médical remboursé",
                        ul(
                            "Les personnes qui ne peuvent pas se déplacer seules pour raison médicale",
                            "Sur prescription de votre médecin — demandez une ordonnance",
                            "La LAMal rembourse le transport si la distance est supérieure à 25 km ou si un transport médicalement justifié",
                            "Demandez l'accord de votre caisse maladie avant le transport si possible",
                        ),
                    ),
                    sec("Options disponibles à Neuchâtel", ul(
                        "<b>Taxi médical :</b> prenez rendez-vous avec un taxi agréé — présentez votre ordonnance médicale",
                        "<b>Ambulance non urgente :</b> pour les soins planifiés — contactez votre médecin",
                        "<b>Bénévoles Croix-Rouge NE :</b> accompagnement bénévole à vos RDV médicaux — 032 913 77 77",
                        "<b>Pro Senectute NE :</b> aide à la mobilité pour les seniors — 032 722 07 90",
                    ), width='half'),
                    sec("En cas d'urgence", ul(
                        "<b>Ambulance :</b> 144 — gratuit, 24h/24",
                        "Le transport d'urgence est toujours remboursé par la LAMal",
                        "Gardez votre carte d'assuré LAMal toujours avec vous",
                    ), width='half'),
                ),
            },

            {
                'name': "J'ai une voiture, que dois-je faire en Suisse ?",
                'description': "Je veux savoir comment assurer ma voiture, l'immatriculer et passer le contrôle technique à Neuchâtel.",
                'tags': ['Permis de conduire', 'Mobilite', 'Documents officiels', 'Formulaire', 'Budget'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an"],
                'body': body(
                    sec("Assurance RC (responsabilité civile)",
                        para("En Suisse, l'assurance RC est <b>obligatoire</b> pour tout véhicule. Sans assurance RC, votre voiture ne peut pas circuler ni être immatriculée."),
                        ul(
                            "Couvre les dommages que vous causez à d'autres personnes ou véhicules",
                            "<b>Casco partielle :</b> couvre aussi vol, bris de glace, catastrophes naturelles",
                            "<b>Casco complète :</b> couvre en plus les dommages à votre propre véhicule",
                            "<b>Comparer :</b> <a href='https://www.comparis.ch/assurances-auto' target='_blank'>comparis.ch/assurances-auto</a>",
                        ),
                    ),
                    sec("Immatriculation et plaques NE", ul(
                        "<b>SAN Neuchâtel :</b> Chemin de la Vuarpillière 29, 2000 Neuchâtel — 032 889 67 67",
                        "<b>Documents :</b> permis de conduire, permis de séjour, attestation d'assurance RC, certificat d'origine du véhicule",
                        "<b>Contrôle technique :</b> obligatoire à l'immatriculation, puis tous les 2 ou 4 ans",
                        "<b>Site :</b> <a href='https://www.ne.ch/san' target='_blank'>ne.ch/san</a>",
                    ), width='full'),
                ),
            },

        ],
    },

]


# ---------------------------------------------------------------------------
# Sous-catégories par catégorie
# ---------------------------------------------------------------------------

SUBCATEGORIES = {
    'Work': [
        {'name': 'Chercher un emploi', 'order': 1},
        {'name': 'Droits et salaire', 'order': 2},
        {'name': 'Se former', 'order': 3},
    ],
    'Health': [
        {'name': 'Assurance maladie', 'order': 1},
        {'name': 'Trouver des soins', 'order': 2},
        {'name': 'Santé et bien-être', 'order': 3},
    ],
    'Money & budget': [
        {'name': 'Aides et allocations', 'order': 1},
        {'name': 'Gérer mes finances', 'order': 2},
    ],
    'Education': [
        {'name': 'Apprendre le français', 'order': 1},
        {'name': 'Formation et diplômes', 'order': 2},
    ],
    'Children & family': [
        {'name': 'Scolarité et garde', 'order': 1},
        {'name': 'Aides et droits', 'order': 2},
    ],
    'Rights & duties': [
        {'name': 'Permis et séjour', 'order': 1},
        {'name': 'Droits et protection', 'order': 2},
    ],
    'Housing': [
        {'name': 'Trouver un logement', 'order': 1},
        {'name': 'Droits du locataire', 'order': 2},
    ],
    'Mobility': [
        {'name': 'Transports', 'order': 1},
        {'name': 'Conduire', 'order': 2},
    ],
}

# resource name → subcategory name (None = no subcategory)
RESOURCE_SUBCATEGORY = {
    # Work
    "Je cherche un travail saisonnier ou en agriculture": "Chercher un emploi",
    "Je cherche du travail, par où commencer ?": "Chercher un emploi",
    "Je veux préparer un CV pour trouver du travail en Suisse": "Chercher un emploi",
    "Je veux trouver du travail rapidement via une agence": "Chercher un emploi",
    "Je ne sais pas quel métier choisir en Suisse": "Chercher un emploi",
    "Je veux utiliser LinkedIn pour trouver du travail": "Chercher un emploi",
    "Je veux faire du bénévolat pour avoir une première expérience": "Chercher un emploi",
    "Je veux connaître mes droits en tant qu'employé": "Droits et salaire",
    "Je ne sais pas si je suis payé correctement": "Droits et salaire",
    "Je veux me former ou changer de métier": "Se former",
    "Je veux travailler à mon compte en Suisse": "Se former",
    # Health
    "Je suis malade mais mon médecin n'est pas disponible": "Trouver des soins",
    "Je dois m'assurer contre la maladie": "Assurance maladie",
    "Je veux payer moins cher mon assurance maladie": "Assurance maladie",
    "Je cherche un médecin de famille": "Trouver des soins",
    "J'ai besoin d'aide médicale en urgence": "Trouver des soins",
    "J'ai besoin de soins dentaires": "Trouver des soins",
    "Je veux me faire vacciner": "Trouver des soins",
    "Je me sens mal et j'ai besoin d'aide psychologique": "Santé et bien-être",
    "Je suis enceinte, que dois-je faire ?": "Santé et bien-être",
    "Je cherche des informations sur la contraception ou les IST": "Santé et bien-être",
    "J'ai un handicap ou une maladie grave, quelles aides existent ?": "Santé et bien-être",
    "J'ai des problèmes avec l'alcool, les drogues ou le jeu": "Santé et bien-être",
    # Money & budget
    "J'ai reçu un acte de poursuite, que faire ?": "Gérer mes finances",
    "Je n'ai pas assez d'argent pour vivre": "Aides et allocations",
    "J'ai perdu mon emploi et je veux toucher le chômage": "Aides et allocations",
    "Ma rente ne suffit pas pour vivre": "Aides et allocations",
    "Je n'ai pas assez à manger": "Aides et allocations",
    "Je veux ouvrir un compte bancaire": "Gérer mes finances",
    "Je ne comprends pas comment fonctionnent les impôts": "Gérer mes finances",
    "Je veux comprendre la retraite en Suisse": "Gérer mes finances",
    "J'ai des dettes et je ne sais plus quoi faire": "Gérer mes finances",
    "Je veux mieux gérer mon argent": "Gérer mes finances",
    # Education
    "Je veux apprendre le français": "Apprendre le français",
    "Je veux apprendre le français depuis chez moi": "Apprendre le français",
    "Je veux certifier mon niveau de français": "Apprendre le français",
    "Je veux savoir si l'État peut payer mes cours de langue": "Apprendre le français",
    "Je ne sais pas encore lire ni écrire": "Apprendre le français",
    "Je cherche des cours de langue avec des horaires flexibles": "Apprendre le français",
    "Je veux faire reconnaître mon diplôme étranger en Suisse": "Formation et diplômes",
    "Je veux obtenir un diplôme professionnel suisse": "Formation et diplômes",
    "Je veux me former en ligne pour améliorer mes compétences": "Formation et diplômes",
    "Je veux étudier à l'université à Neuchâtel": "Formation et diplômes",
    # Children & family
    "Je cherche des activités pour mes enfants pendant les vacances": "Scolarité et garde",
    "Je veux inscrire mon enfant à l'école": "Scolarité et garde",
    "Je cherche une place en crèche pour mon enfant": "Scolarité et garde",
    "Mon enfant a besoin d'aide pour apprendre le français à l'école": "Scolarité et garde",
    "Je cherche une garde pour mes enfants avant ou après l'école": "Scolarité et garde",
    "Je veux recevoir les allocations pour mes enfants": "Aides et droits",
    "Je veux connaître mes droits lors d'une naissance": "Aides et droits",
    "Je subis des violences à la maison": "Aides et droits",
    # Rights & duties
    "Je dois obtenir un document d'état civil (acte de naissance, mariage)": "Permis et séjour",
    "Je ne comprends pas les différents permis de séjour": "Permis et séjour",
    "Je veux comprendre la procédure d'asile": "Permis et séjour",
    "Je veux faire venir ma famille en Suisse": "Permis et séjour",
    "Je veux devenir citoyen suisse": "Permis et séjour",
    "Je veux passer du permis B au permis C": "Permis et séjour",
    "Je divorce, est-ce que ça change mon droit de séjour ?": "Permis et séjour",
    "Je viens d'arriver, je dois m'inscrire à ma commune": "Permis et séjour",
    "J'ai besoin d'aide juridique gratuite": "Droits et protection",
    "Je veux voter aux élections à Neuchâtel": "Droits et protection",
    "J'ai été victime de discrimination": "Droits et protection",
    # Housing
    "Je n'ai pas de logement, j'ai besoin d'aide": "Trouver un logement",
    "Je cherche un appartement à louer": "Trouver un logement",
    "Je cherche un logement à loyer réduit": "Trouver un logement",
    "Je veux connaître mes droits en tant que locataire": "Droits du locataire",
    "Je ne comprends pas le dépôt de garantie": "Droits du locataire",
    "Je dois prendre une assurance pour mon appartement": "Droits du locataire",
    # Mobility
    "Je veux utiliser les transports en commun": "Transports",
    "Je veux me déplacer à vélo à Neuchâtel": "Transports",
    "J'ai du mal à me déplacer pour mes rendez-vous médicaux": "Transports",
    "Je veux échanger mon permis de conduire étranger": "Conduire",
    "J'ai une voiture, que dois-je faire en Suisse ?": "Conduire",
}


# ---------------------------------------------------------------------------
# Commande Django
# ---------------------------------------------------------------------------

class Command(BaseCommand):
    help = 'Seed the database with Swiss migration resources for Neuchâtel.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete all existing data before seeding.')

    def handle(self, *_args, **options):
        if options['reset']:
            Resource.objects.all().delete()
            Subcategory.objects.all().delete()
            Category.objects.all().delete()
            Audience.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write('  Données existantes supprimées.')

        # -- Tags --
        self.stdout.write('\nCréation des tags...')
        tag_map = {}
        for label in TAGS:
            tag, created = Tag.objects.get_or_create(label=label)
            tag_map[label] = tag
            if created:
                self.stdout.write(f'  + Tag: {label}')

        # -- Audiences --
        self.stdout.write('\nCréation des audiences...')
        audience_map = {}
        for aud_data in AUDIENCES:
            rel_tags = aud_data.pop('relevant_tags')
            aud, created = Audience.objects.get_or_create(
                name=aud_data['name'], defaults=aud_data,
            )
            if not created:
                for field, value in aud_data.items():
                    setattr(aud, field, value)
                aud.save()
            aud.relevant_tags.set([tag_map[t] for t in rel_tags if t in tag_map])
            audience_map[aud.name] = aud
            self.stdout.write(f'  {"+" if created else "~"} Audience: {aud.name}')

        # -- Catégories + Sous-catégories + Ressources --
        self.stdout.write('\nCréation des catégories et ressources...')
        for cat_data in CATEGORIES:
            cat_audience_names = cat_data.pop('audiences')
            resources_data = cat_data.pop('resources')

            cat, created = Category.objects.get_or_create(
                name=cat_data['name'], defaults=cat_data,
            )
            if not created:
                for field, value in cat_data.items():
                    setattr(cat, field, value)
                cat.save()
            cat.audiences.set([audience_map[n] for n in cat_audience_names if n in audience_map])
            self.stdout.write(f'  {"+" if created else "~"} Category: {cat.name}')

            # Sous-catégories
            subcat_map = {}
            for sc_data in SUBCATEGORIES.get(cat.name, []):
                sc, sc_created = Subcategory.objects.get_or_create(
                    category=cat, name=sc_data['name'],
                    defaults={'order': sc_data['order']},
                )
                if not sc_created:
                    sc.order = sc_data['order']
                    sc.save(update_fields=['order'])
                subcat_map[sc.name] = sc
                self.stdout.write(f'    {"+" if sc_created else "~"} Subcategory: {sc.name}')

            for res_data in resources_data:
                tag_labels = res_data.pop('tags')
                res_audience_names = res_data.pop('audiences')
                body_data = res_data.pop('body', None)

                res, res_created = Resource.objects.get_or_create(
                    name=res_data['name'], category=cat,
                    defaults={k: v for k, v in res_data.items() if k != 'name'},
                )
                if not res_created:
                    res.description = res_data.get('description', res.description)
                    res.save(update_fields=['description'])

                res.tags.set([tag_map[t] for t in tag_labels if t in tag_map])
                res.audiences.set([audience_map[n] for n in res_audience_names if n in audience_map])

                subcat_name = RESOURCE_SUBCATEGORY.get(res.name)
                res.subcategory = subcat_map.get(subcat_name)
                res.save(update_fields=['subcategory'])

                if body_data:
                    res.body = body_data
                    res.save(update_fields=['body'])
                elif not res.body or not res.body.get('sections'):
                    res.body = {'sections': [
                        {'title': 'Contenu', 'body': {'blocks': [
                            {'type': 'paragraph', 'data': {'text': res.description}},
                        ]}},
                    ]}
                    res.save(update_fields=['body'])

                self.stdout.write(f'      {"+" if res_created else "~"} {res.name}')

        self.stdout.write(self.style.SUCCESS('\nSeed terminé.'))
