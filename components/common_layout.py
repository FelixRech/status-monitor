import datetime
from urllib import parse
from itertools import repeat
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from components.tests import get_last_test, summarize_tests


def get_results_list(tests, vm=None):
    """
    Gets a list of tests results.

    :param tests: a list of tests, e.g. ['dns', 'dhcp, ...]
    :returns: a list of test results [[passed, failed, output, date, vm], ..]
    """
    if vm is None:
        return list(map(get_last_test, tests))
    else:
        return list(map(get_last_test, tests, repeat(vm, len(tests))))


def get_indicator(success):
    """
    Get a success indicator.

    :param success: True is green, False is red indicator
    :returns: a indicator (html.Span)
    """
    indicator_type = 'indicator-success' if success else 'indicator-failure'
    return html.Span(className=indicator_type)


def get_two_columns_layout(col1, col2):
    """
    Get a two column layout.

    :param col1: the first column (html.Div children compatible)
    :param col2: the second column (html.Div children compatible)
    :returns: the container with the two columns (html.Div)
    """
    return html.Div(className='two-column-horizontal-container',
                    children=[col1, col2])


def get_three_columns_layout(col1, col2, col3):
    """
    Get a three column layout where the first column is left aligned, the
    second centered and the third right aligned.

    :param col1: the first column, a string or a list of html/dcc objects
    :param col2: the second column, a string or a list of html/dcc objects
    :param col3: the third column, a string or a list of html/dcc objects
    :returns: the container with all three columns (html.Div)
    """
    return html.Div(className='three-column-horizontal-container', children=[
        html.Div(className='left-align', children=col1),
        html.Div(className='center-align', children=col2),
        html.Div(className='right-align', children=col3)
    ])


def get_test_summarizing_layout(tests, left_col_name, href, vm='%'):
    """
    Gets a three column layout there the first column contains all tests
    passed indicator and the name of this set of tests. The middle column
    containes the number of passed/failed tests. Finally, the right column
    contains a link to the given href.

    :param tests: a list of tests (list of strings, e.g. ['dns', 'dhcp'])
    :param left_col_name: name of this set of tests (string, e.g. vm01 or week 1)
    :param href: the link's href (string)
    :returns: container with the layout (html.Div) or None if len(test) = 0
    """
    # If there are no tests, return nothing
    if len(tests) == 0:
        return None
    passed, failed = summarize_tests(tests, vm=vm)
    # Create left column
    left_column = [get_indicator(failed == 0),
                   html.Div(left_col_name, className='big-text')]
    # Combine all three columns
    weeks = get_three_columns_layout(
        left_column,
        '{0} of {1} tests passed'.format(passed, passed + failed),
        dcc.Link('Details', href=href, className='button')
    )
    # Put it in a box and return it
    return html.Div(className='box', children=weeks)


def format_date(date):
    """
    Format a datetime.datetime object into natural language.

    Examples: today, yesterday, monday, ...

    :param date: datetime.datetime object
    :returns: natural language version (string)
    """
    today = datetime.date.today()
    difference = (today - date.date()).days
    if difference == 0:
        day = 'today'
    elif difference == 1:
        day = 'yesterday'
    elif difference < 7:
        day = date.strftime('%A')
    else:
        day = 'on ' + date.date().strftime('%w.%m.%Y')
    return day + ' at ' + date.strftime('%H:%M')


def get_test_layout(name, results, id, id_preset):
    """
    Returns the layout of a single test.

    : param name: the test's name, e.g. 'dhcp'
    : param results: list[passed, failed, output, date, vm]
    : param id: the unique numeric id to identify this test to dash callbacks
    : param id_preset: what to preset ids, e.g. 'vm' or 'status'
    """
    # Variables to clean up below
    pass_msg = ('{0} of {1} tests passed'
                .format(results['passed'], results['passed'] + results['failed']))
    date = format_date(results['date'])
    details_button = html.Button(
        title='Show test output',
        id='{0}-test-toggle-output-{1}'.format(id_preset, id),
        className='triangle-button',
        children=[html.Div(className='triangle-down')]
    )
    # Create the test output layout
    details_layout = html.Div(
        "Executed on {0} {1}".format(results['vm'], date),
        className='test-details')
    terminal_layout = html.Div(
        # id='{0}-test-output-{1}'.format(id_preset, id),
        className='terminal',
        children=html.Div(list(map(html.Div, results['output'].split('\n'))))
    )
    output_layout = html.Div(
        id='{0}-test-output-{1}'.format(id_preset, id),
        children=[terminal_layout, details_layout],
        style={'display': 'none'}
    )
    # Create main visible layout
    left_column = [get_indicator(results['failed'] == 0),
                   html.Div('Test {0}'.format(name), className='big-text')]
    content_layout = get_three_columns_layout(
        left_column, pass_msg, details_button)
    # Combine the layouts into a test box and return it
    return html.Div(className='box', children=[content_layout, output_layout])


def add_heading_from_search_callback(id_preset):
    """
    Returns a callback to add the 2nd part of a page heading on page load.

    :param id_preset: preset of id, e.g. <preset>-heading-part2, & search arg
    """
    def generate_callback(id_preset):
        def insert_heading(_, search):
            parsed_search = parse.parse_qs(search[1:])
            return parsed_search[id_preset]
        return insert_heading
    trigger_id = id_preset + '-heading-part1'
    heading_id = id_preset + '-heading-part2'
    # Add the callback
    app.callback(Output(heading_id, 'children'),
                 [Input(trigger_id, 'children')],
                 [State('url', 'search')])(
        generate_callback(id_preset)
    )


def add_test_details_callbacks(id_preset):
    """
    This function will add callbacks for all possible tests.
    Unfortunately, callbacks can not be dynamically generated for each new test
    added. Therefore, we have to add a finite number of them and hope we never
    need more.

    :param id_preset: preset for id, e.g. <preset>-test-output-<number>
    """
    def generate_callbacks():
        """
        Generate the callback function for toggling test output visibility.

        : returns: A callback function.
        """
        def toggle_test_output_visibility(n):
            if n % 2 == 0:
                return [{'display': 'none'},
                        html.Div(className='triangle-down'),
                        "Show test output"]
            return [{}, html.Div(className='triangle-up'), "Hide test output"]
        return toggle_test_output_visibility

    # Iterate through i in '0', '1', '2', ...
    for i in list(map(str, range(0, 100))):
        toggle_id = id_preset + '-test-toggle-output-' + i
        output_id = id_preset + '-test-output-' + i
        # And add the callback to each possible test-more-button
        app.callback([Output(output_id, 'style'),
                      Output(toggle_id, 'children'),
                      Output(toggle_id, 'title')],
                     [Input(toggle_id, 'n_clicks')])(
            generate_callbacks()
        )
