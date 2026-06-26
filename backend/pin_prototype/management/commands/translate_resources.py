import hashlib
import json
import re

from django.conf import settings
from django.core.management.base import BaseCommand
from pin_prototype.ai import chat_completion
from pin_prototype.models import Resource, ResourceTranslation, resource_section_dicts

# Target languages supported by the script. Kept simple: Russian only for now.
LANGUAGES = {'ru': 'Russian'}

# Sidecar file remembering the source hash translated for each (resource, lang).
# Lets periodic runs translate only what changed — no data-model change needed.
STATE_FILE = settings.BASE_DIR / 'translation_state.json'


def _payload(resource):
    """The translatable content of a resource: name, description and the text of
    each body section (the section `kind` is structural and stays untouched)."""
    return {
        'name': resource.name or '',
        'description': resource.description or '',
        'sections': resource_section_dicts(resource),
    }


def source_hash(resource):
    payload = json.dumps(_payload(resource), ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(payload.encode('utf-8')).hexdigest()


def load_state():
    try:
        return json.loads(STATE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def save_state(state):
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=0), encoding='utf-8')


SYSTEM_PROMPT = (
    "You are a professional translator for a public-service website that helps "
    "migrants in Switzerland. Translate the VALUES of the given JSON object from "
    "French to {language}. Rules:\n"
    "- Keep the JSON keys exactly as they are.\n"
    "- Keep every HTML tag, attribute and URL exactly as in the source.\n"
    "- Do not translate proper nouns, place names, organisation names, emails, "
    "phone numbers or addresses.\n"
    "- Use simple, clear wording (easy-to-read style).\n"
    "- Return ONLY the translated JSON object, nothing else."
)


def _parse_json(raw):
    m = re.search(r'\{.*\}', raw, re.DOTALL)
    return json.loads(m.group()) if m else {}


def _flatten(payload):
    """Flatten the payload into a single-level JSON dict of values to translate —
    the AI handles a flat object far more reliably than nested arrays."""
    flat = {'name': payload['name'], 'description': payload['description']}
    for i, section in enumerate(payload['sections']):
        if section.get('heading'):
            flat[f'heading_{i}'] = section['heading']
        flat[f'content_{i}'] = section['content']
    return flat


class Command(BaseCommand):
    help = 'Translate approved resources into another language using the AI.'

    def add_arguments(self, parser):
        parser.add_argument('--lang', default='ru', help='Target language code (default: ru).')
        parser.add_argument('--limit', type=int, default=0, help='Only translate the first N resources (0 = all).')
        parser.add_argument('--force', action='store_true', help='Re-translate even if a translation already exists.')

    def handle(self, *args, **options):
        lang = options['lang']
        if lang not in LANGUAGES:
            self.stderr.write(f"Unsupported language '{lang}'. Available: {', '.join(LANGUAGES)}")
            return
        language_name = LANGUAGES[lang]
        system = SYSTEM_PROMPT.format(language=language_name)
        force = options['force']

        state = load_state()
        resources = Resource.objects.filter(status=Resource.STATUS_APPROVED).order_by('id')
        translated_ids = set(
            ResourceTranslation.objects.filter(language=lang).values_list('resource_id', flat=True)
        )

        # Decide what needs (re)translating, based on the source content hash.
        todo = []
        for resource in resources:
            key = str(resource.id)
            h = source_hash(resource)
            prev = state.get(key, {}).get(lang)
            if force or resource.id not in translated_ids:
                todo.append((resource, h))
            elif prev is None:
                # Already translated before change-tracking existed → assume current.
                state.setdefault(key, {})[lang] = h
            elif prev != h:
                todo.append((resource, h))  # source changed since last translation

        if options['limit']:
            todo = todo[:options['limit']]

        self.stdout.write(f'{len(todo)} resource(s) to translate to {language_name} (changed or new).')
        done = 0
        for resource, h in todo:
            payload = _payload(resource)
            flat = _flatten(payload)
            if not any(v for v in flat.values()):
                continue
            try:
                raw = chat_completion([
                    {'role': 'system', 'content': system},
                    {'role': 'user', 'content': json.dumps(flat, ensure_ascii=False)},
                ])
                translated = _parse_json(raw)
            except Exception as e:
                self.stdout.write(f'  --  #{resource.id} {resource.name[:40]} (error: {e})')
                continue

            # Rebuild the translated body as StreamField section blocks,
            # keeping each section's kind.
            sections_out = []
            for i, section in enumerate(payload['sections']):
                sections_out.append(('section', {
                    'kind': section['kind'],
                    'heading': translated.get(f'heading_{i}', section['heading']),
                    'content': translated.get(f'content_{i}') or section['content'],
                }))

            # Standalone fiches enter the validation queue (pending). Guide-step
            # resources (no category) are not validated individually — they are
            # reviewed with their guide — so their translation is auto-approved.
            status = (
                ResourceTranslation.STATUS_APPROVED if resource.category_id is None
                else ResourceTranslation.STATUS_PENDING
            )
            ResourceTranslation.objects.update_or_create(
                resource=resource, language=lang,
                defaults={
                    'name': translated.get('name') or '',
                    'description': translated.get('description') or '',
                    'body': sections_out,
                    'status': status,
                },
            )
            state.setdefault(str(resource.id), {})[lang] = h
            done += 1
            self.stdout.write(f'  OK  #{resource.id} {resource.name[:40]}')

        save_state(state)
        self.stdout.write(self.style.SUCCESS(f'\nTranslated {done}/{len(todo)} resources to {language_name}.'))
