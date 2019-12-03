from urllib import parse
from functools import partial
from itertools import repeat
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from components.tests import get_tests_of_vm
from components.common_layout import get_results_list, get_test_layout
from components.common_layout import add_test_details_callbacks, add_heading_from_search_callback


layout = html.Div([
    html.Div(className='big-text', children=[
        html.Span('VM ', id='vm-heading-part1'),
        html.Span('', id='vm-heading-part2'),
    ]),
    html.Div(id='vm-tests-div')
])


def get_week_layout(args, vm):
    """
    Get the layout of one week for a given VM.

    :param args: a tuple/list in the format [week, [test1, ...], [id1, ...]]
    :param vm: the VM's name
    :returns: the week's layout (a div)
    """
    week, tests, ids = args
    # Get the test passed, failed and output from database
    results_list = get_results_list(tests, vm)
    # Get the layout for each test and filter empty ones
    vm_name = repeat('vm', len(tests))
    tests_layout = map(get_test_layout, tests, results_list, ids, vm_name)
    tests_layout = list(filter(None, tests_layout))
    # Set up layout for week
    week_layout = html.Div(className='box', children=[
        html.Div(className='week-container', children=[
            html.Div(className='left-align', children=[
                html.Span("Week {0}".format(week), className='big-text')
            ]),
            html.Div(className='centered-column', children=tests_layout)
        ])
    ])
    return week_layout


def format_weeks_tests(tests):
    """
    Format the list of tests [(week, test), ...] into usable format for
    generating the layout.

    :param tests: a list/tuple of tests in the format [(week, test), ...]
    :returns: a list in the format [(week, tests, ids), ...]
    """
    def id_helper(lists, ids, index, current_id):
        """Generate ids for list of lists
        :returns: a list of lists [[id1, id2, ...], [id5, ...]]"""
        if len(lists) == 0 or index >= len(lists):
            return ids
        n_els = len(lists[index])
        c_ids = [current_id + i for i in range(n_els)]
        n_ids = ids + [c_ids]
        return id_helper(lists, n_ids, index + 1, current_id + n_els)
    # Get sorted list of distinct weeks (= tests[i][0])
    weeks = sorted(list(set(map(lambda x: x[0], tests))))
    # Nth function will return True iff. input[0] == weeks[n]
    fs = [partial(lambda w, x: x[0] == w, w) for w in weeks]
    # Filter tests to list of tests for each week
    weekly_tests = [list(map(lambda x: x[1], filter(f, tests))) for f in fs]
    # Combine the weeks, weekly_tests and id lists
    ids = id_helper(weekly_tests, [], 0, 0)
    return [(weeks[i], weekly_tests[i], ids[i]) for i in range(len(weeks))]


@app.callback(Output('vm-tests-div', 'children'),
              [Input('vm-heading-part1', 'children')],
              [State('url', 'search')])
def insert_tests(_, search):
    """
    Insert the tests when the page is rendered

    :param _: ignored
    :param search: the search part of the url
    :returns: a layout containing the weeks' tests
    """
    # Extract the vm from search
    try:
        parsed_search = parse.parse_qs(search[1:])
        vm = parsed_search['vm']
    # In case extraction fails, return error
    except Exception as _:
        return []
    # Get the tests of the VM and format into something useful
    tests = get_tests_of_vm(vm)
    weekly_tests = format_weeks_tests(tests)
    # Get the weeks' layouts
    vms = repeat(vm, len(weekly_tests))
    weeks_layout = list(filter(None, map(get_week_layout, weekly_tests, vms)))
    # Return a centered version of the weeks' layouts
    layout = html.Div(className="centered-column", children=weeks_layout)
    return layout


# Set the vm from a callback depending on search
add_heading_from_search_callback('vm')
# Add callbacks for toggling test's visibility
add_test_details_callbacks('vm')
