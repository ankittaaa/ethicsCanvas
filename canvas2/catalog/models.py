from django.db import models
from django.urls import reverse
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver

from django.utils import timezone
import datetime


# TODO: Add Idea categories
# these are columns in the ethics canvas

# TODO: Add Idea ordering (preserve the order of ideas shown)

# TODO: CanvasTag instead of IdeaTag
# canvases have tags and text within ideas is highlighted with these tags


class Canvas(models.Model):
    """
    The model for canvas metadata
    """
    title = models.CharField(
        max_length = 255, 
        db_index = True,
        help_text="The title of the canvas"
    )
    date_created = models.DateTimeField(auto_now_add = True, db_index = True)
    date_modified = models.DateTimeField(auto_now = True, db_index = True)
    public = models.BooleanField(default = False, db_index = True)
    
    admins = models.ManyToManyField(User, related_name = 'admins')
    users = models.ManyToManyField(User, related_name = 'users')


    def __str__(self):
        """
        String of the Canvas
        """
        return self.title

    def get_absolute_url(self):
        return reverse('canvas-detail', args = [str(self.pk)])

    class Meta:
        ordering = ('date_modified',)

@staticmethod
@receiver(pre_save, sender=Canvas)
def ensure_canvas_has_atleast_one_admin(sender, instance, **kwargs):
    if instance.admins.count == 0:
        raise Exception('Canvas should have at least one admin.')
        

class IdeaCategory(models.Model):
    """
    Model associating ideas with a category
    """
    description = models.CharField(max_length = 50, help_text = "Category Description")

    def __str__(self):
        return self.description


class CanvasTag(models.Model):
    """
    Model representing tags that relate ideas - many to many relationship, there may exist many different tags to an idea and vice versa 
    Composite key made of the ideaID foreign key and the tagID 
    """
    text = models.CharField(max_length = 255)
    
    def __str__(self):
        return self.text


class Idea(models.Model):
    """
    Model representing an Idea on the canvas
    """
    # limit on charfields is 255
    text = models.CharField(max_length = 255, help_text = "The description of the idea")
    date_created = models.DateTimeField(auto_now_add = True, db_index = True)
    date_modified = models.DateTimeField(auto_now = True, db_index = True)
    
    category = models.ForeignKey('IdeaCategory', on_delete = models.CASCADE, null = True)
    canvas = models.ForeignKey('Canvas', on_delete = models.CASCADE, null = True)
    canvas_tags = models.ManyToManyField('CanvasTag', related_name = 'canvas_tags', blank = True)


    def __str__(self):
        return self.text    

    # for now, order by created in ascending order (oldest at top)
    class Meta:
        ordering = ('date_created',)


class Comment(models.Model):
    """
    Model representing comments, 1-1 relationship as a single comment does not apply do different ideas 
    """
    text = models.CharField(max_length = 255, help_text = "Type a comment")
    resolved = models.BooleanField(default = False, db_index = True)

    user = models.ForeignKey(User, on_delete = models.CASCADE)
    idea = models.ForeignKey('Idea', on_delete = models.CASCADE, null = True)

    def __str__(self):
        if isResolved == true: 
            return 'Comment: ' + self.text + '\n STATUS: Resolved'
        else:
            return 'Comment: ' + self.text + '\n STATUS: Unresolved'

    class Meta: 
        ordering = ('resolved',)


