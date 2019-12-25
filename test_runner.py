import pymysql
import threading
from time import sleep
from subprocess import run
from datetime import datetime

from components.sql import Cursor, WriteCursor


def run_cmd(cmd):
    """
    Returns the CompletedProcess instance of running the given command in a
    shell and capturing stdout, stderr and returncode.

    :param cmd: the command to execute (string)
    :returns: CompletedProcess instance
    """
    return run(cmd, capture_output=True, shell=True)


def get_returncode(process):
    """
    Get the returncode of a CompletedProcess instance.

    :param process: CompletedProcess instance
    :returns: the process's returncode (int)
    """
    return process.returncode


def get_output(process):
    """
    Returns the output of given CompletedProcess instance. Uses both stdout
    and stderr and removes test's bash coloring.

    :param process: CompletedProcess instance
    :returns: the process's output (string)
    """
    output = process.stdout.decode('utf-8') + process.stderr.decode('utf-8')
    output = (output.replace('...\b\b\b\033[0;32m[OK]\033[0m', '[OK]')   # Remove green color
              .replace('...\b\b\b\033[0;31m[FAIL]\033[0m', '[FAIL]'))    # Remove red color
    return output


def check_output(output):
    """
    Checks whether the output ends with a test summary, i.e. nothing went
    wrong when executing the test.

    :param output: the test output (string)
    :returns: whether test summary exists (boolean)
    """
    return "All tests passed!" in output or " test(s) failed!" in output


def parse_output(output, returncode):
    """
    Count how many tests have been passed and how many have been failed.
    Handles tests that have not ended correctly by using dummy values
    instead.

    :param output: the test output (string)
    :param returncode: the test's returncode (int)
    :returns: number of tests passed, number of tests failed
    """
    # If test has failed before the test summary, return dummy values
    if returncode != 0 or not check_output(output):
        return 0, 1
    passed = output.count("[OK]")
    failed = output.count("[FAIL]")
    return passed, failed


def execute_test(test, vm):
    """
    Executes the given test on given vm. Saves the results in the database.

    :param test: test to run (string, e.g. 'dns')
    :param vm: vm to run test on (string, e.g. 'vm01')
    """
    # Execute test
    cmd = "ssh {0} \"python3.7 /root/tests/{1}.py\"".format(vm, test)
    p = run_cmd(cmd)
    # Get values for database entry
    passed, failed = parse_output(get_output(p), get_returncode(p))
    output = get_output(p)
    date = datetime.utcnow().isoformat()
    # Insert test into database
    with WriteCursor() as c:
        sql = """insert into test_results
              values ( %s, %s, %s, %s, %s, %s );"""
        c.execute(sql, (test, passed, failed, output, date, vm))


def get_scheduled_tests():
    """
    Gets all the tests scheduled for now or before call from the database.

    :returns: list of tests (list of strings, e.g. ['dns'])
    """
    with Cursor() as c:
        sql = """select run_on.test, run_on.vm from run_on
                where exists (
                    select * from test_schedule
                    where scheduled_for <= utc_timestamp() and run = False
                );"""
        c.execute(sql)
        return c.fetchall()


def set_schedules_run():
    """
    Sets all the tests scheduled for before current time to run.
    """
    with WriteCursor() as c:
        sql = """update test_schedule
              set run = True
              where scheduled_for <= utc_timestamp();"""
        c.execute(sql)


def loop():
    """
    Loops infinitely and executes scheduled tests
    """
    while True:
        try:
            tests = get_scheduled_tests()
        except pymysql.err.OperationalError as e:
            print("[Test runner] Connection to database failed: {0}".format(e))
            sleep(5)
            continue
        # If there are tests scheduled, execute them and mark them run
        if len(tests) > 0:
            print(("[Test runner] Creating {0} threads for executing tests"
                   .format(len(tests))))
            threads = [threading.Thread(target=execute_test, args=test)
                       for test in tests]
            print("[Test runner] Starting threads")
            [t.start() for t in threads]
            print("[Test runner] Joining threads")
            [t.join() for t in threads]
            set_schedules_run()
            print("[Test runner] Schedule(s) set to run, loop finished")
        # Do not dos database
        sleep(5)


if __name__ == "__main__":
    loop()
