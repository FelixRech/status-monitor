import pymysql


class Cursor(object):
    """
    Returns a database read-only cursor for use in with statements.

    This is a read-only cursor, changes are not committed.

    Usage:
        with Cursor() as c:
            c.execute(read_sql)
    """

    def __init__(self, host='localhost', port='3306',
                 user='user', password='pw', db='db'):
        self.db = pymysql.connect(
            host=host,
            user=user,
            password=password,
            database=db)

    def __enter__(self):
        return self.db.cursor()

    def __exit__(self, exc_type, exc_val, trace):
        self.db.close()


class WriteCursor(Cursor):
    """
    Returns a database cursor for use in with statements.

    Will commit changes made using the cursor.

    Usage:
        with Cursor() as c:
            c.execute(write_sql)
    """

    def __exit__(self, exc_type, exc_val, trace):
        self.db.commit()
        super().__exit__(exc_type, exc_val, trace)


def flatten_results(results):
    """
    Flatten the results of a cursor.fetchall() call.

    :param results: results of cursor.fetall(), e.g. ((el1), (el2))
    :returns: flattened results, e.g. [el1, el2]
    """
    return list(map(lambda x: x[0], results))


def setup_database():
    """
    Sets the database up. This includes creating the necessary tables if
    they don't exist. Note that you have to manually create a database user
    before calling this function!
    """
    with WriteCursor() as c:
        # Create the table containing users and their passwords
        sql = """create table if not exists users (
                username varchar(48),
                admin boolean not null,
                pw_hash varchar(128) not null,
                primary key (username)
              );"""
        c.execute(sql)
        # Add the scheduler user
        sql = """insert ignore into users values ("scheduler", 1, "*");"""
        c.execute(sql)
        # Create the table containing the active sessions
        sql = """create table if not exists sessions (
                username varchar(48),
                id varchar(48) not null,
                expires datetime,
                logout datetime not null,
                primary key (username, id, expires),
                foreign key (username) references users (username),
                constraint uc_session_id unique (id)
              );"""
        c.execute(sql)
        # Create the table containing the VMs
        sql = """create table if not exists vms (
                vm varchar(8),
                primary key (vm)
              );"""
        c.execute(sql)
        # Create the table containing the weeks
        sql = """create table if not exists weeks (
                test varchar(48),
                week tinyint not null,
                week_num tinyint not null,
                primary key (test),
                constraint uc_week_num unique (week, week_num)
              );"""
        c.execute(sql)
        # Create the table containing which test to run on which VM
        sql = """create table if not exists run_on (
                test varchar(48),
                vm varchar(8),
                primary key(test, vm),
                foreign key (test) references weeks (test),
                foreign key (vm) references vms (vm)
              );"""
        c.execute(sql)
        # Create the table containing the test results
        sql = """create table if not exists test_results (
                test varchar(48),
                passed tinyint not null,
                failed tinyint not null,
                output text not null,
                date datetime not null,
                vm varchar(8),
                primary key (test, date, vm),
                foreign key (test) references weeks (test),
                foreign key (vm) references vms (vm)
              );"""
        c.execute(sql)
        # Create the table containing the test schedule
        sql = """create table if not exists test_schedule (
              by_user varchar(48),
              scheduled_on datetime not null,
              scheduled_for datetime,
              run boolean not null,
              primary key (by_user, scheduled_for),
              foreign key (by_user) references users (username)
              );"""
        c.execute(sql)


if __name__ == "__main__":
    setup_database()
