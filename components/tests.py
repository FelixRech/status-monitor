from datetime import datetime
from components.sql import WriteCursor, Cursor, flatten_results


def get_all_weeks():
    """
    Get all the weeks for which exist tests in the database.

    :returns: list of weeks (list of ints, e.g. [1, 2])
    """
    with Cursor() as c:
        sql = """select distinct week from weeks
              where exists (
                  select * from run_on
                  where weeks.test = run_on.test)
              order by week, week_num;"""
        c.execute(sql)
        weeks = c.fetchall()
    # Flatten list, e.g. from ((1), (2)) to [1,2]
    return flatten_results(weeks)


def get_tests_in_week(week):
    """
    Get all the tests for a given week.
    Limited to the tests that have actually been executed at some point.

    :param week: week to get tests for
    :returns: a list of tests (list of strings, e.g. ['dns'])
    """
    with Cursor() as c:
        sql = """select distinct weeks.test from weeks
              inner join run_on on weeks.test = run_on.test
              inner join test_results on weeks.test = test_results.test and run_on.vm = test_results.vm
              where weeks.week = %s
              order by test_results.date DESC;"""
        c.execute(sql, (week))
        tests = c.fetchall()
    # Flatten list, e.g. from (('dns'), ('dhcp')) to ['dns', 'dhcp']
    return flatten_results(tests)


def get_all_vms():
    """
    Get all the vms listed in the database
    Limited to the vms on which at least one test has run at some point.

    :returns: list of vms (list of strings, e.g. ['vm01', 'vm02'])
    """
    with Cursor() as c:
        sql = """select distinct vms.vm from vms
              inner join run_on on vms.vm = run_on.vm
              inner join test_results on vms.vm = test_results.vm
              order by vms.vm ASC;"""
        c.execute(sql)
        tests = c.fetchall()
    # Flatten list, e.g. from (('vm01'), ('vm02')) to ['vm01', 'vm02']
    return flatten_results(tests)


def get_tests_of_vm(vm):
    """
    Get all the tests that are associated with a given vm and which week they
    are scheduled for.
    Limited to tests that have actually been run on the vm at some point.

    :param vm: the name of the vm (string, e.g. 'vm01')
    :returns: list of weeks & tests (list of pairs, e.g. [[3, 'dns']])
    """
    with Cursor() as c:
        sql = """select distinct weeks.week, test_results.test from test_results
              inner join run_on on test_results.vm = run_on.vm and test_results.test = run_on.test
              inner join weeks on test_results.test = weeks.test
              where test_results.vm = %s
              order by weeks.week ASC;"""
        c.execute(sql, (vm))
        return c.fetchall()


def get_tests_names_of_vm(vm):
    """
    Get all the tests that are associated with a given vm.
    Limited to tests that have actually been run on the vm at some point.

    :param vm: the name of the vm (string, e.g. 'vm01')
    :returns: list of tests (list of strings, e.g. ['dns', 'dhcp'])
    """
    return list(map(lambda x: x[1], get_tests_of_vm(vm)))


def get_last_test(test, vm='%'):
    """
    Returns the results of the last run of a given test.

    :param test: test to get results for (string, e.g. 'dns')
    :param vm: limit to results on this vm (string, e.g. 'vm01')
    :returns: results as dict if there are any, e.g. {'passed': 2, ...},
              None otherwise
    """
    with Cursor() as c:
        # test_results.vm like %s works since default value for arg vm is '%'
        sql = """select passed, failed, output, date, test_results.vm
              from test_results
              inner join run_on on test_results.vm = run_on.vm
              where test_results.test = %s and test_results.vm like %s
              order by date DESC
              limit 1;"""
        c.execute(sql, (test, vm))
        row = c.fetchone()
        # If row is None, now results exist for specified arguments
        if row is None:
            return None
        passed, failed, output, date, vm = row
    return {'passed': passed, 'failed': failed,
            'output': output, 'date': date, 'vm': vm}


def summarize_tests(tests):
    """
    Summarises a list of tests by looking up the results of their last
    execution and returning the number of (completely) passed and failed
    tests among them.

    :param tests: list of tests (list of strings, e.g. ['dns', 'dhcp'])
    :returns: number of passed & failed tests (pair of ints, e.g. 5, 0)
    """
    # Get the tests' results
    results = list(filter(None, map(get_last_test, tests)))
    # Extract how many of them did not fail any check -> passed tests
    passed = len(list(filter(lambda x: x['failed'] == 0, results)))
    # The number of failed tests is (# of all tests) - (# of passed tests)
    failed = len(results) - passed
    return passed, failed


def next_tests_scheduled():
    """
    Returns the next time for which a test is scheduled.

    :returns: time (datetime.dateime) or None if no tests are scheduled
    """
    with Cursor() as c:
        sql = """select scheduled_for
              from test_schedule
              where run = False
              order by scheduled_for ASC
              limit 1;
              """
        c.execute(sql)
        sched = c.fetchone()
    return sched if sched is None else sched[0]


def formatted_next_tests_scheduled():
    """
    Returns a formatted version of the time on which the next round of tests
    are scheduled.

    The format is best specified by examples: 'never', 'now', 'in 2 days'

    :returns: formatted time of next test (string)
    """
    sched = next_tests_scheduled()
    if sched is None:
        return 'never'
    if sched <= datetime.utcnow():
        return 'now'
    diff = sched - datetime.utcnow()
    if diff.days >= 1:
        return "in {0} days".format(diff.days)
    if diff.seconds >= 60:
        return "in {0} min.".format(int(diff.seconds / 60))
    else:
        return "in {0} sec.".format(int(diff.seconds))


def add_test_scheduling(by, sched_on=None, sched_for=None):
    """
    Schedules tests' execution for given time and by given user.
    Defaults to scheduled on and for current time.

    :param by: username that added test scheduling
    :param sched_on: tests scheduled on (optional, defaults to now)
    :param sched_for: tests scheduled for (optional, defaults to now)
    """
    # Default to now if sched_on and/or sched_for not specified
    sched_on = datetime.utcnow() if sched_on is None else sched_on
    sched_for = datetime.utcnow() if sched_for is None else sched_for
    with WriteCursor() as c:
        sql = """insert into test_schedule
              values ( % s, % s, % s, 0 ); """
        c.execute(sql, (by, sched_on, sched_for))


def scheduled_test_ran_since(date):
    """
    Returns whether a scheduled tests have run since given date.
    (Returns whether schedules for after date have been marked run).

    :param date: given date (datetime.datetime or MySQL accepted string)
    :returns: whether tests have run (boolean)
    """
    with Cursor() as c:
        sql = """select * from test_schedule
              where scheduled_for >= %s
              and scheduled_for <= now()
              and run = True;"""
        c.execute(sql, (date))
    # If cursor returns entries, tests have been run
    return len(c.fetchall()) > 0
