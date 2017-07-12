from flask import Flask
from flask import render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import *
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from flask_bcrypt import Bcrypt
import os, pandas, json
import sqlite3 as sql
app = Flask(__name__)

#WINDOWS
#app.config['UPLOAD_FOLDER'] = 'D:/Downloads/uploads/'
#LINUX
app.config['UPLOAD_FOLDER'] = '/Users/justin/Downloads/uploads/'
#app.config['DB_FILE'] = '/home/justin/PycharmProjects/Attendance/static/database.db'
#app.config['DB_FILE'] = '/home/justin/Dropbox/Justin/Documents/Python/database2.db'
#app.config['DB_FILE'] = 'C:/Users/justi/PycharmProjects/Attendance/static/database.db'
app.config['ALLOWED_EXTENSIONS'] = set(['xls','xlsx', 'csv'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/justin/Dropbox/Justin/Documents/Python/database3.db'
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
    def __init__(self, username,password):
        self.username = username
        self.password = bcrypt.generate_password_hash(password).decode('utf-8')

    def __repr__(self):
        return '<User %r>' % self.username


class Admin(db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer,primary_key=True)
    key = db.Column(db.String(50),unique=True,nullable=False)
    value = db.Column(db.String(50),nullable=False)
    def __init__(self,key,value):
        self.key = key
        self.value = value


class SubStuMap(object):
    def __init__(self,student_id,subject_id):
        self.student_id = student_id
        self.subject_id = subject_id


class SubTutMap(object):
    def __init__(self,tutor_id,subject_id):
        self.tutor_id = tutor_id
        self.subject_id = subject_id

class StuAttendance(object):
    def __init__(self,class_id,student_id):
        self.class_id=class_id
        self.student_id=student_id
##Association tables
substumap = db.Table('substumap',
    db.Column('id',db.Integer,primary_key=True),
    db.Column('student_id', db.Integer, db.ForeignKey('students.id')),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id')),
)

subtutmap = db.Table('subtutmap',
    db.Column('id',db.Integer,primary_key = True),
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id')),
    db.Column('subject_id', db.Integer, db.ForeignKey('subjects.id')),
)

stuattendance = db.Table('stuattendance',
                         db.Column('id',db.Integer,primary_key=True),
                         db.Column('class_id',db.Integer,db.ForeignKey('classes.id')),
                         db.Column('student_id',db.Integer,db.ForeignKey('students.id'))
                         )


class Subject(db.Model):
    __tablename__ = 'subjects'
    id = db.Column(db.Integer,primary_key=True)
    subcode = db.Column(db.String(50),nullable = False)
    subname = db.Column(db.String(50),nullable = False)
    year = db.Column(db.Integer,nullable = False)
    studyperiod = db.Column(db.String(50),nullable = False)

    def __init__(self,subcode,subname,year,studyperiod):
        self.subcode = subcode
        self.subname = subname
        self.year = year
        self.studyperiod = studyperiod

class Student(db.Model):
    __tablename__ = 'students'
    id = db.Column(db.Integer,primary_key=True)
    studentcode = db.Column(db.String(50),nullable = False)
    firstname = db.Column(db.String(50),nullable = False)
    lastname = db.Column(db.String(50),nullable = False)
    year = db.Column(db.Integer,nullable = False)
    studyperiod = db.Column(db.String(50),nullable = False)
    subjects = db.relationship("Subject",secondary = substumap,backref = db.backref('students'))

    def __init__(self,studentcode,firstname,lastname,year,studyperiod):
        self.studentcode = studentcode
        self.firstname = firstname
        self.lastname = lastname
        self.year = year
        self.studyperiod = studyperiod

class Tutor(db.Model):
    __tablename__ = 'tutors'
    id = db.Column(db.Integer, primary_key=True)
    firstname = db.Column(db.String(50),nullable = False)
    lastname = db.Column(db.String(50),nullable = False)
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    year = db.Column(db.Integer,nullable = False)
    studyperiod = db.Column(db.String(50),nullable = False)
    subjects = db.relationship("Subject", secondary = subtutmap,backref = db.backref('tutor',uselist = False))

    def __init__(self,firstname,lastname,email,phone,year,studyperiod):
        self.firstname = firstname
        self.lastname = lastname
        self.email = email
        self.phone = phone
        self.year = year
        self.studyperiod = studyperiod


class Class(db.Model):
    __tablename__ = 'classes'
    id = db.Column(db.Integer,primary_key=True)
    subjectid = db.Column(db.Integer,db.ForeignKey('subjects.id'))
    tutorid = db.Column(db.Integer,db.ForeignKey('tutors.id'))
    datetime = db.Column(db.String(50),nullable=False)
    year = db.Column(db.Integer,nullable=False)
    studyperiod = db.Column(db.String(50),nullable=False)
    attendees = db.relationship("Student",secondary = stuattendance)

    def __init__(self,subjectid,tutorid,datetime,year,studyperiod):
        self.subjectid = subjectid
        self.tutorid = tutorid
        self.datetime = datetime
        self.year = year
        self.studyperiod = studyperiod

class TutorAvailability(db.Model):
    __tablename__ = 'tutoravailability'
    id = db.Column(db.Integer,primary_key=True)
    tutorid = db.Column(db.Integer, db.ForeignKey('tutors.id'))
    time1 = db.Column(db.Integer, default=1)
    time2 = db.Column(db.Integer, default=1)
    time3 = db.Column(db.Integer, default=1)
    time4 = db.Column(db.Integer, default=1)
    time5 = db.Column(db.Integer, default=1)
    time6 = db.Column(db.Integer, default=1)
    time7 = db.Column(db.Integer, default=1)
    time8 = db.Column(db.Integer, default=1)
    time9 = db.Column(db.Integer, default=1)

    def __init__(self,tutorid, time1,time2,time3,time4,time5,time6,time7,time8,time9):
        self.tutorid = tutorid
        self.time1 = time1
        self.time2 = time2
        self.time3 = time3
        self.time4 = time4
        self.time5 = time5
        self.time6 = time6
        self.time7 = time7
        self.time8 = time8
        self.time9 = time9

#DATABASE METHODS
db.create_all()
db.mapper(SubStuMap,substumap)
db.mapper(SubTutMap,subtutmap)
db.mapper(StuAttendance,stuattendance)

if Admin.query.filter_by(key='currentyear').first() == None:
    admin = Admin(key='currentyear',value = 2017)
    db.session.add(admin)
    db.session.commit()
if Admin.query.filter_by(key='studyperiod').first() == None:
    study = Admin(key='studyperiod',value = 'Semester 2')
    db.session.add(study)
    db.session.commit()

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
    return render_template("uploadstudentdata.html", msg = msg)

@app.route('/updateadminsettings', methods=['POST'])
def updateadminsettings():
    year = request.form['year']
    studyperiod = request.form['studyperiod']
    update_year(year)
    update_studyperiod(studyperiod)
    return render_template('admin.html',admin = getadmin())


@app.route('/uploadtutordata',methods = ['POST'])
def uploadtutordata():
    try:
        filename2 = upload(request.files['file'])
        print("Uploaded Successfully")
        populate_tutors(filename2)
        print("Populated Tutors")
        #os.remove(filename2)
        msg = "Completed successfully"
    except:
        msg="There was an error with the upload, please try again."
    return render_template("uploadtutordata.html",msg=msg)


@app.route('/timetable')
def view_timetable():
    return render_template('viewtimetable.html')


@app.route('/removeclass?classid=<classid>')
def remove_class(classid):
    specificclass = Class.query.get(classid)
    subcode = specificclass.subject
    db.session.delete(specificclass)
    db.session.commit()
    return view_subject_template(subcode)



@app.route('/updatetutoravailability?tutorid=<tutorid>',methods=['GET','POST'])
def update_tutor_availability(tutorid):

    time1 = checkboxvalue(request.form.get('time1'))
    time2 = checkboxvalue(request.form.get('time2'))
    time3 = checkboxvalue(request.form.get('time3'))
    time4 = checkboxvalue(request.form.get('time4'))
    time5 = checkboxvalue(request.form.get('time5'))
    time6 = checkboxvalue(request.form.get('time6'))
    time7 = checkboxvalue(request.form.get('time7'))
    time8 = checkboxvalue(request.form.get('time8'))
    time9 = checkboxvalue(request.form.get('time9'))
    availability =  [time1,time2,time3,time4,time5,time6,time7,time8,time9]
    msg = set_tutor_availability(tutorid,availability)
    return view_tutor_template(tutorid,msg3=msg)






@app.route('/addsubjecttotutor?tutorid=<tutorid>',methods=['GET','POST'])
def add_subject_to_tutor(tutorid):
    if request.method == 'POST':
        subcode = request.form['subject']
        msg = linksubjecttutor(tutorid, subcode)
        return view_tutor_template(tutorid,msg)

@app.route('/addclass?subcode=<subcode>',methods=['GET','POST'])
def add_class(subcode):

    if request.method == 'GET':
        return render_template('addclass.html', subject = get_subject(subcode),students = get_subject_and_students(subcode))
    elif request.method == 'POST':
        classtime = request.form["time"]
        repeat = request.form["repeat"]

        students = get_subject_and_students(subcode)
        attendees = []
        for student in students:
            if checkboxvalue(request.form.get(student["studentcode"])) == 1:
                attendees.append(student["studentcode"])
        add_class_to_db(classtime, subcode,attendees, repeat)
        return view_subject_template(subcode)

@app.route('/viewclass?classid=<classid>')
def view_class(classid):
    classdata = get_class(classid)
    return render_template('class.html', classdata = classdata,subject = get_subject(classdata["subcode"]), tutor = get_tutor(classdata["tutorid"]),students = get_subject_and_students(classdata["subcode"]), attendees = get_attendees(classid))

@app.route('/admin')
def admin():
    return render_template('admin.html',admin = getadmin())



@app.route('/addtutortosubject?subcode=<subcode>',methods=['GET','POST'])
def add_tutor_to_subject(subcode):
    if request.method == 'POST':

        tutorid = request.form['tutor']
        msg = linksubjecttutor(tutorid, subcode)
        return view_subject_template(subcode,msg)

@app.route('/removesubjectfromtutor?tutorid=<tutorid>&subcode=<subcode>')
def remove_subject_from_tutor(tutorid,subcode):
    msg = unlinksubjecttutor(tutorid,subcode)
    return view_tutor_template(tutorid,msg2=msg)


@app.route('/removetutorfromsubject?tutorid=<tutorid>&subcode=<subcode>')
def remove_tutor_from_subject(tutorid,subcode):
    msg = unlinksubjecttutor(tutorid,subcode)
    return view_subject_template(subcode,msg)

@app.route('/removesubjectfromstudent?studentcode=<studentcode>&subcode=<subcode>')
def remove_subject_from_student(studentcode,subcode):
    msg = unlinksubjectstudent(studentcode,subcode)
    return view_student_template(studentcode,msg)

@app.route('/removestudentfromsubject?studentcode=<studentcode>&subcode=<subcode>')
def remove_student_from_subject(studentcode,subcode):
    msg = unlinksubjectstudent(studentcode,subcode)
    return view_subject_template(subcode,msg)

@app.route('/addsubjecttostudent?studentcode=<studentcode>',methods=['POST'])
def add_subject_to_student(studentcode):
    subcode = request.form['subject']
    msg=linksubjectstudent(studentcode,subcode)
    return view_student_template(studentcode,msg=msg)

@app.route('/')
def hello_world():
    return render_template('index.html')


@app.route('/rolls')
def view_rolls():
    return render_template('rolls.html')


@app.route('/subjects')
def view_subjects():
    return render_template('subjects.html')


@app.route('/viewsubjectsajax')
def viewsubjects_ajax():
    data = Subject.query.filter_by(year = get_current_year(),studyperiod = get_current_studyperiod()).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state']=""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/viewtutorsajax')
def viewtutors_ajax():
    data = Tutor.query.filter_by(year = get_current_year(),studyperiod = get_current_studyperiod()).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'

@app.route('/viewstudentsajax')
def viewstudents_ajax():
    data = Student.query.filter_by(year = get_current_year(),studyperiod = get_current_studyperiod())
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'

@app.route('/addsubject',methods=['GET','POST'])
def add_subject():
    if request.method == 'GET':
        return render_template('addsubject.html')
    elif request.method == 'POST':
        try:
            subcode = request.form['subcode']
            subname = request.form['subname']
            if Subject.query.filter_by(subcode = subcode, year = get_current_year(), studyperiod = get_current_studyperiod()).first() == None:
                sub = Subject(subcode = subcode, subname = subname, studyperiod = get_current_studyperiod(), year = get_current_studyperiod())
                db.session.add(sub)
                db.session.commit()
            msg = "Record successfully added"
        except:
            msg = "Error"
        finally:
            return render_template("subjects.html", msg=msg, rows = get_subjects())


@app.route('/subject?subcode=<subcode>')
def view_subject(subcode):
    return view_subject_template(subcode)



@app.route('/removesubject?subcode=<subcode>')
def remove_subject(subcode):
    try:
        sub = Subject.query.filter_by(subcode = subcode,year = get_current_year(), studyperiod = get_current_studyperiod()).first()
        db.session.remove(sub)
        db.session.commit()
        msg = "Completed Successfully"
        return render_template("subjects.html", rows = get_subjects(), msg=msg)
    except:
        msg = "Error"
        return render_template("subjects.html", rows = get_subjects(), msg=msg)


@app.route('/removetutor?tutorid=<tutorid>')
def remove_tutor(tutorid):
    try:
        tut = Tutor.query.filter_by(tutorid = tutorid)
        db.session.remove(tut)
        db.session.commit()
        msg = "Completed Successfully"
        return render_template("viewtutors.html", rows = get_tutors(), msg=msg)
    except:
        msg = "Error"
        return render_template("viewtutors.html", rows = get_tutors(), msg=msg)


@app.route('/viewtutors')
def view_tutors():

    return render_template('viewtutors.html', rows=get_tutors())


@app.route('/viewstudents')
def view_students():

    return render_template('viewstudents.html', rows=get_students())


@app.route('/viewstudent?studentcode=<studentcode>')
def view_student(studentcode):
    return view_student_template(studentcode)



@app.route('/viewtutor?tutorid=<tutorid>')
def view_tutor(tutorid):
    return view_tutor_template(tutorid)



@app.route('/addtutor',methods=['GET','POST'])
def add_tutor():
    if request.method == 'GET':
        return render_template('addtutor.html')
    elif request.method == 'POST':
        try:
            firstnm = request.form['firstnm'].strip()
            lastnm = request.form['lastnm'].strip()
            email = request.form['email'].strip()
            phone = request.form['phone'].strip()
            year = get_current_year()
            studyperiod = get_current_studyperiod()
            if Tutor.query.filter_by(firstname = firstnm,lastname = lastnm, email = email, phone = phone, year = year,studyperiod = studyperiod).first() == None:
                tut = Tutor(firstname = firstnm,lastname = lastnm, email = email, phone = phone, year = year,studyperiod = studyperiod)
                db.session.add(tut)
                db.session.commit()
            msg = "Record successfully added"
        except:
            msg = "error in insert operation"
        finally:
            return render_template("viewtutors.html", msg=msg, rows = get_tutors())

@app.route('/uploadstudentdata')
def upload_student_data():
    return render_template('uploadstudentdata.html')


@app.route('/uploadtutordata')
def upload_tutor_data():
    return render_template('uploadtutordata.html')


#HELPER METHODS
def get_tutor(tutorid):
    return Tutor.query.get(tutorid)


def get_student(studentcode):
    return Student.query.filter_by(studentcode = studentcode, year = get_current_year(),studyperiod = get_current_studyperiod()).first()


def get_subjects():
    return Subject.query.filter_by(year = get_current_year(), studyperiod = get_current_studyperiod()).all()


def get_students():
    return Student.query.filter_by(year = get_current_year(),studyperiod = get_current_studyperiod()).all()


def unlinksubjecttutor(tutorid, subcode):
    subject = Subject.query.filter_by(subcode = subcode, year = get_current_year(), studyperiod = get_current_studyperiod()).first()
    subject.tutor = None
    db.session.commit()
    return "Unlinked Successfully."


def unlinksubjectstudent(studentcode,subcode):
    student = Student.query.filter_by(studentcode = studentcode,year=get_current_year(), studyperiod = get_current_studyperiod()).first()
    subject = Subject.query.filter_by(subcode = subcode, year = get_current_year(), studyperiod = get_current_studyperiod()).first()
    student.subjects.remove(subject)
    db.session.commit()
    return "Unlinked Successfully"


def linksubjecttutor(tutorid, subcode):
    subject = Subject.query.filter_by(subcode=subcode, year=get_current_year(), studyperiod=get_current_studyperiod()).first()
    subject.tutor = Tutor.query.filter_by(id = tutorid).first()
    db.session.commit()
    msg = "Subject Linked to Tutor Successfully"
    return msg


def get_subject(subcode):
    return Subject.query.filter_by(subcode = subcode, year = get_current_year(), studyperiod = get_current_studyperiod()).first()


def view_subject_template(subcode,msg=""):
    return render_template("subject.html",rows = get_subject(subcode) ,students = get_subject_and_students(subcode), tutor = get_subject_and_tutor(subcode), tutors = get_tutors(),classes = get_classes_for_subject(subcode),attendees = get_attendees_for_subject(subcode),msg=msg)


def get_classes_for_subject(subcode):
    sub = get_subject(subcode)
    return Class.query.filter_by(subjectid = sub.id, year = get_current_year(), studyperiod = get_current_studyperiod()).all()


def get_tutor_availability(tutorid):
    return TutorAvailability.query.filter_by(tutorid = tutorid).first()

def set_tutor_availability(tutorid, availability):
    if TutorAvailability.query.filter_by(tutorid = tutorid).first() == None:
        avail = TutorAvailability(tutorid = tutorid, time1 = availability[0],time2=availability[1],time3=availability[2],time4=availability[3],time5=availability[4],time6=availability[5],time7=availability[6],time8=availability[7],time9=availability[8])
        db.session.add(avail)
        db.session.commit()
    else:
        avail = TutorAvailability.query.filter_by(tutorid = tutorid).first()
        avail.time1 = availability[0]
        avail.time2 = availability[1]
        avail.time3 = availability[2]
        avail.time4 = availability[3]
        avail.time5 = availability[4]
        avail.time6 = availability[5]
        avail.time7 = availability[6]
        avail.time8 = availability[7]
        avail.time9 = availability[8]
        db.session.commit()
    return "Successful."

def checkboxvalue(checkbox):
    if(checkbox != None):
        return 1
    else:
        return 0


def view_tutor_template(tutorid,msg= "",msg2="", msg3=""):
    return render_template('tutor.html', rows=get_tutor(tutorid), eligiblesubjects=get_subjects(),
                    subjects=get_tutor_and_subjects(tutorid),availability = get_tutor_availability(tutorid), msg=msg, msg2= msg2, msg3=msg3)



def get_student_and_subjects(studentcode):
    student = Student.query.filter_by(studentcode = studentcode, year = get_current_year(), studyperiod = get_current_studyperiod()).first()
    return student.subjects


def get_subject_and_students(subcode):
    subject = Subject.query.filter_by(subcode = subcode, year = get_current_year(), studyperiod = get_current_studyperiod()).first()
    return subject.students


def get_subject_and_tutor(subcode):
    subject = Subject.query.filter_by(subcode = subcode, year =get_current_year(), studyperiod = get_current_studyperiod()).first()
    return subject.tutor


def get_tutor_and_subjects(tutorid):
    tutor = Tutor.query.filter_by(id = tutorid).first()
    return tutor.subjects

def getadmin():
    admin = {}
    admin["currentyear"] = get_current_year()
    admin["studyperiod"] = get_current_studyperiod()
    return admin



def get_tutors():
    return Tutor.query.filter_by(year = get_current_year(), studyperiod = get_current_studyperiod()).all()


def populate_students(filename):
    print("Populating Students")
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    xl = pandas.ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])

    for index,row in df.iterrows():
        try:
            if row['Study Period'] == studyperiod:
                if Student.query.filter_by(studentcode = row["Student Id"], year = year, studyperiod = studyperiod).first() == None:
                    student = Student(studentcode = row["Student Id"],firstname = row["Given Name"], lastname = row['Family Name'], year = year, studyperiod = studyperiod)
                    db.session.add(student)
                    db.session.commit()
                if Subject.query.filter_by(subcode = row["Component Study Package Code"], year = year, studyperiod = studyperiod).first() == None:
                    subject = Subject(subcode = row["Component Study Package Code"], subname = row["Component Study Package Title"], year = year, studyperiod = studyperiod)
                    db.session.add(subject)
                    db.session.commit()
                student = Student.query.filter_by(studentcode=row["Student Id"], firstname=row["Given Name"],
                                                  lastname=row['Family Name'], year=year,
                                                  studyperiod=studyperiod).first()
                subject = Subject.query.filter_by(subcode=row["Component Study Package Code"], year=year,
                                                  studyperiod=studyperiod).first()
                if db.session.query(substumap).filter(substumap.c.student_id==student.id, substumap.c.subject_id==subject.id).first() is None:
                    mapping = SubStuMap(student_id=student.id, subject_id=subject.id)
                    db.session.add(mapping)
                    db.session.commit()
            print("Success")
        except:
            print("Error with StudentID %d with Subject" % (row['Student Id'],row['Component Study Package Code']))



