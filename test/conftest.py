from tempfile import NamedTemporaryFile

from django.core.files import File
from fuzzy import Timestamp
import pytest

from publish.models import Asset, Dandiset, Version


@pytest.fixture
@pytest.mark.django_db
def dandiset():
    dandiset = Dandiset(id='000001', draft_folder_id='abc123')
    dandiset.save()
    return dandiset


@pytest.fixture
@pytest.mark.django_db
def dandiset_json(dandiset):
    return {
        'identifier': '000001',
        'created': Timestamp(),
        'updated': Timestamp(),
    }


@pytest.fixture
@pytest.mark.django_db
def version(dandiset):
    version = Version(dandiset=dandiset, metadata={'a': 1, 'b': '2', 'c': ['x', 'y', 'z']})
    version.save()
    return version


@pytest.fixture
@pytest.mark.django_db
def version_list_json(version, dandiset_json):
    return {
        'dandiset': dandiset_json,
        'version': version.version,
        'created': Timestamp(),
        'updated': Timestamp(),
        'count': version.count,
        'size': version.size,
    }


@pytest.fixture
@pytest.mark.django_db
def version_detail_json(version_list_json, version):
    return {
        **version_list_json,
        'metadata': version.metadata,
    }


@pytest.fixture
@pytest.mark.django_db
def asset(version):
    with NamedTemporaryFile('r+b') as local_stream:
        blob = File(file=local_stream, name='foo/bar.nwb',)
        blob.content_type = 'application/octet-stream'
        asset = Asset(
            version=version,
            path='/foo/bar.nwb',
            size=1337,
            sha256='sha256',
            metadata={'foo': ['bar', 'baz']},
            blob=blob,
        )
        asset.save()
    return asset


@pytest.fixture
@pytest.mark.django_db
def asset_json(asset, version_list_json):
    return {
        'version': version_list_json,
        'uuid': str(asset.uuid),
        'path': asset.path,
        'size': asset.size,
        'sha256': asset.sha256,
        'created': Timestamp(),
        'updated': Timestamp(),
        'metadata': asset.metadata,
    }
