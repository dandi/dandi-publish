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

    name = models.TextField(default=str)
    email = models.TextField(default=str)
    orcid = models.TextField(default=str)
    roles = ArrayField(
        models.CharField(max_length=21, choices=RoleType.choices, default=RoleType.Other),
        default=list
    )
    affiliations = ArrayField(
        models.TextField(default=str), default=list
    )

    def __str__(self) -> str:
        return f'name: {self.name}, email: {self.email}, orcid: {self.orcid}, roles: {self.roles}), affiliations: {self.affiliations}'
