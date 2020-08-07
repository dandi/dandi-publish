from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

from .role import Role


class Contributor(models.Model):
    # https://github.com/dandi/schema/blob/master/releases/1.0.0-rc1/dandiset.json#L424

    identifier = models.TextField(max_length=65536, blank=True)

    name = models.CharField(max_length=255)

    email = models.CharField(max_length=254, blank=True)

    url = models.TextField(max_length=65536, blank=True)  # TODO: validate length on the api level

    roleName = models.ManyToManyField(Role)

    includeInCitation = models.BooleanField(blank=True)

    awardNumber = models.TextField(max_length=65536, blank=True)  # TODO: validate length

    contributorType = models.CharField(max_length=12)  # 'Person' or 'Organization'

    affiliation = ArrayField(models.CharField(max_length=255), blank=True) # TODO: remove these arrayfields

    contactPoint = ArrayField(models.CharField(max_length=255), blank=True)
