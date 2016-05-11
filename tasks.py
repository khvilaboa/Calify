# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base
from webapp2_extras import i18n, sessions

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'],
    autoescape=True)

JINJA_ENVIRONMENT.install_gettext_translations(i18n)


class TasksHandler(base.BaseHandler):
    def get(self, action, idTask, idSt):
        if not self.loggedIn():
            self.redirect("/")
            return
        values = self.getValues()
        i18n.get_i18n().set_locale(self.getLanguage())

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

            if self.session.get('correctLines', None) != None:  # File load results
                values["correct"] = self.session.pop('correctLines', None)
                values["incorrect"] = self.session.pop('incorrectLines', None)
                values["incorrect_lines"] = self.session.pop('incorrectLinesData', None)

            template = JINJA_ENVIRONMENT.get_template('view/tasks/calify.html')
        elif action == "addmark":  # Called by ajax requests
            task = db.Task.get_by_id(long(idTask))
            sub = task.subject.get()
            student = db.Student.get_by_id(long(idSt))
            mark = float(self.request.get("mark"))

            db.Mark.addOrUpdate(student.key, task.key, mark)  # TODO: check if mark it's updated correctly
            if student.key in sub.promoteds:
                sub.removePromoted(student.key)
            return
        else:
            self.redirect("/")
            return

        self.response.write(template.render(values))

    def dispatch(self):
        # Get a session store for this request.
        self.session_store = sessions.get_store(request=self.request)

        try:
            # Dispatch the request.
            webapp2.RequestHandler.dispatch(self)
        finally:
            # Save all sessions.
            self.session_store.save_sessions(self.response)

    @webapp2.cached_property
    def session(self):
        # Returns a session using the default cookie key.
        return self.session_store.get_session()

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': '5680fd16956dd8ef2290e4c029e6e841',
}

app = webapp2.WSGIApplication([
    ('/tasks/?([a-z]*)/?([0-9]*)/?([0-9]*)', TasksHandler)
], debug=True, config=config)
