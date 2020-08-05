from django.db import models
from django.contrib.postgres.fields import ArrayField, JSONField

class Contributor(models.Model):
    class RoleType(models.TextChoices):
        Author = "Author"
        Conceptualization = "Conceptualization"
        ContactPerson = "ContactPerson"
        DataCollector = "DataCollector"
        DataCurator = "DataCurator"
        DataManager = "DataManager"
        FormalAnalysis = "FormalAnalysis"
        FundingAcquisition = "FundingAcquisition"
        Investigation = "Investigation"
        Maintainer = "Maintainer"
        Methodology = "Methodology"
        Producer = "Producer"
        ProjectLeader = "ProjectLeader"
        ProjectManager = "ProjectManager"
        ProjectMember = "ProjectMember"
        ProjectAdministration = "ProjectAdministration"
        Researcher = "Researcher"
        Resources = "Resources"
        Software = "Software"
        Supervision = "Supervision"
        Validation = "Validation"
        Visualization = "Visualization"
        Funder = "Funder"
        Sponsor = "Sponsor"
        StudyParticipant = "StudyParticipant"
        Other = "Other"

    name = models.CharField(default=str, max_length=150) # TODO: verify max_length is correct
    email = models.TextField(default=str) # TODO: need max length, use charfield if possible
    orcid = models.TextField(default=str) # TODO: same as email
    roles = ArrayField(
        models.CharField(max_length=21, choices=RoleType.choices, default=RoleType.Other),
        default=list
    )
    affiliations = ArrayField(
        models.TextField(default=str), default=list # TODO: need max length, use charfield if possible
    )

    def __str__(self) -> str:
        return f'name: {self.name}, email: {self.email}, orcid: {self.orcid}, roles: {self.roles}), affiliations: {self.affiliations}'
