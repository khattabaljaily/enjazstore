import json
import logging

import requests
from django.conf import settings
from django.utils import timezone

from products.models import Product
from products.pricing import to_sdg

logger = logging.getLogger(__name__)

DEEPSEEK_URL = 'https://api.deepseek.com/chat/completions'
DEEPSEEK_MODEL = 'deepseek-v4-flash'
TAVILY_URL = 'https://api.tavily.com/search'

MAX_PRODUCTS = 20
MAX_TOOL_ROUNDS = 6

SEARCH_TOOL = {
    'type': 'function',
    'function': {
        'name': 'web_search',
        'description': (
            'ابحث في الويب عن معلومات حالية ومحدّثة (اتجاهات السوق، أسعار منافسين، '
            'مواقع بيع في السودان). استخدمه دائمًا بدل الاعتماد على معرفتك المسبقة، '
            'لأن الأسعار والاتجاهات تتغيّر باستمرار.'
        ),
        'parameters': {
            'type': 'object',
            'properties': {
                'query': {'type': 'string', 'description': 'نص البحث بالعربي أو الإنجليزي'},
            },
            'required': ['query'],
            'additionalProperties': False,
        },
    },
}

RESPONSE_SCHEMA_HINT = '''
أعد النتيجة النهائية ككائن JSON فقط (بدون أي نص خارج الـ JSON)، بهذا الشكل بالضبط:
{
  "trending": [{"name": "اسم المنتج/الفئة", "reason": "سبب موجز لكونه رائجًا الآن"}],
  "comparisons": [{
    "product_name": "اسم منتجنا كما أُعطي لك",
    "our_price_sdg": <رقم بالجنيه السوداني كما أُعطي لك>,
    "market_low_price_sdg": <أقل سعر وجدته بالجنيه السوداني، أو null لو ما لقيت>,
    "market_source": "اسم الموقع/المصدر، أو null",
    "note": "ملاحظة قصيرة (مثلاً: نفس الموديل، أو موديل مشابه، أو غير متوفر بالسودان)"
  }],
  "summary": "فقرة قصيرة (3-4 جمل) تلخّص أهم ما يستحق اهتمام صاحب المتجر"
}
'''.strip()


class MarketInsightError(Exception):
    pass


def _build_product_lines():
    products = (
        Product.objects.filter(is_active=True)
        .order_by('-is_featured', '-created_at')[:MAX_PRODUCTS]
    )
    lines = []
    for product in products:
        price_sdg = to_sdg(product.price)
        lines.append(f'- {product.name} ({product.category.name}) — سعرنا الحالي: {price_sdg:,.0f} ج.س')
    return lines


def _tavily_search(query):
    if not settings.TAVILY_API_KEY:
        return {'error': 'Tavily API key not configured'}
    try:
        resp = requests.post(
            TAVILY_URL,
            headers={'Authorization': f'Bearer {settings.TAVILY_API_KEY}'},
            json={'query': query, 'max_results': 5, 'search_depth': 'basic'},
            timeout=20,
        )
        resp.raise_for_status()
        data = resp.json()
    except requests.RequestException as exc:
        logger.warning('Tavily search failed for %r: %s', query, exc)
        return {'error': str(exc)}

    results = [
        {'title': r.get('title'), 'url': r.get('url'), 'content': r.get('content')}
        for r in data.get('results', [])
    ]
    return {'query': query, 'results': results}


def _deepseek_call(messages, tools=None, response_format=None):
    if not settings.DEEPSEEK_API_KEY:
        raise MarketInsightError('لم يتم إعداد مفتاح DeepSeek API — أضفه في secrets.json.')

    payload = {'model': DEEPSEEK_MODEL, 'messages': messages}
    if tools:
        payload['tools'] = tools
        payload['tool_choice'] = 'auto'
    if response_format:
        payload['response_format'] = response_format

    resp = requests.post(
        DEEPSEEK_URL,
        headers={
            'Authorization': f'Bearer {settings.DEEPSEEK_API_KEY}',
            'Content-Type': 'application/json',
        },
        json=payload,
        timeout=120,
    )
    if not resp.ok:
        raise MarketInsightError(f'DeepSeek API error ({resp.status_code}): {resp.text[:500]}')
    return resp.json()


