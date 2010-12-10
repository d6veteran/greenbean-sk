
"""Cool Beans base app"""

#Web enabled
#app name - sampyxisstockwatcher
FACEBOOK_APP_ID = "157819884231043"
FACEBOOK_APP_SECRET = "7142daa5ac2753ac6b06f70855830a9a"
#local
#app name - coolbeans-local
#FACEBOOK_APP_ID = "13641208923"
#FACEBOOK_APP_SECRET = "71e4b7fea11728cd8e0c022801b278b1"
SITE="gbsamtest"
#SITE="mymicrodonations"
_DEBUG = True

#local

import facebook
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

class FBUser(db.Model):
    id = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    updated = db.DateTimeProperty(auto_now=True)
    name = db.StringProperty(required=True)
    profile_url = db.StringProperty(required=True)
    access_token = db.StringProperty(required=True)
    total_votes = db.IntegerProperty()


class Bean(db.Model):
    author = db.StringProperty(required=True)
    content = db.StringProperty(multiline=True)
    id = db.StringProperty(required=True)
    status_id = db.StringProperty(required=True)
    date = db.DateTimeProperty(auto_now_add=True)
    votes = db.IntegerProperty()
    tags  = db.StringProperty()

    
class Tags(db.Model):
    tag=db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add=True)
    bean = db.ReferenceProperty(Bean, required=True)
    
class userBeanVote(db.Model):
    user = db.ReferenceProperty(FBUser,
                                required=True,
                                collection_name='Beans')
    bean = db.ReferenceProperty(Bean,
                                required=True,
                                collection_name='beanUser')
    createdon = db.DateTimeProperty(auto_now_add=True)

    
    
## The following code should be in it's own file
## I'll figure that out later
import  urllib, urllib2, socket
from django.utils import simplejson as json

def GetIPInfo(baseurl, ip=None, timezone=False) :
    """Same as GetCity and GetCountry, but a baseurl is required.  This is for if you want to use a different server that uses the the php scripts on ipinfodb.com."""
    passdict = {"output":"json"}
    if ip :
        try :
            passdict["ip"] = socket.gethostbyaddr(ip)[2][0]
        except : passdict["ip"] = ip
    if timezone :
        passdict["timezone"] = "true"
    else :
        passdict["timezone"] = "false"
    urldata = urllib.urlencode(passdict)
    url = baseurl + "?" + urldata
    urlobj = urllib2.urlopen(url)
    data = urlobj.read()
    urlobj.close()
    datadict = json.loads(data)
    return datadict

def GetCity(ip=None, timezone=False) :
    """Gets the location with the context of the city of the given IP.  If no IP is given, then the location of the client is given.  The timezone option defaults to False, to spare the server some queries."""
    baseurl = "http://ipinfodb.com/ip_query.php"
    return GetIPInfo(baseurl, ip, timezone)

def GetCountry(ip=None, timezone=False) :
    """Gets the location with the context of the country of the given IP.  If no IP is given, then the location of the client is given.  The timezone option defaults to False, to spare the server some queries."""
    baseurl = "http://ipinfodb.com/ip_query_country.php"
    return GetIPInfo(baseurl, ip, timezone)
## end of what should be in it's own file

class BaseHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):           
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            if cookie:
                # Store a local instance of the user data so we don't need
                # a round-trip to Facebook on every request
                user = FBUser.get_by_key_name(cookie["uid"])
                if not user:
                    graph = facebook.GraphAPI(cookie["access_token"])
                    profile = graph.get_object("me")
                    user = FBUser(key_name=str(profile["id"]),
                                id=str(profile["id"]),
                                name=profile["name"],
                                profile_url=profile["link"],
                                access_token=cookie["access_token"])
                    user.put()
                    
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()

                self._current_user = user
                getToken(cookie["access_token"])
                getID(user.id)
                
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
            'application_name': 'Green Bean',
            'city': GetCity()}
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
        user = FBUser.get_by_key_name(FBUserID)
                
        attachment = {}
        action_links = {}
        message = status_text
        caption = 'GreenBean is AWESOME. I am earning points by being Green!'
        attachment['caption'] = caption
        attachment['name'] = 'Play GreenBean'
        attachment['link'] = 'http://apps.facebook.com/' + SITE + '/user?user=' + user.id
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
        #Now put it all in the db
        bean = Bean(
            key_name=status_id,
            author = user.name,
            id = user.id,
            content = status_text,
            tags = self.request.get('tags'),
            status_id = status_id)
        bean.put()
        
        #now get tags
        #now add the tags
        #tag = tags()
        tag_names = self.request.get('tags').split()
        for tag_name in tag_names:
            #print(tag_name)
            Tags(tag=tag_name, bean=bean).put()
            
        #facebook.GraphAPI(FBAccess_token).put_wall_post(bean.content, attachment={"name": "Link name","link": "http://www.example.com/","caption": "{*actor*} posted a new review","description": "This is a longer description of the attachment","picture": "http://www.example.com/thumbnail.jpg"}, user.id)                 
        #self.generate('index.html', {
        #             'beans': beans})
        self.redirect('/')
        
class UserPost(BaseHandler):
    def get(self):
        status_id = self.request.get('userStatus')
        beans_query = Bean.all().order('-date')
        beans_query = beans_query.filter('status_id', status_id)
        beans = beans_query.fetch(10)

        self.generate('userStatus.html', {
                      'beans': beans,
                      'status_id':status_id,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})        

class User(BaseHandler):
    def get(self):
        user_id = self.request.get('user')
        beans_query = Bean.all().order('-date')
        beans_query = beans_query.filter('id', user_id)
        beans = beans_query.fetch(10)

        self.generate('index.html', {
                      'beans': beans,
                      'user_id':user_id,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})          
                    
class voteBean(webapp.RequestHandler):
    # Need error checking
     def get(self):
        key = self.request.get('id')
        bean = Bean.get(key)
        user = FBUser.get_by_key_name(bean.id)
        #first - make sure the user can vote on this
        #voted = userBeanVote(str(user.key()), str(bean.key())).get()
        #votedQ  = userBeanVote().filter('bean' , bean.key()).filter('user', user.key()).get()
        #print(user.userID)
        #print(bean.key())
        #votedQ = userBeanVote().get(user.userID,bean.key())
        #if votedQ:
        #    print('already voted: ')
        #    return
        if bean:
            i = bean.votes
            if i == None:
                i = 1
            bean.votes =  i + 1
            bean.put()
            
            #Now sum the total votes per user
            #user = beanUser.get_by_key_name(bean.user_id)
            if user:
                j = user.total_votes
                if j == None:
                    j = 1
                user.total_votes = j + 1
                user.put()
                        
            #Now - add them to the reference table - so they can only vote once
            userBeanVote(user=user, bean=bean).put()
            
        self.redirect('/')
        
class HomeHandler(BaseHandler):
    def get(self):         
        beans_query = Bean.all().order('-date')
        beans = beans_query.fetch(10)
                
        
        #self.response.out.write(template.render(path, template_values))
        self.generate('index.html', {
                       'beans': beans,
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
