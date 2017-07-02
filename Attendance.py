from flask import Flask
from flask import render_template, request
import sqlite3 as sql
app = Flask(__name__)


def connect_db():
    """Connects to the specific database."""
    rv = sql.connect("/Users/justin/PycharmProjects/Attendance/static/database.db")
    rv.row_factory = sql.Row
    return rv


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

@app.route('/viewtutors')
def view_tutors():
    rows = get_tutors()
    return render_template('viewtutors.html', rows=rows)

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
            rows = get_tutors()
            return render_template("viewtutors.html", msg=msg, rows = rows)


if __name__ == '__main__':
    app.run()
