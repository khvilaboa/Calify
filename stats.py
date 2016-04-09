# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, jinja2, os, db, base

JINJA_ENVIRONMENT = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)),
    extensions=['jinja2.ext.autoescape'],
    autoescape=True)


class StatsHandler(base.BaseHandler):
    def get(self, subId):
        self.checkLogin()
        values = self.getValues()

        if not subId:
            teacher = db.Teacher.getByEmail(self.getEmail())
            subjects = db.Subject.getSubjectsByTeacher(teacher.key)

            values["subjects"] = "[" + ",".join(['"' + sub.name + '"' for sub in subjects]) + "]"
            values["studentsBySubject"] = "[" + ",".join(['"' + str(len(sub.students)) + '"' for sub in subjects]) + "]"

            values["marksByRanges"] = "[" + ",".join(['"' + mark + '"' for mark in self.getMarksPercentages(subjects)]) + "]"
            values["showMarksByRanges"] = values["marksByRanges"] != '["0","0","0","0","0"]'
            self.response.write(values["showMarksByRanges"])

            template = JINJA_ENVIRONMENT.get_template('/view/stats/index.html')
        self.response.write(template.render(values))

    def getMarksPercentages(self, subjects):
        marks = [0, 0, 0, 0, 0]
        for s in subjects:
            for m in s.getMarks():
                if m.mark < 5:
                    marks[0] += 1
                elif m.mark < 6:
                    marks[1] += 1
                elif m.mark < 7:
                    marks[2] += 1
                elif m.mark < 9:
                    marks[3] += 1
                else:
                    marks[4] += 1

        marksSum = sum(marks)
        return ["{0:.2f}".format(100*float(mark)/marksSum) if marksSum > 0 else "0" for mark in marks]

app = webapp2.WSGIApplication([
    ('/stats/?([a-z]*)', StatsHandler)
], debug=True)
