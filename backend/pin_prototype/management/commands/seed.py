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
# Tags
# ---------------------------------------------------------------------------

TAGS = [
    # Format / access
    'Formulaire',
    'En personne',
    'En ligne',
    'Gratuit',
    'Urgence',
    'Traduction disponible',
    'Multilingue',
    # Life domains
    'Logement',
    'Santé',
    'Travail',
    'Formation',
    'Droits',
    'Budget',
    'Mobilité',
    'Intégration',
    'Langue',
    # Target groups
    'Enfants',
    'Garde',
    'Famille',
    'Jeune',
    'Senior',
    'Femmes',
    # Permit types
    'Permis N/F/S',
    'Permis B',
    'Permis C',
    'Permis G',
    # Process
    'Documents officiels',
    'Assurance maladie',
    'Aide sociale',
    'Reconnaissance de diplôme',
]

# ---------------------------------------------------------------------------
# Audiences
# Conditions: statuses (comma-sep permit codes), has_children (bool/None),
#             origin_sectors (comma-sep), arrived_over_year (bool/None),
#             min_age / max_age (int/None)
# relevant_tags: list of tag labels whose resources get boosted for this audience
# ---------------------------------------------------------------------------

AUDIENCES = [
    {
        'name': "Demandeur d'asile",
        'description': "Personnes titulaires d'un permis N (requérant d'asile), F (admission provisoire) ou S (protection temporaire).",
        'statuses': 'N,F,S',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': None,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Permis N/F/S', 'Droits', 'Aide sociale', 'Urgence', 'Logement'],
    },
    {
        'name': 'Parents',
        'description': "Personnes ayant des enfants à charge.",
        'statuses': '',
        'has_children': True,
        'origin_sectors': '',
        'arrived_over_year': None,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Garde', 'Enfants', 'Famille', 'Formation'],
    },
    {
        'name': 'Nouveaux arrivants',
        'description': "Personnes arrivées en Suisse depuis moins d'un an.",
        'statuses': '',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': False,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Logement', 'Intégration', 'Langue', 'Documents officiels', 'Assurance maladie'],
    },
    {
        'name': "Établis depuis plus d'un an",
        'description': "Personnes résidant en Suisse depuis plus d'un an, en phase d'intégration avancée.",
        'statuses': '',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': True,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Formation', 'Travail', 'Reconnaissance de diplôme', 'Intégration'],
    },
    {
        'name': 'Résident long terme',
        'description': "Titulaires d'un permis B ou C — résidents stables avec droits élargis.",
        'statuses': 'B,C',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': None,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Permis B', 'Permis C', 'Droits', 'Travail'],
    },
    {
        'name': 'Frontalier',
        'description': "Titulaires d'un permis G — travaillent en Suisse et résident à l'étranger.",
        'statuses': 'G',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': None,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Permis G', 'Mobilité', 'Travail'],
    },
    {
        'name': 'Jeune adulte',
        'description': "Personnes de 18 à 30 ans — accès facilité à certaines formations et aides.",
        'statuses': '',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': None,
        'min_age': 18,
        'max_age': 30,
        'relevant_tags': ['Formation', 'Jeune', 'Langue', 'Travail'],
    },
    {
        'name': 'Senior',
        'description': "Personnes de 60 ans et plus — besoins spécifiques en santé et mobilité.",
        'statuses': '',
        'has_children': None,
        'origin_sectors': '',
        'arrived_over_year': None,
        'min_age': 60,
        'max_age': None,
        'relevant_tags': ['Senior', 'Santé', 'Mobilité', 'Aide sociale'],
    },
    {
        'name': 'Professionnel de santé',
        'description': "Personnes ayant travaillé dans le secteur de la santé dans leur pays d'origine.",
        'statuses': '',
        'has_children': None,
        'origin_sectors': 'healthcare',
        'arrived_over_year': None,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Reconnaissance de diplôme', 'Travail', 'Formation', 'Santé'],
    },
    {
        'name': 'Travailleur qualifié',
        'description': "Personnes issues de secteurs qualifiés (ingénierie, IT, administration, éducation).",
        'statuses': '',
        'has_children': None,
        'origin_sectors': 'engineering,it,administration,education',
        'arrived_over_year': None,
        'min_age': None,
        'max_age': None,
        'relevant_tags': ['Reconnaissance de diplôme', 'Travail', 'Formation', 'En ligne'],
    },
]

