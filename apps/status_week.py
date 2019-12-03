from urllib import parse
from itertools import repeat
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from components.tests import get_tests_in_week
from components.common_layout import get_results_list, get_test_layout
from components.common_layout import add_test_details_callbacks, add_heading_from_search_callback


layout = html.Div([
    html.Div(className='big-text', children=[
        html.Span('Week ', id='week-heading-part1'),
        html.Span('', id='week-heading-part2'),
    ]),
    html.Div(id='week-tests-div')
])


@app.callback(Output('week-tests-div', 'children'),
              [Input('week-heading-part1', 'children')],
              [State('url', 'search')])
def insert_tests(_, search):
    """
    Returns the layout containing the tests for one week.

    :param search: current url's search
    :returns: layout containing tests (html.Div or None)
    """
    # Parse week number from search
    try:
        parsed_search = parse.parse_qs(search[1:])
        week = parsed_search['week']
    # If parsing fails, exit
    except Exception as _:
        return
    tests = get_tests_in_week(week)
    results = get_results_list(tests)
    ids = range(len(tests))
    id_presets = repeat('week', len(results))
    test_layouts = list(map(get_test_layout, tests, results, ids, id_presets))
    return html.Div(className='centered-column', children=test_layouts)


# Set the week from a callback depending on search
add_heading_from_search_callback('week')
# Add callbacks for toggling test's visibility
add_test_details_callbacks('week')
