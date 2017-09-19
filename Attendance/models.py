from Attendance import app,db, bcrypt
from flask import render_template
from Attendance.helpers import *
import os
from operator import attrgetter
from pandas import ExcelFile, isnull
from datetime import time


class Base(db.Model):
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
    classes = db.relationship("Tutorial", backref=db.backref('subject'), single_parent=True, cascade='all,delete-orphan')
    repeats = db.Column(db.Integer,default = 1)
    timetabledclasses = db.relationship("TimetabledClass",single_parent=True, cascade = 'all,delete-orphan')
    def __init__(self, subcode, subname, repeats = 1):
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

    def get_recent_average_attendance(self):
        attendedstudents = 0
        timeframe = 3
        tutorials = self.classes
        tutorials = sorted(tutorials, key=lambda tutorial: tutorial.week)
        if len(tutorials) >= 3:
            for k in range(1, 1 + timeframe):
                attendedstudents += len(tutorials[len(tutorials) - k].attendees)
                averageattendance = attendedstudents / timeframe
        elif len(tutorials)>0:
            for k in range(1, 1 + len(tutorials)):
                attendedstudents += len(tutorials[len(tutorials) - k].attendees)
                averageattendance = attendedstudents / len(tutorials)
        else:
            averageattendance = 0
        return round(averageattendance,2)

    def view_subject_template(self, form,msg=""):
        return render_template("subject.html", subject=self, students=self.students,
                               tutor=self.tutor, tutors=get_tutors(),
                               classes=self.classes, attendees=get_attendees_for_subject(self.subcode),
                               msg=msg, times=find_possible_times(self.subcode),
                               timeslots=get_timeslots(),
                               timetabledclasses=self.timetabledclasses, form = form)

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

    def view_student_template(self, msg=""):
        return render_template('student.html', student=self, eligiblesubjects=get_subjects(),
                               subjects=self.subjects, msg=msg)


class Timetable(Base):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    studyperiod = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    key = db.Column(db.String(50), nullable=True)
    timeslots = db.relationship("Timeslot", single_parent = True, cascade = 'all,delete-orphan')
    def __init__(self, key=""):
        super().__init__()
        self.key = key




class Tutor(Base):
    __tablename__ = 'tutors'
    name = db.Column(db.String(50), nullable=False)
    subjects = db.relationship("Subject", secondary=subtutmap,
                               backref=db.backref('tutor', uselist=False,lazy='joined'))
    availabletimes = db.relationship("Timeslot", secondary=tutoravailabilitymap,
                                     backref=db.backref('availabiletutors'))
    timetabledclasses = db.relationship("TimetabledClass",single_parent=True,cascade ="all,delete-orphan", backref=db.backref('tutor'))
    classes = db.relationship("Tutorial", single_parent=True, cascade='all,delete-orphan', backref=db.backref('tutor'))
    userid = db.Column(db.Integer, db.ForeignKey('users.id'))
    user = db.relationship("User", backref=db.backref('tutor',uselist=False))

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

    def view_tutor_template(self, form,msg="", msg2="", msg3=""):
        return render_template('tutor.html', tutor=self, eligiblesubjects=get_subjects(),
                               subjects=self.subjects, timeslots=get_timeslots(),
                               availability=self.availabletimes,
                               msg=msg, msg2=msg2, msg3=msg3, form = form)

    def generate_user_for_tutor(self):
        username = self.name.split(' ')[0][0] + self.name.split(' ')[1]
        if User.query.filter_by(username = username, year = get_current_year(), studyperiod = get_current_studyperiod()).first() is None:
            user = User(username = username, password = username)
            db.session.add(user)
            user.tutor = self
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
    timetabledclasses = db.relationship("TimetabledClass", backref = db.backref('timeslot'),single_parent=True,cascade ='all,delete-orphan')
    preferredtime = db.Column(db.Boolean)

    def __init__(self, timetable, day, time, preferredtime=True):
        super().__init__()
        self.timetable = timetable
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
        self.subjectid = subjectid
        self.tutorid = tutorid
        self.week = week


##### MODELS HELPER FUNCTIONS


