from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver

# TODO: Add Idea ordering (preserve the order of ideas shown)
# NOTE: can order ideas by last_modified


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

    class Meta:
        # reverse ordered, least recently modified shows up first
        ordering = ('-date_modified',)


@receiver(pre_save, sender=Canvas)
def ensure_canvas_has_atleast_one_admin(sender, instance, **kwargs):
    if instance.admins.count == 0:
        raise Exception('Canvas should have at least one admin.')


# TODO: callback function to handle intersection in Canvas admins and users


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

    class Meta:
        ordering = ('-date_created',)


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
        ordering = ('label')


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
    timestamp = models.DateTimeField(auto_now_Add=True, db_index=True)

    def __str__(self):
        # @andrew this will return something like
        # "(Resolved) This is a comment - Harsh"
        if self.resolved:
            status = 'Resolved'
        else:
            status = 'Unresolved'
        return f'({status}) {self.text} - {self.user}'

    class Meta:
        # @andrew comments are ordered by most recent first
        ordering = ('-timestamp',)
