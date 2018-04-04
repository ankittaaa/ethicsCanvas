'''
from django.test import TestCase
from django.utils import timezone
from catalog.models import Canvas, IdeaCategory, IdeaTag, Idea, Comment
from django.contrib.auth.models import User
import pytz
import datetime

# CANVAS IDEA USER COMMENT TAG COLLABORATIONS
# Tests include 10 instances of any model being tested
# ID is queried with i+1, as i begins at zero but IDs begin with 1 (and as it turns out cannot be 0)

global TEST_LIMIT
TEST_LIMIT = 10



class CanvasTestModel(TestCase):
  """

  """
  @classmethod
  def setUpTestData(cls):
    for i in range(TEST_LIMIT):
      Canvas.objects.create(title = 'Hella Derp %s' % i, date = ( timezone.now() - datetime.timedelta(days = i) ) )

  def testTitle(self):
    for i in range(TEST_LIMIT):
      canvas = Canvas.objects.get(id=(i+1))
      field_label = canvas.title
      self.assertEquals(field_label, 'Hella Derp %s' % i)

  def testDate(self):
    for i in range(TEST_LIMIT):
      canvas = Canvas.objects.get(id=(i+1))
      field_label = canvas.date
      self.assertTrue( ( timezone.now() - datetime.timedelta(days = i) ).date() == field_label )



class IdeaTestModel(TestCase):
  """

  """
  @classmethod
  def setUpTestData(cls):
    for i in range(TEST_LIMIT):
      User.objects.create_user( email = 'fatclub%s@example.com' % i, username = 'Fatclub %s' % i)
      Idea.objects.create( ownerID = User.objects.get(id = i+1),text = 'I am an idea and my name is %s' % (i+1))


  def testTextIsRight(self):
    for i in range(TEST_LIMIT):
      idea = Idea.objects.get(id=(i+1))
      self.assertEquals(idea.text, 'I am an idea and my name is %s' % (i+1))

  def testID(self):
    for i in range(TEST_LIMIT):
      idea = Idea.objects.get(id=(i+1))
      self.assertEquals(idea.id, (i+1))

  def testLinkedUser(self):
    for i in range(TEST_LIMIT):
      idea = Idea.objects.get(id=(i+1))
      user = idea.ownerID
      self.assertEquals( user.username, 'Fatclub %s' % i )
      self.assertEquals( user.email, 'fatclub%s@example.com' % i )



class CollaborationsTestModel(TestCase):
  """

  """
  @classmethod
  def setUpTestData(cls):
    for i in range(TEST_LIMIT):
      # First create the user and the canvas instances
      User.objects.create_user( email = 'fatclub%s@example.com' % i, username = 'Fatclub %s' % i)
      Canvas.objects.create(title = 'Hella Derp %s' % i, date = (timezone.now() - datetime.timedelta(days = i)) )
      # Then create the collaborations instance and assign the two prior instances to it
      Collaborations.objects.create(canvasID = Canvas.objects.get(id = (i+1)), userID = User.objects.get(id = (i+1)) )

  def testIDs(self):
    for i in range(TEST_LIMIT):
      collab = Collaborations.objects.get(id = (i+1))
      self.assertEquals(collab.canvasID, Canvas.objects.get(id = (i+1)))
      self.assertEquals(collab.userID, User.objects.get(id = (i+1)))

  def testLinkedUsers(self):
    for i in range(TEST_LIMIT):
      collab = Collaborations.objects.get(id = (i+1))
      # as it turns out the user instance itself is acquired by assigning from the userID field - the instance is stored here, not the numeric ID 
      user = collab.userID
      self.assertEquals(user.email, 'fatclub%s@example.com' % i)
      self.assertEquals(user.username, 'Fatclub %s' % i)

  def testLinkedCanvasses(self):
    for i in range(TEST_LIMIT):
      collab = Collaborations.objects.get(id = (i+1))
      canvas = collab.canvasID
      self.assertEquals(canvas.title, 'Hella Derp %s' % i)
      self.assertTrue( (timezone.now() - datetime.timedelta(days = i)).date() == canvas.date )



class CommentsTestModel(TestCase):
  """

  """
  @classmethod
  def setUpTestData(cls):
    for i in range(TEST_LIMIT * 2):
      # ID Sequence: 1,3,5,7,9,11,13,15,17,19
      User.objects.create_user( email = 'fatclub%s@example.com' % i, username = 'Fatclub %s' % i)   # ODD
      # ID Sequence: 2,4,6,8,10,12,14,16,18,20
      User.objects.create_user( email = 'commenter%s@example.com' % i, username = 'Commenter %s' % i) # EVEN
    
    for i in range(TEST_LIMIT):
      # ID Sequence: 1,3,5,7,9,11,13,15,17,19
      Idea.objects.create( ownerID = User.objects.get(id = i*2 + 1),text = 'I am an idea and my name is %s' % (i+1)) 
      # ID Sequence: 2,4,6,8,10,12,14,16,18,20
      Comments.objects.create( ownerID = User.objects.get(id = i * 2 + 2), ideaID = Idea.objects.get(id = (i+1)), text = "ok but why though, evil boss %s" %i )

  def testInitiallyUnresolved(self):
    for i in range(TEST_LIMIT):
      comment = Comments.objects.get(id = i+1)
      self.assertFalse(comment.isResolved)

  def testLinkedIdea(self):
    for i in range(TEST_LIMIT):
      comment = Comments.objects.get(id = i+1)
      idea = comment.ideaID
      self.assertEquals(idea.text, 'I am an idea and my name is %s' % (i+1))

  def testCommenter(self):
    for i in range(TEST_LIMIT):
      comment = Comments.objects.get(id = i+1)
      user = comment.ownerID
      self.assertEquals( user.username, 'Commenter %s' % i )
      self.assertEquals( user.email, 'commenter%s@example.com' % i )

  def testOwnerOfLinkedIdea(self):
    for i in range(TEST_LIMIT):
      idea = Idea.objects.get(id=(i+1))
      user = idea.ownerID
      self.assertEquals( user.username, 'Fatclub %s' % i )
      self.assertEquals( user.email, 'fatclub%s@example.com' % i )
'''

