#!/usr/bin/env python

import datetime
from google.appengine.ext import ndb


class Subject(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    description = ndb.StringProperty(indexed=False)
    startdate = ndb.DateProperty(indexed=False)
    enddate = ndb.DateProperty(indexed=False)
    completed = ndb.BooleanProperty(indexed=False)
    creationdate = ndb.DateTimeProperty(indexed=True)

    teachers = ndb.KeyProperty(kind="Teacher", repeated=True)
    students = ndb.KeyProperty(kind="Student", repeated=True)
    promoted = ndb.KeyProperty(kind="Student", repeated=True)

    def getTasks(self):
        return Task.query(Task.subject == self.key)

    def getMarks(self):
        m = []
        for t in self.getTasks():
            m += t.getMarks()
        return m

    def getStudents(self):
        return Student.query(Student.key.IN(self.students))

    def addStudent(self, stKey):
        self.students.append(stKey)
        return self.put()

    def removeStudent(self, stKey):
        self.students.remove(stKey)
        for mark in Mark.query(Mark.student == stKey):
            mark.key.delete()
        return self.put()

    """def searchStudents(self, s):
        return Student.query(ndb.OR(Student.dni == s, Student.name == s))"""

    def searchStudents(self, search):
        students = []
        for st in self.getStudents().fetch():
            if search in st.name or search in st.dni:
                students.append(st)
        return students

    def getTeachers(self):
        return [tKey.get() for tKey in self.teachers]

    def containsTeacher(self, key):
        return key in self.teachers

    def addTeacher(self, tKey):
        self.teachers.append(tKey)
        return self.put()

    def removeTeacher(self, tKey):
        self.teachers.remove(tKey)
        return self.put()

    def removeTask(self, taskKey):
        task = taskKey.get()
        if task:
            taskKey.delete()

    def setCompleted(self, comp):
        self.completed = comp
        return self.put()

    def removeAllPromoteds(self):
        self.promoted = []
        return self.put()

    def addPromoted(self, stKey):
        self.promoted.append(stKey)
        return self.put()

    def removePromoted(self, stKey):
        self.promoted.remove(stKey)
        return self.put()

    def getStudentFinalMark(self, stKey):

        def getPromotedMark(mark):
            for impMark in [5,7,9]:
                if 0.25 >= impMark - mark > 0:
                    return impMark
            return mark

        tasks = self.getTasks()
        student = stKey.get()
        weightedAvg = 0
        extraPoints = 0
        pres = False
        for task in tasks:
            rawMark = Mark.getByStudentAndTask(student.key, task.key)
            if not rawMark or task.informative:
                continue
            elif task.extra:
                extraPoints += rawMark.mark
                pres = True
                continue
            mark = (rawMark.mark / task.maxmark) * 10 * (task.percent/100.0)
            weightedAvg += mark
            pres = True

        if pres:
            mark = min(weightedAvg + extraPoints, 10)
            if stKey in self.promoted:
                mark = getPromotedMark(mark)
            if mark == int(mark):
                mark = int(mark)
            return mark

        return None

    @staticmethod
    def getSubjectsByTeacher(key):
        return Subject.query(Subject.teachers == key)

    @staticmethod
    def removeById(id):
        sub = Subject.get_by_id(long(id))
        if sub:
            for task in sub.getTasks():
                task.key.delete()
            sub.key.delete()
            return True
        return False

    @staticmethod
    def addOrUpdate(name, desc, startDate, endDate,  teachers, students=[], key=None):

        if key == None:  # add
            sub = Subject(name=name, description=desc, startdate=startDate,enddate=endDate ,teachers=teachers, creationdate=datetime.datetime.now(), completed=False, students=students)
        else:
            sub = key.get()
            sub.name = name
            sub.description = desc
            sub.startdate = startDate
            sub.enddate = endDate
            sub.teachers = teachers
            sub.students = students

        return sub.put()


class Task(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    percent = ndb.IntegerProperty(indexed=True)
    order = ndb.IntegerProperty(indexed=True)
    maxmark = ndb.IntegerProperty(indexed=True)
    informative = ndb.BooleanProperty(indexed=False)
    extra = ndb.BooleanProperty(indexed=False)

    subject = ndb.KeyProperty(kind='Subject')

    def getStudents(self):
        sub = self.subject.get()
        return sub.students

    def getMarks(self):
        return Mark.query(Mark.task == self.key).fetch()

    @staticmethod
    def addOrUpdate(subKey, name, percent, order, maxMark, informative, extra, taskKey=None):

        if taskKey is None:  # add
            task = Task(subject=subKey, name=name, order=order, percent=int(percent), maxmark=maxMark,
                        informative=informative, extra=extra)
        else:
            task = taskKey.get()
            task.name = name
            task.percent = int(percent)
            task.order = order

        return task.put()


class Teacher(ndb.Model):
    email = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=True)
    language = ndb.StringProperty(indexed=False)

    def setLanguage(self, lang):
        self.language = lang
        return self.put()

    @staticmethod
    def exists(email):
        return len(Teacher.query(Teacher.email == email).fetch()) > 0

    @staticmethod
    def getByEmail(email):
        teacher = Teacher.query(Teacher.email == email).fetch()
        return teacher[0] if len(teacher) > 0 else None

    @staticmethod
    def addOrUpdate(email, name, lang=None):
        t = Teacher.getByEmail(email)
        if t is None:
            if lang is None: lang = "en_US"
            t = Teacher(email=email, language=lang)
        else:
            t.name = name
            if lang is not None: t.language = lang
        return t.put()


class Student(ndb.Model):
    # email = ndb.StringProperty(indexed=False)
    dni = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=True)

    def hasHonorsInSubject(self, subKey):
        sub = subKey.get()
        if sub and self.key in sub.promoted:
            return sub.getStudentFinalMark(self.key) >= 9
        return False

    @staticmethod
    def exists(dni):
        return len(Student.query(Student.dni == dni).fetch()) > 0

    @staticmethod
    def getByDni(dni):
        st = Student.query(Student.dni == dni).fetch()
        return st[0] if len(st) > 0 else None

    @staticmethod
    def addOrUpdate(dni, name):
        st = Student.getByDni(dni)
        if st is None:
            st = Student(dni=dni, name=name)
        else:
            st.name = name
        return st.put()


