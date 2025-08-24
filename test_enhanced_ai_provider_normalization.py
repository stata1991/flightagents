import pytest
from api.enhanced_ai_provider import EnhancedAITripProvider

@pytest.fixture
def provider():
    return EnhancedAITripProvider()

def test_normalize_only_detailed_itinerary(provider):
    ai_data = {
        'detailed_itinerary': {'day_1': {'activity': 'A'}},
        'trip_summary': {'title': 'Test'}
    }
    norm = provider._normalize_ai_response(ai_data)
    assert 'itinerary' in norm
    assert norm['itinerary'] == {'day_1': {'activity': 'A'}}

def test_normalize_only_itinerary(provider):
    ai_data = {
        'itinerary': {'day_1': {'activity': 'B'}},
        'trip_summary': {'title': 'Test'}
    }
    norm = provider._normalize_ai_response(ai_data)
    assert 'itinerary' in norm
    assert norm['itinerary'] == {'day_1': {'activity': 'B'}}

def test_normalize_both_detailed_and_empty_itinerary(provider):
    ai_data = {
        'detailed_itinerary': {'day_1': {'activity': 'C'}},
        'itinerary': {},
        'trip_summary': {'title': 'Test'}
    }
    norm = provider._normalize_ai_response(ai_data)
    assert 'itinerary' in norm
    assert norm['itinerary'] == {'day_1': {'activity': 'C'}}

def test_normalize_neither_itinerary(provider):
    ai_data = {
        'trip_summary': {'title': 'Test'}
    }
    norm = provider._normalize_ai_response(ai_data)
    assert 'itinerary' in norm
    assert norm['itinerary'] == {}

def test_normalize_extra_keys(provider):
    ai_data = {
        'detailed_itinerary': {'day_1': {'activity': 'D'}},
        'hotels': {'luxury': []},
        'flights': {'fastest': []},
        'trip_summary': {'title': 'Test'}
    }
    norm = provider._normalize_ai_response(ai_data)
    assert 'itinerary' in norm
    assert norm['itinerary'] == {'day_1': {'activity': 'D'}}
    assert 'accommodation' in norm
    assert 'transportation' in norm

def test_extract_largest_json_object_simple(provider):
    text = '{"a": 1, "b": 2}'
    result = provider._extract_largest_json_object(text)
    assert result == '{"a": 1, "b": 2}'

def test_extract_largest_json_object_with_text(provider):
    text = 'Some intro text\n{"a": 1, "b": {"c": 3}}\nSome trailing text.'
    result = provider._extract_largest_json_object(text)
    assert result == '{"a": 1, "b": {"c": 3}}'

def test_extract_largest_json_object_multiple_json(provider):
    text = '{"a": 1}{"b": 2, "c": {"d": 4}}'
    result = provider._extract_largest_json_object(text)
    assert result == '{"b": 2, "c": {"d": 4}}'

def test_extract_largest_json_object_whitespace(provider):
    text = '\n  {\n    "a": 1,\n    "b": {\n      "c": 3\n    }\n  }\n  '
    result = provider._extract_largest_json_object(text)
    assert '"a": 1' in result and '"c": 3' in result

def test_extract_largest_json_object_no_json(provider):
    text = 'No JSON here!'
    result = provider._extract_largest_json_object(text)
    assert result == ''
