import unittest

from flask import Flask

from Attendance import db
from Attendance.models import Student, Admin, Timetable


class StudentTests(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        db.init_app(self.app)

        db.session.remove()
        db.drop_all()
        db.create_all()
        populate_admin_table()
        # Create student for the test
        student = Student.create(name='Justin Smallwood', studentcode=542066)

    def tearDown(self):
        db.session.remove()
        db.drop_all()

    def test_get(self):
        student = Student.get(name="Justin Smallwood")
        self.assertTrue(isinstance(student, Student))
        self.assertEqual(student.name, "Justin Smallwood")

    def test_update(self):
        newname = "Jemima Capper"
        student = Student.get(name="Justin Smallwood")
        student.update(name=newname)
        self.assertEqual(student.name, newname)

    def test_delete(self):
        student = Student.get(name='Justin Smallwood')
        student = Student.get(name="Justin Smallwood")
        student.delete()
        self.assertEqual(Student.get(name="Justin Smallwood"), None)


def populate_admin_table():
    if Admin.query.filter_by(key='currentyear').first() == None:
        admin = Admin(key='currentyear', value=2017)
        db.session.add(admin)
        db.session.commit()
    if Admin.query.filter_by(key='studyperiod').first() == None:
        study = Admin(key='studyperiod', value='Semester 2')
        db.session.add(study)
        db.session.commit()
    if Admin.query.filter_by(key='timetable').first() is None:
        timetable = Timetable(key="default")
        db.session.add(timetable)
        db.session.commit()
        timetableadmin = Admin(key='timetable', value=timetable.id)
        db.session.add(timetableadmin)
        db.session.commit()
