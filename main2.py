#!/usr/bin/env python

# Copyright 2016 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# [Start Imports]
import logging # let's me print stuff in python
import webapp2 # request handler
import urllib
import os  # gives us access to directoris
import jinja2 # dynamic html handler
import time


from google.appengine.api import users
from google.appengine.api import search
from google.appengine.api import images
from google.appengine.ext import ndb # google's datastore model
from google.appengine.ext import blobstore
from google.appengine.ext.webapp import blobstore_handlers


from models import theme_key
from models import Athlete
from models import Report
from models import Theme
from models import DEFAULT_THEME

# [End Imports]


# Do the chron job tutorial

""" Go to where the directory is for templates
 logging.info(os.path.join(os.path.dirname(__file__), 'templates')) 
 and set up jinja environment
"""
templates_dir = (os.path.join(os.path.dirname(__file__), 'templates'))
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(templates_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)

# [START LOGIN HANDLER]
class LoginHandler(webapp2.RequestHandler):
  def get(self):
    
    # see if a user is logged in
    user = users.get_current_user()
    if(user):
      self.redirect('/home')
      return

    # link to google authentication
    url = users.create_login_url(dest_url = '/home')
    
    # store value in a dictionary to pass into jinja
    template_values = {'url' : url}

    # Pass values into jinja, render, and write
    template = JINJA_ENVIRONMENT.get_template('welcome.html')

    template_rendered = template.render(template_values)

    self.response.write(template_rendered)
    
# [END LOGIN HANDLER]

# [START HOME HANDLER]
class HomeHandler(webapp2.RequestHandler):
  def get(self):
    # see if a user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')
    
    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # Check if the user that's logged in exists in Athletes Datastore
    current_user_id = user.user_id()    
    check_athlete = Athlete.query(Athlete.identity == current_user_id).get()
    
    
    # Default values
    profile_pic_url = ""
    upload_img_button_text = "Add New Profile PIcture"
    profile_description = ""

    # See if this athlete exists
    if(check_athlete == None):
      # store athlete into datastore
      self.redirect('/newuser?' + 'first login')
      return
    
    
    # check if athlete has a profile pic url
    if(check_athlete.profile_pic_url != None):
      upload_img_button_text = "Change Profile PIcture"
      profile_pic_url = check_athlete.profile_pic_url
    
    # update the profile_description
    profile_description = check_athlete.description
      
      
    """ https://cloud.google.com/appengine/docs/standard/python/blobstore/
    this creates blobstore upload url that calls handler for upload_profile
    """
    upload_url = blobstore.create_upload_url('/upload_profile')
    
    # Put the results into a dictionary and pass it to jinja
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'profile_pic_url' : profile_pic_url,
            'upload_img_button_text' : upload_img_button_text,
            'upload_url' : upload_url,
            'profile_description' : profile_description,
            'check_athlete': check_athlete
    }

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there

    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("home.html")

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

  def post(self):
    # grab the current user's information
    user = users.get_current_user()
    current_user_id = user.user_id()    
    check_athlete = Athlete.query(Athlete.identity == current_user_id).get()
    
    # grab the description
    description = self.request.get('description')
    
    # store the description for the current user
    check_athlete.description = description
    check_athlete.put()
   
    # query parameters that go in url
    athlete_key = check_athlete.put()
    
    query_params = { 'athlete_key' : athlete_key}

    time.sleep(0.11)
    self.redirect('/home?' + urllib.urlencode(query_params))
    
    
# [END HOME HANDLER]

class NewUserHandler(webapp2.RequestHandler):
  def get(self):
    # see if a user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # the full URI path including query string
    path_qs = self.request.path_qs

    # create upload url for blob store
    upload_url = blobstore.create_upload_url('/upload_newuser')

    # Put the results into a dictionary
    template_values = {
            'upload_url': upload_url,
            'error' : error,
            'url': url,
            'url_linktext': url_linktext
    }
    
    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there

    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("newuser.html")


    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

class UploadNewUserHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):
    # default values
    error = ''

    # if user didn't select a file stay on home page
    if(len(self.get_uploads()) == 0):
      
      error = "Image Upload Is Required"
      query_params = {'error': error}
      self.redirect('/newuser?' + urllib.urlencode(query_params))
      return

    # grabs the upload of the profile picture
    upload = self.get_uploads()[0]

    # creates a url to the image upload
    url = images.get_serving_url(upload.key(), secure_url = True)

    # grab the form details
    user_name = self.request.get('user_name')
    description = self.request.get('description')

    # check if the user_name already exists!
    if(Athlete.query(Athlete.user_name == user_name).get()):
      error = "That Username already exists!"
      query_params = {'error': error}

      # Delete Blob Key
      blobstore.delete(upload.key())
      self.redirect('/newuser?' + urllib.urlencode(query_params))
      return

    # Check for any missing fields or mistakes
    if(len(user_name) == 0):
      error = "Username Is Required"
      query_params = {'error': error}

      # Delete Blob Key
      blobstore.delete(upload.key())
      self.redirect('/newuser?' + urllib.urlencode(query_params))
      return

    if(" " in user_name):
      error = "Spaces in Username Are Not Allowed"
      query_params = {'error': error}

      # Delete Blob Key
      blobstore.delete(upload.key())
      self.redirect('/newuser?' + urllib.urlencode(query_params))
      return

    if(len(description) == 0):
      error = "Profile Description Is Required"
      query_params = {'error': error}

      # Delete Blob Key
      blobstore.delete(upload.key())
      self.redirect('/newuser?' + urllib.urlencode(query_params))
      return
    
    # grab the user who just logged in's google info
    user = users.get_current_user()
    current_user_id = user.user_id() 

    # Create a new athlete object to store information
    new_athlete = Athlete()
    new_athlete.blob_key = upload.key()
    new_athlete.identity = current_user_id
    new_athlete.email = user.email()
    new_athlete.description = description
    new_athlete.profile_pic_url = url
    new_athlete.user_name = user_name

    # update the datastore
    new_athlete.put()

    # redirect back to page with new query parameters, give it time to process the data!
    time.sleep(0.20)
    new_athlete_key = new_athlete.key
    query_params = {'new_athlete_key': new_athlete_key}

    self.redirect('/home?' + urllib.urlencode(query_params))


# [START ProfilePicHandler]
""" inspired from Dr. Julien's code here
https://github.com/UT-APAD/ChristinesTestProject/blob/master/profile/main.py
"""

class ProfilePicHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):

    # if user didn't select a file stay on home page
    if(len(self.get_uploads()) == 0):
      self.redirect('/home?')
      return

    # grabs the upload
    upload = self.get_uploads()[0]

    # creates a url to the image upload
    url = images.get_serving_url(upload.key(), secure_url = True)
    
    # grab the current user's information
    user = users.get_current_user()
    current_user_id = user.user_id()    
    check_athlete = Athlete.query(Athlete.identity == current_user_id).get()
    
    # Delete old photo if there is one so that we can replace
    if(check_athlete.blob_key != None):
      blobstore.delete(check_athlete.blob_key)
    
    # Store the new blob key of the image
    check_athlete.blob_key = upload.key()
    
    # Store the image url and update the datastore
    check_athlete.profile_pic_url = url
    check_athlete.put()

    # Query all reports that this athlete has posted to 
    athlete_reports = Report.query(Report.athlete_id == check_athlete.identity).fetch()
    
    # update the usernames!
    for i in athlete_reports:
      i.athlete_profile_pic_url = url
      i.put()
    
    # redirect back to homepage, but give it time to process the data!
    time.sleep(0.11)
    self.redirect('/home')

    
      
# [END ProfilePicHandler]


