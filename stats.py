# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class StatsHandler(base.BaseHandler):
    def get(self):
        self.checkLogin()
        values = self.getValues()

        template = JINJA_ENVIRONMENT.get_template('/view/stats/index.html')
        self.response.write(template.render(values))

app = webapp2.WSGIApplication([
    ('/stats', StatsHandler)
], debug=True)
