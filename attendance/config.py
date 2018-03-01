appcfg = {
    # Path to upload files directory
    "upload": '/path/to/upload/directory',
    # Database string
    "dbstring": 'sqlite:////database/string',
    # Secret key for password hashing
    "secretkey": 'internationalhouseattendanceprogram',
    # Administrator password
    "adminpassword": 'password',
    # Logging file
    "log": '/path/to/log.log',
    # Default start and study period
    "startyear" : '2018',
    "startstudyperiod" : "Semester 1",
    # Rooms avaliable (Name, HasProjector?, Capacity)
    "rooms" : [
        ['GHB1', True, 20],
        ['GHB2', True, 20],
        ['GHB3', True, 20],
        ['GHB4', False, 20],
        ['GHB5', False, 20],
        ['GHB6', False, 20],
        ['GHB7', False, 20],
        ['Peter Waylen', False, 20],
        ['Ronald Cowan', True, 20],
        ['Frank Larkins', False, 20],
        ['Mavis Jackson', True, 20],
        ['Library Project Room', False, 4]
    ],
    # Timeslots avaliable and preference (True/False)
    "timeslots": [
        ['Monday 17:30', False],
        ['Monday 19:30', True],
        ['Monday 20:30', True],
        ['Monday 21:30', False],
        ['Tuesday 17:30', False],
        ['Tuesday 19:30', True],
        ['Tuesday 20:30', True],
        ['Tuesday 21:30', False],
        ['Wednesday 17:30', False],
        ['Wednesday 19:30', True],
        ['Wednesday 20:30',True],
        ['Wednesday 21:30', False]
    ],
    # Schema of XLS Enrolment File (mapping between column headers)
    "enrolment_schema": {
        "student_id": "Student Id",
        "student_first_name": "Given Name",
        "student_last_name": "Family Name",
        "subject_code": "Component Study Package Code",
        "subject_name": "Component Study Package Title",
        "study_period": "Study Period"
    },
    "max_class_size": 15,
    "min_class_size": 3,
    "default_room_capacity": 20
}
