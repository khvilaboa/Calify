#!/usr/bin/env python

from google.appengine.ext import ndb


class Subject(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    description = ndb.StringProperty(indexed=False)
    year = ndb.IntegerProperty(indexed=True)

    teachers = ndb.KeyProperty(kind="Teacher", repeated=True)
    students = ndb.KeyProperty(kind="Student", repeated=True)

    def tasks(self):
        return Task.query(Task.subject == self.key)

    def getStudents(self):
        return [stKey.get() for stKey in self.students]

    def addStudent(self, stKey):
        self.students.append(stKey)
        return self.put()

    def addTeacher(self, tKey):
        self.teachers.append(tKey)
        return self.put()

    def removeTeacher(self, tKey):
        self.teachers.remove(tKey)
        return self.put()

    def removeStudent(self, stKey):
        self.students.remove(stKey)
        for mark in Mark.query(Mark.student == stKey):
            mark.key.delete()
        return self.put()

    def removeTask(self, taskKey):
        task = taskKey.get()
        if task:
            taskKey.delete()


    @staticmethod
    def removeById(id):
        sub = Subject.get_by_id(long(id))
        if sub:
            for task in sub.tasks():
                task.key.delete()
            sub.key.delete()
            return True
        return False

    @staticmethod
    def addOrUpdate(name, desc, year, teachers, students=[], key=None):

        if key == None: # add
            sub = Subject(name=name, description=desc, year=year, teachers=teachers, students=students)
        else:
            sub = key.get()
            sub.name = name
            sub.description = desc
            sub.teachers = teachers
            sub.students = students

        return sub.put()



class Task(ndb.Model):
    name = ndb.StringProperty(indexed=True)
    percent = ndb.IntegerProperty(indexed=True)

    subject = ndb.KeyProperty(kind='Subject')

    def getStudents(self):
        sub = self.subject.get()
        return sub.students

    def getMarks(self):
        sub = self.subject.get()
        return Mark.getMarks(self)

    @staticmethod
    def addOrUpdate(subKey, name, percent, taskKey = None):

        if taskKey == None: # add
            task = Task(subject=subKey, name=name, percent=percent)
        else:
            task = taskKey.get()
            task.name = name
            task.percent = percent

        return task.put()


class Teacher(ndb.Model):
    email = ndb.StringProperty(indexed=True)

    @staticmethod
    def exists(email):
        return len(Teacher.query(Teacher.email == email).fetch()) > 0

    @staticmethod
    def getByEmail(email):
        teacher = Teacher.query(Teacher.email == email).fetch()
        return teacher[0] if len(teacher) > 0 else None

    @staticmethod
    def addOrUpdate(email):
        t = Teacher.getByEmail(email)
        if t is None:
            t = Teacher(email=email)
        else:
            t.email = email
        return t.put()




class Student(ndb.Model):
    #email = ndb.StringProperty(indexed=False)
    dni = ndb.StringProperty(indexed=True)
    name = ndb.StringProperty(indexed=False)

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

    @staticmethod
    def getMarks(task):
        return Mark.query(Mark.task == task.key).fetch()
