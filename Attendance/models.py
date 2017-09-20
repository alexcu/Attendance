from datetime import time
from operator import attrgetter

from pandas import ExcelFile, isnull
from flask import render_template
from Attendance import db, bcrypt
from Attendance.helpers import *


class CRUDMixin(object):
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)

    @classmethod
    def get(cls, **kwargs):
        return cls.query.filter_by(**kwargs, year=get_current_year(), studyperiod=get_current_studyperiod()).first()

    @classmethod
    def get_or_create(cls, **kwargs):
        obj = cls.get(**kwargs)
        if obj is None:
            obj = cls(**kwargs)
            db.session.add(obj)
            db.session.commit()
            return obj
        else:
            return obj

    def update(self, commit=True, **kwargs):
        for attr, value in kwargs.items():
            setattr(self, attr, value)
        return commit and self.save() or self

    def save(self, commit=True):
        db.session.add(self)
        if commit:
            db.session.commit()
        return self

    def delete(self, commit=True):
        db.session.delete(self)
        return commit and db.session.commit()

    @classmethod
    def create(cls, commit=True, **kwargs):
        instance = cls(**kwargs)
        return instance.save(commit=commit)

    @classmethod
    def get_all(cls, **kwargs):
        return cls.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(), **kwargs).all()


class Base(db.Model, CRUDMixin):
    __abstract__ = True
    '''
    I'm using this class to house the common database columns that come up again and again when defining these things.
    All of my classes can now extend Base and call its constructor.
    '''
    id = db.Column('id', db.Integer, primary_key=True)
    year = db.Column('year', db.Integer, nullable=False)
    studyperiod = db.Column('studyperiod', db.String(20), nullable=False)

    def __init__(self):
        self.year = get_current_year()
        self.studyperiod = get_current_studyperiod()


class User(Base):
    '''
    This is the basic User class that is used by Flask-Login and Flask-Principal.

    By default it creates a non-admin user.
    '''
    __tablename__ = "users"
    username = db.Column('username', db.String(40), unique=True, index=True, nullable=False)
    password = db.Column('password', db.String(50), nullable=False)
    email = db.Column('email', db.String(50))
    is_admin = db.Column('is_admin', db.String(10))

    def __init__(self, username, password):
        super().__init__()
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')
        self.is_admin = False

    def make_admin(self):
        self.update(is_admin=True)

    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.username)

    def __repr__(self):
        return '<User %r>' % (self.username)

    def view_user_template(self):
        return render_template('user.html', user=self, tutors=Tutor.get_all())


####MODELS


class Admin(db.Model):
    '''
    This is the Admin table where we keep key value pairs for certain things like year, studyperiod, timetable etc.
    It specifically does not inherit from Base as I do not want a year/studyperiod tag on this table.
    '''
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(50), nullable=False)

    def __init__(self, key, value):
        self.key = key
        self.value = value


'''
##Association tables
Association tables for the many-to-many relationships. These are the secondaries on db.relationship.
'''
substumap = db.Table('substumap',
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
                     db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id')),
                     )

subtutmap = db.Table('subtutmap',
                     db.Column('id', db.Integer, primary_key=True),
                     db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id')),
                     db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id')),
                     )

stuattendance = db.Table('stuattendance',
                         db.Column('id', db.Integer, primary_key=True),
                         db.Column('class_id', db.Integer, db.ForeignKey('tutorials.id')),
                         db.Column('student_id', db.Integer, db.ForeignKey('students.id'))
                         )

stutimetable = db.Table('stutimetable',
                        db.Column('id', db.Integer, primary_key=True),
                        db.Column('timetabledclass_id', db.Integer, db.ForeignKey('timetabledclass.id')),
                        db.Column('student_id', db.Integer, db.ForeignKey('students.id'))
                        )

timeslotclassesmap = db.Table('timeslotclassesmap',
                              db.Column('id', db.Integer, primary_key=True),
                              db.Column('timeslot_id', db.Integer, db.ForeignKey('timeslots.id')),
                              db.Column('timetabledclass_id', db.Integer, db.ForeignKey('timetabledclass.id'))
                              )

tutoravailabilitymap = db.Table('tutoravailabilitymap',
                                db.Column('id', db.Integer, primary_key=True),
                                db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id')),
                                db.Column('timeslot_id', db.Integer, db.ForeignKey('timeslots.id'))
                                )

'''
This is the subject class that contains each subject for each year/studyperiod
'''


