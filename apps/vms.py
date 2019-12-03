import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from components.tests import get_all_vms, get_tests_names_of_vm
from components.common_layout import get_test_summarizing_layout


layout = html.Div([
    html.H2('Your VMs', id='vm-headline'),
    html.Div(className='centered-column', id='vms-div')
])


@app.callback(Output('vms-div', 'children'),
              [Input('vm-headline', 'children')])
def insert_tests(_):
    """
    Combines the individual vm layouts.

    :returns: combined layout (list of html.Div)
    """
    vms = get_all_vms()
    layout = list(filter(None, map(get_vm_layout, vms)))
    return layout


def get_vm_layout(vm):
    """
    Creates the layout for one vm.

    :param vm: the vm to create a layout for
    :returns: layout (html.Div or None)
    """
    tests = get_tests_names_of_vm(vm)
    return get_test_summarizing_layout(tests, vm, '/vms?vm=' + vm, vm=vm)
