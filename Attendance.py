import json
from datetime import datetime
from operator import attrgetter

import pandas
from flask import Flask
from flask import render_template
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import *
from pulp import *
from sqlalchemy.orm import joinedload
from concurrent.futures import ThreadPoolExecutor

# DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
executor = ThreadPoolExecutor(2)
app = Flask(__name__)

# WINDOWS
# app.config['UPLOAD_FOLDER'] = 'D:/Downloads/uploads/'
# LINUX
app.config['UPLOAD_FOLDER'] = '/Users/justin/Downloads/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['xls', 'xlsx'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/justin/Dropbox/Justin/Documents/Python/database43.db'
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)


def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


####MODELS
class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True)
    password = db.Column(db.String(50))

    def __init__(self, username, password):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return '<User %r>' % self.username


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(50), nullable=False)

    def __init__(self, key, value):
        self.key = key
        self.value = value


class SubStuMap(object):
    def __init__(self, student_id, subject_id):
        self.student_id = student_id
        self.subject_id = subject_id


class SubTutMap(object):
    def __init__(self, tutor_id, subject_id):
        self.tutor_id = tutor_id
        self.subject_id = subject_id


class StuAttendance(object):
    def __init__(self, class_id, student_id):
        self.class_id = class_id
        self.student_id = student_id


class StuTimetable(object):
    def __init__(self, timetabledclass_id, student_id):
        self.timetabledclass_id = timetabledclass_id
        self.student_id = student_id


class TimeslotClasses(object):
    def __init__(self, timeslot_id, timetabledclass_id):
        self.timetabledclass_id = timetabledclass_id
        self.timeslot_id = timeslot_id


class TutorAvailability(object):
    def __init__(self, tutor_id, timeslot_id):
        self.tutor_id = tutor_id
        self.timeslot_id = timeslot_id

##Association tables
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
                         db.Column('class_id', db.Integer, db.ForeignKey('classes.id')),
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

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subcode = db.Column(db.String(50), nullable=False)
    subname = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    studyperiod = db.Column(db.String(50), nullable=False)
    classes = db.relationship("Class")
    repeats = db.Column(db.Integer,default = 1)
    timetabledclasses = db.relationship("TimetabledClass",single_parent=True, cascade = 'all,delete-orphan')
    def __init__(self, subcode, subname, year, studyperiod,repeats = 1):
        self.subcode = subcode
        self.subname = subname
        self.year = year
        self.studyperiod = studyperiod
        self.repeats = repeats


class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer, primary_key=True)
    studentcode = db.Column(db.String(50), nullable=False)
    firstname = db.Column(db.String(50), nullable=False)
    lastname = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(50), nullable=True)
    year = db.Column(db.Integer, nullable=False)
    studyperiod = db.Column(db.String(50), nullable=False)
    subjects = db.relationship("Subject", secondary=substumap, backref=db.backref('students'))
    timetabledclasses = db.relationship("TimetabledClass", secondary=stutimetable,
                                        backref=db.backref('students'))
    def __init__(self, studentcode, firstname, lastname, year, studyperiod):
        self.studentcode = studentcode
        self.firstname = firstname
        self.lastname = lastname
        self.name = firstname + " " + lastname
        self.year = year
        self.studyperiod = studyperiod


class Timetable(db.Model):
    __tablename__ = 'timetable'
    id = db.Column(db.Integer, primary_key=True)
    studyperiod = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    key = db.Column(db.String(50), nullable=True)
    timeslots = db.relationship("Timeslot", single_parent = True, cascade = 'all,delete-orphan')
    def __init__(self, year, studyperiod, key=""):
        self.studyperiod = studyperiod
        self.year = year
        self.key = key




class Tutor(db.Model):
    __tablename__ = 'tutors'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    studyperiod = db.Column(db.String(50), nullable=False)
    subjects = db.relationship("Subject", secondary=subtutmap,
                               backref=db.backref('tutor', uselist=False,lazy='joined'))
    availabletimes = db.relationship("Timeslot", secondary=tutoravailabilitymap,
                                     backref=db.backref('availabiletutors'))
    timetabledclasses = db.relationship("TimetabledClass",single_parent=True,cascade ="all,delete-orphan", backref=db.backref('teacher'))
    def __init__(self, name, year, studyperiod):
        self.name = name
        self.year = year
        self.studyperiod = studyperiod

    def get_teaching_times(self):
        teachingtimes = []
        for timeclass in self.timetabledclasses:
            teachingtimes.append(timeclass.timeslot)
        return teachingtimes


class TimetabledClass(db.Model):
    __tablename__ = 'timetabledclass'
    id = db.Column(db.Integer, primary_key=True)
    studyperiod = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    subjectid = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    subject = db.relationship("Subject")
    timetable = db.Column(db.Integer, db.ForeignKey('timetable.id'))
    time = db.Column(db.Integer, db.ForeignKey('timeslots.id'))
    tutor = db.Column(db.Integer, db.ForeignKey('tutors.id'))

    def __init__(self, studyperiod, year, subjectid, timetable, time, tutor):
        self.studyperiod = studyperiod
        self.year = year
        self.subjectid = subjectid
        self.timetable = timetable
        self.time = time
        self.tutor = tutor


class Timeslot(db.Model):
    __tablename__ = 'timeslots'
    id = db.Column(db.Integer, primary_key=True)
    studyperiod = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    timetable = db.Column(db.Integer, db.ForeignKey('timetable.id'))
    day = db.Column(db.String(50), nullable=False)
    daynumeric = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)
    timetabledclasses = db.relationship("TimetabledClass", backref = db.backref('timeslot'),single_parent=True,cascade ='all,delete-orphan')
    def __init__(self, studyperiod, year, timetable, day, time):
        self.studyperiod = studyperiod
        self.year = year
        self.timetable = timetable
        self.day = day
        self.daynumeric = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"].index(day)
        self.time = time


