import bcrypt
import pymysql
import secrets
import datetime
from flask import request
from components.sql import Cursor, WriteCursor
import dash_core_components as dcc


# A redirect to the login page to be used in the case of e.g. expired sessions
login_page_redirect = dcc.Location(pathname='/login', id='')


def login(username, password):
    """
    Create a new session for the user and returns a session key to identify
    the user from now on.

    :param username: the user's username
    :param password: the user's password
    :returns: session key (string) or None if credentials wrong & expiry date
              (datetime.datetime)
    """
    # Get the user's password hash from the database
    with Cursor() as c:
        sql = "select pw_hash from users where username = %s"
        c.execute(sql, (username))
        pw_hash = c.fetchone()[0]
    # Compare password with hash
    if not bcrypt.checkpw(password.encode('utf-8'), pw_hash.encode('utf-8')):
        return None, None
    # Create a new session key and calculate expiry
    session = secrets.token_urlsafe(64)[0:48]
    expiry_date = datetime.datetime.now() + datetime.timedelta(days=7)
    expires = expiry_date.isoformat()
    # Insert session key into database
    with WriteCursor() as c:
        sql = """insert into sessions
              values(%s, %s, %s, %s);"""
        c.execute(sql, (username, session, expires, expires))
    return session, expiry_date


def logout():
    """
    Sets the user's current session as logged out.
    """
    if is_authorized():
        session = request.cookies['session']
    with WriteCursor() as c:
        sql = """update sessions
              set logout = utc_timestamp()
              where id = %s;"""
        c.execute(sql, (session))


def is_authorized():
    """
    Checks whether the request is coming from an authorized session.

    Uses the cookies username and session and checks whether this combination
    also exists in the valid (and not expired) sessions in the database.

    :returns: whether request is authorized (boolean)
    """
    # If cookie is not even set, request is unauthorized for sure
    if 'session' not in request.cookies:
        return False
    # Extract session key from cookie
    session = request.cookies['session']
    # Check whether session exists
    sql = """select * from sessions
          where expires >= utc_timestamp() and logout >= utc_timestamp() and id = %s;"""
    with Cursor() as c:
        c.execute(sql, (session))
        session_active = len(c.fetchall()) >= 1
    return session_active


def get_username():
    """
    Returns the username associated with the current session.

    :returns: username (string), or None in case of expired/nonexistent session
    """
    if 'session' not in request.cookies:
        return None
    with Cursor() as c:
        sql = """select username
              from sessions
              where id = %s;"""
        c.execute(sql, (request.cookies['session']))
        username = c.fetchone()
    return None if username is None else username[0]


def is_admin():
    """
    Returns whether the current session is associated with an admin user.

    :returns: session's user is admin (boolean)
    """
    # Try to get username, if not logged in return False
    username = get_username()
    if username is None:
        return False
    with Cursor() as c:
        sql = """select admin
              from users
              where username = %s;"""
        c.execute(sql, (username))
        return c.fetchone()[0]


def add_user(username, admin, password):
    """
    Adds a user with given credentials as admin or user.

    :param username: new user's username (string)
    :param admin: new user is admin? (boolean or 1/0 int)
    :param password: new user's password (string)
    :returns: success (boolean)
    """
    if not is_authorized() or not is_admin():
        return False
    with WriteCursor() as c:
        sql = """insert into users
              values (%s, %s, "*");"""
        try:
            c.execute(sql, (username, int(admin)))
        # Primary key error means user already exists
        except pymysql.err.IntegrityError as _:
            return False
    # Set new user's password
    return change_password(username, password)


def change_password(username, password):
    """
    Change password of given user.

    :param username: user's username
    :param password: user's new password
    :returns: success (boolean)
    """
    # Deny requests from user's that aren't logged in
    if not is_authorized():
        return False
    # Deny requests for changing someone else's username, except if request
    # comes from an admin
    if get_username() != username and not is_admin():
        return False
    pw_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    with WriteCursor() as c:
        sql = """update users
              set pw_hash = %s
              where username = %s;"""
        c.execute(sql, (pw_hash, username))
    return True
