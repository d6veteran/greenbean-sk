#Web enabled
#app name = sampyxisstockwatcher
#FACEBOOK_APP_ID = "157819884231043"
#FACEBOOK_APP_SECRET = "7142daa5ac2753ac6b06f70855830a9a"
#local
#app name - coolbeans-local
#FACEBOOK_APP_ID = "13641208923"
#FACEBOOK_APP_SECRET = "71e4b7fea11728cd8e0c022801b278b1"
#SITE="gbsamtest"
#SITE="mymicrodonations"
## LOCALHOST:8080
FACEBOOK_APP_ID = "174331539272451"
FACEBOOK_APP_SECRET = "f4f8e3762a2abbe62dee8bf44a4967a4"
SITE="localhosttest-sk"
CATS=["Reduse","Reuse","Recycle","Organic","Wind","Solar",
      "Walk","Bus","Bike","Local","Carpool"]

# local site: http://apps.facebook.com/mymicrodonations/
DEBUG = True

#local

import base64
import cgi
import Cookie
import email.utils
import hashlib
import hmac
import logging
import os.path
import time
import urllib
import wsgiref.handlers
import models
import facebook
import re

from django.utils import simplejson as json
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import util
from google.appengine.ext.webapp import template

############################# REQUEST HANDLERS ###############################
    
class MainHandler(webapp.RequestHandler):
    """Provides access to the active Facebook user in self.current_user

    The property is lazy-loaded on first access, using the cookie saved
    by the Facebook JavaScript SDK to determine the user ID of the active
    user. See http://developers.facebook.com/docs/authentication/ for
    more information.
    """
    @property
    def current_user(self):
        logging.info('########### BaseHandler:: current_user ###########')
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
                                       fb_profile_url=profile["link"],
                                       access_token=cookie["access_token"])
                    user.put()
                elif user.access_token != cookie["access_token"]:
                    user.access_token = cookie["access_token"]
                    user.put()
                self._current_user = user
        return self._current_user
    
    def generate(self, template_name, template_values):
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', template_name))
        self.response.out.write(template.render(path, template_values, debug=DEBUG))

class BaseHandler(MainHandler):
    """Returns content for the home page.
    """
    def get(self):
        # TODO: build lists of top users, categories and locations.
        logging.info("#############  BaseHandler:: get(self): ##############")
        text = "TODO: build lists of top users, categories and locations."
        if facebookRequest(self.request):
            template = "facebook/fb_base_index.html"            
        else:    
            template = "base_index.html"        
        self.generate(template, {
                      'text': text,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})

class UserProfile(MainHandler):
    """Returns content for User Profile pages.
    """
    def get(self, user_id=None):
        logging.info('################# UserProfile::get ###################')
        user = self.current_user # this is the logged in User
        profile_user = getFBUser(fb_id=user_id) # this is the profiled User
        brag_query = models.Brag.all().order('-create_date')
        brag_query = brag_query.filter('user', profile_user)
        brags = brag_query.fetch(20)
        newBrag = []        
        catList = []
        for i in brags: # get Bean count and Categories for Brags
           brag = i
           bCount = db.GqlQuery("SELECT * FROM BragBeans WHERE brag=:1", brag)
           bCount.fetch(1)
           bean_count = 0
           for count in bCount:
             bean_count = count.bean_count
           newBrag.append({'brag':i, 'bCount':bean_count})
           

        if facebookRequest(self.request):
            template = "facebook/fb_base_user_profile.html"
            
        else:    
            template = "base_user_profile.html"
        
        self.generate(template, {
                      'brags': newBrag,
                      'profile_user': profile_user,
                      'categories': CATS,
                      'current_user': self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID}) 
                      
    def post(self, user_id=None):
        """POSTs a new Brag.
        """
        logging.info('################## UserProfile::post #################')
        user = getFBUser(fb_id=user_id) # this is the profiled User
        message = self.request.get('message')
        origin = self.request.get('origin')
        categories = self.request.get_all('category')
        brag = models.Brag(user = user,
                           categories = categories,
                           message = message,
                           origin = origin)
        brag.put()
        self.redirect('/user/'+user_id)  
        return          
        
class CategoryProfile(MainHandler):
    """Returns content for Category Profile pages.
    """    
    def get(self, category=None):
        logging.info('################ CategoryProfile::get ################')
        if facebookRequest(self.request):
            template = "facebook/fb_base_category_profile.html"
            
        else:    
            template = "base_category_profile.html"
            
        self.generate(template, {
                      'text': text,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})  
    
