from django.contrib import admin
from import_export.admin import ImportExportModelAdmin
from .models import Canvas, CanvasTag, Idea, IdeaComment, Project

@admin.register(Canvas)
class CanvasAdmin(ImportExportModelAdmin):
    pass
@admin.register(CanvasTag)
class CanvasTagAdmin(ImportExportModelAdmin):
    pass
@admin.register(Idea)
class IdeaAdmin(ImportExportModelAdmin):
    pass
@admin.register(IdeaComment)
class IdeaCommentAdmin(ImportExportModelAdmin):
    pass
@admin.register(Project)
class ProjectAdmin(ImportExportModelAdmin):
    pass
#admin.site.register(Canvas)
#admin.site.register(CanvasTag)
#admin.site.register(Idea)
#admin.site.register(IdeaComment)
#admin.site.register(Project)

# Register your models here.
