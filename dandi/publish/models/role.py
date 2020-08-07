from django.db import models


class Role(models.Model):
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

    roleName = models.CharField(max_length=21)
