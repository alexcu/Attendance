# Attendance

# Overview
This project started as a way to make my job easier. I was in charge of timetabling classes at a college, and had 400 students, 35 tutors, 9 timeslots and almost 80 subjects to timetable, all while respecting teacher's availabilities and ensuring no clashes for the students.

# Main Components of this App
1. Student, Subject and Tutor Management. Easy to use UI with Excel import options to make management easy.
2. Timetabling. After entering data, you can generate a timetable using linear programming - all point and click.
3. Class Management. You can use this to keep track of the tutorial program, see how attendance rates are going with charts and graphics.


# Setting up the database

We use Flask-Migrate to create the database, run the following:
$ python manage.py db init
$ python manage.py db migrate
$ python manage.py db upgrade