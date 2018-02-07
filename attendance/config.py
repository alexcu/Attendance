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
        ['GHB1', True,20],
        ['GHB2', True,20],
        ['GHB3', True,20],
        ['GHB4', False,20],
        ['GHB5', False,20],
        ['GHB6', False,20],
        ['GHB7', False,20],
        ['Peter Waylen', False,20],
        ['Ronald Cowan', True,20],
        ['Frank Larkins', False,20],
        ['Mavis Jackson', True,20],
        ['Library Project Room', False,5]
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
