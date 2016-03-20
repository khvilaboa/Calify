#!/usr/bin/env python

from google.appengine.ext import ndb


class Subject(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    description = ndb.StringProperty(indexed=False)
    year = ndb.IntegerProperty(indexed=True)

    def tasks(self):
        return Task.query(ancestor=self.key)

    def teachers(self):
        return Teacher.query(ancestor=self.key)


class Task(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    percent = ndb.IntegerProperty(indexed=True)

    # students = db.ListProperty(ndb.Key)


class Teacher(ndb.Model):
    email = ndb.StringProperty(indexed=False)

    subjects = ndb.KeyProperty(kind="Subject", repeated=True)


class Student(ndb.Model):
    email = ndb.StringProperty(indexed=False)
    dni = ndb.StringProperty(indexed=False)
    name = ndb.StringProperty(indexed=False)

    # subjects = db.ListProperty(ndb.Key)