class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer, primary_key=True)
    subjectid = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    classtime = db.Column(db.DateTime, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    studyperiod = db.Column(db.String(50), nullable=False)
    repeat = db.Column(db.Integer, default=1)
    attendees = db.relationship("Student", secondary=stuattendance)

    def __init__(self, subjectid, tutorid, classtime, year, studyperiod, repeat):
        self.subjectid = subjectid
        self.tutorid = tutorid
        self.classtime = classtime
        self.year = year
        self.studyperiod = studyperiod
        self.repeat = repeat


# class TutorAvailability(db.Model):
#    __tablename__ = 'tutoravailability'
#    id = db.Column(db.Integer, primary_key=True)
#    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))
#    time1 = db.Column(db.Integer, default=1)
#    time2 = db.Column(db.Integer, default=1)
#    time3 = db.Column(db.Integer, default=1)
#    time4 = db.Column(db.Integer, default=1)
#    time5 = db.Column(db.Integer, default=1)
#    time6 = db.Column(db.Integer, default=1)
#    time7 = db.Column(db.Integer, default=1)
#    time8 = db.Column(db.Integer, default=1)
#    time9 = db.Column(db.Integer, default=1)
#
#    def __init__(self, tutorid, time1, time2, time3, time4, time5, time6, time7, time8, time9):
#        self.tutorid = tutorid
#        self.time1 = time1
#        self.time2 = time2
#        self.time3 = time3
#        self.time4 = time4
#        self.time5 = time5
#        self.time6 = time6
#        self.time7 = time7
#        self.time8 = time8
#        self.time9 = time9


# DATABASE METHODS
db.create_all()
db.mapper(SubStuMap, substumap)
db.mapper(SubTutMap, subtutmap)
db.mapper(StuAttendance, stuattendance)
db.mapper(StuTimetable, stutimetable)
db.mapper(TimeslotClasses, timeslotclassesmap)
db.mapper(TutorAvailability, tutoravailabilitymap)


### APP ROUTES


# Route that will process the file upload
@app.route('/uploadstudentdata', methods=['POST'])
def uploadstudentdata():
    try:
        filename2 = upload(request.files['file'])
        populate_students(filename2)
        msg = "Completed Successfully"
    except:
        msg = "There was an error with the upload, please try again"
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
    return render_template("uploadstudentdata.html", msg=msg)


@app.route('/uploadtimetableclasslists', methods=['GET', 'POST'])
def uploadtimetableclasslists():
    if request.method == 'POST':
        filename2 = upload(request.files['file'])
        populate_timetabledata(filename2)
        msg = "Completed Successfully"
    return render_template("uploadtimetabledata.html")


@app.route('/viewclashreport')
def viewclashreport():
    return render_template("viewclashreport.html")


@app.route('/viewclashesajax')
def viewclashreportajax():
    timeslots = get_timeslots()
    clashes = {}
    for timeslot in timeslots:
        clashestimeslot = {}
        students = []
        for timeclass in timeslot.timetabledclasses:
            for student in timeclass.students:
                if student in students:
                    clashestimeslot[student.id] = {}
                    clashestimeslot[student.id]['student'] = student
                    clashestimeslot[student.id]['timeslot'] = timeslot
                students.append(student)
        clashes[timeslot.id] = clashestimeslot
    data2 = []
    for row in clashes.keys():
        if clashes[row] != {}:
            for key in clashes[row].keys():
                data2.append(clashes[row][key])
    for row in data2:
        # row['_sa_instance_state'] = ""
        row['timeslot'] = row['timeslot'].__dict__
        row['timeslot']['_sa_instance_state'] = ""
        row['student'] = row['student'].__dict__
        row['student']['_sa_instance_state'] = ""
        row['timeslot']['availabiletutors'] = []
        row['timeslot']['timetabledclasses'] = []
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'



@app.route('/updateadminsettings', methods=['POST'])
def updateadminsettings():
    year = request.form['year']
    studyperiod = request.form['studyperiod']
    update_year(year)
    update_studyperiod(studyperiod)
    return render_template('admin.html', admin=getadmin())


@app.route('/uploadtutordata', methods=['POST'])
def uploadtutordata():

    filename2 = upload(request.files['file'])
    print("Uploaded Successfully")
    populate_tutors(filename2)
    print("Populated Tutors")
    # os.remove(filename2)
    msg = "Completed successfully"
    return render_template("uploadtutordata.html", msg=msg)

@app.route('/uploadtutoravailabilities', methods=['POST'])
def upload_tutor_availabilities():
    filename2 = upload(request.files['file'])
    print("Uploaded Successfully")
    populate_availabilities(filename2)
    msg2 = "Completed Successfully"
    return render_template("uploadtutordata.html",msg2=msg2)

@app.route('/runtimetabler')
def run_timetabler():
    return render_template("runtimetabler.html", tutors=get_tutors(), timeslots=get_timeslots())

@app.route('/timetable')
def view_timetable():
    return render_template('viewtimetable.html')


@app.route('/timeslots')
def view_timeslots():
    return render_template('viewtimeslots.html')


@app.route('/removeclass?classid=<classid>')
def remove_class(classid):
    specificclass = Class.query.get(classid)
    sub = Subject.query.get(specificclass.subjectid)
    db.session.delete(specificclass)
    db.session.commit()
    return view_subject_template(sub.subcode)


@app.route('/updatetutoravailability?tutorid=<tutorid>', methods=['GET', 'POST'])
def update_tutor_availability(tutorid):
    tutor = Tutor.query.get(tutorid)
    tutor.availabletimes = []
    for (k, v) in request.form.items():

        if k.find('time') != -1:
            id = int(k.split('/')[1])
            timeslot = Timeslot.query.get(id)
            tutor.availabletimes.append(timeslot)
    db.session.commit()
    msg = ""
    # time1 = checkboxvalue(request.form.get('time1'))
    # time2 = checkboxvalue(request.form.get('time2'))
    # time3 = checkboxvalue(request.form.get('time3'))
    # time4 = checkboxvalue(request.form.get('time4'))
    # time5 = checkboxvalue(request.form.get('time5'))
    # time6 = checkboxvalue(request.form.get('time6'))
    # time7 = checkboxvalue(request.form.get('time7'))
    # time8 = checkboxvalue(request.form.get('time8'))
    # time9 = checkboxvalue(request.form.get('time9'))
    # availability = [time1, time2, time3, time4, time5, time6, time7, time8, time9]
    #msg = set_tutor_availability(tutorid, availability)
    return view_tutor_template(tutorid, msg3=msg)


@app.route('/updatetutoravailabilityajax', methods=['POST'])
def update_tutor_availability_ajax():
    timeslotid = int(request.form['timeslotid'])
    tutorid = int(request.form['tutorid'])
    timeslot = Timeslot.query.get(timeslotid)
    tutor = Tutor.query.get(tutorid)
    if timeslot in tutor.availabletimes:
        tutor.availabletimes.remove(timeslot)
    else:
        tutor.availabletimes.append(timeslot)
    db.session.commit()
    return json.dumps("Done")


@app.route('/updatestudentscheduledclassajax', methods=['POST'])
def update_student_scheduled_class_ajax():
    timeclassid = int(request.form['timeclassid'])
    studentid = int(request.form['studentid'])
    timeclass = TimetabledClass.query.get(timeclassid)
    student = Student.query.get(studentid)
    subject = timeclass.subject
    if student not in timeclass.students:
        for timeclass2 in subject.timetabledclasses:
            if student in timeclass2.students:
                timeclass2.students.remove(student)
        timeclass.students.append(student)
    db.session.commit()
    return json.dumps("Done")


@app.route('/addsubjecttotutor?tutorid=<tutorid>', methods=['GET', 'POST'])
def add_subject_to_tutor(tutorid):
    if request.method == 'POST':
        subcode = request.form['subject']
        msg = linksubjecttutor(tutorid, subcode)
        return view_tutor_template(tutorid, msg)


@app.route('/addclass?subcode=<subcode>', methods=['GET', 'POST'])
def add_class(subcode):
    if request.method == 'GET':
        return render_template('addclass.html', subject=get_subject(subcode),
                               students=get_subject_and_students(subcode))
    elif request.method == 'POST':
        classtime = request.form["date"]
        print(classtime)
        repeat = request.form["repeat"]
        students = get_subject_and_students(subcode)
        attendees = []
        for student in students:
            print(student.studentcode)
            if checkboxvalue(request.form.get(student.studentcode)) == 1:
                attendees.append(student.studentcode)
        add_class_to_db(classtime, subcode, attendees, repeat)
        return view_subject_template(subcode)


@app.route('/addtimetabledclasstosubject?subcode=<subcode>', methods=['POST'])
def add_timetabledclass_to_subject(subcode):
    subject = get_subject(subcode)
    timeslot = Timeslot.query.get(request.form['timeslot'])
    timetable = get_current_timetable()
    if TimetabledClass.query.filter_by(studyperiod=get_current_studyperiod(), year=get_current_year(),
                                       subjectid=subject.id, timetable=timetable, time=timeslot.id,
                                       tutor=subject.tutor.id).first() is None:
        timetabledclass = TimetabledClass(studyperiod=get_current_studyperiod(), year=get_current_year(),
                                          subjectid=subject.id, timetable=timetable, time=timeslot.id,
                                          tutor=subject.tutor.id)
        db.session.add(timetabledclass)
        db.session.commit()
        timetabledclass.students = subject.students
        db.session.commit()
    return view_subject_template(subcode)


@app.route('/viewclass?classid=<classid>')
def view_class(classid):
    classdata = get_class(classid)
    subject = Subject.query.get(classdata.subjectid)
    return render_template('class.html', classdata=classdata, subject=get_subject(subject.subcode),
                           tutor=get_tutor(classdata.tutorid),
                           students=get_subject_and_students(subject.subcode), attendees=get_attendees(classid))


@app.route('/admin')
def admin():
    return render_template('admin.html', admin=getadmin())


@app.route('/addtutortosubject?subcode=<subcode>', methods=['GET', 'POST'])
def add_tutor_to_subject(subcode):
    if request.method == 'POST':
        tutorid = request.form['tutor']
        msg = linksubjecttutor(tutorid, subcode)
        return view_subject_template(subcode, msg)


@app.route('/addtutortosubjecttimetabler?subcode=<subcode>', methods=['GET', 'POST'])
def add_tutor_to_subject_timetabler(subcode):
    if request.method == 'POST':
        tutorid = request.form['tutor']
        msg = linksubjecttutor(tutorid, subcode)
    return render_template("runtimetabler.html", tutors=get_tutors(), timeslots=get_timeslots())


@app.route('/removesubjectfromtutor?tutorid=<tutorid>&subcode=<subcode>')
def remove_subject_from_tutor(tutorid, subcode):
    msg = unlinksubjecttutor(tutorid, subcode)
    return view_tutor_template(tutorid, msg2=msg)


@app.route('/removesubjectfromtutortimetabler?tutorid=<tutorid>&subcode=<subcode>')
def remove_subject_from_tutor_timetabler(tutorid, subcode):
    msg = unlinksubjecttutor(tutorid, subcode)
    return render_template("runtimetabler.html", timeslots=get_timeslots(), tutors=get_tutors())


@app.route('/removetutorfromsubject?tutorid=<tutorid>&subcode=<subcode>')
def remove_tutor_from_subject(tutorid, subcode):
    msg = unlinksubjecttutor(tutorid, subcode)
    return view_subject_template(subcode, msg)


@app.route('/removesubjectfromstudent?studentcode=<studentcode>&subcode=<subcode>')
def remove_subject_from_student(studentcode, subcode):
    msg = unlinksubjectstudent(studentcode, subcode)
    return view_student_template(studentcode, msg)


@app.route('/removetimetabledclass?timetabledclassid=<timetabledclassid>')
def remove_timetabled_class(timetabledclassid):
    timetabledclass = TimetabledClass.query.get(timetabledclassid)
    db.session.delete(timetabledclass)
    db.session.commit()
    return render_template("viewtimetable.html")


@app.route('/removetimetabledclasssubject?timetabledclassid=<timetabledclassid>')
def remove_timetabled_class_subject(timetabledclassid):
    timetabledclass = TimetabledClass.query.get(timetabledclassid)
    subject = timetabledclass.subject
    db.session.delete(timetabledclass)
    db.session.commit()
    return view_subject_template(subject.subcode)

@app.route('/removestudentfromsubject?studentcode=<studentcode>&subcode=<subcode>')
def remove_student_from_subject(studentcode, subcode):
    msg = unlinksubjectstudent(studentcode, subcode)
    return view_subject_template(subcode, msg)


@app.route('/addsubjecttostudent?studentcode=<studentcode>', methods=['POST'])
def add_subject_to_student(studentcode):
    subcode = request.form['subject']
    msg = linksubjectstudent(studentcode, subcode)
    return view_student_template(studentcode, msg=msg)


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/rolls')
def view_rolls():
    return render_template('rolls.html')


@app.route('/deleteallclasses')
def delete_all_classes():
    timetabledclasses = TimetabledClass.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                        timetable=get_current_timetable()).all()
    print(timetabledclasses)
    for timeclass in timetabledclasses:
        db.session.delete(timeclass)
        db.session.commit()
    timetabledclasses = TimetabledClass.query.filter_by(year=get_current_year(),
                                                        studyperiod=get_current_studyperiod(),
                                                        timetable=get_current_timetable()).all()
    print(timetabledclasses)
    return "Done"

