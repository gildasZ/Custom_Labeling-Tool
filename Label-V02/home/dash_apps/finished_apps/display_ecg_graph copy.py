
# home/dash_apps/finished_apps/display_ecg_graph.py
import logging
import datetime
from lxml import etree
import plotly.graph_objs as go
from dash import dcc, html, Output, Input, State
from django_plotly_dash import DjangoDash
import dpd_components as dpd
from dash.exceptions import PreventUpdate
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

from home.utils import handle_annotation_to_csv

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
            channel_name='Receive_Django_Message_Channel'), # channel_name='Path_and_Channel_data_channel'), # Channel whose messages are to be examined
    dpd.Pipe(id='Channels_Data',           # ID in callback
            value = {'all_channels': None},
            label='All-Channels',          # Label used to identify relevant messages
            channel_name='Receive_Django_Message_Channel'), # channel_name='Channels_Extracted'), # Channel whose messages are to be examined
    dpd.Pipe(id='Button_Action',           # ID in callback
            value = {'Action': None},
            label='This-Action',          # Label used to identify relevant messages
            channel_name='Receive_Django_Message_Channel'), # channel_name='Action_Requested') # Channel whose messages are to be examined
    dcc.Store(id='click-data', data= {'Indices': None, 'Manual': None}, storage_type='memory'),  # Store for click data
    dcc.Store(id='prev-file-path-and-channel', data=None, storage_type='memory'),  # Store for previous file path and channel data, Initialized with an empty dict
    dcc.Store(id='Button_Action_Store', data=None, storage_type='memory'),  # Store for handling consecutive 'undo' or 'refresh' actions.
    dcc.Store(id='dummy-output', data=None, storage_type='memory'),
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
])


#----------------------------------------------------------------------------------------------------------

# This callback is supposed to manage the sending of information to Django side, inside the ECGConsumer consummer
@app.callback(
    Output('dummy-output', 'data'),  # Add a dummy output
    [Input('submit-button', 'n_clicks'),
     Input('annotation-input', 'n_submit')], # Handle 'Enter' button to trigger 'Submit'
    [State('annotation-input', 'value'),
     State('click-data', 'data'),
     State('FilePath_and_Channel', 'value'),
     State('Channels_Data', 'value')],
    prevent_initial_call=True
)
def handle_form_submission(submit_n_clicks, enter_pressed, input_value, clicks, file_path_and_channel_data, channels_data, callback_context):
    logger.info(f"\n\n********handle_form_submission callback triggered.\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    logger.info(f"Triggered by: {button_id}\n")
    if button_id in ('submit-button', 'annotation-input'): 
        logger.info(f"You have entered input_value: {input_value}\n")
        sanitized_input = input_value.replace('"', '\\"')  # Properly escape quotation marks
        logger.info(f"The sanitized_input to send is: {sanitized_input}\n")
        click_indices = clicks['Indices']
        logger.info(f"Click indices: {click_indices}\n")

        channels = channels_data['all_channels'] # A list of all channels
        logger.info(f"Data for handle_annotation_to_csv function: \n\t\tchannels data: {channels}")
        full_file_path = file_path_and_channel_data['File-path']
        selected_channel = file_path_and_channel_data['Channel']
        logger.info(f"\t\tfull_file_path data: '{full_file_path}' \n\t\tand selected_channel: '{selected_channel}'\n")

        # Annotation data for handle_annotation_to_csv function 
        annotation_data = {
            'Start Index': click_indices[0],
            'End Index': click_indices[1],
            'Label': sanitized_input,
            'Color': '#FF6347'  # By default for now, later will include a condition for choosing the color
        }
        handle_annotation_to_csv(channels, full_file_path, selected_channel, annotation_data, 'add')
        logger.info(f"Executed handle_annotation_to_csv function to add new annotations to a CSV file.\n")
        
        existing_values = handle_annotation_to_csv(full_file_path=full_file_path, selected_channel=selected_channel, task_to_do='retrieve')
        logger.info(f"Executed handle_annotation_to_csv function: \n\t\tretrieved existing_values = \n{existing_values}\n")

        if existing_values:
            last_item_number = existing_values[-1]['Item Number']
            logger.info(f"The current item number (from the last dictionary) is: {last_item_number}\n")
        else:
            last_item_number = '***'
            logger.info("The list of existing values is empty.")

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            "ecg_analysis_group",  # This is the group name that your consumer should be listening to
            {
                "type": "form_submission",  # This should match a method in your consumer
                "annotation": sanitized_input,
                "click_indices": click_indices,  # Include click indices in the sent data
                "item_number": last_item_number  # Current item number
            }
        )
        logger.info(f"async_to_sync was executed to send sanitized_input data along with click indices to Django.\n")
        return {'status': 'completed'}  # Return some dummy data

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

