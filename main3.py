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
import psycopg2


conn = psycopg2.connect(dbname="referral", user='postgres', password=pw, host= "35.225.56.214")


templates_dir = (os.path.join(os.path.dirname(__file__), 'templates'))
JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(templates_dir),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


authentication =['-804199651', '277964362', '-838395413', '1179386537', '2143074266', '484104542']

# [START LOGIN HANDLER]
class LoginHandler(webapp2.RequestHandler):
  def get(self):

    # Pass values into jinja, render, and write
    template = JINJA_ENVIRONMENT.get_template('welcome.html')

    template_rendered = template.render(template_values)

    self.response.write(template_rendered)
    
# [END LOGIN HANDLER]




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