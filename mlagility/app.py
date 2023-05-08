import os
import requests
import base64
from io import BytesIO
import pandas as pd
import dash
from dash import html, dcc
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dependencies import Input, Output, State

import pkg_resources

app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP, "/assets/css/style.css"], suppress_callback_exceptions=True)

python_files_directory = pkg_resources.resource_filename('mlagility_models', '')
github_lfs_url = 'https://github.com/onnx/models/blob/main'
onnx_model_directory = '/net/home/rsivakumar/onnx_models/image_classification/'

def fetch_files_by_extension(directory, extension):
    matched_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                matched_files.append(os.path.join(root, file))

    return matched_files

onnx_models = fetch_files_by_extension(onnx_model_directory, ".onnx")
python_files = fetch_files_by_extension(python_files_directory, ".py")

def onnx_card(model_name):
    model_id = model_name.replace(".", "_")
    # Dummy data for now, you can replace these with actual data from your source
    opset = "Opset: 12"
    author = "Author: John Doe"
    use_case = "Use case: Image classification"
    downloads = "Downloads: 1500"

    return dbc.Card(
        [
            dbc.CardHeader(model_name),
            dbc.CardBody(
                [
                    html.P(opset, className="card-text mb-1"),
                    html.P(author, className="card-text mb-1"),
                    html.P(use_case, className="card-text mb-1"),
                    html.P(downloads, className="card-text mb-1"),
                    dbc.Button(
                        [
                            html.I(className="fa fa-arrow-down"),
                        ],
                        id=f"{model_id}_download",
                        className="btn btn-primary position-absolute",
                        style={"bottom": "10px", "right": "10px"},
                    )
                ],
                style={"position": "relative"}
            ),
        ],
        style={"width": "18rem", "margin": "10px"},
    )

def create_filter_panel(identifier):
    return dbc.Card(
        dbc.Checklist(
            options=[
                {"label": "Option 1", "value": 1},
                {"label": "Option 2", "value": 2},
                {"label": "Option 3", "value": 3},
            ],
            id=f"filter_checklist_{identifier}",
            inline=True,
        ),
        className="filter-panel",
    )

app.layout = html.Div([
    dbc.NavbarSimple(
        children=[
            dbc.NavbarBrand(
                html.Img(src="/assets/img/onnx-logo.png", height="50px"),
                className="navbar-brand mr-2"
            ),
            html.Div(
                [
                    html.H1("ONNX Model Zoo", className="navbar-title"),
                    html.H6("Powered by MLAgility", className="navbar-subtitle"),
                ],
                className="navbar-left",
            ),
        ],
        brand=None,
        color="white",
        className="navbar-custom",
    ),
    dcc.Tabs([
        dcc.Tab(label="ONNX models", children=[
            html.Div(className="container-fluid", children=[
                dcc.Input(
                    id="search_bar",
                    type="text",
                    placeholder="Search...",
                    style={"width": "100%", "marginBottom": "10px"},
                    className="search-bar"
                ),
                dbc.Row([
                    dbc.Col([
                        html.H3("Filters"),
                        create_filter_panel("onnx")
                    ], width=2),
                    dbc.Col([
                        dbc.Row([
                            onnx_card(model) for model in onnx_models
                        ]),
                    ], width=10)
                ]),
            ]),
        ]),
        dcc.Tab(label="All others", children=[
            html.Div(className="container-fluid", children=[
                dbc.Row([
                    dbc.Col([
                        html.H3("Filters"),
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
                        dcc.Textarea(
                            id="code_viewer",
                            style={"width": "100%", "height": "40vh"},
                        ),
                    ], width=6),
                ]),
            ]),
        ]),
    ]),
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




# Download button callback for ONNX models
for model in onnx_models:
    model_id = model.replace(".", "_")
    @app.callback(
        Output(f"{model_id}_download", "href"),
        Input(f"{model_id}_download", "n_clicks"),
    )
    def download_onnx_model(n_clicks, model_name=model):
        if n_clicks:
            file_path = os.path.join(onnx_model_directory, model_name)
            response = requests.get(github_lfs_url + file_path)
            b64 = base64.b64encode(BytesIO(response.content).read()).decode()
            href = f'data:application/octet-stream;base64,{b64}'
            return href
        return ''

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
