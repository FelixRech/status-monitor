import dash

# Load dash default stylesheet
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']

# The app
app = dash.Dash(__name__, external_stylesheets=external_stylesheets)

# Allow callbacks to dynamically generated elements
app.config.suppress_callback_exceptions = True


# Overwrite body margin and set title-.-
app.index_string = '''
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>Status app</title>
        {%favicon%}
        {%css%}
    </head>
    <body class=no-margin-body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
'''

server = app.server
