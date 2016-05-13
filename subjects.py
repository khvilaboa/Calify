# -*- coding: utf-8 -*-
#!/usr/bin/env python

import webapp2, jinja2, os, db, base, re, time, sys, xlwt, StringIO, datetime
from webapp2_extras import i18n, sessions

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.i18n', 'jinja2.ext.autoescape'],
    autoescape=True)

JINJA_ENVIRONMENT.install_gettext_translations(i18n)


class SubjectsHandler(base.BaseHandler):

    class Parser:

        @staticmethod
        def exportCsvStudentsFile(sub):
            students = sub.getStudents().order(db.Student.dni)
            fileContent = ""

            for st in students:
                mark = sub.getStudentFinalMark(st.key, True)
                if mark is not None:
                    fileContent += "%s;%s\n" % (st.dni[:8], mark)

            return fileContent

        @staticmethod
        def exportXlsStudentsFile(sub):
            def getBaseXls(name, count):
                wb = xlwt.Workbook()
                ws = wb.add_sheet('Acta')
                ws.show_grid = False
                ws._cell_overwrite_ok = True

                texts = {(0, 3): u'Lista de Cualificacións',
                         (2, 1): u'Titulación: ',
                         (2, 3): name,
                         (3, 1): u'Curso: ',
                         (4, 1): u'Código: ',
                         (5, 1): u'Denominación: ',
                         (6, 1): u'Convocatoria: ',
                         (7, 1): u'Tipo de acta: ',
                         (8, 1): u'Alumnos en: ',
                         (10, 1): u'Orde',
                         (10, 2): u'DNI',
                         (10, 3): u'Apelidos e Nome',
                         (10, 4): u'C.P.C.',
                         (10, 5): u'Cualificacións',
                         (11, 5): u'Conceptual',
                         (11, 6): u'Numérica',
                         (12, 1): u'¡¡ Lea a folla de Axuda para consultala nova forma de cualificar establecida polo Real Decreto 1125/2003 !!'
                         }

                for i in range(8):
                    widths = (3, 14, 12, 30, 9, 10, 9, 3)
                    ws.col(i).width = 256 * widths[i]

                strDarkGray = 'font: height 160, name Arial, colour white, bold on; pattern: pattern solid, fore_colour gray40;'
                styleDarkGray = xlwt.easyxf(strDarkGray)
                styleDarkGrayR = xlwt.easyxf(strDarkGray + " align: horz right")
                styleDarkGrayY = xlwt.easyxf(strDarkGray.replace('colour white', 'colour yellow'))
                strLightGray = 'pattern: pattern solid, fore_colour gray25; font: colour black;' # borders: bottom thin, top thin, left thin, right thin
                styleLightGray = xlwt.easyxf(strLightGray)

                lastRow = 13 + count + 2
                for row in (0, 10, 11, 12, lastRow):
                    for col in range(8):
                        text = texts.get((row, col), '')
                        if row == 12:
                            style = styleDarkGrayY
                        elif row == 0 or row < 13:
                            style = styleDarkGray
                        else:
                            style = styleLightGray if lastRow % 2 == 1 else styleDarkGray
                        ws.write(row, col, text, style=style)

                for row in range(2, 8):
                    for col in range(1, 7):
                        style = styleDarkGrayR if col < 3 else styleLightGray
                        text = texts.get((row, col), '')
                        ws.write(row, col, text, style=style)

                return wb

            def writeXlsData(ws, row, col, val):
                strDarkGray = 'pattern: pattern solid, fore_colour gray40; align: horz center; font: height 160, name Arial, colour black'
                styleDarkGrayC = xlwt.easyxf(strDarkGray + (', bold: on' if row == 4 else ''))
                strLightGray = 'font: height 160, name Arial, colour black; pattern: pattern solid, fore_colour gray25; align: horz center'
                styleLightGrayC = xlwt.easyxf(strLightGray)

                style = (styleDarkGrayC, styleLightGrayC)[row % 2]
                ws.write(row, col, val, style=style)

            students = sub.getStudents().order(db.Student.dni)

            try:
                count = students.count()
            except Exception:
                count = 0

            xls = getBaseXls(sub.name, count)
            ws = xls.get_sheet(0)
            row = 13
            fileContent = ""

            for st in students:
                mark = sub.getStudentFinalMark(st.key, True)
                if mark is not None:
                    fileContent += "%s;%s\n" % (st.dni[:8], mark)

                writeXlsData(ws, row, 1, row - 12)
                writeXlsData(ws, row, 2, st.dni)
                writeXlsData(ws, row, 3, st.name)
                writeXlsData(ws, row, 4, 0)

                if mark is not None:
                    writeXlsData(ws, row, 5, 'MH' if st.hasHonorsInSubject(sub.key) else '')
                    writeXlsData(ws, row, 6, mark)
                else:
                    writeXlsData(ws, row, 5, 'NP')
                    writeXlsData(ws, row, 6, '')

                row += 1

            out = StringIO.StringIO()
            xls.save(out)
            return out.getvalue()

        @staticmethod
        def formatDni(dni):
            dni = dni.upper()
            letters = "TRWAGMYFPDXBNJZSQVHLCKE"

            if not re.match("[0-9XYZ][0-9]{7}[A-Z]?", dni):
                return None

            if 'X' <= dni[0] <= 'Z':
                eqDni = str(ord(dni[0]) - 88) + dni[1:]

                if len(eqDni) == 8:
                    return dni + letters[int(eqDni) % 23]
                elif letters[int(eqDni[:8]) % 23] == dni[8]:
                    return dni

            elif '0' <= dni[0] <= '9':
                if len(dni) == 8:
                    return dni + letters[int(dni) % 23]
                elif letters[int(dni[:8]) % 23] == dni[8]:
                    return dni

            return None

        @classmethod
        def importCsvStudentsFile(cls, fileContent, sub):
            lines = fileContent.split("\r\n")
            separators = (";", ":", "^")

            results = {"correct": 0, "incorrect": 0, "incorrect_lines": ""}

            # Parse CSV
            separator = None
            for sep in separators:
                if lines[0].find(sep):
                    separator = sep
                    break

            if len(lines) > 0:
                firstLine = lines[0].split(separator)
                dniInd = 0
                nameInd = 1

                try:
                    validDni = cls.formatDni(firstLine[dniInd])  # Could be header

                    if not validDni:
                        lines = lines[1:]
                except:
                    lines = lines[1:]

                for line in lines:
                    fields = line.split(separator)

                    dni = fields[dniInd]
                    name = fields[nameInd]

                    validDni = None
                    try:
                        validDni = cls.formatDni(fields[dniInd])
                    except:
                        results["incorrect"] += 1
                        results["incorrect_lines"] += "%s, %s (parse error)<br>" % (dni, name)

                    if validDni:
                        st = db.Student.getByDni(validDni)
                        if st is not None and st.key in sub.students:
                            results["incorrect"] += 1
                            results["incorrect_lines"] += "%s, %s (it already exists)<br>" % (dni, name)
                        else:
                            stKey = db.Student.addOrUpdate(dni, name)
                            if stKey not in sub.students:
                                sub.addStudent(stKey)
                            results["correct"] += 1
                    else:
                        results["incorrect"] += 1
                        results["incorrect_lines"] += "%s, %s (invalid dni)<br>" % (dni, name)

            return results

        @classmethod
        def importXlsStudentsFile(cls, fileContent, sub):
            lines = fileContent.split("\r\n")
            buff = []

            results = {"correct": 0, "incorrect": 0, "incorrect_lines": ""}
            for l in lines:
                if re.match("\<tr ", l):
                    buff = []
                elif re.match("\<font", l):
                    buff.append(re.sub("\<.*\>", "", re.sub("\</.*.>", "", l)))
                elif re.match("\</tr\>", l) and len(buff) > 1:

                    try:
                        validDni = cls.formatDni(buff[0])
                    except:
                        results["incorrect"] += 1
                        results["incorrect_lines"] += ",".join(buff) + " (parse error)<br>"

                    if validDni:
                        st = db.Student.getByDni(validDni)
                        if st is not None and st.key in sub.students:
                            results["incorrect"] += 1
                            results["incorrect_lines"] += ",".join(buff) + " (it already exists)<br>"
                        else:
                            stKey = db.Student.addOrUpdate(buff[0], buff[1])
                            if stKey not in sub.students:
                                sub.addStudent(stKey)
                            results["correct"] += 1
                    else:
                        results["incorrect"] += 1
                        results["incorrect_lines"] += ",".join(buff) + " (invalid dni)<br>"
                    buff = []

            return results


        @classmethod
        def importCsvMarksFile(cls, fileContent, task, sub):
            lines = fileContent.split("\r\n") if "\r\n" in fileContent else fileContent.split("\n")
            lines = map(lambda x: re.sub("\s+", " ", x).strip(), lines)

            results = {"correct": 0, "incorrect": 0, "incorrect_lines": ""}

            # Parse CSV
            separator = None
            for sep in (";", ":", ","):
                if lines[0].find(sep):
                    separator = sep
                    break

            if len(lines) > 0:
                firstLine = lines[0].split(separator)
                dniInd = 0
                markInd = 1

                try:
                    validDni = cls.formatDni(firstLine[dniInd])  # Could be header

                    if not validDni:
                        lines = lines[1:]
                except:
                    lines = lines[1:]

                for line in lines:
                    fields = line.split(separator)

                    dni = fields[dniInd]
                    mark = float(fields[markInd])  # check

                    validDni = None

                    try:
                        #self.response.write(">%s<<br>" % fields[dniInd])
                        validDni = cls.formatDni(fields[dniInd])
                        #self.response.write("correct<br>")
                    except:
                        #self.response.write("nope<br>")
                        results["incorrect"] += 1
                        results["incorrect_lines"] += "%s, %s (parse error)<br>" % (dni, mark)

                    if validDni:
                        st = db.Student.getByDni(validDni)
                        if st is not None and db.Mark.getByStudentAndTask(st.key, task.key) is not None:  # Update mark
                            results["correct"] += 1
                            #self.response.write("(U) %s -> %s<br>" % (dni, mark))
                            db.Mark.addOrUpdate(st.key, task.key, mark)
                        elif st is None or st is not None and st.key not in sub.students:
                            results["incorrect"] += 1
                            results["incorrect_lines"] += "%s, %s (student not belong to the subject)<br>" % (dni, mark)
                        elif mark == -1:
                            results["correct"] += 1
                        else:  # Create mark
                            results["correct"] += 1
                            #self.response.write("(C) %s -> %s<br>" % (dni, mark))
                            db.Mark.addOrUpdate(st.key, task.key, mark)
                    else:
                        results["incorrect"] += 1
                        results["incorrect_lines"] += "%s, %s (invalid dni)<br>" % (dni, mark)

            return results

    def get(self, action, idSub):
        if not self.loggedIn():
            self.redirect("/")
            return
        if not db.Teacher.exists(self.getEmail()):  # If the user doesn't exist in the BD (first log in) add it
            db.Teacher.addOrUpdate(self.getEmail(), "", "en_US")

        values = self.getValues()
        i18n.get_i18n().set_locale(self.getLanguage())

        if idSub != "":
            sub = db.Subject.get_by_id(long(idSub))
            teacher = db.Teacher.getByEmail(self.getEmail())

            if teacher is not None and not sub.containsTeacher(teacher.key):
                self.redirect("/")

        if not action:  # index
            template = JINJA_ENVIRONMENT.get_template('view/subjects/index.html')

        elif action == "view":
            sub = db.Subject.get_by_id(long(idSub))
            values["sub"] = sub
            values["teachers"] = sub.getTeachers()
            values["tasks"] = sub.getTasks().order(db.Task.order)
            values["promoted"] = "[" + ",".join(['"' + str(stKey.id()) + '"' for stKey in sub.promoteds]) + "]"

            if self.session.get('correctLines', None) is not None:  # File load results
                values["correct"] = self.session.pop('correctLines', None)
                values["incorrect"] = self.session.pop('incorrectLines', None)
                values["incorrect_lines"] = self.session.pop('incorrectLinesData', None)

            template = JINJA_ENVIRONMENT.get_template('view/subjects/view.html')

        elif action == "create":
            values["action"] = "create"
            template = JINJA_ENVIRONMENT.get_template('view/subjects/create.html')

        elif action == "modify" and idSub != "":
            values["subject"] = db.Subject.get_by_id(long(idSub))
            values["tasks"] = values["subject"].getTasks().order(db.Task.order)
            values["action"] = "modify"
            template = JINJA_ENVIRONMENT.get_template('view/subjects/create.html')
        elif action == "export" and idSub != "":

            # Current subject
            sub = db.Subject.get_by_id(long(idSub))

            type = self.request.get("ext", None)
            if type != "csv" and type != "xls":
                self.redirect("/subjects/view/%s" % sub.key.id())

            # Task that contains the current subject
            tasksInfo = sub.getTasks()

            # Marks per each task and student
            tasksMarks = {task.key: {m.student: m.mark for m in task.getMarks()} for task in sub.getTasks()}
            students = sub.getStudents().order(db.Student.dni)

            try:
                count = students.count()
            except Exception:
                count = 0

            if type == "csv":
                self.response.headers['Content-Type'] = 'text/csv'
                filename = self.getUserName() + "_" + str(time.time()).replace(".", "") + ".csv"
                self.response.headers['Content-Disposition'] = 'attachment; filename=' + filename

                fileContent = self.Parser.exportCsvStudentsFile(sub)
                self.response.write(fileContent)

                return
            elif type == "xls":
                self.response.headers['Content-Type'] = 'application/vnd.ms-excel'
                filename = self.getUserName() + "_" + str(time.time()).replace(".", "") + ".xls"
                self.response.headers['Content-Disposition'] = 'attachment; filename=' + filename
                #self.response.write(sys.path)

                fileContent = self.Parser.exportXlsStudentsFile(sub)
                self.response.write(fileContent)

                return

            self.redirect("/")
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
            teacherKey = db.Teacher.getByEmail(self.getEmail()).key

            # Subject data
            name = self.request.get("name")
            desc = self.request.get("description")
            start = self.request.get("startDate")
            end = self.request.get("endDate")

            startDate = datetime.date(*tuple(map(int, start.split("/"))[::-1]))
            endDate = datetime.date(*tuple(map(int, end.split("/"))[::-1]))

            subKey = db.Subject.addOrUpdate(name, desc, startDate, endDate, [teacherKey])

            # Go throught all the tasks of the subject
            for task in filter(lambda x: re.match('task[[0-9]*].name', x), list(self.request.POST)):
                id = task[5:task.find(']')]
                taskName = self.request.get(task)
                taskPercent = self.request.get("task[%s].percent" % id)
                taskMaxMark = self.request.get("task[%s].maxmark" % id)
                taskMinMark = self.request.get("task[%s].minmark" % id)
                taskInformative = self.request.get("task[%s].informative" % id)
                taskExtra = self.request.get("task[%s].extra" % id)

                db.Task.addOrUpdate(subKey, taskName, int(taskPercent), int(id), int(taskMaxMark), int(taskMinMark), taskInformative == "true", taskExtra == "true")

            idSub = str(subKey.id())

        elif action == "modify" and idSub != "":  # Modify existing subject
            sub = db.Subject.get_by_id(long(idSub))

            if not sub:
                self.redirect("/")

            tasks = {}
            for t in sub.getTasks().fetch():
                tasks[t.name] = t.key

            # Subject data
            name = self.request.get("name")
            desc = self.request.get("description")
            start = self.request.get("startDate")
            end = self.request.get("endDate")

            startDate = datetime.date(*tuple(map(int, start.split("/"))[::-1]))
            endDate = datetime.date(*tuple(map(int, end.split("/"))[::-1]))

            sub.update(name, desc, startDate, endDate)

            self.response.write(tasks)
            self.response.write("<br>")

            # Go throught all the tasks of the subject
            for task in filter(lambda x: re.match('task[[0-9]*].name', x), list(self.request.POST)):
                id = task[5:task.find(']')]
                taskName = self.request.get(task)
                taskPercent = self.request.get("task[%s].percent" % id)
                taskMaxMark = self.request.get("task[%s].maxmark" % id)
                taskMinMark = self.request.get("task[%s].minmark" % id)
                taskInformative = self.request.get("task[%s].informative" % id)
                taskExtra = self.request.get("task[%s].extra" % id)

                self.response.write("%s <> %s<br>" % (taskName, taskPercent))

                if taskName in tasks:
                    taskKey = tasks[taskName]
                    db.Task.addOrUpdate(sub.key, taskName, int(taskPercent), int(id), int(taskMaxMark), int(taskMinMark), taskInformative == "true", taskExtra == "true", taskKey)
                    del tasks[taskName]
                else:
                    db.Task.addOrUpdate(sub.key, taskName, int(taskPercent), int(id), int(taskMaxMark), int(taskMinMark), taskInformative == "true", taskExtra == "true")
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
                dni = self.request.get("dni").upper()
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
                fileContent = self.request.POST["filename"].value
                lines = self.request.POST["filename"].value.split("\r\n")

                filename = self.request.POST["filename"].filename

                if filename.endswith(".csv"):
                    # Get the subject from the datastore
                    sub = db.Subject.get_by_id(long(idSub))

                    results = self.Parser.importCsvStudentsFile(fileContent, sub)

                    self.session['correctLines'] = results["correct"]
                    self.session['incorrectLines'] = results["incorrect"]
                    self.session['incorrectLinesData'] = results["incorrect_lines"]
                    self.redirect("/subjects/view/" + idSub)
                elif filename.endswith(".xls"):
                    sub = db.Subject.get_by_id(long(idSub))

                    results = self.Parser.importXlsStudentsFile(fileContent, sub)
                    #self.response.write("/subjects/view/" + idSub + "?" + "&".join(["%s=%s" % (k, results[k]) for k in results]))
                    self.session['correctLines'] = results["correct"]
                    self.session['incorrectLines'] = results["incorrect"]
                    self.session['incorrectLinesData'] = results["incorrect_lines"]
                    self.redirect("/subjects/view/" + idSub)
                    return
            elif opt == "subject":
                pass
        elif action == "addteacher" and idSub != "":
            # Get params data
            email = self.request.get("teacherEmail")

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            # Add the teacher if they don't exist
            teacher = db.Teacher.getByEmail(email)
            if not teacher:
                tKey = db.Teacher.addOrUpdate(email, "")
            else:
                tKey = teacher.key

            if tKey not in sub.teachers:
                sub.addTeacher(tKey)
        elif action == "removeteacher" and idSub != "":  # ajax
            # Get params data
            teacherId = self.request.get("teacherId")
            teacher = db.Teacher.get_by_id(long(teacherId))

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            if teacher is not None and sub is not None:
                sub.removeTeacher(teacher.key)
            return
        elif action == "removestudent" and idSub != "":  # ajax
            # Get params data
            studentId = self.request.get("studentId")
            student = db.Student.get_by_id(long(studentId))

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            if student is not None and sub is not None:
                # Remove all the marks related with the tasks of the subject
                tasks = sub.getTasks()
                for task in tasks:
                    mark = db.Mark.getByStudentAndTask(student.key, task.key)
                    mark.remove()

                # Remove the student
                sub.removeStudent(student.key)
            return
        elif action == "removetask" and idSub != "":  # ajax
            # Get params data
            taskId = self.request.get("taskId")
            task = db.Task.get_by_id(long(taskId))

            # Get the subject from the datastore
            sub = db.Subject.get_by_id(long(idSub))

            if task is not None and sub is not None:
                sub.removeTask(task.key)
            return
        elif action == "addpromoted" and idSub != "":
            # Get subject
            sub = db.Subject.get_by_id(long(idSub))

            # Get student
            studentId = self.request.get("st")
            student = db.Student.get_by_id(long(studentId))

            if student.key not in sub.promoteds:
                sub.addPromoted(student.key)
            return
        elif action == "removepromoted" and idSub != "":
            # Get subject
            sub = db.Subject.get_by_id(long(idSub))

            # Get student
            studentId = self.request.get("st")
            student = db.Student.get_by_id(long(studentId))

            if student.key in sub.promoteds:
                sub.removePromoted(student.key)
            return
        elif action == "importmarks" and idSub != "":

            # Get subject
            sub = db.Subject.get_by_id(long(idSub))

            # Get task
            taskId = self.request.get("taskId")
            task = db.Task.get_by_id(long(taskId))

            fileContent = self.request.POST["filename"].value

            results = self.Parser.importCsvMarksFile(fileContent, task, sub)

            self.session['correctLines'] = results["correct"]
            self.session['incorrectLines'] = results["incorrect"]
            self.session['incorrectLinesData'] = results["incorrect_lines"]

            self.redirect("/tasks/calify/%s" % taskId)
            return
        elif action == "remove" and idSub != "":
            # Get subject
            sub = db.Subject.get_by_id(long(idSub))
            if sub:
                sub.remove()
            return
        self.redirect("/subjects/view/" + idSub)

    def formatDni(self, dni):
        dni = dni.upper()
        letters = "TRWAGMYFPDXBNJZSQVHLCKE"

        if not re.match("[0-9XYZ][0-9]{7}[A-Z]?", dni):
            return None

        if 'X' <= dni[0] <= 'Z':
            eqDni = str(ord(dni[0]) - 88) + dni[1:]

            if len(eqDni) == 8:
                return dni + letters[int(eqDni) % 23]
            elif letters[int(eqDni[:8]) % 23] == dni[8]:
                return dni

        elif '0' <= dni[0] <= '9':
            if len(dni) == 8:
                return dni + letters[int(dni) % 23]
            elif letters[int(dni[:8]) % 23] == dni[8]:
                return dni

        return None

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



class SearchHandler(base.BaseHandler):
    def get(self):
        if not self.loggedIn():
            self.redirect("/")
            return

        teacher = db.Teacher.getByEmail(self.getEmail())
        query = db.Subject.getSubjectsByTeacher(teacher.key)
        off = self.request.get("o", None)

        # Paginate the query (beginning after a offset if it's specified)
        data = db.paginateOff(query, (-db.Subject.creationdate, db.Subject.key), int(off) if off else 0)

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

config = {}
config['webapp2_extras.sessions'] = {
    'secret_key': '5680fd16956dd8ef2290e4c029e6e841',
}

app = webapp2.WSGIApplication([
    ('/subjects/search', SearchHandler),
    ('/subjects/?([a-z]*)/?([0-9]*)', SubjectsHandler)
], debug=True, config=config)
