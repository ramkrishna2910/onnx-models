import os
import requests
import textwrap
import base64
from io import BytesIO
import dash
import yaml
from dash import html, dcc
import dash_ace
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dependencies import Input, Output, State, ALL
import pkg_resources
import mlagility.api.report as report_api
import base64
import json
from typing import List, Dict
from pathlib import Path
import subprocess

#Global Constants
python_files_directory = pkg_resources.resource_filename('mlagility_models', '')

# Create application instance
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "/assets/css/style.css"], suppress_callback_exceptions=True)
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        <!-- Import Bootstrap CSS -->
        <link rel="stylesheet" href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css">
        <!-- Import the FontAwesome library -->
        <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.1/css/all.min.css">
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""


def get_onnx_files(repo_path):
    """
    Get a list of ONNX files from a Git repository using git lfs ls-files command.

    Args:
        repo_path (str): Path to the Git repository.

    Returns:
        list: A list of tuples containing the filename and download URL for each ONNX file.
    """
    # Use subprocess to run the git lfs ls-files command and get output
    result = subprocess.run(['git', 'lfs', 'ls-files'], cwd=repo_path, stdout=subprocess.PIPE)
    base_url = "https://github.com/onnx/models/raw/main"
    # Decode the output from bytes to string and split into lines
    lines = result.stdout.decode('utf-8').split('\n')

    # Filter lines to only include .onnx files and construct a tuple with filename and path for each file
    onnx_files = [
        (Path(line.split(' ')[-1]).name, f"{base_url}/{line.split(' ')[-1]}")
        for line in lines
        if Path(line.split(' ')[-1]).suffix == '.onnx'
    ]

    return onnx_files


def fetch_files_by_extension(directory: str, extension: str, report_csv: str, columns: List[str]) -> Dict[str, Dict[str, str]]:
    file_dict = report_api.get_dict(report_csv, columns)
    file_dict = {k: v for k, v in file_dict.items() if str(v.get('onnx_exported')).lower() == 'true'}

    matched_files_dict = {}

    for dirpath, dirnames, files in os.walk(directory):
        if 'skip' in dirnames:
            dirnames.remove('skip')

        for file in files:
            file_name_without_extension, file_extension = os.path.splitext(file)
            if file_extension == extension and file_name_without_extension in file_dict:
                matched_files_dict[os.path.join(dirpath, file)] = file_dict[file_name_without_extension]

    return matched_files_dict

onnx_models = get_onnx_files("/net/home/rsivakumar/github/models")
matched_files_dict = fetch_files_by_extension(python_files_directory, ".py", "assets/data/2023-05-24.csv", ["onnx_exported", "author", "task"])
python_files = list(matched_files_dict.keys())

# Load the yaml file
with open('model-metadata.yaml') as f:
    data = yaml.safe_load(f)

def onnx_card(model_name, model_url):
    model_id = model_name.replace(".", "_")
    display_name = model_name.replace(".onnx", "")
    try:
        use_case = data[model_name]['task']
    except KeyError:
        use_case = "Unknown"

    try:
        opset = data[model_name]['opset']
    except KeyError:
        opset = "Unknown"

    try:
        description = data[model_name]['description']
    except KeyError:
        description = "No description available"


    info_id = f"{model_id}_info"

    return dbc.Card(
        [
            dbc.CardHeader([
                html.Div(display_name, className="float-left"),
                dbc.Button("i", id=info_id, color="link", className="float-right info-circle")
            ]),
            dbc.Tooltip(description, target=info_id),
            dbc.CardBody(
                [
                    html.P(use_case, className="card-text mb-1"),
                    html.P(f"Opset: {opset}", className="card-text mb-1"),
                    html.A(
                        html.I(className="fas fa-arrow-down"),
                        id=f"{model_id}_download",
                        className="btn btn-primary btn-sm position-absolute",
                        style={"bottom": "10px", "right": "10px"},
                        # download=model_name,
                        href=model_url
                    )
                ],
                style={"position": "relative"}
            ),
        ],
        style={"width": "18rem", "margin": "10px"},
    )

def task_to_value(task):
    task_value_mapping = {
        "Computer Vision": 1,
        "Natural Language Processing": 2,
        "Audio": 3,
        "Tabular": 4,
        "Reinforcement Learning": 5,
        "MultiModal": 6,
        "Generative AI": 7,
        "Graph Machine Learning": 8,
    }
    return task_value_mapping.get(task, None)


def create_filter_panel(identifier):
    return dbc.Card(
        [
            dbc.Tabs(
                [
                    dbc.Tab(
                        dbc.Checklist(
                            options=[
                                {"label": "Computer Vision", "value": 1},
                                {"label": "Natural Language Processing", "value": 2},
                                {"label": "Audio", "value": 3},
                                {"label": "Tabular", "value": 4},
                                {"label": "Reinforcement Learning", "value": 5},
                                {"label": "MultiModal", "value": 6},
                                {"label": "Generative AI", "value": 7},
                                {"label": "Graph Machine Learning", "value": 8},
                            ],
                            id=f"filter_checklist_tasks_{identifier}",
                            inline=False,
                            className="my-2"
                        ),
                        label="Tasks",
                        className="p-3"
                    ),
                ],
                className="nav-tabs-custom",
                style={"display": "flex",},
            )
        ],
        className="filter-panel p-3",
    )

