from django import forms

from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _


class SignUpForm(forms.Form):
  '''
  Each field (both passwords at once in their case) is checked with it's own function as 
  by doing so all can be checked at once for errors and have errors thrown simultaneously.
  If the user happens to enter an email that already exists as well as a username that already
  exists and the two passwords don't match, then the user will be notified of all three errors
  without having to perform three correct_error - submit - read_error cycles
  '''
  name = forms.CharField()
  email = forms.EmailField()
  password = forms.CharField(max_length = 50, min_length = 8, widget = forms.PasswordInput)
  password2 = forms.CharField(max_length = 50, min_length = 8, widget = forms.PasswordInput)

   
  # clean passwords, two fields can't be declared as above 
  def clean(self):
    cleanName = self.cleaned_data['name']
    nameExists = User.objects.filter(username = cleanName).count()

    if nameExists > 0 :
      raise ValidationError(_('Username already exists. Please try a different one.'))

    mail = self.cleaned_data['email']
    emailExists = User.objects.filter(email = mail).count()
    
    if emailExists > 0 :
      raise ValidationError(_('An account already exists with the email provided. Please use a different email address, or log in.'))

    p1 = self.cleaned_data.get('password')
    p2 = self.cleaned_data.get('password2')

    if (p1 != p2):
      raise ValidationError(_('Passwords do not match.'))

    return self.cleaned_data

