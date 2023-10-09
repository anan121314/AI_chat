from django.contrib import admin

# Register your models here.
from .models import params

from .models import summ

admin.site.register(params)

admin.site.register(summ)