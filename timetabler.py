from pulp import *



STUDENTS = ["Justin Smallwood", "Tom Cox"]
SUBJECTS = ["Accelerated Mathematics 2", "Introduction to Actuarial Studies", "Myth, Art and Culture"]
TIMES =["Monday 7:30", "Tuesday 8:30","Wednesday 9:30", "Tuesday 7:30", "Tuesday 5:30", "Wednesday 5:30", "Wednesday 7:30", "Monday 9:30", "Monday 8:30"]
MONDAY = ["Monday 7:30", "Monday 8:30", "Monday 9:30"]
TUESDAY = ["Tuesday 5:30", "Tuesday 8:30", "Tuesday 7:30"]
WEDNESDAY = ["Wednesday 9:30", "Wednesday 5:30", "Wednesday 7:30"]
DAYS = [MONDAY, TUESDAY,WEDNESDAY]
TEACHERS = ["Fiona Yew", "Darren Lalchand"]
SUBJECTMAPPING = {}
SUBJECTMAPPING["Justin Smallwood"] = ["Accelerated Mathematics 2", "Myth, Art and Culture"]
SUBJECTMAPPING["Tom Cox"] = ["Introduction to Actuarial Studies", "Accelerated Mathematics 2"]

TEACHERMAPPING = {}
TEACHERMAPPING["Fiona Yew"] = ["Introduction to Actuarial Studies"]
TEACHERMAPPING["Darren Lalchand"] = ["Accelerated Mathematics 2", "Myth, Art and Culture"]

REPEATS = {}
REPEATS["Introduction to Actuarial Studies"] = 1
REPEATS["Accelerated Mathematics 2"] = 1
REPEATS["Myth, Art and Culture"] = 1


TUTORAVAILABILITY = {}
TUTORAVAILABILITY["Fiona Yew"] = ["Wednesday 9:30", "Tuesday 5:30", "Monday 8:30", "Tuesday 7:30"]
TUTORAVAILABILITY["Darren Lalchand"] = ["Tuesday 8:30", "Wednesday 5:30", "Wednesday 7:30", "Monday 7:30", "Monday 9:30"]
#Controls the number of variables to create
maxclasssize = 20
minclasssize = 1
nrooms = 12

def runtimetable(STUDENTS,SUBJECTS,TIMES,DAYS,TEACHERS,SUBJECTMAPPING, REPEATS,TEACHERMAPPING,TUTORAVAILABILITY,maxclasssize,minclasssize,nrooms):
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
        for d in range(len(DAYS)):

            model += daysforteachers[(m,d)] >= 0.1*lpSum(subject_vars[(j,k,m)] for j in SUBJECTS for k in DAYS[d])
            model += daysforteachers[(m,d)] <=  lpSum(subject_vars[(j, k, m)] for j in SUBJECTS for k in DAYS[d])
    for m in TEACHERS:
        model += daysforteacherssum[(m)] == lpSum(daysforteachers[(m,d)] for d in range(len(DAYS)))

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
              if j in SUBJECTMAPPING[i]:
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
        if i.find('9:30') != -1:
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
    model.solve()

    for i in STUDENTS:
        for j in SUBJECTS:
            for k in TIMES:
                for m in TEACHERS:
                    if assign_vars[(i,j,k,m)].varValue == 1:
                        print((i,j,k,m))
    print(model.objective.value())

runtimetable(STUDENTS,SUBJECTS,TIMES,DAYS,TEACHERS,SUBJECTMAPPING,REPEATS,TEACHERMAPPING,TUTORAVAILABILITY,maxclasssize,minclasssize,nrooms)