# [START CREATE NEW POST HANDLER]
class CreateNewReportHandler(webapp2.RequestHandler):
  def get(self):

    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')


    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # create upload url for blob store
    upload_url = blobstore.create_upload_url('/upload_newpost')

    # grab theme names from datastore
    theme_name = Theme.query().order(Theme.name)
    theme_name = theme_name.fetch()
    
    # grab any errors
    error = self.request.get('error')

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'upload_url': upload_url,
            'theme_names': theme_name,
            'error': error
    }

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there

    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("createnewreport.html")


    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

# [END CREATE NEW POST HANDLER]

# [START REPORT AND PIC HANDLER]
class SubmitNewReportHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):

    # if user didn't select a file stay on create new report page
    if(len(self.get_uploads()) == 0):
      
      error = "Image Upload Is Required"
      query_params = {'error': error}
      self.redirect('/createnewreport?' + urllib.urlencode(query_params))
      return

    # grabs the upload
    upload = self.get_uploads()[0]

    # creates a url to the image upload
    url = images.get_serving_url(upload.key(), secure_url = True)
    
    # grab the current athlete and report details
    user = users.get_current_user()
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()
    report_message = self.request.get('message')


    # Check if post description is written
    if(len(report_message) == 0):
      error = "Description Is Required"
      query_params = {'error': error}
      
      # Delete Blob key 
      blobstore.delete(upload.key())

      self.redirect('/createnewreport?' + urllib.urlencode(query_params))
      return
     
    # Grab the tags and put in list
    report_tags = self.request.get('tags')
    report_tags = report_tags.split()

    if(len(report_tags) == 0):
      error = "Tags Are Required"
      query_params = {'error': error}

      # Delete Blob key 
      blobstore.delete(upload.key())

      self.redirect('/createnewreport?' + urllib.urlencode(query_params))
      return

    # Grab the selected theme
    theme_name = self.request.get('selectedtheme')

    # Create a report object to store picture url + blob, athlete , tags, and etc. 
    current_report = Report(parent=theme_key(theme_name))
    current_report.blob_key = upload.key()
    current_report.pic_url = url 
    current_report.tags = report_tags
    current_report.description = report_message
    current_report.theme = Theme.query(Theme.name == theme_name).get()
    current_report.athlete_username = current_athlete.user_name
    current_report.athlete_id = current_athlete.identity
    current_report.athlete_profile_pic_url = current_athlete.profile_pic_url
    current_report.report_hash = str(hash(tuple([current_report.timestamp, current_athlete.identity, url, current_report.description, current_report.key.urlsafe()])))

    # Update the datastore
    current_report.put()
    
    # redirect back to page with new query parameters, give it time to process the data!
    time.sleep(0.11)
    report_key = current_report.key
    query_params = {'report_key': report_key}

    self.redirect('/home?' + urllib.urlencode(query_params))

class CreateNewThemeHandler(webapp2.RequestHandler):
  def get(self):

    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'
   
    # create upload url for blob store
    upload_url = blobstore.create_upload_url('/upload_newtheme')

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'upload_url': upload_url,
            'error' : error
    }

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there

    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("createnewtheme.html")


    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

class SubmitNewThemeHandler(blobstore_handlers.BlobstoreUploadHandler):
  def post(self):

    # default values
    error = ''

    # if user didn't select a file stay on home page
    if(len(self.get_uploads()) == 0):
      
      error = "Image Upload Is Required"
      query_params = {'error': error}
      self.redirect('/createnewtheme?' + urllib.urlencode(query_params))
      return

    # grabs the upload
    upload = self.get_uploads()[0]

    # creates a url to the image upload
    url = images.get_serving_url(upload.key(), secure_url = True)
    
    # grab the current athlete and report details
    user = users.get_current_user()
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()
    theme_name = self.request.get('theme_name')

    # Check if the theme name already exists!
    if(Theme.query(Theme.name == theme_name).get()):
      error = "Theme Name Already Exists!"
      query_params = {'error': error}
      
      # Delete Blob key 
      blobstore.delete(upload.key())

      self.redirect('/createnewtheme?' + urllib.urlencode(query_params))
      return    
    
    
    # Check for any missing fields
    if(len(theme_name) == 0):
      error = "Theme Name Is Required"
      query_params = {'error': error}
      
      # Delete Blob key 
      blobstore.delete(upload.key())

      self.redirect('/createnewtheme?' + urllib.urlencode(query_params))
      return
      
    theme_description = self.request.get('description')

    if(len(theme_description) == 0):
      error = "Theme Description Is Required"
      query_params = {'error': error}

      # Delete Blob key 
      blobstore.delete(upload.key())

      self.redirect('/createnewtheme?' + urllib.urlencode(query_params))
      return

    # Create a theme object to store picture url + blob , and etc. 
    new_theme = Theme()
    new_theme.blob_key = upload.key()
    new_theme.cover_pic_url = url 
    new_theme.name = theme_name
    new_theme.description = theme_description
    

    # Update the datastore
    new_theme.put()
    
    # redirect back to page with new query parameters, give it time to process the data!
    time.sleep(0.11)
    new_theme_key = new_theme.key
    query_params = {'new_theme_key': new_theme_key}

    self.redirect('/home?' + urllib.urlencode(query_params))

