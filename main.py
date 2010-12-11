
"""Cool Beans base app"""

#Web enabled
#app name - sampyxisstockwatcher
#FACEBOOK_APP_ID = "157819884231043"
#FACEBOOK_APP_SECRET = "7142daa5ac2753ac6b06f70855830a9a"
#local
#app name - coolbeans-local
FACEBOOK_APP_ID = "13641208923"
FACEBOOK_APP_SECRET = "71e4b7fea11728cd8e0c022801b278b1"
#SITE="gbsamtest"
SITE="mymicrodonations"
# local site: http://apps.facebook.com/mymicrodonations/
_DEBUG = True

#local

import facebook
import models
import location
import os.path
import wsgiref.handlers
import cgi
import os

from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import run_wsgi_app


#
# need to just change these to global vars below the facebook app id
def getToken(token=""):
    global FBAccess_token     
    if token =="":
        return FBAccess_token
    FBAccess_token = token
    return FBAccess_token

def getID(id=""):
    global FBUserID    
    #FBUserID = ""
    if id=="":
        return FBUserID
    FBUserID = id
    return FBUserID
  
    
class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):
        #for now - adding a location
        #loc = Location(city="Chicago", state="IL", country="US")
        #loc.put()
        #cat = models.Category(name="Green")
        #cat.put()
        
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = models.User.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = models.User(key_name=str(profile["id"]),
                                fb_id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                fb_access_token=cookie["access_token"])
                    user.put()
                    
                elif user.fb_access_token != cookie["access_token"]:
                    user.fb_access_token = cookie["access_token"]
                    user.put()

                self._current_user = user
                getToken(cookie["access_token"])
                getID(user.fb_id)
                
        return self._current_user
    
    def generate(self, template_name, template_values={}):

        values = {
            #'url': url,
            #'url_linktext': url_linktext,
            'request': self.request,
            'user': self.current_user,
            #'login_url': users.create_login_url(self.request.uri),
            #'logout_url': users.create_logout_url('http://%s/' % (
            #    self.request.host,)),
            'debug': self.request.get('deb'),
            'application_name': 'Green Bean'}
            #'city': GetCity()}
        values.update(template_values)
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', template_name))
        self.response.out.write(template.render(path, values, debug=_DEBUG))
    

class postStatus(BaseHandler):
    def post(self):

        #now post on the wall
        # The function below works - but I'm looking at something more
        # robust - hence the put_wall_post function
        #facebook.GraphAPI(FBAccess_token).put_object(user.id, "feed", message=bean.content)
        
        status_text = self.request.get('content')
        #userC = self.current_user
        #user = FBUser.get_by_key_name(FBUserID)
        user = models.User.get_by_key_name(FBUserID)
                
        attachment = {}
        action_links = {}
        message = status_text
        caption = 'GreenBean is AWESOME. I am earning points by being Green!'
        attachment['caption'] = caption
        attachment['name'] = 'Play GreenBean'
        attachment['link'] = 'http://apps.facebook.com/' + SITE + '/user?user=' + user.fb_id
        attachment['description'] = 'Vote for my Bean!'
        attachment['picture'] = 'http://greenbean.me/public/checkresizeimg.php?src=user_image/41388_679874743_5282_n.jpg&w=35&h=35&zc=1'
        action_links['text'] = 'Vote for my Bean'
        action_links['href'] = 'http://apps.facebook.com/gbsamtest/'
        #facebook.GraphAPI(FBAccess_token).put_post_w_action(message, attachment, action_links)
        results = {}     
        # take the 2 lines out below to just update the db - not facebook
        # good for testing
        results  = facebook.GraphAPI(FBAccess_token).put_wall_post(message, attachment)
        status_id = str(results['id'])
        #status_id = 'ldldl'
        
        # Get the users category
        cat_names = self.request.get_all('tag_checks')           
        
        #Now put it all in the db
        brag = models.Brag(
            user = user,
            category = cat_names,
            message = status_text,
            origin = 'Facebook')
        brag.put()
        
        #now get tags
        #now add the tags
        #tag = tags()
        #tag_names = self.request.get('tags').split()
        #new_tags = self.request.get_all('tag_checks')
        #for tag_name in new_tags:
            #print(tag_name)
         #   Tags(tag=tag_name, bean=bean).put()
            
        #facebook.GraphAPI(FBAccess_token).put_wall_post(bean.content, attachment={"name": "Link name","link": "http://www.example.com/","caption": "{*actor*} posted a new review","description": "This is a longer description of the attachment","picture": "http://www.example.com/thumbnail.jpg"}, user.id)                 
        #self.generate('index.html', {
        #             'beans': beans})
        self.redirect('/')
        
class UserPost(BaseHandler):
    def get(self):
        status_id = self.request.get('userStatus')
        brag_query = models.Brag.all().order('-date')
        brag_query = brag_query.filter('status_id', status_id)
        brags = brag_query.fetch(10)

        self.generate('userStatus.html', {
                      'brags': brags,
                      'status_id':status_id,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})        

class User(BaseHandler):
    def get(self):
        user_id = self.request.get('user')
        brag_query = models.Brag.all().order('-date')
        brag_query = beans_query.filter('id', user_id)
        brags = brag_query.fetch(10)

        self.generate('index.html', {
                      'brags': brags,
                      'user_id':user_id,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})          
                    
class voteBean(webapp.RequestHandler):
    # Need error checking
     def get(self):
        key = self.request.get('id')
        brag = models.Brag.get(key)
        user = models.User.get_by_key_name(FBUserID)

        if (brag and user):
            # create bean
            # need to get the get_or_insert working - so there can only be one person one vote per bean
            #bean = models.Bean.get_or_insert(brag, user, brag=brag, user=user)
            bean = models.Bean(brag = brag, user = user).put()
            
            # now that the bean is in - add the vote
            # So, we're using get_or_insert here - using the key_name (which for us is the key from the brag
            #  this insures that it's unique)
            bragKey = str(brag.key())
            print(bragKey)
            bragbeans = models.BragBeans.get_or_insert(bragKey, brag=brag, bean_count=0)
            #if bragbeans:
            i = bragbeans.bean_count
            if i == None:
                    i = 1
            bragbeans.bean_count =  i + 1
            #bragbeans.brag = brag
            bragbeans.put()
            
            #Now sum the total beans per user
            #Create the row in UserBeans the first time the user gets a vote
            userKey = str(user.key())
            print(userKey)
            userBeans = models.UserBeans.get_or_insert(userKey, user=user, bean_count=0)
            i = userBeans.bean_count
            if i == None:
                i = 1
            userBeans.bean_count = i +1
            userBeans.put()

            #Now do the same for categories
            
            #Now do the same for location
        self.redirect('/')
        
class HomeHandler(BaseHandler):
    def get(self):         
        brag_query = models.Brag.all().order('-create_date')
        brags = brag_query.fetch(10)
                
        
        #self.response.out.write(template.render(path, template_values))
        self.generate('index.html', {
                       'brags': brags,
                       'current_user': self.current_user,
                       'facebook_app_id':FACEBOOK_APP_ID})


def main():
    util.run_wsgi_app(webapp.WSGIApplication([(r"/", HomeHandler),
                                              ('/sign', postStatus),
                                              ('/userPost', UserPost),
                                              ('/user', User),
                                              ('/vote', voteBean)],
                                              debug=True))


if __name__ == "__main__":
    main()