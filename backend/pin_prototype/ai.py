"""Thin helper around the Infomaniak OpenAI-compatible chat API."""
import json
import urllib.request

from django.conf import settings


def chat_completion(messages, max_tokens=4000, temperature=0.1):
    """Call the configured Infomaniak model and return the text reply.
    Raises RuntimeError if the AI is not configured."""
    api_key = settings.INFOMANIAK_API_KEY
    product_id = settings.INFOMANIAK_PRODUCT_ID
    model = settings.INFOMANIAK_MODEL
    if not api_key or not product_id:
        raise RuntimeError('AI not configured — set INFOMANIAK_API_KEY and INFOMANIAK_PRODUCT_ID.')

    payload = json.dumps({
        'model': model,
        'messages': messages,
        'max_tokens': max_tokens,
        'temperature': temperature,
    }).encode('utf-8')

    req = urllib.request.Request(
        f'https://api.infomaniak.com/2/ai/{product_id}/openai/v1/chat/completions',
        data=payload,
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        method='POST',
    )
    with urllib.request.urlopen(req, timeout=120) as resp:
        result = json.loads(resp.read())
    return result['choices'][0]['message']['content']