# This callback will manage the appearance of the annotation area
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
    logger.info(f"\n\n toggle_modal callback triggered.\n")
    # logger.info(f"\ncallback_context: \n{callback_context}\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    logger.info(f"Triggered by: {button_id}\n\n")
    if button_id == 'click-data' and clicks['Indices'] and clicks['Manual'] and len(clicks['Indices']) == 2:
        style['display'] = 'block'  # Show modal
    elif button_id in ('submit-button', 'cancel-button', 'annotation-input'):
        style['display'] = 'none'   # Hide modal
    return style

# Callback to update ButtonAction_Store store, consecutive same clicks of 'undo' or 'refresh' buttons.
@app.callback(
    [Output('Button_Action_Store', 'data')],
    [Input('Button_Action', 'value')],
    [State('click-data', 'data'),
     State('Button_Action_Store', 'data')],
    prevent_initial_call=True
)
def store_action_button_data(Action_var, click_data_Store, Button_Action_Store, callback_context):
    logger.info(f"\n\n store_action_button_data callback triggered.\n")
    logger.info(f"click_data: {click_data_Store}\n")
    logger.info(f"Button_Action_Store: {Button_Action_Store}\n")
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]  # Identifies the input that triggered the callback
    logger.info(f"Triggered by: {trigger_id}\n")
    if trigger_id == 'Button_Action':
        logger.info(f"Triggered by Button_Action with Action_var: {Action_var}\n")
        if Button_Action_Store:
            return Button_Action_Store
        else:
            raise PreventUpdate
    else:
        logger.info(f"\t\t\t\telse condition executed.\n\n\n")
        raise PreventUpdate

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
            # Return the start and end indices of the last dictionary
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']
            existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
            if existing_values:
                last_item = existing_values[-1]
                start_end_indices = [int(last_item['Start Index']), int(last_item['End Index'])]
            else:
                start_end_indices = []
            logger.info(f"Click_data was updated from retrieved data: \n\t\tstart_end_indices = {start_end_indices}\n")
            # Add a flag to indicate that this update is programmatic
            return {'Indices': start_end_indices, 'Manual': False}, file_path_and_channel_data  # Update click-data and update prev_file_path_and_channel
        else:
            logger.info(f"Same file path and channel data received, not resetting click-data.\n")
            raise PreventUpdate  # Prevent callback if the values are the same
    if click_data:
        clicks['Manual'] = True
        x_click = click_data['points'][0]['x']
        logger.info(f"\nx_click: {x_click}\n")
        # button_click = click_data['points'][0].get('button', 0)  # Default to 0 (left click) if 'button' key is not found
        # logger.info(f"x_click: {x_click}, button_click: {button_click}\n")
        if clicks:
            if len(clicks['Indices']) > 0 and x_click < clicks['Indices'][-1]:
                logger.info(f"New click index {x_click} is inferior to the previous index {clicks['Indices'][-1]}, preventing update.\n")
                raise PreventUpdate  # Prevent update if the new index is inferior to the previous index
            clicks['Indices'].append(x_click)
            if len(clicks['Indices']) > 2:  # Keep only the last two clicks
                clicks['Indices'] = clicks['Indices'][-2:]
        else:
            clicks = {'Indices': [x_click], 'Manual': True} # This is the part to modify later to start annotations from index '0'.
        return clicks, prev_file_path_and_channel
    raise PreventUpdate