@app.route('/subjects')
def view_subjects():
    return render_template('subjects.html')


@app.route('/updatesubjectrepeats', methods=['POST'])
def update_subject_repeats():
    subject = Subject.query.get(int(request.form['subject']))
    subject.repeats = int(request.form['repeats'])
    db.session.commit()
    return "Done"

@app.route('/viewsubjectsajax')
def viewsubjects_ajax():
    data = Subject.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
        row['students'] = []
        row['tutor'] = []
    print(data2)
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'

@app.route('/viewcurrentmappedsubjectsajax')
def viewcurrentmappedsubjects_ajax():
    data = Subject.query.filter(Subject.year==get_current_year(), Subject.studyperiod==get_current_studyperiod(), Subject.tutor!= None).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
        row['students'] = []
        row['tutor'] = row['tutor'].__dict__
        row['tutor']['_sa_instance_state']=""
    print(data2)
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/vieweligiblesubjectsajax')
def vieweligiblesubjects_ajax():
    data = Subject.query.options(joinedload('students')).filter(Subject.year == get_current_year(),
                                                                Subject.studyperiod == get_current_studyperiod(),
                                                                Subject.tutor == None).all()
    data2 = []
    for subject in data:
        if len(subject.students) >= 3:
            data2.append(subject)
    data3 = []
    for row in data2:
        data3.append(row.__dict__)
    for row in data3:
        row['_sa_instance_state'] = ""
        row['students'] = len(row['students'])
    print(data3)
    data = json.dumps(data3)
    return '{ "data" : ' + data + '}'



