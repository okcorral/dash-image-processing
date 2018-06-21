import os
import base64
import time
import sys

import pandas as pd
import numpy as np
import json
import dash
from PIL import Image, ImageFilter
from dash.dependencies import Input, Output, State
import dash_core_components as dcc
import dash_html_components as html
import dash_reusable_components as drc
import plotly.graph_objs as go

from utils import FILTER_OPTIONS, STORAGE_PLACEHOLDER, GRAPH_PLACEHOLDER
from utils import apply_filters

DEBUG = True

app = dash.Dash(__name__)
server = app.server

# Custom Script for Heroku
if 'DYNO' in os.environ:
    app.scripts.append_script({
        'external_url': 'https://cdn.rawgit.com/chriddyp/ca0d8f02a1659981a0ea7f013a378bbd/raw/e79f3f789517deec58f41251f7dbb6bee72c44ab/plotly_ga.js'
    })

app.layout = html.Div([
    # Banner display
    html.Div([
        html.H2(
            'App Name',
            id='title'
        ),
        html.Img(
            src="https://s3-us-west-1.amazonaws.com/plotly-tutorials/logo/new-branding/dash-logo-by-plotly-stripe-inverted.png"
        )
    ],
        className="banner"
    ),

    # Body
    html.Div(className="container", children=[
        html.Div(className='row', children=[
            html.Div(className='four columns', children=[
                drc.Card([
                    dcc.Upload(
                        id='upload-image',
                        children=[
                            'Drag and Drop or ',
                            html.A('Select a File')
                        ],
                        style={
                            'width': '100%',
                            'height': '50px',
                            'lineHeight': '50px',
                            'borderWidth': '1px',
                            'borderStyle': 'dashed',
                            'borderRadius': '5px',
                            'textAlign': 'center'
                        },
                        accept='image/*'
                    ),

                    html.Div(
                        id='div-storage-image',
                        children=STORAGE_PLACEHOLDER,  # [Bytes, Filename, Image Size]
                        style={'display': 'none'}
                    ),

                    # drc.NamedInlineRadioItems(
                    #     name='Selection Mode',
                    #     short='selection-mode',
                    #     options=[
                    #         {'label': 'Rectangular', 'value': 'select'},
                    #         {'label': 'Lasso', 'value': 'lasso'}
                    #     ],
                    #     val='select'
                    # ),
                ]),

                drc.Card([
                    dcc.Dropdown(
                        id='dropdown-filters',
                        options=FILTER_OPTIONS,
                        searchable=False,
                        placeholder='Use a Filter'
                    ),

                    html.Button('Run Operation', id='button-run-operation')
                ]),
            ]),

            html.Div(className='eight columns', children=[
                html.Div(
                    id='div-interactive-image',
                    children=GRAPH_PLACEHOLDER  # Placeholder
                )
            ])
        ])
    ])
])


@app.callback(Output('div-storage-image', 'children'),
              [Input('upload-image', 'contents'),
               Input('button-run-operation', 'n_clicks')],
              [State('dropdown-filters', 'value'),
               State('interactive-image', 'selectedData'),
               State('upload-image', 'filename'),
               State('div-storage-image', 'children')])
def update_image_storage(content, n_clicks, filters, selectedData, new_filename, storage):
    t1 = time.time()

    # Retrieve data from storage
    enc_str, filename, im_size, im_mode = storage

    # TODO: Add support for Lasso
    # Define the zone selected by user
    if selectedData and selectedData['points']:  # lasso mode
        selection_mode = 'lasso'
        selection_zone = (0, 0, 1, 1)

    elif selectedData and selectedData['range']['y']:  # select mode
        selection_mode = 'select'
        lower, upper = map(int, selectedData['range']['y'])
        left, right = map(int, selectedData['range']['x'])

        # Adjust height difference
        height = eval(im_size)[1]
        upper = height - upper
        lower = height - lower

        selection_zone = (left, upper, right, lower)

    else:
        selection_mode = 'select'
        selection_zone = (0, 0) + eval(im_size)

    # If the file has changed (when a file is uploaded)
    if new_filename and new_filename != filename:
        if DEBUG:
            print(filename, "replaced by", new_filename)

        string = content.split(';base64,')[-1]
        im_pil = drc.b64_to_pil(string)

    elif filters:
        im_pil = drc.bytes_string_to_pil(encoding_string=enc_str, size=im_size, mode=im_mode)

        apply_filters(
            image=im_pil,
            zone=selection_zone,
            filter=filters,
            mode=selection_mode)

    else:
        return storage

    enc_str, im_size, im_mode = drc.pil_to_bytes_string(im_pil)

    t2 = time.time()
    if DEBUG:
        print(f"Updated Image Storage in {t2-t1:.3f} sec")

    return [enc_str, new_filename, str(im_size), im_mode]


@app.callback(Output('div-interactive-image', 'children'),
              [Input('div-storage-image', 'children')])
def update_interactive_image(children):
    if children[0]:
        t1 = time.time()
        enc_str, filename, im_size, im_mode = children

        im_pil = drc.bytes_string_to_pil(encoding_string=enc_str, size=im_size, mode=im_mode)

        t2 = time.time()
        if DEBUG:
            print(f"Size of the image file: {sys.getsizeof(enc_str)} bytes")
            print(f"Decoded interactive image in {t2-t1:.3f} sec")

        return drc.InteractiveImagePIL(
            image_id='interactive-image',
            image=im_pil,
            enc_format='bmp',
            display_mode='fixed',
            verbose=DEBUG
        )

    else:
        return GRAPH_PLACEHOLDER


@app.callback(Output('dropdown-filters', 'value'),
              [Input('button-run-operation', 'n_clicks')])
def reset_dropdown_filters(n_clicks):
    return None


external_css = [
    "https://cdnjs.cloudflare.com/ajax/libs/normalize/7.0.0/normalize.min.css",  # Normalize the CSS
    "https://fonts.googleapis.com/css?family=Open+Sans|Roboto"  # Fonts
    "https://maxcdn.bootstrapcdn.com/font-awesome/4.7.0/css/font-awesome.min.css",
    "https://cdn.rawgit.com/xhlulu/0acba79000a3fd1e6f552ed82edb8a64/raw/dash_template.css"  # For production,
    # "https://rawgit.com/xhlulu/dash-image-display-experiments/master/custom_styles.css"  # For Development
]

for css in external_css:
    app.css.append_css({"external_url": css})

# Running the server
if __name__ == '__main__':
    app.run_server(debug=True)
