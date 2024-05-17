
# home/dash_apps/finished_apps/display_ecg_graph.py
import logging
import datetime
import json
from lxml import etree
import plotly.graph_objs as go
from dash import dcc, html, Output, Input, State
from django_plotly_dash import DjangoDash
import dpd_components as dpd
from dash.exceptions import PreventUpdate
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

# Setup logger
logger = logging.getLogger('home')

# Dash app initialization
external_stylesheets = ['https://codepen.io/chriddyp/pen/bWLwgP.css']
app = DjangoDash('Display_ECG_Graph', external_stylesheets=external_stylesheets)
# app = DjangoDash('Display_ECG_Graph')

# Layout of the app
app.layout = html.Div([
    html.H1(f"ECG Waveform. Time: {str(datetime.datetime.now())}", style={
        'textAlign': 'center',
        'color': 'black',
        'font-size': '24px',
        'backgroundColor': '#4fa1ee',
        'margin': '0 auto',
        'padding': '3px 20px',
        'width': 'max-content',
        'display': 'block',
        'border-radius': '10px',
        'font-weight': 'bold',
    }),
    dcc.Graph(id='ecg-graph', style={
                                    "backgroundColor": "#e4451e",
                                    'color': '#ffffff',
                                    # 'height': '100%', 
                                    # 'width': '100%'
                                    },
                                    config={"staticPlot": False},  # Allow hover effects
                                    ), # Think about removing this style later
    dpd.Pipe(id='FilePath_and_Channel',    # ID in callback
            # value = {'File-path': r"C:\Users\gilda\OneDrive\Documents\_NYCU\Master's Thesis\LABORATORY\Labeling Tool\Testing_Folder\20160101_110598000517103_EKG_11059800_110598000517103_001.xml", 
            #          'Channel': "II"},
            value = {'File-path': None, 'Channel': None},
            label='Path_and_Channel_label',                      # Label used to identify relevant messages
            channel_name='Path_and_Channel_data_channel'), # Channel whose messages are to be examined
    dcc.Store(id='click-data', storage_type='memory'),  # Store for click data
    dcc.Store(id='prev-file-path-and-channel', data=None, storage_type='memory'),  # Store for previous file path and channel data, Initialized with an empty dict
    html.Div(
        id='input-modal',
        children=[
            html.P("Enter your annotation:"),
            dcc.Input(id='annotation-input', type='text', placeholder="Type here...", n_submit=0),
            html.Button('Submit', id='submit-button', n_clicks=0),
            html.Button('Cancel', id='cancel-button', n_clicks=0)
        ],
        style={'display': 'none', 'position': 'fixed', 'top': '20%', 'left': '30%', 'width': '40%', 'padding': '20px', 'border': '1px solid black', 'background-color': 'white', 'z-index': '1000'}
    ),


    # dcc.Store(id='modal-visible', data=False),  # Store to manage modal visibility, not being used yet, can think of a use later

    html.Div(id='javascript-output', style={'display': 'none'}),  # Place to inject and send information to Django side's ECGConsumer

])


#----------------------------------------------------------------------------------------------------------

# This callback is supposed to manage the sending of information to Django side, inside the ECGConsumer consummer
@app.callback(
    Output('javascript-output', 'children'),
    [Input('submit-button', 'n_clicks'),
     Input('annotation-input', 'n_submit')], # Handle 'Enter' button to trigger 'Submit'
    [State('annotation-input', 'value'),
     State('click-data', 'data')],
    prevent_initial_call=True
)
def handle_form_submission(submit_n_clicks, enter_pressed, input_value, click_data_value, callback_context):
    logger.info(f"\n\n********handle_form_submission callback triggered.\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    logger.info(f"Triggered by: {button_id}\n")
    if button_id in ('submit-button', 'annotation-input'): # Check which 'annotation-input' is being used. From the Input or from the State
        logger.info(f"If is running, triggered by: {button_id}\n")
        logger.info(f"You have entered input_value: {input_value}\n")
        sanitized_input = input_value.replace('"', '\\"')  # Properly escape quotation marks
        logger.info(f"You have entered sanitized_input: {sanitized_input}\n")

        # Include click indices if available
        click_indices = click_data_value if click_data_value else ['Index_1', 'Index_2']
        logger.info(f"Click indices: {click_indices}\n")

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ecg_analysis_group",  # This is the group name that your consumer should be listening to
            {
                "type": "form_submission",  # This should match a method in your consumer
                "annotation": sanitized_input,
                "click_indices": click_indices  # Include click indices in the sent data
            }
        )
        logger.info(f"async_to_sync was executed to send sanitized_input data along with click indices to Django.\n")

