# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base, re
from google.appengine.ext import ndb

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class SubjectsHandler(base.BaseHandler):
    def get(self, action, idSub):
        self.checkLogin()
        values = self.getValues()

        if idSub != "":
            sub = db.Subject.get_by_id(long(idSub))
            teacher = db.Teacher.getByEmail(self.getEmail())

            if teacher is not None and not sub.containsTeacher(teacher.key):
                self.redirect("/")

        if not action:  # index
            #self.response.write(db.Subject.paginate())

            #self.response.write(db.Subject.query(db.Subject.teachers == teacher.key).fetch())

            #for i in db.Subject.query(db.Subject.teachers == teacher.key).fetch():
                #self.response.write(i.name + "<br>")
            #return
            #data = db.paginateArray(db.Subject.getSubjectsByTeacher(teacher.key))
            #data["subjects"] = data.pop("objects")
            #values.update(data)
            #n = self.request.get("n", None)

            teacher = db.Teacher.getByEmail(self.getEmail())
            template = JINJA_ENVIRONMENT.get_template('view/subjects/index.html')
        elif action == "view":
            values["sub"] = sub
            #values["students"] = sub.getStudents()
            values["teachers"] = sub.getTeachers()
            values["tasks"] = sub.getTasks()
            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')
        elif action == "test":  # Only for testing purposes
            """try:
                offset = int(self.request.get("offset"))
            except ValueError:
                offset = 0

            students, cursor, more = db.Student.query().order(db.Student.name).fetch_page(10, offset)
            self.response.write(offset)"""
            task = db.Task.get_by_id(long(self.request.get("id")))

            if task:
                task.key.delete()
            else:
                self.response.write("vacio")

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
            teacherKey = db.Teacher.addOrUpdate(self.getEmail())

            # Subject data
            name = self.request.get("name")
            desc = self.request.get("description")

            subKey = db.Subject.addOrUpdate(name, desc, 2012, [teacherKey])

            # Go throught all the tasks of the subject
            i = 0

            for task in filter(lambda x: re.match('task[[0-9]*].name', x), list(self.request.POST)):
                id = task[5:task.find(']')]
                taskName = self.request.get(task)
                taskPercent = self.request.get("task[%s].percent" % id)

                db.Task.addOrUpdate(subKey, taskName, int(taskPercent))

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
        elif action == "removeteacher" and idSub != "":  # ajax
            # Get params data
            teacherId = self.request.get("teacherId")
            teacher = db.Teacher.get_by_id(long(teacherId))

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            if teacher is not None and sub is not None:
                sub.removeTeacher(teacher.key)
                self.response.write("1")
            else:
                self.response.write("0")
        elif action == "removestudent" and idSub != "":  # ajax
            # Get params data
            studentId = self.request.get("studentId")
            student = db.Student.get_by_id(long(studentId))

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            if student is not None and sub is not None:
                sub.removeStudent(student.key)
                self.response.write("1")
            else:
                self.response.write("0")
        elif action == "removetask" and idSub != "":  # ajax
            # Get params data
            taskId = self.request.get("taskId")
            task = db.Task.get_by_id(long(taskId))

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            if task is not None and sub is not None:
                sub.removeTask(task.key)
                self.response.write("1")
            else:
                self.response.write("0")
        elif action == "remove" and idSub != "":
            db.Subject.removeById(long(idSub))
            self.redirect("/")
            return
        self.redirect("/subjects/view/" + idSub)

class SearchHandler(base.BaseHandler):
    def get(self):
        self.checkLogin()

        query = db.Subject.query()
        page = self.request.get("p", None)
        clicked = self.request.get("c", None)
        data = {}

        if not page and not clicked:
            data = db.paginate(query, db.Subject.key)
        elif clicked == "next":
            data = db.paginate(query, db.Subject.key, None, page)
        elif clicked == "prev":
            data = db.paginate(query, db.Subject.key, page, None)

        resp = ""

        # Add the rows info
        for subject in data["objects"]:
            resp += "<tr data-id=\"%s\" class=\"with-pointer\" onclick=\"window.document.location = '/subjects/view/%s'\">" % (subject.key.id(),subject.key.id())
            resp += "<td>%s</td>" % subject.name
            resp += "<td>%s</td>" % len(subject.students)
            resp += "<td><img src=\"/img/delete.png\" class=\"img-icon icon-delete\" /></td></tr>"

        # Add the buttons info in a new line
        resp += "\n"
        if data["hasPrev"]:
            resp += "<button class=\"btn btn-default\" id=\"prevPage\" data-id=\"%s\">Previous</button>" % data["prevStr"]
        if data["hasNext"]:
            resp += "<button class=\"btn btn-default\" id=\"nextPage\" data-id=\"%s\">Next</button>" % data["nextStr"]

        self.response.write(resp)


app = webapp2.WSGIApplication([
    ('/subjects/search', SearchHandler),
    ('/subjects/?([a-z]*)/?([0-9]*)', SubjectsHandler)
], debug=True)