# HELPER METHODS
def get_tutor(tutorid):
    return Tutor.query.get(tutorid)

def get_student(studentcode):
    return Student.query.filter_by(studentcode=studentcode, year=get_current_year(),
                                   studyperiod=get_current_studyperiod()).first()


def get_classes():
    return Tutorial.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).all()

def get_subjects():
    return Subject.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).all()


def get_students():
    return Student.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).all()


def unlinksubjecttutor(tutorid, subcode):
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    subject.tutor = None
    db.session.commit()
    return "Unlinked Successfully."


def unlinksubjectstudent(studentcode, subcode):
    student = Student.query.filter_by(studentcode=studentcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    student.subjects.remove(subject)
    db.session.commit()
    return "Unlinked Successfully"


def linksubjecttutor(tutorid, subcode):
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    subject.tutor = Tutor.query.filter_by(id=tutorid).first()
    db.session.commit()
    msg = "Subject Linked to Tutor Successfully"
    return msg


def get_subject(subcode):
    return Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                   studyperiod=get_current_studyperiod()).first()




def get_min_max_week():
    classes = get_classes()
    minweek = 13
    maxweek = 0
    for tutorial in classes:
        if tutorial.week < minweek:
            minweek = tutorial.week
        elif tutorial.week > maxweek:
            maxweek = tutorial.week
    return [minweek, maxweek]

def get_classes_for_subject(subcode):
    sub = get_subject(subcode)
    results = Tutorial.query.filter_by(subjectid=sub.id, year=get_current_year(),
                                    studyperiod=get_current_studyperiod()).all()
    return sorted(results, key=attrgetter('week'))


def add_student(name, studentcode, email):
    print("Adding Student " + name)
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    if Student.query.filter_by(year=year, studyperiod=studyperiod, studentcode=studentcode).first() is None:
        student = Student(name=name, email=email, studentcode=studentcode)
        db.session.add(student)
        db.session.commit()


def get_timetabled_classes(subcode):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    subject = Subject.query.filter_by(subcode=subcode, year=year, studyperiod=studyperiod).first()
    return subject.timetabledclasses

def get_tutor_availability(tutorid):
    tutor = Tutor.query.get(tutorid)
    return tutor.availabletimes



def checkboxvalue(checkbox):
    if (checkbox != None):
        return 1
    else:
        return 0


def get_student_and_subjects(studentcode):
    student = Student.query.filter_by(studentcode=studentcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    return student.subjects


def get_timeslots():
    timetable = get_current_timetable()
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    timeslots = Timeslot.query.filter_by(timetable=timetable, year=year, studyperiod=studyperiod).order_by(
        Timeslot.daynumeric.asc(), Timeslot.time.asc()).all()
    return timeslots




def get_subject_and_students(subcode):
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    return subject.students


def get_subject_and_tutor(subcode):
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    return subject.tutor


def get_tutor_and_subjects(tutorid):
    tutor = Tutor.query.filter_by(id=tutorid).first()
    return tutor.subjects


def find_possible_times(subcode):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    subject = Subject.query.filter_by(subcode=subcode, year=year, studyperiod=studyperiod).first()
    students = subject.students
    times = get_timeslots()
    for student in students:
        for classes in student.timetabledclasses:
            timeslot = Timeslot.query.get(classes.time)
            if timeslot in times:
                times.remove(timeslot)
    return times


def getadmin():
    admin = {}
    admin["currentyear"] = get_current_year()
    admin["studyperiod"] = get_current_studyperiod()
    return admin


def get_tutors():
    return Tutor.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).order_by(
        Tutor.name.asc()).all()


