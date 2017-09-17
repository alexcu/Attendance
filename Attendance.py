import json
from concurrent.futures import ThreadPoolExecutor
from operator import attrgetter

import pandas
from flask import Flask
from flask import render_template, redirect, url_for
from flask_bcrypt import Bcrypt
from flask_sqlalchemy import *
from pulp import *
from sqlalchemy.orm import joinedload

# DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
executor = ThreadPoolExecutor(2)
app = Flask(__name__)

# WINDOWS
# app.config['UPLOAD_FOLDER'] = 'D:/Downloads/uploads/'
# LINUX
app.config['UPLOAD_FOLDER'] = 'C:/Users/justi/Downloads/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['xls', 'xlsx'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/justi/Dropbox/Justin/Documents/Python/database50.db'
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

class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer, primary_key=True)
    subcode = db.Column(db.String(50), nullable=False)
    subname = db.Column(db.String(50), nullable=False)
    year = db.Column(db.Integer, nullable=False)
    studyperiod = db.Column(db.String(50), nullable=False)
    classes = db.relationship("Tutorial", backref=db.backref('subject'), single_parent=True, cascade='all,delete-orphan')
    repeats = db.Column(db.Integer,default = 1)
    timetabledclasses = db.relationship("TimetabledClass",single_parent=True, cascade = 'all,delete-orphan')
    def __init__(self, subcode, subname, year, studyperiod,repeats = 1):
        self.subcode = subcode
        self.subname = subname
        self.year = year
        self.studyperiod = studyperiod
        self.repeats = repeats

    def get_attendance_rate(self):
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
    timetabledclasses = db.relationship("TimetabledClass",single_parent=True,cascade ="all,delete-orphan", backref=db.backref('tutor'))
    classes = db.relationship("Tutorial", single_parent=True, cascade='all,delete-orphan', backref=db.backref('tutor'))
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
    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))

    def __init__(self, studyperiod, year, subjectid, timetable, time, tutorid):
        self.studyperiod = studyperiod
        self.year = year
        self.subjectid = subjectid
        self.timetable = timetable
        self.time = time
        self.tutorid = tutorid


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