class ManagementHandler(webapp2.RequestHandler):
  def get(self):
    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')


    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # grab current user from data store
    user = users.get_current_user()
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # grab all of his reports
    all_reports = Report.query(Report.athlete_id == current_athlete.identity).order(-Report.timestamp)
    all_reports = all_reports.fetch()

    # grab all of his subs
    subs = current_athlete.subs[:]

    # Check if a report exists
    if(len(all_reports) > 0):
      report_exist = True
    else:
      report_exist = False

    # check if a sub exists
    if( len(subs) > 0):
      sub_exist = True
    else:
      sub_exist = False

    # grab the current iteration of reports and subs from the post url
    iteration = self.request.get('iteration')
    if(len(iteration) == 0):
      iteration = '0'

    sub_iteration = self.request.get('sub_iteration')
    if(len(sub_iteration) == 0):
      sub_iteration = '0'
    
    # logic for previous button report button
    if(iteration == '0'):
      not_first = False
    else:
      not_first = True

    if(sub_iteration == '0'):
      sub_not_first = False
    else:
      sub_not_first = True

    # logic for next button report or sub button
    if(int(iteration) < len(all_reports) - 1):
      not_last = True
    else:
      not_last = False

    if(int(sub_iteration) < len(subs) - 1):
      sub_not_last = True
    else:
      sub_not_last = False

    # grab theme name, image url, date, and caption
    if(report_exist == True):
      current_report = all_reports[int(iteration)]
      theme_name = current_report.key.flat()[1]
      image_url = current_report.pic_url
      date = str(current_report.timestamp)
      caption = current_report.description
    
    else:
      theme_name = ""
      image_url = ""
      date = ""
      caption = ""

    # grab theme name, cover picture, description
    if(sub_exist == True):
      sub_theme_name = subs[int(sub_iteration)]
      current_sub = Theme.query(Theme.name == sub_theme_name).get()
      sub_image_url = current_sub.cover_pic_url
      sub_description = current_sub.description

    else:
      sub_theme_name = ""
      sub_image_url = ""
      sub_description = ""

    # grab any errors
    error = self.request.get('error')
    if(report_exist == False):
      no_reports_error = "You have no posts!"
    elif(len(all_reports) == 1):
      no_reports_error = "You have " + str(len(all_reports)) + " post!"
    elif(len(all_reports) > 1):
      no_reports_error = "You have " + str(len(all_reports)) + " posts!"

    if(sub_exist == False):
      no_subs_error = "You aren't subscribed to anything!"
    else:
      no_subs_error = "Number of subscriptions: " + str(len(subs))

    # the full URI path including query string
    path_qs = self.request.path_qs

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'theme_name': theme_name,
            'sub_theme_name': sub_theme_name,
            'error': error,
            'no_reports_error': no_reports_error,
            'no_subs_error': no_subs_error,
            'not_first': not_first,
            'sub_not_first': sub_not_first,
            'not_last': not_last,
            'sub_not_last': sub_not_last,
            'iteration': iteration,
            'sub_iteration': sub_iteration,
            'image_url': image_url,
            'sub_image_url': sub_image_url,
            'date': date, # might not exist
            'caption': caption, 
            'sub_description': sub_description,
            'report_exist': report_exist,
            'sub_exist': sub_exist,
            'path_qs' : path_qs
    }

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there

    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("management.html")


    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

  def post(self):
    # Grab the section
    section = self.request.get('section')

    # grab current user from data store
    user = users.get_current_user()
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # grab all of his reports
    all_reports = Report.query(Report.athlete_id == current_athlete.identity).order(-Report.timestamp)
    all_reports = all_reports.fetch()

    # grab the current iteration
    iteration = self.request.get('iteration')
    iteration = int(iteration)

    # grab the current iteration
    iteration = self.request.get('iteration')
    iteration = int(iteration)

    sub_iteration = self.request.get('sub_iteration')
    sub_iteration = int(sub_iteration)

    # is this a post request from my posts or subscriptions?
    if(section == 'myposts'):

      # determine the iterationbutton
      iterationbutton = self.request.get('iterationbutton')
    
      # grab either the previous or next iteration
      if(iterationbutton == 'Previous'):
        iteration -= 1

      elif(iterationbutton == 'Next'):
        iteration += 1

    elif(section == 'subs'):

      # determine the sub_iterationbutton
      sub_iterationbutton = self.request.get('sub_iterationbutton')

      # grab either the previous or next iteration
      if(sub_iterationbutton == 'Previous'):
        sub_iteration -= 1

      elif(sub_iterationbutton == 'Next'):
        sub_iteration += 1

     
    # pass next iterations to the get handler
    query_params = {'iteration' : iteration, 'sub_iteration' : sub_iteration}
    time.sleep(0.11)
    self.redirect('/management?' + urllib.urlencode(query_params))
    
