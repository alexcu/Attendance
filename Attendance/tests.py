import unittest

from flask import Flask
from Attendance import db
from Attendance.models import Student, Admin, Timetable, Subject, User


class BaseTest(unittest.TestCase):
    '''
    This class takes in the common setup and teardown methods. This means that
    we don't have to repeat ourselves and we can just put any inital stuff for a class
    in the setUpTestData method.

    '''
    def setUp(self):
        self.app = Flask(__name__)
        # self.app.config['SQLALCHEMY_DATABASE_URI']='sqlite:////'
        db.init_app(self.app)
        db.session.remove()
        db.drop_all()
        db.create_all()
        populate_admin_table()
        self.setUpTestData()

        def tearDown(self):
            db.session.remove()
            db.drop_all()


class StudentTests(BaseTest):
    # Create student for the test
    def setUpTestData(self):
        student = Student.create(name='Justin Smallwood', studentcode=542066)



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


class SubjectTests(BaseTest):
    def setUpTestData(self):
        # Create subject for the test
        subject = Subject.create(subcode='ECON10005', subname='Quantitative Methods 1')

    def test_get(self):
        subject = Subject.get(subcode="ECON10005")
        self.assertTrue(isinstance(subject, Subject))
        self.assertEqual(subject.subname, "Quantitative Methods 1")

    def test_update(self):
        newname = "Quantitative Methods 2"
        subject = Subject.get(subcode="ECON10005")
        subject.update(subname=newname)
        self.assertEqual(subject.subname, newname)

    def test_delete(self):
        subject = Subject.get(subcode="ECON10005")
        self.assertEqual(subject.subname, "Quantitative Methods 1")
        subject.delete()
        self.assertEqual(Subject.get(subcode="ECON10005"), None)


class UserTests(BaseTest):
    def setUpTestData(self):
        User.create(username='testuser', password='testuser')

    def test_get(self):
        user = User.get(username="testuser")
        self.assertTrue(isinstance(user, User))




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