def populate_students(filename):
    print("Populating Students")
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    xl = ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        if row['Study Period'] == studyperiod:
            if Student.query.filter_by(studentcode=str(int(row["Student Id"])), year=year,
                                       studyperiod=studyperiod).first() == None:
                student = Student(studentcode=str(int(row["Student Id"])),
                                  name=row["Given Name"] + " " + row["Family Name"])
                db.session.add(student)
                db.session.commit()
            if Subject.query.filter_by(subcode=row["Component Study Package Code"], year=year,
                                       studyperiod=studyperiod).first() == None:
                subject = Subject(subcode=row["Component Study Package Code"],
                                  subname=row["Component Study Package Title"])
                db.session.add(subject)
                db.session.commit()
            student = Student.query.filter_by(studentcode=str(int(row["Student Id"])),
                                              name=row["Given Name"] + " " + row["Family Name"], year=year,
                                              studyperiod=studyperiod).first()
            subject = Subject.query.filter_by(subcode=row["Component Study Package Code"], year=year,
                                              studyperiod=studyperiod).first()
            if subject not in student.subjects:
                student.subjects.append(subject)
                db.session.commit()


def populate_timetabledata(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    if Timetable.query.filter_by(year=year, studyperiod=studyperiod).first() is None:
        timetable = Timetable(key="default")
        db.session.add(timetable)
        db.session.commit()
    print("Timetable Created")
    xl = ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        if Tutor.query.filter_by(year=year, studyperiod=studyperiod, name=row['x3']).first() is None:
            tutor = Tutor(name=row['x3'])
            db.session.add(tutor)
            db.session.commit()
        tutor = Tutor.query.filter_by(year=year, studyperiod=studyperiod, name=row['x3']).first()
        if Subject.query.filter_by(year=year, studyperiod=studyperiod, subcode=row['x1']).first() is None:
            subject = Subject(subcode=row['x1'])
            db.session.add(subject)
            db.session.commit()
        subject = Subject.query.filter_by(subcode=row['x1'], year=year, studyperiod=studyperiod).first()
        time2 = row['x4'].split(' ')
        day = time2[0]
        time2 = time2[1]
        time2 = check_time(time2)

        if Timeslot.query.filter_by(year=year, studyperiod=studyperiod, day=day, time=time2).first() is None:
            timeslot = Timeslot(day = day,time = time2,timetable=get_current_timetable())
            db.session.add(timeslot)
            db.session.commit()
        timeslot = Timeslot.query.filter_by(year=year, studyperiod=studyperiod, day=day, time=time2).first()
        timetable = Timetable.query.get(get_current_timetable())

        if TimetabledClass.query.filter_by(studyperiod=studyperiod, year=year, time=timeslot.id, subjectid=subject.id,
                                           timetable=timetable.id).first() is None:
            timetabledclass = TimetabledClass(subjectid=subject.id,
                                              timetable=timetable.id, time=timeslot.id, tutorid=tutor.id)
            db.session.add(timetabledclass)
            db.session.commit()
        timetabledclass = TimetabledClass.query.filter_by(studyperiod=studyperiod, year=year, time=timeslot.id,
                                                          subjectid=subject.id, timetable=timetable.id).first()
        for i in range(5, len(row)):
            if not isnull(row[i]):
                student = Student.query.filter_by(year=year, studyperiod=studyperiod, name=row[i]).first()
                if timetabledclass not in student.timetabledclasses:
                    student.timetabledclasses.append(timetabledclass)
                    db.session.commit()






def populate_availabilities(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    timetable = get_current_timetable()
    xl = ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])
    for index,row in df.iterrows():
        if Tutor.query.filter_by(name=row["Tutor"], year=year, studyperiod=studyperiod).first() is None:
            tutor = Tutor(name=row["Tutor"])
            db.session.add(tutor)
            db.session.commit()
        tutor = Tutor.query.filter_by(name=row["Tutor"], year=year, studyperiod=studyperiod).first()
        tutor.availabletimes = []
        db.session.commit()
        for key in row.keys():
            keysplit = key.split(' ')
            if keysplit[0] in ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']:
                if Timeslot.query.filter_by(year=year, studyperiod=studyperiod, timetable=timetable, day=keysplit[0],
                                            time=keysplit[1]).first() is None:
                    timeslot = Timeslot(timetable=timetable, day=keysplit[0],
                                        time=keysplit[1])
                    db.session.add(timeslot)
                    db.session.commit()
                timeslot = Timeslot.query.filter_by(year=year, studyperiod=studyperiod, timetable=timetable,
                                                    day=keysplit[0], time=keysplit[1]).first()
                if row[key] == 1:
                    tutor.availabletimes.append(timeslot)
                db.session.commit()