class DeleteReportHandler(webapp2.RequestHandler):
  """ To delete a report we need to know
      the current iteration, report_exist boolean
  """
  def post(self):
    # grab the current iteration
    iteration = self.request.get('iteration')
    iteration = int(iteration)

    # grab current user from data store
    user = users.get_current_user()
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # grab all of his reports
    all_reports = Report.query(Report.athlete_id == current_athlete.identity).order(-Report.timestamp)
    all_reports = all_reports.fetch()

    # Delete the iteration of those reports and save the deletion 
    all_reports[iteration].key.delete()

    # pass first iteration to the get handler
    iteration = 0
    query_params = {'iteration' : iteration}
    time.sleep(0.11)
    self.redirect('/management?' + urllib.urlencode(query_params))

class ViewAllThemesHandler(webapp2.RequestHandler):
  def get(self):
    """ We gonna need theme name and picture and a subscribe
    button next to each theme. We also need the current user.
    """

    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # Grab all themes!
    all_themes = Theme.query().order(Theme.name)
    all_themes = all_themes.fetch()

    # the full URI path including query string
    path_qs = self.request.path_qs

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there
    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("browse.html")

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'error' : error,
            'themes': all_themes,
            'current_athlete': current_athlete,
            'path_qs': path_qs
    }

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

class SubscriptionHandler(webapp2.RequestHandler):
  def post(self):
    # grab the page where this post request came from
    page = self.request.get('page')
    
    # grab the relevant theme
    theme_name = self.request.get('theme_name')

    # Is the user unsubscribing or subscribing?
    subbutton = self.request.get('subbutton')

    # grab current user from data store
    user = users.get_current_user()
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()
    
    # either append or remove the user's subs list
    reference = current_athlete.subs[:]
    if(subbutton == 'Subscribe'):
      reference.append(theme_name)
      reference.sort()
      current_athlete.subs = reference[:]
      current_athlete.put()
    
    elif(subbutton == 'Unsubscribe' or subbutton == 'Unsubscribe Theme'):
      reference.remove(theme_name)
      current_athlete.subs = reference[:]
      current_athlete.put()
    
    time.sleep(0.11)
    self.redirect(page)

