import os
import requests
import base64
from io import BytesIO
import pandas as pd
import dash
from dash import html, dcc
import dash_ace
import dash_bootstrap_components as dbc
from dash import dash_table
from dash.dependencies import Input, Output, State
from azure.storage.blob import BlobServiceClient, BlobClient, ContainerClient
import pkg_resources

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

# Read the connection string from an environment variable. Contact @ramkrishna2910 for demo.
# Once this website is live, connection string will be handled by Azure managed services
connection_string = os.getenv("AZURE_S_C_S")
container_name = "onnx-models"
account_name = "onnxtrial"

blob_service_client = BlobServiceClient.from_connection_string(connection_string)
container_client = blob_service_client.get_container_client(container_name)

blobs_list = container_client.list_blobs()
onnx_models = [(blob.name, get_public_blob_url(account_name, container_name, blob.name)) for blob in blobs_list]


python_files_directory = pkg_resources.resource_filename('mlagility_models', '')

def fetch_files_by_extension(directory, extension):
    matched_files = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(extension):
                matched_files.append(os.path.join(root, file))

    return matched_files

python_files = fetch_files_by_extension(python_files_directory, ".py")

def onnx_card(model_name, model_url):
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
                    html.A(
                        html.I(className="fas fa-arrow-down"),  # Using a down arrow icon instead of text
                        id=f"{model_id}_download",
                        className="btn btn-primary btn-sm position-absolute",
                        style={"bottom": "10px", "right": "10px"},
                        download=model_name,
                        href=""  # Will be populated by the callback
                    )
                ],
                style={"position": "relative"}
            ),
        ],
        style={"width": "18rem", "margin": "10px"},
    )

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
                        ),
                        label="Tasks",
                    ),
                    # dbc.Tab(
                    #     dbc.Checklist(
                    #         options=[
                    #             {"label": "Convolutional Neural Network (CNN)", "value": 1},
                    #             {"label": "Recurrent Neural Network (RNN)", "value": 2},
                    #             {"label": "Long Short-Term Memory (LSTM)", "value": 3},
                    #             {"label": "Transformers", "value": 4},
                    #             {"label": "Generative Adversarial Network (GAN)", "value": 5},
                    #             {"label": "Graph Neural Networks (GNN)", "value": 6},
                    #         ],
                    #         id=f"filter_checklist_architectures_{identifier}",
                    #         inline=True,
                    #     ),
                    #     label="Model Architectures",
                    # ),
                ],
                className="nav-tabs-custom",
                style={"display": "flex"},
            ),
            dbc.Row(
                [
                    dbc.Col(
                        [
                            dbc.Label("Parameter count"),
                            dcc.Slider(
                                id=f"parameter_count_slider_{identifier}",
                                min=0,
                                max=100,
                                value=50,
                                marks={i: str(i) for i in range(0, 101, 50)},
                                tooltip={"always_visible": False, "placement": "bottom"},
                            ),
                        ],
                        width={"size": 60, "offset": 0},
                    )
                ]
            ),
        ],
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
                    ], width=3),
                    dbc.Col([
                        dbc.Row([
                            onnx_card(model_name, model_url) for model_name, model_url in onnx_models
                        ]),
                    ], width=9)
                ]),
            ]),
        ]),
        dcc.Tab(label="All others", children=[
            html.Div(className="container-fluid", children=[
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
                            style={"width": "100%", "height": "50vh", "fontFamily": "Menlo, monospace", "lineHeight": "1.4"},
                            readOnly=True,
                        ),
                        html.H3("Steps to export to ONNX"),
                        dash_ace.DashAceEditor(
                            id='export_steps',
                            mode='python',
                            theme='monokai',
                            value='',
                            style={"width": "100%", "height": "20vh", "fontFamily": "Menlo, monospace", "lineHeight": "1.4"},
                            readOnly=True,
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

if __name__ == "__main__":
    app.run_server(debug=True, port=8051)
