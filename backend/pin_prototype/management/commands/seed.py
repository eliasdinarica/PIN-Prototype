"""
Seed command, données réelles pour le canton de Neuchâtel (NE).

Usage:
    python manage.py seed            # additif (get_or_create)
    python manage.py seed --reset    # efface tout puis recrée
"""

import re
from datetime import date

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.core.management.base import BaseCommand
from pin_prototype.models import (
    Audience, Category, Subcategory, Tag, Resource, Guide, GuideStep,
    Contributor, ResourcePlace, Profile, ResourceFeedback, ResourceTranslation,
    section_stream_blocks,
)

# ---------------------------------------------------------------------------
# Helpers, construction des corps d'articles (format Wagtail StreamField)
# ---------------------------------------------------------------------------

def para(text):
    return f'<p>{text}</p>'

def h3(text):
    return f'<h3>{text}</h3>'

def ul(*items):
    return '<ul>' + ''.join(f'<li>{i}</li>' for i in items) + '</ul>'

def ol(*items):
    return '<ol>' + ''.join(f'<li>{i}</li>' for i in items) + '</ol>'

def sec(title, *blocks, width='full'):
    parts = ([f'<h2>{title}</h2>'] if title else []) + [str(b) for b in blocks if b]
    html = ''.join(parts)
    if width == 'half':
        return ('__half__', html)
    return {'type': 'richtext', 'value': html}

def body(*sections):
    result = []
    i = 0
    while i < len(sections):
        s = sections[i]
        if isinstance(s, tuple) and s and s[0] == '__half__':
            nxt = sections[i + 1] if i + 1 < len(sections) else None
            if isinstance(nxt, tuple) and nxt and nxt[0] == '__half__':
                result.append({'type': 'columns', 'value': {'left': s[1], 'right': nxt[1]}})
                i += 2
            else:
                result.append({'type': 'richtext', 'value': s[1]})
                i += 1
        else:
            result.append(s)
            i += 1
    return result


# Fixed-section fields (same template for every resource)
SECTION_FIELDS = ('description', 'why_interesting', 'how_to', 'location')

# Keyword hints to map an old freeform section (by its <h2> title) into one
# of the three fixed sections.
# 'utile'/'avantages'/'intérêt' removed: they wrongly sent link sections like
# "Ressources utiles" / "Liens utiles" into the "why" bucket.
_WHY_KW = ('à quoi ça sert', 'a quoi ca sert', 'pourquoi', "c'est quoi", "qu'est-ce",
           'ce que c\'est', 'ce que ça')
_LOC_KW = ('adresse', 'contact', 'coordonnées', 'coordonnees', 'horaires',
           'téléphone', 'telephone', 'permanence', 'guichet',
           'où s', 'où se', 'où aller', 'où trouver', 'où m')

_CONTACT_RE = re.compile(r'<b>\s*(Adresse|Téléphone|Tél|Tel|Email|E-mail|Courriel)\b', re.IGNORECASE)


def _block_title(html):
    m = re.search(r'<h[123]>(.*?)</h[123]>', html or '')
    return (m.group(1) if m else '').lower()


def _strip_tags(s):
    return re.sub(r'<[^>]+>', '', s or '').strip()


def _labeled(html, labels):
    """Value of a '<b>Label :</b> value</li>' item, stripped of tags."""
    for label in labels:
        m = re.search(r'<b>\s*' + label + r'[^<]*</b>\s*(.*?)</li>', html, re.IGNORECASE | re.DOTALL)
        if m:
            return _strip_tags(m.group(1)).lstrip(': ').strip()
    return ''


def _city_from_address(address):
    m = re.search(r'\b\d{4}\s+([A-Za-zÀ-ÿ][\wÀ-ÿ.\- ]+?)(?:,|$)', address)
    return m.group(1).strip() if m else ''


def split_body(blocks_list):
    """Sort an old body into the three fixed sections. Contact cards go to the
    'location' bucket; two-column blocks are sorted side by side (not dumped)."""
    buckets = {'why': [], 'how': [], 'location': []}

    def place_html(html):
        if not html:
            return
        if _CONTACT_RE.search(html):
            buckets['location'].append(html)
            return
        title = _block_title(html)
        if any(k in title for k in _WHY_KW):
            buckets['why'].append(html)
        elif any(k in title for k in _LOC_KW):
            buckets['location'].append(html)
        else:
            buckets['how'].append(html)

    for b in blocks_list or []:
        btype = b.get('type')
        if btype == 'richtext':
            place_html(b.get('value', ''))
        elif btype == 'columns':
            v = b.get('value', {})
            place_html(v.get('left', ''))
            place_html(v.get('right', ''))
        elif btype == 'callout':
            buckets['how'].append(b.get('value', {}).get('text', ''))

    def join(parts):
        return ''.join(parts).replace('<h2>', '<h3>').replace('</h2>', '</h3>')
    return {k: join(v) for k, v in buckets.items()}


def extract_places_from_html(html):
    """Turn contact cards (heading + Adresse/Téléphone/Email items) into
    structured place dicts. Used to fill the 'Location' section."""
    if not html:
        return []
    parts = re.split(r'<h[123]>(.*?)</h[123]>', html)
    out = []
    for i in range(1, len(parts), 2):
        name = _strip_tags(parts[i])
        content = parts[i + 1] if i + 1 < len(parts) else ''
        address = _labeled(content, ['Adresse'])
        phone = _labeled(content, ['Téléphone', 'Tél', 'Tel'])
        email = _labeled(content, ['Email', 'E-mail', 'Courriel'])
        if not (address or phone or email):
            continue
        out.append({
            'name': name[:200], 'city': _city_from_address(address)[:120],
            'address': address[:300], 'phone': phone[:50], 'email': email[:120],
        })
    return out


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
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis N/F/S', 'Asile', 'Droits', 'Aide sociale', 'Urgence', 'Logement urgence', 'Interprete'],
    },
    {
        'name': 'Parents',
        'description': "Personnes ayant des enfants à charge.",
        'statuses': '', 'has_children': True,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Garde enfants', 'Enfants', 'Famille', 'Scolarisation', 'Allocations familiales', 'Soutien scolaire'],
    },
    {
        'name': 'Nouveaux arrivants',
        'description': "Arrivés en Suisse depuis moins d'un an.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': False,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Logement', 'Langue', 'Cours de langue', 'Documents officiels', 'Assurance maladie', 'Banque', 'Traduction disponible'],
    },
    {
        'name': "Établis depuis plus d'un an",
        'description': "En phase d'intégration avancée.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': True,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Formation', 'Reconnaissance diplome', 'Naturalisation', 'Vie sociale'],
    },
    {
        'name': 'Résident long terme',
        'description': "Titulaires d'un permis B ou C.",
        'statuses': 'B,C', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis B', 'Permis C', 'Droits', 'Naturalisation', 'Impots'],
    },
    {
        'name': 'Frontalier',
        'description': "Titulaires d'un permis G.",
        'statuses': 'G', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis G', 'Mobilite', 'Travail', 'Droit du travail', 'Impots'],
    },
    {
        'name': 'Femmes',
        'description': "Ressources spécifiquement destinées aux femmes migrantes.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Femmes', 'Sante mentale', 'Aide juridique'],
    },
    {
        'name': 'Avec permis de conduire',
        'description': "Personnes titulaires d'un permis de conduire.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': True, 'min_computer_skills': '', 'min_education_level': '',
        'relevant_tags': ['Permis de conduire', 'Mobilite', 'Transports publics'],
    },
    {
        'name': 'Compétences numériques de base',
        'description': "Personnes sachant utiliser internet et les services en ligne.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': 'basic', 'min_education_level': '',
        'relevant_tags': ['En ligne', 'E-learning', 'Formulaire'],
    },
    {
        'name': 'Compétences numériques avancées',
        'description': "Personnes à l'aise avec les outils numériques et bureautiques.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': 'advanced', 'min_education_level': '',
        'relevant_tags': ['En ligne', 'E-learning', 'CV candidature', 'Universite'],
    },
    {
        'name': 'Formation supérieure',
        'description': "Personnes avec un diplôme universitaire ou équivalent.",
        'statuses': '', 'has_children': None,
        'arrived_over_year': None,
        'has_driving_license': None, 'min_computer_skills': '', 'min_education_level': 'bachelor',
        'relevant_tags': ['Reconnaissance diplome', 'Universite', 'Formation', 'CV candidature'],
    },
]

# ---------------------------------------------------------------------------
# "Pourquoi c'est intéressant" — première section du gabarit, rédigée à la main
# pour chaque ressource (motivation / ce qu'on y gagne). Rendu en paragraphe
# (pas de sous-titre repliable), keyée sur le nom exact de la ressource.
# ---------------------------------------------------------------------------

RESOURCE_WHY = {
    # --- Work ---
    "Je cherche du travail, par où commencer ?": para("Trouver un emploi ouvre la porte à l'autonomie et à l'intégration. Le ONE vous accompagne gratuitement, et si vous avez cotisé, vous pouvez recevoir de l'argent chaque mois pendant votre recherche."),
    "Je veux préparer un CV pour trouver du travail en Suisse": para("Le CV suisse suit des règles précises. Un CV bien présenté augmente nettement vos chances d'être appelé pour un entretien."),
    "Je veux me former ou changer de métier": para("Se former ou se réorienter permet d'accéder à un métier reconnu en Suisse. Le CNIP vous aide gratuitement à valoriser votre expérience, même acquise à l'étranger."),
    "Je veux travailler à mon compte en Suisse": para("Travailler à son compte peut être une vraie voie vers l'autonomie. Mais la loi impose des règles précises : les connaître dès le départ évite de gros problèmes."),
    "Je veux connaître mes droits en tant qu'employé": para("Connaître vos droits vous protège : salaire, congés, délais de licenciement. Beaucoup de personnes acceptent de mauvaises conditions faute de les connaître."),
    "Je veux trouver du travail rapidement via une agence": para("Une agence d'intérim peut vous placer vite en entreprise, même sans expérience suisse. C'est souvent un tremplin vers un emploi fixe."),
    "Je ne sais pas si je suis payé correctement": para("Comprendre votre fiche de salaire vous permet de vérifier que vous êtes payé selon les règles de votre secteur, et d'agir si ce n'est pas le cas."),
    "Je ne sais pas quel métier choisir en Suisse": para("Un conseiller d'orientation vous aide gratuitement à trouver une direction professionnelle réaliste, adaptée à votre parcours et au marché suisse."),
    "Je veux utiliser LinkedIn pour trouver du travail": para("En Suisse, beaucoup de postes ne sont jamais publiés : ils passent par le réseau. Un bon profil LinkedIn augmente vraiment vos chances."),
    "Je cherche un travail saisonnier ou en agriculture": para("Le travail saisonnier ne demande pas toujours de diplôme et permet de démarrer vite. C'est une bonne façon de construire une première expérience et un réseau en Suisse."),
    "Je veux faire du bénévolat pour avoir une première expérience": para("Le bénévolat permet de pratiquer le français, de rencontrer des gens et d'ajouter une référence locale à votre CV, même sans permis de travail complet."),
    # --- Health ---
    "Je dois m'assurer contre la maladie": para("L'assurance maladie est obligatoire pour tout le monde en Suisse. Sans elle, vos frais médicaux ne sont pas couverts et vous risquez une pénalité. Vous avez 3 mois pour vous inscrire."),
    "Je veux payer moins cher mon assurance maladie": para("Si vos revenus sont modestes, l'État peut payer une partie de votre prime. C'est un droit, pas une faveur : beaucoup de personnes qui y ont droit ne le demandent pas."),
    "Je cherche un médecin de famille": para("Le médecin de famille est votre premier contact pour votre santé et celle de vos proches. En trouver un tôt vous évite de dépendre des urgences."),
    "J'ai besoin d'aide médicale en urgence": para("En cas d'urgence, savoir quel numéro appeler et où aller peut faire gagner un temps précieux, parfois vital."),
    "Je me sens mal et j'ai besoin d'aide psychologique": para("Arriver dans un nouveau pays est difficile : stress, tristesse et anxiété sont normaux. Une aide existe, souvent gratuite et avec un interprète. Vous n'êtes pas seul."),
    "Je suis enceinte, que dois-je faire ?": para("Bien suivre sa grossesse protège votre santé et celle de votre bébé. En Suisse, le suivi et l'accouchement sont pris en charge, et vous avez droit à un congé maternité."),
    "J'ai besoin de soins dentaires": para("Les soins dentaires coûtent cher et sont peu remboursés. Connaître les options abordables évite de renoncer aux soins ou de s'endetter."),
    "Je suis malade mais mon médecin n'est pas disponible": para("Quand on ne peut pas attendre un rendez-vous, il existe des permanences et des conseils par téléphone pour être pris en charge rapidement."),
    "Je veux me faire vacciner": para("Les vaccins protègent votre santé et celle de vos proches. Savoir lesquels sont recommandés en Suisse et où les faire vous évite des risques inutiles."),
    "Je cherche des informations sur la contraception ou les IST": para("Prendre soin de sa santé sexuelle est important. À Neuchâtel, des services gratuits ou peu chers existent, dans le respect de votre confidentialité."),
    "J'ai un handicap ou une maladie grave, quelles aides existent ?": para("Si un problème de santé vous empêche de travailler, l'assurance invalidité (AI) peut vous soutenir. Faire la demande tôt est important, car les délais sont longs."),
    "J'ai des problèmes avec l'alcool, les drogues ou le jeu": para("Demander de l'aide est un pas courageux. Des professionnels vous accompagnent gratuitement et en toute confidentialité, sans jugement."),
    # --- Money & budget ---
    "Je n'ai pas assez d'argent pour vivre": para("Si vos revenus ne couvrent pas vos besoins de base, vous avez droit à un soutien. Le demander est un droit et peut éviter que votre situation empire."),
    "Je veux ouvrir un compte bancaire": para("Un compte bancaire est nécessaire pour recevoir un salaire, payer ses factures et vivre au quotidien en Suisse. Savoir quelle banque et quels documents choisir fait gagner du temps."),
    "J'ai perdu mon emploi et je veux toucher le chômage": para("Si vous avez cotisé, le chômage vous verse de l'argent chaque mois pendant votre recherche. S'inscrire vite est essentiel pour ne pas perdre de droits."),
    "Je ne comprends pas comment fonctionnent les impôts": para("Comprendre comment vous êtes imposé évite les mauvaises surprises et vous permet de payer le juste montant, ni plus ni moins."),
    "Je veux comprendre la retraite en Suisse": para("Comprendre le système de retraite vous aide à savoir ce que vous cotisez et à quoi vous aurez droit plus tard. C'est utile à tout âge."),
    "J'ai des dettes et je ne sais plus quoi faire": para("Des dettes peuvent vite s'aggraver. En parler tôt à un professionnel, gratuitement, permet souvent de trouver des solutions avant que la situation devienne critique."),
    "Ma rente ne suffit pas pour vivre": para("Si votre rente AVS ou AI est trop petite, vous avez droit à un complément. Ce n'est pas de l'aide sociale, c'est un droit que beaucoup n'utilisent pas."),
    "Je veux mieux gérer mon argent": para("Bien organiser ses dépenses évite les difficultés financières. Des conseils et des outils gratuits existent pour vous aider à garder le contrôle."),
    "J'ai reçu un acte de poursuite, que faire ?": para("Recevoir un acte de poursuite fait peur, mais cela ne veut pas dire qu'on va vous expulser ou vous arrêter. Comprendre ce que c'est vous permet de réagir calmement."),
    "Je n'ai pas assez à manger": para("Personne ne devrait avoir faim. Des associations distribuent de la nourriture gratuitement ou à très bas prix, en toute discrétion."),
    # --- Education ---
    "Je veux apprendre le français": para("Apprendre le français ouvre la porte à tout le reste : le travail, la santé, l'école des enfants et les démarches. Des cours gratuits ou peu chers existent près de chez vous."),
    "Je veux faire reconnaître mon diplôme étranger en Suisse": para("Faire reconnaître votre diplôme vous permet d'accéder à des emplois à votre niveau, plutôt que de repartir de zéro."),
    "Je veux obtenir un diplôme professionnel suisse": para("Un diplôme professionnel suisse est très valorisé sur le marché du travail. Il est possible de l'obtenir en tant qu'adulte, même sans avoir fait d'apprentissage."),
    "Je veux apprendre le français depuis chez moi": para("Pratiquer chez soi, à son rythme, accélère les progrès. Des applications et des sites gratuits complètent bien les cours en présentiel."),
    "Je veux certifier mon niveau de français": para("Le certificat FIDE prouve officiellement votre niveau de français. Il peut être exigé pour le permis C ou pour la naturalisation."),
    "Je veux savoir si l'État peut payer mes cours de langue": para("Les cours de langue peuvent coûter cher. À Neuchâtel, le canton peut en financer une partie : ne pas le savoir, c'est payer plus que nécessaire."),
    "Je ne sais pas encore lire ni écrire": para("Apprendre à lire et écrire est possible à tout âge, dans un cadre bienveillant. C'est la base pour gagner en autonomie au quotidien."),
    "Je cherche des cours de langue avec des horaires flexibles": para("Des cours du soir et du week-end permettent d'apprendre le français même en travaillant. Choisir le bon format aide à progresser plus vite."),
    "Je veux me former en ligne pour améliorer mes compétences": para("Se former en ligne permet d'apprendre un métier ou de monter en compétences depuis chez soi, gratuitement ou à petit prix."),
    "Je veux étudier à l'université à Neuchâtel": para("Étudier en Suisse ouvre de nombreuses portes. Connaître les conditions d'inscription et les aides financières possibles rend le projet plus accessible."),
    # --- Children & family ---
    "Je veux recevoir les allocations pour mes enfants": para("Chaque famille avec enfants a droit à des allocations chaque mois. C'est un soutien financier important qu'il ne faut pas laisser de côté."),
    "Je veux inscrire mon enfant à l'école": para("L'école est gratuite et obligatoire pour tous les enfants. Elle est aussi un lieu clé d'intégration et d'apprentissage du français."),
    "Je cherche une place en crèche pour mon enfant": para("Une place en crèche permet de travailler ou de suivre des cours l'esprit tranquille. Une aide financière est souvent possible selon vos revenus."),
    "Mon enfant a besoin d'aide pour apprendre le français à l'école": para("Un bon accompagnement en français aide votre enfant à réussir à l'école et à s'intégrer. Des cours de soutien gratuits existent."),
    "Je cherche une garde pour mes enfants avant ou après l'école": para("Le parascolaire garde vos enfants avant, pendant et après l'école. Cela permet de concilier travail, cours et vie de famille."),
    "Je cherche des activités pour mes enfants pendant les vacances": para("Pendant les vacances, des camps et des activités à prix réduit occupent les enfants et les aident à se faire des amis et à progresser en français."),
    "Je veux connaître mes droits lors d'une naissance": para("À la naissance d'un enfant, vous avez droit à un congé et à des allocations. Les connaître vous évite de perdre des droits importants."),
    # --- Rights & duties ---
    "Je ne comprends pas les différents permis de séjour": para("Votre permis détermine vos droits : travailler, voyager, faire venir votre famille. Bien le comprendre vous évite des erreurs qui peuvent coûter cher."),
    "J'ai besoin d'aide juridique gratuite": para("Face à un problème de permis ou de droits, un bon conseil peut tout changer. Des associations vous aident gratuitement."),
    "Je veux comprendre la procédure d'asile": para("Comprendre les étapes de votre demande d'asile et vos droits pendant la procédure vous aide à prendre les bonnes décisions au bon moment."),
    "Je veux faire venir ma famille en Suisse": para("Le regroupement familial permet de réunir votre famille. Les conditions et les délais sont stricts : les connaître augmente vos chances de réussite."),
    "Je veux devenir citoyen suisse": para("La naturalisation donne accès à des droits complets, dont le droit de vote. Connaître les conditions vous permet de préparer votre demande à l'avance."),
    "Je veux passer du permis B au permis C": para("Le permis C offre plus de stabilité et de droits, et il ne doit plus être renouvelé chaque année. Savoir quand et comment le demander est utile."),
    "Je veux voter aux élections à Neuchâtel": para("À Neuchâtel, les personnes étrangères peuvent voter après 5 ans de résidence. Voter, c'est avoir voix au chapitre sur la vie locale."),
    "Je divorce, est-ce que ça change mon droit de séjour ?": para("Une séparation peut avoir des conséquences sur votre permis. Bien vous informer à temps vous permet de protéger votre situation."),
    "J'ai été victime de discrimination": para("La discrimination est illégale en Suisse. Savoir quoi faire et où s'adresser vous aide à faire respecter vos droits."),
    "Je dois obtenir un document d'état civil (acte de naissance, mariage)": para("Beaucoup de démarches exigent un acte de naissance ou de mariage. Savoir comment l'obtenir depuis votre pays évite des blocages."),
    "Je viens d'arriver, je dois m'inscrire à ma commune": para("S'annoncer à sa commune dans les 14 jours est obligatoire et donne accès à la plupart des autres services. C'est la première démarche à faire."),
    # --- Housing ---
    "Je n'ai pas de logement, j'ai besoin d'aide": para("Personne ne devrait dormir dehors. Des numéros et des structures d'urgence existent à Neuchâtel pour vous héberger rapidement."),
    "Je veux connaître mes droits en tant que locataire": para("Connaître vos droits vous protège face à votre propriétaire : loyer, réparations, résiliation. Beaucoup de locataires paient trop faute d'information."),
    "Je cherche un appartement à louer": para("Trouver un logement peut être difficile. Savoir où chercher et bien préparer son dossier augmente nettement vos chances."),
    "Je ne comprends pas le dépôt de garantie": para("Le dépôt de garantie représente souvent plusieurs mois de loyer. Bien le comprendre vous aide à le payer sans mauvaise surprise et à le récupérer à la fin."),
    "Je cherche un logement à loyer réduit": para("Si vos revenus sont faibles, un logement social peut alléger fortement votre budget. Encore faut-il savoir où et comment s'inscrire."),
    "Je dois prendre une assurance pour mon appartement": para("L'assurance ménage est souvent exigée par le propriétaire et vous protège en cas de dégât ou de vol. La choisir bien permet d'éviter de gros frais."),
    # --- Integration ---
    "Je viens d'arriver, que peut faire le COSM pour moi ?": para("Le COSM est souvent le premier endroit à contacter en arrivant : il oriente, informe et aide gratuitement pour la langue et les démarches. Le connaître fait gagner beaucoup de temps."),
    "Je suis une femme migrante, je cherche du soutien": para("Le RECIF offre un espace bienveillant aux femmes migrantes : cours de français, aide administrative et rencontres. Un vrai point d'appui pour s'intégrer."),
    "Je veux rencontrer des gens et m'intégrer": para("Créer des liens aide à se sentir chez soi, à pratiquer le français et à trouver du soutien. Les associations et le bénévolat sont d'excellents points de départ."),
    "Je veux comprendre les règles de vie en Suisse": para("Connaître les habitudes et les règles du quotidien évite les malentendus et aide à bien s'entendre avec ses voisins."),
    "Je ne parle pas encore le français, j'ai besoin d'un interprète": para("Un interprète communautaire vous permet d'être compris à vos rendez-vous médicaux, scolaires ou administratifs. C'est essentiel pour ne pas rester bloqué."),
    "Je veux apprendre à utiliser un ordinateur ou Internet": para("Beaucoup de démarches se font en ligne. Apprendre les bases de l'informatique vous rend plus autonome au quotidien. Des cours gratuits existent."),
    # --- Mobility ---
    "Je veux utiliser les transports en commun": para("Bien utiliser le train et le bus fait gagner du temps et de l'argent. Il existe des abonnements et des réductions qui allègent vos trajets."),
    "Je veux échanger mon permis de conduire étranger": para("Vous devez échanger votre permis dans les 12 mois après votre arrivée. Passé ce délai, la démarche devient plus compliquée."),
    "Je veux me déplacer à vélo à Neuchâtel": para("Le vélo est économique, bon pour la santé et pratique en ville. Connaître les pistes, les vélos partagés et les règles rend vos trajets plus sûrs."),
    "J'ai du mal à me déplacer pour mes rendez-vous médicaux": para("Ne pas pouvoir se déplacer ne doit pas empêcher de se soigner. Des solutions de transport existent, parfois remboursées."),
    "J'ai une voiture, que dois-je faire en Suisse ?": para("Une voiture implique des obligations : assurance, immatriculation, contrôle technique. Les connaître vous évite des amendes et de gros problèmes."),
    # --- Démo (invité) ---
    "Atelier conversation français (Caritas)": para("Pratiquer le français à l'oral, gratuitement et sans stress, aide à gagner en confiance et à progresser plus vite. C'est aussi un moment de rencontre."),
}