class Tutorial(db.Model):
    __tablename__ = 'tutorials'
    id = db.Column(db.Integer, primary_key=True)
    subjectid = db.Column(db.Integer, db.ForeignKey('subjects.id'))
    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    week = db.Column(db.Integer, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    studyperiod = db.Column(db.String(50), nullable=False)
    attendees = db.relationship("Student", secondary=stuattendance)

    def __init__(self, subjectid, tutorid, week, year, studyperiod):
        self.subjectid = subjectid
        self.tutorid = tutorid
        self.week = week
        self.year = year
        self.studyperiod = studyperiod




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


@app.route('/tutoravailability')
def managetutoravailability():
    return render_template("tutoravailability.html", timeslots=get_timeslots(), tutors=get_tutors())


@app.route('/numbereligiblesubjectsmappedajax')
def num_eligible_subjects_mapped():
    subjects = Subject.query.filter(Subject.tutor != None, Subject.year == get_current_year(),
                                    Subject.studyperiod == get_current_studyperiod()).all()
    eligiblesubjects = []
    allsubjects = Subject.query.filter(Subject.tutor == None, Subject.year == get_current_year(),
                                       Subject.studyperiod == get_current_studyperiod()).all()
    for subject in allsubjects:
        if len(subject.students) >= 3:
            eligiblesubjects.append(subject)

    data = {}
    data['Eligible Subjects'] = len(eligiblesubjects)
    data['Mapped Subjects'] = len(subjects)
    data = json.dumps(data)
    return data

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


@app.route('/deletetutorial?tutorialid=<tutorialid>')
def delete_tutorial(tutorialid):
    specificclass = Tutorial.query.get(tutorialid)
    sub = Subject.query.get(specificclass.subjectid)
    db.session.delete(specificclass)
    db.session.commit()
    return redirect(url_for('view_subject', subcode=sub.subcode))

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


@app.route('/updatestudentclassattendanceajax', methods=['POST'])
def update_student_class_attendance_ajax():
    classid = int(request.form['classid'])
    studentid = int(request.form['studentid'])
    tutorial = Tutorial.query.get(classid)
    student = Student.query.get(studentid)
    if student not in tutorial.attendees:
        tutorial.attendees.append(student)
        db.session.commit()
    else:
        tutorial.attendees.remove(student)
        db.session.commit()
    return json.dumps("Done")


@app.route('/addsubjecttotutor?tutorid=<tutorid>', methods=['GET', 'POST'])
def add_subject_to_tutor(tutorid):
    if request.method == 'POST':
        subcode = request.form['subject']
        msg = linksubjecttutor(tutorid, subcode)
        return redirect(url_for('view_tutor', tutorid=tutorid))



@app.route('/addtimetabledclasstosubject?subcode=<subcode>', methods=['POST'])
def add_timetabledclass_to_subject(subcode):
    subject = get_subject(subcode)
    timeslot = Timeslot.query.get(request.form['timeslot'])
    timetable = get_current_timetable()
    if TimetabledClass.query.filter_by(studyperiod=get_current_studyperiod(), year=get_current_year(),
                                       subjectid=subject.id, timetable=timetable, time=timeslot.id,
                                       tutorid=subject.tutor.id).first() is None:
        timetabledclass = TimetabledClass(studyperiod=get_current_studyperiod(), year=get_current_year(),
                                          subjectid=subject.id, timetable=timetable, time=timeslot.id,
                                          tutorid=subject.tutor.id)
        db.session.add(timetabledclass)
        db.session.commit()
        if len(subject.timetabledclasses) ==1:
            timetabledclass.students = subject.students
            db.session.commit()
    return redirect(url_for('view_subject', subcode=subcode))


@app.route('/admin')
def admin():
    return render_template('admin.html', admin=getadmin())


@app.route('/addtutortosubject?subcode=<subcode>', methods=['GET', 'POST'])
def add_tutor_to_subject(subcode):
    if request.method == 'POST':
        tutorid = request.form['tutor']
        msg = linksubjecttutor(tutorid, subcode)
        return redirect(url_for('view_subject', subcode=subcode))


@app.route('/addtutortosubjecttimetabler?subcode=<subcode>', methods=['GET', 'POST'])
def add_tutor_to_subject_timetabler(subcode):
    if request.method == 'POST':
        tutorid = request.form['tutor']
        msg = linksubjecttutor(tutorid, subcode)
    return redirect("/runtimetabler")


@app.route('/removesubjectfromtutor?tutorid=<tutorid>&subcode=<subcode>')
def remove_subject_from_tutor(tutorid, subcode):
    msg = unlinksubjecttutor(tutorid, subcode)
    return redirect(url_for('view_tutor', tutorid=tutorid))


@app.route('/removesubjectfromtutortimetabler?tutorid=<tutorid>&subcode=<subcode>')
def remove_subject_from_tutor_timetabler(tutorid, subcode):
    msg = unlinksubjecttutor(tutorid, subcode)
    return redirect("/runtimetabler")


@app.route('/removetutorfromsubject?tutorid=<tutorid>&subcode=<subcode>')
def remove_tutor_from_subject(tutorid, subcode):
    msg = unlinksubjecttutor(tutorid, subcode)
    return redirect(url_for('view_subject', subcode=subcode))


@app.route('/removesubjectfromstudent?studentcode=<studentcode>&subcode=<subcode>')
def remove_subject_from_student(studentcode, subcode):
    msg = unlinksubjectstudent(studentcode, subcode)
    return redirect(url_for('view_student', studentcode=studentcode))


@app.route('/removetimetabledclass?timetabledclassid=<timetabledclassid>')
def remove_timetabled_class(timetabledclassid):
    timetabledclass = TimetabledClass.query.get(timetabledclassid)
    subject = TimetabledClass.query.get(timetabledclass.subjectid)
    db.session.delete(timetabledclass)
    db.session.commit()
    if len(subject.timetabledclasses) == 1:
        for tutorial in subject.timetabledclasses:
            tutorial.students = subject.students
            db.session.commit()
    return redirect("/timetable")


@app.route('/removetimetabledclasssubject?timetabledclassid=<timetabledclassid>')
def remove_timetabled_class_subject(timetabledclassid):
    timetabledclass = TimetabledClass.query.get(timetabledclassid)
    subject = timetabledclass.subject
    db.session.delete(timetabledclass)
    db.session.commit()
    if len(subject.timetabledclasses) == 1:
        for tutorial in subject.timetabledclasses:
            tutorial.students = subject.students
            db.session.commit()
    return redirect(url_for('view_subject', subcode=subject.subcode))

@app.route('/removestudentfromsubject?studentcode=<studentcode>&subcode=<subcode>')
def remove_student_from_subject(studentcode, subcode):
    msg = unlinksubjectstudent(studentcode, subcode)
    return redirect(url_for('view_subject', subcode=subcode))


@app.route('/addsubjecttostudent?studentcode=<studentcode>', methods=['POST'])
def add_subject_to_student(studentcode):
    subcode = request.form['subject']
    msg = linksubjectstudent(studentcode, subcode)
    return redirect(url_for('view_student', studentcode=studentcode))


@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/deleteallclasses')
def delete_all_classes():
    timetabledclasses = TimetabledClass.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                        timetable=get_current_timetable()).all()
    for timeclass in timetabledclasses:
        db.session.delete(timeclass)
        db.session.commit()
    timetabledclasses = TimetabledClass.query.filter_by(year=get_current_year(),
                                                        studyperiod=get_current_studyperiod(),
                                                        timetable=get_current_timetable()).all()
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
    data = Subject.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).options(
        joinedload('students')).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
        row['students'] = len(row['students'])
        row['tutor'] = []
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/updateclasstimeajax', methods=['POST'])
def update_class_time_ajax():
    classid = int(request.form['classid'])
    week = int(request.form['week'])
    tutorial = Tutorial.query.get(classid)
    tutorial.week = week
    db.session.commit()
    print(tutorial.week)
    return json.dumps("Done")


