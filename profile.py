# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class StatsHandler(base.BaseHandler):
    def get(self, teachId):
        self.checkLogin()
        values = self.getValues()

        teacher = db.Teacher.get_by_id(long(teachId))

        if not teachId or not teacher:
            self.redirect("/")
        else:
            values["teacher"] = teacher
            values["subjects"] = ", ".join([s.name for s in db.Subject.getSubjectsByTeacher(teacher.key)])

            template = JINJA_ENVIRONMENT.get_template('/view/profile/index.html')
            self.response.write(template.render(values))


app = webapp2.WSGIApplication([
    ('/profile/?([0-9]*)', StatsHandler)
], debug=True)
