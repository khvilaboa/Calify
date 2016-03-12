#!/usr/bin/env python

import webapp2, jinja2, os


JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class SubjectsHandler(webapp2.RequestHandler):
    def get(self, action = "index"):

    	if not action: # index
    		template = JINJA_ENVIRONMENT.get_template('view/subjects/index.html')
        else:
        	template = JINJA_ENVIRONMENT.get_template('view/subjects/%s.html' % action)

        self.response.write(template.render())


app = webapp2.WSGIApplication([
    ('/subjects/?(.*)', SubjectsHandler)
], debug=True)

