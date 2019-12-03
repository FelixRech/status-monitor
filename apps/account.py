import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State

from app import app
from components import auth
from components.common_layout import get_two_columns_layout


layout = html.Div(children=[
    get_two_columns_layout(
        html.Div(className='left-align', children=[
            html.H4('Hello', id='account-greeting'),
        ]),
        html.Div(className='right-align', children=[
            dcc.Link('Logout', href='/logout', className='button')
        ])
    ),
    html.Div(className='centered-column', children=[
        html.Div(id='new_password_success'),
        html.Div(className='box', children=[
            html.Div(id='user_area', children=[
                dcc.Input(
                    id='new_password_input',
                    placeholder='Enter your new password',
                    type='password',
                    value='',
                    autoFocus=True
                ),
                html.Span(style={'margin-right': '25px'}),
                html.Button(
                    'Change my password!',
                    id='new_password_button'
                )
            ]),
            html.Div(id='admin_area')
        ])
    ])
])


@app.callback(Output('account-greeting', 'children'),
              [Input('account-greeting', 'role')])
def set_greeting(_):
    """
    Sets the username and adds admin distinction is user is admin.

    :returns: username and if admin admin distrinction (string)
    """
    username = auth.get_username()
    addition = '' if not auth.is_admin() else " (admin)"
    return "Hello {0}{1}".format(username, addition)


@app.callback(Output('admin_area', 'children'),
              [Input('admin_area', 'role')])
def render_admin_area(_):
    """
    Renders the admin area containing new user and admin creation.

    :returns: html.Div or None if not admin
    """
    if not auth.is_admin():
        return
    admin_area = html.Div(children=[
        html.Br(),
        dcc.Input(
            id='new_user_name_input',
            placeholder="Enter new user\'s username",
            type='text',
            value='',
            autoFocus=True
        ),
        html.Span(style={'margin-right': '25px'}),
        dcc.Input(
            id='new_user_password_input',
            placeholder="Enter new user\'s password",
            type='password',
            value=''
        ),
        html.Span(style={'margin-right': '25px'}),
        html.Button(
            'Add new user!',
            id='new_user_button'
        ),
        html.Span(style={'margin-right': '25px'}),
        html.Span(id='new_user_message'),
        html.Div(),
        html.Br(),
        dcc.Input(
            id='new_admin_name_input',
            placeholder="Enter new admin\'s username",
            type='text',
            value=''
        ),
        html.Span(style={'margin-right': '25px'}),
        dcc.Input(
            id='new_admin_password_input',
            placeholder="Enter new admin\'s password",
            type='password',
            value=''
        ),
        html.Span(style={'margin-right': '25px'}),
        html.Button(
            'Add new admin!',
            id='new_admin_button'
        ),
        html.Span(style={'margin-right': '25px'}),
        html.Span(id='new_admin_message')
    ])
    return admin_area


@app.callback([Output('new_password_success', 'children'),
               Output('new_password_input', 'value')],
              [Input('new_password_button', 'n_clicks'),
               Input('new_password_input', 'n_submit')],
              [State('new_password_input', 'value')])
def change_password(_, __, password):
    """
    Change the current user's password.

    :param password: new user password
    :returns: success or error messge, new value for password input box
    """
    username = auth.get_username()
    if auth.change_password(username, password):
        return ["Password change successful!", ""]
    else:
        return ["Not authorized to do that, please log in again", ""]


@app.callback([Output('new_user_message', 'children'),
               Output('new_user_name_input', 'value'),
               Output('new_user_password_input', 'value')],
              [Input('new_user_button', 'n_clicks'),
               Input('new_user_name_input', 'n_submit'),
               Input('new_user_password_input', 'n_submit')],
              [State('new_user_name_input', 'value'),
               State('new_user_password_input', 'value')])
def add_user(_, __, ___, username, password):
    """
    Add a non-admin user. Returns a sucess/failure message.

    :param username: new user's username
    :param password: new user's password
    :returns: message & new values for input boxes (list of strings)
    """
    if auth.add_user(username, False, password):
        return ["Success!", '', '']
    else:
        return ["Failure...", username, password]


@app.callback([Output('new_admin_message', 'children'),
               Output('new_admin_name_input', 'value'),
               Output('new_admin_password_input', 'value')],
              [Input('new_admin_button', 'n_clicks'),
               Input('new_admin_name_input', 'n_submit'),
               Input('new_admin_password_input', 'n_submit')],
              [State('new_admin_name_input', 'value'),
               State('new_admin_password_input', 'value')])
def add_admin(_, __, ___, username, password):
    """
    Add an admin user. Returns a sucess/failure message.

    :param username: new user's username
    :param password: new user's password
    :returns: message & new values for input boxes (list of strings)
    """
    if auth.add_user(username, True, password):
        return ["Success!", '', '']
    else:
        return ["Failure...", username, password]
