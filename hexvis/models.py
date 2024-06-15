from django.db import models
from django.forms import ModelForm

class CoordinatesEntry(models.Model):
    h3ref = models.CharField(max_length=256)
    h3scale = models.IntegerField()
    lat = models.CharField(max_length=20)
    lon = models.CharField(max_length=20)
    scale = models.CharField(max_length=20, null=True)

# class CoordinatesForm(forms.ModelForm):
#     lat = models.CharField(max_length=20)
#     lon = models.CharField(max_length=20)
