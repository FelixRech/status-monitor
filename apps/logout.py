import dash
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from components import auth

layout = html.Div([
    html.H2('Logging you out...', id="logout_msg"),
    html.Div(id="logout_trigger")
])


@app.callback(Output('logout_msg', 'children'),
              [Input('logout_trigger', 'children')])
def logout(_):
    print("[Server] User {0} logged out".format(auth.get_username()))
    # Set session in database to logged out
    auth.logout()
    # Expire the session cookie
    dash.callback_context.response.set_cookie('session', '', expires=0)
    return "Logout successful!"
