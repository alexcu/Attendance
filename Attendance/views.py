import json

from flask import request, redirect, current_app, url_for
from flask_login import login_user, logout_user, current_user, login_required
from flask_principal import identity_changed, Identity
from sqlalchemy.orm import joinedload

from Attendance import admin_permission
from Attendance.forms import LoginForm, AddSubjectForm, NameForm, TimeslotForm, StudentForm, EditTutorForm, \
    EditStudentForm, AddTimetableForm, JustNameForm
from Attendance.helpers import *
from Attendance.models import *


### APP ROUTES
@app.route('/')
@login_required
def hello_world():
    return render_template('index.html')


# FLASK LOGIN / LOGOUT / REGISTER
@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if request.method == 'GET':
        return render_template("login.html", form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            if User.query.filter_by(username=form.user_id.data).first() is not None:
                user = User.query.filter_by(username=form.user_id.data).first()
                if bcrypt.check_password_hash(user.password, form.password.data):
                    login_user(user)
                    identity_changed.send(current_app._get_current_object(), identity=Identity(user.username))
                    return redirect('/')
            return render_template('login.html', form=form, msg="Username or Password was incorrect")


@app.route('/register', methods=['GET', 'POST'])
@admin_permission.require()
def register():
    form = LoginForm()
    if request.method == 'GET':
        return render_template("register.html", form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            if User.query.filter_by(username=form.user_id.data).first() is None:
                user = User(username=form.user_id.data, password=form.password.data)
                db.session.add(user)
                db.session.commit()
            return redirect('/users')


@app.route('/logout')
def logout():
    logout_user()
    return redirect('/')


#UPLOAD ROUTES

@app.route('/uploadstudentdata', methods=['GET', 'POST'])
@admin_permission.require()
def uploadstudentdata():
    filename2 = upload(request.files['file'])
    df = read_excel(filename2)
    populate_students(df)
    # msg = "Completed Successfully"
    # except:
    #    msg = "There was an error with the upload, please try again"
        # Redirect the user to the uploaded_file route, which
        # will basicaly show on the browser the uploaded file
    return redirect("/students")


@app.route('/uploadtimetableclasslists', methods=['GET', 'POST'])
@admin_permission.require()
def uploadtimetableclasslists():
    if request.method == 'POST':
        filename2 = upload(request.files['file'])
        df = read_excel(filename2)
        populate_timetabledata(df)

        msg = "Completed Successfully"
    return render_template("uploadtimetabledata.html")





@app.route('/currentuser')
@login_required
def currentuser():
    return render_template("user.html", user=current_user)





@app.route('/updateadminsettings', methods=['POST'])
@admin_permission.require()
def updateadminsettings():
    studyperiod = request.form['studyperiod']
    year = request.form['year']
    if year != None:
        admin = Admin.get(key='currentyear')
        admin.update(value=year)
    admin = Admin.get(key='studyperiod')
    admin.update(value=studyperiod)
    for user in User.get_all(is_admin=True):
        user.update(year=year, studyperiod=studyperiod)
    Timetable.get_or_create(key='default')
    return redirect('/admin')


@app.route('/updatetimetable', methods=['POST'])
@admin_permission.require()
def updatetimetable():
    if request.form['timetable'] is not None:
        admin = Admin.get(key='timetable')
        admin.update(value=request.form['timetable'])
    return redirect('/admin')


@app.route('/uploadtutordata', methods=['GET', 'POST'])
@admin_permission.require()
def uploadtutordata():
    if request.method == 'GET':
        return render_template('uploadtutordata.html')
    elif request.method == 'POST':
        filename2 = upload(request.files['file'])
        print("Uploaded Successfully")
        df = read_excel(filename2)
        populate_tutors(df)
        print("Populated Tutors")
        # os.remove(filename2)
        msg = "Completed successfully"
        return render_template('uploadtutordata.html', msg=msg)

@app.route('/uploadtutoravailabilities', methods=['POST'])
def upload_tutor_availabilities():
    filename2 = upload(request.files['file'])
    print("Uploaded Successfully")
    df = read_excel(filename2)
    populate_availabilities(df)
    msg2 = "Completed Successfully"
    return render_template("uploadtutordata.html",msg2=msg2)

@app.route('/runtimetabler')
@admin_permission.require()
def run_timetabler():
    return render_template("runtimetabler.html", tutors=Tutor.get_all(), timeslots=Timeslot.get_all())









@app.route('/addsubjecttotutor?tutorid=<tutorid>', methods=['GET', 'POST'])
def add_subject_to_tutor(tutorid):
    if request.method == 'POST':
        subcode = request.form['subject']
        msg = linksubjecttutor(tutorid, subcode)
        return redirect(url_for('view_tutor', tutorid=tutorid))



@app.route('/addtimetabledclasstosubject?subcode=<subcode>', methods=['POST'])
def add_timetabledclass_to_subject(subcode):
    subject = Subject.get(subcode=subcode)
    timeslot = Timeslot.query.get(request.form['timeslot'])
    timetable = get_current_timetable().id
    timetabledclass = TimetabledClass.get_or_create(subjectid=subject.id, timetable=timetable, time=timeslot.id,
                                                    tutorid=subject.tutor.id)
    if len(subject.timetabledclasses) == 1:
        timetabledclass.students = subject.students
        db.session.commit()
    return redirect(url_for('view_subject', subcode=subcode))


@app.route('/admin')
@admin_permission.require()
def admin():
    return render_template('admin.html', admin=getadmin(), timetables=Timetable.get_all())


@app.route('/addtutortosubject?subcode=<subcode>', methods=['GET', 'POST'])
def add_tutor_to_subject(subcode):
    if request.method == 'POST':
        tutor = Tutor.query.get(request.form['tutor'])
        tutor.addSubject(subcode=subcode)
        return redirect(url_for('view_subject', subcode=subcode))

@app.route('/myclasses')
def get_my_classes():
    return render_template('myclasses.html',tutor=current_user.tutor)

@app.route('/myprofile')
def view_my_profile():
    return current_user.tutor.view_tutor_template()

@app.route('/addtutortosubjecttimetabler?subcode=<subcode>', methods=['GET', 'POST'])
def add_tutor_to_subject_timetabler(subcode):
    if request.method == 'POST':
        tutorid = request.form['tutor']
        msg = linksubjecttutor(tutorid, subcode)
    return redirect("/runtimetabler")





@app.route('/addsubjecttostudent?studentcode=<studentcode>', methods=['POST'])
def add_subject_to_student(studentcode):
    subcode = request.form['subject']
    msg = linksubjectstudent(studentcode, subcode)
    return redirect(url_for('view_student', studentcode=studentcode))


#DELETION ROUTES

@app.route('/deleteallclasses')
def delete_all_classes():
    timetabledclasses = TimetabledClass.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                        timetable=get_current_timetable().id).all()
    for timeclass in timetabledclasses:
        db.session.delete(timeclass)
        db.session.commit()
    timetabledclasses = TimetabledClass.query.filter_by(year=get_current_year(),
                                                        studyperiod=get_current_studyperiod(),
                                                        timetable=get_current_timetable().id).all()
    return "Done"


@app.route('/deletetutorial?tutorialid=<tutorialid>')
@login_required
def delete_tutorial(tutorialid):
    specificclass = Tutorial.query.get(tutorialid)
    sub = Subject.query.get(specificclass.subjectid)
    db.session.delete(specificclass)
    db.session.commit()
    return redirect(url_for('view_subject', subcode=sub.subcode))


@app.route('/deleteuser?username=<username>')
@admin_permission.require()
def delete_user(username):
    user = User.query.filter_by(username=username).first()
    db.session.delete(user)
    db.session.commit()
    return redirect('/users')


@app.route('/removesubject?subcode=<subcode>')
@admin_permission.require()
def remove_subject(subcode):
    sub = Subject.get(subcode=subcode)
    sub.delete()
    msg = "Completed Successfully"
    return redirect("/subjects")


@app.route('/removetutor?tutorid=<tutorid>')
@admin_permission.require()
def remove_tutor(tutorid):
    tut = Tutor.query.get(tutorid)
    tut.delete()
    msg = "Completed Successfully"
    return redirect("/tutors")


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
    subject = timetabledclass.subject
    db.session.delete(timetabledclass)
    db.session.commit()
    if subject.timetabledclasses is not None:
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



@app.route('/removetimeslot?timeslotid=<timeslotid>')
@admin_permission.require()
def remove_timeslot(timeslotid):
    timeslot = Timeslot.query.get(timeslotid)
    timeslot.delete()
    return redirect("/timeslots")


# View Data Methods (TUTORS/TIMESLOTS/ROOMS/STUDENTS/ETC)
@app.route('/tutors', methods=['GET', 'POST'])
@login_required
def view_tutors():
    form = NameForm()
    if request.method == 'GET':
        return render_template('viewtutors.html', form=form)
    else:
        if form.validate_on_submit():
            name = form.name.data
            email = form.email.data
            if Tutor.query.filter_by(name=name, year=get_current_year(),
                                     studyperiod=get_current_studyperiod()).first() is None:
                tut = Tutor(name=name,email=email)
                db.session.add(tut)
                db.session.commit()
            msg = "Record successfully added"
            return redirect("/tutors")
        return render_template('viewtutors.html',form=form)


@app.route('/rooms', methods=['GET', 'POST'])
@login_required
def view_rooms():
    form = JustNameForm()
    if request.method == 'GET':
        return render_template('viewrooms.html', form=form, rooms=Room.get_all(), timeslots=Timeslot.get_all())
    else:
        if form.validate_on_submit():
            name = form.name.data
            if Room.query.filter_by(name=name).first() is None:
                room = Room(name=name)
                db.session.add(room)
                db.session.commit()
            msg = "Record successfully added"
            return redirect("/rooms")
        return render_template('viewrooms.html', form=form, rooms=Room.get_all(), timeslots=Timeslot.get_all())


@app.route('/universities', methods=['GET', 'POST'])
@login_required
def view_universities():
    form = JustNameForm()
    if request.method == 'GET':
        return render_template('viewuniversities.html', form=form)
    else:
        if form.validate_on_submit():
            name = form.name.data
            if University.query.filter_by(name=name).first() is None:
                uni = University(name=name)
                db.session.add(uni)
                db.session.commit()
            msg = "Record successfully added"
            return redirect("/universities")
        return render_template('viewuniversities.html', form=form)


@app.route('/colleges', methods=['GET', 'POST'])
@login_required
def view_colleges():
    form = JustNameForm()
    if request.method == 'GET':
        return render_template('viewcolleges.html', form=form)
    else:
        if form.validate_on_submit():
            name = form.name.data
            if College.query.filter_by(name=name).first() is None:
                college = College(name=name)
                db.session.add(college)
                db.session.commit()
            msg = "Record successfully added"
            return redirect("/colleges")
        return render_template('viewcolleges.html', form=form)



@app.route('/subjects', methods=['GET', 'POST'])
@login_required
def view_subjects():
    form = AddSubjectForm()
    if request.method == 'GET':
        return render_template('subjects.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit() and int(current_user.is_admin) == 1:
            subname = form.subname.data
            subcode = form.subcode.data
            if Subject.query.filter_by(subcode=subcode, year=get_current_year(),
                                       studyperiod=get_current_studyperiod()).first() is None:
                sub = Subject(subcode=subcode, subname=subname)
                db.session.add(sub)
                db.session.commit()
            msg = "Record successfully added"
            return redirect("/subjects")
        return render_template('subjects.html', form=form)


@app.route('/viewclashreport')
@admin_permission.require()
def viewclashreport():
    return render_template("viewclashreport.html")


@app.route('/timetable', methods=['GET', 'POST'])
def view_timetable():
    form = AddTimetableForm()
    if request.method == 'GET':
        return render_template('viewtimetable.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            Timetable.create(key=form.key.data)
        return redirect('/timetable')


@app.route('/timeslots', methods=['GET', 'POST'])
@login_required
def view_timeslots():
    form = TimeslotForm()
    if request.method == 'GET':
        return render_template('viewtimeslots.html', form=form)
    else:
        if form.validate_on_submit():
            day = form.day.data
            time = form.time.data
            Timeslot.get_or_create(day=day, time=time)
        return render_template('viewtimeslots.html', form=form)


@app.route('/tutoravailability')
@admin_permission.require()
def managetutoravailability():
    return render_template("tutoravailability.html", timeslots=Timeslot.get_all(), tutors=Tutor.get_all())


@app.route('/students', methods=['GET', 'POST'])
@login_required
def view_students():
    form = StudentForm()
    if request.method == 'GET':
        return render_template('viewstudents.html', form=form)
    elif request.method == 'POST':
        if form.validate_on_submit():
            name = form.name.data
            studentcode = form.studentcode.data
            email = form.email.data
            Student.create(name=name, studentcode=studentcode, email=email)
            return redirect('/students')
        return render_template('viewstudents.html', form=form)


@app.route('/users')
@admin_permission.require()
def view_users():
    form = LoginForm()
    return render_template('viewusers.html', form=form)


#VIEW INDIVIDUAL PAGES

@app.route('/viewstudent?studentcode=<studentcode>', methods=['GET', 'POST'])
@login_required
def view_student(studentcode):
    student = Student.get(studentcode=studentcode)
    form = EditStudentForm(obj=student)
    if request.method == 'GET':
        if student.university is not None:
            form.university.data = student.university
        if student.college is not None:
            form.college.data = student.college
        return student.view_student_template(form)
    elif request.method == 'POST' and current_user.is_admin:
        if form.validate_on_submit():
            form.populate_obj(student)
            student.save()
            # student.update(name = form.name.data, studentcode = form.studentcode.data, university=form.university.data,college = form.college.data)
            redirect(url_for('view_student', studentcode=studentcode))
        return student.view_student_template(form)


@app.route('/viewtutor?tutorid=<tutorid>', methods=['GET', 'POST'])
@login_required
def view_tutor(tutorid):
    tutor = Tutor.query.get(tutorid)
    form = EditTutorForm(obj=tutor)
    users = User.get_all()
    choices = [(-1, "")]
    for user in users:
        choices.append((int(user.id), user.username))
    form.user.choices = choices
    if current_user.is_admin == '1' or current_user.tutor.id == tutorid:
        if request.method == 'GET':
            if tutor.user is not None:
                form.user.data = tutor.user.id
            return tutor.view_tutor_template(form)
        elif request.method == 'POST':
            if form.validate_on_submit():
                tutor.name = form.name.data
                tutor.email = form.email.data
                if form.user.data != -1:
                    tutor.user = User.query.get(form.user.data)
                    db.session.commit()
                else:
                    tutor.user = None
                    db.session.commit()
            return redirect(url_for('view_tutor', tutorid=tutorid))
    else:
        return redirect('/')


@app.route('/subject?subcode=<subcode>', methods=['GET', 'POST'])
@login_required
def view_subject(subcode):
    subject = Subject.get(subcode=subcode)
    form = AddSubjectForm(obj=subject)
    if current_user.is_admin == '1' or current_user.tutor == subject.tutor:
        if request.method == 'GET':
            return subject.view_subject_template(form)
        elif request.method == 'POST':
            if form.validate_on_submit():
                subject.update(**form.data)
                # subject.subcode = form.subcode.data
                # subject.subname = form.subname.data
                # db.session.commit()
            return redirect(url_for('view_subject', subcode=subcode))
    else:
        return redirect('/')

@app.route('/viewuser?username=<username>')
@login_required
def view_user(username):
    user = User.get(username=username)
    return user.view_user_template()


@app.route('/runtimetableprogram', methods=['GET', 'POST'])
@admin_permission.require()
def run_timetable_program():
    # addnewtimetable = request.form['addtonewtimetable']
    # print(addnewtimetable == "true")
    preparetimetable()
    return "Done"


# APP ERROR HANDLERS
@app.errorhandler(404)
def page_not_found(e):
    app.logger.error('Page not found: %s', (request.path))
    return render_template("ErrorPage.html", code=404), 404


@app.errorhandler(500)
def internal_server_error(error):
    app.logger.error('Server Error: %s', (error))
    return render_template('ErrorPage.html', code=500), 500


# AJAX ROUTES

@app.route('/getatriskclassesajax', methods=['GET', 'POST'])
def get_at_risk_classes():
    subjects = [subject.__dict__ for subject in Subject.query.filter(Subject.year == get_current_year(),
                                                                     Subject.studyperiod == get_current_studyperiod(),
                                                                     Subject.tutor != None).all() if
                subject.is_at_risk()]
    for row in subjects:
        row['_sa_instance_state'] = ""
        row['tutor'] = row['tutor'].__dict__
        row['tutor']['_sa_instance_state'] = ""
        row['classes'] = []
        subject = Subject.query.get(row['id'])
        row['recentaverageattendance'] = subject.get_recent_average_attendance()
    return '{ "data": ' + json.dumps(subjects) + '}'


@app.route('/viewtimeslotsajax')
def viewtimeslots_ajax():
    data = Timeslot.get_all()
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
        joinedload('tutor'), joinedload('room')).all()
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
        if data2[i]['room'] is not None:
            data2[i]['room'] = data2[i]['room'].__dict__
            data2[i]['room']['_sa_instance_state'] = ""
        else:
            data2[i]['room'] = {}
            data2[i]['room']['name'] = ""
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


@app.route('/viewroomsajax')
def viewrooms_ajax():
    data = Room.query.all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/viewuniversitiesajax')
def viewuniversities_ajax():
    data = University.query.all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/viewcollegesajax')
def viewcolleges_ajax():
    data = College.query.all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'

@app.route('/viewusersajax')
def viewusers_ajax():
    data = User.query.options(joinedload('tutor')).all()
    data2 = []
    for row in data:
        data2.append(row.__dict__)
    for row in data2:
        row['_sa_instance_state'] = ""
        if row['tutor'] is not None:
            row['tutor'] = row['tutor'].__dict__
            row['tutor']['_sa_instance_state'] = ""
    print(data2)
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


@app.route('/createnewclassajax', methods=['POST'])
def create_new_class_ajax():
    subjectid = int(request.form['subjectid'])
    subject = Subject.query.get(subjectid)
    tutorial = Tutorial(subjectid=subjectid, week=3, tutorid=subject.tutor.id)
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
        row['tutor']['_sa_instance_state'] = ""
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
    alltutorials = Subject.query.filter(Subject.year == get_current_year(),
                                        Subject.studyperiod == get_current_studyperiod(), Subject.tutor != None).all()
    data = {}
    for i in range(minweek, maxweek + 1):
        week = i
        tutorials = Tutorial.query.filter(Tutorial.year == get_current_year(),
                                          Tutorial.studyperiod == get_current_studyperiod(),
                                          Tutorial.week == week).all()
        key = "Week " + str(week)
        data[key] = {}
        if len(tutorials) == 0:
            data[key]['Roll Marking'] = 0
        else:
            data[key]['Roll Marking'] = 100 * round(len(tutorials) / len(alltutorials), 2)
    print(data)
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


@app.route('/numbereligiblesubjectsmappedajax')
def num_eligible_subjects_mapped():
    subjects = Subject.query.filter(Subject.tutor != None, Subject.year == get_current_year(),
                                    Subject.studyperiod == get_current_studyperiod()).all()

    allsubjects = Subject.query.filter(Subject.tutor == None, Subject.year == get_current_year(),
                                       Subject.studyperiod == get_current_studyperiod()).all()
    eligiblesubjects = [subject for subject in allsubjects if len(subject.students) >= 3]
    data = {}
    data['Eligible Subjects'] = len(eligiblesubjects)
    data['Mapped Subjects'] = len(subjects)
    data = json.dumps(data)
    return data


@app.route('/viewclashesajax')
def viewclashreportajax():
    timeslots = Timeslot.get_all()
    clashes = {}
    for timeslot in timeslots:
        clashestimeslot = {}
        students = []
        clashstudents = []
        for timeclass in timeslot.timetabledclasses:
            for student in timeclass.students:
                if student not in students:
                    clashestimeslot[student.id] = {}
                    clashestimeslot[student.id]['student'] = student
                    clashestimeslot[student.id]['timeslot'] = timeslot
                    clashestimeslot[student.id]['subjects'] = []
                    students.append(student)
                clashestimeslot[student.id]['subjects'].append(timeclass.subject.subname)
                if len(clashestimeslot[student.id]['subjects']) >= 2:
                    clashstudents.append(student.id)
        clashes[timeslot.id] = {key: clashestimeslot[key] for key in clashstudents}
        clashes[timeslot.id]['time'] = timeslot.day + " " + timeslot.time

    data2 = []
    for row in clashes.keys():
        if clashes[row] != {}:
            for key in clashes[row].keys():
                if isinstance(clashes[row][key], dict):
                    data2.append(clashes[row][key])
    print(data2)
    for row in data2:
        # row['_sa_instance_state'] = ""
        print(row)
        row['timeslot'] = row['timeslot'].__dict__
        row['timeslot']['_sa_instance_state'] = ""
        row['student'] = row['student'].__dict__
        row['student']['_sa_instance_state'] = ""
        row['timeslot']['availabiletutors'] = []
        row['timeslot']['timetabledclasses'] = []
    print(data2)
    data = json.dumps(data2)
    return '{ "data" : ' + data + '}'


@app.route('/updatesubjectrepeats', methods=['POST'])
def update_subject_repeats():
    subject = Subject.query.get(int(request.form['subject']))
    subject.update(repeats=int(request.form['repeats']))
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


@app.route('/viewmysubjectsajax')
def viewmysubjects_ajax():
    data = Subject.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                   tutor=current_user.tutor).options(
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


@app.route('/useradminajax', methods=['POST'])
def user_admin_ajax():
    user = User.query.get(int(request.form['user_id']))
    adminvalue = int(request.form['admin'])
    if user.is_admin == '1' and user.username != 'admin':
        if adminvalue == 0:
            user.is_admin = '0'
            db.session.commit()
    else:
        if adminvalue == 1:
            print(adminvalue)
            user.is_admin = '1'
            db.session.commit()
    print(user.is_admin)
    return "Done"


@app.route('/maptutoruserajax', methods=['POST'])
def user_tutor_mapping():
    user = User.query.get(int(request.form['user_id']))
    if int(request.form['tutor_id']) != -1:
        tutor = Tutor.query.get(int(request.form['tutor_id']))
        user.tutor = tutor
        db.session.commit()
    else:
        user.tutor = None
        db.session.commit()
    return "Done"


@app.route('/updateclasstimeajax', methods=['POST'])
def update_class_time_ajax():
    classid = int(request.form['classid'])
    week = int(request.form['week'])
    tutorial = Tutorial.query.get(classid)
    tutorial.week = week
    db.session.commit()
    print(tutorial.week)
    return json.dumps("Done")


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
        tutorials = Tutorial.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                             subjectid=subject.id, week=i).options(joinedload('attendees')).all()
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
    for i in range(minweek, maxweek + 1):
        week = i
        tutorials = Tutorial.query.filter(Tutorial.year == get_current_year(),
                                          Tutorial.studyperiod == get_current_studyperiod(),
                                          Tutorial.week == week).all()
        key = "Week " + str(week)
        numstudents = 0
        numattended = 0
        for tutorial in tutorials:
            numstudents += len(tutorial.subject.students)
            numattended += len(tutorial.attendees)
        data[key] = {}
        if numstudents > 0:
            data[key]['Attendance Rate'] = 100 * round(numattended / numstudents, 2)
        else:
            data[key]['Attendance Rate'] = 0

    return json.dumps(data)


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


@app.route('/updateclassroomajax', methods=['POST'])
def update_class_room_ajax():
    timeclass = TimetabledClass.get(id=int(request.form['timeclassid']))
    if int(request.form['roomid']) != -1:
        room = Room.query.get(int(request.form['roomid']))
        timeclass.update(room=room)
    else:
        timeclass.update(room=None)
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


@app.route('/document')
def document_test():
    subject = Subject.get(subcode='MAST10006')
    students = subject.students
    timeslot = subject.timetabledclasses[0].timeslot
    print()
    room = subject.timetabledclasses[0].room
    print(room)
    document = create_roll(students, subject, timeslot, room)
    return send_file('../demo.docx')


@app.route('/downloadroll?classid=<classid>')
def download_roll(classid):
    document = get_roll(classid)
    return send_file(document, as_attachment=True)
