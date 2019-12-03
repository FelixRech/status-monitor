import os
import threading
from urllib import parse
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
from dash.exceptions import PreventUpdate

from app import app
from scheduler import loop
from components import auth, config
from apps.topbar import layout as topbar
from apps import status, status_week, vms, vms_vm, account, login, logout


app.layout = html.Div([
    # represents the URL bar, doesn't render anything
    dcc.Location(id='url', refresh=False),
    # Top bar of the app
    topbar,
    # content will be rendered in this element
    html.Div(id='page-content', style={"margin": "8px"})
])


def parse_search(layout, search, keyword, alternative_layout):
    """
    Tries to parse search and returns an alternative layout if it succeeds,
    otherwise the default layout.

    :param layout: the default layout (html.Div children possibility)
    :param search: the current search
    :param keyword: the keyword to look for in the search
    :param alternative_layout: the alt. layout (html.Div children pos.)
    :returns: one of the two input layouts
    """
    # If no search is specified, return default layout
    if search is None or len(search) <= 1:
        return layout
    # If search is correct, return alternative layout
    try:
        if keyword in parse.parse_qs(search[1:]):
            return alternative_layout
    except Exception as _:
        pass
    # If search cannot be parsed, return default layout as fallback
    return layout


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname'), Input('url', 'search')])
def display_page(pathname, search):
    """
    Returns the page content to be displayed depending on pathname and search.

    :param pathname: current pathname
    :param search: current search
    :returns: page content layout (html.Div children possibility)
    """
    if pathname == '/login':
        return login.layout
    elif not auth.is_authorized():
        return auth.login_page_redirect
    elif pathname == '/':
        return parse_search(status.layout, search, 'week', status_week.layout)
    elif pathname == '/vms':
        return parse_search(vms.layout, search, 'vm', vms_vm.layout)
    elif pathname == '/account':
        return account.layout
    elif pathname == '/logout':
        return logout.layout
    else:
        # TODO: Implement 404 page
        raise PreventUpdate


if __name__ == '__main__':
    # Do not create threads twice, see https://stackoverflow.com/a/9476701
    # for details why this is necessary and done like this
    if os.environ.get("WERKZEUG_RUN_MAIN") == "true":
        print("[Scheduler] Creating thread")
        scheduler = threading.Thread(target=loop)
        scheduler.start()
        print("[Scheduler] Thread creation finished")
    print("[Server] Started/reloaded")
    app.run_server(debug=config.SERVER_DEBUG_MODE, host=config.SERVER_HOST)
