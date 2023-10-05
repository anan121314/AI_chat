from django.db import models

# Create your models here.
class params(models.Model):
    collection_name = models.CharField(max_length=30)
    ans_type = models.CharField(max_length=30,null=True)
    inst_type= models.CharField(max_length=30,null=True)
    inst=models.CharField(max_length=500,null=True)