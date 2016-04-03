# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class StatsHandler(base.BaseHandler):
    def get(self, subId):
        self.checkLogin()
        values = self.getValues()

        if not subId:
            teacher = db.Teacher.getByEmail(self.getEmail())
            subjects = db.Subject.getSubjectsByTeacher(teacher.key)
            values["subjects"] = "[" + ",".join(['"' + sub.name + '"' for sub in subjects]) + "]"
            values["studentsBySubject"] = "[" + ",".join(['"' + str(len(sub.students)) + '"' for sub in subjects]) + "]"
            #self.response.write()

            template = JINJA_ENVIRONMENT.get_template('/view/stats/index.html')
        self.response.write(template.render(values))

app = webapp2.WSGIApplication([
    ('/stats/?([a-z]*)', StatsHandler)
], debug=True)