@app.route('/viewtimeslotsajax')
def viewtimeslots_ajax():
    data = get_timeslots()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
        row['timetabledclasses'] = []
        row['tutor'] = []
        row['availabiletutors'] = []
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'



@app.route('/viewtimetableajax')
def viewtimetable_ajax():
    data = TimetabledClass.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).all()
    data2 = []

    for row3 in data:
        data2.append(row3.__dict__)
    for i in range(len(data2)):
        data2[i]['timeslot'] = Timeslot.query.get(data2[i]['time'])
        data2[i]['tutor'] = Tutor.query.filter_by(id=data2[i]['tutor']).first()
        data2[i]['subject'] = Subject.query.filter_by(id=data2[i]['subjectid']).first()
    for i in range(len(data2)):
        data2[i]['tutor'] = data2[i]['tutor'].__dict__
        data2[i]['tutor']['_sa_instance_state'] = ""
        data2[i]['subject'] = data2[i]['subject'].__dict__
        data2[i]['subject']['_sa_instance_state'] = ""
        data2[i]['subject']['students'] = []
        data2[i]['subject']['tutor'] = ""
        data2[i]['students'] = []
        data2[i]['_sa_instance_state'] = ""
        data2[i]['timeslot'] = data2[i]['timeslot'].__dict__
        data2[i]['timeslot']['_sa_instance_state'] = ""
        data2[i]['timeslot']['availabiletutors'] = []
        data2[i]['timeslot']['timetabledclasses'] = []
        data2[i]['timetabledclasses'] = []
    print(data2)
    data = json.dumps(data2)

    return '{ "data" : ' + data + '}'

@app.route('/viewtutorsajax')
def viewtutors_ajax():
    data = Tutor.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/viewstudentsajax')
def viewstudents_ajax():
    data = Student.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod())
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/addsubject', methods=['GET', 'POST'])
def add_subject():
    if request.method == 'GET':
        return render_template('addsubject.html')
    elif request.method == 'POST':
        try:
            subcode = request.form['subcode']
            subname = request.form['subname']
            if Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                       studyperiod=get_current_studyperiod()).first() == None:
                sub = Subject(subcode=subcode, subname=subname, studyperiod=get_current_studyperiod(),
                              year=get_current_studyperiod())
                db.session.add(sub)
                db.session.commit()
            msg = "Record successfully added"
        except:
            msg = "Error"
        finally:
            return render_template("subjects.html", msg=msg, rows=get_subjects())


