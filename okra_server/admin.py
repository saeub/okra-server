from django.contrib import admin

from okra_server import models

admin.site.register(models.Participant)
admin.site.register(models.Experiment)
admin.site.register(models.Task)
admin.site.register(models.TaskRating)
admin.site.register(models.TaskAssignment)
