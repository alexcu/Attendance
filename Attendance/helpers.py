from Attendance import app, db, executor
from Attendance.models import *
from pulp import LpMinimize, LpProblem, LpVariable, lpSum, LpInteger, LpBinary, LpStatus

#TIMETABLE CODE
def runtimetable(STUDENTS, SUBJECTS, TIMES, day, DAYS, TEACHERS, SUBJECTMAPPING, REPEATS, TEACHERMAPPING,
                 TUTORAVAILABILITY, maxclasssize, minclasssize, nrooms):
    print("Running solver")
    model = LpProblem('Timetabling', LpMinimize)
    #Create Variables
    print("Creating Variables")
    assign_vars = LpVariable.dicts("StudentVariables",[(i, j,k,m) for i in STUDENTS for j in SUBJECTS for k in TIMES for m in TEACHERS], 0, 1, LpBinary)
    subject_vars = LpVariable.dicts("SubjectVariables",[(j,k,m) for j in SUBJECTS for k in TIMES for m in TEACHERS], 0, 1, LpBinary)

    #c
    num930classes = LpVariable.dicts("930Classes", [(i) for i in TIMES], lowBound = 0, cat = LpInteger)
    #w
    daysforteachers = LpVariable.dicts("numdaysforteachers", [(i,j) for i in TEACHERS for j in range(len(DAYS))], 0,1,LpBinary)
    #p
    daysforteacherssum = LpVariable.dicts("numdaysforteacherssum", [(i) for i in TEACHERS],0,cat = LpInteger)
    #variables for student clashes
    studenttime = LpVariable.dicts("StudentTime", [(i,j) for i in STUDENTS for j in TIMES],lowBound=0,upBound=1,cat=LpBinary)
    studentsum = LpVariable.dicts("StudentSum", [(i) for i in STUDENTS],0,cat = LpInteger)

    #Count the days that a teacher is rostered on. Make it bigger than a small number times the sum
    #for that particular day.
    for m in TEACHERS:
        for d in range(len(day)):
            model += daysforteachers[(m, d)] >= 0.1 * lpSum(
                subject_vars[(j, k, m)] for j in SUBJECTS for k in DAYS[day[d]])
            model += daysforteachers[(m, d)] <= lpSum(subject_vars[(j, k, m)] for j in SUBJECTS for k in DAYS[day[d]])
    for m in TEACHERS:
        model += daysforteacherssum[(m)] == lpSum(daysforteachers[(m, d)] for d in range(len(day)))

    print("Constraining tutor availability")
    #This bit of code puts in the constraints for the tutor availability.
    #It reads in the 0-1 matrix of tutor availability and constrains that no classes
    # can be scheduled when a tutor is not available.
    #The last column of the availabilities is the tutor identifying number, hence why we have
    #used a somewhat convoluted idea down here.
    for m in TEACHERS:
        for k in TIMES:
            if k not in TUTORAVAILABILITY[m]:
                model += lpSum(subject_vars[(j,k,m)] for j in SUBJECTS) == 0


    #Constraints on subjects for each students
    print("Constraining student subjects")
    for i in STUDENTS:
        for j in SUBJECTS:
            if i in SUBJECTMAPPING[j]:
                model += lpSum(assign_vars[(i,j,k,m)] for k in TIMES for m in TEACHERS) == 1
            else:
                model += lpSum(assign_vars[(i,j,k,m)] for k in TIMES for m in TEACHERS) == 0



    #This code means that students cannot attend a tute when a tute is not running
    #But can not attend a tute if they attend a repeat.
    for i in STUDENTS:
        for j in SUBJECTS:
            for k in TIMES:
                for m in TEACHERS:
                    model += assign_vars[(i,j,k,m)] <= subject_vars[(j,k,m)]


    #Constraints on which tutor can take each class
    #This goes through each list and either constrains it to 1 or 0 depending if
    #the teacher needs to teach that particular class.
    print("Constraining tutor classes")
    for m in TEACHERS:
        for j in SUBJECTS:
            if j in TEACHERMAPPING[m]:
                #THIS WILL BE CHANGED TO NUMBER OF REPEATS
                model+= lpSum(subject_vars[(j,k,m)] for k in TIMES) == REPEATS[j]
            else:
                model += lpSum(subject_vars[(j,k,m)] for k in TIMES) == 0

    #General Constraints on Rooms etc.
    print("Constraining times")
    # For each time cannot exceed number of rooms
    for k in TIMES:
        model += lpSum(subject_vars[(j,k,m)] for j in SUBJECTS for m in TEACHERS) <= nrooms

    #Teachers can only teach one class at a time
    for k in TIMES:
        for m in TEACHERS:
            model += lpSum(subject_vars[(j,k,m)] for j in SUBJECTS) <= 1

    #STUDENT CLASHES
    for i in STUDENTS:
        for k in TIMES:
            model += studenttime[(i,k)] <= lpSum(assign_vars[(i,j,k,m)] for j in SUBJECTS for m in TEACHERS)/2
            model += studenttime[(i, k)] >= 0.3*(0.5*lpSum(assign_vars[(i, j, k, m)] for j in SUBJECTS for m in TEACHERS) -0.5)

    for i in STUDENTS:
        model += studentsum[(i)] == lpSum(studenttime[(i,k)] for k in TIMES)

    #This minimizes the number of 9:30 classes.
    for i in TIMES:
        if i.find('21:30') != -1:
            model += num930classes[(i)] == lpSum(subject_vars[(j,i,m)] for j in SUBJECTS for m in TEACHERS)

        else:
            model += num930classes[(i)] == 0

    print("Setting objective function")

    #Class size constraint
    for j in SUBJECTS:
        for k in TIMES:
            for m in TEACHERS:
                model +=lpSum(assign_vars[(i,j,k,m)] for i in STUDENTS) >= minclasssize*subject_vars[(j,k,m)]
                model += lpSum(assign_vars[(i,j,k,m)] for i in STUDENTS) <= maxclasssize

    #Solving the model
    model += (100*lpSum(studentsum[(i)] for i in STUDENTS) + lpSum(num930classes[(i)] for i in TIMES) + 500*lpSum(daysforteacherssum[(m)] for m in TEACHERS))
    print("Solving Model")
    model.solve()
    print("Status:", LpStatus[model.status])
    print("Complete")
    for j in SUBJECTS:
        subject = Subject.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                          subcode=j).first()
        for k in TIMES:
            timesplit = k.split(' ')
            timeslot = Timeslot.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                timetable=get_current_timetable(), day=timesplit[0],
                                                time=timesplit[1]).first()
            for m in TEACHERS:
                tutor = Tutor.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                              name=m).first()
                if subject_vars[(j, k, m)].varValue == 1:

                    timetabledclass = TimetabledClass(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                                      subjectid=subject.id, timetable=get_current_timetable(),
                                                      time=timeslot.id, tutorid=tutor.id)
                    db.session.add(timetabledclass)
                    db.session.commit()

                    for i in STUDENTS:

                        if assign_vars[(i, j, k, m)].varValue == 1:
                            student = Student.query.filter_by(year=get_current_year(),
                                                              studyperiod=get_current_studyperiod(), name=i).first()
                            timetabledclass.students.append(student)
                            db.session.commit()
    print("Status:", LpStatus[model.status])
    return model.objective.value()