@app.route('/addtimeslot', methods=['GET', 'POST'])
def add_timeslot():
    if request.method == 'GET':
        return render_template("addtimeslot.html")
    else:
        day = request.form['day']
        time = request.form['time']
        print(time)
        if Timeslot.query.filter_by(year=get_current_year(), timetable=get_current_timetable(),
                                    studyperiod=get_current_studyperiod(), day=day, time=time).first() is None:
            timeslot = Timeslot(studyperiod=get_current_studyperiod(), year=get_current_year(),
                                timetable=get_current_timetable(), day=day, time=time)
            db.session.add(timeslot)
            db.session.commit()

        return render_template("viewtimeslots.html")


@app.route('/subject?subcode=<subcode>')
def view_subject(subcode):
    return view_subject_template(subcode)


@app.route('/removesubject?subcode=<subcode>')
def remove_subject(subcode):
    try:
        sub = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                      studyperiod=get_current_studyperiod()).first()
        db.session.delete(sub)
        db.session.commit()
        msg = "Completed Successfully"
        return render_template("subjects.html", rows=get_subjects(), msg=msg)
    except:
        msg = "Error"
        return render_template("subjects.html", rows=get_subjects(), msg=msg)


@app.route('/removetutor?tutorid=<tutorid>')
def remove_tutor(tutorid):
    try:
        tut = Tutor.query.get(tutorid)
        db.session.delete(tut)
        db.session.commit()
        msg = "Completed Successfully"
        return render_template("viewtutors.html", rows=get_tutors(), msg=msg)
    except:
        msg = "Error"
        return render_template("viewtutors.html", rows=get_tutors(), msg=msg)


@app.route('/removetimeslot?timeslotid=<timeslotid>')
def remove_timeslot(timeslotid):
    timeslot = Timeslot.query.get(timeslotid)
    print(timeslot.day)
    db.session.delete(timeslot)
    db.session.commit()
    return render_template("viewtimeslots.html")

@app.route('/viewtutors')
def view_tutors():
    return render_template('viewtutors.html', rows=get_tutors())


@app.route('/viewstudents')
def view_students():
    return render_template('viewstudents.html', rows=get_students())


@app.route('/viewstudent?studentcode=<studentcode>')
def view_student(studentcode):
    return view_student_template(studentcode)


@app.route('/runtimetableprogram')
def run_timetable_program():
    preparetimetable()
    return "Done"

@app.route('/viewtutor?tutorid=<tutorid>')
def view_tutor(tutorid):
    return view_tutor_template(tutorid)


@app.route('/addtutor', methods=['GET', 'POST'])
def add_tutor():
    if request.method == 'GET':
        return render_template('addtutor.html')
    elif request.method == 'POST':
        try:
            name = request.form['name'].strip()
            year = get_current_year()
            studyperiod = get_current_studyperiod()
            if Tutor.query.filter_by(name=name, year=year,
                                     studyperiod=studyperiod).first() is None:
                tut = Tutor(name=name, year=year,
                            studyperiod=studyperiod)
                db.session.add(tut)
                db.session.commit()
            msg = "Record successfully added"
        except:
            msg = "error in insert operation"
        finally:
            return render_template("viewtutors.html", msg=msg, rows=get_tutors())


@app.route('/uploadstudentdata')
def upload_student_data():
    return render_template('uploadstudentdata.html')


@app.route('/uploadtutordata')
def upload_tutor_data():
    return render_template('uploadtutordata.html')


@app.route('/updatestudentattendance?subcode=<subcode>', methods=['POST'])
def update_student_attendance(subcode):
    subject = get_subject(subcode)
    for specificclass in subject.classes:
        specificclass.attendees = []
    dates = {}
    times = {}
    for (k, v) in request.form.items():
        if v != '':
            if "classdate" not in k:
                v = v.split('/')
                classid = int(v[0])
                studentid = int(v[1])
                specificclass = Class.query.get(classid)
                specificclass.attendees.append(Student.query.get(studentid))
            else:
                k = k.split('/')
                v = v.split('/')
                if (k[1] == 'date'):
                    dates[int(k[0].split('classdate')[1])] = v
                else:
                    times[int(k[0].split('classdate')[1])] = v

        db.session.commit()
    for key, value in dates.items():
        classtime = dates[key] + times[key]
        classtime = classtime[0] + "T" + classtime[1]
        classtime = datetime.strptime(classtime, '%Y-%m-%dT%H:%M')
        specificclass = Class.query.get(key)
        specificclass.classtime = classtime
        db.session.commit()
    return view_subject_template(subcode)


# HELPER METHODS
def get_tutor(tutorid):
    return Tutor.query.get(tutorid)


def get_student(studentcode):
    return Student.query.filter_by(studentcode=studentcode, year=get_current_year(),
                                   studyperiod=get_current_studyperiod()).first()


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


def view_subject_template(subcode, msg=""):
    return render_template("subject.html", rows=get_subject(subcode), students=get_subject_and_students(subcode),
                           tutor=get_subject_and_tutor(subcode), tutors=get_tutors(),
                           classes=get_classes_for_subject(subcode), attendees=get_attendees_for_subject(subcode),
                           msg=msg, subject=get_subject(subcode), times=find_possible_times(subcode),
                           timeslots=get_timeslots(),
                           timetabledclasses=get_timetabled_classes(subcode))


def get_classes_for_subject(subcode):
    sub = get_subject(subcode)
    results = Class.query.filter_by(subjectid=sub.id, year=get_current_year(),
                                    studyperiod=get_current_studyperiod()).all()
    return sorted(results, key=attrgetter('classtime'))


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


