# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, db, base


class SearchHandler(base.BaseHandler):
    def get(self):
        self.checkLogin()

        subId = self.request.get("sub", None)
        if not subId:
            self.response.write(subId)
            return

        sub = db.Subject.get_by_id(long(subId))
        if not sub:
            return


        #query = db.Student.query()

        page = self.request.get("p", None)
        search = self.request.get("s", None)
        clicked = self.request.get("c", None)

        if search:
            query = sub.searchStudents(search)
        else:
            query = sub.getStudents()

        data = {}

        if not page and not clicked:
            data = db.paginate(query, db.Student.key)
        elif clicked == "next":
            data = db.paginate(query, db.Student.key, None, page)
        elif clicked == "prev":
            data = db.paginate(query, db.Student.key, page, None)

        resp = ""

        # Add the rows info
        for student in data["objects"]:
            resp += "<tr data-id=\"%s\">" % student.key.id()
            resp += "<td>%s</td>" % student.name
            resp += "<td>%s</td>" % student.dni
            resp += "<td><img src=\"/img/delete.png\" class=\"img-icon icon-delete\" /></td></tr>"

        # Add the buttons info in a new line
        resp += "\n"
        if data["hasPrev"]:
            resp += "<button class=\"btn btn-default\" id=\"prevPage\" data-id=\"%s\">Previous</button>" % data["prevStr"]
        if data["hasNext"]:
            resp += "<button class=\"btn btn-default\" id=\"nextPage\" data-id=\"%s\">Next</button>" % data["nextStr"]

        self.response.write(resp)

app = webapp2.WSGIApplication([
    ('/students/search', SearchHandler)
], debug=True)
