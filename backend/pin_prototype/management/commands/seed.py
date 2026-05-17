"""
Seed command — realistic data for the PIN prototype.

Usage:
    python manage.py seed            # additive (get_or_create)
    python manage.py seed --reset    # wipe categories/resources/audiences/tags first
"""

from django.core.management.base import BaseCommand
from pin_prototype.models import Audience, Category, Tag, Resource

SAMPLE_FILE = 'resources/sample.pdf'

# ---------------------------------------------------------------------------
# Tags — granular taxonomy (75 tags) for accurate similarity matching
# ---------------------------------------------------------------------------

TAGS = [
    # --- Format / accès ---
    'Formulaire', 'En personne', 'En ligne', 'Hotline',
    'Gratuit', 'Urgence', 'Traduction disponible', 'Interprete', 'Multilingue',
    # --- Logement ---
    'Logement', 'Logement urgence', 'Logement social',
    'Droits du locataire', 'Bail', 'Depot de garantie', 'Assurance menage',
    # --- Santé ---
    'Sante', 'Sante mentale', 'Medecin', 'Assurance maladie',
    'Reduction de prime', 'Maternite', 'Handicap', 'Vaccination',
    # --- Travail ---
    'Travail', 'Recherche emploi', 'Droit du travail',
    'Salaire', 'Independent', 'Chomage', 'CV candidature',
    # --- Formation ---
    'Formation', 'Apprentissage', 'Universite',
    'Langue', 'Cours de langue', 'Reconnaissance diplome', 'E-learning',
    # --- Droits & documents ---
    'Droits', 'Documents officiels', 'Permis sejour',
    'Naturalisation', 'Asile', 'Aide juridique', 'Regroupement familial', 'Discrimination',
    # --- Budget & aides ---
    'Budget', 'Aide sociale', 'Allocation', 'Subvention',
    'Impots', 'Banque', 'Alimentation',
    # --- Mobilité ---
    'Mobilite', 'Transports publics', 'Permis de conduire', 'Velo', 'Transport medical',
    # --- Famille & enfants ---
    'Famille', 'Enfants', 'Garde enfants', 'Scolarisation',
    'Allocations familiales', 'Soutien scolaire', 'Droits parentaux',
    # --- Profils spécifiques ---
    'Femmes', 'Jeune', 'Senior',
    'Permis N/F/S', 'Permis B', 'Permis C', 'Permis G',
    # --- Intégration & vie sociale ---
    'Integration', 'Vie sociale', 'Benevol', 'Culture',
]

# ---------------------------------------------------------------------------
# Audiences
# ---------------------------------------------------------------------------

AUDIENCES = [
    {
        'name': "Demandeur d'asile",
        'description': "Titulaires d'un permis N, F ou S.",
        'statuses': 'N,F,S', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Permis N/F/S', 'Asile', 'Droits', 'Aide sociale', 'Urgence', 'Logement urgence', 'Interprete'],
    },
    {
        'name': 'Parents',
        'description': "Personnes ayant des enfants à charge.",
        'statuses': '', 'has_children': True, 'origin_sectors': '',
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Garde enfants', 'Enfants', 'Famille', 'Scolarisation', 'Allocations familiales', 'Soutien scolaire'],
    },
    {
        'name': 'Nouveaux arrivants',
        'description': "Arrivés en Suisse depuis moins d'un an.",
        'statuses': '', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': False, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Logement', 'Integration', 'Langue', 'Cours de langue', 'Documents officiels', 'Assurance maladie', 'Banque'],
    },
    {
        'name': "Établis depuis plus d'un an",
        'description': "En phase d'intégration avancée.",
        'statuses': '', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': True, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Formation', 'Travail', 'Reconnaissance diplome', 'Integration', 'Naturalisation'],
    },
    {
        'name': 'Résident long terme',
        'description': "Titulaires d'un permis B ou C.",
        'statuses': 'B,C', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Permis B', 'Permis C', 'Droits', 'Travail', 'Naturalisation', 'Impots'],
    },
    {
        'name': 'Frontalier',
        'description': "Titulaires d'un permis G.",
        'statuses': 'G', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Permis G', 'Mobilite', 'Travail', 'Droit du travail', 'Impots'],
    },
    {
        'name': 'Jeune adulte',
        'description': "18 à 30 ans.",
        'statuses': '', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': None, 'min_age': 18, 'max_age': 30,
        'relevant_tags': ['Formation', 'Jeune', 'Cours de langue', 'Apprentissage', 'Universite', 'CV candidature', 'Recherche emploi'],
    },
    {
        'name': 'Senior',
        'description': "60 ans et plus.",
        'statuses': '', 'has_children': None, 'origin_sectors': '',
        'arrived_over_year': None, 'min_age': 60, 'max_age': None,
        'relevant_tags': ['Senior', 'Sante', 'Mobilite', 'Transport medical', 'Aide sociale', 'Handicap'],
    },
    {
        'name': 'Professionnel de santé',
        'description': "Ayant travaillé dans le secteur de la santé.",
        'statuses': '', 'has_children': None, 'origin_sectors': 'healthcare',
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Reconnaissance diplome', 'Travail', 'Formation', 'Sante', 'Documents officiels'],
    },
    {
        'name': 'Travailleur qualifié',
        'description': "Ingénierie, IT, administration, éducation.",
        'statuses': '', 'has_children': None,
        'origin_sectors': 'engineering,it,administration,education',
        'arrived_over_year': None, 'min_age': None, 'max_age': None,
        'relevant_tags': ['Reconnaissance diplome', 'Travail', 'Formation', 'CV candidature', 'E-learning', 'Independent'],
    },
]

