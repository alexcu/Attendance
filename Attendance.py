from flask import Flask
from flask import render_template, request, redirect, url_for, send_from_directory
from flask_sqlalchemy import *
from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from flask.ext.bcrypt import Bcrypt
import os, pandas, json
import sqlite3 as sql
app = Flask(__name__)

#WINDOWS
#app.config['UPLOAD_FOLDER'] = 'D:/Downloads/uploads/'
#LINUX
app.config['UPLOAD_FOLDER'] = '/home/justin/Downloads/uploads/'
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

class Admin(db.model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer,primary_key=True)
    key = db.Column(db.String(50),unique=True,nullable=False)
    value = db.Column(db.String(50),nullable=False)


class SubStuMap(object):
    def __init__(self,studentcode,subcode):
        self.studentcode = studentcode
        self.subcode = subcode


class SubTutMap(object):
    def __init__(self,tutor_id,subcode):
        self.tutor_id = tutor_id
        self.subcode = subcode

class StuAttendance(object):
    def __init__(self,classid,studentid):
        self.classid=classid
        self.studentid=studentid
##Association tables
substumap = db.Table('substumap',
    db.Column('id',db.Integer,primary_key=True),
    db.Column('studentcode', db.Integer, db.ForeignKey('students.id')),
    db.Column('subcode', db.Integer, db.ForeignKey('subjects.id')),
)

subtutmap = db.Table('subtutmap',
    db.Column('id',db.Integer,primary_key = True),
    db.Column('tutor_id', db.Integer, db.ForeignKey('tutors.id')),
    db.Column('subcode', db.Integer, db.ForeignKey('subjects.id')),
)

