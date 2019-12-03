import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from components import auth

layout = html.Div(className="centered-column", children=[
    html.H3('Please login!'),
    html.Div(id='password-test'),
    dcc.Input(
        id='username_input',
        placeholder='Enter your username',
        type='text',
        value='',
        autoFocus=True
    ),
    html.Br(),
    dcc.Input(
        id='password_input',
        placeholder='Enter your password',
        type='password',
        value=''
    ),
    html.Br(),
    html.Button(
        'Log me in!',
        id='login_button'
    )
])


@app.callback(Output('password-test', 'children'),
              [Input('login_button', 'n_clicks'),
               Input('username_input', 'n_submit'),
               Input('password_input', 'n_submit')],
              [State('username_input', 'value'), State('password_input', 'value')])
def login(_, __, ___, username, password):
    """
    Tries to log the user in with the given credentials. Will show an error
    message when the credentials are wrong. Otherwise sets the username and
    session key cookies and redirects to status page.

    :param username: input in the username box
    :param password: input in the password box
    :returns: either error message (string) or redirect to status page
    """
    if username == "":
        return
    # Try to log in using the credentials specified by the user
    session, expires = auth.login(username, password)
    # auth.login returns None on an invalid request. Show error message
    if session is None:
        return "Wrong username/password combination. Please try again!"
    print("[Server] User {0} logged in".format(username))
    # Set the cookies and return redirect
    dash.callback_context.response.set_cookie(
        'session', session, expires=expires)
    return dcc.Location(pathname='/', id='arbitrary-unique-location-id')