def python_file_card(file_name):
    file_name_encoded = base64.b64encode(file_name.encode()).decode()
    file_name_only = os.path.basename(file_name)
    use_case = matched_files_dict.get(file_name, {}).get('task', '')
    author = matched_files_dict.get(file_name, {}).get('author', '')

    card = dbc.Card(
            [
                dbc.CardHeader(
                    html.H6(file_name_only, className="mb-0", style={"font-weight": "bold"}), 
                    className="bg-light text-dark", 
                ),
                dbc.CardBody(
                    [
                        html.P(f"Task: {use_case.replace('_', ' ').title()}" if isinstance(use_case, str) else "Task: Unknown", className="card-text text-muted mb-auto"),
                        html.P(f"Author: {author.replace('_', ' ').title()}" if isinstance(author, str) else "Author: Unknown", className="card-text text-muted mb-auto"),
                        html.Div(
                            dbc.Button(
                                "View Source",
                                color="primary",
                                size="sm",
                                id={'type': 'dynamic-button', 'index': file_name_encoded},
                            ),
                            className="d-flex justify-content-end mt-auto",
                        ),
                    ],
                    className="d-flex flex-column",
                ),
            ],
            className="mb-3 shadow-sm",
        )
    return card


# Grid of cards
grid = dbc.Row(
    [
        dbc.Col(onnx_card(model_name, model_url), lg=4, md=6, xs=12) 
        for model_name, model_url in onnx_models
    ],
    className="row-cols-1 row-cols-md-2 row-cols-lg-3"
)

grid_other_models = dbc.Row(
    [
        dbc.Col(python_file_card(file_name), width=12)
        for file_name in python_files
    ],
    className="row-cols-1",
)

page_navigation = html.Div(
    [
        dbc.Button("Prev", id="prev_button", n_clicks=0, className="mr-2 btn btn-primary btn-sm"),
        dbc.Button("Next", id="next_button", n_clicks=0, className="mr-2 btn btn-primary btn-sm"),
        html.Div(
            html.Div(id="page_number", children="Page: 1"),
            style={"display": "flex", "justifyContent": "center", "width": "100%"}
        )
    ],
    className="mt-2"
)



# App Layout
app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavbarBrand(
                html.Img(src="/assets/img/onnx-logo.png", height="75px"),
                className=""
            ),
            html.Div(
                [
                    html.H1("ONNX Model Zoo", className=""),
                    html.H6([
                        "Powered by ",
                        dcc.Link("MLAgility", href="https://github.com/groq/mlagility", target="_blank", className="navbar-link")
                    ], className="navbar-subtitle"),
                ],
                className="mx-auto",
            ),
        ],
        brand=None,
        color="white",
        className="d-flex justify-content-center",
    ),
    dcc.Tabs(
        id='tabs',
        value='tab-1',
        children=[
            dcc.Tab(
                label='ONNX models',
                value='tab-1',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Div(className="container-fluid", children=[
                        dcc.Input(
                            id="search_bar",
                            type="text",
                            placeholder="Search...",
                            style={"width": "100%", "marginBottom": "20px", "borderRadius": "15px"},
                            className="form-control form-control-lg"
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.H3("Filters"),
                                create_filter_panel("onnx")
                            ], width=3),
                            dbc.Col([
                                html.Div(id="card_container", children=grid),
                            ], width=9)
                        ]),
                    ]),
                ],
            ),
            dcc.Tab(
                label='All others',
                value='tab-2',
                className='custom-tab',
                selected_className='custom-tab--selected',
                children=[
                    html.Div(className="container-fluid", children=[
                        dbc.Row([
                            dbc.Col([
                                dcc.Input(
                                    id="search_bar_all_others",
                                    type="text",
                                    placeholder="Search...",
                                    style={"width": "100%", "marginBottom": "20px", "borderRadius": "15px"},
                                    className="form-control form-control-lg"
                                ),
                            ], width=12),
                        ]),
                        dbc.Row([
                            dbc.Col([
                                html.H4("Filters"),
                                create_filter_panel("all_others")
                            ], width=3),
                            dbc.Col([
                                html.Div(id="card_container_all_others", children=grid_other_models),
                                html.Div(page_navigation, style={"display": "flex", "justifyContent": "center"}),
                            ], width=4),
                            dbc.Col([
                                html.H4("Code Viewer"),
                                dash_ace.DashAceEditor(
                                    id='code_viewer',
                                    mode='python',
                                    theme='monokai',
                                    value='',
                                    wrapEnabled=True,
                                    showPrintMargin=False,
                                    style={
                                        "width": "100%",
                                        "height": "50vh",
                                        "fontFamily": "Menlo, monospace",
                                        "lineHeight": "1.4",
                                        "borderRadius": "10px",
                                        "padding": "20px",
                                    },
                                    readOnly=True,
                                ),
                                html.H4("Steps to export to ONNX"),
                                dash_ace.DashAceEditor(
                                    id='export_steps',
                                    mode='python',
                                    theme='monokai',
                                    value='',
                                    wrapEnabled=True,
                                    showPrintMargin=False,
                                    style={
                                        "width": "100%",
                                        "height": "10vh",
                                        "fontFamily": "Menlo, monospace",
                                        "lineHeight": "1.4",
                                        "borderRadius": "10px",
                                        "padding": "20px",
                                    },
                                    readOnly=True,
                                ),
                            ], width=5),
                        ]),
                    ]),
                ]
            )
        ],
        className='custom-tabs'
    ),
])

