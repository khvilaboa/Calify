#!/usr/bin/env python

from google.appengine.ext import ndb


class Subject(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    description = ndb.StringProperty(indexed=False)
    year = ndb.IntegerProperty(indexed=True)

    teachers = ndb.KeyProperty(kind="Teacher", repeated=True)

    def tasks(self):
        return Task.query(ancestor=self.key)

    #def teachers(self):
    #    return Teacher.query().filter(Teacher.subjects == self.key)


class Task(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    percent = ndb.IntegerProperty(indexed=True)

    # students = db.ListProperty(ndb.Key)


class Teacher(ndb.Model):
    email = ndb.StringProperty(indexed=True)

    @staticmethod
    def exists(email):
        return len(Teacher.query(Teacher.email == email).fetch()) > 0

    @staticmethod
    def getByEmail(email):
        teacher = Teacher.query(Teacher.email == email).fetch()
        return teacher[0] if len(teacher) > 0 else None

class Student(ndb.Model):
    email = ndb.StringProperty(indexed=False)
    dni = ndb.StringProperty(indexed=False)
    name = ndb.StringProperty(indexed=False)

    # subjects = db.ListProperty(ndb.Key)
