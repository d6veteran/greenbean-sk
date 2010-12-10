# Placeholder of new datastore models

from google.appengine.ext import db

class User(db.Model):
	name = db.StringProperty(required=True)
	profile_url = db.StringProperty(required=True)
	fb_access_token = db.StringProperty(required=True)
	fb_id = db.StringProperty(required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	updated = db.DateTimeProperty(auto_now=True)

class Brag(db.Model):
	text = db.StringProperty(required=True)
	create_date = db.DateTimeProperty(auto_now_add=True)
	category = db.ReferenceProperty(Category, required=True)
	user = db.ReferenceProperty(User, required=True)
	location = db.ReferenceProperty(Location, required=True)
	origin = db.StringProperty(required=True)
	
class Bean(db.Model):
	brag = db.ReferenceProperty(Brag, require=True)	
	user = db.ReferenceProperty(User, required=True)
	created = db.DateTimeProperty(auto_now_add=True)
	
class BragBeans(db.Model):
	brag = db.ReferenceProperty(Brag, require=True)	
	bean_count = db.IntegerProperty(required=True)
	updated = db.DateTimeProperty(auto_now=True)

class UserBeans(db.Model):
	user = db.ReferenceProperty(User, required=True)
	bean_count = db.IntegerProperty(required=True)
	updated = db.DateTimeProperty(auto_now=True)

class CategoryBeans(db.Model):
	category = db.ReferenceProperty(Category, required=True)
	bean_count = db.IntegerProperty(required=True)
	updated = db.DateTimeProperty(auto_now=True)

class LocationBeans(db.Model):
	location = db.ReferenceProperty(Location, required=True)
	bean_count = db.IntegerProperty(required=True)
	updated = db.DateTimeProperty(auto_now=True)
		
class Category(db.Model):
	name = db.ReferenceProperty(required=True)
	
class Location(db.Model):
	city = db.StringProperty(required=True)
	state = db.StringProperty(required=True)
	country = db.StringProperty(required=True)		