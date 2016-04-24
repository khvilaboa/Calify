# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base
from webapp2_extras import i18n

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'],
    autoescape=True)

JINJA_ENVIRONMENT.install_gettext_translations(i18n)

class StatsHandler(base.BaseHandler):
    def get(self, teachId):
        if not self.loggedIn():
            self.redirect("/")
            return
        values = self.getValues()
        locale = self.request.GET.get('locale', 'es_ES')
        i18n.get_i18n().set_locale(locale)

        teacher = db.Teacher.get_by_id(long(teachId))

        if not teachId or not teacher:
            self.redirect("/")
        else:

            own = teachId == str(self.getUserId())
            values["own"] = own
            values["teacher"] = teacher
            values["subjects"] = ", ".join([s.name for s in db.Subject.getSubjectsByTeacher(teacher.key)])

            template = JINJA_ENVIRONMENT.get_template('/view/profile/index.html')
            self.response.write(template.render(values))

    def post(self):
        if not self.loggedIn():
            self.redirect("/")
            return

        # Modify teacher
        teacher = db.Teacher.getByEmail(self.getEmail())
        teacher.name = self.request.get("name")
        teacher.put()

        self.redirect("/profile/%s" % teacher.key.id())

app = webapp2.WSGIApplication([
    ('/profile/?([0-9]*)', StatsHandler),
    ('/profile/modify', StatsHandler)
], debug=True)