class Mark(ndb.Model):
    mark = ndb.FloatProperty(indexed=False)

    student = ndb.KeyProperty(kind='Student')
    task = ndb.KeyProperty(kind='Task')

    @staticmethod
    def exists(student, task):
        return len(Mark.query(ndb.AND(Mark.student == student.key, Mark.task == task.key)).fetch()) > 0

    @staticmethod
    def getByStudentAndTask(studentKey, taskKey):
        mark = Mark.query(ndb.AND(Mark.student == studentKey, Mark.task == taskKey)).fetch()
        return mark[0] if len(mark) > 0 else None

    @staticmethod
    def addOrUpdate(studentKey, taskKey, mark):
        m = Mark.getByStudentAndTask(studentKey, taskKey)
        if m is None:
            m = Mark(student=studentKey, task=taskKey, mark=mark)
        else:
            m.mark = mark
        return m.put()


ITEMS_PER_PAGE = 8


def paginateOff(query, order, offset=0):
    qOrdered = query.order(*order) if type(order) is tuple else query.order(order)
    objects, nextCursor, more = qOrdered.fetch_page(ITEMS_PER_PAGE, offset=offset)
    prev_offset = max(offset - ITEMS_PER_PAGE, 0) if bool(offset) else -1
    next_offset = offset + ITEMS_PER_PAGE if bool(more) else -1

    return {'objects': objects, 'prevOffset': prev_offset, 'nextOffset': next_offset, 'curOffset': offset}

def paginateArray(array, offset=0):
    objects = array[offset:offset+ITEMS_PER_PAGE]
    prev_offset = max(offset - ITEMS_PER_PAGE, 0) if bool(offset) else -1
    next_offset = offset + ITEMS_PER_PAGE if len(array) >= offset + ITEMS_PER_PAGE else -1
    return {'objects': objects, 'prevOffset': prev_offset, 'nextOffset': next_offset, 'curOffset': offset}