# ---------------------------------------------------------------------------
# Categories + Resources
# audiences: list of audience names assigned to the category (empty = universal)
# resources: list of {name, description, tags: [label, ...]}
# ---------------------------------------------------------------------------

CATEGORIES = [
    {
        'name': 'Money & budget',
        'description': 'Financial aid, social assistance, banking, and budget management in Switzerland.',
        'icon': 'CurrencyDollarIcon',
        'priority': 10,
        'audiences': [],  # universal
        'resources': [
            {
                'name': "Guide des aides financières pour primo-arrivants",
                'description': "Vue d'ensemble des aides disponibles : aide sociale, avances sur salaire, épiceries sociales.",
                'tags': ['Aide sociale', 'Budget', 'Gratuit'],
            },
            {
                'name': "Demande d'aide sociale d'urgence",
                'description': "Formulaire de demande d'aide financière d'urgence auprès de votre commune.",
                'tags': ['Formulaire', 'En personne', 'Urgence', 'Aide sociale'],
            },
            {
                'name': "Ouvrir un compte bancaire en Suisse — guide pratique",
                'description': "Quelle banque choisir, quels documents apporter, comment procéder depuis l'étranger.",
                'tags': ['En personne', 'Documents officiels', 'Budget'],
            },
            {
                'name': "Demande de subvention au loyer",
                'description': "Comment demander une aide au logement auprès des services sociaux cantonaux.",
                'tags': ['Formulaire', 'Logement', 'Aide sociale'],
            },
            {
                'name': "Comprendre sa feuille de salaire suisse",
                'description': "Explication des cotisations, des déductions et des droits liés à votre salaire.",
                'tags': ['Travail', 'Budget', 'Multilingue'],
            },
            {
                'name': "Guide de la fiscalité pour résidents étrangers",
                'description': "Imposition à la source, déclaration fiscale, délais et déductions possibles.",
                'tags': ['Documents officiels', 'Formulaire', 'En ligne'],
            },
            {
                'name': "Épiceries sociales et banques alimentaires — liste cantonale",
                'description': "Adresses et conditions d'accès aux épiceries à prix solidaires et banques alimentaires.",
                'tags': ['Gratuit', 'En personne', 'Aide sociale'],
            },
        ],
    },
    {
        'name': 'Children & family',
        'description': 'Childcare, family allowances, schooling, and parental support resources.',
        'icon': 'UsersIcon',
        'priority': 5,
        'audiences': ['Parents'],
        'resources': [
            {
                'name': "Inscription à la crèche et à la garderie",
                'description': "Démarches pour inscrire votre enfant dans une structure d'accueil agréée.",
                'tags': ['Garde', 'Enfants', 'Formulaire', 'En personne'],
            },
            {
                'name': "Demande d'allocations familiales",
                'description': "Formulaire et conditions pour obtenir les allocations familiales cantonales.",
                'tags': ['Formulaire', 'Famille', 'Budget', 'Enfants'],
            },
            {
                'name': "Aide à la garde — subventionnement cantonal",
                'description': "Comment bénéficier d'une réduction sur les frais de garde selon vos revenus.",
                'tags': ['Garde', 'Enfants', 'Budget', 'Gratuit'],
            },
            {
                'name': "Scolariser son enfant en Suisse",
                'description': "Fonctionnement de l'école publique, inscription, calendrier et fournitures scolaires.",
                'tags': ['Enfants', 'Formation', 'Intégration', 'Gratuit'],
            },
            {
                'name': "Soutien scolaire pour enfants allophones",
                'description': "Cours de rattrapage, classes d'accueil et ressources pour enfants non-francophones.",
                'tags': ['Enfants', 'Langue', 'Gratuit', 'Intégration'],
            },
            {
                'name': "Droits parentaux : congé maternité et paternité",
                'description': "Durée, montants et démarches pour les congés parentaux en Suisse.",
                'tags': ['Famille', 'Travail', 'Droits', 'Documents officiels'],
            },
        ],
    },
    {
        'name': 'Education',
        'description': 'Language courses, diploma recognition, vocational training, and adult education.',
        'icon': 'AcademicCapIcon',
        'priority': 8,
        'audiences': ['Nouveaux arrivants', 'Jeune adulte', "Établis depuis plus d'un an", 'Travailleur qualifié', 'Professionnel de santé'],
        'resources': [
            {
                'name': "Cours de français / allemand / italien gratuits ou subventionnés",
                'description': "Liste des centres de langues, conditions d'accès et niveaux disponibles par canton.",
                'tags': ['Langue', 'Gratuit', 'Intégration', 'En personne'],
            },
            {
                'name': "Reconnaissance de diplômes étrangers — procédure",
                'description': "Démarches auprès de la CDIP, SEFRI ou des ordres professionnels selon votre domaine.",
                'tags': ['Reconnaissance de diplôme', 'Documents officiels', 'Formulaire'],
            },
            {
                'name': "Formation professionnelle pour adultes (AFP / CFC)",
                'description': "Comment obtenir une attestation ou un certificat fédéral de capacité en tant qu'adulte.",
                'tags': ['Formation', 'Travail', 'En personne'],
            },
            {
                'name': "Accès à l'université pour réfugiés et personnes admises à titre provisoire",
                'description': "Programmes universitaires spécifiques, bourses et conditions d'admission.",
                'tags': ['Formation', 'Permis N/F/S', 'Gratuit', 'Jeune'],
            },
            {
                'name': "Validation des acquis de l'expérience (VAE)",
                'description': "Faire reconnaître vos compétences professionnelles sans passer par une formation complète.",
                'tags': ['Reconnaissance de diplôme', 'Travail', 'Formation'],
            },
            {
                'name': "Cours de préparation au marché du travail suisse",
                'description': "CV suisse, lettre de motivation, codes culturels et simulation d'entretien.",
                'tags': ['Travail', 'Formation', 'Intégration', 'Gratuit'],
            },
            {
                'name': "Plateformes d'e-learning gratuites pour migrants",
                'description': "Sélection de ressources en ligne pour apprendre les langues nationales et les bases professionnelles.",
                'tags': ['En ligne', 'Gratuit', 'Langue', 'Formation'],
            },
        ],
    },
    {
        'name': 'Housing',
        'description': 'Emergency housing, tenant rights, social housing applications, and moving tips.',
        'icon': 'HomeIcon',
        'priority': 9,
        'audiences': ['Nouveaux arrivants', "Demandeur d'asile"],
        'resources': [
            {
                'name': "Trouver un logement d'urgence",
                'description': "Hébergements d'urgence, foyers et hôtels sociaux disponibles dans votre canton.",
                'tags': ['Urgence', 'Logement', 'En personne'],
            },
            {
                'name': "Droits du locataire en Suisse",
                'description': "Résiliation de bail, dépôt de garantie, charges, état des lieux — tout ce qu'il faut savoir.",
                'tags': ['Droits', 'Logement', 'Multilingue'],
            },
            {
                'name': "Demande de logement social",
                'description': "Comment s'inscrire sur les listes d'attente des coopératives et offices HLM cantonaux.",
                'tags': ['Formulaire', 'Logement', 'Aide sociale'],
            },
            {
                'name': "Éviter la discrimination dans la recherche de logement",
                'description': "Vos droits face au refus de bail, ressources juridiques et organismes de médiation.",
                'tags': ['Droits', 'Logement', 'En personne'],
            },
            {
                'name': "Dépôt de garantie — règles et remboursement",
                'description': "Montant maximum légal, compte bloqué, procédure de restitution à la fin du bail.",
                'tags': ['Droits', 'Logement', 'Budget'],
            },
            {
                'name': "Assurance ménage — ce qui est obligatoire",
                'description': "Quelles assurances souscrire, comment les comparer et à quel prix.",
                'tags': ['Logement', 'Budget', 'Documents officiels'],
            },
            {
                'name': "Annonces de logement — plateformes et astuces",
                'description': "Les meilleures plateformes de recherche d'appartement et conseils pour maximiser ses chances.",
                'tags': ['Logement', 'En ligne'],
            },
        ],
    },
    {
        'name': 'Rights & duties',
        'description': 'Residence permits, asylum procedures, legal aid, and civic obligations.',
        'icon': 'ScaleIcon',
        'priority': 7,
        'audiences': ["Demandeur d'asile", 'Résident long terme', "Établis depuis plus d'un an"],
        'resources': [
            {
                'name': "Comprendre votre permis de séjour",
                'description': "Différences entre les permis N, F, S, B, C, L, G — droits et restrictions de chacun.",
                'tags': ['Droits', 'Documents officiels', 'Permis N/F/S', 'Multilingue'],
            },
            {
                'name': "Procédure d'asile en Suisse — guide complet",
                'description': "Étapes de la demande, auditions, décision du SEM, recours possibles.",
                'tags': ['Permis N/F/S', 'Droits', 'Formulaire', 'Traduction disponible'],
            },
            {
                'name': "Recours contre une décision du SEM",
                'description': "Comment contester un refus ou une décision négative — délais, formulaires, aide juridique.",
                'tags': ['Permis N/F/S', 'Droits', 'Formulaire', 'Urgence'],
            },
            {
                'name': "Aide juridique gratuite — où trouver un avocat",
                'description': "Services d'aide juridique, permanences gratuites et organisations de défense des migrants.",
                'tags': ['Droits', 'Gratuit', 'En personne', 'Traduction disponible'],
            },
            {
                'name': "Regroupement familial — conditions et formulaire",
                'description': "Qui peut faire venir sa famille en Suisse, délais légaux et documents requis.",
                'tags': ['Famille', 'Formulaire', 'Documents officiels', 'Permis B', 'Permis C'],
            },
            {
                'name': "Naturalisation — conditions et procédure",
                'description': "Durée de résidence requise, test d'intégration, démarches cantonales et fédérales.",
                'tags': ['Droits', 'Intégration', 'Documents officiels', 'Formulaire'],
            },
            {
                'name': "Obligations civiques : impôts, adresse, déclarations",
                'description': "Ce que vous devez annoncer à votre commune : changement d'adresse, arrivée, départ.",
                'tags': ['Documents officiels', 'Formulaire', 'En ligne'],
            },
        ],
    },
    {
        'name': 'Mobility',
        'description': 'Public transport, driving licence exchange, disability transport, and travel tips.',
        'icon': 'TruckIcon',
        'priority': 4,
        'audiences': [],  # universal
        'resources': [
            {
                'name': "Abonnement demi-tarif CFF — comment l'obtenir",
                'description': "Réduction de 50 % sur tous les billets de train, bus et bateau en Suisse.",
                'tags': ['Mobilité', 'Budget', 'En ligne'],
            },
            {
                'name': "Échange d'un permis de conduire étranger",
                'description': "Démarches auprès du service des automobiles, documents requis selon votre pays d'origine.",
                'tags': ['Mobilité', 'Formulaire', 'En personne', 'Documents officiels'],
            },
            {
                'name': "Guide des transports publics par canton",
                'description': "Réseaux TPG (Genève), VBZ (Zurich), BVB (Bâle) — tarifs, abonnements et applications.",
                'tags': ['Mobilité', 'Budget', 'Multilingue'],
            },
            {
                'name': "SwissPass — créer son compte et gérer ses abonnements",
                'description': "Tutoriel pour configurer le SwissPass et y rattacher vos abonnements de transport.",
                'tags': ['Mobilité', 'En ligne'],
            },
            {
                'name': "Transport médical non urgent — comment en bénéficier",
                'description': "Prise en charge des transports vers les soins médicaux par l'assurance maladie.",
                'tags': ['Mobilité', 'Santé', 'Assurance maladie'],
            },
            {
                'name': "Location de vélos et mobilité douce",
                'description': "Systèmes de vélo en libre-service (PubliBike, Velospot) et pistes cyclables.",
                'tags': ['Mobilité', 'Gratuit', 'En ligne'],
            },
        ],
    },
    {
        'name': 'Health',
        'description': 'Health insurance, finding a doctor, mental health, vaccinations, and emergency care.',
        'icon': 'HeartIcon',
        'priority': 9,
        'audiences': [],  # universal
        'resources': [
            {
                'name': "Choisir sa caisse maladie (LAMal) — comparatif",
                'description': "Comment comparer les primes, franchises et réseaux de soins pour choisir la meilleure option.",
                'tags': ['Assurance maladie', 'Budget', 'En ligne'],
            },
            {
                'name': "Demande de réduction de prime d'assurance maladie",
                'description': "Conditions d'accès aux subsides cantonaux, formulaire et délais à respecter.",
                'tags': ['Assurance maladie', 'Budget', 'Formulaire', 'Aide sociale'],
            },
            {
                'name': "Trouver un médecin qui parle votre langue",
                'description': "Annuaires en ligne et services de médiation pour trouver un praticien adapté.",
                'tags': ['Santé', 'Traduction disponible', 'En ligne', 'Multilingue'],
            },
            {
                'name': "Urgences médicales — que faire et où aller",
                'description': "Numéros d'urgence, permanences de nuit, garde médicale et rôle du SMUR.",
                'tags': ['Santé', 'Urgence', 'Multilingue', 'Gratuit'],
            },
            {
                'name': "Santé mentale pour migrants — ressources et soutien",
                'description': "Services de consultation psychologique adaptés aux personnes issues de la migration.",
                'tags': ['Santé', 'Gratuit', 'Traduction disponible', 'En personne'],
            },
            {
                'name': "Calendrier de vaccination officiel suisse",
                'description': "Vaccins obligatoires et recommandés pour adultes et enfants en Suisse.",
                'tags': ['Santé', 'Enfants', 'Gratuit', 'Documents officiels'],
            },
            {
                'name': "Guide de la maternité en Suisse",
                'description': "Suivi de grossesse, accouchement, sage-femme, prise en charge LAMal.",
                'tags': ['Santé', 'Famille', 'Assurance maladie', 'Femmes'],
            },
            {
                'name': "Handicap et accès aux soins — droits et aides",
                'description': "Prestations AI, aides techniques, transport médical et accompagnement.",
                'tags': ['Santé', 'Droits', 'Aide sociale'],
            },
        ],
    },
]


