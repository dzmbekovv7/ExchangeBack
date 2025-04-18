from django.contrib import admin

from .models import Event, Currency, User

# Register your models here.
admin.site.register(Event)
admin.site.register(Currency)
admin.site.register(User)
