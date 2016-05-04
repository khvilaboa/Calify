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
    def get(self, subId):
        if not self.loggedIn():
            self.redirect("/")
            return

        values = self.getValues()

        i18n.get_i18n().set_locale(self.getLanguage())

        teacher = db.Teacher.getByEmail(self.getEmail())

        subjects = db.Subject.getSubjectsByTeacher(teacher.key).order(-db.Subject.creationdate).fetch()
        values["subjectsData"] = subjects

        if subId:
            sub = db.Subject.get_by_id(long(subId))

            if not sub:
                self.redirect("/stats")
                return

            tasks = sub.getTasks()
            values["tasks"] = "[" + ",".join(['"' + task.name + '"' for task in tasks]) + "]"
            values["studentsByTask"] = "[" + ",".join(['"' + str(len(task.getMarks())) + '"' for task in tasks]) + "]"
            values["avgMarkByTask"] = "[" + ",".join(['"' + mark + '"' for mark in self.getMeanMarkByTask(tasks)]) + "]"
            values["showTasksStats"] = len(tasks.fetch()) > 0

            values["marksByRanges"] = "[" + ",".join(['"' + mark + '"' for mark in self.getMarksPercentagesByTasks(tasks)]) + "]"
            values["showMarksByRanges"] = values["marksByRanges"] != '["0","0","0","0","0"]'

            values["showSubjectsStats"] = False
            values["subjectId"] = subId

            #self.response.write(values["showTasksStats"]); return

        else:
            values["subjects"] = "[" + ",".join(['"' + sub.name + '"' for sub in subjects]) + "]"
            values["studentsBySubject"] = "[" + ",".join(['"' + str(len(sub.students)) + '"' for sub in subjects]) + "]"
            values["avgMarkBySubject"] = "[" + ",".join(['"' + mark + '"' for mark in self.getMeanMarkBySubject(subjects)]) + "]"
            values["showSubjectsStats"] = len(subjects) > 0

            values["marksByRanges"] = "[" + ",".join(['"' + mark + '"' for mark in self.getMarksPercentagesBySubjects(subjects)]) + "]"
            values["showMarksByRanges"] = values["marksByRanges"] != '["0","0","0","0","0"]'

            values["showTasksStats"] = False
        template = JINJA_ENVIRONMENT.get_template('/view/stats/index.html')

        self.response.write(template.render(values))



    def getMarksPercentagesBySubjects(self, subjects):
        marks = [0, 0, 0, 0, 0]
        for s in subjects:
            for m in s.getMarks():
                t = m.task.get()
                sm = (m.mark / t.maxmark) * 10
                if sm < 5:
                    marks[0] += 1
                elif sm < 6:
                    marks[1] += 1
                elif sm < 7:
                    marks[2] += 1
                elif sm < 9:
                    marks[3] += 1
                else:
                    marks[4] += 1

        marksSum = sum(marks)
        return ["{0:.2f}".format(100*float(mark)/marksSum) if marksSum > 0 else "0" for mark in marks]

    def getMarksPercentagesByTasks(self, tasks):
        marks = [0, 0, 0, 0, 0]
        for t in tasks:
            for m in t.getMarks():
                sm = (m.mark / t.maxmark) * 10
                if sm < 5:
                    marks[0] += 1
                elif sm < 6:
                    marks[1] += 1
                elif sm < 7:
                    marks[2] += 1
                elif sm < 9:
                    marks[3] += 1
                else:
                    marks[4] += 1

        marksSum = sum(marks)
        return ["{0:.2f}".format(100*float(mark)/marksSum) if marksSum > 0 else "0" for mark in marks]

    def getMeanMarkByTask(self, tasks):
        avgMarkByTask = []
        for task in tasks:
            marks = task.getMarks()
            avgMarkByTask.append("{0:.2f}".format(float(sum([(m.mark / m.task.get().maxmark) * 10 for m in task.getMarks()])) / len(marks) if len(marks) > 0 else 0))
        return avgMarkByTask

    def getMeanMarkBySubject(self, subjects):
        avgMarkBySubject = []
        for sub in subjects:
            marks = sub.getMarks()
            avgMarkBySubject.append("{0:.2f}".format(float(sum([(m.mark / m.task.get().maxmark) * 10 for m in sub.getMarks()])) / len(marks) if len(marks) > 0 else 0))
        return avgMarkBySubject

app = webapp2.WSGIApplication([
    ('/stats/?([a-z0-9]*)', StatsHandler)
], debug=True)