class Subject(Base):
    __tablename__ = 'subjects'
    subcode = db.Column(db.String(50), nullable=False)
    subname = db.Column(db.String(50), nullable=False)
    classes = db.relationship("Tutorial", backref=db.backref('subject'), single_parent=True,
                              cascade='all,delete-orphan')
    repeats = db.Column(db.Integer, default=1)
    timetabledclasses = db.relationship("TimetabledClass", single_parent=True, cascade='all,delete-orphan')

    def __init__(self, subcode, subname, repeats=1):
        super().__init__()
        self.subcode = subcode
        self.subname = subname
        self.repeats = repeats

    def get_attendance_rate(self):
        '''
            This method gets the percentage attendance rate for all tutorials that have currently had rolls marked.
        '''
        totalstudents = 0
        attendedstudents = 0
        tutorials = self.classes
        for tutorial in tutorials:
            if len(tutorials) > 0:
                totalstudents += len(self.students)
                attendedstudents += len(tutorial.attendees)
        if totalstudents == 0:
            return 0
        else:
            return 100 * round(attendedstudents / totalstudents, 2)

    def is_at_risk(self):
        averageattendance = self.get_recent_average_attendance()
        if averageattendance == 0:
            return False
        elif averageattendance < 3:
            return True
        else:
            return False

    def addTutor(self, tutor):
        self.tutor = tutor
        db.session.commit()

    def get_recent_average_attendance(self):
        attendedstudents = 0
        timeframe = 3
        tutorials = self.classes
        tutorials = sorted(tutorials, key=lambda tutorial: tutorial.week)
        if len(tutorials) >= 3:
            for k in range(1, 1 + timeframe):
                attendedstudents += len(tutorials[len(tutorials) - k].attendees)
                averageattendance = attendedstudents / timeframe
        elif len(tutorials) > 0:
            for k in range(1, 1 + len(tutorials)):
                attendedstudents += len(tutorials[len(tutorials) - k].attendees)
                averageattendance = attendedstudents / len(tutorials)
        else:
            averageattendance = 0
        return round(averageattendance, 2)

    def view_subject_template(self, form, msg=""):
        return render_template("subject.html", subject=self, students=self.students,
                               tutor=self.tutor, tutors=Tutor.get_all(),
                               classes=self.classes, attendees=get_attendees_for_subject(self.subcode),
                               msg=msg, times=self.find_possible_times,
                               timeslots=Timeslot.get_all(),
                               timetabledclasses=self.timetabledclasses, form=form)

    def find_possible_times(self):
        students = self.students
        times = Timeslot.get_all()
        for student in students:
            for classes in student.timetabledclasses:
                timeslot = classes.timeslot
                if timeslot in times:
                    times.remove(timeslot)
        return times

    def get_tutorials_sorted(self):
        results = Tutorial.get_all(subjectid=self.id)
        return sorted(results, key=attrgetter('week'))


class Student(Base):
    __tablename__ = 'students'
    studentcode = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=True)
    subjects = db.relationship("Subject", secondary=substumap, backref=db.backref('students'))
    timetabledclasses = db.relationship("TimetabledClass", secondary=stutimetable,
                                        backref=db.backref('students'))
    university = db.Column(db.String(50))
    college = db.Column(db.String(50))
    email = db.Column(db.String(50))

    def __init__(self, studentcode, name, email=""):
        super().__init__()
        self.studentcode = studentcode
        self.name = name
        self.email = email

    def view_student_template(self, form, msg=""):
        return render_template('student.html', student=self, eligiblesubjects=Subject.get_all(),
                               subjects=self.subjects, msg=msg, form=form)

    def addSubject(self, subject):
        if subject not in self.subjects:
            self.subjects.append(subject)
            db.session.commit()


class Timetable(Base):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    studyperiod = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    key = db.Column(db.String(50), nullable=True)
    timeslots = db.relationship("Timeslot", single_parent=True, cascade='all,delete-orphan')

    def __init__(self, key=""):
        super().__init__()
        self.key = key


