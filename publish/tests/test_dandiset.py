import pytest

from .fuzzy import TIMESTAMP_RE


@pytest.mark.django_db
def test_dandiset_identifier(dandiset):
    assert int(dandiset.identifier) == dandiset.id


def test_dandiset_identifer_missing(dandiset_factory):
    dandiset = dandiset_factory.build()
    # This should have a sane fallback
    assert dandiset.identifier == ''


@pytest.mark.django_db
def test_dandiset_rest_list(api_client, dandiset):
    assert api_client.get('/api/dandisets/').data == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [
            {'identifier': dandiset.identifier, 'created': TIMESTAMP_RE, 'updated': TIMESTAMP_RE}
        ],
    }


@pytest.mark.django_db
def test_dandiset_rest_retrieve(api_client, dandiset):
    assert api_client.get(f'/api/dandisets/{dandiset.identifier}/').data == {
        'identifier': dandiset.identifier,
        'created': TIMESTAMP_RE,
        'updated': TIMESTAMP_RE,
    }