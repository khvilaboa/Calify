#!/usr/bin/env python

import webapp2, jinja2, os, db, base

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class SubjectsHandler(base.BaseHandler):
    def get(self, action, idSub):
        self.checkLogin()
        values = self.getValues()

        """if action == "dbfill":
            est = db.Subject(name="EST", description="asdf", year=2012)
            est.put()
            task = db.Task(parent=est.key, name="Examen parcial 1", percent=80)
            task.put()
            task = db.Task(parent=est.key, name="Examen parcial 2", percent=20)
            task.put()"""

        if not action:  # index
            values["subjects"] = db.Subject.query()
            template = JINJA_ENVIRONMENT.get_template('view/subjects/index.html')
        elif action == "view":
            values["sub"] = db.Subject.get_by_id(long(idSub))
            values["students"] = [ db.Student.get_by_id(stKey.id()) for stKey in values["sub"].students ]
            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')
        elif action == "delete":
            self.response.write("toca borrar la asignatura con id " + idSub)
            db.Subject.deleteById(long(idSub))
            self.redirect("/")
            return
        elif action == "test":  # Only for testing purposes
            # New teacher
            if not db.Teacher.exists(self.getEmail()):
                teacher = db.Teacher(email=self.getEmail(), subjects=[])
                teacher.put()
                self.response.write("creating...")

            return
        elif action == "testdos":  # Only for testing purposes

            """if db.Teacher.exists(self.getEmail()):
                self.response.write("existe: " + self.getEmail())
            else:
                self.response.write("no existe")
            return"""

            teacherKey = db.Teacher.getByEmail(self.getEmail())
            if teacherKey == None:
                teacher = db.Teacher(email=self.getEmail())
                teacherKey = teacher.put()
                self.response.write("creating...")
                self.response.write(teacherKey)
                return
            else:
                self.response.write(teacherKey.key)
                return
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

    def post(self, action, idSub):
        self.checkLogin()

        if action == "create" and idSub == "":
            # Teacher data
            teacherKey = db.Teacher.getByEmail(self.getEmail())
            if teacherKey <> None:
                teacherKey = teacherKey.key
            else:
                teacher = db.Teacher(email=self.getEmail())
                teacherKey = teacher.put()


            # Subject data
            name = self.request.get("name")
            desc = self.request.get("description")

            sub = db.Subject(name=name, description=desc, year=2012, teachers=[teacherKey], students=[])
            sub.put()

            self.response.write("Name: " + name)
            self.response.write("<br>Description: " + desc)
            self.response.write("<br>Tasks:<br>")

            i = 0
            taskName = self.request.get("task[%d].name" % i, "")
            taskPercent = self.request.get("task[%d].percent" % i, "")  # TODO: check types

            while taskName != "" and taskPercent != "":
                task = db.Task(parent=sub.key, name=taskName, percent=int(taskPercent))
                task.put()
                self.response.write(taskName + "<br>" + str(taskPercent) + "<br>")
                i += 1
                taskName = self.request.get("task[%d].name" % i, "")
                taskPercent = self.request.get("task[%d].percent" % i, "")

        elif action == "addstudents" and idSub != "":
            opt = self.request.get("optAddStudents")
            if opt == "manual":
                self.response.write("manual... " + idSub + "<br>")
                # Get params data
                dni = self.request.get("dni")
                name = self.request.get("name")
                self.response.write(dni + ", " + name + "<br>")

                # Get the subject from the datastore
                sub = db.Subject.get_by_id(long(idSub))

                # Get student from the datastore (create it if not exist)
                st = db.Student.getByDni(dni)
                if st is None:
                    st = db.Student(dni=dni, name=name)
                    stKey = st.put()
                else:
                    stKey = st.key

                self.response.write(str(stKey) + "<br>")
                self.response.write(str(sub) + "<br>")

                if stKey not in sub.students:
                    sub.students.append(stKey)
                    sub.put()

            elif opt == "file":
                pass
            elif opt == "subject":
                pass

        self.redirect("/subjects/view/" + idSub)


app = webapp2.WSGIApplication([
    ('/subjects/?([a-z]*)/?([0-9]*)', SubjectsHandler)
], debug=True)
