appcfg = {
    # Path to upload files directory
    "upload": '/path/to/uploads/directory',
    # Database string
    "dbstring": 'sqlite:////path/to/database.db',
    # Secret key for password hashing
    "secretkey": 'internationalhouseattendanceprogram',
    # Administrator password
    "adminpassword": 'password',
    # Logging file
    "startyear" : '2018',
    "startstudyperiod" : "Semester 1",
    "rooms" : [
        ['GHB1', True],
        ['GHB2', True],
        ['GHB3', True],
        ['GHB4', False],
        ['GHB5', False],
        ['GHB6', False],
        ['GHB7', False],
        ['Peter Waylen', False],
        ['Ronald Cowan', True],
        ['Frank Larkins', False],
        ['Mavis Jackson', True],
        ['Library Project Room', False]
    ],
    "timeslots": [
        ['Monday 19:30', True],
        ['Monday 20:30', True],
        ['Monday 21:30', False],
        ['Tuesday 19:30', True],
        ['Tuesday 20:30', True],
        ['Tuesday 21:30', False],
        ['Wednesday 19:30', True],
        ['Wednesday 20:30',True],
        ['Wednesday 21:30', False]
    ]
}
