import logging
from concurrent.futures import ThreadPoolExecutor
from logging.handlers import RotatingFileHandler

from flask import Flask
from flask_bcrypt import Bcrypt
from flask_login import LoginManager, current_user
from flask_principal import Principal, RoleNeed, ActionNeed, Permission, identity_loaded
from flask_sqlalchemy import *

# DOCS https://docs.python.org/3/library/concurrent.futures.html#concurrent.futures.ThreadPoolExecutor
executor = ThreadPoolExecutor(2)
app = Flask(__name__)
# app.config['UPLOAD_FOLDER'] = 'C:/Users/justi/Downloads/uploads/'
app.config['ALLOWED_EXTENSIONS'] = set(['xls', 'xlsx'])
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////Users/justi/Dropbox/Justin/Documents/Python/database70.db'
app.config.update(
    SECRET_KEY='jemimaisababe'
)
db = SQLAlchemy(app)
bcrypt = Bcrypt(app)
principals = Principal(app, skip_static=True)
login_manager = LoginManager()
login_manager.init_app(app)

# WINDOWS
# app.config['UPLOAD_FOLDER'] = 'D:/Downloads/uploads/'
# LINUX



'''
FLASK-LOGIN SET UP AREA

'''
login_manager.login_view = '/login'


@login_manager.user_loader
def load_user(user_id):
    return User.query.filter_by(username=user_id).first()



'''
FLASK_PRINCIPAL SET-UP AREA. 

Firstly we set up Needs - Admin and User level preferences.
'''
# Needs
be_admin = RoleNeed('admin')
to_sign_in = ActionNeed('sign in')

# Permissions
user_permission = Permission(to_sign_in)
user_permission.description = 'User\'s permissions'
admin_permission = Permission(be_admin)
admin_permission.description = 'Admin\'s permissions'

apps_needs = [be_admin, to_sign_in]
apps_permissions = [user_permission, admin_permission]


@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    identity.user = current_user
    if current_user.is_authenticated:
        needs = []
        needs.append(to_sign_in)
        if current_user.is_admin == 1 or current_user.is_admin == '1':
            needs.append(be_admin)
        for n in needs:
            identity.provides.add(n)

def current_privileges():
    return (('{method} : {value}').format(method=n.method, value=n.value)
            for n in apps_needs if n in g.identity.provides)

import Attendance.views
from Attendance.models import *
from Attendance.helpers import *
from Attendance.forms import LoginForm, AddSubjectForm, NameForm, TimeslotForm, StudentForm

# DATABASE METHODS
db.create_all()
#db.mapper(SubStuMap, substumap)
#db.mapper(SubTutMap, subtutmap)
#db.mapper(StuAttendance, stuattendance)
#db.mapper(StuTimetable, stutimetable)
#db.mapper(TimeslotClasses, timeslotclassesmap)
#db.mapper(TutorAvailability, tutoravailabilitymap)





if Admin.query.filter_by(key='currentyear').first() == None:
    admin = Admin(key='currentyear', value=2017)
    db.session.add(admin)
    db.session.commit()
if Admin.query.filter_by(key='studyperiod').first() == None:
    study = Admin(key='studyperiod', value='Semester 2')
    db.session.add(study)
    db.session.commit()

if Admin.query.filter_by(key='timetable').first() is None:
    timetable = Timetable(key="default")
    db.session.add(timetable)
    db.session.commit()
    timetableadmin = Admin(key='timetable', value=timetable.id)
    db.session.add(timetableadmin)
    db.session.commit()

if User.query.filter_by(username='admin').first() is None:
    user = User.create(username='admin', password='password')
    user.update(is_admin=True)

if University.query.filter_by(name='University of Melbourne').first() is None:
    uni = University(name='University of Melbourne')
    db.session.add(uni)
    db.session.commit()

if College.query.filter_by(name="International House").first() is None:
    college = College(name='International House')
    db.session.add(college)
    db.session.commit()

if __name__ == '__main__':
    handler = RotatingFileHandler('foo.log', maxBytes=10000, backupCount=10)
    handler.setLevel(logging.INFO)
    app.logger.addHandler(handler)
    app.run(debug=True)
