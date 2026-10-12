"""Day 52 unit tests for health-aware provider routing (offline, pure functions).

Covers recommend_provider() in sentinelai.routing, which combines the
--routing policy with Day 51 provider health scoring. No LLM or network is
required.
"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from sentinelai.routing import (
    recommend_provider,
    route_provider,
    ROUTING_PROVIDER,
)
from provider_health import (
    ProviderHealth,
    recommend_provider_for_task,
    score_provider_health,
)


def test_recommend_provider_report_prefers_gemini():
    # report policy -> gemini eligible, ollama ineligible; gemini has highest score
    assert recommend_provider(routing='report', provider_scores={'gemini': 90.0, 'ollama': 78.0}) == 'gemini'


def test_recommend_provider_private_prefers_ollama():
    # private policy -> gemini ineligible, ollama eligible; ollama has highest score
    assert recommend_provider(routing='private', provider_scores={'gemini': 80.0, 'ollama': 95.0}) == 'ollama'


def test_recommend_provider_no_policy_uses_health_scores():
    # No routing policy, is_sensitive=False -> ollama preferred (+5 bonus for local)
    assert recommend_provider(provider_scores={'gemini': 80.0, 'ollama': 78.0}, is_sensitive=False) == 'ollama'

def test_recommend_provider_no_policy_sensitive_ollama_winning():
    # No routing policy, is_sensitive=True -> gemini penalised (-15), ollama (78) wins
    # gemini: 80-15=65, ollama: 78 -> ollama wins
    assert recommend_provider(provider_scores={'gemini': 80.0, 'ollama': 78.0}, is_sensitive=True) == 'ollama'


def test_recommend_provider_explicit_llm_wins():
    # Explicit --llm should still win over any routing or health scores.
    assert route_provider('ollama', 'report') == 'ollama'


def test_recommend_provider_invalid_policy():
    try:
        recommend_provider(routing='bogus', provider_scores={'gemini': 80.0, 'ollama': 78.0})
    except ValueError:
        return
    raise AssertionError('invalid routing policy should raise ValueError')


def test_recommend_provider_consistent_with_health_scoring():
    # Health scores chosen so gemini wins on report, ollama wins on private.
    scores = {'gemini': 90.0, 'ollama': 78.0}
    assert recommend_provider(routing='report', provider_scores=scores) == 'gemini'
    scores['ollama'] = 95.0
    assert recommend_provider(routing='private', provider_scores=scores) == 'ollama'


def _mini_health(provider, availability, latency_ms, privacy='cloud'):
    return ProviderHealth(name=provider, availability=availability, latency_ms=latency_ms, privacy=privacy)


def test_health_score_rounding():
    h = _mini_health('gemini', 0.92, 1300)
    s = score_provider_health(h)
    assert 0 <= s <= 100
    assert isinstance(s, float)


def _main():
    fns = [v for k, v in sorted(globals().items()) if k.startswith('test_') and callable(v)]
    for fn in fns:
        fn()
        print(f'  PASS  {fn.__name__}')
    print(f'ALL {len(fns)} day52 routing TESTS PASSED (offline, pure functions)')


if __name__ == '__main__':
    _main()
