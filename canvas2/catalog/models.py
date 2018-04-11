from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import pre_save, m2m_changed
from django.dispatch import receiver




class Canvas(models.Model):
    """Canvas
    A collection of ideas collected into categories"""
    title = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modified = models.DateTimeField(auto_now=True, db_index=True)
    is_public = models.BooleanField(default=False, db_index=True)
    # admins are implicitly assumed to be users
    # should there be a check to see whether some admins are in users
    # and vice versa?
    admins = models.ManyToManyField(User, related_name='admins')
    users = models.ManyToManyField(User, related_name='users')
    # @andrew moved these tags from Idea to here
    tags = models.ManyToManyField('CanvasTag', related_name='tags', blank=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        # NOTE: @andrew no need to str(int) here
        return reverse('canvas-detail', args=[self.pk])

    def get_collaborators_url(self):
        return reverse('collaborators', args=[self.pk])

    class Meta:
        # reverse ordered, least recently modified shows up first
        ordering = ('-date_modified',)


@receiver(pre_save, sender=Canvas)
def ensure_canvas_has_atleast_one_admin(sender, instance, **kwargs):
    if instance.pk is not None:
        ''' The above line is to ensure that it doesn't break when creating a brand new canvas. It throws an error when the canvas is new; the canvas has no pk before it is saved, so 
            an error is thrown when the m2m field is referenced below 
        '''
        if instance.admins.count == 0:
            raise Exception('Canvas should have at least one admin.')


# TODO: callback function to handle intersection in Canvas admins and users
# By 'handle' I presume 'do not store in users if they already exist in admins', as all admins are users but not all users are admins.

# @receiver(m2m_changed, sender=Canvas)
# def enforce_empty_intersection_between_admins_and_users(sender, instance, **kwargs):
#     print('happy')


class IdeaCategory(models.Model):
    """IdeaCategory
    A collection of ideas."""
    title = models.CharField(max_length=50, db_index=True)
    description = models.CharField(max_length=255)
    # @andrew no need to add descriptions to all fields if they are implied

    def __str__(self):
        return self.title

    class Meta:
        ordering = ('title',)


class Idea(models.Model):
    """Idea
    A block/post belonging to a category on the Canvas"""
    title = models.CharField(max_length=50, db_index=True)
    text = models.CharField(max_length=255, db_index=True)
    date_created = models.DateTimeField(auto_now_add=True, db_index=True)
    date_modified = models.DateTimeField(auto_now=True, db_index=True)

    # If category == null, then the Idea is uncategorised
    category = models.ForeignKey(
        'IdeaCategory', on_delete=models.CASCADE, null=True)
    # @andrew an Idea cannot exist without the canvas, so null=False
    canvas = models.ForeignKey('Canvas', on_delete=models.CASCADE)
    # @andrew an idea does not have any tags
    # we are only highlighting the tags on the canvas
    # moved tags to Canvas

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
    """Canvas Tag
    Model representing tags that relate ideas - many to many relationship,
    there may exist many different tags to an idea and vice versa
    Composite key made of the ideaID foreign key and the tagID
    """
    # labels should be short and to the point
    label = models.CharField(max_length=25)

    def __str__(self):
        return self.label

    class Meta:
        ordering = ('label',)


class IdeaComment(models.Model):
    """IdeaComment
    Comments on an idea
    """
    text = models.CharField(max_length=255, help_text="Type a comment")
    resolved = models.BooleanField(default=False, db_index=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # @andrew a comment will always be on an Idea, so idea cannot be null
    idea = models.ForeignKey(
        'Idea', on_delete=models.CASCADE, related_name='comments')
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
        print('shit')
        return reverse('comment-resolve', args=[self.idea.pk])

    class Meta:
        # @andrew comments are ordered by most recent first
        ordering = ('-timestamp',)