class Tutor(Base):
    __tablename__ = 'tutors'
    name = db.Column(db.String(50), nullable=False)
    subjects = db.relationship("Subject", secondary=subtutmap,
                               backref=db.backref('tutor', uselist=False, lazy='joined'))
    availabletimes = db.relationship("Timeslot", secondary=tutoravailabilitymap,
                                     backref=db.backref('availabiletutors'))
    timetabledclasses = db.relationship("TimetabledClass", single_parent=True, cascade="all,delete-orphan",
                                        backref=db.backref('tutor'))
    email = db.Column(db.String(50), nullable=True)
    classes = db.relationship("Tutorial", single_parent=True, cascade='all,delete-orphan', backref=db.backref('tutor'))
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", backref=db.backref('tutor', uselist=False))

    def __init__(self, name, email=""):
        super().__init__()
        self.name = name
        self.email = email
        self.generate_user_for_tutor()

    def get_teaching_times(self):
        teachingtimes = []
        for timeclass in self.timetabledclasses:
            teachingtimes.append(timeclass.timeslot)
        return teachingtimes

    def view_tutor_template(self, form, msg="", msg2="", msg3=""):
        return render_template('tutor.html', tutor=self, eligiblesubjects=Subject.get_all(),
                               subjects=self.subjects, timeslots=Timeslot.get_all(),
                               availability=self.availabletimes,
                               msg=msg, msg2=msg2, msg3=msg3, form=form)

    def generate_user_for_tutor(self):
        if len(self.name.split(' ')) > 1:
            # What if someone doesn't have a family name? This has happened before.
            username = self.name.split(' ')[0][0] + self.name.split(' ')[1]
        else:
            username = self.name
        if User.query.filter_by(username=username, year=get_current_year(),
                                studyperiod=get_current_studyperiod()).first() is None:
            user = User(username=username, password=username)
            db.session.add(user)
            user.tutor = self
            db.session.commit()

    def addAvailableTime(self, timeslot):
        if timeslot not in self.availabletimes:
            self.availabletimes.append(timeslot)
            db.session.commit()

    def addSubject(self, **kwargs):
        subject = Subject.get(**kwargs)
        if subject not in self.subjects:
            self.subjects.append(subject)
            db.session.commit()


class TimetabledClass(Base):
    '''
    This class represents a class on the timetable - for example, Linear Algebra is timetabled to be at Wednesday 7:30pm.

    When the timetable solver has finished - it inputs timetabledclasses.

    '''
    __tablename__ = 'timetabledclass'
    subjectid = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    subject = db.relationship("Subject")
    timetable = db.Column(db.Integer, db.ForeignKey('timetable.id'))
    time = db.Column(db.Integer, db.ForeignKey('timeslots.id'))
    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))

    def __init__(self, subjectid, timetable, time, tutorid):
        super().__init__()
        self.subjectid = subjectid
        self.timetable = timetable
        self.time = time
        self.tutorid = tutorid


class Room(db.Model):
    __tablename__ = 'rooms'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    projector = db.Column(db.Boolean)
    building = db.Column(db.String(50))


class Timeslot(Base):
    __tablename__ = 'timeslots'
    timetable = db.Column(db.Integer, db.ForeignKey('timetable.id'))
    day = db.Column(db.String(50), nullable=False)
    daynumeric = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    timetabledclasses = db.relationship("TimetabledClass", backref=db.backref('timeslot'), single_parent=True,
                                        cascade='all,delete-orphan')
    preferredtime = db.Column(db.Boolean)

    def __init__(self, day, time, preferredtime=True):
        super().__init__()
        self.timetable = get_current_timetable().id
        self.day = day
        self.daynumeric = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day)
        self.time = time
        self.preferredtime = preferredtime


class Tutorial(Base):
    '''
    This class is the physical tutorial that occurs 12 weeks in the semester. For instance - this is the tutorial that occurs on the
    30th October 2017.
    '''
    __tablename__ = 'tutorials'
    subjectid = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    week = db.Column(db.Integer, nullable=False)
    attendees = db.relationship("Student", secondary=stuattendance)
    datetime = db.Column(db.DateTime)

    def __init__(self, subjectid, tutorid, week):
        super().__init__()
        self.subjectid = subjectid
        self.tutorid = tutorid
        self.week = week


##### MODELS HELPER FUNCTIONS


# HELPER METHODS
def unlinksubjecttutor(tutorid, subcode):
    subject = Subject.get(subcode=subcode)
    subject.tutor = None
    db.session.commit()
    return "Unlinked Successfully."


def unlinksubjectstudent(studentcode, subcode):
    student = Student.get(studentcode=studentcode)
    subject = Subject.get(subcode=subcode)
    student.subjects.remove(subject)
    db.session.commit()
    return "Unlinked Successfully"


def linksubjecttutor(tutorid, subcode):
    subject = Subject.get(subcode=subcode)
    subject.tutor = Tutor.get(id=tutorid)
    db.session.commit()
    msg = "Subject Linked to Tutor Successfully"
    return msg


def get_min_max_week():
    classes = Tutorial.get_all()
    minweek = 13
    maxweek = 0
    for tutorial in classes:
        if tutorial.week < minweek:
            minweek = tutorial.week
        elif tutorial.week > maxweek:
            maxweek = tutorial.week
    return [minweek, maxweek]


