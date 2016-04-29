# -*- coding: utf-8 -*-
#!/usr/bin/env python


import webapp2, db, base


class SearchHandler(base.BaseHandler):
    def get(self):
        if not self.loggedIn():
            self.redirect("/")
            return

        # Get request parameters
        subId = self.request.get("sub", None)
        taskId = self.request.get("t", None)
        off = self.request.get("o", None)
        search = self.request.get("s", None)

        if not subId:
            self.redirect("/")
            return

        sub = db.Subject.get_by_id(long(subId))

        if not sub:
            self.redirect("/")
            return

        # If a search string is passed, filter the subject students, else get all of them
        if search:
            query = sub.searchStudents(search)  # modify
        else:
            query = sub.getStudents()

        try:
            lenQuery = query.count()  #len(query.fetch())
        except Exception:
            lenQuery = 0

        resp = ""

        if lenQuery > 0:
            # Paginate the query (beginning after a offset if it's specified)
            data = db.paginateOff(query, (db.Student.name, db.Student.key), int(off) if off else 0)

            # If the user is in a task view retrieve the mark for each of the selected students
            marks = {}
            if taskId:
                task = db.Task.get_by_id(long(taskId))
                for mark in task.getMarks():
                    marks[mark.student.id()] = mark.mark



            # Add the rows info
            for student in data["objects"]:
                resp += "%s^^%s^^%s" % (student.key.id(), student.name, student.dni)  # Data to be formatted in the JS code
                resp += "^^%s" % marks.get(student.key.id(), "-1") if taskId else ""  # Add marks if the destination is a task view
                resp += "\n"

            if len(data["objects"]):
                # Add the buttons info (new offsets)
                resp += "\n%d\n%d" % (data["prevOffset"], data["nextOffset"])

                # Add the nearest pages info
                maxPage = max(0, 8*((lenQuery - 1)//8))
                curPage = data["curOffset"]
                leftPage = max(0, curPage-2*db.ITEMS_PER_PAGE)
                rightPage = min(curPage+2*db.ITEMS_PER_PAGE, maxPage)
                resp += "\n\n%d\n%d\n%d\n%d" % (leftPage, rightPage, curPage, db.ITEMS_PER_PAGE)

        self.response.write(resp)

app = webapp2.WSGIApplication([
    ('/students/search', SearchHandler)
], debug=True)