def view_tutor_template(tutorid, msg="", msg2="", msg3=""):
    return render_template('tutor.html', tutor=get_tutor(tutorid), eligiblesubjects=get_subjects(),
                           subjects=get_tutor_and_subjects(tutorid), timeslots=get_timeslots(),
                           availability=get_tutor_availability(tutorid),
                           msg=msg, msg2=msg2, msg3=msg3)


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
    xl = pandas.ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        if row['Study Period'] == studyperiod:
            if Student.query.filter_by(studentcode=str(int(row["Student Id"])), year=year,
                                       studyperiod=studyperiod).first() == None:
                student = Student(studentcode=str(int(row["Student Id"])), firstname=row["Given Name"],
                                  lastname=row['Family Name'], year=year, studyperiod=studyperiod)
                db.session.add(student)
                db.session.commit()
            if Subject.query.filter_by(subcode=row["Component Study Package Code"], year=year,
                                       studyperiod=studyperiod).first() == None:
                subject = Subject(subcode=row["Component Study Package Code"],
                                  subname=row["Component Study Package Title"], year=year, studyperiod=studyperiod)
                db.session.add(subject)
                db.session.commit()
            student = Student.query.filter_by(studentcode=str(int(row["Student Id"])), firstname=row["Given Name"],
                                              lastname=row['Family Name'], year=year,
                                              studyperiod=studyperiod).first()
            subject = Subject.query.filter_by(subcode=row["Component Study Package Code"], year=year,
                                              studyperiod=studyperiod).first()
            if db.session.query(substumap).filter(substumap.c.student_id == student.id,
                                                  substumap.c.subject_id == subject.id).first() is None:
                mapping = SubStuMap(student_id=student.id, subject_id=subject.id)
                db.session.add(mapping)
                db.session.commit()