class FeedHandler(webapp2.RequestHandler):
  # get all of the users subscribed reports
  def get(self):
    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # grab the current user's subs
    subs = current_athlete.subs[:]

    # the full URI path including query string
    path_qs = self.request.path_qs

    # query the subscriptions based on timestamp
    reports = []
    if(len(subs) > 0):
      reports = Report.query(Report.theme.name.IN(subs)).order(-Report.timestamp).fetch()
    
    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there
    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("feed.html")

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'error' : error,
            'current_athlete': current_athlete,
            'path_qs': path_qs,
            'reports': reports
    }

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

class ViewThemeHandler(webapp2.RequestHandler):
  def get(self):
    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # the full URI path including query string
    path_qs = self.request.path_qs

    # grab the previous link
    prev_link = self.request.get('previouslink')

    # grab the theme name
    theme_name = self.request.get('view_theme_name')

    # grab the theme object
    theme_query = Theme.query(Theme.name == theme_name).get()
    sub_image_url = theme_query.cover_pic_url
    sub_description = theme_query.description

    # grab all posts based on that themename
    theme_reports_query = Report.query(
      ancestor=theme_key(theme_name)).order(-Report.timestamp)
    theme_reports = theme_reports_query.fetch()

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there
    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("view.html")

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'error' : error,
            'current_athlete': current_athlete,
            'path_qs': path_qs,
            'reports': theme_reports,
            'name_of_theme': theme_name,
            'current_athlete': current_athlete,
            'sub_image_url': sub_image_url,
            'sub_description': sub_description
    }

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)


class ViewProfileHandler(webapp2.RequestHandler):
  def get(self):
    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # the full URI path including query string
    path_qs = self.request.path_qs

    # grab the other user
    other_user_identity = self.request.get('other_user_identity')

    # query this user info
    other_user = Athlete.query(Athlete.identity == other_user_identity).get()

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there
    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("viewprofile.html")

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'error' : error,
            'current_athlete': current_athlete,
            'path_qs': path_qs,
            'other_user': other_user
    }

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

class ChangeUsernameHandler(webapp2.RequestHandler):
  def get(self):
    # grab any errors
    error = self.request.get('error')

    # see if a user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')
    
    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # Check if the user that's logged in exists in Athletes Datastore
    current_user_id = user.user_id()    
    check_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    template_values = {
            'error': error,
            'url': url,
            'url_linktext': url_linktext,
    }

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there

    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("changeusername.html")

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

  def post(self):
    # default values
    error = ''

    # grab the form details
    user_name = self.request.get('user_name')

    # grab the user's info
    user = users.get_current_user()
    current_user_id = user.user_id() 
    check_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # check if its the same username!
    if(check_athlete.user_name == user_name):
      error = "You're Already Using That Username"
      query_params = {'error': error}
      self.redirect('/changeusername?' + urllib.urlencode(query_params))
      return

    # check if the user_name already exists!
    if(Athlete.query(Athlete.user_name == user_name).get()):
      error = "That Username already exists!"
      query_params = {'error': error}
      self.redirect('/changeusername?' + urllib.urlencode(query_params))
      return

    # other errors
    if(" " in user_name):
      error = "Spaces in Username Are Not Allowed"
      query_params = {'error': error}
      self.redirect('/changeusername?' + urllib.urlencode(query_params))
      return   

    if(user_name == ""):
      error = "Username can't be blank!"
      query_params = {'error': error}
      self.redirect('/changeusername?' + urllib.urlencode(query_params))
      return   
    
    # update the datastore for everything
    check_athlete.user_name = user_name
    check_athlete.put()

    # Query all reports that this athlete has posted to 
    athlete_reports = Report.query(Report.athlete_id == check_athlete.identity).fetch()
    
    # update the usernames!
    for i in athlete_reports:
      i.athlete_username = user_name
      i.put()

    # redirect back to page with new query parameters, give it time to process the data!
    time.sleep(0.50)
    athlete_key = check_athlete.key
    query_params = {'athlete_key': athlete_key}

    self.redirect('/home?' + urllib.urlencode(query_params))

