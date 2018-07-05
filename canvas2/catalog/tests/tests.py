from django.test import TestCase
from django.utils import timezone
from catalog.models import Project, Canvas, CanvasTag, Idea, IdeaComment
from django.contrib.auth.models import User
import pytz
import datetime

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from channels.testing import ChannelsLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait


    # def test_idea_add(self):
        # self.browser.get('http://localhost:8000')
        # test_user = User.objects.create_user(
        #     username=f'test',
        #     email=f'test@example.com',
        #     password='zyxwvuts'
        # )



        # self.selenium.get('%s%s' % (self.live_server_url, '/accounts/login/'))
        # username_input = self.selenium.find_element_by_name("username")
        # username_input.send_keys('test')
        # password_input = self.selenium.find_element_by_name("password")
        # password_input.send_keys('zyxwvuts')
        # self.selenium.find_element_by_xpath('//input[@value="login"]').click()

        # project = Project(
        #     owner=test_user,
        #     is_public=False
        # )
        # project.save()
        # project.admins.add(test_user)
        # project.users.add(test_user)
        # project.save()

        # self.selenium.find_element_by_id('new-project').click()

        # canvas = Canvas(
        #     project=project
        # )
        # canvas.save()
        # self.selenium.find_element_by_id('new-ethics-canvas').click()
        # # self.selenium.get('%s%s' % (self.live_server_url, f'/catalog/canvas/{canvas.pk}'))
        # # first_idea_div = self.selenium.find_element_by_class_name('idea-flex-container-0')

        # for i in range(0, 10):
        #     self.selenium.find_element_by_css_selector(f'.idea-flex-container-{i} > .main-idea-buttons > #new-idea-button').click()
        # # button.click()

        # idea_input = self.selenium.find_element_by_css_selector('.idea-flex-container-0 > .idea-container > textarea.idea-input ')
        # idea_input.send_keys('DJANGO YOU MOTHERFUCKER!')


# VIEWS THAT NEED TEST CASES: 

# new_project
# class ProjectViewTestCases(TestCase):
#     def setUpTestData(cls):
#         for i in range(TEST_LIMIT):
#             User.objects.create_user(
#                 username=f'test_{i}',
#                 email=f'test{i}@example.com',
#                 password='zyxwvuts'
#             )


#         project = Project(
#             owner=test_user
#         )
#         project.admins.add(test_user)
#         project.users.add(test_user)
#         project.save()


# delete_project

# new_canvas

# delete_canvas





# ProjectListView

# ProjectDetailView

# CanvasDetailView




# new_idea

# delete_idea

# idea_detail




# comment_thread

# new_comment

# delete_comment

# comment_resolve




# index

# register

# add_user

# delete_user

# promote_user

# demote_user

# toggle_public




# add_tag

# remove_tag

# delete_tag




# get_canvasses_accessible_by_user

# update_canvas_session_variables

# search_canvas_for_tag

# user_permission

# admin_permission