# This callback will clear the 'annotation-input' field whenever it is closed.
@app.callback(
    Output('annotation-input', 'value'),
    [Input('submit-button', 'n_clicks'),
     Input('cancel-button', 'n_clicks'),
     Input('annotation-input', 'n_submit'),],  # Handle 'Enter' button to trigger 'Submit'
    prevent_initial_call=True
)
def clear_input(submit_clicks, cancel_clicks, enter_pressed):
    logger.info(f"\n\n clear_input callback triggered.\n\n")
    return ""  # Clear the input field

# This callback will manage the appearance of the annaotation area
@app.callback(
    Output('input-modal', 'style'),
    [Input('click-data', 'data'), 
     Input('submit-button', 'n_clicks'), 
     Input('cancel-button', 'n_clicks'),
     Input('annotation-input', 'n_submit')], # Handle 'Enter' button to trigger 'Submit'
    [State('input-modal', 'style')],
    prevent_initial_call=True
)
def toggle_modal(clicks, submit_n_clicks, cancel_n_clicks, enter_pressed, style, callback_context):
    logger.info(f"\n\n toggle_modal callback triggered.\n\n")
    logger.info(f"\ncallback_context: \n{callback_context}\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    logger.info(f"Triggered by: {button_id}")
    if button_id == 'click-data' and clicks and len(clicks) == 2:
        style['display'] = 'block'  # Show modal
    elif button_id in ('submit-button', 'cancel-button', 'annotation-input'):
        style['display'] = 'none'   # Hide modal
    return style

# Callback to update click data store, clicks on the waveform for annotation
@app.callback(
    [Output('click-data', 'data'),
     Output('prev-file-path-and-channel', 'data')],
    [Input('ecg-graph', 'clickData'),
     Input('FilePath_and_Channel', 'value')],
    [State('click-data', 'data'),
     State('prev-file-path-and-channel', 'data')],
    prevent_initial_call=True
)
def store_click_data(click_data, file_path_and_channel_data, clicks, prev_file_path_and_channel, callback_context):
    logger.info(f"\n\n store_click_data callback triggered.\n")
    logger.info(f"click_data: {click_data}\n")
    logger.info(f"clicks: {clicks}\n")
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]  # Identifies the input that triggered the callback
    logger.info(f"Triggered by: {trigger_id}\n")
    if trigger_id == 'FilePath_and_Channel':
        logger.info(f"FilePath_and_Channel triggered.\n")
        if file_path_and_channel_data != prev_file_path_and_channel:
            logger.info(f"New file path and channel data received, resetting click-data.\n")
            return [], file_path_and_channel_data  # Reset click-data and update prev_file_path_and_channel
        else:
            logger.info(f"Same file path and channel data received, not resetting click-data.\n")
            raise PreventUpdate  # Prevent callback if the values are the same
    
    if click_data:
        x_click = click_data['points'][0]['x']
        if clicks:
            clicks.append(x_click)
            if len(clicks) > 2:  # Keep only the last two clicks
                clicks = clicks[-2:]
        else:
            clicks = [x_click]
        return clicks, prev_file_path_and_channel
    raise PreventUpdate
#----------------------------------------------------------------------------------------------------------


