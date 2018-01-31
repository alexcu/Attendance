# Attendance

# Overview
This project started as a way to make my job easier. I was in charge of timetabling classes at a college, and had 400 students, 35 tutors, 9 timeslots and almost 80 subjects to timetable, all while respecting teacher's availabilities and ensuring no clashes for the students.

# Main Components of this App
1. Student, Subject and Tutor Management. Easy to use UI with Excel import options to make management easy.
2. Timetabling. After entering data, you can generate a timetable using linear programming - all point and click.
3. Class Management. You can use this to keep track of the tutorial program, see how attendance rates are going with charts and graphics.


# Setting up the database
We use Flask-Migrate to create the database, but firstly we need to comment this line in the __init__.py:

Attendance.models.init_db()

From a command window, run the following:

$ python manage.py db init

$ python manage.py db migrate

$ python manage.py db upgrade

Then uncomment the line in the __init__.py.

If there are any issues, delete the migrations directory and try again.


# Settings
Create a config.py like the following and update the settings as desired:

appcfg = {

    "upload" : '/path/to/upload/directory',

    "dbstring" : 'sqlite:////database.db',

    "secretkey" : 'insertsecretkeyhere',

    "adminpassword" : 'admin',

    "startyear" : '2018',

    "startstudyperiod" : "Semester 1",

    "rooms" : [['GHB1', True], ['GHB2', True], ['GHB3', True], ['GHB4', False], ['GHB5', False], ['GHB6', False], ['GHB7', False], ['Peter Waylen', False], ['Ronald Cowan', True], ['Frank Larkins', False], ['Mavis Jackson', True], ['Library Project Room', False]],

    "timeslots": [['Monday 19:30',True], ['Monday 20:30',True], ['Monday 21:30', False], ['Tuesday 19:30', True], ['Tuesday 20:30', True], ['Tuesday 21:30', False], ['Wednesday 19:30', True], ['Wednesday 20:30',True], ['Wednesday 21:30', False]]
    
}