def populate_timetabledata(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    if Timetable.query.filter_by(year=year, studyperiod=studyperiod).first() is None:
        timetable = Timetable(year, studyperiod, "default")
        db.session.add(timetable)
        db.session.commit()
    print("Timetable Created")
    xl = pandas.ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        if Tutor.query.filter_by(year=year, studyperiod=studyperiod, name=row['x3']).first() is None:
            tutor = Tutor(year=year, studyperiod=studyperiod, name=row['x3'])
            db.session.add(tutor)
            db.session.commit()
        tutor = Tutor.query.filter_by(year=year, studyperiod=studyperiod, name=row['x3']).first()
        if Subject.query.filter_by(year=year, studyperiod=studyperiod, subcode=row['x1']).first() is None:
            subject = Subject(year=year, studyperiod=studyperiod, subcode=row['x1'])
            db.session.add(subject)
            db.session.commit()
        subject = Subject.query.filter_by(subcode=row['x1'], year=year, studyperiod=studyperiod).first()
        time2 = row['x4'].split(' ')
        day = time2[0]
        time2 = time2[1]
        time2 = check_time(time2)
        print(day)
        print(time2)
        if Timeslot.query.filter_by(year=year, studyperiod=studyperiod, day=day, time=time2).first() is None:
            timeslot = Timeslot(year = get_current_year(), studyperiod = get_current_studyperiod(),day = day,time = time2,timetable=get_current_timetable())
            db.session.add(timeslot)
            db.session.commit()
        timeslot = Timeslot.query.filter_by(year=year, studyperiod=studyperiod, day=day, time=time2).first()
        timetable = Timetable.query.get(get_current_timetable())
        print(timeslot)
        if TimetabledClass.query.filter_by(studyperiod=studyperiod, year=year, time=timeslot.id, subjectid=subject.id,
                                           timetable=timetable.id).first() is None:
            timetabledclass = TimetabledClass(studyperiod=studyperiod, year=year, subjectid=subject.id,
                                              timetable=timetable.id, time=timeslot.id, tutor=tutor.id)
            db.session.add(timetabledclass)
            db.session.commit()
        timetabledclass = TimetabledClass.query.filter_by(studyperiod=studyperiod, year=year, time=timeslot.id,
                                                          subjectid=subject.id, timetable=timetable.id).first()
        for i in range(5, len(row)):
            if not pandas.isnull(row[i]):
                print(row[i])
                student = Student.query.filter_by(year=year, studyperiod=studyperiod, name=row[i]).first()
                if db.session.query(stutimetable).filter(stutimetable.c.student_id == student.id,
                                                         stutimetable.c.timetabledclass_id == timetabledclass.id).first() is None:
                    mapping = StuTimetable(student_id=student.id, timetabledclass_id=timetabledclass.id)
                    db.session.add(mapping)
                    db.session.commit()






def populate_availabilities(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    timetable = get_current_timetable()
    xl = pandas.ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])
    for index,row in df.iterrows():
        if Tutor.query.filter_by(name=row["Tutor"], year=year, studyperiod=studyperiod).first() is None:
            tutor = Tutor(name=row["Tutor"], year=year, studyperiod=studyperiod)
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
                    timeslot = Timeslot(year=year, studyperiod=studyperiod, timetable=timetable, day=keysplit[0],
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
    xl = pandas.ExcelFile(filename)

    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        if Tutor.query.filter_by(name=row['Tutor'], year=year, studyperiod=studyperiod).first() is None:
            tutor = Tutor(name=row['Tutor'], year=year, studyperiod=studyperiod)
            db.session.add(tutor)
            db.session.commit()

        tutor = Tutor.query.filter_by(name=row['Tutor'], year=year, studyperiod=studyperiod).first()
        if Subject.query.filter_by(subcode=row["Subject Code"], year=year, studyperiod=studyperiod).first() is None:
            subject = Subject(subcode=row["Subject Code"], subname=" ", year=year, studyperiod=studyperiod,
                              repeats=row["Repeats"])
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
    split = tutor["Tutor"].split()
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    tutor = Tutor.query.filter_by(firstname=split[0], lastname=split[1], year=year, studyperiod=studyperiod).first(0)
    return tutor


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
    classdata = Class.query.filter_by(id=classid).first()
    rows = classdata.attendees
    returns = []
    for row in rows:
        returns.append(row.studentcode)
    print(returns)
    return returns


def get_class(classid):
    return Class.query.filter_by(id=classid).first()


def add_class_to_db(classtime, subcode, attendees, repeat=1):
    tutor = get_subject_and_tutor(subcode)
    subject = get_subject(subcode)
    classtime = datetime.strptime(classtime, '%Y-%m-%dT%H:%M')
    if Class.query.filter_by(classtime=classtime, subjectid=subject.id, year=get_current_year(),
                             studyperiod=get_current_studyperiod(), tutorid=tutor.id, repeat=repeat).first() == None:
        specificclass = Class(classtime=classtime, subjectid=subject.id, year=get_current_year(),
                              studyperiod=get_current_studyperiod(), tutorid=tutor.id, repeat=repeat)
        db.session.add(specificclass)
        db.session.commit()
        add_students_to_class(specificclass, attendees)
    return "Completed Successfully"





def add_students_to_class(specificclass, attendees):
    for i in range(len(attendees)):
        student = get_student(attendees[i])
        mapping = StuAttendance(class_id=specificclass.id, student_id=student.id)
        db.session.add(mapping)
    db.session.commit()
    return "Completed Successfully"


def get_attendees_for_subject(subcode):
    subject = get_subject(subcode)
    classes = Class.query.filter_by(subjectid=subject.id).all()
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
    mapping = SubStuMap(student_id=student.id, subject_id=subject.id)
    db.session.add(mapping)
    db.session.commit()
    return "Linked Successfully."


def view_student_template(studentcode, msg=""):
    return render_template('student.html', rows=get_student(studentcode), eligiblesubjects=get_subjects(),
                           subjects=get_student_and_subjects(studentcode), msg=msg)

#TIMETABLE CODE
def runtimetable(STUDENTS, SUBJECTS, TIMES, day, DAYS, TEACHERS, SUBJECTMAPPING, REPEATS, TEACHERMAPPING,
                 TUTORAVAILABILITY, maxclasssize, minclasssize, nrooms):
    print("Running solver")
    model = LpProblem('Timetabling', LpMinimize)
    #Create Variables
    print("Creating Variables")
    assign_vars = LpVariable.dicts("StudentVariables",[(i, j,k,m) for i in STUDENTS for j in SUBJECTS for k in TIMES for m in TEACHERS], 0, 1, LpBinary)
    subject_vars = LpVariable.dicts("SubjectVariables",[(j,k,m) for j in SUBJECTS for k in TIMES for m in TEACHERS], 0, 1, LpBinary)

    #c
    num930classes = LpVariable.dicts("930Classes", [(i) for i in TIMES], lowBound = 0, cat = LpInteger)
    #w
    daysforteachers = LpVariable.dicts("numdaysforteachers", [(i,j) for i in TEACHERS for j in range(len(DAYS))], 0,1,LpBinary)
    #p
    daysforteacherssum = LpVariable.dicts("numdaysforteacherssum", [(i) for i in TEACHERS],0,cat = LpInteger)
    #variables for student clashes
    studenttime = LpVariable.dicts("StudentTime", [(i,j) for i in STUDENTS for j in TIMES],lowBound=0,upBound=1,cat=LpBinary)
    studentsum = LpVariable.dicts("StudentSum", [(i) for i in STUDENTS],0,cat = LpInteger)

    #Count the days that a teacher is rostered on. Make it bigger than a small number times the sum
    #for that particular day.
    for m in TEACHERS:
        for d in range(len(day)):
            model += daysforteachers[(m, d)] >= 0.1 * lpSum(
                subject_vars[(j, k, m)] for j in SUBJECTS for k in DAYS[day[d]])
            model += daysforteachers[(m, d)] <= lpSum(subject_vars[(j, k, m)] for j in SUBJECTS for k in DAYS[day[d]])
    for m in TEACHERS:
        model += daysforteacherssum[(m)] == lpSum(daysforteachers[(m, d)] for d in range(len(day)))

    print("Constraining tutor availability")
    #This bit of code puts in the constraints for the tutor availability.
    #It reads in the 0-1 matrix of tutor availability and constrains that no classes
    # can be scheduled when a tutor is not available.
    #The last column of the availabilities is the tutor identifying number, hence why we have
    #used a somewhat convoluted idea down here.
    for m in TEACHERS:
        for k in TIMES:
            if k not in TUTORAVAILABILITY[m]:
                model += lpSum(subject_vars[(j,k,m)] for j in SUBJECTS) == 0


    #Constraints on subjects for each students
    print("Constraining student subjects")
    for i in STUDENTS:
        for j in SUBJECTS:
            if i in SUBJECTMAPPING[j]:
                model += lpSum(assign_vars[(i,j,k,m)] for k in TIMES for m in TEACHERS) == 1
            else:
                model += lpSum(assign_vars[(i,j,k,m)] for k in TIMES for m in TEACHERS) == 0



    #This code means that students cannot attend a tute when a tute is not running
    #But can not attend a tute if they attend a repeat.
    for i in STUDENTS:
        for j in SUBJECTS:
            for k in TIMES:
                for m in TEACHERS:
                    model += assign_vars[(i,j,k,m)] <= subject_vars[(j,k,m)]


    #Constraints on which tutor can take each class
    #This goes through each list and either constrains it to 1 or 0 depending if
    #the teacher needs to teach that particular class.
    print("Constraining tutor classes")
    for m in TEACHERS:
        for j in SUBJECTS:
            if j in TEACHERMAPPING[m]:
                #THIS WILL BE CHANGED TO NUMBER OF REPEATS
                model+= lpSum(subject_vars[(j,k,m)] for k in TIMES) == REPEATS[j]
            else:
                model += lpSum(subject_vars[(j,k,m)] for k in TIMES) == 0

    #General Constraints on Rooms etc.
    print("Constraining times")
    # For each time cannot exceed number of rooms
    for k in TIMES:
        model += lpSum(subject_vars[(j,k,m)] for j in SUBJECTS for m in TEACHERS) <= nrooms

    #Teachers can only teach one class at a time
    for k in TIMES:
        for m in TEACHERS:
            model += lpSum(subject_vars[(j,k,m)] for j in SUBJECTS) <= 1

    #STUDENT CLASHES
    for i in STUDENTS:
        for k in TIMES:
            model += studenttime[(i,k)] <= lpSum(assign_vars[(i,j,k,m)] for j in SUBJECTS for m in TEACHERS)/2
            model += studenttime[(i, k)] >= 0.3*(0.5*lpSum(assign_vars[(i, j, k, m)] for j in SUBJECTS for m in TEACHERS) -0.5)

    for i in STUDENTS:
        model += studentsum[(i)] == lpSum(studenttime[(i,k)] for k in TIMES)

    #This minimizes the number of 9:30 classes.
    for i in TIMES:
        if i.find('21:30') != -1:
            model += num930classes[(i)] == lpSum(subject_vars[(j,i,m)] for j in SUBJECTS for m in TEACHERS)

        else:
            model += num930classes[(i)] == 0

    print("Setting objective function")

    #Class size constraint
    for j in SUBJECTS:
        for k in TIMES:
            for m in TEACHERS:
                model +=lpSum(assign_vars[(i,j,k,m)] for i in STUDENTS) >= minclasssize*subject_vars[(j,k,m)]
                model += lpSum(assign_vars[(i,j,k,m)] for i in STUDENTS) <= maxclasssize

    #Solving the model
    model += (100*lpSum(studentsum[(i)] for i in STUDENTS) + lpSum(num930classes[(i)] for i in TIMES) + 500*lpSum(daysforteacherssum[(m)] for m in TEACHERS))
    print("Solving Model")
    model.solve()
    print("Complete")
    for j in SUBJECTS:
        subject = Subject.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                          subcode=j).first()
        for k in TIMES:
            timesplit = k.split(' ')
            timeslot = Timeslot.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                timetable=get_current_timetable(), day=timesplit[0],
                                                time=timesplit[1]).first()
            for m in TEACHERS:
                tutor = Tutor.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                              name=m).first()
                if subject_vars[(j, k, m)].varValue == 1:

                    timetabledclass = TimetabledClass(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                      subjectid=subject.id, timetable=get_current_timetable(),
                                                      time=timeslot.id, tutor=tutor.id)
                    db.session.add(timetabledclass)
                    db.session.commit()
                    print(timetabledclass.subject.subname)
                    for i in STUDENTS:

                        if assign_vars[(i, j, k, m)].varValue == 1:
                            student = Student.query.filter_by(year=get_current_year(),
                                                              studyperiod=get_current_studyperiod(), name=i).first()
                            timetabledclass.students.append(student)
                            db.session.commit()

    return model.objective.value()


