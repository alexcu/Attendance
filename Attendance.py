from flask import Flask
from flask import render_template, request
import sqlite3 as sql
app = Flask(__name__)


def connect_db():
    """Connects to the specific database."""
    rv = sql.connect("database.db")
    rv.row_factory = sql.Row
    return rv


@app.route('/')
def hello_world():
    return render_template('index.html')

@app.route('/rolls')
def view_rolls():
    return render_template('rolls.html')

@app.route('/viewtutors')
def view_tutors():
    con =  sql.connect("database.db")
    con.row_factory = sql.Row
    cur = con.cursor()
    cur.execute("SELECT * FROM tutors")
    rows = cur.fetchall();
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

            with sql.connect("database.db") as con:
                cur = con.cursor()
                cur.execute("INSERT INTO tutors (name,email,phone) VALUES(?, ?, ?)",(nm,email,phone) )
                con.commit()
                msg = "Record successfully added"
        except:
            con.rollback()
            msg = "error in insert operation"

        finally:
            return render_template("viewtutors.html", msg=msg)
            con.close()

if __name__ == '__main__':
    app.run()