'''
TAGS MODEL CHANGED - TESTS NO LONGER VALID



class TagListDoublingTestModel(TestCase):
  """
  """
  @classmethod
  def setUpTestData(cls):
    for i in range (TEST_LIMIT * 2):
      # 20 ideas, 2:1 idea:tag ratio - only text wanted for purposes of the test
      Idea.objects.create(text = 'I am an idea and my name is %s' % (i+1)) 
    for i in range (TEST_LIMIT):
      # Tag ID range 1,1,2,2,3,3,4,4,5,5
      # Compound ID (1,1)--(1,2) (2,3)--(2,4) (3,5)--(3,6) (4,7)--(4,8) (5,9)--(5,10)
      Tags.objects.create(ideaID = Idea.objects.get(id = i + 1))

  def testIdeaPairing(self):
    for i in range(TEST_LIMIT):
      # only test i values 0,2,4,6,8 as for odd values the tests will fail due to them starting too high for the given tagID
      if (i % 2 == 0):
        tag = Tags.objects.all()
        idea0 = tag[0].ideaID
        idea1 = tag[1].ideaID
        self.assertEquals(idea0.text, 'I am an idea and my name is %s' % (i+1))
        self.assertEquals(idea1.text, 'I am an idea and my name is %s' % (i+2))





class TagListTriplingTestModel(TestCase):
  """
  """
  @classmethod
  def setUpTestData(cls):
    for i in range (TEST_LIMIT * 3):
      # 30 ideas, 3:1 idea:tag ratio - only text wanted for purposes of the test
      Idea.objects.create(text = 'I am an idea and my name is %s' % (i+1)) 
    for i in range (12):
      # Tag ID range 1,1,1,2,2,2,3,3,3,4,4,4
      # Compound ID (1,1)--(1,2)--(1,3) (2,4)--(2,5)--(2,6) (3,7)--(3,8)--(3,9) (4,10)--(4,11)--(4,12)
      Tags.objects.create(ideaID = Idea.objects.get(id = i + 1))

  def testIdeaTripling(self):
    for i in range(12):
    # only test i values 0,3,6,9 as for other values the tests will fail due to them starting too high for the given tagID
      if (i%3 == 0):
        tag = Tags.objects.all()
        idea0 = tag[0].ideaID
        idea1 = tag[1].ideaID
        idea2 = tag[2].ideaID
        self.assertEquals(idea0.text, 'I am an idea and my name is %s' % (i+1))
        self.assertEquals(idea1.text, 'I am an idea and my name is %s' % (i+2))
        self.assertEquals(idea2.text, 'I am an idea and my name is %s' % (i+3))





class TagListManyTagsSingleIdea(TestCase):
  """
  """
  @classmethod
  def setUpTestData(cls):
    for i in range (TEST_LIMIT):
      Idea.objects.create(text = 'I am an idea and my name is %s' % (i+1)) 
      Tags.objects.create(Idea.tags = Idea.objects.get(id = 1))

  def testIdeaTripling(self):
    for i in range(TEST_LIMIT):
      tag = Tags.objects.all()
      # above query returns a singleton list of tag objects for some reason, which is distinct from a tag object
      idea = tag[0].Idea.tags
      self.assertEquals(idea.text, 'I am an idea and my name is %s' % (1))



'''

      


