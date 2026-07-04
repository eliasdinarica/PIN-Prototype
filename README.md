# PIN-Prototype

Projet full-stack : backend **Django + Wagtail** (API REST, SQLite) et frontend **Vue 3 + Vite**.
Les deux tournent sur des serveurs de développement séparés.

## Prérequis

- Python 3.13
- Node.js 18+ et npm

## Backend (Django + Wagtail)

```bash
cd backend

# Environnement virtuel (déjà présent dans backend/venv ; sinon le créer)
python -m venv venv
source venv/Scripts/activate      # Git Bash / macOS / Linux
# venv\Scripts\activate           # Windows (cmd / PowerShell)

pip install -r requirements.txt

python manage.py migrate
python manage.py seed             # données de démo (ajouter --reset pour tout regénérer)
python manage.py createsuperuser  # compte d'administration (Django + Wagtail)
python manage.py runserver        # http://localhost:8000
```

Accès une fois le serveur lancé :

| Élément            | URL                              |
|--------------------|----------------------------------|
| API REST           | http://localhost:8000/api/       |
| Admin Django       | http://localhost:8000/admin/     |
| CMS Wagtail        | http://localhost:8000/cms/       |

## Frontend (Vue 3 + Vite)

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

Build de production :

```bash
npm run build      # génère dist/
npm run preview    # sert le build localement
```

Le frontend appelle l'API sur `http://localhost:8000` par défaut. Pour pointer ailleurs, créer un fichier `frontend/.env` :

```
VITE_API_URL=http://localhost:8000
```

## Variables d'environnement (backend/.env)

Toutes optionnelles (valeurs par défaut fournies). Seules les fonctions **IA** (recherche par chatbot et commande de traduction) nécessitent une configuration :

| Variable                | Rôle                                              | Défaut               |
|-------------------------|---------------------------------------------------|----------------------|
| `INFOMANIAK_API_KEY`    | Clé API IA — requise pour le chatbot / traduction | *(vide)*             |
| `INFOMANIAK_PRODUCT_ID` | Identifiant produit IA — requis pour l'IA         | *(vide)*             |
| `INFOMANIAK_MODEL`      | Modèle IA                                         | `mistral3`           |
| `SECRET_KEY`            | Clé secrète Django                                | valeur de dev        |
| `DEBUG`                 | Mode debug                                        | `True`               |
| `ALLOWED_HOSTS`         | Hôtes autorisés (séparés par des virgules)        | *(vide)*             |
| `CORS_ALLOWED_ORIGINS`  | Origines CORS autorisées                          | `http://localhost:5173` |
| `WAGTAILADMIN_BASE_URL` | URL de base du CMS                                | `http://localhost:8000` |

Sans configuration IA, toute l'application fonctionne, seuls le chatbot et la traduction automatique sont indisponibles.

## Traductions du contenu (ukrainien)

Le contenu (fiches et guides) peut être traduit en ukrainien par l'IA :

```bash
python manage.py translate_resources --lang uk          # traduire ce qui a changé / est nouveau
python manage.py translate_resources --lang uk --force  # tout re-traduire
```

> [!IMPORTANT]
> **Par défaut, les traductions sont APPROUVÉES et affichées immédiatement dans l'app.**
> Une **dizaine de fiches** sont volontairement laissées **« en attente de validation »**
> (réparties sur plusieurs catégories) pour illustrer le circuit de relecture du COSM.
>
> - Une traduction **en attente n'est pas montrée** aux usagers : l'app affiche le **français**
>   tant qu'elle n'a pas été approuvée.
> - **Approuver une traduction** : CMS Wagtail (`http://localhost:8000/cms/`) →
>   menu **« Translations to validate »** → sélectionner les traductions relues →
>   action groupée **« Approve »**.

Options de la commande :

| Option        | Rôle                                                                    | Défaut |
|---------------|-------------------------------------------------------------------------|--------|
| `--pending N` | Nombre de fiches laissées en attente de validation (`0` = tout approuver) | `10`   |
| `--force`     | Re-traduire même si une traduction existe déjà                          | —      |
| `--lang`      | Langue cible (seul `uk` est pris en charge pour le contenu)             | `uk`   |

## Synthèse vocale (lecture audio)

Le bouton de lecture audio des fiches génère l'audio **côté serveur** (endpoint
`POST /api/tts/`) via [`edge-tts`](https://pypi.org/project/edge-tts/) — les voix
neurales en ligne de Microsoft Edge, **gratuites et sans clé API**.

- Fonctionne de façon identique sur tous les appareils, y compris en **ukrainien**
  (avant, la lecture dépendait des voix installées sur la machine, d'où le silence
  sur le cyrillique). Aucune configuration nécessaire.
- Le backend doit avoir un **accès Internet** sortant. Les audios sont mis en cache
  sur disque dans `backend/tts_cache/` (ignoré par git) : la relecture est instantanée.

## Commandes utiles (backend)

```bash
python manage.py seed [--reset]                  # (re)générer les données de démo
python manage.py translate_resources --lang uk   # traduire le contenu (nécessite l'IA)
python manage.py makemigrations                  # générer les migrations
python manage.py migrate                         # appliquer les migrations
python manage.py test pin_prototype              # lancer les tests
```
