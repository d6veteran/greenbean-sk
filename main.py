## APPSPOT.COM - UNCOMMENT FOR PRODUCTION ####################################
#FACEBOOK_APP_ID = "112884208756371"
#FACEBOOK_APP_SECRET = "9091225114bdb7017e6b3c23a09cfb38"
#SITE="Greenbean.me"
##############################################################################

## LOCALHOST:8080 - UNCOMMENT FOR LOCAL TESTING ##############################
FACEBOOK_APP_ID = "174331539272451"
FACEBOOK_APP_SECRET = "f4f8e3762a2abbe62dee8bf44a4967a4"
SITE="localhosttest-sk"
##############################################################################

CATS=["Reduse","Reuse","Recycle","Organic","Wind","Solar",
      "Walk","Bus","Bike","Local","Carpool"]

# local site: http://apps.facebook.com/mymicrodonations/
DEBUG = True

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
        template.register_template_library('templatefilters')
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, 
                            os.path.join('templates', template_name))
                            
        self.response.out.write(template.render(path, 
                                                template_values, 
                                                debug=DEBUG))

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
        brags = brag_query.fetch(10)
        if facebookRequest(self.request):
            template = "facebook/fb_base_user_profile.html"
            
        else:    
            template = "base_user_profile.html"
        
        self.generate(template, {
                      'brags': brags,
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

class Bean(MainHandler):
    """Updates bean count for a Brag and associated Categories, Users and
    Locations.
    """
    def post(self):    
        logging.info('################ Bean::post ################') 
        brag_key = self.request.get('brag') 
        voter_fb_id = self.request.get('voter')
        user = self.current_user
        logging.info('################ brag_key =' + brag_key + '###########') 
        logging.info('################ voter_fb_id =' + voter_fb_id + '#####') 
        logging.info('################ user.fb_id =' + user.fb_id + '#######')         
        # Update Brag
        brag = models.Brag.get(brag_key)
        if brag is not None:
            if voter_fb_id not in brag.voter_keys:
                # This is a valid vote, so start updating Entities 
                # Update the Brag ...
                brag.voter_keys.append(voter_fb_id)
                brag.beans += 1
                brag.put()
                # Update the BragBean
                user_beans = models.UserBeans.get_by_key_name(user.fb_id)
                if user_beans is not None:
                    user_beans.beans += 1
                else:
                    user_beans = models.UserBeans(user = user,
                                                  key_name = user.fb_id,
                                                  beans = 1)
                                                  
                user_beans.put()    
                # Update the CategoryBeans  
                for c in brag.categories:
                    cat_beans = models.CategoryBeans.get_by_key_name(c)
                    if cat_beans is not None:
                        cat_beans.beans += 1
                    else:
                        cat_beans = models.CategoryBeans(key_name = c,
                                                         category = c,    
                                                         beans = 1)
                    cat_beans.put()
  
        return


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
                                              (r'/location/(.*)', LocationProfile),
                                              ('/bean', Bean)],
                                              debug=DEBUG))
##############################################################################
if __name__ == "__main__":
    main()