# @app.callback(
#     Output('ecg-graph', 'figure'),
#     [Input('FilePath_and_Channel', 'value'),])
# def update_graph(file_path_and_channel_data):
@app.callback(
    Output('ecg-graph', 'figure'),
    [Input('FilePath_and_Channel', 'value'),
     Input('click-data', 'data'),],
    # prevent_initial_call=True
)
def update_graph(file_path_and_channel_data, clicks, callback_context):

    if not callback_context.triggered:
        logger.info(f"\n\n update_graph callback triggered for initialization of the Dashboard: \n\n")
        waveform_data = []
        Title_Color = 'orange'
        plot_title = f"Initializing. No Data Available. Time: {str(datetime.datetime.now())}"
        fig = plot_waveform(waveform_data, plot_title, Title_Color) # Assume this function exists and works
        return fig 
        # raise PreventUpdate
    
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]  # Identifies the input that triggered the callback
    logger.info(f"\n\n update_graph callback triggered by trigger_id: \n{trigger_id}\n")
    # logger.info(f"callback_context: \n{callback_context}\n")

    if trigger_id == 'FilePath_and_Channel':
        file_path = file_path_and_channel_data['File-path']
        channel = file_path_and_channel_data['Channel']
        logger.info(f"\n update_graph received \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
   
        # Use this later once everything is okay
        # waveform_data = extract_waveform(file_path, channel) if file_path and channel else []
        # fig = plot_waveform(waveform_data, "ECG Waveform", 'green')

        # Check if either file_path or channel is None or empty
        if file_path == "" or file_path is None or channel == "" or channel is None:
            logger.info(f"\nNo valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
            waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
            Title_Color = 'orange'
            plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
            # logger.info(f"\nwaveform_data: \n{waveform_data}\n")
            logger.info(f"\n'if condition' waveform_data length: {len(waveform_data)}\n")

        elif file_path and channel:
            logger.info(f"\nUpdating graph in DjangoDash with \n-file path: {file_path} \n-and channel: {channel}\n")
            waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
            plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
            Title_Color = 'green'
            # logger.info(f"\nwaveform_data: \n{waveform_data}\n")
            logger.info(f"\n'elif condition' waveform_data length: {len(waveform_data)}\n")
        
        else:
            logger.info(f"\nElse condition in DjangoDash, maybe there is an error somewhere: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
            waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
            plot_title = f"This is the else condition. Time: {str(datetime.datetime.now())}"
            Title_Color = 'red'
            logger.info(f"\n'else condition' waveform_data: \n{waveform_data}\n")
            logger.info(f"\nwaveform_data length: {len(waveform_data)}\n")

        # Plot as usual if not enough clicks or other conditions
        fig = plot_waveform(waveform_data, plot_title, Title_Color) # Assume this function exists and works

        logger.info(f"\nplot_waveform() was executed.\n")
        logger.info(f"\nFinal figure layout: {fig['layout']}\n")
        # logger.info(f"\nData length: {list(fig['data'][0]['y'])}\n")
        logger.info(f"\nData length: {len(fig['data'][0]['y'])}\n")
        return fig 


    elif trigger_id == 'click-data':    
        if clicks and len(clicks) == 2:
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']

            # Check if either file_path or channel is None or empty
            if file_path == "" or file_path is None or channel == "" or channel is None:
                logger.info(f"\nOn 2 clicks, no valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                Title_Color = 'orange'
                plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
                # logger.info(f"\nwaveform_data: \n{waveform_data}\n")
                logger.info(f"\nOn 2 clicks, 'if condition': waveform_data length: {len(waveform_data)}\n")


            elif file_path and channel:
                logger.info(f"\nOn 2 clicks, updating graph in DjangoDash with \n-file path: {file_path} \n-and channel: {channel}\n")
                waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
                Title_Color = 'green'
                # logger.info(f"\nwaveform_data: \n{waveform_data}\n")
                logger.info(f"\nOn 2 clicks, 'elif condition': waveform_data length: {len(waveform_data)}\n")

            else:
                logger.info(f"\nOn 2 clicks, else condition in DjangoDash, maybe there is an error somewhere: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                plot_title = f"This is the else condition. Time: {str(datetime.datetime.now())}"
                Title_Color = 'red'
                logger.info(f"\nOn 2 clicks, 'else condition' waveform_data: \n{waveform_data}\n")
                logger.info(f"\nwaveform_data length: {len(waveform_data)}\n")


            logger.info(f"\nOn 2 clicks, update_graph clicks: {clicks}\n")
            # Convert click positions to indices (approximation)
            x1, x2 = sorted(clicks)
            logger.info(f"\nx1, x2 =: {sorted(clicks)}\n")
            # Split waveform data into three segments
            seg1 = waveform_data[:x1]
            seg2 = waveform_data[x1:x2]
            seg3 = waveform_data[x2:]

            # Color the middle segment differently
            data_segments = [seg1, seg2, seg3]
            # logger.info(f"\ndata_segments: \n{data_segments}\n")

            fig = plot_waveform(data_segments, plot_title, Title_Color) # Assume this function exists and works

            logger.info(f"\nOn 2 clicks, plot_waveform() was executed for data_segments.\n")
            logger.info(f"\nOn 2 clicks, with data_segments, final figure layout: {fig['layout']}\n")
            # logger.info(f"\nData length: {list(fig['data'][0]['y'])}\n")
            logger.info(f"\nOn 2 clicks, data length of data_segments: {len(fig['data'][0]['y'])}\n")

            return fig 
        
        else:
            raise PreventUpdate

# Function to plot waveform data using Plotly
def plot_waveform(data, plot_title, Title_Color):
    # Initialize figure with layout that supports animations
    fig = go.Figure(
        layout={
            'xaxis': {
                'title': 'Sample Index',
                'color': 'yellow',
                'autorange': True,  # Ensure axis range adjusts to fit the data
                # 'uirevision': 'constant'  # Maintain user interactions like zoom/pan
            },
            'yaxis': {
                'title': 'Amplitude',
                'color': 'lightgreen',
                'autorange': True,  # Ensure axis range adjusts to fit the data
                # 'uirevision': 'constant'  # Maintain user interactions
            },
            'title': {'text': plot_title, 'font': {'size': 24, 'color': Title_Color, 'family': 'Arial, sans-serif'}},
            'paper_bgcolor': '#27293d',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'transition': {'duration': 300, 'easing': 'cubic-in-out'}
        }
    )

    # # Example data for three segments
    # data = [
    # [1, 2, 3, 4, 5],
    # [5, 4, 3, 2, 1],
    # [1, 3, 5, 7, 9]]

    # Define a list of 12 colors
    colors = [
        '#4fa1ee', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#1a55FF', '#db7100'
    ]

    # Handle both single list and list of lists for data
    if data and all(isinstance(item, list) for item in data):  # Check if data is a list of lists and not empty
        logger.info(f"\nYes it is instance.\n")
        # logger.info(f"\nYes it is instance, and data = {data}.\n")
        x_start = 0  # Starting x-value for the first segment
        for index, segment  in enumerate(data):
            x_values = list(range(x_start, x_start + len(segment )))  # Generate x-values for the current segment
            logger.info(f"\nIteration {index}.\n")
            # logger.info(f"\nIteration {index}: \n-x_values = {x_values} \n- y_values = {segment }")
            fig.add_trace(go.Scatter(
                x=x_values,  # Set x-values for alignment
                y=segment ,
                line=dict(color=colors[index % len(colors)]),  # Cycle through colors if there are more segments than colors
                mode='lines'
            ))
            x_start += len(segment ) - 1  # Update x_start for the next segment

    else:  # Handle case where data is just a single list
        fig.add_trace(
            go.Scatter(
                y=data,
                mode='lines',
                line=dict(color='#4fa1ee')
            )
        )

    fig.frames = [go.Frame(data=[go.Scatter(y=data)])] # Looks like this can be removed.
    return fig

# Function to extract waveform data from XML file
def extract_waveform(xml_file_path, target_channel):
    try:
        with open(xml_file_path, 'rb') as file:  # Open the XML file
            tree = etree.parse(file)
        root = tree.getroot()
        channels = root.findall('.//Channel')
        target_found = False
        for channel in channels:
            if channel.text.strip() == target_channel:
                target_found = True
                data_element = channel.xpath('./following-sibling::Waveform/Data')[0]
                if data_element is not None and data_element.text:
                    data = data_element.text.strip()
                    return [int(x) for x in data.split()]
                
        if not target_found:
            logger.info(f"\n-------In DjangoDash, target channel '{target_channel}' not found in the XML file.\n")
        return [] #waveform_data
    
    except FileNotFoundError:
        logger.info(f"\n-------In DjangoDash, file not found at path: {xml_file_path}\n")
        return [] #waveform_data
    except etree.XMLSyntaxError as e:
        logger.info(f"\n-------In DjangoDash, XML parsing error in file {xml_file_path}: \n{str(e)}\n")
        return [] #waveform_data
    except Exception as e:
        logger.info(f"\n-------In DjangoDash, unexpected error while processing file {xml_file_path}: \n{str(e)}\n")
        return [] #waveform_data






# # Function to create an empty graph using Plotly
# def create_empty_graph():
#     """Returns an empty Plotly graph with predefined styling."""
#     return go.Figure(
#         data=[go.Scatter(x=[], y=[])],  # Empty data set
#         layout=go.Layout(
#             title = f"No Data Available. Time: {str(datetime.datetime.now())}",
#             title_font=dict(size=24, color='red', family='Arial, sans-serif'),  # Custom font for the title
#             font=dict(family='Arial, sans-serif', size=18, color='white'),  # Default font for all text in layout
#             xaxis=dict(title='Sample Index', color='yellow'),
#             yaxis=dict(title='Amplitude', color='lightgreen'),
#             plot_bgcolor='rgba(0,0,0,0)',  # Transparent background
#             paper_bgcolor='#27293d',  # Dark paper background
#             showlegend=False
#         )
#     )





    # # Update layout to add titles and axis labels
    # fig.update_layout(
    #     # uirevision='constant',  # Helps in maintaining the user-driven changes like zoom level across updates
    #     paper_bgcolor='#27293d',
    #     plot_bgcolor='rgba(0,0,0,0)',
    #     title = plot_title,
    #     title_font=dict(size=24, color=Title_Color, family='Arial, sans-serif'),  # Custom font for the title
    #     font=dict(family='Arial, sans-serif', size=18, color='white'),  # Default font for all text in layout
    #     xaxis=dict( # Will override the font
    #         autorange=True,  # Automatically adjust the x-axis range to fit the data
    #         title='Sample Index',
    #         color='yellow'  # This sets the text color specifically for the x-axis
    #     ),
    #     yaxis=dict( # Will override the font
    #         autorange=True,  # Automatically adjust the x-axis range to fit the data
    #         title='Amplitude',
    #         color='lightgreen'  # This sets the text color specifically for the y-axis
    #     ),
    # )
  




# app.layout = html.Div([
#     html.H1('ECG Graph'),
#     dcc.Input(id='xml-file-path', type='text', style={'display': 'none'}),  # Ensure hidden inputs are available if needed
#     dcc.Input(id='channel-input', type='text', style={'display': 'none'}),
#     html.Button('Submit', id='submit-button', style={'display': 'none'}),
#     dcc.Graph(id='ecg-graph', animate=True)
# ])


# Callback to update graph based on file path and channel
# @app.callback(
#     Output('ecg-graph', 'figure'),
#     Input('submit-button', 'n_clicks'),
#     State('xml-file-path', 'value'), State('channel-input', 'value'),
#     prevent_initial_call=True
# )
# def update_graph(n_clicks, xml_file, channel):
#     # Access Django session using the Django request object if possible
#     request = dash.callback_context.request
#     xml_file = request.session.get('full_file_path', None)  # Get file path from session

#     if n_clicks and xml_file and channel:
#         data = extract_waveform(xml_file, channel)
#         fig = plot_waveform(data)
#         return fig
#     return go.Figure()

# app.layout = html.Div([
#     html.H1('ECG Graph'),
#     dcc.Input(id='xml-file-path', type='text', placeholder='Enter XML file path'),
#     dcc.Input(id='channel-input', type='text', placeholder='Enter Channel (e.g., I)'),
#     html.Button('Submit', id='submit-button'),
#     dcc.Graph(id='ecg-graph', animate=True)
# ])


# @app.callback(
#     Output('ecg-graph', 'figure'),
#     [Input('submit-button', 'n_clicks')],
#     [State('xml-file-path', 'value'), State('channel-input', 'value')]
# )
# def update_graph(n_clicks, xml_file, channel):
#     if n_clicks and xml_file and channel:
#         data = extract_waveform(xml_file, channel)
#         fig = plot_waveform(data)
#         return fig
#     return go.Figure()





















# app.layout = html.Div([
#     html.H1('ECG Graph', style={
#             'textAlign': 'center',
#             'color': 'black',
#             'font-size': '24px',
#             'backgroundColor': '#4fa1ee',
#             'margin': '0 auto',
#             'padding': '3px 20px',
#             'width': 'max-content',
#             'display': 'block',
#             'border-radius': '10px',  
#             'font-weight': 'bold',
#         }),
#     dcc.Graph(id='ecg-graph', animate=True, style={"backgroundColor": "#e4451e", 'color': '#ffffff', 'height': '100%', 'width': '100%'}), # Think about remving this style later
#     dcc.Slider(
#         id='slider-updatemode',
#         marks={i: '{}'.format(i) for i in range(20)},
#         max=20,
#         value=2,
#         step=1,
#         updatemode='drag',
#     ),
# ])
# @app.callback(
#                 Output('ecg-graph', 'figure'),
#                 [Input('slider-updatemode', 'value')])
# def display_value(value):
#     x = []
#     for i in range(value):
#         x.append(i)
#     y = []
#     for i in range(value):
#         y.append(i*i)
#     graph = go.Scatter(
#         x=x,
#         y=y,
#         name='Manipulate Graph',
#         line=dict(color='red'),  # Set the color of the line here
#         marker=dict(color='blue')  # Set the color of the markers here
#     )
#     layout = go.Layout(
#         paper_bgcolor='#27293d',
#         plot_bgcolor='rgba(0,0,0,0)',
#         xaxis=dict(range=[min(x), max(x)]),
#         yaxis=dict(range=[min(y), max(y)]),
#         font=dict(color='white'),
#     )
#     return {'data': [graph], 'layout': layout}







# app = DjangoDash('SimpleExample', external_stylesheets=external_stylesheets)
# app.layout = html.Div([
#     html.H1('Square Root Slider Graph'),
#     dcc.Graph(id='slider-graph', animate=True, style={"backgroundColor": "#1a2d46", 'color': '#ffffff'}),
#     dcc.Slider(
#         id='slider-updatemode',
#         marks={i: '{}'.format(i) for i in range(20)},
#         max=20,
#         value=2,
#         step=1,
#         updatemode='drag',
#     ),
# ])
# @app.callback(
#                 Output('slider-graph', 'figure'),
#                 [Input('slider-updatemode', 'value')])
# def display_value(value):
#     x = []
#     for i in range(value):
#         x.append(i)
#     y = []
#     for i in range(value):
#         y.append(i*i)
#     graph = go.Scatter(
#         x=x,
#         y=y,
#         name='Manipulate Graph'
#     )
#     layout = go.Layout(
#         paper_bgcolor='#27293d',
#         plot_bgcolor='rgba(0,0,0,0)',
#         xaxis=dict(range=[min(x), max(x)]),
#         yaxis=dict(range=[min(y), max(y)]),
#         font=dict(color='white'),
#     )
#     return {'data': [graph], 'layout': layout}
