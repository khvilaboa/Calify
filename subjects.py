# -*- coding: utf-8 -*-
#!/usr/bin/env python

import webapp2, jinja2, os, db, base, re, time
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from webapp2_extras import i18n

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'],
    autoescape=True)

JINJA_ENVIRONMENT.install_gettext_translations(i18n)

class SubjectsHandler(base.BaseHandler):
    def get(self, action, idSub):
        if not self.loggedIn():
            self.redirect("/")
            return
        if not db.Teacher.exists(self.getEmail()):  # If the user doesn't exist in the BD (first log in) add it
            db.Teacher.addOrUpdate(self.getEmail())

        values = self.getValues()
        locale = self.request.GET.get('locale', 'es_ES')
        i18n.get_i18n().set_locale(locale)

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
            values["tasks"] = sub.getTasks().order(db.Task.order)
            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')

        elif action == "create":
            template = JINJA_ENVIRONMENT.get_template('view/subjects/create.html')

        elif action == "modify" and idSub != "":
            values["subject"] = db.Subject.get_by_id(long(idSub))
            values["tasks"] = values["subject"].getTasks().order(db.Task.order)
            template = JINJA_ENVIRONMENT.get_template('view/subjects/create.html')
        elif action == "export" and idSub != "":
            self.response.headers['Content-Type'] = 'text/csv'
            filename = self.getUserName() + "_" + str(time.time()).replace(".", "") + ".csv"
            self.response.headers['Content-Disposition'] = 'attachment; filename=' + filename

            sub = db.Subject.get_by_id(long(idSub))
            tasksInfo = sub.getTasks()
            tasksMarks = {task.key: {m.student: m.mark for m in task.getMarks()} for task in sub.getTasks()}
            students = sub.getStudents()

            """self.response.write(tasksMarks)
            self.response.write("<br><br>")
            self.response.write(self.getUserName() + "_" + str(time.time()).replace(".","") + ".csv")
            self.response.write("<br><br>")"""

            fileContent = ""
            for st in students:
                #self.response.write(st.name + "<br>")
                weightedAvg = 0
                extraPoints = 0
                for task in tasksInfo:
                    rawMark = tasksMarks[task.key].get(st.key, None)
                    if not rawMark or task.informative:
                        continue
                    elif task.extra:
                        extraPoints += rawMark
                        continue
                    mark = (rawMark / task.maxmark) * 10 * (task.percent/100.0)
                    weightedAvg += mark
                    """self.response.write(task.name + " (" + str(task.percent) + "%, " + str(task.maxmark) + "): ")
                    self.response.write("%s, %s, %s" % (rawMark, rawMark / task.maxmark * 10, mark))
                    self.response.write("<br>")"""
                """self.response.write("Final mark: %s<br>" % weightedAvg)
                self.response.write("Extra: %s<br>" % extraPoints)
                self.response.write("Final mark with extra: %s<br><br>" % (weightedAvg+extraPoints))"""
                fileContent += "%s;%s\n" % (st.dni, weightedAvg+extraPoints)
            self.response.write(fileContent)
            return
        else:
            self.redirect("/")
            return

        self.response.write(template.render(values))

    def post(self, action, idSub):
        if not self.loggedIn():
            self.redirect("/")
            return

        if action == "create" and idSub == "":  # Create subject
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
                taskMaxMark = self.request.get("task[%s].maxmark" % id)
                taskInformative = self.request.get("task[%s].informative" % id)
                taskExtra = self.request.get("task[%s].extra" % id)

                db.Task.addOrUpdate(subKey, taskName, int(taskPercent), int(id), int(taskMaxMark), taskInformative == "true", taskExtra == "true")

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
                taskMaxMark = self.request.get("task[%s].maxmark" % id)
                taskInformative = self.request.get("task[%s].informative" % id)
                taskExtra = self.request.get("task[%s].extra" % id)

                self.response.write("%s <> %s<br>" % (taskName, taskPercent))

                if taskName in tasks:
                    taskKey = tasks[taskName]
                    self.response.write("was: ")
                    self.response.write(taskKey)
                    self.response.write("<br>")
                    db.Task.addOrUpdate(sub.key, taskName, int(taskPercent), int(id), int(taskMaxMark), taskInformative == "true", taskExtra == "true", taskKey)
                    del tasks[taskName]
                else:
                    db.Task.addOrUpdate(sub.key, taskName, int(taskPercent), int(id), int(taskMaxMark), taskInformative == "true", taskExtra == "true")
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
                lines = self.request.POST["filename"].value.split("\r\n")

                filename = self.request.POST["filename"].filename

                if filename.endswith(".csv"):
                    # Get the subject from the datastore
                    sub = db.Subject.get_by_id(long(idSub))

                    # Parse CSV
                    header = lines[0].decode('utf-8').lower().split(separator)

                    nameInd = header.index("nombre")
                    dniInd = header.index("dni")

                    for line in lines[1:]:
                        fields = line.decode('utf-8').split(separator)
                        name = fields[nameInd]
                        dni = fields[dniInd]
                        self.response.write(fields[nameInd] + ", " + fields[dniInd] + "<br>")

                        # Get student from the datastore (create it if not exist)
                        stKey = db.Student.addOrUpdate(dni, name)

                        # Add the student to the subject
                        if stKey not in sub.students:
                            sub.addStudent(stKey)
                elif filename.endswith(".xls"):
                    sub = db.Subject.get_by_id(long(idSub))
                    buff = []
                    for l in lines:
                        if re.match("\<tr ", l):
                            buff = []
                        elif re.match("\<font", l):
                            buff.append(re.sub("\<.*\>", "", re.sub("\</.*.>", "", l)))
                        elif re.match("\</tr\>", l) and len(buff) > 1:
                            self.response.write(buff[0] + ", " + buff[1] + "<br>")
                            stKey = db.Student.addOrUpdate(buff[0], buff[1])
                            if stKey not in sub.students:
                                sub.addStudent(stKey)
                            buff = []

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
        if not self.loggedIn():
            self.redirect("/")
            return

        teacher = db.Teacher.getByEmail(self.getEmail())
        query = db.Subject.getSubjectsByTeacher(teacher.key)
        off = self.request.get("o", None)
        data = {}

        # Paginate the query (beginning after a offset if it's specified)
        data = db.paginateOff(query, db.Student.key, int(off) if off else 0)

        resp = ""
        for subject in data["objects"]:
            resp += "%s^^%s^^%s\n" % (subject.key.id(), subject.name, len(subject.students))  # Data to be formatted in the JS code

        if len(data["objects"]):
            # Add the buttons info (new offsets)
            resp += "\n%d\n%d" % (data["prevOffset"], data["nextOffset"])

            # Add the nearest pages info
            lenQuery = query.count()  #len(query.fetch())
            maxPage = max(0, 8*((lenQuery - 1)//8))
            curPage = data["curOffset"]
            leftPage = max(0, curPage-2*db.ITEMS_PER_PAGE)
            rightPage = min(curPage+2*db.ITEMS_PER_PAGE, maxPage)
            resp += "\n\n%d\n%d\n%d\n%d" % (leftPage, rightPage, curPage, db.ITEMS_PER_PAGE)

        self.response.write(resp)


app = webapp2.WSGIApplication([
    ('/subjects/search', SearchHandler),
    ('/subjects/?([a-z]*)/?([0-9]*)', SubjectsHandler)
], debug=True)