def preparetimetable():
    print("Preparing Timetable")
    SUBJECTS = []
    SUBJECTMAPPING = {}
    STUDENTS = []
    REPEATS = {}
    TEACHERS = []
    TUTORAVAILABILITY = {}
    TEACHERMAPPING = {}
    allsubjects = Subject.query.filter(Subject.year == get_current_year(),
                                       Subject.studyperiod == get_current_studyperiod(), Subject.tutor != None).all()
    alltutors = []
    for subject in allsubjects:
        SUBJECTMAPPING[subject.subcode] = []
        REPEATS[subject.subcode] = subject.repeats
        SUBJECTS.append(subject.subcode)
        TEACHERS.append(subject.tutor.name)
        if subject.tutor not in alltutors:
            alltutors.append(subject.tutor)
        for student in subject.students:
            STUDENTS.append(student.name)
            SUBJECTMAPPING[subject.subcode].append(student.name)
    STUDENTS = list(set(STUDENTS))
    TEACHERS = list(set(TEACHERS))
    for tutor in alltutors:
        TUTORAVAILABILITY[tutor.name] = []
        TEACHERMAPPING[tutor.name] = []
        for timeslot in tutor.availabletimes:
            TUTORAVAILABILITY[tutor.name].append(timeslot.day + " " + timeslot.time)
        for subject in tutor.subjects:
            TEACHERMAPPING[tutor.name].append(subject.subcode)
    print(TEACHERS)

    maxclasssize = 400
    minclasssize = 1
    nrooms = 12
    TIMES = []
    day = []
    timeslots = Timeslot.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                         timetable=get_current_timetable()).all()
    for timeslot in timeslots:
        TIMES.append(timeslot.day + " " + timeslot.time)
        day.append(timeslot.day)
    day = list(set(day))
    DAYS = {}
    for d in day:
        DAYS[d] = []
    for timeslot in timeslots:
        DAYS[timeslot.day].append(timeslot.day + " " + timeslot.time)
    print("Everything ready")
    executor.submit(runtimetable,STUDENTS, SUBJECTS, TIMES, day, DAYS, TEACHERS, SUBJECTMAPPING, REPEATS, TEACHERMAPPING,
                       TUTORAVAILABILITY, maxclasssize, minclasssize, nrooms)
    return render_template("viewtimetable.html")



if Admin.query.filter_by(key='currentyear').first() == None:
    admin = Admin(key='currentyear', value=2017)
    db.session.add(admin)
    db.session.commit()
if Admin.query.filter_by(key='studyperiod').first() == None:
    study = Admin(key='studyperiod', value='Semester 2')
    db.session.add(study)
    db.session.commit()

if Admin.query.filter_by(key='timetable').first() is None:
    timetable = Timetable(year=get_current_year(), studyperiod=get_current_studyperiod(), key="default")
    db.session.add(timetable)
    db.session.commit()
    timetableadmin = Admin(key='timetable', value=timetable.id)
    db.session.add(timetableadmin)
    db.session.commit()


if __name__ == '__main__':
    app.run(debug=True)
