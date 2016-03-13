#!/usr/bin/env python

import webapp2, jinja2, os, db
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class SubjectsHandler(webapp2.RequestHandler):
    def get(self, action, idSub):

        values = {}

        """if action == "dbfill":
            est = db.Subject(name="EST", description="asdf", year=2012)
            est.put()
            task = db.Task(parent=est.key, name="Examen parcial 1", percent=80)
            task.put()
            task = db.Task(parent=est.key, name="Examen parcial 2", percent=20)
            task.put()"""

        if not action:  # index
            subjects = db.Subject.query()
            values["subjects"] = subjects
            template = JINJA_ENVIRONMENT.get_template('view/subjects/index.html')
        elif action == "view":
            sub = db.Subject.get_by_id(long(idSub))
            values["tasks"] = sub.tasks()
            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')
        elif os.path.isfile('view/subjects/%s.html' % action):
            template = JINJA_ENVIRONMENT.get_template('view/subjects/%s.html' % action)
        else:
            self.redirect("/")
            return

        self.response.write(template.render(values))

        # subject = db.Subject(name = "EST", description = "aaaaaah!!!", year = 2015)
        # subject.put()


        """try:
            self.response.write("Tareas de una asignatura:<br>")
            for s in db.Task.query(ancestor=db.Subject.query().fetch()[0].key).fetch():
                self.response.write(s.name + "<br>")

            self.response.write("<br>porcentaje > 20%:<br>")
            for s in ndb.gql("SELECT * FROM Task WHERE percent > :1", 20):
                self.response.write(s.name)

            self.response.write("<br>porcentaje = 20%:<br>")
            for s in db.Task.query(db.Task.percent > 20).fetch():
                self.response.write(s.name)

            self.response.write("<br>prueba 2:<br>")
            for s in db.Task.query(db.Task.name == "Examen parcial 2"):
                self.response.write(s.name)

        except Exception as e:
            self.response.write("error: " + str(e))"""

        """task = db.Task(parent=est.key, name="Examen parcial 1", percent=80)
        task.put()
        task = db.Task(parent=est.key, name="Examen parcial 2", percent=20)
        task.put()"""


app = webapp2.WSGIApplication([
    ('/subjects/?([a-z]*)/?([0-9]*)', SubjectsHandler)
], debug=True)