# ---------------------------------------------------------------------------
# Categories + Resources
# audiences: audiences ciblées par la ressource (vide = générique, jamais "recommandé")
# tags: 4-6 tags contenu/profil pour la similarité feedback
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        'name': 'Money & budget',
        'description': 'Aides financières, assistance sociale, banque et gestion du budget en Suisse.',
        'icon': 'CurrencyDollarIcon',
        'priority': 10,
        'audiences': [],
        'resources': [
            {
                'name': "Guide des aides financières pour primo-arrivants",
                'description': "Vue d'ensemble des aides disponibles : aide sociale, subsides, allocations et épiceries sociales.",
                'tags': ['Aide sociale', 'Budget', 'Allocation', 'Subvention', 'Multilingue', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Demande d'aide sociale d'urgence",
                'description': "Formulaire de demande d'aide financière d'urgence auprès de votre commune.",
                'tags': ['Formulaire', 'En personne', 'Urgence', 'Aide sociale', 'Traduction disponible'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Ouvrir un compte bancaire en Suisse",
                'description': "Quelle banque choisir, quels documents apporter, comptes spéciaux pour permis N/F.",
                'tags': ['Banque', 'Budget', 'Documents officiels', 'En personne', 'Multilingue'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Demande de subvention au loyer",
                'description': "Comment demander une aide au logement auprès des services sociaux cantonaux.",
                'tags': ['Formulaire', 'Logement', 'Subvention', 'Aide sociale', 'Budget'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Comprendre sa feuille de salaire suisse",
                'description': "Cotisations AVS, LPP, chômage, déductions et net à payer — explication complète.",
                'tags': ['Travail', 'Salaire', 'Budget', 'En ligne', 'Multilingue'],
                'audiences': ["Établis depuis plus d'un an", 'Résident long terme', 'Frontalier'],
            },
            {
                'name': "Guide de la fiscalité pour résidents étrangers",
                'description': "Imposition à la source, déclaration fiscale, délais et déductions possibles.",
                'tags': ['Impots', 'Documents officiels', 'Formulaire', 'En ligne', 'Budget'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an", 'Frontalier'],
            },
            {
                'name': "Épiceries sociales et banques alimentaires",
                'description': "Adresses, horaires et conditions d'accès aux épiceries à prix solidaires.",
                'tags': ['Gratuit', 'En personne', 'Aide sociale', 'Alimentation', 'Urgence'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Comprendre les allocations chômage (LACI)",
                'description': "Conditions, montant, durée et démarches pour percevoir les indemnités de chômage.",
                'tags': ['Chomage', 'Allocation', 'Budget', 'Travail', 'Formulaire', 'Droits'],
                'audiences': ["Établis depuis plus d'un an", 'Résident long terme', 'Frontalier'],
            },
            {
                'name': "Aide d'urgence — solution de dernier recours",
                'description': "Aide en espèces ou en nature pour personnes déboutées ou sans ressources.",
                'tags': ['Aide sociale', 'Urgence', 'Budget', 'Gratuit', 'En personne', 'Permis N/F/S'],
                'audiences': ["Demandeur d'asile"],
            },
            {
                'name': "Comparatif des banques accessibles aux migrants",
                'description': "Neobanques, banques postales et comptes basiques ouverts sans conditions strictes.",
                'tags': ['Banque', 'Budget', 'En ligne', 'Multilingue', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
        ],
    },
    {
        'name': 'Children & family',
        'description': 'Garde, allocations, scolarisation et droits parentaux.',
        'icon': 'UsersIcon',
        'priority': 6,
        'audiences': ['Parents'],
        'resources': [
            {
                'name': "Inscription à la crèche et à la garderie",
                'description': "Démarches pour inscrire votre enfant dans une structure agréée, listes d'attente et coûts.",
                'tags': ['Garde enfants', 'Enfants', 'Formulaire', 'En personne', 'Budget'],
                'audiences': ['Parents'],
            },
            {
                'name': "Demande d'allocations familiales",
                'description': "Formulaire et conditions pour obtenir les allocations familiales cantonales.",
                'tags': ['Allocations familiales', 'Enfants', 'Formulaire', 'Budget', 'Aide sociale'],
                'audiences': ['Parents'],
            },
            {
                'name': "Aide à la garde — subventionnement cantonal",
                'description': "Comment bénéficier d'une réduction sur les frais de garde selon vos revenus.",
                'tags': ['Garde enfants', 'Enfants', 'Subvention', 'Budget', 'Formulaire'],
                'audiences': ['Parents'],
            },
            {
                'name': "Scolariser son enfant en Suisse",
                'description': "Fonctionnement de l'école publique, inscription, calendrier et fournitures scolaires.",
                'tags': ['Enfants', 'Scolarisation', 'Integration', 'Gratuit', 'Formulaire'],
                'audiences': ['Parents', 'Nouveaux arrivants'],
            },
            {
                'name': "Soutien scolaire pour enfants allophones",
                'description': "Classes d'accueil, cours de rattrapage et ressources pour enfants non-francophones.",
                'tags': ['Enfants', 'Soutien scolaire', 'Cours de langue', 'Langue', 'Gratuit', 'Integration'],
                'audiences': ['Parents', 'Nouveaux arrivants'],
            },
            {
                'name': "Droits parentaux : congé maternité et paternité",
                'description': "Durée, montants et démarches pour les congés parentaux en Suisse.",
                'tags': ['Droits parentaux', 'Famille', 'Travail', 'Droits', 'Documents officiels'],
                'audiences': ['Parents', 'Résident long terme'],
            },
            {
                'name': "Médiation scolaire et conflits à l'école",
                'description': "Rôle du médiateur scolaire, comment signaler un problème et vos droits.",
                'tags': ['Enfants', 'Scolarisation', 'Droits', 'En personne', 'Gratuit'],
                'audiences': ['Parents'],
            },
            {
                'name': "Activités et loisirs pour enfants de migrants",
                'description': "Clubs sportifs, maisons de quartier, activités culturelles à prix réduit ou gratuit.",
                'tags': ['Enfants', 'Integration', 'Vie sociale', 'Culture', 'Gratuit'],
                'audiences': ['Parents'],
            },
            {
                'name': "Santé de l'enfant : vaccins et suivi pédiatrique",
                'description': "Carnet de vaccination, pédiatres acceptant de nouveaux patients, consultations gratuites.",
                'tags': ['Enfants', 'Sante', 'Vaccination', 'Assurance maladie', 'Medecin'],
                'audiences': ['Parents'],
            },
        ],
    },
    {
        'name': 'Education',
        'description': "Cours de langue, reconnaissance de diplômes, formation professionnelle et e-learning.",
        'icon': 'AcademicCapIcon',
        'priority': 8,
        'audiences': ['Nouveaux arrivants', 'Jeune adulte', "Établis depuis plus d'un an", 'Travailleur qualifié', 'Professionnel de santé'],
        'resources': [
            {
                'name': "Cours de français / allemand / italien gratuits ou subventionnés",
                'description': "Centres de langues, niveaux A1 à C1, conditions d'accès et horaires souples par canton.",
                'tags': ['Cours de langue', 'Langue', 'Gratuit', 'Integration', 'En personne', 'Formation'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Jeune adulte'],
            },
            {
                'name': "Reconnaissance de diplômes étrangers — procédure",
                'description': "Démarches auprès de la CDIP, SEFRI ou des ordres professionnels selon votre domaine.",
                'tags': ['Reconnaissance diplome', 'Documents officiels', 'Formulaire', 'Travail', 'Formation'],
                'audiences': ['Travailleur qualifié', 'Professionnel de santé', "Établis depuis plus d'un an"],
            },
            {
                'name': "Formation professionnelle pour adultes (AFP / CFC)",
                'description': "Comment obtenir une attestation ou un certificat fédéral de capacité en tant qu'adulte.",
                'tags': ['Formation', 'Apprentissage', 'Travail', 'En personne', 'Gratuit'],
                'audiences': ["Établis depuis plus d'un an", 'Jeune adulte'],
            },
            {
                'name': "Accès à l'université pour réfugiés et permis F",
                'description': "Programmes universitaires spécifiques, bourses cantonales et conditions d'admission.",
                'tags': ['Universite', 'Formation', 'Permis N/F/S', 'Subvention', 'Jeune', 'Gratuit'],
                'audiences': ["Demandeur d'asile", 'Jeune adulte'],
            },
            {
                'name': "Validation des acquis de l'expérience (VAE)",
                'description': "Faire reconnaître vos compétences sans formation complète. Bilan de compétences inclus.",
                'tags': ['Reconnaissance diplome', 'Travail', 'Formation', 'Documents officiels'],
                'audiences': ['Travailleur qualifié', 'Professionnel de santé'],
            },
            {
                'name': "Se préparer au marché du travail suisse",
                'description': "CV suisse, lettre de motivation, codes culturels et simulation d'entretien.",
                'tags': ['CV candidature', 'Recherche emploi', 'Travail', 'Formation', 'Integration', 'Gratuit'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Jeune adulte'],
            },
            {
                'name': "Plateformes d'e-learning gratuites pour migrants",
                'description': "Ressources en ligne pour langues nationales, informatique et bases professionnelles.",
                'tags': ['E-learning', 'Gratuit', 'Cours de langue', 'Langue', 'Formation', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Jeune adulte'],
            },
            {
                'name': "Formation continue pour adultes en emploi",
                'description': "Cours du soir, formations certifiantes, financement par l'employeur ou le Canton.",
                'tags': ['Formation', 'Travail', 'En ligne', 'Budget', 'Subvention'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
            },
            {
                'name': "Bilan de compétences pour migrants qualifiés",
                'description': "Évaluation des compétences acquises à l'étranger, orientations et débouchés en Suisse.",
                'tags': ['Reconnaissance diplome', 'Travail', 'CV candidature', 'Formation', 'Gratuit', 'En personne'],
                'audiences': ['Travailleur qualifié', 'Professionnel de santé'],
            },
            {
                'name': "Réseau de mentors professionnels pour migrants",
                'description': "Mise en relation avec un professionnel de votre domaine pour un accompagnement personnalisé.",
                'tags': ['Recherche emploi', 'Travail', 'Integration', 'Gratuit', 'En personne'],
                'audiences': ["Établis depuis plus d'un an", 'Travailleur qualifié'],
            },
        ],
    },
    {
        'name': 'Housing',
        'description': 'Logement urgence, droits du locataire, logement social et astuces de recherche.',
        'icon': 'HomeIcon',
        'priority': 9,
        'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
        'resources': [
            {
                'name': "Trouver un logement d'urgence",
                'description': "Hébergements d'urgence, foyers et hôtels sociaux disponibles dans votre canton.",
                'tags': ['Logement urgence', 'Urgence', 'En personne', 'Gratuit', 'Aide sociale'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Droits du locataire en Suisse",
                'description': "Bail, résiliation, état des lieux, charges locatives — guide complet de vos droits.",
                'tags': ['Droits du locataire', 'Bail', 'Droits', 'Logement', 'Multilingue'],
                'audiences': [],
            },
            {
                'name': "Demande de logement social (HLM / coopératives)",
                'description': "Inscription sur les listes cantonales, conditions de revenus et délais d'attente.",
                'tags': ['Logement social', 'Formulaire', 'Aide sociale', 'Logement', 'Budget'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Signaler une discrimination dans la recherche de logement",
                'description': "Recours possibles, organismes de médiation et preuves à conserver.",
                'tags': ['Discrimination', 'Droits', 'Logement', 'Aide juridique', 'En personne'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Dépôt de garantie — règles et restitution",
                'description': "Montant légal maximum, compte bloqué obligatoire et procédure de remboursement.",
                'tags': ['Depot de garantie', 'Bail', 'Budget', 'Droits du locataire', 'Documents officiels'],
                'audiences': [],
            },
            {
                'name': "Assurance ménage — ce qui est obligatoire",
                'description': "Couvertures exigées par les bailleurs, comparatif et souscription en ligne.",
                'tags': ['Assurance menage', 'Logement', 'Budget', 'En ligne', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants'],
            },
            {
                'name': "Trouver un appartement — plateformes et astuces",
                'description': "Homegate, Immoscout24, groupes locaux et techniques pour se démarquer.",
                'tags': ['Logement', 'En ligne', 'Budget', 'Integration'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Comprendre le contrat de bail suisse",
                'description': "Clauses importantes, durée, sous-location, résiliation anticipée et recours.",
                'tags': ['Bail', 'Droits du locataire', 'Documents officiels', 'Logement', 'Multilingue'],
                'audiences': [],
            },
            {
                'name': "Recours en cas d'expulsion ou résiliation abusive",
                'description': "Délais légaux, autorité de conciliation, aide juridique gratuite pour locataires.",
                'tags': ['Droits du locataire', 'Bail', 'Urgence', 'Aide juridique', 'Droits', 'Gratuit'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
        ],
    },
    {
        'name': 'Rights & duties',
        'description': "Permis de séjour, procédure d'asile, aide juridique et obligations civiques.",
        'icon': 'ScaleIcon',
        'priority': 7,
        'audiences': ["Demandeur d'asile", 'Résident long terme', "Établis depuis plus d'un an"],
        'resources': [
            {
                'name': "Comprendre les permis de séjour (N, F, S, B, C, G)",
                'description': "Droits et restrictions de chaque permis : travail, voyage, regroupement familial.",
                'tags': ['Permis sejour', 'Droits', 'Documents officiels', 'Multilingue', 'Permis N/F/S'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Procédure d'asile en Suisse — guide complet",
                'description': "Étapes de la demande, auditions au SEM, décision et voies de recours disponibles.",
                'tags': ['Asile', 'Permis N/F/S', 'Droits', 'Formulaire', 'Traduction disponible', 'Interprete'],
                'audiences': ["Demandeur d'asile"],
            },
            {
                'name': "Recours contre une décision du SEM",
                'description': "Contester un refus d'asile — délais impératifs, formulaires et aide juridique.",
                'tags': ['Asile', 'Permis N/F/S', 'Droits', 'Formulaire', 'Urgence', 'Aide juridique'],
                'audiences': ["Demandeur d'asile"],
            },
            {
                'name': "Aide juridique gratuite pour migrants",
                'description': "Permanences d'avocats, associations de défense et consultations gratuites.",
                'tags': ['Aide juridique', 'Droits', 'Gratuit', 'En personne', 'Traduction disponible'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Regroupement familial — conditions et formulaire",
                'description': "Qui peut faire venir sa famille, revenus requis, délais et documents à fournir.",
                'tags': ['Regroupement familial', 'Famille', 'Formulaire', 'Documents officiels', 'Permis B', 'Permis C'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
            },
            {
                'name': "Naturalisation — conditions et procédure cantonale",
                'description': "Durée de résidence, test de langue et civisme, frais et démarches par canton.",
                'tags': ['Naturalisation', 'Integration', 'Documents officiels', 'Formulaire', 'Langue'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an"],
            },
            {
                'name': "Obligations civiques : déménagement, registres, impôts",
                'description': "Ce que vous devez déclarer à votre commune : arrivée, départ, changement d'état civil.",
                'tags': ['Documents officiels', 'Impots', 'Formulaire', 'En ligne', 'Droits'],
                'audiences': ['Nouveaux arrivants', 'Résident long terme'],
            },
            {
                'name': "Signaler une discrimination (travail, logement, services)",
                'description': "Vos droits, comment porter plainte et les organismes de lutte contre la discrimination.",
                'tags': ['Discrimination', 'Droits', 'Aide juridique', 'En personne', 'Gratuit'],
                'audiences': [],
            },
            {
                'name': "Droits et obligations du travailleur étranger",
                'description': "Contrat de travail, protection contre le licenciement, droits syndicaux et recours.",
                'tags': ['Droit du travail', 'Travail', 'Droits', 'Salaire', 'Multilingue'],
                'audiences': ['Résident long terme', "Établis depuis plus d'un an", 'Frontalier'],
            },
            {
                'name': "Renouvellement et changement de permis de séjour",
                'description': "Quand déposer la demande, documents requis et risques en cas de retard.",
                'tags': ['Permis sejour', 'Documents officiels', 'Formulaire', 'Droits', 'Urgence'],
                'audiences': ["Établis depuis plus d'un an", 'Résident long terme'],
            },
        ],
    },
    {
        'name': 'Mobility',
        'description': 'Transports publics, échange de permis de conduire, mobilité douce et transport médical.',
        'icon': 'TruckIcon',
        'priority': 4,
        'audiences': [],
        'resources': [
            {
                'name': "Abonnement demi-tarif CFF — comment l'obtenir",
                'description': "50 % de réduction sur tous les billets CFF, CarPostal et bateaux en Suisse.",
                'tags': ['Transports publics', 'Mobilite', 'Budget', 'En ligne'],
                'audiences': [],
            },
            {
                'name': "Échange d'un permis de conduire étranger",
                'description': "Procédure auprès du Service des automobiles, documents requis selon pays d'origine.",
                'tags': ['Permis de conduire', 'Mobilite', 'Formulaire', 'En personne', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an"],
            },
            {
                'name': "Guide des transports publics par canton",
                'description': "Réseaux TPG, VBZ, BVB — tarifs, abonnements, zones et applications officielles.",
                'tags': ['Transports publics', 'Mobilite', 'Budget', 'Multilingue'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "SwissPass — créer son compte et gérer ses abonnements",
                'description': "Tutoriel complet pour rattacher abonnements et acheter des billets en ligne.",
                'tags': ['Transports publics', 'Mobilite', 'En ligne', 'Multilingue'],
                'audiences': [],
            },
            {
                'name': "Transport médical non urgent — prise en charge LAMal",
                'description': "Conditions de remboursement des transports vers médecins et soins spécialisés.",
                'tags': ['Transport medical', 'Sante', 'Assurance maladie', 'Handicap', 'Mobilite'],
                'audiences': ['Senior', "Demandeur d'asile"],
            },
            {
                'name': "Location de vélos et mobilité douce",
                'description': "PubliBike, Velospot, pistes cyclables et aides à l'achat d'un vélo électrique.",
                'tags': ['Velo', 'Mobilite', 'Budget', 'En ligne'],
                'audiences': [],
            },
            {
                'name': "Aides au transport pour personnes en situation de handicap",
                'description': "Abonnements spéciaux AI, véhicules adaptés et services de transport à la demande.",
                'tags': ['Transport medical', 'Handicap', 'Mobilite', 'Aide sociale', 'Formulaire'],
                'audiences': ['Senior'],
            },
            {
                'name': "Covoiturage et alternatives à la voiture personnelle",
                'description': "Blablacar, Communauto, Share Now — réduire ses coûts de transport en Suisse.",
                'tags': ['Mobilite', 'Budget', 'Transports publics', 'En ligne'],
                'audiences': [],
            },
        ],
    },
    {
        'name': 'Health',
        'description': "Assurance maladie, trouver un médecin, santé mentale, vaccins et urgences.",
        'icon': 'HeartIcon',
        'priority': 9,
        'audiences': [],
        'resources': [
            {
                'name': "Choisir sa caisse maladie (LAMal) — comparatif",
                'description': "Comparer primes, franchises et réseaux de soins. Outils officiels de comparaison.",
                'tags': ['Assurance maladie', 'Budget', 'En ligne', 'Multilingue'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Réduction de prime d'assurance maladie (subsides)",
                'description': "Conditions d'accès aux subsides cantonaux, formulaire et délais à respecter.",
                'tags': ['Assurance maladie', 'Reduction de prime', 'Budget', 'Subvention', 'Formulaire', 'Aide sociale'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile", 'Résident long terme'],
            },
            {
                'name': "Trouver un médecin qui parle votre langue",
                'description': "Annuaires multilingues, médiation linguistique et consultation à distance.",
                'tags': ['Medecin', 'Sante', 'Multilingue', 'Traduction disponible', 'En ligne'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Urgences médicales — que faire et où aller",
                'description': "Numéros d'urgence (144), permanences de nuit, gardes médicales cantonales.",
                'tags': ['Sante', 'Urgence', 'Multilingue', 'Gratuit', 'Hotline'],
                'audiences': [],
            },
            {
                'name': "Santé mentale pour migrants — ressources et soutien",
                'description': "Consultations psychologiques adaptées, soutien par les pairs, groupes de parole.",
                'tags': ['Sante mentale', 'Sante', 'Gratuit', 'Traduction disponible', 'En personne', 'Interprete'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
            {
                'name': "Calendrier de vaccination officiel suisse",
                'description': "Vaccins recommandés pour adultes et enfants, rattrapages et centres de vaccination.",
                'tags': ['Vaccination', 'Sante', 'Enfants', 'Gratuit', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants', 'Parents'],
            },
            {
                'name': "Guide de la maternité en Suisse",
                'description': "Suivi de grossesse, sages-femmes, accouchement et prise en charge LAMal.",
                'tags': ['Maternite', 'Sante', 'Assurance maladie', 'Femmes', 'Documents officiels'],
                'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
            },
            {
                'name': "Handicap et accès aux soins — droits et prestations AI",
                'description': "Prestations de l'assurance invalidité, aides techniques et transport médical.",
                'tags': ['Handicap', 'Sante', 'Droits', 'Aide sociale', 'Formulaire', 'Transport medical'],
                'audiences': ['Senior'],
            },
            {
                'name': "Soins dentaires — coûts, prise en charge et centres low-cost",
                'description': "Dentistes universitaires, centres subventionnés et assurances complémentaires.",
                'tags': ['Sante', 'Budget', 'Assurance maladie', 'En ligne', 'Gratuit'],
                'audiences': [],
            },
            {
                'name': "Addictions — ressources d'aide et de prévention pour migrants",
                'description': "Services d'accompagnement anonymes, groupes de soutien et consultations gratuites.",
                'tags': ['Sante mentale', 'Sante', 'Gratuit', 'En personne', 'Traduction disponible'],
                'audiences': ["Demandeur d'asile", 'Nouveaux arrivants'],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with realistic PIN prototype data.'

    def add_arguments(self, parser):
        parser.add_argument('--reset', action='store_true',
                            help='Delete all existing data before seeding.')

    def handle(self, *args, **options):
        if options['reset']:
            Resource.objects.all().delete()
            Category.objects.all().delete()
            Audience.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write('  Existing data cleared.')

        # -- Tags --
        self.stdout.write('\nCreating tags...')
        tag_map = {}
        for label in TAGS:
            tag, created = Tag.objects.get_or_create(label=label)
            tag_map[label] = tag
            if created:
                self.stdout.write(f'  + Tag: {label}')

        # -- Audiences --
        self.stdout.write('\nCreating audiences...')
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

        # -- Categories + Resources --
        self.stdout.write('\nCreating categories and resources...')
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

            for res_data in resources_data:
                tag_labels = res_data.pop('tags')
                res_audience_names = res_data.pop('audiences')
                res, res_created = Resource.objects.get_or_create(
                    name=res_data['name'], category=cat,
                    defaults={**res_data, 'file': SAMPLE_FILE},
                )
                res.tags.set([tag_map[t] for t in tag_labels if t in tag_map])
                res.audiences.set([audience_map[n] for n in res_audience_names if n in audience_map])
                if res_created:
                    self.stdout.write(f'      + {res.name}')

        self.stdout.write(self.style.SUCCESS('\nSeed complete.'))
