
import webapp2, db, base


class CrudHandler(base.BaseHandler):

    def get(self, action, teacherId):
        pass


class SearchHandler(base.BaseHandler):
    def get(self):
        if not self.loggedIn():
            self.redirect("/")
            return
        s = self.request.get("s")
        count = 0
        for teacher in db.Teacher.query().order(-db.Teacher.email):
            if teacher.email.find(s) != -1:
                self.response.write("<div class='searchResult'>" + teacher.email + "</div>")
                count += 1
                if count == 5:
                    break


app = webapp2.WSGIApplication([
    ('/teachers/search', SearchHandler),
    ('/teachers/(delete)/([0-9]+)', CrudHandler)
], debug=True)
