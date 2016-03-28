# -*- coding: utf-8 -*-
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
            values["students"] = [ stKey.get() for stKey in values["sub"].students ]
            values["teachers"] = [ tKey.get() for tKey in values["sub"].teachers ]
            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')
        elif action == "delete":
            self.response.write("toca borrar la asignatura con id " + idSub)
            db.Subject.deleteById(long(idSub))
            self.redirect("/")
            return
        elif action == "test":  # Only for testing purposes
            try:
                offset = int(self.request.get("offset"))
            except ValueError:
                offset = 0

            students, cursor, more = db.Student.query().order(db.Student.name).fetch_page(10, offset)
            self.response.write(offset)

            return
        elif action == "testdos":  # Only for testing purposes

            """if db.Teacher.exists(self.getEmail()):
                self.response.write("existe: " + self.getEmail())
            else:
                self.response.write("no existe")
            return"""

            """teacherKey = db.Teacher.getByEmail(self.getEmail())
            if teacherKey == None:
                teacher = db.Teacher(email=self.getEmail())
                teacherKey = teacher.put()
                self.response.write("creating...")
                self.response.write(teacherKey)
                return
            else:
                self.response.write(teacherKey.key)
                return"""
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
            teacherKey = db.Teacher.addOrUpdate(self.getEmail())

            # Subject data
            name = self.request.get("name")
            desc = self.request.get("description")

            subKey = db.Subject.addOrUpdate(name, desc, 2012, [teacherKey])

            # Go throught all the tasks of the subject
            i = 0
            taskName = self.request.get("task[%d].name" % i, "")
            taskPercent = self.request.get("task[%d].percent" % i, "")  # TODO: check types

            while taskName != "" and taskPercent != "":
                db.Task.addOrUpdate(subKey, taskName, int(taskPercent))

                i += 1
                taskName = self.request.get("task[%d].name" % i, "")
                taskPercent = self.request.get("task[%d].percent" % i, "")

            idSub = str(subKey.id())
        elif action == "addstudents" and idSub != "":
            opt = self.request.get("optAddStudents")
            if opt == "manual":
                # Get params data
                dni = self.request.get("dni")
                name = self.request.get("name")

                # Get the subject from the datastore
                sub = db.Subject.get_by_id(long(idSub))

                # Get student from the datastore (create it if not exist)
                stKey = db.Student.addOrUpdate(dni, name)

                # Add the student to the subject
                if stKey not in sub.students:
                    sub.addStudent(stKey)

            elif opt == "file":
                # Get params data
                filename = self.request.get("filename")
                separator = self.request.get("separator")
                csvLines = self.request.POST["filename"].value.split("\r\n")

                # Get the subject from the datastore
                sub = db.Subject.get_by_id(long(idSub))

                # Parse CSV
                header = csvLines[0].decode('utf-8').lower().split(separator)

                nameInd = header.index("nombre")
                dniInd = header.index("dni")

                for line in csvLines[1:]:
                    fields = line.decode('utf-8').split(separator)
                    name = fields[nameInd]
                    dni = fields[dniInd]
                    self.response.write(fields[nameInd] + ", " + fields[dniInd] + "<br>")

                    # Get student from the datastore (create it if not exist)
                    stKey = db.Student.addOrUpdate(dni, name)

                    # Add the student to the subject
                    if stKey not in sub.students:
                        sub.addStudent(stKey)

            elif opt == "subject":
                pass
        elif action == "addteacher" and idSub != "":
            # Get params data
            email = self.request.get("teacherEmail")

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            # Add the teacher if they don't exist
            tKey = db.Teacher.addOrUpdate(email)

            sub.addTeacher(tKey)


        self.redirect("/subjects/view/" + idSub)


app = webapp2.WSGIApplication([
    ('/subjects/?([a-z]*)/?([0-9]*)', SubjectsHandler)
], debug=True)