class LocationProfile(MainHandler):
    """Returns content for Location Profile pages.
    """    
    def get(self, location=None):
        logging.info('################ LocationProfile::get ################')        
        if facebookRequest(self.request):
            template = "facebook/fb_base_location_profile.html"
            
        else:    
            template = "base_location_profile.html"
            
        self.generate(template, {
                      'text': text,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})   
    
            
"""        class HomeHandler(BaseHandler):
            def get(self):

                facebookRequest(self.request)

                brag_query = models.Brag.all().order('-create_date')
                user = self.current_user
                brag_query = brag_query.filter('user', user)
                brags = brag_query.fetch(20)
                # for each brag - get the category  

                newBrag = []        
                catList = []
                for i in brags:
                   brag = i
                   catQuery = models.BragCategory.all()
                   catQuery = catQuery.filter("brag", brag)
                   cats = catQuery.fetch(10)
                   #get bean count for brag
                   bCount = db.GqlQuery("SELECT * FROM BragBeans WHERE brag=:1", brag)
                   bCount.fetch(1)
                   bean_count = 0
                   for count in bCount:
                    bean_count = count.bean_count
                   if cats:
                    for x in cats:
                     cat = models.Category.get(x.category.key())
                     catList.append(cat.name)
                   newBrag.append({'cats':catList, 'brag':i, 'bCount':bean_count})
                   catList = []

                self.generate('index.html', {
                               'newBrags': newBrag,
                               'current_user': self.current_user,
                               'facebook_app_id':FACEBOOK_APP_ID})

class postStatus(BaseHandler):
    def post(self):

        #now post on the wall
        status_text = self.request.get('content')
        user = self.current_user
        
        #first check that the status is less than 140 chars
        if len(status_text) > 140:
            print("error")
            self.redirect('/')   
                
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
        results  = facebook.GraphAPI(user.fb_access_token).put_wall_post(message, attachment)
        status_id = str(results['id'])
        #status_id = 'This is for testing'       
        
        #remove all this once categories work
        # Get the users category
        cat_names = self.request.get_all('cat_checks')
        
        # With the change in categories - may not need this
        #get the category keys for the reference
        #right now - puts the first one - we need to make cat_ref a list
        catKey = [] 
        for cat_name in cat_names:
            catKey.append( models.Category.get(cat_name).name)
        
        #Now put it all in the db
        brag = models.Brag(
            user = user,
            category = catKey,
            #category_ref = catKey,
            message = status_text,
            origin = 'Facebook')
        brag.put()
        
        # With the change in categories - may not need this
        #now get categories
        # store the brag and category in the BragCategory Table
        new_cats = self.request.get_all('cat_checks')
        for cat_checks in new_cats:
           if new_cats:
            cat = models.Category.get(cat_checks)
            models.BragCategory(brag=brag, category=cat).put()

        self.redirect('/')     
       
# This function is used when we want to view all beans from a particular
# user that is not the user logged in
class User(BaseHandler):
    def get(self):
        user_id = self.request.get('user')
        user = models.User.get_by_key_name(user_id)
        brag_query = models.Brag.all().order('-create_date')
        brag_query = brag_query.filter('user', user)
        brags = brag_query.fetch(20)

        newBrag = []        
        catList = []
        for i in brags:
           brag = i
           catQuery = models.BragCategory.all()
           catQuery = catQuery.filter("brag", brag)
           cats = catQuery.fetch(10)
           #get bean count for brag
           bCount = db.GqlQuery("SELECT * FROM BragBeans WHERE brag=:1", brag)
           bCount.fetch(1)
           bean_count = 0
           for count in bCount:
            bean_count = count.bean_count
           if cats:
            for x in cats:
             cat = models.Category.get(x.category.key())
             catList.append(cat.name)
            newBrag.append({'cats':catList, 'brag':i, 'bCount':bean_count})
            catList = []
            
        self.generate('index.html', {
                      'newBrags': newBrag,
                      'user_id':user_id,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})          
                    
class voteBean(BaseHandler):
    # Need error checking
     def get(self):
        key = self.request.get('id')
        brag = models.Brag.get(key)
        user = self.current_user
        
        if (brag and user):
            # create bean
            # User can only vote for a Bean once, so make sure they haven't already voted
            # do a query using both brag and user
            # if none - then put
            q = db.GqlQuery("select * from Bean where user =:1 and brag=:2", user.key(), brag.key())
            count = q.count(1)
            if count == 0:
                bean = models.Bean(brag = brag, user = user).put()

                # now that the bean is in - add the vote
                # So, we're using get_or_insert here - using the key_name (which for us is the key from the brag
                #  this insures that it's unique)
                bragKey = str(brag.key())
                bragbeans = models.BragBeans.get_or_insert(bragKey, brag=brag, bean_count=0)
                #if bragbeans:
                i = bragbeans.bean_count
                if i == None:
                        i = 1
                bragbeans.bean_count =  i + 1
                bragbeans.put()
            
                #Now sum the total beans per user
                #Create the row in UserBeans the first time the user gets a vote
                userKey = str(user.key())
                userBeans = models.UserBeans.get_or_insert(userKey, user=user, bean_count=0)
                i = userBeans.bean_count
                if i == None:
                    i = 1
                userBeans.bean_count = i +1
                userBeans.put()

                 Arg...can't get this to work yet!
                #Now do the same for categories
                
                for category in brag.category:
                    catKey = models.Category.all().filter("name", category).fetch(1)
                    print(catKey)
                    #caKey = str(catKey.key())
                    c = models.Category.get('ag9jb29sYmVhbnMtbG9jYWxyDgsSCENhdGVnb3J5GHYM')
                    print(c.name)
                    catBean = models.CategoryBeans.get_or_insert(c.key(), category=category, bean_count=0)
                    #catQuery = db.GqlQuery("select bean_count from CategoryBeans where category =:1", category)
                    #catQuery.fetch(1)
#                    catQuery = models.CategoryBeans.all().filter("name", categories).fetch(1)
                    print(catBean.bean_count)
                    i = catQuery.bean_count
                    if i == None:
                        i = 1
                    catQuery.bean_count = i + 1
                    catQuery.put()
                  
            
            #Now do the same for location
        self.redirect('/')

        
# New oauth facebook code
class LoginHandler(BaseHandler):
    def get(self):
        verification_code = self.request.get("code")
        args = dict(client_id=FACEBOOK_APP_ID, redirect_uri="http://apps.facebook.com/" + SITE + "/auth/login" )
        #redir = self.request.path_url
        redir = "http://apps.facebook.com/" + SITE + "/auth/login"
        if self.request.get("code"):
            args["client_secret"] = FACEBOOK_APP_SECRET
            args["code"] = self.request.get("code")
            args["scope"] = "user_photos,user_videos,publish_stream,read_stream"
            response = cgi.parse_qs(urllib.urlopen(
                "https://graph.facebook.com/oauth/access_token?" +
                urllib.urlencode(args)).read())
            print(response)
            access_token = response["access_token"][-1]

            # Download the user profile and cache a local instance of the
            # basic profile info            
            profile = json.load(urllib.urlopen(
                "https://graph.facebook.com/me?" +
                urllib.urlencode(dict(access_token=access_token))))
            user = models.User(key_name=str(profile["id"]),
                        fb_id=str(profile["id"]),
                        name=profile["name"],
                        fb_access_token=access_token,
                        profile_url=profile["link"])
            user.put()
            
            #This is on here for iframe issues with IE
            self.response.headers["P3P"] = 'CP="IDC CURa ADMa OUR IND PHY ONL COM STA"'
            set_cookie(self.response, "fb_user", str(profile["id"]),
                       expires=time.time() + 30 * 86400)
            self.redirect("/")
        else:
            args["scope"] = "user_photos,user_videos,publish_stream,read_stream"
            #self.redirect(
            #    "https://graph.facebook.com/oauth/authorize?" +
            #    urllib.urlencode(args) )
            args1 = urllib.urlencode(args)
            self.generate('fbAuth.html', {
                   'current_user': self.current_user,
                   'redirection': redir,
                   'scope': "user_photos,user_videos,publish_stream,read_stream",
                   'facebook_app_id':FACEBOOK_APP_ID})


class LogoutHandler(BaseHandler):
    def get(self):
        set_cookie(self.response, "fb_user", "", expires=time.time() - 86400)
        self.redirect("/")
"""

############################### METHODS ######################################

def facebookRequest(request):
    """Returns True if request is from a Facebook iFrame, otherwise False.
    """
    try:
        referer = request.headers["Referer"]
        logging.info("############# Referer = " + referer + "###############")
    except KeyError:
        return False    
    if re.search(r".*apps\.facebook\.com.*", referer): # match a Facebook apps uri
        logging.info("############### facebook.com detected! ###############")
        return True
    else:
        return False

def getFBUser(fb_id=None):
    """Returns a User for the given fb_id.
    """
    logging.info("################ getFBUser("+fb_id+") ####################")
    user_query = models.User.all().filter('fb_id =', fb_id)
    user = user_query.get() # this is the profiled User
    return user

def main():
    util.run_wsgi_app(webapp.WSGIApplication([(r'/', BaseHandler),
                                              (r'/user/(.*)', UserProfile),
                                              (r'/category/(.*)', CategoryProfile),  
                                              (r'/location/(.*)', LocationProfile)],
                                              debug=DEBUG))
##############################################################################
if __name__ == "__main__":
    main()