def populate_tutors(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    xl = ExcelFile(filename)

    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        if Tutor.query.filter_by(name=row['Tutor'], year=year, studyperiod=studyperiod).first() is None:
            tutor = Tutor(name=row['Tutor'])
            db.session.add(tutor)
            db.session.commit()

        tutor = Tutor.query.filter_by(name=row['Tutor'], year=year, studyperiod=studyperiod).first()
        if Subject.query.filter_by(subcode=row["Subject Code"], year=year, studyperiod=studyperiod).first() is None:
            subject = Subject(subcode=row["Subject Code"], subname=" ", repeats=row["Repeats"])
            db.session.add(subject)
            db.session.commit()
        subject = Subject.query.filter_by(subcode=row["Subject Code"], year=year, studyperiod=studyperiod).first()
        if subject not in tutor.subjects:
            subject.tutor = tutor
            msg = db.session.commit()


def update_year(year):
    admin = Admin.query.filter_by(key='currentyear').first()
    admin.value = year
    db.session.commit()


def update_studyperiod(studyperiod):
    admin = Admin.query.filter_by(key='studyperiod').first()
    admin.value = studyperiod
    db.session.commit()


def check_time(time2):
    if time2.find('pm') != -1:
        time2 = time.strftime("%H:%M", time.strptime(time2, "%I:%M%p"))
    elif len(time2) < 5:
        time2 = time2 + "pm"
        time2 = time.strftime("%H:%M", time.strptime(time2, "%I:%M%p"))
    return time2


def get_tutor_from_name(tutor):
    tutor = tutor["Tutor"]
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    tutor = Tutor.query.filter_by(name=tutor, year=year, studyperiod=studyperiod).first()
    return tutor


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


def upload(file):
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = file.filename
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename2 = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        return filename2


def get_attendees(classid):
    classdata = Tutorial.query.get(classid)
    rows = classdata.attendees
    returns = []
    for row in rows:
        returns.append(row.studentcode)
    return returns


def get_class(classid):
    return Tutorial.query.filter_by(id=classid).first()


def add_class_to_db(week, subcode, attendees):
    tutor = get_subject_and_tutor(subcode)
    subject = get_subject(subcode)
    if Tutorial.query.filter_by(week = week, subjectid=subject.id, year=get_current_year(),
                             studyperiod=get_current_studyperiod(), tutorid=tutor.id).first() == None:
        specificclass = Tutorial(week = week, subjectid=subject.id, tutorid=tutor.id)
        db.session.add(specificclass)
        db.session.commit()
        add_students_to_class(specificclass, attendees)
    return "Completed Successfully"





def add_students_to_class(specificclass, attendees):
    for i in range(len(attendees)):
        student = get_student(attendees[i])
        specificclass.attendees.append(student)
        db.session.commit()
    return "Completed Successfully"


def get_attendees_for_subject(subcode):
    subject = get_subject(subcode)
    classes = Tutorial.query.filter_by(subjectid=subject.id).all()
    data = {}
    for row in classes:
        data[row.id] = row.attendees
    return data


def get_current_year():
    admin = Admin.query.filter_by(key='currentyear').first()
    return int(admin.value)


def get_current_timetable():
    admin = Admin.query.filter_by(key='timetable').first()
    return int(admin.value)

def get_current_studyperiod():
    admin = Admin.query.filter_by(key='studyperiod').first()
    return admin.value


def linksubjectstudent(studentcode, subcode):
    student = Student.query.filter_by(studentcode=studentcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
    if subject not in student.subjects:
        student.subjects.append(subject)
        db.session.commit()
    return "Linked Successfully."

def get_users():
    return User.query.filter_by(year = get_current_year(), studyperiod = get_current_studyperiod()).all()


def view_user_template(username):
    return render_template('user.html', user = get_user(username), tutors = get_tutors())

def get_user(username):
    return User.query.filter_by(username=username).first()
