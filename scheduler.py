import pymysql
import warnings
from time import sleep
from datetime import datetime, timedelta

from components.sql import Cursor, WriteCursor
from components.tests import add_test_scheduling


def get_starting_time():
    """
    Returns the time of the next test schedule

    :returns: time of next schedule (datetime.datetime)
    """
    now = datetime.utcnow()
    # Round to nearest thirty minute interval (XX:00 or XX:30)
    now = now.replace(second=0, microsecond=0)
    if now.minute <= 30:
        return now.replace(minute=30)
    return now.replace(minute=0) + timedelta(hours=1)


def get_scheduling_times(start):
    """
    Returns the scheduling times for the next 100 days beginning from given
    date & time in 15 minute intervals.

    :param start: the date & time of first schedule (datetime.datetime)
    :returns: list of scheduling times (list of datetime isoformat strings)
    """
    times = [start + i * timedelta(minutes=15) for i in range(4 * 24 * 100)]
    return list(map(lambda x: x.isoformat(), times))


def schedule_exists(time):
    """
    Checks whether a schedule for given time exists.

    :param time: the time to check for (datetime.datetime)
    :returns: whether a schedule exists (boolean)
    """
    with Cursor() as c:
        sql = """select * from test_schedule
              where by_user = 'scheduler' and scheduled_for = %s; """
        c.execute(sql, (time))
    return len(c.fetchall()) > 0


def loop():
    """
    Loops infinitely and adds the test schedule for the next 100 days
    """
    print("[Scheduler] Started")
    # Do not print warnings about ignored primary keys error
    # warnings.filterwarnings('ignore', category=pymysql.Warning)
    while True:
        now = datetime.utcnow().isoformat()
        for time in get_scheduling_times(get_starting_time()):
            if not schedule_exists(time):
                add_test_scheduling('scheduler', now, time)
        print("[Scheduler] Added new round of schedules")
        # Sleep for 15 minutes
        sleep(60 * 15)
