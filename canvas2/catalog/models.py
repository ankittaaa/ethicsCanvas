from django import template
from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver

# register = template.Library()


class Project(models.Model):
    '''
    Project - a collection of (ideally) related canvasses which share users, admins and tags
    '''
    title = models.CharField(max_length=25, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modified = models.DateTimeField(auto_now=True, db_index=True)
    is_public = models.BooleanField(default=False, db_index=True)

    admins = models.ManyToManyField(User, related_name='admins', blank=True)
    users = models.ManyToManyField(User, related_name='users', blank=True)
    # Owner (creator) for canvas - owner promotes / demotes admins and can delete the canvas
    owner = models.ForeignKey(User, related_name = 'owner', on_delete=models.CASCADE, null=True, blank=True)

    def get_absolute_url(self):
        return reverse('project-detail', args=[self.pk])


@receiver(pre_save, sender=Project)
def ensure_project_has_atleast_one_admin(sender, instance, **kwargs):
    # TODO: check post_save hooks if you want behaviour to happen AFTER instance is saved
    if instance.pk is not None:
        ''' 
        The above line is to ensure that it doesn't break when creating a brand new project. 
        It throws an error when the project is new; the project has no pk before it is saved, so 
        an error is thrown when the m2m field is referenced below 
        '''
        if instance.admins.count == 0 and title != 'blank-project':
            raise Exception('Project should have at least one admin.')


class Canvas(models.Model):
    """Canvas
    A collection of ideas collected into categories"""
    title = models.CharField(max_length=25, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modified = models.DateTimeField(auto_now=True, db_index=True)
    # 0 for Ethics, 1 for Business, 2 for Privacy (TBD)
    # TODO: change canvas_type to strings, update URL parameters to reflect this in routing, views.py, and in the html templates...
    canvas_type = models.PositiveSmallIntegerField(default=0)
    tags = models.ManyToManyField('CanvasTag', related_name='canvas_set', blank=True)

    project = models.ForeignKey(Project, related_name='canvas_set', on_delete=models.CASCADE, default=0)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # NOTE: @andrew no need to str(int) here
        return reverse('canvas-detail', args=[self.pk])

    def get_collaborators_url(self):
        return reverse('collaborators', args=[self.pk])

    def get_delete_url(self):
        return reverse('delete-canvas', args=[self.pk])

    # @register.simple_tag
    # def get_remove_collaborator_url(self):
    #     return reverse('delete-user', args=[self.pk])

    class Meta:
        # reverse ordered, least recently modified shows up first
        ordering = ('-date_modified',)



class Idea(models.Model):
    """
    Idea
    A block/post belonging to a category on the Canvas
    """
    title = models.CharField(max_length=50)
    text = models.CharField(max_length=255)
    # Default = 9 for uncategorised
    category = models.PositiveSmallIntegerField(default=9, db_index=True);
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modified = models.DateTimeField(auto_now=True, db_index=True)

    canvas = models.ForeignKey('Canvas', on_delete=models.CASCADE)
    # M2M RELATION WITH IDEAS - A TAG CAN EXIST IN MANY IDEAS AND AN IDEA MAY CONTAIN MANY TAGS
    tags = models.ManyToManyField('CanvasTag', related_name='idea_set', blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('idea-detail', args=[self.pk])

    def get_delete_url(self):
        return reverse('delete-idea', args=[self.pk])

    def get_comments_url(self):
        return reverse('comment-thread', args=[self.pk])

    class Meta:
        ordering = ('-date_modified',)


class CanvasTag(models.Model):
    """
    Canvas Tag
    Model representing tags that relate ideas,
    many to many relationship (declared in canvas model),
    there may exist many different tags to an idea and vice versa
    """
    # labels should be short and to the point
    label = models.CharField(max_length=25)
    # including date_created and date_modified to help with ordering them
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modified = models.DateTimeField(auto_now=True, db_index=True)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ('-date_modified',)


class IdeaComment(models.Model):
    """
    IdeaComment
    Comments on an idea
    """
    text = models.CharField(max_length=255, help_text="Type a comment")
    resolved = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    idea = models.ForeignKey(
        'Idea', null = False,
        on_delete=models.CASCADE, 
        related_name='comments',
        db_index=True
    )
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)

    def __str__(self):
        # @andrew this will return something like
        # "(Resolved) This is a comment - Harsh"
        if self.resolved:
            status = 'Resolved'
        else:
            status = 'Unresolved'
        return f'({status}) {self.text} - {self.user}'

    def get_delete_url(self):
        return reverse('delete-comment', args=[self.pk])

    def get_resolve_url(self):
        return reverse('comment-resolve', args=[self.idea.pk])

    class Meta:
        # comments are ordered by most recent first
        ordering = ('-timestamp',)
