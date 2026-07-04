"""Server-side text-to-speech.

The browser Web Speech API can only use voices installed on the visitor's own
device — so Ukrainian (Cyrillic) stayed silent on any machine without a
Ukrainian voice pack. To make audio work the same everywhere, we synthesise it
on the server with `edge-tts` (Microsoft Edge's free online neural voices, no
API key) and let the frontend play the returned MP3.
"""
import asyncio
import hashlib
import re

from django.conf import settings
from django.http import HttpResponse
from rest_framework.decorators import api_view
from rest_framework.response import Response

# One neural voice per supported language (Swiss French where available).
TTS_VOICES = {
    'fr': 'fr-CH-ArianeNeural',
    'uk': 'uk-UA-PolinaNeural',
    'ru': 'ru-RU-SvetlanaNeural',
    'en': 'en-GB-SoniaNeural',
}
DEFAULT_LANG = 'fr'
MAX_CHARS = 3000
CACHE_DIR = settings.BASE_DIR / 'tts_cache'


def _synthesize(text, voice):
    """Collect the MP3 bytes produced by edge-tts for one utterance."""
    import edge_tts

    async def run():
        buf = bytearray()
        async for chunk in edge_tts.Communicate(text, voice).stream():
            if chunk['type'] == 'audio':
                buf.extend(chunk['data'])
        return bytes(buf)

    return asyncio.run(run())


@api_view(['POST'])
def tts_view(request):
    """Return an MP3 reading `text` in `lang`. Results are cached on disk by
    content hash, so replaying the same passage is instant and free."""
    text = re.sub(r'\s+', ' ', (request.data.get('text') or '')).strip()[:MAX_CHARS]
    lang = request.data.get('lang') or DEFAULT_LANG
    if not text:
        return Response({'error': 'missing text'}, status=400)

    voice = TTS_VOICES.get(lang, TTS_VOICES[DEFAULT_LANG])
    key = hashlib.sha256(f'{voice}\n{text}'.encode('utf-8')).hexdigest()
    CACHE_DIR.mkdir(exist_ok=True)
    path = CACHE_DIR / f'{key}.mp3'

    if not path.exists():
        try:
            audio = _synthesize(text, voice)
        except Exception as exc:  # network / service error → let the UI fall back
            return Response({'error': f'tts failed: {exc}'}, status=502)
        if not audio:
            return Response({'error': 'empty audio'}, status=502)
        path.write_bytes(audio)

    resp = HttpResponse(path.read_bytes(), content_type='audio/mpeg')
    resp['Cache-Control'] = 'public, max-age=86400'
    return resp
