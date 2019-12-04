import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from components.common_layout import get_three_columns_layout, format_date
from components.tests import get_all_weeks, get_tests_in_week, get_vms_of_test, get_test_history


layout = html.Div(className='centered-column', children=[
    get_three_columns_layout(
        html.Div(id='week_div', style={'width': '300px'}),
        html.Div(id='test_div', style={'width': '300px'}, children=[
            dcc.Dropdown(placeholder="Please select a week first")
        ]),
        html.Div(id='vm_div', style={'width': '300px'}, children=[
            dcc.Dropdown(placeholder="Please select a test first")
        ]),
    ),
    html.Div(id='plot_div')
])


@app.callback(Output('week_div', 'children'),
              [Input('week_div', 'role')])
def insert_weeks_dropdown(_):
    """
    Insert the weeks dropdown upon loading of page.

    :returns: dcc.Dropdown
    """
    weeks = [{'label': 'Week ' + str(w), 'value': w} for w in get_all_weeks()]
    return dcc.Dropdown(id='weeks_dropdown', options=weeks,
                        placeholder="Select a week...")


@app.callback(Output('test_div', 'children'),
              [Input('weeks_dropdown', 'value')])
def insert_tests_dropdown(week):
    """
    Insert the tests dropdown upon selection of week. Only displays tests in
    the given week.

    :param test: selected week (int, e.g. 1)
    :returns: dcc.Dropdown
    """
    if week is None:
        return dcc.Dropdown(placeholder="Please select a week first")
    tests = [{'label': t, 'value': t} for t in get_tests_in_week(week)]
    return dcc.Dropdown(id='tests_dropdown', options=tests)


@app.callback(Output('vm_div', 'children'),
              [Input('tests_dropdown', 'value')])
def insert_vms_dropdown(test):
    """
    Insert the vm dropdown upon selection of test. Only displays vms on which
    the given test actually ran.

    :param test: selected test (string, e.g. 'dns')
    :returns: dcc.Dropdown
    """
    # Catch unselection of test
    if test is None:
        return dcc.Dropdown(placeholder="Please select a test first")
    vms = [{'label': vm, 'value': vm} for vm in get_vms_of_test(test)]
    return dcc.Dropdown(id='vms_dropdown', options=vms)


@app.callback(Output('plot_div', 'children'),
              [Input('vms_dropdown', 'value')],
              [State('tests_dropdown', 'value')])
def insert_plot(vm, test):
    """
    Inserts the plot into the plot_div div.

    :param vm: the selected vm (string, e.g. 'vm01')
    :param test: the selected test (string, e.g. 'dns')
    :returns: dcc.Graph
    """
    tests = get_test_history(test, vm)
    # Extract date, passed, failed, output and bring them to the right format
    date = map(format_date, tests['date'])
    date = list(map(lambda x: x[0].upper() + x[1:], date))
    passed, failed = tests['passed'], tests['failed']
    output = list(map(lambda x: x.replace('\n', '<br>'), tests['output']))
    # Show date and passed/failed in main box, output in box to the side
    hovertext = [("<b>{0}</b>:<br> {1} passed, {2} failed<extra>{3}</extra>"
                  .format(date[i], passed[i], failed[i], output[i]))
                 for i in range(len(tests['date']))]
    return dcc.Graph(
        id='plot',
        figure={
            'data': [{
                'x': tests['date'],
                'y': tests['quota'],
                'customdata': hovertext,
                'hovertemplate': '%{customdata}'
            }],
            # y-axis goes from 0 to 1 and is formatted as percentage
            'layout': {'yaxis': {'range': [0, 1], 'tickformat': '%'},
                       'title': "Test history of test {0} on {1}".format(test, vm)},
        },
        config={'displayModeBar': False}
    )