@app.route('/createnewclassajax', methods=['POST'])
def create_new_class_ajax():
    subjectid = int(request.form['subjectid'])
    subject = Subject.query.get(subjectid)
    tutorial = Tutorial(year=get_current_year(), studyperiod=get_current_studyperiod(), subjectid=subjectid,
                     week = 3, tutorid=subject.tutor.id)
    db.session.add(tutorial)
    db.session.commit()
    return json.dumps(tutorial.id)

@app.route('/viewcurrentmappedsubjectsajax')
def viewcurrentmappedsubjects_ajax():
    data = Subject.query.filter(Subject.year == get_current_year(), Subject.studyperiod == get_current_studyperiod(),
                                Subject.tutor != None).options(joinedload('students')).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
        row['students'] = len(row['students'])
        row['tutor'] = row['tutor'].__dict__
        row['tutor']['_sa_instance_state']=""
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
    data = json.dumps(data3)
    return '{ "data" : ' + data + '}'

@app.route('/getrollmarkingajax')
def get_roll_marking_ajax():
    weeks = get_min_max_week()
    minweek = weeks[0]
    maxweek = weeks[1]
    alltutorials = Subject.query.filter(Subject.year == get_current_year(), Subject.studyperiod == get_current_studyperiod(), Subject.tutor != None).all()
    data = {}
    for i in range(minweek, maxweek+1):
        week = i
        tutorials = Tutorial.query.filter(Tutorial.year == get_current_year(), Tutorial.studyperiod == get_current_studyperiod(),Tutorial.week == week).all()
        key = "Week " + str(week)
        data[key] = {}
        if len(tutorials) == 0:
            data[key]['Roll Marking'] =0
        else:
            data[key]['Roll Marking'] = 100*round(len(tutorials)/len(alltutorials),2)
    return json.dumps(data)


@app.route('/getstudentattendancerate?studentid=<studentid>')
def get_student_attendance_rate_ajax(studentid):
    student = Student.query.get(studentid)
    subjects = [subject for subject in student.subjects if subject.tutor is not None]
    weeks = get_min_max_week()
    minweek = weeks[0]
    maxweek = weeks[1]
    data = {}
    cumtotalclasses = 0
    cumattendedclasses = 0
    for i in range(minweek, maxweek + 1):
        week = i
        key = "Week " + str(week)
        data[key] = {}
        totalclasses = 0
        attendedclasses = 0
        for subject in subjects:
            for tutorial in subject.classes:
                if tutorial.week == i:
                    totalclasses += 1
                    cumtotalclasses += 1
                    if student in tutorial.attendees:
                        attendedclasses += 1
                        cumattendedclasses += 1
        if totalclasses == 0:
            data[key]["Attendance Rate"] = 0
        else:
            data[key]["Attendance Rate"] = 100 * round(attendedclasses / totalclasses, 2)
        if cumtotalclasses == 0:
            data[key]["Cum. Attendance Rate"] = 0
        else:
            data[key]["Cum. Attendance Rate"] = 100 * round(cumattendedclasses / cumtotalclasses, 2)
    return json.dumps(data)

