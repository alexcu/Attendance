from flask import Flask
from flask import render_template, request
import sqlite3 as sql
app = Flask(__name__)


def connect_db():
    """Connects to the specific database."""
    rv = sql.connect("/Users/justin/PycharmProjects/Attendance/static/database.db")
    rv.row_factory = sql.Row
    return rv


def init_db():
    con = connect_db()
    cur = con.cursor()
    cur.execute("CREATE TABLE if not EXISTS subjects (subcode char(50) NOT NULL, subname char(50) NOT NULL, studyperiod char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists tutors (name char(50) NOT NULL, email char(50) NOT NULL, phone char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists students (studentid char(50) NOT NULL, firstname char(50) NOT NULL, lastname char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not EXISTS substumap (studentid char(50) NOT NULL, subcode char(50) NOT NULL)")
    cur.execute("CREATE TABLE if not exists subtutmap (tutorname char(50) NOT NULL, subcode char(50) NOT NULL)")
    con.close()


def get_tutors():
    con = connect_db()
    cur = con.cursor()
    cur.execute("SELECT * FROM tutors")
    rows = cur.fetchall()
    con.close()
    return rows


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
            cur.execute("INSERT INTO subjects (subcode,subname,studyperiod) VALUES(?, ?, ?)",(subcode,subname,studyperiod))
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
    return render_template("subject.html",rows = get_subject(subcode))


@app.route('/removesubject?subcode=<subcode>')
def remove_subject(subcode):
    try:
        con = connect_db()
        cur = con.cursor()
        cur.execute("delete from subjects where subcode = ?", (subcode,))
        print("delete from subjects where subcode = ?", (subcode,))
        msg = "Completed Successfully"
        con.close()
        return render_template("subjects.html", rows = get_subjects(), msg=msg)
    except:
        con.rollback()
        msg = "Error"
        return render_template("subjects.html", rows = get_subjects(), msg=msg)
    finally:
        con.close()

def get_subjects():
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from subjects")
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
    return render_template('viewtutors.html', rows=get_tutors())

@app.route('/viewtutor?name=<name>')
def view_tutor(name):
    return render_template('tutor.html', rows = get_tutor(name))

def get_tutor(name):
    con = connect_db()
    cur = con.cursor()
    cur.execute("select * from tutors where name = ?", (name,))
    rows = cur.fetchone()
    con.close()
    return rows


@app.route('/addtutor',methods=['GET','POST'])
def add_tutor():
    if request.method == 'GET':
        return render_template('addtutor.html')
    elif request.method == 'POST':
        try:
            nm = request.form['nm']
            email = request.form['email']
            phone = request.form['phone']

            con = connect_db()
            cur = con.cursor()
            cur.execute("INSERT INTO tutors (name,email,phone) VALUES(?, ?, ?)",(nm,email,phone))
            con.commit()
            msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"

        finally:
            con.close()
            return render_template("viewtutors.html", msg=msg, rows = get_tutors())


if __name__ == '__main__':
    app.run()
