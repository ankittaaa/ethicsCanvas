from django.contrib import admin
from .models import Canvas, IdeaCategory, CanvasTag, Idea, IdeaComment


admin.site.register(Canvas)
admin.site.register(IdeaCategory)
admin.site.register(CanvasTag)
admin.site.register(Idea)
admin.site.register(IdeaComment)

# Register your models here.