stuattendance = db.Table('stuattendance',
                         db.Column('id',db.Integer,primary_key=True),
                         db.Column('classid',db.Integer,db.ForeignKey('classes.id')),
                         db.Column('studentid',db.Integer,db.ForeignKey('students.id'))
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
    subjects = db.relationship("Subject", secondary = subtutmap,backref = db.backref('tutor'))

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

#DATABASE METHODS
db.create_all()
db.mapper(SubStuMap,substumap)
db.mapper(SubTutMap,subtutmap)
db.mapper(StuAttendance,stuattendance)

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
        print(filename2)
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
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from classes where classid = ?",(classid,))
    classdata = cur.fetchone()
    cur.execute("delete from classes where classid = ?",(classid,))
    cur.execute("delete from stuattendance where classid = ?", (classid,))
    con.commit()
    con.close()
    return view_subject_template(classdata["subcode"])



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
    con = connect_db()
    cur = con.cursor()
    cur.execute("select subcode,subname,studyperiod from subjects where year = ? and studyperiod = ?", (get_current_year(),get_current_studyperiod()))
    data = cur.fetchall()
    columns = [d[0] for d in cur.description]
    con.close()
    data = json.dumps([dict(zip(columns, row)) for row in data])
    return '{ "data" : ' + data + '}'


@app.route('/viewtutorsajax')
def viewtutors_ajax():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from tutors where year = ? and studyperiod = ?", (get_current_year(), get_current_studyperiod()))
    data = cur.fetchall()
    columns = [d[0] for d in cur.description]
    con.close()
    data = json.dumps([dict(zip(columns, row)) for row in data])
    return '{ "data" : ' + data + '}'

@app.route('/viewstudentsajax')
def viewstudents_ajax():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select studentcode,firstname,lastname from students where year = ? and studyperiod = ?", (get_current_year(), get_current_studyperiod()))
    data = cur.fetchall()
    columns = [d[0] for d in cur.description]
    con.close()
    data = json.dumps([dict(zip(columns, row)) for row in data])
    return '{ "data" : ' + data + '}'

@app.route('/addsubject',methods=['GET','POST'])
def add_subject():
    if request.method == 'GET':
        return render_template('addsubject.html')
    elif request.method == 'POST':
        try:
            subcode = request.form['subcode']
            subname = request.form['subname']
            studyperiod = request.form['studyperiod']

            con = connect_db()
            cur = con.cursor()
            cur.execute("INSERT OR IGNORE INTO subjects (subcode,subname,year, studyperiod) VALUES(?, ?, ?)",(subcode,subname,get_current_year(), studyperiod))
            con.commit()
            msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"

        finally:
            con.close()
            return render_template("subjects.html", msg=msg, rows = get_subjects())


@app.route('/subject?subcode=<subcode>')
def view_subject(subcode):
    return view_subject_template(subcode)



@app.route('/removesubject?subcode=<subcode>')
def remove_subject(subcode):
    try:
        con = connect_db()
        cur = con.cursor()
        cur.execute("delete from subjects where subcode = ? and year = ? and studyperiod = ?", (subcode, get_current_year(), get_current_studyperiod()))
        con.commit()
        msg = "Completed Successfully"
        con.close()
        return render_template("subjects.html", rows = get_subjects(), msg=msg)
    except:
        con.rollback()
        msg = "Error"
        return render_template("subjects.html", rows = get_subjects(), msg=msg)
    finally:
        con.close()


@app.route('/removetutor?tutorid=<tutorid>')
def remove_tutor(tutorid):
    try:
        con = connect_db()
        cur = con.cursor()
        cur.execute("delete from tutors where tutorid = ?", (tutorid,))
        con.commit()
        msg = "Completed Successfully"
        con.close()
        return render_template("viewtutors.html", rows = get_tutors(), msg=msg)
    except:
        con.rollback()
        msg = "Error"
        return render_template("viewtutors.html", rows = get_tutors(), msg=msg)
    finally:
        con.close()



@app.route('/viewtutors')
def view_tutors():

    return render_template('viewtutors.html', rows=get_tutors())


@app.route('/viewstudents')
def view_students():

    return render_template('viewstudents.html', rows=get_students())


@app.route('/viewstudent?studentcode=<studentcode>')
def view_student(studentcode):
    return render_template('student.html', rows = get_student(studentcode), subjects=get_student_and_subjects(studentcode))



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
            con = connect_db()
            cur = con.cursor()
            cur.execute("select firstname from tutors where firstname = ? and lastname = ? and year = ? and studyperiod = ?",(firstnm,lastnm,year,studyperiod))
            if cur.fetchone() is None:
                cur.execute("INSERT INTO tutors (firstname,lastname,email,phone, year, studyperiod) VALUES(?, ?,?,?,?,?)",(firstnm,lastnm,email,phone,get_current_year(), get_current_studyperiod()))
            con.commit()
            msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"

        finally:
            con.close()
            return render_template("viewtutors.html", msg=msg, rows = get_tutors())

@app.route('/uploadstudentdata')
def upload_student_data():
    return render_template('uploadstudentdata.html')


@app.route('/uploadtutordata')
def upload_tutor_data():
    return render_template('uploadtutordata.html')


#HELPER METHODS
def get_tutor(tutorid):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from tutors where tutorid = ?", (tutorid,))
    rows = cur.fetchone()
    con.close()
    return rows


def get_student(studentcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from students where studentcode = ? and year = ? and studyperiod = ?", (studentcode,get_current_year(), get_current_studyperiod()))
    rows = cur.fetchone()
    con.close()
    return rows


def get_subjects():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from subjects where year = ? and studyperiod = ?", (get_current_year(),get_current_studyperiod()))
    rows = cur.fetchall()
    con.close()
    return rows


def get_students():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from students")
    rows = cur.fetchall()
    con.close()
    return rows


def unlinksubjecttutor(tutorid, subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("delete from subtutmap where subtutmap.tutorid = ? and subtutmap.subcode = ?",(tutorid, subcode))
    con.commit()
    con.close()
    return "Unlinked Successfully."

def linksubjecttutor(tutorid, subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select id from subtutmap where subtutmap.tutorid = ? and subtutmap.subcode = ? ",
                (tutorid, subcode))
    if cur.fetchone() is None:
        cur.execute("insert into subtutmap (tutorid, subcode, year, studyperiod) values (?,?,?,?)",
                    (tutorid, subcode, get_current_year(), get_current_studyperiod()))
    con.commit()
    con.close()
    msg = "Subject Linked to Tutor Successfully"
    return msg

def get_subject(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from subjects where subcode = ? and year = ? and studyperiod = ?", (subcode,get_current_year(),get_current_studyperiod()))
    rows = cur.fetchone()
    con.close()
    return rows

def view_subject_template(subcode,msg=""):
    return render_template("subject.html",rows = get_subject(subcode),students = get_subject_and_students(subcode), tutor = get_subject_and_tutor(subcode), tutors = get_tutors(),classes = get_classes_for_subject(subcode),attendees = get_attendees_for_subject(subcode),msg=msg)

def get_classes_for_subject(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from classes where subcode = ? and year = ? and studyperiod = ?",(subcode,get_current_year(), get_current_studyperiod()))
    return cur.fetchall()


def get_tutor_availability(tutorid):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select tutorid, time1,time2,time3,time4,time5,time6, time7,time8,time9 from tutavailability where tutorid = ?", (tutorid,))
    rows = cur.fetchone()
    con.close()
    return rows

def set_tutor_availability(tutorid, availability):
    con = connect_db()
    cur = con.cursor()
    cur.execute("insert or replace into tutavailability (tutorid, time1,time2,time3,time4,time5,time6,time7,time8,time9,year,studyperiod) VALUES (?,?,?,?,?,?,?,?,?,?,?,?)", (tutorid,availability[0],availability[1], availability[2], availability[3],availability[4],availability[5], availability[6], availability[7], availability[8],get_current_year(), get_current_studyperiod()))
    con.commit()
    con.close()
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
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select students.studentcode, students.firstname, students.lastname, subjects.subcode, subjects.subname,subjects.studyperiod from ((substumap inner join students on substumap.studentcode = students.studentcode) inner join subjects on substumap.subjectcode = subjects.subcode) where students.studentcode = ? and students.year = ? and students.studyperiod = ? and subjects.year = ? and subjects.studyperiod = ? and substumap.year = ? and substumap.studyperiod = ?", (studentcode,get_current_year(),get_current_studyperiod(),get_current_year(),get_current_studyperiod(),get_current_year(),get_current_studyperiod()))
    rows = cur.fetchall()
    return rows

def get_subject_and_students(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select students.studentcode, students.firstname, students.lastname, subjects.subcode, subjects.subname,subjects.studyperiod from ((substumap inner join students on substumap.studentcode = students.studentcode) inner join subjects on substumap.subjectcode = subjects.subcode) where subjects.subcode = ? and students.year = ? and students.studyperiod = ? and subjects.year = ? and subjects.studyperiod = ? and substumap.year = ? and substumap.studyperiod = ?",        (subcode,get_current_year(), get_current_studyperiod(),get_current_year(), get_current_studyperiod(),get_current_year(), get_current_studyperiod()))
    rows = cur.fetchall()
    con.close()
    return rows


def get_subject_and_tutor(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select tutors.tutorid, tutors.firstname, tutors.lastname, tutors.email, tutors.phone,subjects.subcode, subjects.subname,subjects.studyperiod from ((subtutmap inner join tutors on subtutmap.tutorid = tutors.tutorid) inner join subjects on subtutmap.subcode = subjects.subcode) where subjects.subcode = ? and tutors.year = ? and tutors.studyperiod = ? and subjects.year = ? and subjects.studyperiod = ? and subtutmap.year = ? and subtutmap.studyperiod = ?",
        (subcode,get_current_year(),get_current_studyperiod(),get_current_year(),get_current_studyperiod(),get_current_year(),get_current_studyperiod()))
    rows = cur.fetchone()
    con.close()
    return rows


def get_tutor_and_subjects(tutorid):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select tutors.tutorid, tutors.firstname, tutors.lastname, subjects.subcode, subjects.subname,subjects.studyperiod from ((subtutmap inner join tutors on subtutmap.tutorid = tutors.tutorid) inner join subjects on subtutmap.subcode = subjects.subcode) where tutors.tutorid = ? and tutors.year = ? and tutors.studyperiod = ? and subjects.year = ? and subjects.studyperiod = ? and subtutmap.year = ? and subtutmap.studyperiod = ?",
        (tutorid,get_current_year(),get_current_studyperiod(),get_current_year(),get_current_studyperiod(),get_current_year(),get_current_studyperiod()))
    rows = cur.fetchall()
    con.close()
    return rows

def getadmin():
    admin = {}
    admin["currentyear"] = get_current_year()
    admin["studyperiod"] = get_current_studyperiod()
    return admin



def get_tutors():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM tutors where year = ? and studyperiod = ?", (get_current_year(), get_current_studyperiod()))
    rows = cur.fetchall()
    con.close()
    return rows


def populate_students(filename):
    print("Populating Students")
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    xl = pandas.ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])

    con = connect_db()
    cur = con.cursor()
    for index,row in df.iterrows():
        try:
            if row['Study Period'] == studyperiod:
                cur.execute("select studentcode from students where studentcode = ? and year = ? and studyperiod = ?", (row["Student Id"],year,studyperiod))
                if cur.fetchone() is None:
                    cur.execute("insert or ignore into students (studentcode,firstname,lastname,year,studyperiod) values (?,?,?,?,?)", (row['Student Id'],row['Given Name'],row['Family Name'],year, studyperiod))
                cur.execute("select subcode from subjects where subcode = ? and year = ? and studyperiod = ?", (row["Component Study Package Code"],year,studyperiod))
                if cur.fetchone() is None:
                    cur.execute("insert or ignore into subjects (subcode,subname,year,studyperiod) values (?,?,?,?)", (row['Component Study Package Code'], row['Component Study Package Title'], year,studyperiod))
                cur.execute("select id from substumap where substumap.studentcode = ? and substumap.subjectcode = ? and substumap.year = ? and substumap.studyperiod = ? ", (row['Student Id'], row['Component Study Package Code'],year,studyperiod))
                if cur.fetchone() is None:
                    cur.execute("insert into substumap (studentcode, subjectcode, year, studyperiod) values (?,?,?,?)", (row['Student Id'],row['Component Study Package Code'],year, studyperiod))
                print("Successful")
        except:
            print("Error with StudentID %d with Subject" % (row['Student Id'],row['Component Study Package Code']))
    con.commit()
    con.close()



def populate_tutors(filename):
    year = get_current_year()
    studyperiod = get_current_studyperiod()
    xl = pandas.ExcelFile(filename)

    df = xl.parse(xl.sheet_names[0])
    con = connect_db()
    cur = con.cursor()
    for index, row in df.iterrows():
        try:
            cur.execute("select * from tutors where firstname = ? and lastname = ? and year = ? and studyperiod = ?",(row['Given Name'],row['Family Name'],year, studyperiod))
            if cur.fetchone() == None:
                print("Trying Insert")
                cur.execute("insert or ignore into tutors (firstname,lastname,email,phone,year,studyperiod) values (?,?,?,?,?,?)",
                            (row['Given Name'], row['Family Name'], row['Email'], row['Phone'],year,studyperiod))
            con.commit()
        except:
            print("Error with Tutor %d" % row['Family Name'])
    try:

        df = xl.parse(xl.sheet_names[1])
        print("Doing this")
        for index,row in df.iterrows():
            print(get_tutor_from_name(row)["tutorid"])
            cur.execute("insert or replace into subtutmap (tutorid,subcode,year,studyperiod) values (?,?,?,?)",(get_tutor_from_name(row)["tutorid"], row["Subject Code"],get_current_year(),get_current_studyperiod()))
        con.commit()
    except:
        msg = "No mappings detected. Skipping"
    finally:
        con.close()

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

def add_class_to_db(classtime,subcode,attendees,repeat=1):
    con = connect_db()
    cur = con.cursor()
    tutor = get_subject_and_tutor(subcode)
    cur.execute("insert into classes (classtime,subcode,repeat,tutorid,year,studyperiod) values (?,?,?,?,?,?)",(classtime,subcode,repeat,tutor["tutorid"],get_current_year(),get_current_studyperiod()))
    con.commit()
    cur.execute("select * from classes where classtime = ? and subcode = ? and repeat = ? and tutorid = ? and year = ? and studyperiod=?", (classtime,subcode,repeat,tutor["tutorid"],get_current_year(),get_current_studyperiod()))
    specificclass=cur.fetchone()
    con.close()
    add_students_to_class(specificclass, attendees)
    return "Completed Successfully"

def add_students_to_class(specificclass, attendees):
    con = connect_db()
    cur = con.cursor()
    for i in range(len(attendees)):
        cur.execute("insert into stuattendance (classid,studentcode,year,studyperiod) values (?,?,?,?)", (specificclass["classid"],attendees[i],get_current_year(),get_current_studyperiod()))
    con.commit()
    con.close()
    return "Completed Successfully"

def get_attendees_for_subject(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select classes.classid, classes.subcode, stuattendance.studentcode from (stuattendance inner join classes on stuattendance.classid = classes.classid) where classes.subcode = ? and classes.year = ? and stuattendance.year = ? and classes.studyperiod = ? and stuattendance.studyperiod = ?",(subcode,get_current_year(),get_current_year(),get_current_studyperiod(),get_current_studyperiod()))
    rows = cur.fetchall()
    con.close()
    data = {}
    for row in rows:
        data[row["classid"]] = []
    for row in rows:
        data[row["classid"]].append(row["studentcode"])
    return data

def get_current_year():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select value from admin where key = 'currentyear'")
    data = cur.fetchone()
    data = data["value"]
    return int(data)

def get_current_studyperiod():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select value from admin where key = 'studyperiod'")
    data = cur.fetchone()
    data = data["value"]
    return data

if __name__ == '__main__':
    app.run(debug=True)