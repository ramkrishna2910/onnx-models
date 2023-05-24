import os
import requests
import base64
from io import BytesIO
import pandas as pd
import dash
import yaml
from dash import html, dcc
import dash_ace
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dependencies import Input, Output, State
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pkg_resources

#Global Constants

# Read the connection string from an environment variable. Contact @ramkrishna2910 for demo.
# Once this website is live, connection string will be handled by Azure managed services
connection_string = os.getenv("AZURE_S_C_S")
container_name = "onnx-models"
account_name = "onnxtrial"
blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)
blobs_list = container_client.list_blobs()
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


def get_public_blob_url(account_name, container_name, blob_name):
    return f"https://{account_name}.blob.core.windows.net/{container_name}/{blob_name}"

def fetch_files_by_extension(directory, extension):
    matched_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                matched_files.append(os.path.join(root, file))

    return matched_files

onnx_models = [(blob.name, get_public_blob_url(account_name, container_name, blob.name)) for blob in blobs_list]
python_files = fetch_files_by_extension(python_files_directory, ".py")

# Load the yaml file
with open('model-metadata.yaml') as f:
    data = yaml.safe_load(f)

def onnx_card(model_name, model_url):
    model_id = model_name.replace(".", "_")
    display_name = model_name.replace(".onnx", "")
    use_case = data[model_name]['task']
    opset = data[model_name]['opset']
    description = data[model_name]['description']

    info_id = f"{model_id}_info"

    return dbc.Card(
        [
            dbc.CardHeader([
                html.Div(display_name, className="float-left"),  # Float the model name to the left
                dbc.Button("i", id=info_id, color="link", className="float-right info-circle")  # Float the button to the right
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
                        download=model_name,
                        href=""
                    )
                ],
                style={"position": "relative"}
            ),
        ],
        style={"width": "18rem", "margin": "10px"},
    )

def task_to_value(task):
    task_value_mapping = {
        "Vision": 1,
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
                                {"label": "Vision", "value": 1},
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

# Grid of cards
grid = dbc.Row(
    [
        dbc.Col(onnx_card(model_name, model_url), lg=4, md=6, xs=12) 
        for model_name, model_url in onnx_models
    ],
    className="row-cols-1 row-cols-md-2 row-cols-lg-3"
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
                    html.H6("Powered by MLAgility", className="navbar-subtitle"),
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
                            style={"width": "100%", "marginBottom": "20px"},
                            className="form-control form-control-lg rounded-pill"
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
                            dcc.Input(
                            id="search_bar_all_others",
                            type="text",
                            placeholder="Search...",
                            style={"width": "100%", "marginBottom": "20px"},
                            className="form-control form-control-lg rounded-pill"
                        ),
                        dbc.Row([
                            dbc.Col([
                                html.H4("Filters"),
                                create_filter_panel("all_others")
                            ], width=3),
                            dbc.Col([
                                html.H3("Python Files"),
                                dash_table.DataTable(
                                    id="file_table",
                                    columns=[{"name": "Files", "id": "file"}],
                                    data=[{"file": file} for file in python_files],
                                    style_cell={
                                        'whiteSpace': 'normal',
                                        'height': 'auto',
                                        'textAlign': 'left'
                                    },
                                    style_table={'overflowX': 'auto'},
                                    style_header={
                                        'backgroundColor': 'rgb(230, 230, 230)',
                                        'fontWeight': 'bold'
                                    },
                                    page_size=10,
                                    row_selectable="single",
                                    selected_rows=[],
                                ),
                            ], width=3),
                            dbc.Col([
                                html.H3("Code Viewer"),
                                dash_ace.DashAceEditor(
                                    id='code_viewer',
                                    mode='python',
                                    theme='monokai',
                                    value='',
                                    wrapEnabled=True,
                                    showPrintMargin=False,
                                    style={"width": "100%",
                                           "height": "50vh",
                                           "fontFamily": "Menlo, monospace",
                                           "lineHeight": "1.4",
                                           "borderRadius": "10px", },
                                    readOnly=True,
                                ),
                                html.H3("Steps to export to ONNX"),
                                dash_ace.DashAceEditor(
                                    id='export_steps',
                                    mode='python',
                                    theme='monokai',
                                    value='',
                                    wrapEnabled=True,
                                    showPrintMargin=False,
                                    style={"width": "100%",
                                           "height": "20vh",
                                           "fontFamily": "Menlo, monospace",
                                           "lineHeight": "1.4",
                                           "borderRadius": "10px", },
                                    readOnly=True,
                                ),
                            ], width=6),
                        ]),
                    ]),
                ]
            ),
        ],
        className='custom-tabs'
    ),
])



@app.callback(
    Output("code_viewer", "value"),
    Input("file_table", "selected_rows"),
    State("file_table", "data")
)
def update_code_viewer(selected_rows, table_data):
    if selected_rows:
        file_name = table_data[selected_rows[0]]["file"]
        file_path = os.path.join(python_files_directory, file_name)
        if os.path.isfile(file_path):
            with open(file_path, "r") as file:
                code = file.read()
            return code
    return ""

@app.callback(
    Output("export_steps", "value"),
    Input("file_table", "selected_rows"),
    State("file_table", "data")
)
def update_export_steps(selected_rows, table_data):
    if selected_rows:
        file_name = table_data[selected_rows[0]]["file"]
        return f"benchit {file_name} --export-only"
    return ""

# Download button callback for ONNX models
for model_name, model_url in onnx_models:
    model_id = model_name.replace(".", "_")
    @app.callback(
        Output(f"{model_id}_download", "href"),
        Input(f"{model_id}_download", "n_clicks"),
    )
    def download_onnx_model(n_clicks, model_url=model_url):
        if n_clicks:
            return model_url  # Simply return the model URL
        return ''

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


@app.callback(
    Output("file_table", "data"),
    Input("search_bar_all_others", "value")
)
def update_file_table(search_value):
    if search_value is None or search_value == '':
        return [{"file": os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))} for file in python_files]
    else:
        searched_files = [file for file in python_files if search_value.lower() in file.lower()]
        return [{"file": os.path.join(os.path.basename(os.path.dirname(file)), os.path.basename(file))} for file in searched_files]


if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