class ViewUserReports(webapp2.RequestHandler):
  def get(self):
    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # the full URI path including query string
    path_qs = self.request.path_qs

    # grab the other user
    other_user_identity = self.request.get('other_user_identity')

    # query this user info
    other_user = Athlete.query(Athlete.identity == other_user_identity).get()
    reports = Report.query(Report.athlete_id == other_user_identity).fetch()

    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there
    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("usersreports.html")

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'error' : error,
            'path_qs': path_qs,
            'other_user': other_user,
            'reports' : reports,
            'current_athlete': current_athlete
    }

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)


# From Piazza! https://piazza.com/class/jiumfj0p7mk7ce?cid=26
class Search(webapp2.RequestHandler):
  def get(self):
    options = search.QueryOptions(limit=5)
    query_string = self.request.get('query_string')

    query = search.Query(query_string=query_string, options=options)
    results = search.Index('tags').search(query)
    doc_ids = ""
    for i in results:
      doc_ids += i.doc_id + " "
    
    query_params = {'doc_ids': doc_ids}

    self.redirect('/search_page?' + urllib.urlencode(query_params))

class SearchPageHandler(webapp2.RequestHandler):
  def get(self):
    # See if user is logged in
    user = users.get_current_user()
    if(user == None):
      self.redirect('/')

    # grab current user from data store
    current_user_id = user.user_id()
    current_athlete = Athlete.query(Athlete.identity == current_user_id).get()

    # grab any error codes
    error = self.request.get('error')

    # If a user is logged in create a logout button that will redirect to login page
    url = users.create_logout_url(dest_url = '/')
    url_linktext = 'Logout'

    # the full URI path including query string
    path_qs = self.request.path_qs

    # grab any doc_ids which are equal to Report.report_hash
    doc_ids = self.request.get('doc_ids')
    doc_ids = doc_ids.split()
    

    # query all the reports
    reports = []
    for i in doc_ids:

      a_report = Report.query(Report.report_hash == i).get()
      # error checking
      if(a_report != None):
        reports.append(a_report)
    
    # Catch errors
    if(len(reports) == 0):
      error = 'There seems to be nothing here. Search 1 Tag At a Time!!!'


    # We should store our html files separately in a directory called templates, 
    # and do our dynamic html typing there
    # Use jinja2 to create template
    template = JINJA_ENVIRONMENT.get_template("search.html")

    # Put the results into a dictionary
    template_values = {
            'url': url,
            'url_linktext': url_linktext,
            'error' : error,
            'path_qs': path_qs,
            'reports': reports,
            'current_athlete': current_athlete
    }

    # render the template and pass in the results dictionary
    rendered_template = template.render(template_values)

    # Send the rendered template back to the client
    self.response.write(rendered_template)

# [START APP]
app = webapp2.WSGIApplication([
  ('/', LoginHandler),
  ('/home', HomeHandler),
  ('/newuser', NewUserHandler),
  ('/createnewreport', CreateNewReportHandler),
  ('/createnewtheme', CreateNewThemeHandler),
  ('/management', ManagementHandler),
  ('/browse', ViewAllThemesHandler),
  ('/subscriptions', SubscriptionHandler),
  ('/feed', FeedHandler),
  ('/viewtheme', ViewThemeHandler),
  ('/viewprofile', ViewProfileHandler),
  ('/changeusername', ChangeUsernameHandler),
  ('/view_user_reports', ViewUserReports),
  ('/upload_profile', ProfilePicHandler),
  ('/upload_newpost', SubmitNewReportHandler),
  ('/upload_newtheme', SubmitNewThemeHandler),
  ('/upload_newuser', UploadNewUserHandler),
  ('/deletereport', DeleteReportHandler),
  ('/search/*', Search),
  ('/search_page', SearchPageHandler)
], debug = True)  

# [END APP]