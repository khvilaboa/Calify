# -*- coding: utf-8 -*-

import webapp2
from google.appengine.api import users


class BaseHandler(webapp2.RequestHandler):

    def checkLogin(self):
        user = users.get_current_user()
        if not user:
            self.redirect("/")

    def getUserName(self):
        user = self.getEmail()
        if user.find("@") <> -1:
            user = user.split("@")[0]
        return user

    def getEmail(self):
        self.checkLogin()
        return users.get_current_user().email()

    def getValues(self):
        return {"logoutUrl": users.create_logout_url("/"),
                "username": self.getUserName()}



app = webapp2.WSGIApplication([
    ('/', BaseHandler)
], debug=True)
