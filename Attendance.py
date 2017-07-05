from flask import Flask
from flask import render_template, request, redirect, url_for, send_from_directory
import os, pandas
import sqlite3 as sql
app = Flask(__name__)





app.config['UPLOAD_FOLDER'] = 'D:/Downloads/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['xls','xlsx', 'csv'])
def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1] in app.config['ALLOWED_EXTENSIONS']


# Route that will process the file upload
@app.route('/upload', methods=['POST'])
def upload():
    # Get the name of the uploaded file
    init_db()
    file = request.files['file']
    # Check if the file is one of the allowed types/extensions
    if file and allowed_file(file.filename):
        # Make the filename safe, remove unsupported chars
        filename = file.filename
        # Move the file form the temporal folder to
        # the upload folder we setup
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        filename2 = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        try:
            populate_students(filename2)
            msg = "Completed Successfully"
        except:
            msg = "There was an error with the upload, please try again"
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
        return render_template("uploadstudentdata.html", msg = msg)



def connect_db():
    rv = sql.connect("C:/Users/justi/PycharmProjects/Attendance/static/database.db")
    rv.row_factory = sql.Row
    return rv


def init_db():
    con = connect_db()
    cur = con.cursor()
    cur.execute("CREATE TABLE if not EXISTS subjects (subjectid integer primary key AUTOINCREMENT, subcode char(50) UNIQUE NOT NULL, subname char(50) NOT NULL, studyperiod char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists tutors (tutorid integer primary key autoincrement,firstname char(50) NOT NULL, lastname char(50) not null, email char(50) NOT NULL, phone char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists students (studentid integer primary key AUTOINCREMENT, studentcode char(50) unique NOT NULL, firstname char(50) NOT NULL, lastname char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not EXISTS substumap (id integer primary key AUTOINCREMENT, studentcode char(50) NOT NULL, subjectcode char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists subtutmap (id integer primary key autoincrement, tutorid integer NOT NULL, subcode char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists tutavailability (id integer primary key autoincrement, tutorid integer unique, time1 integer default 1, time2 integer default 1, time3 integer default 1, time4 integer default 1, time5 integer default 1, time6 integer default 1, time7 integer default 1, time8 integer default 1, time9 integer default 1)")
    cur.execute("create table if not exists classes (classid integer primary key autoincrement, tutorid integer not null, datetime text, subcode char(50) not null, repeat integer) ")
    cur.execute("create table if not exists stuattendance (id integer primary key autoincrement, classid integer not null, studentcode char(50) not null)")
    con.close()



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
    cur.execute("insert or replace into tutavailability (tutorid, time1,time2,time3,time4,time5,time6,time7,time8,time9) VALUES (?,?,?,?,?,?,?,?,?,?)", (tutorid,availability[0],availability[1], availability[2], availability[3],availability[4],availability[5], availability[6], availability[7], availability[8]))
    con.commit()
    con.close()
    return "Successful."


@app.route('/updatetutoravailability?tutorid=<tutorid>',methods=['GET','POST'])
def update_tutor_availability(tutorid):
    init_db()
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
        "select students.studentcode, students.firstname, students.lastname, subjects.subcode, subjects.subname,subjects.studyperiod from ((substumap inner join students on substumap.studentcode = students.studentcode) inner join subjects on substumap.subjectcode = subjects.subcode) where students.studentcode = ?", (studentcode,))
    rows = cur.fetchall()
    return rows

def get_subject_and_students(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select students.studentcode, students.firstname, students.lastname, subjects.subcode, subjects.subname,subjects.studyperiod from ((substumap inner join students on substumap.studentcode = students.studentcode) inner join subjects on substumap.subjectcode = subjects.subcode) where subjects.subcode = ?",
        (subcode,))
    rows = cur.fetchall()
    con.close()
    return rows


def get_subject_and_tutor(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select tutors.tutorid, tutors.firstname, tutors.lastname, tutors.email, tutors.phone,subjects.subcode, subjects.subname,subjects.studyperiod from ((subtutmap inner join tutors on subtutmap.tutorid = tutors.tutorid) inner join subjects on subtutmap.subcode = subjects.subcode) where subjects.subcode = ?",
        (subcode,))
    rows = cur.fetchone()
    con.close()
    return rows


def get_tutor_and_subjects(tutorid):
    con = connect_db()
    cur = con.cursor()
    cur.execute(
        "select tutors.tutorid, tutors.firstname, tutors.lastname, subjects.subcode, subjects.subname,subjects.studyperiod from ((subtutmap inner join tutors on subtutmap.tutorid = tutors.tutorid) inner join subjects on subtutmap.subcode = subjects.subcode) where tutors.tutorid = ?",
        (tutorid,))
    rows = cur.fetchall()
    con.close()
    return rows


