from django.contrib import admin
from .models import Canvas, CanvasTag, Idea, IdeaComment, Project


admin.site.register(Canvas)
admin.site.register(CanvasTag)
admin.site.register(Idea)
admin.site.register(IdeaComment)
admin.site.register(Project)

# Register your models here.