@app.callback(
    Output('code_viewer', 'value'),
    Output('export_steps', 'value'),
    Input({'type': 'dynamic-button', 'index': dash.dependencies.ALL}, 'n_clicks'),
    prevent_initial_call=True,
)
def update_code_viewer(n_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update
    else:
        button_id = ctx.triggered[0]['prop_id'].split('.')[0]
        file_name_encoded = json.loads(button_id)['index']
        file_name = base64.b64decode(file_name_encoded).decode()  # decode the file_name from base64
        file_path = os.path.join(python_files_directory, file_name)
        file_name_with_parent = os.path.join(os.path.basename(os.path.dirname(file_path)), os.path.basename(file_path))

        export_steps = textwrap.dedent(f"""\
        # Create a conda env with python=3.8 (recommended)
        git clone https://github.com/groq/mlagility.git
        pip install -e mlagility
        pip install -r mlagility/models/requirements.txt
        benchit mlagility/models/{file_name_with_parent} --export-only\
        """)

        
        if os.path.isfile(file_path):
            with open(file_path, "r") as file:
                code = file.read()
            return code, export_steps
    return "", ""

@app.callback(
    [Output("card_container_all_others", "children"), Output("page_number", "children")],
    [Input("prev_button", "n_clicks"), 
     Input("next_button", "n_clicks"), 
     Input("search_bar_all_others", "value"),
     Input("filter_checklist_tasks_all_others", "value")]
)
def update_cards(prev_clicks, next_clicks, search_value, filter_values):
    print((prev_clicks, next_clicks, search_value, filter_values))
    cards_per_page = 10
    current_page = max(next_clicks - prev_clicks, 0)

    if filter_values is None or len(filter_values) == 0:  # added check for empty list
        if search_value is None or search_value == '':
            filtered_files = python_files
        else:
            filtered_files = [file_name for file_name in python_files if search_value.lower() in file_name.lower()]
    else:
        filtered_files = [file_name for file_name in python_files if task_to_value(matched_files_dict[file_name]['task'].replace('_', ' ')) in filter_values]
        if search_value is not None and search_value != '':
            filtered_files = [file_name for file_name in filtered_files if search_value.lower() in file_name.lower()]

    paginated_files = filtered_files[current_page * cards_per_page: (current_page + 1) * cards_per_page]
    card_components = [python_file_card(file_name) for file_name in paginated_files]
    grid = dbc.Row(
        [
            dbc.Col(card, xs=6)
            for card in card_components
        ],
        className="row-cols-1"
    )
    return grid, f"Page: {current_page + 1}"

@app.callback(
    Output("card_container", "children"),
    [Input("filter_checklist_tasks_onnx", "value"),
     Input("search_bar", "value")]
)
def update_onnx_cards(filter_values, search_value):
    if filter_values is None or len(filter_values) == 0:  # added check for empty list
        if search_value is None or search_value == '':
            card_components = [onnx_card(model_name, model_url) for model_name, model_url in onnx_models]
        else:
            searched_onnx_models = [(model_name, model_url) for model_name, model_url in onnx_models if search_value.lower() in model_name.lower()]
            card_components = [onnx_card(model_name, model_url) for model_name, model_url in searched_onnx_models]
    else:
        filtered_onnx_models = [(model_name, model_url) for model_name, model_url in onnx_models if task_to_value(data[model_name]['task']) in filter_values]
        if search_value is None or search_value == '':
            card_components = [onnx_card(model_name, model_url) for model_name, model_url in filtered_onnx_models]
        else:
            searched_onnx_models = [(model_name, model_url) for model_name, model_url in filtered_onnx_models if search_value.lower() in model_name.lower()]
            card_components = [onnx_card(model_name, model_url) for model_name, model_url in searched_onnx_models]
    grid = dbc.Row(
        [
            dbc.Col(card, lg=4, md=6, xs=12) 
            for card in card_components
        ],
        className="row-cols-1 row-cols-md-2 row-cols-lg-3"
    )

    return grid


if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
