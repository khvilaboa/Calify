#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
from google.appengine.api import users


class BaseHandler(webapp2.RequestHandler):
    def checkLogin(self):
        user = users.get_current_user()
        if not user:
            self.redirect("/")

    def getValues(self):
        return {"logoutUrl": users.create_logout_url("/")}



app = webapp2.WSGIApplication([
    ('/', BaseHandler)
], debug=True)