@app.route('/getsubjectattendancerate?subjectid=<subjectid>')
def get_subject_attendance_rate_ajax(subjectid):
    subject = Subject.query.get(subjectid)
    weeks = get_min_max_week()
    minweek = weeks[0]
    maxweek = weeks[1]
    data = {}
    totalstudents = 0
    attendedstudents = 0
    for i in range(minweek, maxweek + 1):
        tutorials = Tutorial.query.filter_by(year = get_current_year(), studyperiod = get_current_studyperiod(), subjectid = subject.id, week = i).options(joinedload('attendees')).all()
        week = i
        key = "Week " + str(week)
        data[key] = {}
        if len(tutorials) > 0:
            totalstudents += len(subject.students)
        for tutorial in tutorials:
            attendedstudents += len(tutorial.attendees)
        if totalstudents == 0:
            data[key]["Attendance Rate"] = 0
        else:
            data[key]["Attendance Rate"] = 100 * round(attendedstudents / totalstudents, 2)

    return json.dumps(data)



@app.route('/getattendanceajax')
def get_attendance_ajax():
    weeks = get_min_max_week()
    minweek = weeks[0]
    maxweek = weeks[1]
    data = {}
    for i in range(minweek, maxweek+1):
        week = i
        tutorials = Tutorial.query.filter(Tutorial.year == get_current_year(), Tutorial.studyperiod == get_current_studyperiod(),Tutorial.week==week).all()
        key = "Week " + str(week)
        numstudents = 0
        numattended = 0
        for tutorial in tutorials:
            numstudents += len(tutorial.subject.students)
            numattended += len(tutorial.attendees)
        data[key] = {}
        if numstudents > 0:
            data[key]['Attendance Rate'] = 100*round(numattended / numstudents,2)
        else:
            data[key]['Attendance Rate'] = 0

    return json.dumps(data)


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
    data = TimetabledClass.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).options(
        joinedload('tutor')).all()
    data2 = []

    for row3 in data:
        data2.append(row3.__dict__)
    for i in range(len(data2)):
        data2[i]['timeslot'] = Timeslot.query.get(data2[i]['time'])
        data2[i]['tutor'] = Tutor.query.filter_by(id=data2[i]['tutorid']).first()
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
    data = json.dumps(data2)

    return '{ "data" : ' + data + '}'

@app.route('/viewtutorsajax')
def viewtutors_ajax():
    data = Tutor.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod()).options(
        joinedload('subjects'), joinedload('availabletimes')).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        data3 = []
        data4 = []
        row['_sa_instance_state'] = ""
        for sub in row['subjects']:
            q = sub.__dict__
            q['_sa_instance_state'] = ""
            data3.append(q)
        for time in row['availabletimes']:
            q = time.__dict__
            q['_sa_instance_state'] = ""
            data4.append(q)
        row['subjects'] = data3
        row['availabletimes'] = data4
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
        return redirect('/subjects')
    elif request.method == 'POST':
        subname = request.form['subname']
        subcode = request.form['subcode']
        if Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                   studyperiod=get_current_studyperiod()).first() is None:
            sub = Subject(subcode=subcode, subname=subname, studyperiod=get_current_studyperiod(),
                          year=get_current_year())
            db.session.add(sub)
            db.session.commit()
        msg = "Record successfully added"
        return redirect("/subjects")


@app.route('/addtimeslot', methods=['GET', 'POST'])
def add_timeslot():
    if request.method == 'GET':
        return redirect('/timeslots')
    else:
        day = request.form['day']
        time = request.form['time']
        if Timeslot.query.filter_by(year=get_current_year(), timetable=get_current_timetable(),
                                    studyperiod=get_current_studyperiod(), day=day, time=time).first() is None:
            timeslot = Timeslot(studyperiod=get_current_studyperiod(), year=get_current_year(),
                                timetable=get_current_timetable(), day=day, time=time)
            db.session.add(timeslot)
            db.session.commit()

        return redirect("/timeslots")


@app.route('/subject?subcode=<subcode>')
def view_subject(subcode):
    return view_subject_template(subcode)


@app.route('/removesubject?subcode=<subcode>')
def remove_subject(subcode):
    sub = Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                  studyperiod=get_current_studyperiod()).first()
    db.session.delete(sub)
    db.session.commit()
    msg = "Completed Successfully"
    return redirect("/subjects")


