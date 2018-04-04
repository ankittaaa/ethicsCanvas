from django.contrib import admin
from .models import Canvas, IdeaCategory, CanvasTag, Idea, Comment


admin.site.register(Canvas)
admin.site.register(IdeaCategory)
admin.site.register(CanvasTag)
admin.site.register(Idea)
admin.site.register(Comment)

# Register your models here.
