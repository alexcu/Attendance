# Attendance and Timetabling System

This is the attendance and timetabling system for International House, the
University of Melbourne.

## Setup

1. Install Python v3.4.3 or greater.
2. Install dependencies using pip:

    ```
    $ pip install -r requirements.txt
    ```

3. Make your configurations in `attendance/config.py`.
4. Open `attendance/__init__.py` in a text editor.
5. Comment out the `init_db` function call on line 87.
6. Run the following commands to create and migrate the database:

    ```
    $ python manage.py db init
    $ python manage.py db migrate
    $ python manage.py db upgrade
    ```

7. Uncomment out line 87 as you did in step 5.

## Run

To run, use:

```
$ python manage.py runserver
```