@app.route('/removetutor?tutorid=<tutorid>')
def remove_tutor(tutorid):
    tut = Tutor.query.get(tutorid)
    db.session.delete(tut)
    db.session.commit()
    msg = "Completed Successfully"
    return redirect("/viewtutors")



@app.route('/removetimeslot?timeslotid=<timeslotid>')
def remove_timeslot(timeslotid):
    timeslot = Timeslot.query.get(timeslotid)
    db.session.delete(timeslot)
    db.session.commit()
    return redirect("/viewtimeslots")

@app.route('/viewtutors')
def view_tutors():
    return render_template('viewtutors.html', rows=get_tutors())


@app.route('/viewstudents')
def view_students():
    return render_template('viewstudents.html', rows=get_students())


@app.route('/viewstudent?studentcode=<studentcode>')
def view_student(studentcode):
    return view_student_template(studentcode)


@app.route('/runtimetableprogram', methods=['GET', 'POST'])
def run_timetable_program():
    # addnewtimetable = request.form['addtonewtimetable']
    # print(addnewtimetable == "true")
    preparetimetable()
    return "Done"

@app.route('/viewtutor?tutorid=<tutorid>')
def view_tutor(tutorid):
    return view_tutor_template(tutorid)


@app.route('/addtutor', methods=['GET', 'POST'])
def add_tutor():
    if request.method == 'GET':
        return redirect('viewtutors')
    elif request.method == 'POST':

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
        return redirect("/viewtutors")


@app.route('/uploadstudentdata')
def upload_student_data():
    return render_template('uploadstudentdata.html')


@app.route('/uploadtutordata')
def upload_tutor_data():
    return render_template('uploadtutordata.html')

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


def view_subject_template(subcode, msg=""):
    return render_template("subject.html", rows=get_subject(subcode), students=get_subject_and_students(subcode),
                           tutor=get_subject_and_tutor(subcode), tutors=get_tutors(),
                           classes=get_classes_for_subject(subcode), attendees=get_attendees_for_subject(subcode),
                           msg=msg, subject=get_subject(subcode), times=find_possible_times(subcode),
                           timeslots=get_timeslots(),
                           timetabledclasses=get_timetabled_classes(subcode))


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

        if Timeslot.query.filter_by(year=year, studyperiod=studyperiod, day=day, time=time2).first() is None:
            timeslot = Timeslot(year = get_current_year(), studyperiod = get_current_studyperiod(),day = day,time = time2,timetable=get_current_timetable())
            db.session.add(timeslot)
            db.session.commit()
        timeslot = Timeslot.query.filter_by(year=year, studyperiod=studyperiod, day=day, time=time2).first()
        timetable = Timetable.query.get(get_current_timetable())

        if TimetabledClass.query.filter_by(studyperiod=studyperiod, year=year, time=timeslot.id, subjectid=subject.id,
                                           timetable=timetable.id).first() is None:
            timetabledclass = TimetabledClass(studyperiod=studyperiod, year=year, subjectid=subject.id,
                                              timetable=timetable.id, time=timeslot.id, tutorid=tutor.id)
            db.session.add(timetabledclass)
            db.session.commit()
        timetabledclass = TimetabledClass.query.filter_by(studyperiod=studyperiod, year=year, time=timeslot.id,
                                                          subjectid=subject.id, timetable=timetable.id).first()
        for i in range(5, len(row)):
            if not pandas.isnull(row[i]):

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
    classdata = Tutorial.query.filter_by(id=classid).first()
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
        specificclass = Tutorial(week = week, subjectid=subject.id, year=get_current_year(),
                              studyperiod=get_current_studyperiod(), tutorid=tutor.id)
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
                                                      time=timeslot.id, tutorid=tutor.id)
                    db.session.add(timetabledclass)
                    db.session.commit()

                    for i in STUDENTS:

                        if assign_vars[(i, j, k, m)].varValue == 1:
                            student = Student.query.filter_by(year=get_current_year(),
                                                              studyperiod=get_current_studyperiod(), name=i).first()
                            timetabledclass.students.append(student)
                            db.session.commit()

    return model.objective.value()


def preparetimetable(addtonewtimetable=False):
    # if addtonewtimetable == "true":
    #    timetable = Timetable(get_current_year(),get_current_studyperiod())
    #    db.session.add(timetable)
    #    db.session.commit()
    #    admin = Admin.query.filter_by(key="timetable").first()
    #    admin.value = timetable.id
    #    db.session.commit()
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
