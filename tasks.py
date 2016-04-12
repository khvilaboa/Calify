# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class TasksHandler(base.BaseHandler):
    def get(self, action, idTask, idSt):
        self.checkLogin()
        values = self.getValues()

        if action == "calify":
            # Get task and subject entities
            task = db.Task.get_by_id(long(idTask))
            sub = task.subject.get()

            # Recover marks of the task
            marks = {}
            for mark in task.getMarks():
                marks[mark.student.id()] = mark.mark

            students = sub.getStudents()
            try:
                students = [(student, marks.get(student.key.id(), -1)) for student in students]
            except Exception:  # BadQueryError
                students = []

            values["task"] = task
            values["subject"] = sub
            values["students"] = students# sub.getStudents()

            template = JINJA_ENVIRONMENT.get_template('view/tasks/calify.html')
        elif action == "addnote": # Called by ajax requests
            task = db.Task.get_by_id(long(idTask))
            student = db.Student.get_by_id(long(idSt))
            mark = float(self.request.get("mark"))

            db.Mark.addOrUpdate(student.key, task.key, mark)  # TODO: check if mark it's updated correctly
            return
        else:
            self.redirect("/")
            return

        self.response.write(template.render(values))



app = webapp2.WSGIApplication([
    ('/tasks/?([a-z]*)/?([0-9]*)/?([0-9]*)', TasksHandler)
], debug=True)
