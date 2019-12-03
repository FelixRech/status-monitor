import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from components.common_layout import get_test_summarizing_layout
from components.tests import get_all_weeks, get_tests_in_week


layout = html.Div([
    html.H2('Status page', id='status-headline'),
    html.Div(className='centered-column', id='status-weeks-div')
])


@app.callback(Output('status-weeks-div', 'children'),
              [Input('status-headline', 'children')])
def insert_tests(_):
    """
    Combines the different weeks' layouts into one.

    :returns: combined layout (list of html.Divs)
    """
    weeks = get_all_weeks()
    # Filter out None's
    layout = list(filter(None, map(get_week_layout, weeks)))
    return layout


def get_week_layout(week):
    """
    Returns one week's layout.

    :param week: week to build layout for
    :returns: layout for that week (html.Div or None if week does not have tests)
    """
    # Get the tests in this week and calculate their fail/pass
    tests = get_tests_in_week(week)
    week = str(week)
    return get_test_summarizing_layout(tests, 'Week ' + week, '/?week=' + week)