# ---------------------------------------------------------------------------
# "Comment faire" — deuxième section du gabarit. Rédigé à la main : la 1re
# sous-section dépliable est toujours l'action principale (qui contacter / la
# démarche), puis 1-2 détails. Titres explicites, jamais "Comment faire".
# ---------------------------------------------------------------------------

RESOURCE_HOW = {
    # --- Work ---
    "Je cherche du travail, par où commencer ?": h3("S'inscrire au ONE") + ol("Inscrivez-vous en ligne sur arbeit.swiss dès le premier jour sans emploi.", "Le ONE vous rappelle sous 24 à 48 h pour un rendez-vous.", "Inscrivez-vous aussi à une caisse de chômage.") + h3("Documents à apporter") + ul("Pièce d'identité et permis de séjour", "Numéro AVS", "Certificats de travail et CV à jour") + h3("Bon à savoir") + para("Envoyez 8 à 12 candidatures par mois et gardez une preuve de chaque envoi."),
    "Je veux préparer un CV pour trouver du travail en Suisse": h3("Rédiger votre CV suisse") + ol("Suivez l'ordre : coordonnées, photo, résumé, expériences, formation, langues.", "Maximum 2 pages, du plus récent au plus ancien.", "Indiquez votre niveau de langue (A1 à C2).") + h3("Les règles à respecter") + ul("Photo professionnelle recommandée", "Pas d'état civil ni de religion", "Adaptez le CV à chaque poste") + h3("Se faire aider gratuitement") + para("Le ONE propose des ateliers CV ; le COSM et le CNIP accompagnent aussi la rédaction."),
    "Je veux me former ou changer de métier": h3("Prendre contact avec le CNIP") + ol("Contactez le CNIP pour un premier entretien.", "Faites un bilan de compétences pour évaluer vos acquis.", "Construisez avec un conseiller un projet de formation ou de reconversion.") + h3("Ce qui est possible") + ul("Reconnaissance de votre expérience étrangère", "Formation professionnelle raccourcie pour adultes (AFP/CFC)", "Mise en relation avec des employeurs"),
    "Je veux travailler à mon compte en Suisse": h3("Lancer votre activité") + ol("Choisissez la forme juridique (raison individuelle, Sàrl, SA).", "Annoncez-vous à la caisse de compensation (AVS) — obligatoire.", "Inscrivez-vous au Registre du commerce et à la TVA si le chiffre d'affaires dépasse 100 000 CHF/an.") + h3("À prévoir") + ul("Vous payez vous-même vos cotisations AVS/AI/APG", "Pas d'assurance chômage pour les indépendants", "Un conseil gratuit existe (biz.admin.ch, kmu.admin.ch)"),
    "Je veux connaître mes droits en tant qu'employé": h3("Vérifier votre contrat") + ul("Exigez toujours un contrat écrit (salaire, horaires, délai de congé)", "Vérifiez si une convention collective (CCT) s'applique à votre branche") + h3("Congés et absences") + ul("Minimum 4 semaines de vacances par an", "Droit au salaire en cas de maladie ou d'accident", "Jours fériés selon le canton") + h3("En cas de problème") + para("Un syndicat (Unia, Syna) peut vous conseiller, souvent gratuitement pour les membres."),
    "Je veux trouver du travail rapidement via une agence": h3("S'inscrire dans une agence d'intérim") + ol("Inscrivez-vous dans plusieurs agences en même temps.", "Apportez CV, permis de séjour et certificats de travail.", "Précisez vos langues, votre disponibilité et votre secteur.") + h3("Bon à savoir") + ul("L'agence est votre employeur et paie votre salaire", "Les missions durent de quelques jours à plusieurs mois", "C'est gratuit pour vous — méfiez-vous si on vous demande de l'argent"),
    "Je ne sais pas si je suis payé correctement": h3("Vérifier votre salaire") + ol("Cherchez la convention collective (CCT) de votre secteur.", "Comparez votre salaire au minimum de la branche.", "Vérifiez votre fiche de salaire (brut, cotisations, net, 13e salaire).") + h3("Si vous êtes sous-payé") + para("Un syndicat (Unia, Syna) ou l'inspection du travail peut vous aider, au besoin de façon anonyme."),
    "Je ne sais pas quel métier choisir en Suisse": h3("Consulter l'orientation (OCOSP)") + ol("Prenez rendez-vous à l'Office d'orientation (OCOSP).", "Faites des tests d'aptitudes et un entretien conseil.", "Explorez les métiers et formations sur berufsberatung.ch.") + h3("Tester un métier") + para("Demandez un stage d'observation de 1 à 5 jours en entreprise pour découvrir un métier avant de vous lancer."),
    "Je veux utiliser LinkedIn pour trouver du travail": h3("Créer un bon profil") + ul("Photo professionnelle et titre clair (métier recherché)", "Résumé de 3 à 5 lignes sur votre parcours", "Ajoutez vos expériences, même à l'étranger, et au moins 10 compétences") + h3("Activer votre réseau") + ul("Connectez-vous avec d'anciens collègues, voisins, associations", "Rejoignez des groupes de votre secteur en Suisse romande", "Demandez des recommandations") + h3("Autres sites d'emploi") + para("Complétez avec jobs.ch, jobup.ch, indeed.ch et arbeit.swiss."),
    "Je cherche un travail saisonnier ou en agriculture": h3("Où chercher") + ul("Agriculture : agrijob.ch", "Hôtellerie-restauration : gastrojob.ch", "Toutes régions : saisonnier.ch et agences d'intérim", "Le ONE peut aussi signaler des offres locales") + h3("Conditions importantes") + ul("Vérifiez que votre permis autorise le travail", "Le contrat doit être signé avant de commencer", "Vous avez droit au salaire minimum de la CCT du secteur"),
    "Je veux faire du bénévolat pour avoir une première expérience": h3("Trouver une mission") + ul("Benevol Neuchâtel : benevolat-ne.ch", "Croix-Rouge, Caritas, maisons de quartier", "Demandez au COSM des pistes proches de chez vous") + h3("Le valoriser sur votre CV") + ul("Notez l'organisation, la durée et vos tâches", "Demandez un contact de référence (avec son accord)"),
    # --- Health ---
    "Je dois m'assurer contre la maladie": h3("Choisir une caisse et s'inscrire") + ol("Comparez les primes sur comparis.ch (canton NE, votre âge).", "Choisissez votre franchise (300 à 2500 CHF).", "Contactez la caisse choisie ou inscrivez-vous en ligne, dans les 3 mois.") + h3("Bon à savoir") + ul("La couverture de base (LAMal) est identique partout", "Toutes les caisses doivent vous accepter", "Demandez ensuite une réduction de prime si vos revenus sont modestes"),
    "Je veux payer moins cher mon assurance maladie": h3("Faire la demande de subside") + ol("Rendez-vous à votre Guichet social régional (GSR).", "Apportez vos justificatifs de revenus et de situation familiale.", "Le GSR transmet votre dossier à l'OCAB, qui verse le subside à votre caisse.") + h3("Bon à savoir") + para("La demande passe par le GSR, pas directement par l'OCAB. Le subside peut réduire ou supprimer votre prime."),
    "Je cherche un médecin de famille": h3("Trouver un médecin") + ol("Cherchez sur doctorfmh.ch, le registre officiel des médecins.", "Prenez rendez-vous en ligne sur onedoc.ch ou appelez les cabinets proches.", "Demandez aussi à votre entourage ou au COSM.") + h3("Si vous ne trouvez pas") + para("En attendant, les urgences de l'Hôpital neuchâtelois (HNE) et votre pharmacie peuvent vous orienter."),
    "J'ai besoin d'aide médicale en urgence": h3("Qui appeler") + ul("144 — Ambulance (gratuit, 24h/24)", "145 — Empoisonnement", "143 — Soutien psychologique (La Main Tendue)", "112 — Numéro d'urgence européen") + h3("Où aller") + ul("Urgences de l'Hôpital neuchâtelois (HNE), à Neuchâtel et La Chaux-de-Fonds", "Pharmacies de garde : pharmaguard.ch", "Votre caisse maladie a une ligne de conseil médical 24h/24"),
    "Je me sens mal et j'ai besoin d'aide psychologique": h3("Où trouver de l'aide") + ul("Votre médecin peut vous orienter vers un psychiatre (remboursé)", "Le COSM peut fournir un accompagnement avec interprète", "Caritas et le CSP proposent un soutien") + h3("Lignes d'écoute") + ul("143 — La Main Tendue (anonyme, gratuit, 24h/24)", "147 — Pro Juventute pour les jeunes", "Centre LAVI pour les victimes de violence"),
    "Je suis enceinte, que dois-je faire ?": h3("Organiser le suivi") + ol("Prenez rendez-vous avec un-e gynécologue ou une sage-femme.", "Le suivi et l'accouchement sont remboursés par la LAMal, sans franchise.", "Après la naissance, une sage-femme peut passer à domicile.") + h3("Congé maternité") + ul("14 semaines après l'accouchement", "80 % du salaire, maximum 220 CHF/jour", "Condition : avoir travaillé au moins 5 mois avant"),
    "J'ai besoin de soins dentaires": h3("Trouver un dentiste abordable") + ol("Comparez plusieurs cabinets : les tarifs varient.", "Demandez un devis avant un traitement important.", "Regardez les cliniques dentaires d'école, souvent moins chères.") + h3("Si vous n'avez pas les moyens") + para("En cas de difficulté, l'aide sociale (GSR) ou une association comme Caritas peut parfois participer aux frais urgents."),
    "Je suis malade mais mon médecin n'est pas disponible": h3("Être pris en charge vite") + ul("Rendez-vous dans une permanence médicale sans rendez-vous", "Appelez la ligne de conseil médical de votre caisse (24h/24)", "Votre pharmacie peut traiter les petits problèmes") + h3("Quand aller aux urgences") + para("En cas de signe grave (douleur forte, difficulté à respirer, forte fièvre), appelez le 144 ou allez aux urgences."),
    "Je veux me faire vacciner": h3("Où se faire vacciner") + ol("Prenez rendez-vous chez votre médecin ou en pharmacie.", "Apportez votre carnet de vaccination si vous en avez un.", "Demandez quels vaccins mettre à jour selon votre âge.") + h3("Remboursement") + para("Les vaccins recommandés par l'OFSP sont en général remboursés par la LAMal."),
    "Je cherche des informations sur la contraception ou les IST": h3("Où s'adresser") + ul("Le centre de santé sexuelle (planning familial) de Neuchâtel", "Votre médecin ou gynécologue", "Un dépistage IST est possible, parfois anonyme") + h3("Bon à savoir") + para("Ces services sont confidentiels et proposent souvent des tarifs réduits."),
    "J'ai un handicap ou une maladie grave, quelles aides existent ?": h3("Déposer une demande AI") + ol("Contactez l'Office AI du canton de Neuchâtel.", "Déposez une demande dès que votre santé limite votre travail (les délais sont longs).", "Un-e assistant-e social-e peut vous aider à monter le dossier.") + h3("Ce que l'AI peut faire") + ul("Mesures de réadaptation pour rester actif", "Rente si le travail n'est plus possible", "Moyens auxiliaires (aides techniques)"),
    "J'ai des problèmes avec l'alcool, les drogues ou le jeu": h3("Trouver de l'aide") + ul("Le centre d'addictologie du canton de Neuchâtel", "Votre médecin, en toute confidentialité", "Des groupes d'entraide") + h3("En cas d'urgence") + para("En cas de crise, appelez le 144, ou le 143 (La Main Tendue) pour parler à quelqu'un tout de suite."),
    # --- Money & budget ---
    "Je n'ai pas assez d'argent pour vivre": h3("Demander l'aide sociale") + ol("Prenez rendez-vous à votre Guichet social régional (GSR).", "Apportez vos justificatifs de revenus, loyer et charges.", "Le GSR calcule votre droit et vous accompagne.") + h3("Qui peut en bénéficier") + para("Toute personne dont les revenus ne couvrent pas les besoins de base, selon sa situation et son permis."),
    "Je veux ouvrir un compte bancaire": h3("Ouvrir un compte") + ol("Choisissez une banque (PostFinance et la banque cantonale sont accessibles).", "Prenez rendez-vous ou faites-le en ligne.", "Apportez pièce d'identité, permis de séjour et attestation de domicile.") + h3("Selon votre permis") + para("Avec un permis N ou F, certaines banques limitent les options ; PostFinance accepte en général un compte de base."),
    "J'ai perdu mon emploi et je veux toucher le chômage": h3("S'inscrire au chômage") + ol("Inscrivez-vous au ONE dès votre dernier jour de travail, via arbeit.swiss.", "Choisissez une caisse de chômage.", "Commencez à postuler tout de suite et gardez vos preuves.") + h3("Combien et combien de temps") + ul("70 à 80 % de votre ancien salaire", "Selon vos cotisations et votre situation familiale", "Vous devez rester disponible et chercher activement"),
    "Je ne comprends pas comment fonctionnent les impôts": h3("Savoir comment vous êtes imposé") + ul("Avec un permis B, l'impôt est souvent prélevé à la source, sur le salaire", "Avec un permis C, vous remplissez une déclaration d'impôt", "Les frontaliers ont des règles particulières") + h3("Se faire aider") + para("En cas de doute, le service des contributions du canton peut vous renseigner."),
    "Je veux comprendre la retraite en Suisse": h3("Les 3 piliers") + ul("1er pilier (AVS) : obligatoire, retraite de base", "2e pilier (LPP) : via l'employeur", "3e pilier : épargne privée, facultative") + h3("Bon à savoir") + ul("Vérifiez que vous avez un numéro AVS", "Si vous quittez la Suisse, vous pouvez récupérer une partie de vos cotisations"),
    "J'ai des dettes et je ne sais plus quoi faire": h3("Agir vite") + ol("Ne laissez pas les factures s'accumuler : contactez un service de désendettement.", "Faites la liste de vos dettes et de vos revenus.", "Un conseiller vous aide gratuitement à établir un plan.") + h3("Bon à savoir") + para("Caritas et le CSP proposent un accompagnement au désendettement, gratuit et confidentiel."),
    "Ma rente ne suffit pas pour vivre": h3("Demander des prestations complémentaires (PC)") + ol("Adressez-vous à la caisse de compensation ou à votre commune.", "Apportez vos justificatifs de rente, loyer et charges.", "Les PC complètent votre rente pour couvrir vos besoins.") + h3("Bon à savoir") + para("Ce n'est pas de l'aide sociale mais un droit lié à votre rente AVS ou AI."),
    "Je veux mieux gérer mon argent": h3("Faire un budget") + ol("Notez vos revenus et toutes vos dépenses fixes.", "Prévoyez une réserve pour les factures annuelles (assurance, impôts).", "Utilisez un outil de budget gratuit (budget conseil, applications).") + h3("Pièges à éviter") + ul("Les petits crédits et le leasing coûtent cher", "Payez d'abord l'assurance maladie et le loyer"),
    "J'ai reçu un acte de poursuite, que faire ?": h3("Réagir dès réception") + ol("Ne l'ignorez pas : vous avez 10 jours pour faire opposition si la dette est contestée.", "Si la dette est juste, contactez le créancier pour un arrangement.", "Faites-vous aider par un service de désendettement.") + h3("Bon à savoir") + para("Un acte de poursuite ne signifie ni expulsion ni arrestation. L'Office des poursuites peut vous expliquer la suite."),
    "Je n'ai pas assez à manger": h3("Où trouver de l'aide alimentaire") + ul("Caritas (épiceries à prix réduit)", "Les Cartons du cœur, sur demande", "Colis alimentaires via les associations locales") + h3("Où s'adresser") + para("Adressez-vous au GSR, à Caritas ou au CSP : ils orientent vers l'aide la plus proche, en toute discrétion."),
    # --- Education ---
    "Je veux apprendre le français": h3("Trouver un cours") + ol("Contactez le COSM ou une association (RECIF, Caritas).", "Faites évaluer votre niveau pour choisir le bon cours.", "Inscrivez-vous ; beaucoup de cours sont gratuits ou peu chers.") + h3("Bon à savoir") + para("Le canton peut financer une partie de vos cours via le chèque-langue."),
    "Je veux faire reconnaître mon diplôme étranger en Suisse": h3("Lancer la reconnaissance") + ol("Identifiez l'autorité compétente selon votre métier (SEFRI, CDIP, MEBEKO).", "Rassemblez vos diplômes traduits et vos relevés.", "Déposez la demande, souvent sur recognition.swiss.") + h3("Bon à savoir") + ul("La démarche peut prendre plusieurs mois", "Des mesures complémentaires (stage, examen) peuvent être demandées", "Le CNIP peut vous accompagner"),
    "Je veux obtenir un diplôme professionnel suisse": h3("Accéder au diplôme en tant qu'adulte") + ol("Renseignez-vous sur l'AFP (2 ans) et le CFC (3-4 ans).", "La validation des acquis permet parfois d'obtenir le diplôme via l'expérience.", "Contactez l'orientation professionnelle (OCOSP) ou le CNIP.") + h3("Bon à savoir") + para("Un diplôme professionnel suisse est très demandé sur le marché du travail."),
    "Je veux apprendre le français depuis chez moi": h3("Par où commencer") + ul("Applications gratuites (Duolingo, etc.) pour la base", "Cours en ligne structurés et vidéos", "Écoutez la radio et regardez la TV en français") + h3("Pour progresser vite") + para("Combinez une application avec un vrai cours et de la pratique orale."),
    "Je veux certifier mon niveau de français": h3("Passer le test FIDE") + ol("Inscrivez-vous au test FIDE en ligne (fide-info.ch).", "Choisissez un centre de test à Neuchâtel.", "Passez l'examen oral et/ou écrit selon votre besoin.") + h3("Bon à savoir") + para("Le passeport des langues FIDE peut être exigé pour le permis C ou la naturalisation."),
    "Je veux savoir si l'État peut payer mes cours de langue": h3("Demander le chèque-langue") + ol("Renseignez-vous auprès du COSM sur le chèque-langue.", "Choisissez un cours auprès d'un organisme reconnu.", "Le canton peut financer jusqu'à la moitié du coût.") + h3("Qui peut en bénéficier") + para("Les personnes migrantes domiciliées dans le canton, selon les conditions du moment."),
    "Je ne sais pas encore lire ni écrire": h3("Trouver un cours d'alphabétisation") + ol("Contactez le COSM ou une association (Lire et Écrire).", "Un cours adapté aux débutants complets vous est proposé.", "L'apprentissage se fait à votre rythme, sans jugement.") + h3("Bon à savoir") + para("C'est possible à tout âge et souvent gratuit."),
    "Je cherche des cours de langue avec des horaires flexibles": h3("Trouver un cours adapté") + ul("Cours du soir et du week-end à Neuchâtel", "Cours intensifs pour progresser vite", "Demandez au COSM la liste des organismes") + h3("Bon à savoir") + para("Certains cours mènent à une certification officielle (FIDE, DELF)."),
    "Je veux me former en ligne pour améliorer mes compétences": h3("Où se former") + ul("Plateformes gratuites (cours en ligne ouverts)", "Formations certifiantes suisses", "Tutoriels vidéo pour un métier précis") + h3("Pour réussir") + para("Fixez-vous un horaire régulier et un objectif clair (un métier, une compétence)."),
    "Je veux étudier à l'université à Neuchâtel": h3("S'inscrire") + ol("Choisissez entre l'Université de Neuchâtel (UniNE) et la HE-Arc.", "Vérifiez l'admission : diplômes reconnus et niveau de français exigé.", "Déposez votre dossier avant le délai d'inscription.") + h3("Aides financières") + para("Des bourses cantonales existent selon votre situation ; renseignez-vous au service des bourses."),
    # --- Children & family ---
    "Je veux recevoir les allocations pour mes enfants": h3("Demander les allocations") + ol("La demande passe en général par votre employeur (caisse d'allocations familiales).", "Si vous ne travaillez pas, adressez-vous à la caisse cantonale.", "Fournissez les actes de naissance des enfants.") + h3("Ce que vous recevez") + para("Un montant par enfant chaque mois, plus élevé pour les enfants en formation."),
    "Je veux inscrire mon enfant à l'école": h3("Inscrire votre enfant") + ol("Adressez-vous au service scolaire de votre commune.", "Apportez pièce d'identité, permis et carnet de vaccination.", "L'école indique la classe et la date de rentrée.") + h3("Bon à savoir") + ul("L'école est gratuite et obligatoire dès 4 ans", "Des classes d'accueil aident les enfants qui débutent en français"),
    "Je cherche une place en crèche pour mon enfant": h3("Trouver une place") + ol("Inscrivez-vous tôt : les places sont limitées.", "Contactez les crèches de votre commune ou le guichet de l'accueil de l'enfance.", "Demandez si vous avez droit à un tarif réduit.") + h3("Aide financière") + para("Le tarif dépend souvent de vos revenus : une réduction est possible."),
    "Mon enfant a besoin d'aide pour apprendre le français à l'école": h3("Demander un soutien") + ol("Parlez-en à l'enseignant-e ou à la direction de l'école.", "Votre enfant peut rejoindre une classe ou un cours d'accueil.", "Un appui individualisé peut être mis en place.") + h3("En dehors de l'école") + para("Des associations proposent du soutien scolaire et de l'aide aux devoirs."),
    "Je cherche une garde pour mes enfants avant ou après l'école": h3("Inscrire au parascolaire") + ol("Renseignez-vous auprès de l'école ou de la commune.", "Choisissez les moments : matin, midi (repas), après-midi.", "Inscrivez-vous ; le tarif dépend souvent des revenus.") + h3("Bon à savoir") + para("Le parascolaire permet de concilier travail, cours et vie de famille."),
    "Je cherche des activités pour mes enfants pendant les vacances": h3("Trouver des activités") + ul("Camps et colonies de la commune et des associations", "Activités sportives et culturelles à prix réduit", "Demandez le programme des vacances à votre commune") + h3("Aide financière") + para("Des réductions existent pour les familles à budget modeste."),
    "Je veux connaître mes droits lors d'une naissance": h3("Vos droits") + ul("Congé maternité : 14 semaines, 80 % du salaire", "Congé paternité : 2 semaines", "Allocations familiales dès la naissance") + h3("Les démarches") + para("L'employeur s'occupe des allocations perte de gain (APG) ; annoncez la naissance à votre commune et à votre caisse."),
    # --- Rights & duties ---
    "Je ne comprends pas les différents permis de séjour": h3("Comprendre votre permis") + ul("N : demande d'asile en cours", "F : admission provisoire", "S : statut de protection", "B : séjour ; C : établissement ; L : courte durée") + h3("Renouvellement") + para("Surveillez la date de validité et renouvelez à temps auprès du Service des migrations (SMIG)."),
    "J'ai besoin d'aide juridique gratuite": h3("Où consulter") + ul("Le Centre social protestant (CSP) et Caritas", "Les permanences juridiques associatives", "Les services d'aide juridique pour les questions de migration") + h3("Bon à savoir") + para("Expliquez votre situation clairement et apportez tous vos documents (permis, courriers)."),
    "Je veux comprendre la procédure d'asile": h3("Les grandes étapes") + ol("Enregistrement dans un centre fédéral et audition.", "Décision du Secrétariat d'État aux migrations (SEM).", "En cas de refus, un recours est possible dans un délai court.") + h3("Vos droits pendant la procédure") + ul("Hébergement et aide de base", "Accès aux soins d'urgence", "Aide juridique gratuite pour la procédure"),
    "Je veux faire venir ma famille en Suisse": h3("Faire la demande de regroupement") + ol("Vérifiez que votre permis autorise le regroupement familial.", "Prouvez un logement adéquat et des revenus suffisants.", "Déposez la demande au Service des migrations (SMIG).") + h3("Bon à savoir") + para("Des délais s'appliquent selon votre permis : ne tardez pas, un conseil juridique est utile."),
    "Je veux devenir citoyen suisse": h3("Préparer votre demande") + ol("Vérifiez les années de résidence exigées (Suisse et canton).", "Réunissez les preuves d'intégration (langue, autonomie financière).", "Déposez la demande auprès de votre commune.") + h3("Bon à savoir") + para("La naturalisation demande du temps ; le niveau de français et le respect des lois sont examinés."),
    "Je veux passer du permis B au permis C": h3("Demander le permis C") + ol("Vérifiez la durée de séjour requise (5 ou 10 ans selon votre nationalité).", "Montrez votre intégration (langue, pas de dettes ni d'aide sociale).", "Déposez la demande au Service des migrations (SMIG).") + h3("Bon à savoir") + para("Le permis C n'a plus besoin d'être renouvelé chaque année et donne plus de droits."),
    "Je veux voter aux élections à Neuchâtel": h3("S'inscrire pour voter") + ol("Vérifiez que vous avez 5 ans de résidence dans le canton.", "Inscrivez-vous sur les listes électorales à votre commune.", "Vous recevrez le matériel de vote à la maison.") + h3("Bon à savoir") + para("À Neuchâtel, les personnes étrangères peuvent voter au niveau communal et cantonal."),
    "Je divorce, est-ce que ça change mon droit de séjour ?": h3("Vérifier votre situation") + ol("Renseignez-vous vite : un divorce peut affecter un permis lié au conjoint.", "Rassemblez les preuves de votre intégration et de vos années de séjour.", "Demandez un conseil juridique avant toute démarche.") + h3("Bon à savoir") + para("Après plusieurs années de mariage et une bonne intégration, le maintien du permis est souvent possible."),
    "J'ai été victime de discrimination": h3("Que faire") + ol("Notez les faits (date, lieu, témoins).", "Contactez un centre de conseil contre le racisme et la discrimination.", "Selon la situation, une plainte ou une médiation est possible.") + h3("Bon à savoir") + para("La discrimination est illégale ; vous avez le droit de vous défendre et d'être accompagné-e."),
    "Je dois obtenir un document d'état civil (acte de naissance, mariage)": h3("Obtenir le document") + ol("Demandez l'acte à l'état civil de votre pays d'origine.", "Faites-le traduire et, si besoin, légaliser (apostille).", "Remettez-le à l'autorité suisse qui le demande.") + h3("Si c'est difficile") + para("En cas de blocage (documents introuvables), demandez conseil au Service des migrations ou à une association."),
    "Je viens d'arriver, je dois m'inscrire à ma commune": h3("S'annoncer à la commune") + ol("Rendez-vous au contrôle des habitants dans les 14 jours.", "Apportez pièce d'identité, permis ou visa et contrat de bail.", "Vous recevez une attestation de domicile.") + h3("Bon à savoir") + para("Cette inscription donne accès à la plupart des autres démarches (assurance, école, banque)."),
    # --- Housing ---
    "Je n'ai pas de logement, j'ai besoin d'aide": h3("Qui appeler ce soir") + ul("Contactez l'Armée du Salut ou une structure d'hébergement d'urgence", "Demandeurs d'asile : adressez-vous à votre structure d'accueil", "En dernier recours, le GSR peut accorder une aide d'urgence") + h3("Bon à savoir") + para("N'attendez pas la dernière minute : appelez dans la journée pour avoir une place."),
    "Je veux connaître mes droits en tant que locataire": h3("Vos droits de base") + ul("Le loyer et les charges doivent être clairs dans le bail", "Le propriétaire ne peut pas augmenter le loyer sans respecter des règles", "La résiliation suit des délais précis") + h3("En cas de problème") + para("L'ASLOCA (association des locataires) conseille et défend les locataires, pour une petite cotisation."),
    "Je cherche un appartement à louer": h3("Où chercher") + ul("Sites : homegate.ch, immoscout24.ch, flatfox.ch", "Régies immobilières locales", "Bouche-à-oreille et panneaux de quartier") + h3("Préparer votre dossier") + ul("Pièce d'identité et permis", "Attestation de l'Office des poursuites", "3 dernières fiches de salaire"),
    "Je ne comprends pas le dépôt de garantie": h3("Payer le dépôt") + ol("Le dépôt vaut au maximum 3 mois de loyer.", "Il doit être versé sur un compte bloqué à votre nom.", "Ne le versez jamais en liquide au propriétaire.") + h3("Le récupérer") + para("À la fin du bail, le dépôt vous est rendu si le logement est rendu en bon état."),
    "Je cherche un logement à loyer réduit": h3("Demander un logement social") + ol("Renseignez-vous auprès de votre commune sur les logements subventionnés.", "Vérifiez les conditions de revenu.", "Inscrivez-vous sur la liste d'attente.") + h3("Bon à savoir") + para("Les places sont limitées : inscrivez-vous tôt et relancez régulièrement."),
    "Je dois prendre une assurance pour mon appartement": h3("Souscrire une assurance ménage") + ol("Comparez les offres (assurance ménage + responsabilité civile).", "Choisissez une couverture adaptée à la valeur de vos biens.", "Le propriétaire demande souvent une attestation RC.") + h3("Ce que ça couvre") + para("Vos biens en cas de vol, incendie ou dégât d'eau, et les dommages que vous causez à autrui."),
    # --- Integration ---
    "Je viens d'arriver, que peut faire le COSM pour moi ?": h3("Prendre contact avec le COSM") + ol("Contactez le COSM (Cohésion sociale et multiculturalité).", "Expliquez votre situation : langue, travail, démarches.", "Le COSM vous informe et vous oriente gratuitement.") + h3("Ce qu'ils proposent") + ul("Séances d'information à l'arrivée", "Orientation vers les cours de français", "Appui pour les démarches administratives"),
    "Je suis une femme migrante, je cherche du soutien": h3("Rejoindre le RECIF") + ol("Contactez le RECIF à Neuchâtel.", "Participez aux cours de français et aux activités.", "Demandez de l'aide pour vos démarches administratives.") + h3("Ce qu'ils proposent") + ul("Cours de français avec garde d'enfants", "Rencontres et ateliers entre femmes", "Accompagnement individuel"),
    "Je veux rencontrer des gens et m'intégrer": h3("Où rencontrer des gens") + ul("Rejoignez une association, un club de sport ou une maison de quartier", "Faites du bénévolat", "Participez aux activités du COSM et aux fêtes de quartier") + h3("Bon à savoir") + para("Parler avec les gens est la meilleure façon de progresser en français et de se sentir chez soi."),
    "Je veux comprendre les règles de vie en Suisse": h3("Règles de bon voisinage") + ul("Silence en général de 22h à 7h et le dimanche", "Trier ses déchets et respecter les jours de ramassage", "Utiliser la buanderie selon le planning") + h3("Au quotidien") + ul("La ponctualité est importante", "On prend rendez-vous avant de passer chez les gens"),
    "Je ne parle pas encore le français, j'ai besoin d'un interprète": h3("Demander un interprète") + ol("Prévenez le service (médecin, école, administration) que vous avez besoin d'un interprète.", "Le COSM peut fournir un-e interprète communautaire.", "Pour l'urgent, des services d'interprétariat par téléphone existent.") + h3("Bon à savoir") + para("Un interprète est souvent gratuit pour les rendez-vous médicaux et sociaux."),
    "Je veux apprendre à utiliser un ordinateur ou Internet": h3("Trouver un cours") + ol("Renseignez-vous au COSM ou dans une bibliothèque.", "Inscrivez-vous à un cours débutant, souvent gratuit.", "Apprenez les bases : e-mail, recherche, démarches en ligne.") + h3("S'entraîner") + para("Les bibliothèques et espaces publics numériques prêtent des ordinateurs et aident gratuitement."),
    # --- Mobility ---
    "Je veux utiliser les transports en commun": h3("Voyager en train et en bus") + ol("Achetez vos billets aux automates, aux guichets ou sur l'app CFF.", "Pour voyager souvent, prenez un abonnement (Onde Verte, demi-tarif).", "Ayez toujours un billet valable avant de monter.") + h3("Économiser") + ul("Abonnement demi-tarif pour toute la Suisse", "Billets dégriffés et offres pour jeunes et familles"),
    "Je veux échanger mon permis de conduire étranger": h3("Échanger votre permis") + ol("Faites la demande au Service des automobiles (SCAN) dans les 12 mois.", "Apportez votre permis étranger, une pièce d'identité et une photo.", "Selon le pays, un examen peut être demandé.") + h3("Bon à savoir") + para("Après 12 mois, l'échange devient plus compliqué : ne tardez pas."),
    "Je veux me déplacer à vélo à Neuchâtel": h3("Rouler à vélo") + ul("PubliBike : vélos en libre-service en ville", "Respectez le code de la route et les pistes cyclables", "Lumières obligatoires la nuit") + h3("Bon à savoir") + para("Un casque est fortement conseillé, et une assurance responsabilité civile couvre les accidents."),
    "J'ai du mal à me déplacer pour mes rendez-vous médicaux": h3("Trouver un transport") + ul("La Croix-Rouge propose un service de transport bénévole", "Le transport médical peut être remboursé s'il est prescrit", "Renseignez-vous auprès de votre caisse maladie") + h3("En cas d'urgence") + para("Pour une urgence, appelez le 144 ; ne renoncez pas à vous soigner faute de transport."),
    "J'ai une voiture, que dois-je faire en Suisse ?": h3("Les démarches obligatoires") + ol("Souscrivez une assurance responsabilité civile (RC) — obligatoire.", "Immatriculez la voiture au Service des automobiles (SCAN) et obtenez des plaques NE.", "Passez le contrôle technique quand il est demandé.") + h3("Bon à savoir") + para("Rouler sans assurance ou sans plaques valables entraîne de fortes amendes."),
    # --- Démo (invité) ---
    "Atelier conversation français (Caritas)": h3("Participer à l'atelier") + ol("Venez sans inscription au jour indiqué.", "C'est gratuit et ouvert à tous les niveaux.", "Apportez juste de la motivation pour parler.") + h3("Bon à savoir") + para("C'est un moment convivial pour pratiquer l'oral et rencontrer des gens."),
}


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
                'why_interesting': (
                    para("L'ORP (Office Régional de Placement) s'appelle ONE à Neuchâtel. C'est le service public qui aide les personnes sans emploi à trouver un travail.")
                    + para("Si vous avez travaillé en Suisse et cotisé à l'assurance chômage, vous pouvez aussi recevoir des indemnités, de l'argent chaque mois pendant votre recherche.")
                ),
                'how_to': (
                    h3("Qui peut s'inscrire")
                    + ul(
                        "Vous avez travaillé en Suisse et cotisé à l'assurance chômage",
                        "Vous avez un permis de séjour valide (B, C, ou parfois L)",
                        "Vous êtes disponible pour travailler tout de suite",
                    )
                    + h3("Les étapes")
                    + ol(
                        "Inscrivez-vous dès le premier jour sans emploi, n'attendez pas",
                        "En ligne sur <a href='https://www.arbeit.swiss'>arbeit.swiss</a> (24h/24)",
                        "L'ONE vous contacte dans les 24 à 48 heures pour un rendez-vous",
                        "Inscrivez-vous aussi à une caisse de chômage",
                        "Envoyez 8 à 12 candidatures par mois et gardez une preuve de chaque envoi",
                    )
                    + h3("Documents à apporter")
                    + ul(
                        "Carte d'identité ou passeport + permis de séjour",
                        "Numéro AVS (votre numéro d'assurance sociale suisse)",
                        "Attestation du dernier employeur et certificats de travail",
                        "CV à jour",
                    )
                ),
                'location': (
                    h3("ONE Neuchâtel (ville)")
                    + ul(
                        "<b>Adresse :</b> Avenue Edouard-Dubois 20, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 889 68 18",
                        "<b>Email :</b> one@ne.ch",
                        "<b>Sur rendez-vous</b> (pris après inscription en ligne)",
                    )
                    + h3("ONE La Chaux-de-Fonds")
                    + ul(
                        "<b>Adresse :</b> Espacité 1, 2302 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 889 69 00",
                        "<b>Email :</b> one@ne.ch",
                    )
                ),
                'body': body(
                    sec("À quoi ça sert",
                        para("L'ORP (Office Régional de Placement) s'appelle ONE à Neuchâtel. C'est le service public qui aide les personnes sans emploi à trouver un travail."),
                        para("Si vous avez travaillé en Suisse et cotisé à l'assurance chômage, vous pouvez aussi recevoir des indemnités de chômage, de l'argent chaque mois pendant votre recherche."),
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
                            "Inscrivez-vous dès le premier jour sans emploi, ne pas attendre",
                            "En ligne sur <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a> (disponible 24h/24)",
                            "L'ONE vous contacte dans les 24 à 48 heures pour un rendez-vous",
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
                        "<b>Téléphone :</b> lun à ven 8h à 12h / lun à jeu 13h30 à 17h",
                    ), width='half'),
                    sec("ONE La Chaux-de-Fonds", ul(
                        "<b>Adresse :</b> Espacité 1, 2302 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 889 69 00",
                        "<b>Email :</b> one@ne.ch",
                        "<b>Inscription :</b> <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a>",
                        "<b>Caisse chômage (CCNAC) :</b> Espacité 4, CDF, 032 889 67 90",
                    ), width='half'),
                ),
            },

            {
                'name': "Je veux préparer un CV pour trouver du travail en Suisse",
                'description': "Le CV suisse a des règles différentes. Je dois savoir quoi mettre et comment le présenter pour avoir des chances.",
                'tags': ['CV candidature', 'Recherche emploi', 'Travail', 'Formation'],
                'audiences': ['Nouveaux arrivants', "Établis depuis plus d'un an", 'Jeune adulte'],
                'why_interesting': para("Le CV suisse a ses propres règles. Bien le présenter augmente vos chances d'être contacté par un employeur."),
                'how_to': (
                    h3("Le CV suisse, ce qui est différent")
                    + ul(
                        "Maximum 2 pages (1 page si moins de 10 ans d'expérience)",
                        "Photo professionnelle recommandée (fond neutre)",
                        "Pas d'état civil ni de religion",
                        "Ordre antichronologique : le plus récent en premier",
                        "Langues : indiquez votre niveau (A1 à C2)",
                    )
                ),
                'location': ul(
                    "<b>CV gratuit en ligne :</b> <a href='https://www.arbeit.swiss'>arbeit.swiss</a>",
                    "<b>Aide à la rédaction :</b> votre conseiller ONE",
                ),
                'body': body(
                    sec("Le CV suisse, ce qui est différent",
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
                            "Résumé professionnel (3 à 4 lignes)",
                            "Expériences professionnelles (avec dates et lieu)",
                            "Formation et diplômes",
                            "Compétences et langues",
                            "Références (sur demande ou avec noms et contacts)",
                        ),
                    ),
                    sec("Aide gratuite à Neuchâtel",
                        ul(
                            "<b>ONE Neuchâtel :</b> ateliers CV et simulation d'entretien, demandez à votre conseiller",
                            "<b>COSM :</b> accompagnement à la recherche d'emploi, 032 889 74 42",
                            "<b>CNIP :</b> bilan de compétences et réorientation, <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a>",
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
                        para("En Suisse, travailler à son compte est possible avec un permis B ou C. Avec un permis N ou F, c'est plus compliqué, renseignez-vous d'abord auprès du SMIG (Service des migrations de Neuchâtel)."),
                    ),
                    sec("Les étapes principales",
                        ol(
                            "Choisir votre forme juridique : raison individuelle (la plus simple), Sàrl ou SA",
                            "S'annoncer à la Caisse cantonale neuchâteloise de compensation (CCNC), obligatoire",
                            "Inscrire votre entreprise au Registre du Commerce si chiffre d'affaires > CHF 100 000/an",
                            "S'immatriculer à la TVA si chiffre d'affaires > CHF 100 000/an",
                        ),
                    ),
                    sec("CCNC, Caisse cantonale", ul(
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
                            "Tout contrat peut être oral, mais exigez toujours un contrat écrit",
                            "Le contrat doit mentionner : salaire, durée de travail, délai de congé",
                            "Les conventions collectives de travail (CCT) fixent des minimums dans chaque branche",
                            "En Suisse, il n'y a pas de salaire minimum légal national, sauf dans les cantons et branches qui en ont un",
                        ),
                    ),
                    sec("Congés et absences",
                        ul(
                            "<b>Vacances :</b> minimum 4 semaines par an (5 semaines si moins de 20 ans)",
                            "<b>Jours fériés officiels NE :</b> 1er janvier, Vendredi saint, 1er août, Noël, vérifiez la liste complète sur ne.ch",
                            "<b>Maladie :</b> vous avez droit au salaire pendant votre arrêt maladie (selon l'ancienneté)",
                            "<b>Accident :</b> couvert par l'assurance accidents obligatoire (LAA) de votre employeur",
                        ),
                    ),
                    sec("En cas de licenciement",
                        ul(
                            "Délai de congé minimum : 1 mois (1re année), 2 mois (2e à 9e année), 3 mois ensuite",
                            "Licenciement immédiat sans cause valable = droit à une indemnité",
                            "Licenciement abusif : recours possible devant le tribunal",
                        ),
                    ),
                    sec("Aide à Neuchâtel", ul(
                        "<b>Unia Neuchâtel :</b> syndicat, conseil juridique gratuit pour les membres, <a href='https://www.unia.ch' target='_blank'>unia.ch</a>",
                        "<b>Syna :</b> syndicat chrétien-social, <a href='https://www.syna.ch' target='_blank'>syna.ch</a>",
                        "<b>FER (Fédération patronale) :</b> pour vérifier les CCT de votre branche, <a href='https://www.fer-ne.ch' target='_blank'>fer-ne.ch</a>",
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
                            "Vous êtes employé par l'agence, elle paie votre salaire et vos cotisations",
                            "Vous travaillez chez une entreprise cliente",
                            "Les missions durent de quelques jours à plusieurs mois",
                            "Vous avez les mêmes droits qu'un employé ordinaire (LAA, LAMal, etc.)",
                        ),
                    ),
                    sec("Agences présentes à Neuchâtel", ul(
                        "<b>Adecco :</b> <a href='https://www.adecco.ch' target='_blank'>adecco.ch</a>, bureau à Neuchâtel et La Chaux-de-Fonds",
                        "<b>Manpower :</b> <a href='https://www.manpower.ch' target='_blank'>manpower.ch</a>",
                        "<b>Randstad :</b> <a href='https://www.randstad.ch' target='_blank'>randstad.ch</a>",
                        "<b>Kelly Services :</b> spécialisé IT et industrie, <a href='https://www.kellyservices.ch' target='_blank'>kellyservices.ch</a>",
                        "<b>Temporis :</b> réseau de franchises locales, <a href='https://www.temporis.ch' target='_blank'>temporis.ch</a>",
                    ), width='half'),
                    sec("Conseils", ul(
                        "Inscrivez-vous dans plusieurs agences en même temps",
                        "Apportez : CV, permis de séjour, certificats de travail",
                        "Précisez votre disponibilité, vos langues et votre secteur",
                        "Les agences sont gratuites pour les candidats, méfiez-vous si on vous demande de l'argent",
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
                            "Il n'y a pas de salaire minimum national légal, mais de nombreux secteurs ont des minimums fixés par des <b>conventions collectives de travail (CCT)</b>",
                            "Le salaire est souvent mensuel, versé fin de mois ou le 25",
                            "Votre fiche de salaire doit détailler : salaire brut, cotisations AVS/AI/AC, impôt à la source, salaire net",
                            "<b>13e salaire :</b> fréquent en Suisse, versé en décembre ou moitié juillet / moitié décembre",
                        ),
                    ),
                    sec("Trouver la CCT de votre secteur",
                        ul(
                            "<b>Hôtellerie-restauration (GAV) :</b> <a href='https://www.l-gav.ch' target='_blank'>l-gav.ch</a>, salaire min. env. CHF 3 600/mois",
                            "<b>Nettoyage :</b> CCT nettoyage, env. CHF 3 700/mois",
                            "<b>Construction :</b> CCT construction, renseignez-vous à Unia",
                            "<b>Toutes les CCT :</b> <a href='https://www.seco.admin.ch/cct' target='_blank'>seco.admin.ch/cct</a>",
                        ),
                    ),
                    sec("Si vous pensez être sous-payé", ul(
                        "<b>Unia Neuchâtel :</b> syndicat, consultation gratuite, <a href='https://www.unia.ch' target='_blank'>unia.ch</a>",
                        "<b>Syna :</b> autre syndicat, <a href='https://www.syna.ch' target='_blank'>syna.ch</a>",
                        "<b>Inspection du travail NE :</b> peut contrôler le respect des CCT, <a href='https://www.ne.ch/inspection-travail' target='_blank'>ne.ch/inspection-travail</a>",
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
                            "<b>Neuchâtel :</b> Rue de la Maladière 28, 032 889 65 50",
                            "<b>La Chaux-de-Fonds :</b> Rue du Commerce 7, 032 889 64 46",
                        ),
                    ),
                    sec("Autres ressources", ul(
                        "<b>Berufsberatung.ch :</b> base de données de tous les métiers suisses, salaires, formations, <a href='https://www.berufsberatung.ch/fr' target='_blank'>berufsberatung.ch</a>",
                        "<b>CNIP :</b> bilan de compétences pour adultes avec expérience à l'étranger, 032 889 69 25",
                        "<b>ONE (ORP) :</b> votre conseiller ONE peut vous orienter si vous êtes inscrit au chômage",
                    ), width='half'),
                    sec("Tester un métier avant de se lancer", ul(
                        "Demandez à votre ONE un stage d'observation (<i>Schnupperlehre</i>) en entreprise",
                        "Durée : 1 à 5 jours, gratuit, permet de découvrir un métier concrètement",
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
                        para("En Suisse, beaucoup de postes ne sont jamais publiés sur des sites d'emploi, ils sont pourvus par le réseau. LinkedIn est le réseau professionnel le plus utilisé. Un profil complet augmente vraiment vos chances."),
                    ),
                    sec("Créer votre profil",
                        ul(
                            "<b>Photo :</b> professionnelle, fond neutre, obligatoire (profils sans photo sont moins consultés)",
                            "<b>Titre :</b> votre métier ou ce que vous cherchez (ex: 'Infirmière | Cherche poste canton NE')",
                            "<b>Résumé :</b> 3 à 5 lignes sur votre parcours et ce que vous apportez",
                            "<b>Expériences :</b> même à l'étranger, décrivez vos tâches en français",
                            "<b>Compétences :</b> ajoutez-en au moins 10, vos connexions peuvent les valider",
                        ),
                    ),
                    sec("Utiliser votre réseau", ul(
                        "Connectez-vous avec vos anciens collègues, voisins, membres d'associations",
                        "Rejoignez des groupes LinkedIn de votre secteur en Suisse romande",
                        "<b>COSM :</b> peut vous mettre en contact avec des personnes de votre communauté travaillant localement",
                        "Demandez des recommandations à vos anciens employeurs ou bénévoles",
                    ), width='half'),
                    sec("Plateformes d'emploi complémentaires", ul(
                        "<a href='https://www.jobs.ch' target='_blank'>jobs.ch</a>, le plus utilisé en Suisse",
                        "<a href='https://www.indeed.ch' target='_blank'>indeed.ch</a>",
                        "<a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a>, portail officiel du SECO",
                        "<a href='https://www.jobup.ch' target='_blank'>jobup.ch</a>, spécialiste Suisse romande",
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
                        "<b>Vendanges (septembre à octobre) :</b> Neuchâtel, Valais, Vaud, pas toujours besoin d'expérience",
                        "<b>Hôtellerie et restauration :</b> toute l'année, surtout été et hiver (stations de ski)",
                        "<b>Agriculture (été) :</b> récolte de fruits et légumes, travaux maraîchers",
                        "<b>Bâtiment :</b> printemps à automne, souvent via agences d'intérim",
                    )),
                    sec("Comment chercher", ul(
                        "<b>Agrijob :</b> plateforme dédiée à l'agriculture, <a href='https://www.agrijob.ch' target='_blank'>agrijob.ch</a>",
                        "<b>Gastrojob :</b> hôtellerie et restauration, <a href='https://www.gastrojob.ch' target='_blank'>gastrojob.ch</a>",
                        "<b>Saisonnier.ch :</b> offres saisonnières toutes régions, <a href='https://www.saisonnier.ch' target='_blank'>saisonnier.ch</a>",
                        "<b>ONE Neuchâtel :</b> votre conseiller peut vous signaler des offres locales, 032 889 68 18",
                        "<b>Agences d'intérim :</b> Adecco, Manpower, souvent des missions courtes dans l'industrie",
                    ), width='half'),
                    sec("Conditions importantes", ul(
                        "Vérifiez que votre permis autorise le travail (permis N : possible après 3 mois sous conditions)",
                        "Le contrat de travail doit être signé avant de commencer, même pour une semaine",
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
                        "<b>Benevol Neuchâtel :</b> plateforme officielle, <a href='https://www.benevolat-ne.ch' target='_blank'>benevolat-ne.ch</a>",
                        "<b>Croix-Rouge NE :</b> bénévoles toujours recherchés, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Caritas NE :</b> ateliers de français, aide alimentaire, 032 886 80 70",
                        "<b>Maisons de quartier Neuchâtel :</b> activités variées, demandez au COSM",
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
                            "Toutes les caisses doivent vous accepter, elles ne peuvent pas refuser",
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
                            "<b>Adulte :</b> environ CHF 370 à 430/mois selon la caisse et la franchise",
                            "<b>Enfant :</b> environ CHF 90 à 130/mois",
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
                        "<b>Téléphone :</b> lun à ven 8h30 à 12h",
                    ), width='half'),
                    sec("GSR La Chaux-de-Fonds", ul(
                        "<b>Adresse :</b> Rue du Collège 11, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 967 67 31",
                        "<b>OCAB (suivi dossier) :</b> Rue de Tivoli 28, 2002 Neuchâtel, 032 889 66 30",
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
                        para("Trouver un médecin peut prendre du temps, commencez dès votre arrivée."),
                    ),
                    sec("Comment chercher",
                        ol(
                            "Cherchez sur <a href='https://doctorfmh.ch/fr/' target='_blank'>doctorfmh.ch</a>, le registre officiel de tous les médecins suisses",
                            "Prenez rendez-vous en ligne sur <a href='https://www.onedoc.ch' target='_blank'>onedoc.ch</a>",
                            "Appelez directement les cabinets proches de chez vous",
                            "Demandez à votre entourage ou au COSM",
                        ),
                    ),
                    sec("Si vous ne trouvez pas de médecin", ul(
                        "<b>HNE, Hôpital Neuchâtelois :</b> consultations sans médecin attitré possible aux urgences",
                        "<b>Urgences HNE Neuchâtel :</b> Rue de la Maladière 45, 2000 Neuchâtel, 032 713 31 31",
                        "<b>Urgences HNE La Chaux-de-Fonds :</b> Rue de Chasseral 20, 032 967 28 28",
                        "Votre pharmacie peut aussi vous orienter vers un médecin disponible",
                    ), width='half'),
                    sec("Annuaires utiles", ul(
                        "<a href='https://doctorfmh.ch/fr/' target='_blank'>doctorfmh.ch</a>, registre FMH officiel",
                        "<a href='https://www.onedoc.ch' target='_blank'>onedoc.ch</a>, prise de RDV en ligne",
                        "<a href='https://www.comparis.ch/gesundheit/arzt' target='_blank'>comparis.ch</a>, par caisse maladie",
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
                            "<b>144</b>, Ambulance. Gratuit, 24h/24",
                            "<b>117</b>, Police. Gratuit, 24h/24",
                            "<b>118</b>, Pompiers. Gratuit, 24h/24",
                            "<b>112</b>, Numéro européen d'urgence",
                            "<b>145</b>, Toxicocentre (empoisonnement). Gratuit, 24h/24",
                            "<b>143</b>, La Main Tendue (soutien psychologique). Gratuit, 24h/24",
                        ),
                    ),
                    sec("Hôpitaux à Neuchâtel (HNE)", ul(
                        "<b>Neuchâtel :</b> Rue de la Maladière 45, 032 713 31 31",
                        "<b>La Chaux-de-Fonds :</b> Rue de Chasseral 20, 032 967 28 28",
                        "<b>Pourtalès (Neuchâtel) :</b> Rue de la Maladière 45, urgences 032 713 31 31",
                        "<b>Site HNE :</b> <a href='https://www.h-ne.ch' target='_blank'>h-ne.ch</a>",
                    ), width='half'),
                    sec("Garde médicale de nuit", ul(
                        "<b>Médecin de garde :</b> appelez le 032 713 31 31 (HNE) pour savoir qui est de garde",
                        "<b>Pharmacies de garde :</b> <a href='https://www.pharmaguard.ch' target='_blank'>pharmaguard.ch</a>",
                        "Votre caisse maladie a un numéro de conseil médical gratuit (24h/24), vérifiez votre carte d'assuré",
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
                        para("Arriver dans un nouveau pays est difficile. Stress, tristesse, anxiété, c'est normal. Des professionnels peuvent vous aider, souvent gratuitement et avec un interprète."),
                    ),
                    sec("Où trouver de l'aide à Neuchâtel", ul(
                        "<b>HNE, Psychiatrie :</b> consultations sur rendez-vous via médecin traitant, <a href='https://www.h-ne.ch' target='_blank'>h-ne.ch</a>",
                        "<b>COSM :</b> peut vous orienter vers un soutien psychosocial et fournir un interprète, 032 889 74 42",
                        "<b>CSP Neuchâtel :</b> accompagnement social pour réfugiés, 032 886 91 00",
                        "<b>Caritas Neuchâtel :</b> soutien et groupes de parole, <a href='https://caritas-regio.ch/neuchatel' target='_blank'>caritas-regio.ch</a>",
                    ), width='half'),
                    sec("Lignes d'écoute", ul(
                        "<b>La Main Tendue :</b> 143, écoute anonyme, gratuit, 24h/24, en français",
                        "<b>Pro Juventute (jeunes) :</b> 147, gratuit, 24h/24",
                        "<b>Centre LAVI NE :</b> 032 889 51 00, victimes de violence",
                        "<b>Dargebotene Hand :</b> 143, plusieurs langues disponibles",
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
                        "<b>Maternité HNE :</b> Rue de la Maladière 45, 2000 Neuchâtel, 032 713 31 31",
                        "<b>Sages-femmes indépendantes :</b> <a href='https://www.sage-femme.ch' target='_blank'>sage-femme.ch</a>",
                        "<b>PMI / Consultation de nourrissons :</b> renseignez-vous à votre commune",
                        "<b>RECIF (soutien femmes) :</b> Rue de la Cassarde 22, Neuchâtel, <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                    ), width='half'),
                    sec("Infos pratiques", ul(
                        "<b>Congé paternité :</b> 2 semaines (depuis 2021), à prendre dans les 6 mois",
                        "<b>Allocation naissance :</b> certaines communes accordent une prime, renseignez-vous",
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
                            "<b>Enfants :</b> certaines communes proposent une aide, renseignez-vous à votre commune",
                            "Vous pouvez souscrire une assurance complémentaire dentaire (env. CHF 20 à 50/mois)",
                        ),
                    ),
                    sec("Trouver un dentiste à Neuchâtel",
                        ul(
                            "Cherchez sur <a href='https://www.sso.ch/fr/trouvez-un-dentiste' target='_blank'>sso.ch</a>, annuaire officiel de la Société suisse d'odontologie",
                            "Demandez à votre entourage ou au COSM",
                            "<b>HNE :</b> urgences dentaires en dehors des heures de bureau, 032 713 31 31",
                        ),
                    ),
                    sec("Si vous n'avez pas les moyens", ul(
                        "<b>ASLOCA / CSP :</b> peuvent orienter vers des dentistes pratiquant des tarifs sociaux",
                        "<b>Cliniques dentaires des Hautes Écoles :</b> tarifs réduits (HE-Arc Santé à NE)",
                        "<b>GSR :</b> peut parfois aider à financer des soins urgents dans le cadre de l'aide sociale",
                        "<b>Caritas NE :</b> 032 886 80 70, renseignez-vous sur les aides disponibles",
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
                            "<b>Urgences HNE Neuchâtel :</b> Rue de la Maladière 45, 032 713 31 31, pour les cas urgents uniquement",
                            "<b>Permanence médicale :</b> demandez à votre caisse maladie s'il existe une permanence agréée proche de chez vous",
                            "<b>Pharmacie :</b> le pharmacien peut traiter de nombreux problèmes courants (rhume, douleurs légères, pansements) sans RDV",
                        ),
                    ),
                    sec("Consultation téléphonique ou vidéo", ul(
                        "<b>Medi24 :</b> service médical 24h/24 inclus dans certaines caisses maladie, vérifiez votre carte d'assuré",
                        "<b>Medgate :</b> même principe, inclus dans certains modèles d'assurance (Telmed, HMO)",
                        "Ces services peuvent vous prescrire des ordonnances et décider si une visite est nécessaire",
                        "Appelez votre caisse maladie pour savoir quel service vous avez inclus",
                    ), width='half'),
                    sec("Quand aller aux urgences", ul(
                        "<b>Appelez le 144</b> si c'est une urgence vitale (douleur thoracique, accident, perte de connaissance)",
                        "Les urgences hospitalières ne sont pas faites pour les rhumes ou fièvres légères, préférez la permanence ou le télémédecin",
                        "<b>145</b>, Toxicocentre en cas d'ingestion d'un produit dangereux",
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
                            "<b>Rougeole, oreillons, rubéole (ROR) :</b> très important, obligatoire pour entrer dans certaines structures",
                            "<b>Tétanos, diphtérie, coqueluche :</b> rappel tous les 10 ans",
                            "<b>Hépatite B :</b> recommandé pour les adolescents et certains adultes",
                            "<b>Grippe :</b> recommandée chaque automne pour les personnes à risque",
                            "<b>COVID-19 :</b> vaccinations disponibles, renseignez-vous sur les recommandations actuelles",
                        ),
                    ),
                    sec("Où se faire vacciner à Neuchâtel", ul(
                        "<b>Votre médecin de famille :</b> la première option",
                        "<b>Pharmacies :</b> certaines vaccinent directement, appelez pour vérifier",
                        "<b>HNE :</b> 032 713 31 31, consultations vaccinales",
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
                            "<b>Centre de planning familial NE :</b> consultations gratuites ou à tarif réduit, contraception, grossesse, IST",
                            "<b>Adresse :</b> Rue des Parcs 11, 2000 Neuchâtel, 032 722 95 20",
                            "<b>HNE Gynécologie :</b> consultation sur rendez-vous, 032 713 31 31",
                            "<b>Sages-femmes indépendantes :</b> suivi grossesse, contraception, <a href='https://www.sage-femme.ch' target='_blank'>sage-femme.ch</a>",
                        ),
                    ),
                    sec("Contraception", ul(
                        "La contraception est remboursée par la LAMal jusqu'à 18 ans",
                        "Après 18 ans : à votre charge (pilule env. CHF 15 à 30/mois)",
                        "Préservatifs disponibles dans toutes les pharmacies",
                        "<b>Contraception d'urgence :</b> disponible en pharmacie sans ordonnance",
                    ), width='half'),
                    sec("Dépistage IST", ul(
                        "<b>Checkpoint NE :</b> dépistage VIH et IST, <a href='https://www.checkpoint-ne.ch' target='_blank'>checkpoint-ne.ch</a>",
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
                        "<b>Office AI NE :</b> Rue Chandigarh 2, 2000 Neuchâtel, 032 889 65 00, <a href='https://www.iv-ne.ch' target='_blank'>iv-ne.ch</a>",
                        "<b>Pro Infirmis NE :</b> conseil et accompagnement pour les personnes en situation de handicap, <a href='https://www.proinfirmis.ch' target='_blank'>proinfirmis.ch</a>",
                        "<b>Inclusion Handicap :</b> défense des droits, <a href='https://www.inclusion-handicap.ch' target='_blank'>inclusion-handicap.ch</a>",
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
                        "<b>Adresse Neuchâtel :</b> Rue de la Chapelle 4, 2000 Neuchâtel, 032 725 64 00",
                        "<b>Adresse La Chaux-de-Fonds :</b> Rue du Commerce 10, 032 913 49 00",
                        "<b>Email :</b> addiction-ne@ne.ch",
                        "<b>Site :</b> <a href='https://www.addiction-ne.ch' target='_blank'>addiction-ne.ch</a>",
                        "Consultation gratuite, sans rendez-vous pour les urgences",
                        "Aide pour alcool, drogues, jeux, écrans",
                    ), width='half'),
                    sec("Lignes d'urgence et autres aides", ul(
                        "<b>Ligne nationale alcool :</b> 0800 040 080, gratuit, 24h/24",
                        "<b>Narcotics Anonymous :</b> groupes de parole à Neuchâtel, <a href='https://www.na-switzerland.org' target='_blank'>na-switzerland.org</a>",
                        "<b>Alcooliques Anonymes :</b> <a href='https://www.alcooliquesanonymes.ch' target='_blank'>alcooliquesanonymes.ch</a>",
                        "<b>La Main Tendue :</b> 143, écoute 24h/24",
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
                        para("À Neuchâtel, c'est le GSR (Guichet Social Régional) de votre commune qui traite les demandes. Ce même guichet gère aussi les subsides LAMal et les bourses d'études, un seul endroit pour plusieurs aides."),
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
                        "<b>Permanence téléphonique :</b> lun à ven 8h30 à 12h",
                        "<b>Documents :</b> pièce d'identité, permis de séjour, relevés bancaires, contrat de bail, justificatifs de revenus",
                    ), width='half'),
                    sec("GSR La Chaux-de-Fonds", ul(
                        "<b>Adresse :</b> Rue du Collège 11, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 967 67 31",
                        "<b>Heures :</b> 9h à 12h / 14h à 17h",
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
                            "<b>Permis B ou C :</b> toutes les banques acceptent, comparez sur <a href='https://www.comparis.ch' target='_blank'>comparis.ch</a>",
                            "<b>Permis N ou F :</b> les grandes banques refusent souvent, utilisez une néobanque",
                            "<b>Néobanques :</b> <a href='https://www.neon-free.ch' target='_blank'>Neon</a>, <a href='https://www.yuh.com' target='_blank'>Yuh</a>, <a href='https://www.revolut.com' target='_blank'>Revolut</a>, inscription 100% en ligne",
                            "<b>Banque Cantonale Neuchâteloise (BCN) :</b> présente dans tout le canton, <a href='https://www.bcn.ch' target='_blank'>bcn.ch</a>",
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
                            "Avoir un permis de séjour valide (B, C, permis G pour frontaliers sous conditions)",
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
                    sec("CCNAC, Caisse neuchâteloise", ul(
                        "<b>Adresse :</b> Espacité 4, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 889 67 90",
                        "<b>Email :</b> ccnac@ne.ch",
                        "<b>Site :</b> <a href='https://ccnac.ch' target='_blank'>ccnac.ch</a>",
                        "<b>Heures :</b> lun à ven 8h30 à 11h / 13h30 à 16h",
                    ), width='half'),
                    sec("Plus d'informations", ul(
                        "<b>Guide officiel :</b> <a href='https://www.ch.ch/fr/assurances/assurance-chomage/' target='_blank'>ch.ch/chomage</a>",
                        "Vous pouvez aussi utiliser une caisse syndicale : Unia, Syna, présentes à Neuchâtel",
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
                            "<b>1er pilier (AVS/AI) :</b> obligatoire pour tous, cotisation automatique sur le salaire (5,3 %). Donne droit à une rente vieillesse.",
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
                        "<b>CCNC Neuchâtel :</b> 032 889 65 01, pour toutes questions AVS",
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
                            "Les poursuites apparaissent dans l'extrait du registre, cela nuit à votre dossier de location",
                        ),
                    ),
                    sec("Aide à Neuchâtel", ul(
                        "<b>Budget Conseil NE :</b> consultation gratuite en gestion des dettes, 032 721 30 30, <a href='https://www.budgetconseil.ch' target='_blank'>budgetconseil.ch</a>",
                        "<b>CSP Neuchâtel :</b> accompagnement social et conseil juridique, 032 886 91 00",
                        "<b>Caritas NE :</b> aide d'urgence et conseil budget, 032 886 80 70",
                        "<b>GSR :</b> peut orienter vers les bons services",
                    ), width='half'),
                    sec("Démarches utiles", ul(
                        "Faites une liste de toutes vos dettes (montant, créancier, échéance)",
                        "Contactez vos créanciers pour négocier un plan de paiement",
                        "Ne signez rien sous pression, consultez d'abord un conseiller",
                        "<b>Extrait des poursuites gratuit :</b> Office des poursuites de Neuchâtel, 032 889 67 00",
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
                        para("Les prestations complémentaires (PC) sont une aide de l'État pour les personnes dont la rente AVS ou AI est trop faible pour vivre. Elles ne sont pas une aide sociale ordinaire, c'est un droit légal."),
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
                        "<b>Délai :</b> demandez dès que possible, les PC ne sont pas rétroactives",
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
                            "<b>Assurance maladie :</b> environ CHF 370 à 430/mois pour un adulte",
                            "<b>Nourriture :</b> environ CHF 400 à 600/mois pour une personne",
                            "<b>Transports :</b> demi-tarif CFF recommandé (CHF 185/an) si vous vous déplacez souvent",
                            "<b>Épargne :</b> visez 10 % si possible, pour les imprévus",
                        ),
                    ),
                    sec("Outils gratuits", ul(
                        "<b>Budget Conseil NE :</b> conseil personnalisé gratuit, <a href='https://www.budgetconseil.ch' target='_blank'>budgetconseil.ch</a>, 032 721 30 30",
                        "<b>Calculateur de budget :</b> <a href='https://www.comparis.ch/budget' target='_blank'>comparis.ch/budget</a>",
                        "<b>Guide budget famille :</b> <a href='https://www.ksa.ch' target='_blank'>ksa.ch</a> (Conseils suisses aux familles)",
                    ), width='half'),
                    sec("Pièges courants à éviter", ul(
                        "Achats à tempérament / leasing voiture, intérêts très élevés",
                        "Loteries et jeux d'argent en ligne",
                        "Déménager sans extrait de poursuites propre rend très difficile de trouver un logement",
                        "Chèques postaux non payés, entraînent des frais supplémentaires",
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
                            "Lisez attentivement le document, quel créancier, quel montant, quelle date",
                            "Si vous contestez la dette : faites opposition immédiatement (dans les 10 jours), par écrit à l'Office des poursuites",
                            "Si vous ne contestez pas : négociez un plan de paiement avec le créancier",
                            "Ne jetez jamais ce document, gardez-le",
                        ),
                    ),
                    sec("Office des poursuites NE", ul(
                        "<b>Neuchâtel :</b> Rue du Seyon 4, 032 889 67 00",
                        "<b>La Chaux-de-Fonds :</b> Espacité 4, 032 889 67 30",
                        "<b>Extrait des poursuites :</b> gratuit, demandez-le pour vérifier votre situation avant de chercher un logement",
                    ), width='half'),
                    sec("Aide gratuite", ul(
                        "<b>Budget Conseil NE :</b> 032 721 30 30, <a href='https://www.budgetconseil.ch' target='_blank'>budgetconseil.ch</a>",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00, aide juridique",
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
                        "<b>Caritas Neuchâtel :</b> épicerie sociale sur dossier, Vieux-Châtel 4, 2002 Neuchâtel, 032 886 80 70, <a href='https://caritas-regio.ch/neuchatel' target='_blank'>caritas-regio.ch/neuchatel</a>",
                        "<b>Armée du Salut Neuchâtel :</b> repas et aide alimentaire, <a href='https://armeedusalut.ch' target='_blank'>armeedusalut.ch</a>",
                        "<b>Croix-Rouge Neuchâtel :</b> colis alimentaires, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Banque alimentaire NE :</b> renseignez-vous via votre GSR ou le COSM",
                    ), width='half'),
                    sec("À La Chaux-de-Fonds", ul(
                        "<b>Caritas La Chaux-de-Fonds :</b> aide alimentaire, renseignez-vous via Caritas NE",
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
                'why_interesting': para("Parler français facilite tout : trouver du travail, comprendre les courriers officiels, parler avec l'école de vos enfants. Des cours gratuits ou très peu chers existent partout dans le canton."),
                'how_to': (
                    h3("Trouver un cours près de chez vous")
                    + ol(
                        "Choisissez votre niveau (débutant A1 jusqu'à avancé), en cas de doute, faites un bilan gratuit au COSM",
                        "Contactez un organisme ci-dessous (COSM, Caritas, RECIF, Croix-Rouge)",
                        "Demandez s'il reste de la place et la date de début du prochain cours",
                        "Inscrivez-vous, beaucoup de cours sont gratuits ou coûtent quelques francs",
                    )
                    + h3("Bon à savoir")
                    + ul(
                        "Certains cours sont réservés aux femmes (RECIF)",
                        "La garde d'enfants est parfois proposée pendant les cours",
                        "Un cours de français peut compter pour le permis C ou la naturalisation",
                    )
                ),
                'location': (
                    h3("COSM, Cours officiels d'intégration")
                    + ul(
                        "<b>Adresse :</b> Place de la Gare 6, 2300 La Chaux-de-Fonds (+ permanences à Neuchâtel et Fleurier)",
                        "<b>Téléphone :</b> 032 889 74 42",
                        "<b>Email :</b> cosm@ne.ch",
                        "<b>Site :</b> <a href='https://www.ne.ch/cosm'>ne.ch/cosm</a>",
                    )
                    + h3("Autres organismes")
                    + ul(
                        "<b>Caritas NE :</b> ateliers gratuits (bénévoles), caritas.ateliers@ne.ch, 032 886 80 70",
                        "<b>RECIF (femmes uniquement) :</b> cours A1 à B1, <a href='https://recifne.ch'>recifne.ch</a>",
                        "<b>Croix-Rouge NE :</b> cours de conversation, <a href='https://www.croix-rouge-ne.ch'>croix-rouge-ne.ch</a>",
                    )
                ),
                'body': body(
                    sec("Pourquoi apprendre le français",
                        para("Parler français facilite tout : trouver du travail, comprendre les courriers officiels, parler avec l'école de vos enfants. Des cours gratuits ou très peu chers existent partout dans le canton."),
                    ),
                    sec("COSM, Cours officiels d'intégration", ul(
                        "<b>Adresse :</b> Place de la Gare 6, 2300 La Chaux-de-Fonds (+ permanences à Neuchâtel et Fleurier)",
                        "<b>Téléphone :</b> 032 889 74 42",
                        "<b>Email :</b> cosm@ne.ch",
                        "<b>Site :</b> <a href='https://www.ne.ch/cosm' target='_blank'>ne.ch/cosm</a>",
                        "Cours de français, alphabétisation, informatique, intégration",
                    ), width='half'),
                    sec("Autres organismes", ul(
                        "<b>Caritas NE :</b> ateliers gratuits (bénévoles), 10 groupes à Neuchâtel, 3 à CDF, caritas.ateliers@ne.ch, 032 886 80 70",
                        "<b>RECIF (femmes uniquement) :</b> cours A1 à B1, Rue de la Cassarde 22, Neuchâtel, <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>Croix-Rouge NE :</b> cours de conversation, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
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
                    sec("Médecins, MEBEKO", ul(
                        "<b>Organisme :</b> MEBEKO (Commission des professions médicales)",
                        "<b>Site :</b> <a href='https://www.bag.admin.ch' target='_blank'>bag.admin.ch</a> (chercher MEBEKO)",
                        "<b>Coût :</b> CHF 800 à 1 000",
                        "<b>Délai :</b> 3 à 4 mois (dossier complet)",
                        "<b>Langue requise :</b> B2 en français, allemand ou italien",
                    ), width='half'),
                    sec("Infirmiers, physios, Croix-Rouge suisse", ul(
                        "<b>Site :</b> <a href='https://www.redcross.ch/reconnaissance' target='_blank'>redcross.ch/reconnaissance</a>",
                        "<b>Commencez par :</b> <a href='https://precheck.ch' target='_blank'>precheck.ch</a> (gratuit, obligatoire)",
                        "<b>Coût :</b> CHF 550 à 1 000",
                        "<b>Aide à Neuchâtel :</b> CNIP peut accompagner la démarche",
                    ), width='half'),
                    sec("Enseignants (CDIP) et autres (SEFRI)",
                        ul(
                            "<b>Enseignants :</b> CDIP, <a href='https://www.cdip.ch' target='_blank'>cdip.ch</a>",
                            "<b>Autres professions :</b> SEFRI, <a href='https://www.sefri.admin.ch' target='_blank'>sefri.admin.ch</a>",
                            "<b>Aide à Neuchâtel :</b> CNIP, <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a>, 032 889 69 25",
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
                            "<b>CNIP :</b> 032 889 69 25, <a href='https://www.cnip.ch' target='_blank'>cnip.ch</a>",
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
                            "<b>Duolingo :</b> application ludique, idéale pour débuter, <a href='https://www.duolingo.com' target='_blank'>duolingo.com</a>",
                            "<b>TV5Monde :</b> cours de français avec vidéos, <a href='https://apprendre.tv5monde.com' target='_blank'>apprendre.tv5monde.com</a>",
                            "<b>Français Authentique :</b> YouTube, compréhension orale",
                            "<b>RFI Savoirs :</b> exercices et actualités en français facile, <a href='https://savoirs.rfi.fr' target='_blank'>savoirs.rfi.fr</a>",
                        ),
                    ),
                    sec("Cours en ligne structurés", ul(
                        "<b>Migros Club School :</b> cours en ligne payants mais abordables, <a href='https://www.klubschule.ch' target='_blank'>klubschule.ch</a>",
                        "<b>Coursera / edX :</b> cours FLE de grandes universités, souvent gratuits à l'écoute",
                        "<b>Alliance Française :</b> cours de qualité, en ligne ou à Neuchâtel, <a href='https://www.alliancefrancaise.ch' target='_blank'>alliancefrancaise.ch</a>",
                    ), width='half'),
                    sec("Conseils pour progresser vite", ul(
                        "Pratiquez 15 à 20 minutes chaque jour plutôt qu'une longue session par semaine",
                        "Regardez des séries françaises avec sous-titres",
                        "Parlez avec vos voisins, collègues, commerçants, même avec des erreurs",
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
                        "Payez les frais (env. CHF 100 à 200 selon les modules)",
                        "Recevez votre attestation, valable pour toutes vos démarches officielles",
                    )),
                    sec("Centres de test à Neuchâtel", ul(
                        "<b>COSM :</b> peut orienter vers les centres agréés, 032 889 74 42",
                        "<b>Liste officielle :</b> <a href='https://www.fide-info.ch/fr/test/centres-de-test' target='_blank'>fide-info.ch/centres</a>",
                        "<b>Préparation gratuite :</b> des cours préparatoires existent, demandez au COSM ou à la RECIF",
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
                            "En général : permis N, F, S, B récent, vérifiez selon votre situation",
                        ),
                    ),
                    sec("Comment faire la demande", ol(
                        "Prenez contact avec le COSM : 032 889 74 42, cosm@ne.ch",
                        "Le COSM évalue votre situation et votre niveau de français",
                        "Si éligible, vous recevez un bon ou une prise en charge directe",
                        "Inscrivez-vous dans un organisme de cours agréé",
                    )),
                    sec("Organismes agréés", ul(
                        "<b>COSM :</b> cours propres, Place de la Gare 6, La Chaux-de-Fonds",
                        "<b>RECIF (femmes) :</b> Rue de la Cassarde 22, Neuchâtel, <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>Caritas NE :</b> ateliers gratuits, caritas.ateliers@ne.ch",
                        "<b>Croix-Rouge NE :</b> cours de conversation, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
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
                        "<b>COSM :</b> cours d'alphabétisation pour adultes migrants, 032 889 74 42, premiers cours gratuits",
                        "<b>Caritas NE :</b> ateliers d'alphabétisation en petits groupes avec des bénévoles, 032 886 80 70, gratuit",
                        "<b>RECIF (femmes) :</b> alphabétisation spécifique pour les femmes, <a href='https://recifne.ch' target='_blank'>recifne.ch</a>",
                        "<b>Croix-Rouge NE :</b> cours de base, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                    ), width='half'),
                    sec("Progression typique", ul(
                        "<b>Phase 1 :</b> reconnaissance des lettres et des sons (quelques mois)",
                        "<b>Phase 2 :</b> lecture et écriture simples, lire une pancarte, remplir un formulaire",
                        "<b>Phase 3 :</b> intégration dans un cours de français standard (A1, A2…)",
                        "La durée varie selon chaque personne, il n'y a pas de pression",
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
                        "<b>Migros Klubschule :</b> cours tous niveaux, soir et week-end, <a href='https://www.klubschule.ch' target='_blank'>klubschule.ch</a>, env. CHF 200 à 400/semestre",
                        "<b>Alliance Française Neuchâtel :</b> cours officiels avec certification DELF, <a href='https://www.alliancefrancaise.ch' target='_blank'>alliancefrancaise.ch</a>",
                        "<b>Inlingua Neuchâtel :</b> cours intensifs et semi-intensifs, <a href='https://www.inlingua-neuchatel.ch' target='_blank'>inlingua-neuchatel.ch</a>",
                        "<b>Université populaire NE :</b> cours abordables pour adultes, renseignez-vous en mairie",
                    ), width='half'),
                    sec("Certifications officielles", ul(
                        "<b>DELF :</b> diplôme officiel français (A1 à B2), reconnu dans le monde entier, passé à l'Alliance Française",
                        "<b>FIDE :</b> certificat suisse spécifique aux migrants, reconnu pour naturalisation et permis C",
                        "<b>TCF :</b> test de connaissance du français, rapide, peut être passé en ligne",
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
                        "<b>Coursera :</b> cours de grandes universités mondiales, audit gratuit, <a href='https://www.coursera.org' target='_blank'>coursera.org</a>",
                        "<b>edX :</b> MIT, Harvard, etc., audit gratuit, <a href='https://www.edx.org' target='_blank'>edx.org</a>",
                        "<b>OpenClassrooms :</b> formation professionnalisante en français, <a href='https://openclassrooms.com' target='_blank'>openclassrooms.com</a>",
                        "<b>YouTube :</b> tutoriels gratuits dans tous les domaines",
                        "<b>Khan Academy :</b> maths, sciences, finances, <a href='https://fr.khanacademy.org' target='_blank'>fr.khanacademy.org</a>",
                    ), width='half'),
                    sec("Formations certifiantes suisses", ul(
                        "<b>Migros Klubschule en ligne :</b> cours mixtes présentiel + e-learning, <a href='https://www.klubschule.ch' target='_blank'>klubschule.ch</a>",
                        "<b>SwissSkills :</b> ressources sur les métiers suisses, <a href='https://www.swissskills.ch' target='_blank'>swissskills.ch</a>",
                        "<b>Formation continue UniNE :</b> modules en ligne, <a href='https://www.unine.ch/formcont' target='_blank'>unine.ch/formcont</a>",
                        "<b>LinkedIn Learning :</b> si vous avez un compte LinkedIn Premium, accès via bibliothèques pour certains",
                    ), width='half'),
                    sec("Conseils pour réussir en e-learning",
                        ul(
                            "Fixez-vous un horaire régulier, 30 min/jour vaut mieux que 4h le week-end",
                            "Choisissez un cours avec un certificat, cela motive et valorise votre CV",
                            "Rejoignez les forums et groupes du cours, vous n'êtes pas seul",
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
                            "<b>Admission :</b> maturité suisse ou équivalent reconnu, vérifiez sur unine.ch/admission",
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
                        "<b>Bourses fédérales :</b> pour les étrangers non-UE, <a href='https://www.sbfi.admin.ch/bourses' target='_blank'>sbfi.admin.ch</a>",
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
                            "<b>Enfant de moins de 16 ans :</b> CHF 215/mois minimum (vérifiez le montant actuel, il évolue)",
                            "<b>Enfant de 16 à 25 ans en formation :</b> CHF 268/mois minimum",
                            "Les montants varient selon la caisse d'allocations familiales",
                            "Vous pouvez réclamer jusqu'à 5 ans en arrière si vous ne saviez pas",
                        ),
                    ),
                    sec("Comment les recevoir",
                        ul(
                            "<b>Si vous travaillez :</b> votre employeur fait la demande à votre place, demandez-lui",
                            "<b>Si vous êtes indépendant :</b> demandez à la CCNC (Caisse cantonale)",
                            "<b>Si vous êtes sans emploi :</b> contactez la CCNC directement",
                        ),
                    ),
                    sec("FER-CIAF (salariés)", ul(
                        "<b>Adresse :</b> Avenue du Premier-Mars 18, 2000 Neuchâtel",
                        "<b>Téléphone :</b> 032 727 37 05",
                        "<b>Email :</b> alfa@cian.ch",
                        "<b>Heures :</b> lun à jeu 8h à 11h45 / 13h45 à 17h; ven 8h à 11h45",
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
                            "<b>COSM :</b> peut vous accompagner dans les démarches, 032 889 74 42",
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
                        para("Les crèches sont très demandées. Inscrivez votre enfant le plus tôt possible, même avant sa naissance."),
                        para("Les tarifs sont calculés selon vos revenus. Une aide financière du canton peut réduire le coût."),
                    ),
                    sec("Comment trouver une place",
                        ol(
                            "Cherchez sur le site de votre commune, elles listent souvent les structures disponibles",
                            "Inscrivez votre enfant dans plusieurs structures en même temps",
                            "Demandez une subvention cantonale dès que vous avez une place confirmée",
                        ),
                    ),
                    sec("Liens utiles",
                        ul(
                            "<b>Structures d'accueil NE :</b> <a href='https://www.ne.ch/structures-accueil' target='_blank'>ne.ch/structures-accueil</a>",
                            "<b>Subvention garde :</b> renseignez-vous à votre GSR",
                            "<b>Tarifs :</b> environ CHF 30 à 100/jour selon revenus avant subvention",
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
                            "<b>Bénévoles Caritas :</b> aide aux devoirs gratuite, renseignez-vous à Caritas NE",
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
                'name': "Je cherche une garde pour mes enfants avant ou après l'école",
                'description': "Les structures parascolaires gardent les enfants le matin, le midi et après l'école. Voici comment m'inscrire.",
                'tags': ['Garde enfants', 'Enfants', 'Scolarisation', 'Budget', 'Subvention'],
                'audiences': ['Parents'],
                'body': body(
                    sec("Qu'est-ce que le parascolaire",
                        para("Les structures parascolaires (UAPE, Unité d'Accueil Pour Écoliers) gardent les enfants avant l'école le matin, le midi et après l'école le soir. C'est très utile si vous travaillez."),
                    ),
                    sec("Comment inscrire votre enfant",
                        ol(
                            "Contactez le service scolaire de votre commune dès l'inscription à l'école",
                            "Remplissez le formulaire d'inscription, les places sont limitées",
                            "Les tarifs sont calculés en fonction de votre revenu",
                            "Demandez une réduction de tarif via votre GSR si vos revenus sont modestes",
                        ),
                    ),
                    sec("Liens utiles", ul(
                        "<b>Neuchâtel ville :</b> <a href='https://www.neuchatelville.ch/parascolaire' target='_blank'>neuchatelville.ch</a>, parascolaire",
                        "<b>La Chaux-de-Fonds :</b> renseignez-vous au secrétariat scolaire de votre école",
                        "<b>Tarifs :</b> environ CHF 5 à 20/jour selon revenus",
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
                        "<b>Maisons de quartier :</b> animations vacances pour enfants, demandez à votre mairie",
                        "<b>Jeunesse et Sports (J+S) :</b> camps sportifs subventionnés, <a href='https://www.jugendundsport.ch/fr' target='_blank'>jugendundsport.ch</a>",
                        "<b>Camps de Pro Juventute :</b> colonie de vacances à tarif social, <a href='https://www.projuventute.ch' target='_blank'>projuventute.ch</a>",
                        "<b>Croix-Rouge NE :</b> activités ponctuelles, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                    ), width='half'),
                    sec("Aides financières", ul(
                        "<b>GSR :</b> peut parfois financer des camps ou colonies pour les familles à l'aide sociale",
                        "<b>Bourses de loisirs :</b> certaines communes accordent une aide, renseignez-vous à la mairie",
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
                    sec("APG, Allocations pour perte de gain", ul(
                        "Système qui verse les indemnités maternité et paternité",
                        "<b>Caisse compétente :</b> CCNC Neuchâtel, 032 889 65 01",
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
                            "<b>Permis G :</b> frontalier, travaille en Suisse, habite dans un pays voisin.",
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
                    sec("SMIG, Service des migrations NE", ul(
                        "<b>Adresse :</b> Rue de Tivoli 28, 2002 Neuchâtel 2",
                        "<b>Téléphone :</b> 032 889 63 10",
                        "<b>Email :</b> smig@ne.ch",
                        "<b>Heures :</b> lun à ven 8h à 12h; mer aussi 13h30 à 17h",
                        "<b>Site :</b> <a href='https://www.ne.ch/smig' target='_blank'>ne.ch/smig</a>",
                    ), width='half'),
                    sec("SEM, niveau fédéral", ul(
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
                    sec("CSP Neuchâtel, principal organisme", ul(
                        "<b>Neuchâtel :</b> Rue des Parcs 11, 2000 Neuchâtel",
                        "<b>La Chaux-de-Fonds :</b> Rue du Temple-Allemand 23, 2300 La Chaux-de-Fonds",
                        "<b>Téléphone :</b> 032 886 91 00",
                        "<b>Email :</b> csp.neuchatel@ne.ch",
                        "<b>Permanences migration :</b> jeudi 13h30 à 16h à Neuchâtel (sur RDV)",
                        "<b>Site :</b> <a href='https://csp.ch/neuchatel' target='_blank'>csp.ch/neuchatel</a>",
                    ), width='half'),
                    sec("Caritas, Bureau de consultation juridique (BCJ)", ul(
                        "<b>Adresse :</b> Vieux-Châtel 4, 2002 Neuchâtel",
                        "<b>Téléphone :</b> 026 552 50 40",
                        "<b>Email :</b> bcj-fr@caritas.ch",
                        "<b>Sans RDV :</b> mardi 9h à 12h",
                        "Spécialisé en droit d'asile et droit des étrangers",
                    ), width='half'),
                    sec("Autres ressources",
                        ul(
                            "<b>OSAR (Conseil suisse des réfugiés) :</b> <a href='https://www.osar.ch' target='_blank'>osar.ch</a>",
                            "<b>Ensemble-ne.ch :</b> infos juridiques en 18 langues, <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>",
                            "<b>Centre LAVI NE :</b> 032 889 51 00, victimes de violence",
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
                        "<b>SMIG :</b> Rue de Tivoli 28, 032 889 63 10",
                        "<b>CSP Neuchâtel (aide juridique) :</b> 032 886 91 00",
                        "<b>Caritas BCJ :</b> 026 552 50 40, mardi 9h à 12h sans RDV",
                        "<b>Ensemble-ne.ch :</b> <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>, infos en 18 langues",
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
                            "<b>Permis C :</b> conjoint et enfants de moins de 18 ans, droits étendus",
                            "<b>Permis B :</b> conjoint et enfants, sous conditions de revenus et de logement",
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
                            "Déposez la demande au SMIG : Rue de Tivoli 28, 2002 Neuchâtel, 032 889 63 10",
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
                            "<b>SMIG :</b> Rue de Tivoli 28, 2002 Neuchâtel, 032 889 63 10, <a href='https://www.ne.ch/naturalisation' target='_blank'>ne.ch/naturalisation</a>",
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
                            "<b>Conjoint(e) de Suisse :</b> conditions assouplies, renseignez-vous au SMIG",
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
                        "<b>Votre commune :</b> contrôle des habitants, renseignez-vous directement",
                        "C'est un droit unique en Suisse, profitez-en pour participer à la vie locale",
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
                            "<b>Permis B (obtenu par regroupement familial) :</b> le divorce peut entraîner le non-renouvellement, il faut démontrer une raison importante de rester (enfants, intégration, durée de séjour)",
                            "<b>Moins de 3 ans de mariage :</b> situation plus précaire, consultez immédiatement un juriste",
                        ),
                    ),
                    sec("Aide juridique d'urgence", ul(
                        "<b>CSP Neuchâtel :</b> 032 886 91 00, permanence migration jeudi 13h30 à 16h",
                        "<b>Caritas BCJ :</b> 026 552 50 40, mardi 9h à 12h sans RDV",
                        "<b>Centre LAVI NE :</b> 032 889 51 00, si séparation liée à des violences",
                    ), width='half'),
                    sec("Démarches au SMIG", ul(
                        "Informez le SMIG du changement de situation dès que possible",
                        "Ne dépassez pas la date d'expiration de votre permis sans avoir déposé une demande",
                        "<b>SMIG :</b> 032 889 63 10, smig@ne.ch",
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
                        "<b>COSM (Bureau du délégué) :</b> 032 889 74 42, cosm@ne.ch, peut orienter et soutenir",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00, aide juridique",
                        "<b>Centre LAVI NE :</b> 032 889 51 00, si vous avez subi des violences",
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
                            "Contactez l'ambassade ou le consulat de votre pays en Suisse, ils peuvent parfois obtenir le document pour vous",
                            "Demandez à un membre de votre famille restée dans votre pays de l'obtenir auprès de la mairie locale",
                            "Faites traduire le document par un traducteur assermenté si c'est demandé",
                            "Si votre pays ne délivre plus de documents (guerre, etc.) : signalez-le au SMIG ou à l'avocat qui vous aide",
                        ),
                    ),
                    sec("Documents suisses (si vous êtes né ou marié en Suisse)", ul(
                        "<b>Office de l'état civil NE :</b> Rue du Seyon 4, 2000 Neuchâtel, 032 889 67 87",
                        "<b>En ligne :</b> <a href='https://www.ne.ch/etat-civil' target='_blank'>ne.ch/etat-civil</a>",
                        "Extrait d'acte de naissance ou de mariage disponible sur demande (CHF 30 environ)",
                    ), width='half'),
                    sec("Aide pour les documents étrangers", ul(
                        "<b>COSM :</b> peut vous orienter, 032 889 74 42",
                        "<b>CSP Neuchâtel :</b> aide juridique pour les dossiers complexes, 032 886 91 00",
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
                            "Une attestation de domicile, nécessaire pour ouvrir un compte bancaire, inscrire vos enfants à l'école, etc.",
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
                        "<b>Neuchâtel ville :</b> Hôtel de Ville, Rue de l'Hôpital 1, 032 717 50 00",
                        "<b>La Chaux-de-Fonds :</b> Administration communale, Espacité 1, 032 889 60 00",
                        "<b>Autres communes :</b> cherchez 'contrôle des habitants' + nom de votre commune",
                        "<b>Horaires :</b> généralement lun à ven 8h à 12h / 13h30 à 17h",
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
                            "<b>SMIG (demandeurs d'asile) :</b> Rue de Tivoli 28, Neuchâtel, 032 889 63 10, ils orientent vers les hébergements d'asile",
                            "<b>GSR Neuchâtel (personnes domiciliées) :</b> 032 717 74 10, peut orienter vers des solutions d'urgence",
                            "<b>Armée du Salut :</b> présente à Neuchâtel et La Chaux-de-Fonds, <a href='https://armeedusalut.ch/jai-besoin-dun-hebergement/' target='_blank'>armeedusalut.ch</a>",
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
                        "<b>Caritas NE :</b> 032 886 80 70, peut orienter vers des solutions temporaires",
                        "<b>Croix-Rouge NE :</b> <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00, accompagnement social",
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
                            "L'état des lieux d'entrée est très important, signalez tout défaut immédiatement",
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
                        "<b>Asloca Neuchâtel :</b> association des locataires, conseil juridique, <a href='https://www.asloca.ch' target='_blank'>asloca.ch</a>",
                        "<b>Autorité de conciliation NE :</b> recours gratuit avant tout tribunal",
                        "<b>CSP Neuchâtel :</b> 032 886 91 00, aide juridique générale",
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
                            "<a href='https://www.homegate.ch' target='_blank'>homegate.ch</a>, le plus utilisé en Suisse",
                            "<a href='https://www.immoscout24.ch' target='_blank'>immoscout24.ch</a>, grand choix",
                            "<a href='https://www.anibis.ch' target='_blank'>anibis.ch</a>, petites annonces, souvent moins cher",
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
                            "Répondez très vite aux annonces, les appartements partent en quelques heures",
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
                            "Doit être déposé sur un compte bancaire bloqué au nom du locataire, pas remis directement au propriétaire",
                            "L'argent vous appartient, le propriétaire ne peut y accéder qu'en cas de litige",
                        ),
                    ),
                    sec("Comment payer",
                        ul(
                            "Ouvrez un compte de garantie dans une banque (présentez votre bail)",
                            "Alternative : garantie de loyer via une assurance (ex: Firstcaution, SwissCaution), vous payez une prime annuelle au lieu d'immobiliser l'argent",
                            "<b>Firstcaution :</b> <a href='https://www.firstcaution.ch' target='_blank'>firstcaution.ch</a>",
                            "<b>SwissCaution :</b> <a href='https://www.swisscaution.ch' target='_blank'>swisscaution.ch</a>",
                        ),
                    ),
                    sec("Récupérer son dépôt", ul(
                        "Après l'état des lieux de sortie, le propriétaire a 1 an pour libérer le dépôt",
                        "Si tout est en ordre : remboursement intégral",
                        "En cas de litige : l'Asloca peut vous aider, <a href='https://www.asloca.ch' target='_blank'>asloca.ch</a>",
                    ), width='half'),
                    sec("À savoir", ul(
                        "Exigez toujours un reçu ou la confirmation du compte bancaire créé",
                        "Photographiez chaque pièce lors de l'état des lieux d'entrée",
                        "<b>Asloca NE :</b> conseil gratuit aux locataires, <a href='https://www.asloca.ch' target='_blank'>asloca.ch</a>",
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
                        para("Le logement social s'adresse aux personnes dont les revenus ne permettent pas d'accéder au marché locatif ordinaire. Les listes d'attente peuvent être longues, inscrivez-vous dès que possible."),
                    ),
                    sec("Organismes à contacter", ul(
                        "<b>Neuchâtel ville, Service du logement :</b> 032 717 50 00, mairie, Rue de l'Hôpital 1",
                        "<b>La Chaux-de-Fonds, Service du logement :</b> 032 889 60 00, Espacité 1",
                        "<b>GSR :</b> peut vous orienter selon votre situation, 032 717 74 10",
                        "<b>Caritas NE :</b> logements d'urgence ponctuels, 032 886 80 70",
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
                        "<b>Vaudoise :</b> présente à Neuchâtel, <a href='https://www.vaudoise.ch' target='_blank'>vaudoise.ch</a>",
                        "<b>Helvetia :</b> <a href='https://www.helvetia.com/ch/fr' target='_blank'>helvetia.com</a>",
                        "<b>AXA / Zurich :</b> en ligne et en agence",
                        "<b>Coût :</b> environ CHF 100 à 250/an selon la valeur des biens assurés",
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
                        "<b>Heures :</b> lun à ven 8h à 12h / 13h30 à 17h",
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
                            "<b>Bénévolat NE :</b> <a href='https://www.benevolat-ne.ch' target='_blank'>benevolat-ne.ch</a>, cherchez une activité bénévole selon vos intérêts",
                            "<b>Clubs sportifs :</b> demandez à votre commune ou au COSM",
                            "<b>Maisons de quartier :</b> activités culturelles, cours, rencontres, renseignez-vous dans votre quartier",
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
                            "<b>Buanderie commune :</b> respectez les horaires affichés, c'est pris très au sérieux",
                            "<b>Poubelles :</b> chaque commune a ses règles de tri. Renseignez-vous dès l'arrivée.",
                            "<b>Cave et débarras :</b> ne laissez pas d'affaires dans les parties communes sans autorisation",
                        ),
                    ),
                    sec("Vie quotidienne",
                        ul(
                            "<b>Magasins :</b> fermés le dimanche (sauf gares et certains centres commerciaux)",
                            "<b>Ponctualité :</b> très importante, arrivez à l'heure aux rendez-vous",
                            "<b>Saluer :</b> dites bonjour à vos voisins dans l'ascenseur et les couloirs",
                            "<b>Chaussures :</b> beaucoup de Suisses enlèvent leurs chaussures en entrant, attendez qu'on vous le propose",
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
                        para("C'est une personne formée qui traduit pour vous lors de vos rendez-vous médicaux, scolaires ou administratifs. Ce n'est pas simplement un traducteur, il connaît aussi les différences culturelles."),
                    ),
                    sec("Comment en demander un", ul(
                        "<b>COSM :</b> le premier contact, 032 889 74 42, ils coordonnent les interprètes pour tout le canton",
                        "<b>HNE :</b> l'hôpital dispose d'un service d'interprétariat, demandez lors de la prise de RDV",
                        "<b>Écoles :</b> le COSM peut envoyer un interprète pour les réunions parents-enseignants",
                        "<b>SMIG :</b> un interprète est prévu pour certains rendez-vous officiels",
                    ), width='half'),
                    sec("Plateformes en ligne", ul(
                        "<b>Ensemble-ne.ch :</b> informations officielles en 18 langues, <a href='https://www.ensemble-ne.ch' target='_blank'>ensemble-ne.ch</a>",
                        "<b>ch.ch :</b> guide officiel suisse en plusieurs langues, <a href='https://www.ch.ch' target='_blank'>ch.ch</a>",
                        "<b>Traduction de documents :</b> demandez au COSM pour les documents officiels",
                        "Google Translate peut aider pour les documents simples, mais évitez-le pour les contrats importants",
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
                        "<b>COSM :</b> cours d'informatique pour migrants, 032 889 74 42, renseignez-vous sur les sessions en cours",
                        "<b>Bibliothèques :</b> initiations gratuites à l'informatique, Bibliothèque publique de Neuchâtel, 032 717 69 60",
                        "<b>Croix-Rouge NE :</b> ateliers numériques ponctuels, <a href='https://www.croix-rouge-ne.ch' target='_blank'>croix-rouge-ne.ch</a>",
                        "<b>Caritas NE :</b> bénévoles disponibles pour aider, 032 886 80 70",
                    ), width='half'),
                    sec("Ressources gratuites en ligne", ul(
                        "<b>Clé Numérique :</b> cours en ligne gratuits en français, <a href='https://cle-numerique.ch' target='_blank'>cle-numerique.ch</a>",
                        "<b>OpenClassrooms :</b> formation gratuite, <a href='https://openclassrooms.com' target='_blank'>openclassrooms.com</a>",
                        "<b>France Numérique :</b> tutoriels simples, <a href='https://www.numerique.gouv.fr' target='_blank'>numerique.gouv.fr</a>",
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
                            "<b>CFF :</b> trains entre les villes, <a href='https://www.cff.ch' target='_blank'>cff.ch</a> ou application CFF Mobile",
                            "<b>TRN (Transports Régionaux Neuchâtelois) :</b> bus dans le canton, <a href='https://www.trn.ch' target='_blank'>trn.ch</a>",
                            "<b>TRAVYS :</b> région Yverdon à Val-de-Travers",
                            "<b>CarPostal :</b> cars jaunes pour les villages, <a href='https://www.postauto.ch' target='_blank'>postauto.ch</a>",
                        ),
                    ),
                    sec("Économiser",
                        ul(
                            "<b>Demi-tarif CFF :</b> CHF 185/an, réduit tous vos billets de 50 %",
                            "<b>Abonnement général :</b> voyages illimités sur tout le réseau, environ CHF 3 860/an (2e classe)",
                            "<b>SwissPass :</b> regroupe tous vos abonnements, <a href='https://www.swisspass.ch' target='_blank'>swisspass.ch</a>",
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
                    sec("PubliBike, vélos partagés", ul(
                        "<b>Comment ça marche :</b> louez un vélo (normal ou électrique) à la station, rendez-le n'importe où",
                        "<b>Prix :</b> CHF 3/30 min (vélo normal), CHF 5/30 min (e-bike), abonnement annuel disponible",
                        "<b>App :</b> téléchargez 'PubliBike', <a href='https://www.publibike.ch' target='_blank'>publibike.ch</a>",
                        "<b>Stations :</b> gare, centre-ville, quartiers principaux de Neuchâtel",
                    ), width='half'),
                    sec("Règles et sécurité", ul(
                        "<b>Casque :</b> obligatoire pour les e-bikes, fortement recommandé pour tous",
                        "<b>Lumières :</b> obligatoires de nuit",
                        "<b>Alcool :</b> limite légale à 0,5‰, même à vélo",
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
                            "Sur prescription de votre médecin, demandez une ordonnance",
                            "La LAMal rembourse le transport si la distance est supérieure à 25 km ou si un transport médicalement justifié",
                            "Demandez l'accord de votre caisse maladie avant le transport si possible",
                        ),
                    ),
                    sec("Options disponibles à Neuchâtel", ul(
                        "<b>Taxi médical :</b> prenez rendez-vous avec un taxi agréé, présentez votre ordonnance médicale",
                        "<b>Ambulance non urgente :</b> pour les soins planifiés, contactez votre médecin",
                        "<b>Bénévoles Croix-Rouge NE :</b> accompagnement bénévole à vos RDV médicaux, 032 913 77 77",
                        "<b>Pro Senectute NE :</b> aide à la mobilité pour les seniors, 032 722 07 90",
                    ), width='half'),
                    sec("En cas d'urgence", ul(
                        "<b>Ambulance :</b> 144, gratuit, 24h/24",
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
                        "<b>SAN Neuchâtel :</b> Chemin de la Vuarpillière 29, 2000 Neuchâtel, 032 889 67 67",
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
# Parcours
# ---------------------------------------------------------------------------

PATHWAYS = [

    # -----------------------------------------------------------------------
    {
        'title': "Certifier son niveau de français, le test fide",
        'category': 'Education',
        'description': "Faites reconnaître officiellement votre niveau de français. Le test fide est accepté pour le renouvellement de permis et la naturalisation.",
        'order': 0,
        'steps': [
            {
                'order': 1,
                'step_label': '',
                'resource': {
                    'name': "Comprendre le test fide",
                    'description': "Le test fide mesure votre niveau de français en situations de la vie courante. Niveaux A1 à B1. Reconnu par les autorités suisses.",
                    'tags': ['Langue', 'Cours de langue'],
                    'body': body(
                        sec("À quoi sert le test fide",
                            para("Le test fide évalue deux compétences séparément : l'oral (parler et comprendre) et l'écrit (lire et écrire)."),
                            para("Les niveaux vont de A1 (débutant) à B1 (intermédiaire). Les autorités suisses acceptent le passeport fide pour le renouvellement de permis de séjour B ou C et pour la naturalisation."),
                        ),
                        sec("Tarifs",
                            ul(
                                "Test oral uniquement : CHF 170",
                                "Test écrit uniquement : CHF 120",
                                "Test complet (oral + écrit) : CHF 250",
                            ),
                        ),
                        sec("En savoir plus",
                            para("Site officiel : <a href='https://fide-service.ch' target='_blank'>fide-service.ch</a>"),
                        ),
                    ),
                },
            },
            {
                'order': 2,
                'step_label': '',
                'resource': {
                    'name': "Faire un bilan linguistique gratuit",
                    'description': "Avant de passer le test, évaluez votre niveau gratuitement. Vous serez orienté vers le bon cours ou le bon examen.",
                    'tags': ['Langue', 'Gratuit', 'En personne', 'Traduction disponible'],
                    'body': body(
                        sec("COSM, Service de cohésion multiculturelle",
                            para("Le COSM propose des entretiens d'accueil gratuits et confidentiels en plusieurs langues. L'entretien permet d'évaluer votre niveau de français et de vous orienter vers les bons services."),
                            ul(
                                "<b>Adresse :</b> Rue de Tivoli 22, 2000 Neuchâtel",
                                "<b>Téléphone :</b> 032 889 74 42",
                                "<b>Email :</b> cosm@ne.ch",
                                "<b>Sur rendez-vous</b>, gratuit et confidentiel",
                            ),
                        ),
                        sec("ESPACE, Centre de formation intégré",
                            para("ESPACE intègre l'évaluation de niveau dans son processus d'inscription aux cours de français."),
                            ul(
                                "<b>Adresse :</b> Avenue de Clos-Brochet 10, 2000 Neuchâtel",
                                "<b>Cours :</b> du niveau alphabétisation au niveau A2",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 3,
                'step_label': '',
                'resource': {
                    'name': "Choisir et rejoindre un cours de français",
                    'description': "Si votre niveau n'est pas encore prêt pour le test, inscrivez-vous à un cours adapté. ESPACE propose des cours gratuits à Neuchâtel.",
                    'tags': ['Langue', 'Cours de langue', 'Gratuit', 'En personne'],
                    'body': body(
                        sec("ESPACE (gratuit)",
                            para("ESPACE est le principal centre de formation linguistique du canton. Les cours sont gratuits et vont du niveau alphabétisation au niveau A2."),
                            ul(
                                "Sessions de 6 mois (deux sessions par an)",
                                "Inscription avec liste d'attente possible",
                                "<b>Adresse :</b> Avenue de Clos-Brochet 10, 2000 Neuchâtel",
                            ),
                        ),
                        sec("Université de Neuchâtel, Français pour tous",
                            para("L'UniNE propose des cours de français pour les titulaires de permis N, F ou B."),
                            ul(
                                "Niveaux A2 à C1",
                                "<b>Site :</b> <a href='https://www.unine.ch' target='_blank'>unine.ch</a>",
                            ),
                        ),
                        sec("Cours privés",
                            ul(
                                "inlingua Neuchâtel",
                                "Migros Club School",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 4,
                'step_label': '',
                'resource': {
                    'name': "S'inscrire au test fide en ligne",
                    'description': "L'inscription se fait uniquement en ligne. Délai minimum : 15 jours avant la date de l'examen.",
                    'tags': ['Langue', 'En ligne', 'Formulaire'],
                    'body': body(
                        sec("Centre agréé fide à Neuchâtel",
                            para("Swiss Language Academy est le centre agréé fide à Neuchâtel. L'inscription se fait exclusivement en ligne sur leur site."),
                            ul(
                                "<b>Adresse :</b> Rue de la Maladière 84 (CPLN), 2000 Neuchâtel",
                                "<b>Email :</b> fide@swiss-language-academy.ch",
                                "<b>Inscription en ligne :</b> <a href='https://swiss-language-academy.ch' target='_blank'>swiss-language-academy.ch</a>",
                            ),
                        ),
                        sec("Délais à respecter",
                            ul(
                                "Inscrivez-vous au moins <b>15 jours avant</b> la date de l'examen",
                                "Vous recevez une confirmation par email au moins 10 jours avant",
                                "La convocation indique l'heure et la salle exactes",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 5,
                'step_label': '',
                'resource': {
                    'name': "Recevoir votre passeport linguistique fide",
                    'description': "Après le test, vous recevez un passeport linguistique officiel par courrier. Délai : environ 4 semaines.",
                    'tags': ['Langue', 'Documents officiels'],
                    'body': body(
                        sec("Le passeport linguistique fide",
                            para("Le passeport fide indique votre niveau séparément pour l'oral et l'écrit (par exemple : oral B1, écrit A2). Il est valable à vie et reconnu par toutes les autorités suisses."),
                            ul(
                                "Reçu par courrier environ <b>4 semaines</b> après le test",
                                "Valable à vie, pas de date d'expiration",
                                "Reconnu pour le renouvellement de permis B et C",
                                "Reconnu pour la demande de naturalisation",
                                "Utile aussi pour la recherche d'emploi",
                            ),
                        ),
                    ),
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    {
        'title': "S'inscrire au chômage à Neuchâtel, ONE",
        'category': 'Work',
        'description': "Activez vos droits aux indemnités chômage dès que vous perdez votre emploi. Chaque jour de retard peut vous faire perdre des indemnités.",
        'order': 1,
        'steps': [
            {
                'order': 1,
                'step_label': '',
                'resource': {
                    'name': "Vérifier mon droit aux indemnités chômage",
                    'description': "Pour recevoir de l'argent pendant votre recherche d'emploi, vous devez remplir certaines conditions précises.",
                    'tags': ['Travail', 'Chomage', 'Droits'],
                    'body': body(
                        sec("Conditions à remplir",
                            ul(
                                "Avoir cotisé à l'assurance chômage pendant <b>au moins 12 mois</b> dans les 2 dernières années",
                                "Avoir un permis de séjour valide (B, C ou L selon les cas)",
                                "Être disponible pour travailler immédiatement",
                                "Ne pas avoir quitté son emploi volontairement sans raison valable",
                            ),
                        ),
                        sec("Cas particuliers",
                            para("Les titulaires de permis N (requérants d'asile en cours de procédure) ne peuvent pas recevoir les indemnités ordinaires. Contactez le COSM ou votre assistant social pour connaître les aides disponibles."),
                        ),
                        sec("Montant",
                            para("Les indemnités représentent environ <b>80%</b> de votre dernier salaire assuré, jusqu'à un maximum de CHF 148 par jour."),
                        ),
                    ),
                },
            },
            {
                'order': 2,
                'step_label': '',
                'resource': {
                    'name': "Choisir ma caisse d'assurance chômage",
                    'description': "Avant de vous inscrire à l'ONE, choisissez votre caisse. C'est elle qui calcule et verse vos indemnités chaque mois.",
                    'tags': ['Chomage', 'Travail', 'En personne'],
                    'body': body(
                        sec("Principales caisses à Neuchâtel",
                            ul(
                                "<b>Caisse Cantonale Neuchâteloise (CCNAC) :</b> Espacité 4, 2302 La Chaux-de-Fonds, 032 889 67 90",
                                "<b>Unia :</b> accessible aux membres du syndicat Unia",
                                "Autres caisses syndicales selon votre secteur professionnel",
                            ),
                        ),
                        sec("Comment choisir",
                            para("Vous pouvez choisir n'importe quelle caisse reconnue. Le montant versé est le même quelle que soit la caisse. La CCNAC est la caisse cantonale publique, accessible à tous."),
                        ),
                    ),
                },
            },
            {
                'order': 3,
                'step_label': '',
                'resource': {
                    'name': "M'inscrire à l'ONE avant la fin de mon contrat",
                    'description': "Inscrivez-vous dès que vous savez que vous allez perdre votre emploi. Idéalement avant la fin du contrat de travail.",
                    'tags': ['Chomage', 'Travail', 'En ligne', 'En personne', 'Formulaire'],
                    'body': body(
                        sec("Comment s'inscrire",
                            ul(
                                "En ligne sur <a href='https://www.arbeit.swiss' target='_blank'>arbeit.swiss</a>, disponible 24h/24, sans création de compte obligatoire",
                                "Ou au guichet ONE sur rendez-vous",
                            ),
                        ),
                        sec("ONE Neuchâtel", ul(
                            "<b>Adresse :</b> Avenue Edouard-Dubois 20, 2000 Neuchâtel",
                            "<b>Téléphone :</b> 032 889 68 18",
                            "<b>Email :</b> one@ne.ch",
                        ), width='half'),
                        sec("ONE La Chaux-de-Fonds", ul(
                            "<b>Adresse :</b> Espacité 1, 2302 La Chaux-de-Fonds",
                            "<b>Téléphone :</b> 032 889 69 00",
                        ), width='half'),
                        sec("Documents à préparer",
                            ul(
                                "Pièce d'identité + permis de séjour valide",
                                "Contrat de travail ou lettre de licenciement",
                                "Numéro AVS (numéro d'assurance sociale suisse)",
                                "Coordonnées bancaires (IBAN)",
                                "CV à jour",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 4,
                'step_label': '',
                'resource': {
                    'name': "Participer au premier entretien de conseil",
                    'description': "L'ONE vous contacte dans les 15 jours pour un premier entretien. Vous définissez ensemble votre plan de recherche d'emploi.",
                    'tags': ['Chomage', 'Travail', 'En personne'],
                    'body': body(
                        sec("Ce qui se passe lors de l'entretien",
                            ul(
                                "Le conseiller examine votre dossier et vos compétences professionnelles",
                                "Il définit avec vous les critères du poste à rechercher",
                                "Il fixe le nombre minimum de candidatures par mois (généralement 8 à 12)",
                                "Il peut proposer des mesures actives : ateliers CV, formation courte, stage professionnel",
                            ),
                        ),
                        sec("À apporter",
                            ul(
                                "Pièce d'identité et permis de séjour",
                                "Attestation de l'employeur précédent",
                                "Certificats de travail",
                                "CV à jour",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 5,
                'step_label': '',
                'resource': {
                    'name': "Soumettre l'IPA chaque mois avant le 5",
                    'description': "Chaque mois, avant le 5, vous devez envoyer vos preuves de recherche d'emploi à votre caisse. C'est obligatoire pour recevoir les indemnités.",
                    'tags': ['Chomage', 'Formulaire', 'Documents officiels'],
                    'body': body(
                        sec("L'IPA, formulaire mensuel obligatoire",
                            para("L'IPA est le formulaire qui prouve que vous recherchez activement un emploi. Il doit être envoyé à votre caisse chômage <b>avant le 5 du mois suivant</b>."),
                            ul(
                                "Remplissez-le chaque mois, même si vous n'avez pas trouvé de travail",
                                "Joignez les preuves de chaque candidature : date, nom de l'entreprise, poste, réponse reçue",
                                "Un retard ou un oubli peut entraîner une <b>suspension temporaire des indemnités</b>",
                            ),
                        ),
                        sec("Conseil",
                            para("Tenez un tableau de suivi de vos candidatures dès le premier jour. Cela facilite grandement le remplissage mensuel et prouve votre démarche active en cas de contrôle."),
                        ),
                    ),
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    {
        'title': "Faire reconnaître son diplôme étranger en Suisse",
        'category': 'Education',
        'description': "Votre diplôme obtenu à l'étranger peut être reconnu en Suisse. Une attestation officielle facilite votre recherche d'emploi et est obligatoire pour certaines professions.",
        'order': 2,
        'steps': [
            {
                'order': 1,
                'step_label': '',
                'resource': {
                    'name': "Mon diplôme est-il reconnu automatiquement ?",
                    'description': "En Suisse, certaines professions exigent une reconnaissance officielle obligatoire. Pour les autres, une attestation aide à convaincre les employeurs.",
                    'tags': ['Reconnaissance diplome', 'Formation', 'Travail'],
                    'body': body(
                        sec("Professions réglementées, reconnaissance obligatoire",
                            para("Dans ces professions, vous devez faire reconnaître votre diplôme avant de pouvoir exercer en Suisse :"),
                            ul(
                                "Professions médicales : médecin, dentiste, pharmacien, vétérinaire",
                                "Soins infirmiers : infirmier/infirmière, sage-femme",
                                "Enseignant",
                                "Avocat (pour représenter des clients en justice)",
                            ),
                        ),
                        sec("Professions non réglementées, reconnaissance utile",
                            para("La grande majorité des professions en Suisse ne sont pas réglementées. Un employeur peut vous recruter sans reconnaissance officielle. Mais une attestation de niveau renforce votre candidature."),
                            para("Exemples : ingénieur, comptable, informaticien, économiste, architecte."),
                        ),
                        sec("Vérifier votre situation",
                            para("Consultez la liste complète sur <a href='https://www.recognition.swiss' target='_blank'>recognition.swiss</a>."),
                        ),
                    ),
                },
            },
            {
                'order': 2,
                'step_label': '',
                'resource': {
                    'name': "Identifier l'autorité compétente pour ma demande",
                    'description': "Selon votre diplôme et votre profession, vous devez contacter une autorité différente. Se tromper d'autorité retarde le processus.",
                    'tags': ['Reconnaissance diplome', 'Formation', 'Documents officiels'],
                    'body': body(
                        sec("Quelle autorité contacter",
                            ul(
                                "<b>SERI</b> (Secrétariat d'État à la formation) → professions réglementées non médicales + attestations de niveau → <a href='https://www.recognition.swiss' target='_blank'>recognition.swiss</a>",
                                "<b>Croix-Rouge Suisse (CRS)</b> → infirmiers, sages-femmes → <a href='https://www.redcross.ch' target='_blank'>redcross.ch</a>, CHF 680",
                                "<b>CDIP</b> → enseignants (tous niveaux) → <a href='https://www.cdip.ch' target='_blank'>cdip.ch</a>",
                                "<b>Swiss ENIC / swissuniversities</b> → diplômes universitaires (sur demande de l'employeur) → <a href='https://www.anerkennung.swiss' target='_blank'>anerkennung.swiss</a>",
                            ),
                        ),
                        sec("Cas des médecins",
                            para("Les médecins ressortissants UE/AELE bénéficient d'une reconnaissance facilitée via le SERI. La demande se fait sur recognition.swiss. Délai : 3 à 6 mois. Frais : CHF 550."),
                        ),
                    ),
                },
            },
            {
                'order': 3,
                'step_label': '',
                'resource': {
                    'name': "Préparer les documents requis",
                    'description': "Rassemblez tous vos documents avant de déposer la demande. Tout doit être en format PDF. Une pièce manquante bloque le traitement.",
                    'tags': ['Reconnaissance diplome', 'Documents officiels', 'Formulaire'],
                    'body': body(
                        sec("Documents obligatoires",
                            ul(
                                "Diplôme original, <b>copie certifiée conforme</b> par une autorité officielle (notaire, ambassade)",
                                "Relevés de notes complets",
                                "Pièce d'identité ou permis de séjour en cours de validité",
                            ),
                        ),
                        sec("Traduction",
                            ul(
                                "Traduction certifiée obligatoire si le document n'est <b>pas</b> en allemand, français, italien ou anglais",
                                "Les diplômes en anglais ne nécessitent pas de traduction",
                                "La traduction doit être faite par un traducteur assermenté",
                            ),
                        ),
                        sec("Format",
                            para("Tous les fichiers doivent être soumis en PDF. La qualité de numérisation doit permettre une lecture claire de tous les éléments (sceaux, signatures)."),
                        ),
                    ),
                },
            },
            {
                'order': 4,
                'step_label': '',
                'resource': {
                    'name': "Déposer la demande en ligne sur recognition.swiss",
                    'description': "La demande se fait entièrement en ligne. Créez un compte, téléversez vos documents et payez les frais de traitement.",
                    'tags': ['Reconnaissance diplome', 'En ligne', 'Formulaire'],
                    'body': body(
                        sec("Procédure",
                            ol(
                                "Rendez-vous sur <a href='https://www.recognition.swiss' target='_blank'>recognition.swiss</a>",
                                "Créez un compte personnel",
                                "Remplissez le formulaire de demande en ligne",
                                "Téléversez vos documents en PDF",
                                "Payez les frais en ligne",
                            ),
                        ),
                        sec("Frais",
                            ul(
                                "<b>Attestation de niveau</b> (profession non réglementée) : <b>CHF 350</b>",
                                "<b>Profession réglementée</b> (via SERI) : <b>CHF 550</b>",
                                "Croix-Rouge Suisse (infirmiers) : <b>CHF 680</b>",
                            ),
                        ),
                        sec("Après le dépôt",
                            para("Le SERI vous contacte par email dans les <b>4 semaines</b> suivant le dépôt pour confirmer la réception ou demander des documents complémentaires."),
                        ),
                    ),
                },
            },
            {
                'order': 5,
                'step_label': '',
                'resource': {
                    'name': "Attendre la décision et les éventuelles mesures complémentaires",
                    'description': "Le délai varie selon le type de demande. En cas de formation insuffisante, des mesures complémentaires peuvent être exigées avant la reconnaissance définitive.",
                    'tags': ['Reconnaissance diplome', 'Formation'],
                    'body': body(
                        sec("Délais de traitement",
                            ul(
                                "<b>Attestation de niveau</b> (profession non réglementée) : quelques semaines",
                                "<b>Profession réglementée</b> : 3 à 12 mois selon la complexité",
                                "Les délais peuvent être plus longs en cas de forte demande",
                            ),
                        ),
                        sec("Si des lacunes sont identifiées",
                            para("Si votre formation est jugée insuffisante par rapport aux standards suisses, le SERI peut exiger :"),
                            ul(
                                "Un stage professionnel en Suisse",
                                "Un examen d'aptitude (épreuve théorique ou pratique)",
                                "Une formation complémentaire dans un établissement suisse",
                            ),
                        ),
                        sec("Besoin d'aide",
                            para("Le COSM à Neuchâtel peut vous accompagner pour comprendre la décision et préparer les étapes suivantes. Contact : 032 889 74 42, cosm@ne.ch"),
                        ),
                    ),
                },
            },
        ],
    },

    # -----------------------------------------------------------------------
    {
        'title': "S'assurer avec la LAMal, assurance maladie obligatoire",
        'category': 'Health',
        'description': "Toute personne qui habite en Suisse doit avoir une assurance maladie. Vous avez 3 mois après l'arrivée pour choisir votre caisse.",
        'order': 3,
        'steps': [
            {
                'order': 1,
                'step_label': '',
                'resource': {
                    'name': "Comprendre l'obligation d'assurance maladie (LAMal)",
                    'description': "En Suisse, l'assurance maladie est obligatoire pour tout résident. Même avec un permis N, F ou S. Le délai est de 3 mois après l'arrivée.",
                    'tags': ['Assurance maladie', 'Sante', 'Droits'],
                    'body': body(
                        sec("Ce que vous devez savoir",
                            ul(
                                "Toute personne résidant en Suisse <b>plus de 3 mois</b> doit être assurée",
                                "Délai : <b>3 mois</b> après l'arrivée en Suisse pour souscrire",
                                "La couverture est <b>rétroactive</b> au premier jour d'arrivée, même si vous souscrivez dans le délai",
                                "Si vous ne souscrivez pas à temps, le canton vous assigne automatiquement à une caisse, souvent parmi les plus chères",
                            ),
                        ),
                        sec("Permis N, F et S",
                            para("Les titulaires de permis N, F ou S sont aussi soumis à l'obligation. Dans de nombreux cas, les primes sont prises en charge directement par le canton. Renseignez-vous auprès de votre assistant social ou du COSM (032 889 74 42)."),
                        ),
                    ),
                },
            },
            {
                'order': 2,
                'step_label': '',
                'resource': {
                    'name': "Vérifier mon droit aux subsides (réduction de prime)",
                    'description': "Si vos revenus sont modestes, le canton peut rembourser une partie ou la totalité de votre prime mensuelle. Cela s'appelle les subsides.",
                    'tags': ['Assurance maladie', 'Reduction de prime', 'Aide sociale', 'Formulaire'],
                    'body': body(
                        sec("Qui peut demander des subsides",
                            para("Toute personne avec un revenu bas ou modeste peut demander des subsides, quelle que soit sa nationalité ou son permis de séjour."),
                        ),
                        sec("Comment faire la demande à Neuchâtel",
                            ul(
                                "En ligne sur <a href='https://www.guichet.ne.ch' target='_blank'>guichet.ne.ch</a>",
                                "Ou directement à votre commune de résidence",
                                "Le Service des subsides du canton examine votre dossier",
                            ),
                        ),
                        sec("Points importants",
                            ul(
                                "Faites la demande <b>dès votre inscription</b> à l'assurance maladie",
                                "Les subsides ne sont pas rétroactifs au-delà de l'année en cours",
                                "<b>Contact :</b> Service des subsides Neuchâtel, 032 889 74 00",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 3,
                'step_label': '',
                'resource': {
                    'name': "Comparer les caisses maladie",
                    'description': "Il existe plus de 80 caisses en Suisse. Les primes varient selon la caisse, la franchise et le modèle. Comparer peut faire une différence importante sur votre budget.",
                    'tags': ['Assurance maladie', 'Budget', 'En ligne'],
                    'body': body(
                        sec("Où comparer",
                            ul(
                                "<a href='https://www.comparis.ch' target='_blank'>comparis.ch</a>, comparateur gratuit en ligne",
                                "<a href='https://www.bonus.ch' target='_blank'>bonus.ch</a>, autre comparateur gratuit",
                                "<b>OCAM</b> (Office cantonal d'assurance maladie Neuchâtel), conseil gratuit et neutre : <b>032 889 74 74</b>",
                            ),
                        ),
                        sec("Franchise, que choisir",
                            para("La franchise est le montant que vous payez vous-même chaque année avant que la caisse rembourse. Choix possible : CHF 300 à CHF 2 500."),
                            ul(
                                "<b>Franchise basse (CHF 300)</b> → prime mensuelle élevée → si vous allez souvent chez le médecin",
                                "<b>Franchise haute (CHF 2 500)</b> → prime mensuelle basse → si vous êtes rarement malade",
                            ),
                        ),
                        sec("Modèle de couverture",
                            ul(
                                "<b>Standard</b>, libre choix du médecin (prime plus élevée)",
                                "<b>Médecin de famille</b>, vous devez d'abord appeler votre médecin traitant (moins cher)",
                                "<b>HMO</b>, suivi dans un centre médical agréé (moins cher)",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 4,
                'step_label': '',
                'resource': {
                    'name': "Souscrire à l'assurance maladie",
                    'description': "Une fois votre caisse choisie, l'inscription peut se faire en ligne, par courrier ou en agence. Vous recevez votre carte d'assuré par courrier.",
                    'tags': ['Assurance maladie', 'En ligne', 'Formulaire'],
                    'body': body(
                        sec("Documents nécessaires",
                            ul(
                                "Attestation de domicile : bail signé ou attestation de la commune",
                                "Pièce d'identité ou permis de séjour valide",
                                "Pour les enfants : acte de naissance",
                            ),
                        ),
                        sec("Inscription",
                            ul(
                                "La plupart des caisses acceptent une inscription <b>en ligne en 15 à 30 minutes</b>",
                                "Vous recevez votre carte d'assuré par courrier dans les 2 à 3 semaines",
                                "Conservez cette carte, elle est indispensable à chaque consultation médicale",
                            ),
                        ),
                    ),
                },
            },
            {
                'order': 5,
                'step_label': '',
                'resource': {
                    'name': "Payer les primes et éviter les arriérés",
                    'description': "Les primes se paient chaque mois. Un retard peut entraîner une suspension de couverture et des poursuites. En cas de difficulté, contactez votre caisse rapidement.",
                    'tags': ['Assurance maladie', 'Budget', 'Aide sociale'],
                    'body': body(
                        sec("Règles de paiement",
                            ul(
                                "Payez votre prime dans les délais fixés par votre caisse (généralement le 1er du mois)",
                                "Un retard peut entraîner une <b>suspension du remboursement des soins</b> et des <b>poursuites judiciaires</b>",
                                "En cas de difficulté : contactez votre caisse immédiatement pour un plan de paiement",
                            ),
                        ),
                        sec("Si votre situation change",
                            para("Si vous perdez votre emploi ou si vos revenus baissent, refaites une demande de subsides. Votre prime peut être réduite."),
                            ul(
                                "<b>Service des subsides Neuchâtel :</b> 032 889 74 00",
                                "<b>OCAM (questions sur l'assurance) :</b> 032 889 74 74",
                            ),
                        ),
                    ),
                },
            },
        ],
    },

]


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
            ResourceFeedback.objects.all().delete()
            Profile.objects.all().delete()
            GuideStep.objects.all().delete()
            Guide.objects.all().delete()
            Resource.objects.all().delete()
            Subcategory.objects.all().delete()
            Category.objects.all().delete()
            Audience.objects.all().delete()
            Tag.objects.all().delete()
            self.stdout.write('  Données existantes supprimées.')

        # -- Contributors + accès invités --
        self.stdout.write('\nContributors et accès invités...')
        cosm, _ = Contributor.objects.get_or_create(name='COSM', defaults={'is_default': True})
        if not cosm.is_default:
            cosm.is_default = True
            cosm.save()
        guest_orgs = {}
        for org_name in ['Caritas Neuchâtel', 'RECIF', 'Croix-Rouge Neuchâtel']:
            org, _ = Contributor.objects.get_or_create(name=org_name)
            guest_orgs[org_name] = org
        self.stdout.write(f'  + COSM (défaut) + {len(guest_orgs)} organisations invitées')

        # Groupe "Guests" : peut écrire/éditer des ressources via le CMS, sans approuver.
        guests_group, _ = Group.objects.get_or_create(name='Guests')
        wanted_perms = [
            ('wagtailadmin', 'access_admin'),
            ('pin_prototype', 'add_resource'),
            ('pin_prototype', 'change_resource'),
            ('pin_prototype', 'view_resource'),
            ('pin_prototype', 'view_contributor'),
        ]
        perms = []
        for app_label, codename in wanted_perms:
            p = Permission.objects.filter(content_type__app_label=app_label, codename=codename).first()
            if p:
                perms.append(p)
        guests_group.permissions.set(perms)

        # Utilisateur invité de démo (Caritas), login: caritas / caritas123
        User = get_user_model()
        guest_user, created = User.objects.get_or_create(
            username='caritas',
            defaults={'email': 'caritas@example.org', 'is_staff': False, 'is_active': True},
        )
        if created:
            guest_user.set_password('caritas123')
            guest_user.save()
        guest_user.groups.add(guests_group)
        guest_orgs['Caritas Neuchâtel'].editors.add(guest_user)
        self.stdout.write('  + Groupe "Guests" + invité de démo (caritas / caritas123)')

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

        # Lieu générique pour remplir les ressources sans contact propre.
        GENERIC_PLACE = dict(
            name='COSM Neuchâtel', city='Neuchâtel',
            address='Rue des Beaux-Arts 13, 2000 Neuchâtel',
            phone='032 889 66 87', email='cosm@ne.ch',
            latitude=46.9931, longitude=6.9398,
        )

        def add_places(resource, extracted):
            if resource.places.exists():
                return
            items = extracted or [GENERIC_PLACE]
            for i, pl in enumerate(items):
                ResourcePlace(resource=resource, sort_order=i, **pl).save(geocode=False)

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
                res_data.pop('audiences', None)  # resources link to tags only
                old_body = res_data.pop('body', None)

                section_values = {k: res_data.get(k, '') for k in SECTION_FIELDS}
                # If no hand-written sections, derive them from the old body.
                if old_body and not any(section_values[k] for k in ('why_interesting', 'how_to', 'location')):
                    derived = split_body(old_body)
                    section_values['why_interesting'] = derived['why']
                    section_values['how_to'] = derived['how']
                    section_values['location'] = derived['location']
                # Coherent hand-written "why is it interesting" (first gabarit
                # section), added everywhere it was missing or weak.
                authored_why = RESOURCE_WHY.get(res_data['name'])
                if authored_why:
                    section_values['why_interesting'] = authored_why
                # Coherent hand-written "how to" (action-first, meaningful
                # sub-headings) replacing the messy auto-bucketed version.
                authored_how = RESOURCE_HOW.get(res_data['name'])
                if authored_how:
                    section_values['how_to'] = authored_how
                # Move contact cards out of the location text into structured places.
                extracted = extract_places_from_html(section_values['location'])
                if extracted:
                    section_values['location'] = ''

                res, res_created = Resource.objects.get_or_create(
                    name=res_data['name'], category=cat,
                    defaults={**section_values, 'author': cosm, 'status': Resource.STATUS_APPROVED},
                )
                if not res_created:
                    for f, v in section_values.items():
                        setattr(res, f, v)
                    res.author = cosm
                    res.status = Resource.STATUS_APPROVED
                    res.save(update_fields=list(SECTION_FIELDS) + ['author', 'status'])

                res.tags.set([tag_map[t] for t in tag_labels if t in tag_map])

                subcat_name = RESOURCE_SUBCATEGORY.get(res.name)
                res.subcategory = subcat_map.get(subcat_name)
                res.save(update_fields=['subcategory'])

                res.body = section_stream_blocks(
                    section_values['why_interesting'], section_values['how_to'], section_values['location'])
                res.save(update_fields=['body'])

                add_places(res, extracted)

                self.stdout.write(f'      {"+" if res_created else "~"} {res.name}')

        # -- Démo : une ressource soumise par un invité, en attente de validation --
        edu_cat = Category.objects.filter(name='Education').first()
        demo, demo_created = Resource.objects.get_or_create(
            name="Atelier conversation français (Caritas)",
            defaults={
                'category': edu_cat,
                'description': "Un atelier hebdomadaire pour pratiquer le français à l'oral, animé par des bénévoles de Caritas.",
                'why_interesting': RESOURCE_WHY.get("Atelier conversation français (Caritas)", ''),
                'how_to': h3('Comment participer') + ul(
                    'Venez sans inscription le mardi après-midi',
                    'Gratuit et ouvert à tous les niveaux',
                ),
                'location': h3('Caritas Neuchâtel') + ul(
                    '<b>Adresse :</b> Rue du Vieux-Châtel 4, 2000 Neuchâtel',
                    '<b>Téléphone :</b> 032 886 80 70',
                ),
                'author': guest_orgs['Caritas Neuchâtel'],
                'status': Resource.STATUS_PENDING,
            },
        )
        demo.author = guest_orgs['Caritas Neuchâtel']
        demo.status = Resource.STATUS_PENDING
        demo.why_interesting = RESOURCE_WHY.get("Atelier conversation français (Caritas)", demo.why_interesting)
        demo.how_to = RESOURCE_HOW.get("Atelier conversation français (Caritas)", demo.how_to)
        demo_places = extract_places_from_html(demo.location)
        if demo_places:
            demo.location = ''
        demo.save(update_fields=['author', 'status', 'location', 'why_interesting', 'how_to'])
        demo.body = section_stream_blocks(demo.why_interesting, demo.how_to, demo.location)
        demo.save(update_fields=['body'])
        add_places(demo, demo_places)
        self.stdout.write(f'  {"+" if demo_created else "~"} Démo en attente: {demo.name}')

        # -- Parcours --
        self.stdout.write('\nCréation des parcours...')
        for pw_data in PATHWAYS:
            steps_data = pw_data['steps']
            pw_category = Category.objects.filter(name=pw_data.get('category')).first()
            pw, pw_created = Guide.objects.get_or_create(
                title=pw_data['title'],
                defaults={
                    'description': pw_data['description'],
                    'order': pw_data['order'],
                    'category': pw_category,
                },
            )
            if not pw_created:
                pw.description = pw_data['description']
                pw.order = pw_data['order']
                pw.category = pw_category
                pw.save()
            self.stdout.write(f'  {"+" if pw_created else "~"} Guide: {pw.title}')

            for step_data in steps_data:
                res_data = step_data['resource']
                tag_labels = res_data.get('tags', [])
                section_values = {k: res_data.get(k, '') for k in SECTION_FIELDS}
                old_body = res_data.get('body')
                if old_body and not any(section_values[k] for k in ('why_interesting', 'how_to', 'location')):
                    derived = split_body(old_body)
                    section_values['why_interesting'] = derived['why']
                    section_values['how_to'] = derived['how']
                    section_values['location'] = derived['location']
                extracted = extract_places_from_html(section_values['location'])
                if extracted:
                    section_values['location'] = ''
                res, res_created = Resource.objects.get_or_create(
                    name=res_data['name'],
                    category=None,
                    defaults={**section_values, 'author': cosm, 'status': Resource.STATUS_APPROVED},
                )
                res.tags.set([tag_map[t] for t in tag_labels if t in tag_map])
                for f, v in section_values.items():
                    setattr(res, f, v)
                res.author = cosm
                res.status = Resource.STATUS_APPROVED
                res.save(update_fields=list(SECTION_FIELDS) + ['author', 'status'])
                res.body = section_stream_blocks(
                    section_values['why_interesting'], section_values['how_to'], section_values['location'])
                res.save(update_fields=['body'])
                add_places(res, extracted)
                self.stdout.write(f'      {"+" if res_created else "~"} Resource: {res.name}')

                ps, _ = GuideStep.objects.get_or_create(
                    guide=pw,
                    sort_order=step_data['order'],
                    defaults={'resource': res, 'step_label': step_data.get('step_label', '')},
                )
                if not _:
                    ps.resource = res
                    ps.step_label = step_data.get('step_label', '')
                    ps.save()

        # -- Traductions UK (démo de la file de validation) --
        # Le contenu est traduit en ukrainien (le russe reste une langue
        # d'interface mais pas une langue de contenu). 2 fiches approuvées,
        # 2 en attente. Le reste passe par `python manage.py translate_resources`.
        self.stdout.write('\nCréation des traductions UK (démo)...')
        UK_TRANSLATIONS = [
            {
                'fr': "Je dois m'assurer contre la maladie",
                'status': ResourceTranslation.STATUS_APPROVED,
                'name': "Мені потрібно оформити медичне страхування",
                'description': "У Швейцарії страхування обов'язкове для всіх. Оформіть його протягом 3 місяців після приїзду.",
                'why': para("У Швейцарії базове медичне страхування називається LAMal. Воно обов'язкове для всіх.")
                       + ul("У вас є 3 місяці після приїзду, щоб оформити його",
                            "Усі каси зобов'язані вас прийняти, вони не можуть відмовити"),
                'how': h3("Як вибрати та оформити") + ol(
                    "Порівняйте тарифи на comparis.ch (вкажіть кантон NE та ваш вік)",
                    "Виберіть франшизу",
                    "Зв'яжіться напряму з вибраною касою",
                    "Потім попросіть знижку внеску, якщо дохід невеликий",
                ),
            },
            {
                'fr': "Je cherche un médecin de famille",
                'status': ResourceTranslation.STATUS_APPROVED,
                'name': "Я шукаю сімейного лікаря",
                'description': "Я хочу знайти терапевта, який приймає нових пацієнтів у кантоні Невшатель.",
                'why': para("У Швейцарії сімейний лікар, це перший контакт з усіх питань здоров'я. Він направляє до спеціалістів за потреби."),
                'how': h3("Як шукати") + ol(
                    "Шукайте на doctorfmh.ch, офіційний реєстр лікарів",
                    "Записуйтесь онлайн на onedoc.ch",
                    "Телефонуйте до кабінетів поряд із домом",
                ),
            },
            {
                'fr': "Je cherche du travail, par où commencer ?",
                'status': ResourceTranslation.STATUS_PENDING,
                'name': "Я шукаю роботу, з чого почати?",
                'description': "ONE допомагає шукати роботу. Якщо ви сплачували внески у Швейцарії, ви можете отримувати допомогу під час пошуку.",
                'why': para("ORP (Регіональне бюро працевлаштування) у Невшателі називається ONE. Це державна служба, яка допомагає безробітним знайти роботу.")
                       + para("Якщо ви працювали у Швейцарії та сплачували внески на страхування від безробіття, ви можете отримувати допомогу, гроші щомісяця під час пошуку."),
                'how': h3("Хто може зареєструватися") + ul(
                    "Ви працювали у Швейцарії та сплачували внески",
                    "У вас є дійсний дозвіл на проживання (B, C або іноді L)",
                ) + h3("Кроки") + ol(
                    "Зареєструйтеся в перший же день без роботи, не чекайте",
                    "Онлайн на arbeit.swiss (цілодобово)",
                    "ONE зв'яжеться з вами протягом 24-48 годин",
                ),
            },
            {
                'fr': "Je veux payer moins cher mon assurance maladie",
                'status': ResourceTranslation.STATUS_PENDING,
                'name': "Я хочу платити менше за медичне страхування",
                'description': "Якщо дохід невеликий, держава може оплатити частину страхування. Ця допомога називається subside.",
                'why': para("Subside, це допомога кантону. Вона зменшує або покриває ваш страховий внесок, якщо дохід невеликий."),
                'how': h3("Як подати заявку") + ol(
                    "Зверніться до GSR вашої комуни",
                    "Принесіть довідки про доходи та склад родини",
                    "GSR передає вашу справу в OCAB",
                ),
            },
        ]
        n_tr = n_pending = 0
        for t in UK_TRANSLATIONS:
            res = Resource.objects.filter(name=t['fr']).first()
            if not res:
                continue
            ResourceTranslation.objects.update_or_create(
                resource=res, language='uk',
                defaults={
                    'name': t['name'],
                    'description': t['description'],
                    'body': section_stream_blocks(t.get('why', ''), t.get('how', ''), t.get('location', '')),
                    'status': t['status'],
                },
            )
            n_tr += 1
            n_pending += t['status'] == ResourceTranslation.STATUS_PENDING
        self.stdout.write(f'  + {n_tr} traductions UK ({n_pending} en attente de validation)')

        # -- Profils de démonstration + likes communautaires --
        # Crée de faux profils qui jugent des ressources utiles, afin que les
        # mentions « recommandé par des profils similaires » apparaissent
        # naturellement, par langue et par statut, sans intervention manuelle.
        # Idempotent : ignoré si des avis existent déjà (vrais ou semés).
        if ResourceFeedback.objects.count() == 0:
            self.stdout.write('\nProfils de démonstration et likes communautaires...')
            standalone = list(
                Resource.objects
                .filter(status=Resource.STATUS_APPROVED, category__isnull=False)
                .order_by('name')
            )
            # n profils partageant (langue, statut), aimant une tranche de ressources.
            # Le seuil de cohorte étant COMMUNITY_MIN_LIKES = 2, chaque tranche est
            # aimée par au moins 2 profils pour déclencher la mention.
            # Each cohort is a small group of coherent personas (same situation)
            # liking the same slice of resources. A real visitor whose profile
            # resembles one of these personas will see those resources flagged
            # « recommandé par des profils similaires ».
            COHORTS = [
                {'n': 3, 'slice': (0, 3), 'profile': dict(
                    language='uk', status='S', french_level='A2', has_children=True,
                    arrived_over_year_ago=False, computer_skills='basic',
                    education_level='bachelor', origin_sector='healthcare',
                    birth_date=date(1990, 4, 12))},
                {'n': 3, 'slice': (2, 5), 'profile': dict(
                    language='ru', status='F', french_level='B1', has_children=True,
                    arrived_over_year_ago=True, computer_skills='basic',
                    education_level='vocational', origin_sector='trade',
                    birth_date=date(1975, 9, 3))},
                {'n': 2, 'slice': (5, 7), 'profile': dict(
                    language='fr', status='C', french_level='C1', has_children=False,
                    arrived_over_year_ago=True, computer_skills='advanced',
                    education_level='master_plus', origin_sector='it',
                    birth_date=date(2000, 1, 20))},
                {'n': 3, 'slice': (7, 10), 'profile': dict(
                    language='en', status='N', french_level='none', has_children=False,
                    arrived_over_year_ago=False, computer_skills='basic',
                    education_level='vocational', origin_sector='construction',
                    birth_date=date(1995, 6, 15))},
            ]
            n_profiles = n_likes = 0
            for c in COHORTS:
                liked = standalone[c['slice'][0]:c['slice'][1]]
                if not liked:
                    continue
                for _ in range(c['n']):
                    p = Profile.objects.create(**c['profile'])
                    n_profiles += 1
                    for res in liked:
                        ResourceFeedback.objects.create(profile=p, resource=res, is_useful=True)
                        n_likes += 1
            self.stdout.write(f'  + {n_profiles} profils, {n_likes} avis utiles')
        else:
            self.stdout.write('\nLikes communautaires ignorés (des avis existent déjà).')

        self.stdout.write(self.style.SUCCESS('\nSeed terminé.'))