def populate_tutors(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    xl = pandas.ExcelFile(filename)

    df = xl.parse(xl.sheet_names[0])
    for index, row in df.iterrows():
        try:
            if Tutor.query.filter_by(firstname = row['Given Name'],lastname = row['Family Name'],year= year, studyperiod = studyperiod).first() == None:
                print("Trying Insert")
                tutor = Tutor(firstname = row['Given Name'], lastname = row['Family Name'], email = row['Email'], phone = row['Phone'],year=year,studyperiod=studyperiod)
                db.session.add(tutor)
                db.session.commit()
        except:
            print("Error with Tutor %d" % row['Family Name'])
    try:
        df = xl.parse(xl.sheet_names[1])
        for index,row in df.iterrows():
            tutor = Tutor.query.filter_by(firstname = row['Given Name'], lastname = row['Family Name'], email = row['Email'], phone = row['Phone'],year=year,studyperiod=studyperiod).first()
            subject = Subject.query.filter_by(subcode = row["Subject Code"], year = year, studyperiod = studyperiod).first()
            if SubTutMap.query.filter_by(tutor_id = tutor.id, subject_id = subject.id).first() == None:
                mapping = SubTutMap(tutor_id = tutor.id, subject_id = subject.id)
                db.session.add(mapping)
                db.session.commit()
    except:
        msg = "No mappings detected. Skipping"

def update_year(year):
    admin = Admin.query.filter_by(key='currentyear').first()
    admin.value = year
    db.session.commit()

def update_studyperiod(studyperiod):
    admin = Admin.query.filter_by(key='studyperiod').first()
    admin.value = studyperiod
    db.session.commit()

def get_tutor_from_name(tutor):
    split = tutor["Tutor"].split()
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    tutor = Tutor.query.filter_by(firstname = split[0],lastname=split[1],year = year,studyperiod = studyperiod).first(0)
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
    classdata = Class.query.filter_by(classid = classid).first()
    rows = classdata.attendees
    returns = []
    for row in rows:
        returns.append(row["studentcode"])
    return returns

def get_class(classid):
    return Class.query.filter_by(classid=classid).first()

def add_class_to_db(datetime,subcode,attendees,repeat=1):
    tutor = get_subject_and_tutor(subcode)
    subject = get_subject(subcode)
    if Class.query.filter_by(datetime = datetime,subjectid = subject.id,year = get_current_year(), studyperiod = get_current_studyperiod(), repeat = repeat).first() == None:
        specificclass = Class(datetime = datetime,subjectid = subject.id,year = get_current_year(), studyperiod = get_current_studyperiod(), repeat = repeat)
        db.session.add(specificclass)
        db.session.commit()
    add_students_to_class(specificclass, attendees)
    return "Completed Successfully"

def add_students_to_class(specificclass, attendees):
    for i in range(len(attendees)):
        student = get_student(attendees[i])
        mapping = StuAttendance(class_id = specificclass.id,student_id = student.id)
    return "Completed Successfully"

def get_attendees_for_subject(subcode):
    subject =get_subject(subcode)
    classes = Class.query.filter_by(subjectid = subject.id).all()
    data = {}
    for row in classes:
        data[row.id] = row.attendees
    return data

def get_current_year():
    admin = Admin.query.filter_by(key = 'currentyear').first()
    return int(admin.value)

def get_current_studyperiod():
    admin = Admin.query.filter_by(key='studyperiod').first()
    return admin.value

def linksubjectstudent(studentcode,subcode):
    student = Student.query.filter_by(studentcode = studentcode,year=get_current_year(),studyperiod= get_current_studyperiod()).first()
    subject = Subject.query.filter_by(subcode = subcode, year=get_current_year(),studyperiod = get_current_studyperiod()).first()
    mapping = SubStuMap(student_id = student.id,subject_id = subject.id)
    db.session.add(mapping)
    db.session.commit()
    return "Linked Successfully."


def view_student_template(studentcode,msg=""):
    return render_template('student.html', rows=get_student(studentcode),eligiblesubjects = get_subjects(), subjects=get_student_and_subjects(studentcode),msg= msg)

if __name__ == '__main__':
    app.run(debug=True)