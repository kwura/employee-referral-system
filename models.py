from google.appengine.ext import ndb
DEFAULT_THEME = 'Diet'

from google.appengine.api import search

def theme_key(theme_name = DEFAULT_THEME):
  """Constructs a Datastore key for a Theme entity
  theme_name will be used as the key
  """

  return ndb.Key('Theme', theme_name)

# [START Define Data Models]
  # we are gonna extend upon ndb.Model

class Athlete(ndb.Model):
  identity = ndb.StringProperty() # unique id number from google's users class
  email = ndb.StringProperty()
  profile_pic_url = ndb.StringProperty()
  blob_key = ndb.BlobKeyProperty()
  description = ndb.StringProperty()
  subs = ndb.StringProperty(repeated = True)
  user_name = ndb.StringProperty()


class Theme(ndb.Model):
  name = ndb.StringProperty(required = True)
  description = ndb.StringProperty()
  blob_key = ndb.BlobKeyProperty()
  cover_pic_url = ndb.StringProperty()

class Report(ndb.Model):
  athlete_username = ndb.StringProperty()
  athlete_id = ndb.StringProperty()
  athlete_profile_pic_url = ndb.StringProperty()
  description = ndb.StringProperty(indexed = False)
  timestamp = ndb.DateTimeProperty(auto_now_add = True)
  # location
  pic_url = ndb.StringProperty()
  blob_key = ndb.BlobKeyProperty()
  tags = ndb.StringProperty(repeated = True)
  theme = ndb.StructuredProperty(Theme)
  report_hash = ndb.StringProperty()

  def _post_put_hook(self, future):
    # put tags into a list searchable for the appengine search api
    transformed_tags = []
    for i in self.tags:
      field = search.TextField(name='tags', value = i)
      transformed_tags.append(field)
    
    doc_id = self.report_hash
    # pass these tags into the doc it each value must be a single string
    doc = search.Document(doc_id= doc_id, fields=transformed_tags)
    search.Index('tags').put(doc)
  

# [END Define Data Models]