#----------------------------------------------------------------------------------------------------------

@app.callback(
    Output('ecg-graph', 'figure'),
    [Input('FilePath_and_Channel', 'value'),
     Input('click-data', 'data'),],
    # prevent_initial_call=False # Allow the initial call to trigger the callback 
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
            waveform_data = []
            Title_Color = 'orange'
            plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
            logger.info(f"\n'if condition' waveform_data length: {len(waveform_data)}\n")
            fig = plot_waveform(waveform_data, plot_title, Title_Color) # Assume this function exists and works
            return fig

        elif file_path and channel:
            existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
            logger.info(f"In update_graph callback, \n\texecuted handle_annotation_to_csv function and \n\t\tretrieved existing_values = \n{existing_values}\n")

            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                "ecg_analysis_group",  # This is the group name that your consumer should be listening to
                {
                    "type": "retrieved_data",  # This should match a method in your consumer
                    "Existing_Data": existing_values,
                }
            )
            logger.info(f"async_to_sync was executed to send Retrieved Data to Django.\n")

            logger.info(f"\nUpdating graph in DjangoDash with \n-file path: {file_path} \n-and channel: {channel}\n")
            waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
            plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
            Title_Color = 'green'
            logger.info(f"\n'elif condition' waveform_data length: {len(waveform_data)}\n")
            fig = plot_waveform(waveform_data, plot_title, Title_Color, task_to_do='rebuild', existing_values=existing_values)
            return fig
        
        else:
            logger.info(f"\nElse condition in DjangoDash, maybe there is an error somewhere: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
            waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
            plot_title = f"This is the else condition. Time: {str(datetime.datetime.now())}"
            Title_Color = 'red'
            logger.info(f"\n'else condition' waveform_data: \n{waveform_data}\n")
            logger.info(f"\nwaveform_data length: {len(waveform_data)}\n")
            fig = plot_waveform(waveform_data, plot_title, Title_Color) # Assume this function exists and works
            return fig

    elif trigger_id == 'click-data':    
        if clicks['Indices'] and len(clicks['Indices']) == 2:
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']

            # Check if either file_path or channel is None or empty
            if file_path == "" or file_path is None or channel == "" or channel is None:
                logger.info(f"\nOn 2 clicks, no valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                waveform_data = [] # Assume this function exists and works
                Title_Color = 'orange'
                plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
                logger.info(f"\nOn 2 clicks, 'if condition': waveform_data length: {len(waveform_data)}\n")
                fig = plot_waveform(waveform_data, plot_title, Title_Color) # Assume this function exists and works
                return fig

            elif file_path and channel:
                logger.info(f"\nOn 2 clicks, updating graph in DjangoDash with \n-file path: {file_path} \n-and channel: {channel}\n")
                waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
                Title_Color = 'green'
                logger.info(f"\nOn 2 clicks, 'elif condition': waveform_data length: {len(waveform_data)}\n")
                existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                logger.info(f"In update_graph callback, \n\texecuted handle_annotation_to_csv function and \n\t\tretrieved existing_values = \n{existing_values}\n")
                fig = plot_waveform(waveform_data, plot_title, Title_Color, existing_values=existing_values, click_data=clicks['Indices']) # Assume this function exists and works
                return fig
        
        else:
            raise PreventUpdate

# Function to plot waveform data using Plotly
def plot_waveform(data, plot_title, Title_Color, task_to_do='usual', existing_values=None, click_data=None):
    logger.info(f"plot_waveform function was called!\n")
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

    # Define a list of 12 colors
    colors = [
        '#4fa1ee', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd',
        '#8c564b', '#e377c2', '#7f7f7f', '#bcbd22', '#17becf',
        '#1a55FF', '#db7100'
    ]

    def plot_segments(existing_values, data, color_override=None):
        previous_end_index = 0
        for item in existing_values:
            start_index = int(item['Start Index'])
            end_index = int(item['End Index'])
            color = color_override if color_override else item['Color']
            
            # Plot the portion before the current segment if it exists
            if start_index > previous_end_index:
                logger.info(f"\n\nThe portion before the start index was updated.\n\n")
                segment_before = data[previous_end_index:start_index+1]
                x_values_before = list(range(previous_end_index, start_index+1))
                fig.add_trace(go.Scatter(
                    x=x_values_before, 
                    y=segment_before, 
                    line=dict(color='#4fa1ee'),  # Default color for segments without specific color
                    mode='lines'
                ))
            
            # Plot the current segment
            segment = data[start_index:end_index+1]
            x_values = list(range(start_index, end_index+1))
            fig.add_trace(go.Scatter(
                x=x_values, 
                y=segment, 
                line=dict(color=color), 
                mode='lines'
            ))
            # Update the previous end index
            previous_end_index = end_index
        # Return the index after the last segment
        return previous_end_index

    if data:
        logger.info(f"In plot_segments function, \n\t\t\tif data == True\n")
        if task_to_do == 'rebuild' and existing_values:
            logger.info(f"In plot_segments function, \n\t\t\ttask_to_do == 'rebuild' and existing_values\n")
            previous_end_index = plot_segments(existing_values, data)

            # Plot the portion after the last segment if it exists
            if previous_end_index < len(data):
                segment_after = data[previous_end_index:]
                x_values_after = list(range(previous_end_index, len(data)))
                fig.add_trace(go.Scatter(
                    x=x_values_after, 
                    y=segment_after, 
                    line=dict(color='#4fa1ee'),  # Default color for segments without specific color
                    mode='lines'
                ))

        else:
            logger.info(f"In plot_segments function, \n\t\t\ttask_to_do != 'rebuild'\n")
            if existing_values:
                previous_end_index = plot_segments(existing_values, data)
            else:
                previous_end_index = 0
            
            if click_data:
                x1, x2 = sorted(click_data)
                logger.info(f"In plot_segments function, \n\t\t\tif click_data = True ({click_data})\n")

                if x1 > previous_end_index:
                    logger.info(f"x1 > previous_end_index = {previous_end_index}\n")
                    # Plot the portion before the current segment if it exists
                    segment_before = data[previous_end_index:x1+1]
                    x_values_before = list(range(previous_end_index, x1+1))
                    fig.add_trace(go.Scatter(
                        x=x_values_before, 
                        y=segment_before, 
                        line=dict(color='#4fa1ee'),  # Default color for segments without specific color
                        mode='lines'
                    ))
                    logger.info(f"\n\nThe portion before the x1 index was updated.\n")

                # Plot the clicked segment
                segment = data[x1:x2+1]
                x_values = list(range(x1, x2+1))
                fig.add_trace(go.Scatter(
                    x=x_values, 
                    y=segment, 
                    line=dict(color='green'),  # Highlight the new segment with green color
                    mode='lines'
                ))
                logger.info(f"\n\nThe [x1, x2] segment from click_data was updated.\n\n")

                # Update the previous end index to the end of the clicked segment
                previous_end_index = x2

            # Plot the portion after the last segment if it exists
            if previous_end_index < len(data):
                segment_after = data[previous_end_index:]
                x_values_after = list(range(previous_end_index, len(data)))
                fig.add_trace(go.Scatter(
                    x=x_values_after, 
                    y=segment_after, 
                    line=dict(color='#4fa1ee'),  # Default color for segments without specific color
                    mode='lines'
                ))

    # Final condition to handle empty data
    else:
        fig.add_trace(go.Scatter(
            y=[],
            mode='lines',
            line=dict(color='red')
        ))

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
