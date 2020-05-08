from dataclasses import dataclass
from hashlib import sha256
from json import JSONDecodeError
from tempfile import NamedTemporaryFile
from typing import Any, cast, Dict, List, Optional, TYPE_CHECKING
import subprocess

import boto3  # type: ignore
from botocore.exceptions import ClientError  # type: ignore
from celery import shared_task
from celery.utils.log import get_task_logger
from django.db.transaction import atomic
from httpx import Client, Response, stream
from yaml import dump

from publish import models

if TYPE_CHECKING:
    from mypy_boto3_s3 import S3Client  # noqa

BASE_URL = 'https://girder.dandiarchive.org/api/v1/'
S3_BUCKET = 'dandi'
S3_PREFIX = 'dandisets'
S3_ENDPOINT_URL = 'http://localhost:9000'

logger = get_task_logger(__name__)


class DandiSetLoadError(Exception):
    pass


class DandiClient(Client):
    def __init__(self, token=None, **kwargs):
        kwargs.setdefault('base_url', BASE_URL)
        if token:
            kwargs.setdefault('headers', {'Girder-Token': token})
        super().__init__(**kwargs)


def _get_json(response: Response) -> Any:
    if response.status_code != 200:
        raise DandiSetLoadError(
            f'Girder returned status code {response.status_code}')
    try:
        return response.json()
    except JSONDecodeError:
        raise DandiSetLoadError(
            f'Girder returned non-json response: {repr(response.content)}')


@dataclass
class DandiFile:
    girder_id: str
    name: str
    url: str
    metadata: Dict[str, Any]
    size: int

    def publish(self, subject: models.Subject, s3: 'S3Client', prefix: str):
        nwb_key = f'{prefix}/{self.name}'
        with NamedTemporaryFile('r+b') as nwb, stream('GET', self.url) as response:
            logger.info(f'Downloading {self.name}...')
            response.raise_for_status()
            hash = sha256()
            i = 0
            for chunk in response.iter_bytes():
                if i > 10:
                    break
                if chunk:
                    i += 1
                    hash.update(chunk)
                    nwb.write(chunk)

            r = subprocess.call(["dandi", "validate", nwb.name])
            print("Called dandi validate:", r)

            logger.info(f'Uploading {self.name}...')
            nwb.seek(0)

            s3.upload_fileobj(
                nwb, S3_BUCKET, nwb_key, ExtraArgs={'ACL': 'public-read'},
            )
            nwb_file = models.NWBFile(
                subject=subject,
                name=self.name,
                size=self.size,
                sha256=hash.hexdigest(),
                metadata=self.metadata,
            )
            nwb_file.file = nwb_key
            nwb_file.save()


@dataclass
class DandiSubject:
    girder_id: str
    name: str
    files: List[DandiFile]

    @classmethod
    def load(cls, client: Client, girder_id: str, name: str) -> 'DandiSubject':
        items = _get_json(client.get(
            f'item', params={'folderId': str(girder_id), 'limit': 0}))
        files = []
        for item in items:
            file_list = _get_json(client.get(f'item/{item["_id"]}/files'))
            if len(file_list) != 1:
                raise DandiSetLoadError(
                    f'Expected exactly one file per item not {len(file_list)}')
            f = file_list[0]
            files.append(
                DandiFile(
                    girder_id=f['_id'],
                    name=f['name'],
                    metadata=item['meta'],
                    url=f'{BASE_URL}file/{f["_id"]}/download',
                    size=f['size'],
                )
            )
        return cls(girder_id=girder_id, name=name, files=files)

    def publish(self, dandiset: models.Dandiset, s3: 'S3Client', prefix: str):
        subject = models.Subject(dandiset=dandiset, name=self.name)
        subject.save()
        subject_prefix = f'{prefix}/{self.name}'
        for file in self.files:
            file.publish(subject, s3, subject_prefix)


@dataclass
class DandiSet:
    girder_id: str
    dandi_id: str
    metadata: Dict[str, Any]
    subjects: List[DandiSubject]

    @classmethod
    def load(cls, client: Client, girder_id: str) -> 'DandiSet':
        dandiset_folder = _get_json(client.get(f'folder/{girder_id}'))
        subject_folders = _get_json(
            client.get(
                f'folder', params={'parentId': str(girder_id), 'parentType': 'folder', 'limit': 0}
            )
        )
        subjects = [DandiSubject.load(client, f['_id'], f['name'])
                    for f in subject_folders]

        return cls(
            girder_id=girder_id,
            dandi_id=dandiset_folder['name'],
            metadata=dandiset_folder['meta'],
            subjects=subjects,
        )

    def s3_path(self, version):
        return f'{S3_PREFIX}/{self.dandi_id}/{version}'

    def _get_next_version(self, s3: 'S3Client') -> int:
        version = 1
        while True:
            try:
                s3.get_object(Bucket=S3_BUCKET,
                              Key=f'{self.s3_path(version)}/dandiset.yaml')
            except ClientError as e:
                if e.response['Error']['Code'] == 'NoSuchKey':
                    return version
                raise
            version += 1

    def publish(self, s3: 'S3Client') -> str:
        version = self._get_next_version(s3)
        prefix = self.s3_path(version)

        dandiset = models.Dandiset(
            dandi_id=self.dandi_id,
            version=version,
            metadata=self.metadata,
        )
        dandiset.save()
        for subject in self.subjects:
            subject.publish(dandiset, s3, prefix)

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=f'{prefix}/dandiset.yaml',
            Body=dump(self.metadata['dandiset']).encode(),
            ACL='public-read',
        )
        return f's3://{S3_BUCKET}/{prefix}'


@shared_task
@atomic
def publish_dandiset(girder_id: str, token: Optional[str] = None) -> str:
    s3 = cast('S3Client', boto3.client('s3', endpoint_url=S3_ENDPOINT_URL))
    with DandiClient(token=token) as client:
        dandiset = DandiSet.load(client, girder_id)
    return dandiset.publish(s3)