def preparetimetable(addtonewtimetable=False):
    # if addtonewtimetable == "true":
    #    timetable = Timetable(get_current_year(),get_current_studyperiod())
    #    db.session.add(timetable)
    #    db.session.commit()
    #    admin = Admin.query.filter_by(key="timetable").first()
    #    admin.value = timetable.id
    #    db.session.commit()
    print("Preparing Timetable")
    SUBJECTS = []
    SUBJECTMAPPING = {}
    STUDENTS = []
    REPEATS = {}
    TEACHERS = []
    TUTORAVAILABILITY = {}
    TEACHERMAPPING = {}
    allsubjects = Subject.query.filter(Subject.year == get_current_year(),
                                       Subject.studyperiod == get_current_studyperiod(), Subject.tutor != None).all()
    alltutors = []
    for subject in allsubjects:
        SUBJECTMAPPING[subject.subcode] = []
        REPEATS[subject.subcode] = subject.repeats
        SUBJECTS.append(subject.subcode)
        TEACHERS.append(subject.tutor.name)
        if subject.tutor not in alltutors:
            alltutors.append(subject.tutor)
        for student in subject.students:
            STUDENTS.append(student.name)
            SUBJECTMAPPING[subject.subcode].append(student.name)
    STUDENTS = list(set(STUDENTS))
    TEACHERS = list(set(TEACHERS))
    for tutor in alltutors:
        TUTORAVAILABILITY[tutor.name] = []
        TEACHERMAPPING[tutor.name] = []
        for timeslot in tutor.availabletimes:
            TUTORAVAILABILITY[tutor.name].append(timeslot.day + " " + timeslot.time)
        for subject in tutor.subjects:
            TEACHERMAPPING[tutor.name].append(subject.subcode)

    maxclasssize = 400
    minclasssize = 1
    nrooms = 12
    TIMES = []
    day = []
    timeslots = Timeslot.query.filter_by(year=get_current_year(), studyperiod=get_current_studyperiod(),
                                         timetable=get_current_timetable()).all()
    for timeslot in timeslots:
        TIMES.append(timeslot.day + " " + timeslot.time)
        day.append(timeslot.day)
    day = list(set(day))
    DAYS = {}
    for d in day:
        DAYS[d] = []
    for timeslot in timeslots:
        DAYS[timeslot.day].append(timeslot.day + " " + timeslot.time)
    print("Everything ready")
    executor.submit(runtimetable,STUDENTS, SUBJECTS, TIMES, day, DAYS, TEACHERS, SUBJECTMAPPING, REPEATS, TEACHERMAPPING,
                       TUTORAVAILABILITY, maxclasssize, minclasssize, nrooms)
    return render_template("viewtimetable.html")
