
"""Cool Beans base app"""

#Web enabled
#app name = sampyxisstockwatcher
FACEBOOK_APP_ID = "157819884231043"
FACEBOOK_APP_SECRET = "7142daa5ac2753ac6b06f70855830a9a"
#local
#app name - coolbeans-local
#FACEBOOK_APP_ID = "13641208923"
#FACEBOOK_APP_SECRET = "71e4b7fea11728cd8e0c022801b278b1"
SITE="gbsamtest"
#SITE="mymicrodonations"
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
    @property
    def current_user(self):
        #print(getID())
        #print(self)
        if not hasattr(self, "_current_user"):
            self._current_user = None
            cookie = facebook.get_user_from_cookie(
                self.request.cookies, FACEBOOK_APP_ID, FACEBOOK_APP_SECRET)
            #print(cookie)
            
            if cookie:
                #print("i have a cookie")
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
                
                # Get number of beans for this user
                # Put it in the user packet
                userB = db.GqlQuery("SELECT * FROM UserBeans WHERE user =:1", user.key())
                userB.fetch(1)
                for count in userB:
                    self._current_user.userBeans = count.bean_count
                    
                getToken(cookie["access_token"])
                getID(user.fb_id)
                #print(getID(user.fb_id))
                #print(user.fb_id)

                
        return self._current_user
    
    def generate(self, template_name, template_values={}):

        # Get a list of categories
        cat_query = models.Category.all()
        cats = cat_query.fetch(10)
        
        values = {
            'request': self.request,
            'user': self.current_user,
            'debug': self.request.get('deb'),
            'application_name': 'Green Bean',
            'categories': cats}
        values.update(template_values)
        directory = os.path.dirname(__file__)
        path = os.path.join(directory, os.path.join('templates', template_name))
        self.response.out.write(template.render(path, values, debug=_DEBUG))
    

class postStatus(BaseHandler):
    def post(self):

        #now post on the wall
        status_text = self.request.get('content')
        #print(FBUserID)
        #user = models.User.get_by_key_name(FBUserID)
        user = self.current_user
        #print(user.fb_id)
                
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
        #results  = facebook.GraphAPI(FBAccess_token).put_wall_post(message, attachment)
        #status_id = str(results['id'])
        status_id = 'This is for testing'
        
        
        #remove all this once categories work
        # Get the users category
        cat_names = self.request.get_all('cat_checks')
        
        # With the change in categories - may not need this
        #get the category keys for the reference
        #right now - puts the first one - we need to make cat_ref a list
        catKey = [] 
        for cat_name in cat_names:
        
            catKey.append( models.Category.get(cat_name).name)
            #print(catKey)
        
        
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
        
class UserPost(BaseHandler):
    #actually - I don't think we need this function anymore
    def get(self):
        status_id = self.request.get('userStatus')
        brag_query = models.Brag.all().order('-create_date')
        brag_query = brag_query.filter('status_id', status_id)
        #need to do paging?
        brags = brag_query.fetch(10)

        #now that we have the brags - need to get the categories for each
        self.generate('userStatus.html', {
                      'brags': brags,
                      'status_id':status_id,
                      'current_user':self.current_user,
                      'facebook_app_id':FACEBOOK_APP_ID})        

class User(BaseHandler):
    def get(self):
        user_id = self.request.get('user')
        user = models.User.get_by_key_name(user_id)
        brag_query = models.Brag.all().order('-create_date')
        brag_query = brag_query.filter('user', user)
        brags = brag_query.fetch(10)

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
                    
class voteBean(webapp.RequestHandler):
    # Need error checking
     def get(self):
        key = self.request.get('id')
        brag = models.Brag.get(key)
        user = models.User.get_by_key_name(FBUserID)

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

            #Now do the same for categories
            """
            for categories in brag.category:
                print(categories)
                
                #catBean = models.CategoryBeans.get_or_insert(categories, category=categories, bean_count=0)
                catQuery = db.GqlQuery("SELECT bean_count FROM CategoryBeans WHERE category =:1", categories)
                catQuery.fetch(1)
#                catQuery = models.CategoryBeans.all().filter("name", categories).fetch(1)
                print(catQuery)
                i = catQuery.bean_count
                if i == None:
                    i = 1
                catQuery.bean_count = i + 1
                catQuery.put()
             """   
            
            #Now do the same for location
        self.redirect('/')
        
class HomeHandler(BaseHandler):
    def get(self):

        brag_query = models.Brag.all().order('-create_date')
        brags = brag_query.fetch(10)
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


def main():
    util.run_wsgi_app(webapp.WSGIApplication([(r"/", HomeHandler),
                                              ('/sign', postStatus),
                                              ('/userPost', UserPost),
                                              ('/user', User),
                                              ('/vote', voteBean)],
                                              debug=True))


if __name__ == "__main__":
    main()
