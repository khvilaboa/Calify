#!/usr/bin/env python

import webapp2, jinja2, os


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class MainHandler(webapp2.RequestHandler):
    def get(self):
    	self.redirect("/subjects")


class SubjectsHandler(webapp2.RequestHandler):
    def get(self):
        template = JINJA_ENVIRONMENT.get_template('view/subjects.html')
        self.response.write(template.render())


app = webapp2.WSGIApplication([
    ('/', MainHandler),
    ('/subjects', SubjectsHandler)
], debug=True)

