from django.db import models


class Document(models.Model):
    process_number = models.CharField(max_length=100, blank=True, null=True, unique=True)
    tribunal = models.CharField(max_length=255, blank=True, null=True)
    summary = models.TextField(blank=True, null=True)
    decision = models.TextField(blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    descriptors = models.TextField(blank=True, null=True)
    main_text = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.process_number


class Entity(models.Model):
    document = models.ForeignKey(Document, related_name="entities", on_delete=models.CASCADE)
    name = models.CharField(max_length=255, blank=True, null=True, unique=True)
    label = models.CharField(max_length=50, choices=[("CASE", "Case"), ("LAW", "Law")])
    url = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return self.name