def get_tutors():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM tutors")
    rows = cur.fetchall()
    con.close()
    return rows


def populate_students(filename):
    xl = pandas.ExcelFile(filename)
    df = xl.parse(xl.sheet_names[0])

    con = connect_db()
    cur = con.cursor()
    for index,row in df.iterrows():
        try:
            if row['Study Period'] == "Semester 2":
                cur.execute("insert or ignore into students (studentcode,firstname,lastname) values (?,?,?)", (row['Student Id'],row['Given Name'],row['Family Name']))
                cur.execute("insert or ignore into subjects (subcode,subname,studyperiod) values (?,?,?)", (row['Component Study Package Code'], row['Component Study Package Title'], "Semester 2"))
                cur.execute("select id from substumap where substumap.studentcode = ? and substumap.subjectcode = ? ", (row['Student Id'], row['Component Study Package Code']))
                if cur.fetchone() is None:
                    cur.execute("insert into substumap (studentcode, subjectcode) values (?,?)", (row['Student Id'],row['Component Study Package Code']))
        except:
            print("Error with StudentID %d" % row['Student Id'])
    con.commit()
    con.close()



@app.route('/addsubjecttotutor?tutorid=<tutorid>',methods=['GET','POST'])
def add_subject_to_tutor(tutorid):
    if request.method == 'POST':

        subcode = request.form['subject']
        msg = linksubjecttutor(tutorid, subcode)
        return view_tutor_template(tutorid,msg)


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
        cur.execute("insert into subtutmap (tutorid, subcode) values (?,?)",
                    (tutorid, subcode))
    con.commit()
    con.close()
    msg = "Subject Linked to Tutor Successfully"
    return msg

@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/rolls')
def view_rolls():
    return render_template('rolls.html')

@app.route('/subjects')
def view_subjects():
    try:
        rows = get_subjects()
        return render_template('subjects.html', rows = rows)
    except:
        init_db()
        rows = get_subjects()
        return render_template('subjects.html', rows=rows)

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
            cur.execute("INSERT OR IGNORE INTO subjects (subcode,subname,studyperiod) VALUES(?, ?, ?)",(subcode,subname,studyperiod))
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

def view_subject_template(subcode,msg=""):
    return render_template("subject.html",rows = get_subject(subcode),students = get_subject_and_students(subcode), tutor = get_subject_and_tutor(subcode), tutors = get_tutors(),msg=msg)


@app.route('/removesubject?subcode=<subcode>')
def remove_subject(subcode):
    try:
        con = connect_db()
        cur = con.cursor()
        cur.execute("delete from subjects where subcode = ?", (subcode,))
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

def get_subjects():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from subjects")
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

def get_subject(subcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from subjects where subcode = ?", (subcode,))
    rows = cur.fetchone()
    con.close()
    return rows

@app.route('/viewtutors')
def view_tutors():
    try:
        return render_template('viewtutors.html', rows=get_tutors())
    except:
        init_db()
        return render_template('viewtutors.html', rows=get_tutors())

@app.route('/viewstudents')
def view_students():
    try:
        return render_template('viewstudents.html', rows=get_students())
    except:
        init_db()
        return render_template('viewstudents.html', rows=get_students())

@app.route('/viewstudent?studentcode=<studentcode>')
def view_student(studentcode):
    return render_template('student.html', rows = get_student(studentcode), subjects=get_student_and_subjects(studentcode))


def get_student(studentcode):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from students where studentcode = ?", (studentcode,))
    rows = cur.fetchone()
    con.close()
    return rows

@app.route('/viewtutor?tutorid=<tutorid>')
def view_tutor(tutorid):
    return view_tutor_template(tutorid)

def get_tutor(tutorid):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from tutors where tutorid = ?", (tutorid,))
    rows = cur.fetchone()
    con.close()
    return rows


@app.route('/addtutor',methods=['GET','POST'])
def add_tutor():
    if request.method == 'GET':
        return render_template('addtutor.html')
    elif request.method == 'POST':
        try:
            firstnm = request.form['firstnm']
            lastnm = request.form['lastnm']
            email = request.form['email']
            phone = request.form['phone']

            con = connect_db()
            cur = con.cursor()
            cur.execute("INSERT INTO tutors (firstname,lastname,email,phone) VALUES(?, ?,?, ?)",(firstnm,lastnm,email,phone))
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


if __name__ == '__main__':
    app.run(debug=True)
