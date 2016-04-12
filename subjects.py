# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base, re
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4

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
            template = JINJA_ENVIRONMENT.get_template('view/subjects/index.html')
        elif action == "pdf":
            self.response.headers['Content-Type'] = 'application/pdf'
            self.response.headers['Content-Disposition'] = 'attachment; filename=my.pdf'
            c = canvas.Canvas(self.response.out, pagesize=A4)

            c.drawString(100, 100, "Hello world")
            c.showPage()
            c.save()
            return
        elif action == "view":
            values["sub"] = sub
            values["teachers"] = sub.getTeachers()
            values["tasks"] = sub.getTasks()
            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')

        elif action == "create":
            template = JINJA_ENVIRONMENT.get_template('view/subjects/create.html')

        elif action == "modify" and idSub != "":
            values["subject"] = db.Subject.get_by_id(long(idSub))
            values["tasks"] = values["subject"].getTasks()
            template = JINJA_ENVIRONMENT.get_template('view/subjects/create.html')
        else:
            self.redirect("/")
            return

        self.response.write(template.render(values))

    def post(self, action, idSub):
        self.checkLogin()

        if action == "create" and idSub == "": # Create subject
            # Teacher data
            teacherKey = db.Teacher.addOrUpdate(self.getEmail())

            # Subject data
            name = self.request.get("name")
            desc = self.request.get("description")

            subKey = db.Subject.addOrUpdate(name, desc, 2012, [teacherKey])

            # Go throught all the tasks of the subject
            for task in filter(lambda x: re.match('task[[0-9]*].name', x), list(self.request.POST)):
                id = task[5:task.find(']')]
                taskName = self.request.get(task)
                taskPercent = self.request.get("task[%s].percent" % id)

                db.Task.addOrUpdate(subKey, taskName, int(taskPercent))

            idSub = str(subKey.id())

        elif action == "modify" and idSub != "":  # Modify existing subject
            sub = db.Subject.get_by_id(long(idSub))

            if not sub:
                self.redirect("/")

            tasks = {}
            for t in sub.getTasks().fetch():
                tasks[t.name] = t.key

            self.response.write(tasks)
            self.response.write("<br>")

            # Go throught all the tasks of the subject
            for task in filter(lambda x: re.match('task[[0-9]*].name', x), list(self.request.POST)):
                id = task[5:task.find(']')]
                taskName = self.request.get(task)
                taskPercent = self.request.get("task[%s].percent" % id)

                self.response.write("%s <> %s<br>" % (taskName, taskPercent))

                if taskName in tasks:
                    taskKey = tasks[taskName]
                    self.response.write("was: ")
                    self.response.write(taskKey)
                    self.response.write("<br>")
                    db.Task.addOrUpdate(sub.key, taskName, taskPercent, taskKey)
                    del tasks[taskName]
                else:
                    db.Task.addOrUpdate(sub.key, taskName, taskPercent)
                    self.response.write("create<br>")

            for task in tasks:
                taskKey = tasks[task]
                taskKey.delete()
                self.response.write(task)
                self.response.write("<br>remove")



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

        teacher = db.Teacher.getByEmail(self.getEmail())
        query = db.Subject.getSubjectsByTeacher(teacher.key)
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
