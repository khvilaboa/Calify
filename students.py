# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, db, base
from google.appengine.ext import ndb
from google.appengine.datastore.datastore_query import Cursor


class SearchHandler(base.BaseHandler):
    def get(self):
        self.checkLogin()

        #query = db.Student.query()

        subId = self.request.get("sub", None)
        taskId = self.request.get("t", None)
        off = self.request.get("o", None)
        search = self.request.get("s", None)

        if not subId or not taskId:
            self.redirect("/")
            return

        sub = db.Subject.get_by_id(long(subId))
        task = db.Task.get_by_id(long(taskId))
        if not sub or not task:
            return

        #clicked = self.request.get("c", None)

        if search:
            query = sub.searchStudents(search)  # modify
        else:
            query = sub.getStudents()

        data = {}

        if off:
            data = db.paginateOff(query, db.Student.key, int(off))
        else:
            data = db.paginateOff(query, db.Student.key)

        """if not page and not clicked:
            data = db.paginate(query, db.Student.key)
        elif clicked == "next":
            data = db.paginate(query, db.Student.key, None, page)
        elif clicked == "prev":
            data = db.paginate(query, db.Student.key, page, None)"""

        """st = sub.getStudents()
        self.response.write([s.name for s in db.paginateOff(st, db.Student.key)["objects"]])
        self.response.write(db.paginateOff(st, db.Student.key))
        return"""

        """
        Ci0SJ2oPZGV2fmNhbGlmeS0xMjM0chQLEgdTdHVkZW50GICAgICAsPwIDBgAIAA=
        Ci0SJ2oPZGV2fmNhbGlmeS0xMjM0chQLEgdTdHVkZW50GICAgICAsKwJDBgAIAA=
        Ci0SJ2oPZGV2fmNhbGlmeS0xMjM0chQLEgdTdHVkZW50GICAgICAsNgJDBgAIAA=

        q = db.Student.query(db.Student.key.IN(sub.students))
        #q = db.Student.query()

        objectsF, cursorF, _ = q.order(db.Student.key).fetch_page(8)
        objectsS, cursorS, _ = q.order(db.Student.key).fetch_page(8, start_cursor=cursorF)
        objectsT, cursorT, more = q.order(db.Student.key).fetch_page(8, start_cursor=cursorS)

        # cursorT = cursorT.reversed()
        objectsSR, cursorSR, more = q.order(-db.Student.key).fetch_page(8, start_cursor=cursorT)
        objectsFR, cursorFR, more = q.order(-db.Student.key).fetch_page(8, start_cursor=cursorSR)

        objectsFR, cursorFR, more = q.order(-db.Student.key).fetch_page(9, end_cursor=cursorSR)
        objectsFRR, cursorFRR, more = q.order(-db.Student.key).fetch_page(9, end_cursor=cursorFR)
        objectsFRRR, cursorFRRR, more = q.order(db.Student.key).fetch_page(9, start_cursor=cursorFR)

        #self.response.write("%s,%s,%s,%s" % (page, search, clicked, taskId))
        self.response.write("<br>")
        self.response.write([n.name for n in objectsF])
        self.response.write("<br>")
        self.response.write([n.name for n in objectsS])
        self.response.write("<br>")
        self.response.write([n.name for n in objectsT])
        self.response.write("<br><br>")
        self.response.write([n.name for n in objectsSR])
        self.response.write("<br>")
        self.response.write([n.name for n in objectsFR])
        self.response.write("<br>")
        self.response.write([n.name for n in objectsFRR])
        self.response.write("<br>")
        self.response.write([n.name for n in objectsFRRR])
        self.response.write("<br><br>")
        self.response.write([n.name for n in q.order(db.Student.key)])
        self.response.write("<br>")
        self.response.write(cursorT.urlsafe())
        self.response.write("<br>")
        self.response.write(more)"""


        marks = {}
        for mark in task.getMarks():
            marks[mark.student.id()] = mark.mark

        resp = ""

        # Add the rows info
        for student in data["objects"]:
            """resp += "<tr data-id=\"%s\">" % student.key.id()
            resp += "<td>%s</td>" % student.name
            resp += "<td>%s</td>" % student.dni
            resp += "<td><img src=\"/img/delete.png\" class=\"img-icon icon-delete\" /></td></tr>"""""
            resp += "%s^^%s^^%s" % (student.key.id(), student.name, student.dni)
            resp += "^^%s" % marks.get(student.key.id(), "-1") if taskId else ""
            resp += "\n"



        # Add the buttons info in a new line
        resp += "\n%d\n%d" % (data["prevOffset"], data["nextOffset"])

        self.response.write(resp)

app = webapp2.WSGIApplication([
    ('/students/search', SearchHandler)
], debug=True)