class Command(BaseCommand):
    help = 'Seed the database with realistic PIN prototype data.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete all existing categories, resources, audiences and tags before seeding.',
        )

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
                name=aud_data['name'],
                defaults=aud_data,
            )
            if not created:
                # Update fields in case they changed
                for field, value in aud_data.items():
                    setattr(aud, field, value)
                aud.save()
            # Set relevant_tags (replace)
            aud.relevant_tags.set([tag_map[t] for t in rel_tags if t in tag_map])
            audience_map[aud.name] = aud
            if created:
                self.stdout.write(f'  + Audience: {aud.name}')
            else:
                self.stdout.write(f'  ~ Audience (updated): {aud.name}')

        # -- Categories + Resources --
        self.stdout.write('\nCreating categories and resources...')
        for cat_data in CATEGORIES:
            audience_names = cat_data.pop('audiences')
            resources_data = cat_data.pop('resources')

            cat, created = Category.objects.get_or_create(
                name=cat_data['name'],
                defaults=cat_data,
            )
            if not created:
                for field, value in cat_data.items():
                    setattr(cat, field, value)
                cat.save()

            cat.audiences.set([audience_map[n] for n in audience_names if n in audience_map])

            action = '+' if created else '~'
            self.stdout.write(f'  {action} Category: {cat.name}')

            for res_data in resources_data:
                tag_labels = res_data.pop('tags')
                res, res_created = Resource.objects.get_or_create(
                    name=res_data['name'],
                    category=cat,
                    defaults={**res_data, 'file': SAMPLE_FILE},
                )
                res.tags.set([tag_map[t] for t in tag_labels if t in tag_map])
                if res_created:
                    self.stdout.write(f'      + {res.name}')

        self.stdout.write(self.style.SUCCESS('\nSeed complete.'))
