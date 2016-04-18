# -*- coding: utf-8 -*-

import webapp2, db
from google.appengine.api import users


class BaseHandler(webapp2.RequestHandler):

    def loggedIn(self):
        user = users.get_current_user()
        return user is not None

    def getUserName(self):
        user = self.getEmail()
        if user.find("@") <> -1:
            user = user.split("@")[0]
        return user

    def getEmail(self):
        return users.get_current_user().email()

    def getUserId(self):
        email = self.getEmail()
        teacher = db.Teacher.getByEmail(email)
        return teacher.key.id() if teacher else None

    def getValues(self):

        return {"logoutUrl": users.create_logout_url("/"),
                "username": self.getUserName(),
                "userid": self.getUserId()}



app = webapp2.WSGIApplication([
    ('/', BaseHandler)
], debug=True)
