import pytest


@pytest.mark.django_db
def test_dandisets_list(client, dandiset_json):
    assert client.get('/api/dandisets/').json() == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [dandiset_json],
    }


@pytest.mark.django_db
def test_dandisets_read(client, dandiset_json):
    assert client.get('/api/dandisets/000001/').json() == dandiset_json


@pytest.mark.django_db
def test_dandisets_versions_list(client, version_list_json):
    assert client.get('/api/dandisets/000001/versions/').json() == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [version_list_json],
    }


@pytest.mark.django_db
def test_dandisets_versions_read(client, version, version_detail_json):
    assert (
        client.get(f'/api/dandisets/000001/versions/{version.version}/').json()
        == version_detail_json
    )


@pytest.mark.django_db
def test_dandisets_versions_assets_list(client, version, asset_json):
    assert client.get(f'/api/dandisets/000001/versions/{version.version}/assets/').json() == {
        'count': 1,
        'next': None,
        'previous': None,
        'results': [asset_json],
    }


@pytest.mark.django_db
def test_dandisets_versions_assets_read(client, version, asset, asset_json):
    assert (
        client.get(f'/api/dandisets/000001/versions/{version.version}/assets/{asset.uuid}/').json()
        == asset_json
    )
