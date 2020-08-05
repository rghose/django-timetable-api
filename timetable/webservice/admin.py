from django.contrib import admin

from .models import AvailabilitySlot, Interview, Trainer, Student

# Register your models here.
admin.site.register(AvailabilitySlot)
admin.site.register(Interview)
admin.site.register(Trainer)
admin.site.register(Student)