def getadmin():
    admin = {}
    admin["currentyear"] = get_current_year()
    admin["studyperiod"] = get_current_studyperiod()
    return admin


def populate_students(df):
    print("Populating Students")
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    for index, row in df.iterrows():
        if row['Study Period'] == studyperiod:
            student = Student.get_or_create(studentcode=str(int(row["Student Id"])),
                                            name=row["Given Name"] + " " + row["Family Name"])
            subject = Subject.get_or_create(subcode=row["Component Study Package Code"],
                                            subname=row["Component Study Package Title"])
            student.addSubject(subject)


def populate_timetabledata(df):
    timetable = Timetable.get_or_create(key="default")
    print("Timetable Created")
    for index, row in df.iterrows():
        tutor = Tutor.get_or_create(name=row['x3'])
        subject = Subject.get_or_create(subcode=row['x1'])
        time2 = row['x4'].split(' ')
        day = time2[0]
        time2 = time2[1]
        time2 = check_time(time2)
        timeslot = Timeslot.get_or_create(day=day, time=time2)
        timetable = get_current_timetable()
        timetabledclass = TimetabledClass.get_or_create(time=timeslot.id, subjectid=subject.id, timetable=timetable.id)
        for i in range(5, len(row)):
            if not isnull(row[i]):
                student = Student.get(name=row[i]).first()
                if timetabledclass not in student.timetabledclasses:
                    student.timetabledclasses.append(timetabledclass)
                    db.session.commit()


def populate_availabilities(df):
    for index, row in df.iterrows():
        tutor = Tutor.get_or_create(name=row["Tutor"])
        tutor.availabletimes = []
        db.session.commit()
        for key in row.keys():
            keysplit = key.split(' ')
            if keysplit[0] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                timeslot = Timeslot.get_or_create(day=keysplit[0],
                                                  time=keysplit[1])
                if row[key] == 1:
                    tutor.addAvailableTime(timeslot)


def populate_tutors(df):
    for index, row in df.iterrows():
        tutor = Tutor.get_or_create(name=row['Tutor'])
        subject = Subject.get_or_create(subcode=row["Subject Code"])
        if subject not in tutor.subjects:
            subject.addTutor(tutor)


def update_year(year):
    admin = Admin.get(key='currentyear')
    admin.update(year=year)


def update_studyperiod(studyperiod):
    admin = Admin.query.filter_by(key='studyperiod').first()
    admin.value = studyperiod
    db.session.commit()


def add_class_to_db(week, subcode, attendees):
    '''
    Possibly not needed
    '''
    subject = Subject.get(subcode=subcode)
    tutor = subject.tutor
    if Tutorial.query.filter_by(week=week, subjectid=subject.id, year=get_current_year(),
                                studyperiod=get_current_studyperiod(), tutorid=tutor.id).first() == None:
        specificclass = Tutorial(week=week, subjectid=subject.id, tutorid=tutor.id)
        db.session.add(specificclass)
        db.session.commit()
        add_students_to_class(specificclass, attendees)
    return "Completed Successfully"


def add_students_to_class(specificclass, attendees):
    '''
    possibly not needed,
    '''
    for i in range(len(attendees)):
        student = Student.get(studentcode=attendees[i])
        specificclass.attendees.append(student)
        db.session.commit()
    return "Completed Successfully"


def get_attendees_for_subject(subcode):
    subject = Subject.get(subcode=subcode)
    classes = Tutorial.get_all(subjectid=subject.id)
    data = {}
    for row in classes:
        data[row.id] = row.attendees
    return data


def get_current_year():
    admin = Admin.query.filter_by(key='currentyear').first()
    return int(admin.value)


def get_current_timetable():
    admin = Admin.query.filter_by(key='timetable').first()
    return Timetable.get(id=int(admin.value))


def get_current_studyperiod():
    admin = Admin.query.filter_by(key='studyperiod').first()
    return admin.value


def linksubjectstudent(studentcode, subcode):
    student = Student.get(studentcode=studentcode)
    subject = Subject.get(subcode=subcode)
    if subject not in student.subjects:
        student.subjects.append(subject)
        db.session.commit()
    return "Linked Successfully."


def check_time(time2):
    '''
    This method checks when you input a timetable that the time is in the right format.

    '''
    if time2.find('pm') != -1:
        time2 = time.strftime("%H:%M", time.strptime(time2, "%I:%M%p"))
    elif len(time2) < 5:
        time2 = time2 + "pm"
        time2 = time.strftime("%H:%M", time.strptime(time2, "%I:%M%p"))
    return time2