def run_market_analysis(report):
    """The actual work — called on a background thread from the generate view."""
    report.status = report.Status.RUNNING
    report.save(update_fields=['status'])

    try:
        product_lines = _build_product_lines()
        product_block = '\n'.join(product_lines) if product_lines else '(لا توجد منتجات نشطة حاليًا)'

        system_prompt = (
            'أنت محلل سوق يساعد متجرًا إلكترونيًا سودانيًا (إنجاز ستور). لديك أداة '
            'بحث ويب (web_search) — استخدمها فعليًا للحصول على معلومات حالية، ولا '
            'تعتمد على معرفتك المجمّدة وحدها، لأن الأسعار والاتجاهات في السودان '
            'تتغيّر باستمرار.\n\n'
            'مطلوب منك بحثان:\n'
            '1) ما هي الفئات/المنتجات الأكثر طلبًا أو رواجًا في السودان حاليًا '
            '(أسواق إلكترونية، فيسبوك ماركت بليس، محلات محلية).\n'
            '2) لكل منتج من منتجاتنا أدناه، ابحث عن أقل سعر تجده لمنتج مماثل يبيعه '
            'بائع آخر في السودان، واذكر المصدر إن توفر.\n\n'
            f'منتجاتنا الحالية:\n{product_block}\n\n'
            f'{RESPONSE_SCHEMA_HINT}'
        )

        messages = [
            {'role': 'system', 'content': system_prompt},
            {'role': 'user', 'content': 'ابدأ التحليل الآن باستخدام البحث، ثم أعد النتيجة بصيغة JSON فقط.'},
        ]

        total_usage = {'prompt_tokens': 0, 'completion_tokens': 0, 'search_calls': 0}

        for _ in range(MAX_TOOL_ROUNDS):
            data = _deepseek_call(messages, tools=[SEARCH_TOOL])
            usage = data.get('usage', {})
            total_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
            total_usage['completion_tokens'] += usage.get('completion_tokens', 0)

            choice = data['choices'][0]
            message = choice['message']
            messages.append(message)

            tool_calls = message.get('tool_calls')
            if not tool_calls:
                break

            for call in tool_calls:
                args = json.loads(call['function']['arguments'] or '{}')
                query = args.get('query', '')
                result = _tavily_search(query)
                total_usage['search_calls'] += 1
                messages.append({
                    'role': 'tool',
                    'tool_call_id': call['id'],
                    'content': json.dumps(result, ensure_ascii=False),
                })
        else:
            # Loop exhausted without a final answer — ask once more, tool-free,
            # forcing a wrap-up with whatever's been gathered so far.
            messages.append({
                'role': 'user',
                'content': 'لديك معلومات كافية الآن. أعد النتيجة النهائية كـ JSON فقط، بدون بحث إضافي.',
            })
            data = _deepseek_call(messages, response_format={'type': 'json_object'})
            usage = data.get('usage', {})
            total_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
            total_usage['completion_tokens'] += usage.get('completion_tokens', 0)
            messages.append(data['choices'][0]['message'])

        # Final structured pass: re-ask in JSON mode over the same conversation
        # so the last message is guaranteed valid JSON, regardless of whether
        # the model already wrapped up on its own above.
        messages.append({
            'role': 'user',
            'content': f'{RESPONSE_SCHEMA_HINT}\n\nأعد فقط كائن الـ JSON، بدون أي شرح إضافي.',
        })
        data = _deepseek_call(messages, response_format={'type': 'json_object'})
        usage = data.get('usage', {})
        total_usage['prompt_tokens'] += usage.get('prompt_tokens', 0)
        total_usage['completion_tokens'] += usage.get('completion_tokens', 0)

        final_text = data['choices'][0]['message']['content']
        content = json.loads(final_text)

        report.content = content
        report.usage = total_usage
        report.status = report.Status.COMPLETED
    except Exception as exc:
        logger.exception('Market insight report #%s failed', report.pk)
        report.status = report.Status.FAILED
        report.error_message = str(exc)
    finally:
        report.completed_at = timezone.now()
        report.save()
