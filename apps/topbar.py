from datetime import datetime
import dash_core_components as dcc
import dash_html_components as html
from dash.exceptions import PreventUpdate
from dash.dependencies import Input, Output, State

from app import app
from components import auth
from components.tests import formatted_next_tests_scheduled, add_test_scheduling, scheduled_test_ran_since
from components.common_layout import get_two_columns_layout, get_three_columns_layout


# Left column of topbar - links to the pages
page_links = [dcc.Link("Status page", href='/', id='status_link'),
              dcc.Link("VM overview", href='/vms', id='vm_link'),
              dcc.Link("Test history", href='/history', id='history_link')]

# Middle column of topbar - next & schedule buttons
next_button = html.Div(className='center-align', children=[
    html.Button(id='next_test_button',
                className="topbar-button",
                disabled=True),
    dcc.Interval(id='interval', interval=10000),
    html.Button(id='creation_date',
                style={'display': 'none'})
])
schedule_button = html.Div(
    className='center-align',
    id='schedule_tests_div')
buttons = get_two_columns_layout(next_button, schedule_button)

# Right column of topbar - the link to the account page
account_link = dcc.Link(href='/account', id='username_link')


layout = html.Div(className="topbar", children=[
    get_three_columns_layout(page_links, buttons, account_link)
])


@app.callback([Output('status_link', 'className'),
               Output('vm_link', 'className'),
               Output('history_link', 'className'),
               Output('username_link', 'className')],
              [Input('url', 'pathname')])
def highlight_current_page(pathname):
    """
    Highlights the currently opened page by changing css classes of links.

    :param pathname: the current url
    :returns: list of classNames (strings)
    """
    if pathname is None:
        raise PreventUpdate
    elif pathname == '/':
        return ['active', '', '', '']
    elif pathname == '/vms':
        return ['', 'active', '', '']
    elif pathname == '/history':
        return ['', '', 'active', '']
    elif pathname == '/account':
        return ['', '', '', 'active']
    else:
        return ['', '', '', '']


@app.callback(Output('username_link', 'children'),
              [Input('url', 'pathname')])
def set_username(_):
    """
    Sets the session's username in the right column.

    :returns: the current username (string)
    """
    if auth.is_authorized():
        return auth.get_username()


@app.callback(Output('next_test_button', 'children'),
              [Input('next_test_button', 'n_clicks'),
               Input('interval', 'n_intervals'),
               Input('schedule_tests_div', 'n_clicks')],
              [State('creation_date', 'children')])
def insert_next_test(_, __, ___, date):
    """
    Inserts the text for the button displaying the time of the next scheduled
    test.

    :param date: if tests have been scheduled since date, show update available
    :returns: time until next test schedule or update available (string)
    """
    if not auth.is_authorized():
        return
    if date is not None and scheduled_test_ran_since(date):
        return "update available"
    return "next " + formatted_next_tests_scheduled()


@app.callback(Output('next_test_button', 'style'),
              [Input('url', 'pathname'),
               Input('url', 'search'),
               Input('interval', 'n_intervals')])
def toggle_next_test(_, __, ___):
    """
    Toggles the next test's button visibility depending on whether user is
    logged in.

    :returns: html style
    """
    if auth.is_authorized():
        return {}
    else:
        return {'display': 'none'}


@app.callback(Output('schedule_tests_div', 'style'),
              [Input('url', 'pathname'),
               Input('url', 'search'),
               Input('interval', 'n_intervals')])
def toggle_schedule_button(_, __, ___):
    """
    Toggles the test scheduling button's visibility depending on whether user
    is logged in and an admin.

    :returns: html style
    """
    if auth.is_authorized() and auth.is_admin():
        return {}
    else:
        return {'display': 'none'}


@app.callback(Output('schedule_tests_div', 'children'),
              [Input('schedule_tests_div', 'n_clicks')])
def insert_schedule_tests_button(n):
    """
    Inserts the button for scheduling a new test and inserts test scheduling
    when button is clicked.

    :param n: number of clicks of button
    :returns: html.Button if authorized, None otherwise
    """
    # Catch non authorized requests
    if not auth.is_authorized() or not auth.is_admin():
        return
    # None means page load
    if n is None:
        return html.Button('Schedule now', className='topbar-button')
    # n=1 means first click on button
    if n == 1:
        by = auth.get_username()
        add_test_scheduling(by)
        return html.Button('Scheduled', className='topbar-button')


@app.callback(Output('creation_date', 'children'),
              [Input('creation_date', 'role'),
               Input('url', 'pathname'),
               Input('url', 'search')])
def save_creation_date(_, __, ___):
    """
    When url or search changes, page content updates. Saves the time of last
    url/search change.

    :returns: time of last url change, datetime isoformat (string)
    """
    return datetime.utcnow().isoformat()


@app.callback(Output('schedule_tests_div', 'n_clicks'),
              [Input('url', 'pathname'),
               Input('url', 'search')])
def reset_schedule_button(_, __):
    """
    When url or search changes, page content updates. Resets the schedule
    button upon url/search changes.

    :returns: None
    """
    return None
