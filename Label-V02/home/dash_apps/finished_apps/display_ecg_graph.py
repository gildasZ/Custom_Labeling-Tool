
# home/dash_apps/finished_apps/display_ecg_graph.py
import csv
import os
import logging
import datetime
import dpd_components as dpd
import plotly.graph_objs as go
from lxml import etree
from dash import dcc, html, Output, Input, State
from django_plotly_dash import DjangoDash
from dash.exceptions import PreventUpdate
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from home.utils import handle_annotation_to_csv


# Setup logger
logger = logging.getLogger('home')

logger.info(f"display_ecg_graph.py started running!") # Checking how many times the whole code reruns.

# This is just the default list of labels that will be used if 
# no "Testing_existence.csv" is placed in the project directory 'Label-V02'
labels_list = [
                {'label': 'QRS wave (duration, pattern)', 'value': 'QRS wave (duration, pattern)'},
                {'label': 'Baseline', 'value': 'Baseline'},
                {'label': 'P-wave', 'value': 'P-wave'},
                {'label': 'PR interval', 'value': 'PR interval'},
                {'label': 'Q-wave', 'value': 'Q-wave'},
                {'label': 'R-wave', 'value': 'R-wave'},
                {'label': 'S-wave', 'value': 'S-wave'},
                {'label': 'J-point (End point of QRS)', 'value': 'J-point (End point of QRS)'},
                {'label': 'ST segment', 'value': 'ST segment'},
                {'label': 'T-wave', 'value': 'T-wave'},
                {'label': 'RR interval', 'value': 'RR interval'},
            ]

def get_list_of_labels():
    file_path = "Testing_existence.csv"
    
    if not os.path.exists(file_path):
        with open(file_path, mode='w', newline='') as file:
            writer = csv.DictWriter(file, fieldnames=['label', 'value'])
            writer.writeheader()
            for label in labels_list:
                writer.writerow(label)
    
    labels_list_read = []
    with open(file_path, mode='r', newline='') as file:
        reader = csv.DictReader(file)
        for row in reader:
            labels_list_read.append({'label': row['label'], 'value': row['value']})
    
    return labels_list_read

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
    dpd.Pipe(id='session_user_id',    # ID in callback
            value = {'User_id': None},
            label='User_data_Label',                 # Label used to identify relevant messages
            channel_name='User_data_channel'), # Channel whose messages are to be examined
    dpd.Pipe(id='No_FilePath_and_Channel',    # ID in callback
            value = {'No_Count': None, 'User_id': None},
            label='No_Path_and_Channel_label',                      # Label used to identify relevant messages
            channel_name='Empty_Django_Message_Channel'), # Channel whose messages are to be examined
    dpd.Pipe(id='FilePath_and_Channel',    # ID in callback
            # value = {'File-path': r"C:\Users\gilda\OneDrive\Documents\_NYCU\Master's Thesis\LABORATORY\Labeling Tool\Testing_Folder\20160101_110598000517103_EKG_11059800_110598000517103_001.xml", 
            #          'Channel': "II"},
            value = None, #{'File-path': None, 'Channel': None},
            label='Path_and_Channel_label',                      # Label used to identify relevant messages
            channel_name='Receive_Django_Message_Channel'), # channel_name='Path_and_Channel_data_channel'), # Channel whose messages are to be examined
    dpd.Pipe(id='Channels_Data',           # ID in callback
            value = {'all_channels': None},
            label='All-Channels',          # Label used to identify relevant messages
            channel_name='Channels_Extracted'), # channel_name='Channels_Extracted'), # Channel whose messages are to be examined
    dpd.Pipe(id='Button_Action',           # ID in callback
            value = {'Action': None, 'Click_Order': None},
            label='This_Action',          # Label used to identify relevant messages
            channel_name='This_Action_Channel'), # channel_name='Action_Requested') # Channel whose messages are to be examined
    dpd.Pipe(id='Labels_Pipe',    
             value=[{**label, 'display': 1} for label in get_list_of_labels()],  # Modifying the list directly
             label='Labels_Display_Status',
             channel_name='Labels_status_Channel'),  # Channel name for updates
    dcc.Store(id='click-data', data= {'Indices': None, 'Manual': None}, storage_type='memory'),  # Store for click data
    # dcc.Store(id='Button_Action_Store', data=None, storage_type='memory'),  # Store for handling consecutive 'undo' or 'refresh' actions.
    dcc.Store(id='dummy-output', data=None, storage_type='memory'),
    dcc.Store(id='dummy-output_2', data=None, storage_type='memory'),  # I seem forced to use it, but it is not triggering anything
    dcc.Store(id='store_session_user_data', data={'User_name': None, 'Status': 'Empty'}, storage_type='memory'), # I am using this to prevent all instances of the app to be updated for all users.
    html.Div(
        id='input-modal',
        children=[
            html.P("Enter your annotation:"),
            # dcc.Input(id='annotation-input', type='text', placeholder="Type here...", n_submit=0),
            dcc.Dropdown(id='annotation-input', 
                        #  options=[{'label': 'QRS wave (duration, pattern)', 'value': 'QRS wave (duration, pattern)'},
                        #         {'label': 'Baseline', 'value': 'Baseline'},
                        #         {'label': 'P-wave', 'value': 'P-wave'},
                        #         {'label': 'PR interval', 'value': 'PR interval'},
                        #         {'label': 'Q-wave', 'value': 'Q-wave'},
                        #         {'label': 'R-wave', 'value': 'R-wave'},
                        #         {'label': 'S-wave', 'value': 'S-wave'},
                        #         {'label': 'J-point (End point of QRS)', 'value': 'J-point (End point of QRS)'},
                        #         {'label': 'ST segment', 'value': 'ST segment'},
                        #         {'label': 'T-wave', 'value': 'T-wave'},
                        #         {'label': 'RR interval', 'value': 'RR interval'},],
                        # options= labels_list,
                        options= get_list_of_labels(),
                        placeholder="Select an annotation..."),
            html.Button('Submit', id='submit-button', n_clicks=0),
            html.Button('Cancel', id='cancel-button', n_clicks=0)
        ],
        style={'display': 'none', 'position': 'fixed', 'top': '20%', 'left': '30%', 'width': '40%', 'padding': '20px', 'border': '1px solid black', 'background-color': 'white', 'z-index': '1000'}
    ),
])

#----------------------------------------------------------------------------------------------------------

# This callback is the helping piece to have user specific DjangoDash app updates by the update_graph callback and other callbacks. 
# Otherwise all the instances of the DjangoDash App for all users will be updated anythime the callback is triggered by any user.

# Later see if you can make it that it also isolates work in different browsers or tab too if possible for the same user.
@app.callback(
    Output('store_session_user_data', 'data'),
    Input('session_user_id', 'value'),
    State('store_session_user_data', 'data'),
    prevent_initial_call=False # Allow the initial call to trigger the callback 
)
def store_user_specific_info(user_id_pipe, stored_user_data_pipe, callback_context):    
    # if not callback_context.triggered:
    if not callback_context.triggered:
        pipe_user_name = user_id_pipe['User_id']
        stored_user_name = stored_user_data_pipe['User_name']
        logger.info(f"""
            Initializing store_user_specific_info callback, working with \n
            \t-pipe_user_name: {pipe_user_name}\n
            \t-stored_user_name: {stored_user_name}\n
            \t-and stored_user_data_pipe: {stored_user_data_pipe}\n
            """)
        raise PreventUpdate

    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]
    pipe_user_name = user_id_pipe['User_id']
    stored_user_name = stored_user_data_pipe['User_name']
    # stored_user_name = stored_user_id_pipe
    logger.info(f"""
                store_user_specific_info callback triggered by trigger_id: {trigger_id} \n
                \t-pipe_user_name: {pipe_user_name}\n
                \t-and stored_user_name: {stored_user_name}\n
                """)
    if stored_user_data_pipe['Status'] == 'Empty':
        logger.info(f"Updating 'store_session_user_data' with pipe_user_name.")
        return {'User_name': pipe_user_name, 'Status': 'Updated'}
    else:
        logger.info(f"")
        raise PreventUpdate

@app.callback(
    Output('dummy-output_2', 'data'), # Could use it as a state in this callback to prevent further updates
    Input('store_session_user_data', 'data'), 
    [State('session_user_id', 'value'),  # Listen for changes in the Labels_Pipe value
     State('Labels_Pipe', 'value')],  # Get the stored user data
    prevent_initial_call=True  # Ensure this callback only runs when inputs change
)
def send_labels_when_user_available(stored_user_data, user_id_pipe, labels_pipe_value, callback_context):
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]  # Identifies the input that triggered the callback
    logger.info(f"\n\n send_labels_when_user_available callback triggered by: {trigger_id}\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    
    # Get the user_id from the pipe and the stored data
    pipe_user_id = user_id_pipe['User_id']  # This is coming from the session_user_id pipe
    stored_user_id = stored_user_data['User_name']  # Assuming User_name is the correct stored identifier

    # Check if the user_id from the pipe matches the stored user_id
    if stored_user_id and pipe_user_id == stored_user_id:
        logger.info(f"User_id available: {pipe_user_id}. Proceeding to send Labels_Pipe data to Django.")
        # Send the data to Django
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"ecg_analysis_{pipe_user_id}",  # Using the correct user ID in the group name
            {
                "type": "labels_submission",  # This should match the method in the consumer
                "list_labels_display_status": labels_pipe_value,
            }
        )
        logger.info(f"\n\nLabels_Pipe data sent to Django for user_id '{pipe_user_id}': \n{labels_pipe_value}\n")
        return {'status': 'success'}
    else:
        # Log if the user_id is not yet available or doesn't match
        logger.info(f"User_id '{pipe_user_id}' not available or does not match stored user_id '{stored_user_id}'. No action taken.")
        raise PreventUpdate  # No action if user ID is not available or doesn't match

# This callback is supposed to manage the sending of information to Django side, inside the ECGConsumer consummer
@app.callback(
    Output('dummy-output', 'data'),  # Add a dummy output
    [Input('submit-button', 'n_clicks')], 
    [State('annotation-input', 'value'),
     State('click-data', 'data'),
     State('FilePath_and_Channel', 'value'),
     State('Channels_Data', 'value'),
     State('session_user_id', 'value'), 
     State('store_session_user_data', 'data')], 
    prevent_initial_call=True
)
def handle_form_submission(submit_n_clicks, input_value, clicks, file_path_and_channel_data, channels_data, user_id_pipe, stored_user_data_pipe, callback_context):
    logger.info(f"\n\n********handle_form_submission callback triggered.\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    
    # Only proceed if the (stored_user_name and pipe_user_name == stored_user_name)
    pipe_user_name = user_id_pipe['User_id']
    stored_user_name = stored_user_data_pipe['User_name']
    if stored_user_name and pipe_user_name == stored_user_name:
        user_id = user_id_pipe['User_id'] 
        logger.info(f"In handle_form_submission callback, working with user: {user_id}\n")
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
            # Choosing the color for the segment
            segment_color = select_segment_color(sanitized_input)
            annotation_data = {
                'Start Index': click_indices[0],
                'End Index': click_indices[1],
                'Label': sanitized_input,
                'Color': segment_color,  # By default for now, later will include a condition for choosing the color
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
                f"ecg_analysis_{user_id}",  # This is the group name that your consumer should be listening to
                {
                    "type": "form_submission",  # This should match a method in your consumer
                    "annotation": sanitized_input,
                    "click_indices": click_indices,  # Include click indices in the sent data
                    "item_number": last_item_number,  # Current item number
                    'Color': segment_color # Color coresponding to the annotation
                }
            )
            logger.info(f"async_to_sync was executed to send sanitized_input data along with click indices to Django.\n")
            return annotation_data  # Return some dummy data
        else:
            logger.info(f"This is strange. The callback shouldn't have been triggered.\n")
            raise PreventUpdate
    else:
        raise PreventUpdate

# This callback will clear the 'annotation-input' field whenever it is closed.
@app.callback(
    Output('annotation-input', 'value'),
    [Input('submit-button', 'n_clicks'),
     Input('cancel-button', 'n_clicks')], 
    [State('session_user_id', 'value'), 
     State('store_session_user_data', 'data')],
    prevent_initial_call=True
)
def clear_input(submit_clicks, cancel_clicks, user_id_pipe, stored_user_data_pipe):
    # Only proceed if the (stored_user_name and pipe_user_name == stored_user_name)
    pipe_user_name = user_id_pipe['User_id']
    stored_user_name = stored_user_data_pipe['User_name']
    if stored_user_name and pipe_user_name == stored_user_name:
        logger.info(f"\n\n clear_input callback triggered.\n\n")
        return ""  # Clear the input field
    else:
        raise PreventUpdate
    
# This callback will manage the appearance of the annotation area
@app.callback(
    Output('input-modal', 'style'),
    [Input('click-data', 'data'), 
     Input('submit-button', 'n_clicks'), 
     Input('cancel-button', 'n_clicks')], 
    [State('input-modal', 'style'),
     State('session_user_id', 'value'), 
     State('store_session_user_data', 'data')],
    prevent_initial_call=True
)
def toggle_modal(clicks, submit_n_clicks, cancel_n_clicks, style, user_id_pipe, stored_user_data_pipe, callback_context):
    # logger.info(f"\ncallback_context: \n{callback_context}\n")
    if not callback_context.triggered:
        raise PreventUpdate  # Prevent callback if no input has triggered it
    
    # Only proceed if the (stored_user_name and pipe_user_name == stored_user_name)
    pipe_user_name = user_id_pipe['User_id']
    stored_user_name = stored_user_data_pipe['User_name']
    if stored_user_name and pipe_user_name == stored_user_name:
        button_id = callback_context.triggered[0]['prop_id'].split('.')[0]
        logger.info(f"""
                    \n\ntoggle_modal callback triggered by: {button_id}\n
                    clicks: {clicks}\n
                    submit_n_clicks: {submit_n_clicks}\n
                    cancel_n_clicks: {cancel_n_clicks}\n
                    """)
        if button_id == 'click-data' and clicks['Indices'] and clicks['Manual'] and len(clicks['Indices']) == 2:
            style['display'] = 'block'  # Show modal
        elif button_id in ('submit-button', 'cancel-button', 'annotation-input'):
            style['display'] = 'none'   # Hide modal
        logger.info(f"\n\t toggle_modal finished running.\n")
        return style
    else:
        raise PreventUpdate

# Callback to update click data store, clicks on the waveform for annotation
@app.callback(
    Output('click-data', 'data'), # If you have a single output, please don't use []
    [Input('ecg-graph', 'clickData'),
     Input('FilePath_and_Channel', 'value'),
     Input('No_FilePath_and_Channel', 'value'),
     Input('Button_Action', 'value'),
     Input('cancel-button', 'n_clicks')],
    [State('click-data', 'data'), 
     State('session_user_id', 'value'),
     State('store_session_user_data', 'data')],
    prevent_initial_call=True
)
def store_click_data(click_data, file_path_and_channel_data, No_file_path_and_channel_data, Action_var, cancel_clicks, clicks, user_id_pipe, stored_user_data_pipe, callback_context):
    trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]  # Identifies the input that triggered the callback
    logger.info(f"""
                \n\n store_click_data callback triggered by: {trigger_id}\n
                click_data: {click_data}\n
                clicks: {clicks}\n
                file_path_and_channel_data: {file_path_and_channel_data}\n
                """)
    
    # Only proceed if the (stored_user_name and pipe_user_name == stored_user_name)
    pipe_user_name = user_id_pipe['User_id']
    stored_user_name = stored_user_data_pipe['User_name']
    if stored_user_name and pipe_user_name == stored_user_name:
            
        if trigger_id == 'No_FilePath_and_Channel':
            logger.info(f"Resetting click-data to {str({'Indices': [], 'Manual': False})}.\n")
            return {'Indices': [], 'Manual': False}
                # raise PreventUpdate  # Prevent callback 

        elif trigger_id == 'FilePath_and_Channel':
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']
            if file_path and channel:
                logger.info(f"New file path and channel data received, resetting click-data.\n")
                # Return the start and end indices of the last dictionary
                existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                if existing_values:
                    last_item = existing_values[-1]
                    start_end_indices = [int(last_item['Start Index']), int(last_item['End Index'])]
                else:
                    start_end_indices = []
                logger.info(f"Click_data was updated from retrieved data: \n\t\tstart_end_indices = {start_end_indices}\n")
                # Add a flag to indicate that this update is programmatic
                return {'Indices': start_end_indices, 'Manual': False}  # Update click-data 
            else:
                logger.info(f"There is an issue with the file path or the channel received: \n\tfile_path = {file_path} \n\tchannel = {channel}.\n\tresetting click-data to [].\n")
                return {'Indices': [], 'Manual': False}
                # raise PreventUpdate  # Prevent callback 
            
        elif trigger_id == 'Button_Action': # 'refresh' or 'undo' or 'delete
            logger.info(f"\t\t\tConditional executed in store_click_data callback:\n\t\t\t\t\t\t-Action_var: {Action_var}\n")
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']
            action_to_take = Action_var['Action']
            data_to_delete = Action_var['Click_Order']
            if file_path and channel:
                # Check if data_to_delete is a list and if it is empty or not
                if action_to_take == 'delete':
                # if isinstance(data_to_delete, list):
                    # Handle 'Delete' button action
                    logger.info(f"Data to delete: \n\t\tdata_to_delete = {data_to_delete}\n")
                    handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do=action_to_take, delete_data=data_to_delete)
                else:
                    # Handle 'refresh' or 'undo' action
                    handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do=action_to_take)
                # Retrieve existing data
                existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                if existing_values:
                    last_item = existing_values[-1]
                    start_end_indices = [int(last_item['Start Index']), int(last_item['End Index'])]
                else:
                    start_end_indices = []
                logger.info(f"Click_data was updated from retrieved data: \n\t\tstart_end_indices = {start_end_indices}\n")
                # Add a flag to indicate that this update is programmatic
                return {'Indices': start_end_indices, 'Manual': False}  # Update click-data 
            else:
                logger.info(f"There is an issue with the file path or the channel received: \n\tfile_path = {file_path} \n\tchannel = {channel}.\n\t...\n")
                raise PreventUpdate  # Prevent callback 
        
        elif trigger_id == 'cancel-button': 
            logger.info(f"\t\t\tConditional executed in store_click_data callback:\n\t\t\t\t\t\t-Cancellation by: {cancel_clicks}\n")
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']
            if file_path and channel:
                # Retrieve existing data
                existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                if existing_values:
                    last_item = existing_values[-1]
                    start_end_indices = [int(last_item['Start Index']), int(last_item['End Index'])]
                else:
                    start_end_indices = []
                logger.info(f"Click_data was updated from retrieved data: \n\t\tstart_end_indices = {start_end_indices}\n")
                # Add a flag to indicate that this update is programmatic
                return {'Indices': start_end_indices, 'Manual': False}  # Update click-data 
            else:
                logger.info(f"There is an issue with the file path or the channel received: \n\tfile_path = {file_path} \n\tchannel = {channel}.\n\t...\n")
                raise PreventUpdate  # Prevent callback 
        
        # And for trigger_id == 'ecg-graph':
        if click_data:
            clicks['Manual'] = True
            x_click = click_data['points'][0]['x']
            logger.info(f"\nx_click: {x_click}\n")
            # button_click = click_data['points'][0].get('button', 0)  # Default to 0 (left click) if 'button' key is not found
            # logger.info(f"x_click: {x_click}, button_click: {button_click}\n")
            # Check if there are already 2 numbers in 'Indices'
            if len(clicks['Indices']) == 2:
                logger.info("Two indices already present. Resetting the list.")
                clicks['Indices'] = []  # Empty the indices list
            
            # Add the new x_click to Indices
            clicks['Indices'].append(x_click)

            # If we now have 2 values in Indices, sort them before returning
            if len(clicks['Indices']) == 2:
                clicks['Indices'].sort()
                logger.info(f"Indices sorted: {clicks['Indices']}")
            return clicks
        raise PreventUpdate
    else:
        raise PreventUpdate

# This callback will update the DjangoDash app
@app.callback(
    Output('ecg-graph', 'figure'),
    [Input('FilePath_and_Channel', 'value'),
     Input('No_FilePath_and_Channel', 'value'),
     Input('click-data', 'data'), 
     Input('cancel-button', 'n_clicks'),
     Input('dummy-output', 'data'), # Dummy input after the annotation is entered in the working csv file in handle_form_submission callback
     Input('Labels_Pipe', 'value')],  # Input for determining the display status of each label (display or not) 
    [State('Button_Action', 'value'),
     State('session_user_id', 'value'),
     State('store_session_user_data', 'data')]
    # prevent_initial_call=False # Allow the initial call to trigger the callback 
)
def update_graph(file_path_and_channel_data, No_file_path_and_channel_data, clicks, cancel_n_clicks, dummy_output, labels_pipe_value, Action_var, user_id_pipe, stored_user_data_pipe, callback_context):    
    # if not callback_context.triggered:
    if not callback_context.triggered or (callback_context.triggered[0]['prop_id'].split('.')[0] == 'dummy-output' and dummy_output is None):
        logger.info(f"\n\nupdate_graph callback triggered for initialization of the Dashboard: \n")
        waveform_data = []
        Title_Color = 'orange'
        plot_title = f"\tInitializing. No Data Available. Time: {str(datetime.datetime.now())}"
        fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value) # Assume this function exists and works

        user_id = user_id_pipe['User_id']
        logger.info(f"""
                    Initializing update_graph callback, working with user: {user_id}\n
                    dummy_output: \t{dummy_output}\n
                    FilePath_and_Channel: {file_path_and_channel_data}\n
                    click-data: {clicks}\n
                    cancel-button n_clicks: {cancel_n_clicks}\n
                    Button_Action: {Action_var}\n
                    Labels_Pipe: {labels_pipe_value}\n
                    """)
        return fig
    
    # Only proceed if the (stored_user_name and pipe_user_name == stored_user_name)
    pipe_user_name = user_id_pipe['User_id']
    stored_user_name = stored_user_data_pipe['User_name']
    if stored_user_name and pipe_user_name == stored_user_name:
        
        trigger_id = callback_context.triggered[0]['prop_id'].split('.')[0]  # Identifies the input that triggered the callback
        logger.info(f"""
                    update_graph callback triggered by trigger_id: {trigger_id} \n
                    \t-pipe_user_name: {pipe_user_name}\n
                    \t-stored_user_name: {stored_user_name}\n
                    \t-and stored_user_data_pipe: {stored_user_data_pipe}\n
                    """)
        user_id = user_id_pipe['User_id'] 
        logger.info(f"""
                    \n\n In update_graph callback, working with user: {user_id}\n
                    \n update_graph callback triggered by trigger_id: {trigger_id}\n
                    \n dummy_output: \t{dummy_output}\n
                    FilePath_and_Channel: {file_path_and_channel_data}
                    click-data: {clicks}
                    cancel-button n_clicks: {cancel_n_clicks}
                    Button_Action: {Action_var}
                    Labels_Pipe: {labels_pipe_value}\n
                    """)

        if user_id == No_file_path_and_channel_data['User_id']:
            logger.info(f"The user specific coondition was executed for user_id: {user_id}")
        else:
            logger.info(f"The user specific coondition couldn't be executed for user_id: {user_id}")

        if trigger_id == 'FilePath_and_Channel':
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']
            logger.info(f"\n update_graph received \n\t-file_path: '{file_path}' (type: {type(file_path)}) \n\t-and channel: '{channel}' (type: {type(channel)})\n")
    
            # Use this later once everything is okay
            # waveform_data = extract_waveform(file_path, channel) if file_path and channel else []
            # fig = plot_waveform(waveform_data, "ECG Waveform", 'green', labels_pipe_value)

            if file_path and channel:
                existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                logger.info(f"In update_graph callback, \n\texecuted handle_annotation_to_csv function and \n\t\tretrieved existing_values = \n{existing_values}\n")

                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.group_send)(
                    f"ecg_analysis_{user_id}",  # This is the group name that your consumer should be listening to
                    {
                        "type": "retrieved_data",  # This should match a method in consumer
                        "Existing_Data": existing_values,
                    }
                )
                logger.info(f"async_to_sync was executed to send Retrieved Data to Django.\n")

                logger.info(f"\nUpdating graph in DjangoDash with \n\t-file path: {file_path} \n\t-and channel: {channel}\n")
                waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
                Title_Color = 'green'
                logger.info(f"\n'if condition' waveform_data length: {len(waveform_data)}\n")
                fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value, existing_values=existing_values)
                return fig
        
            # Check if either file_path or channel is None or empty
            else:
                logger.info(f"\nNo valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                waveform_data = []
                Title_Color = 'orange'
                plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
                logger.info(f"\n'else condition' waveform_data length: {len(waveform_data)}\n")
                fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value) # Assume this function exists and works
                return fig

        elif trigger_id == 'No_FilePath_and_Channel':
            logger.info(f"\n update_graph Is emptying the graph.\n")
            waveform_data = []
            Title_Color = 'orange'
            plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
            fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value) # Assume this function exists and works
            return fig
            
        elif trigger_id == 'click-data':
            if clicks['Manual']:
                if clicks['Indices'] and len(clicks['Indices']) == 2:
                    file_path = file_path_and_channel_data['File-path']
                    channel = file_path_and_channel_data['Channel']

                    # Check if either file_path or channel is None or empty
                    if file_path and channel:
                        logger.info(f"\nOn 2 clicks, updating graph in DjangoDash with \n-file path: {file_path} \n-and channel: {channel}\n")
                        waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                        plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
                        Title_Color = 'green'
                        logger.info(f"\nOn 2 clicks, 'if condition': waveform_data length: {len(waveform_data)}\n")
                        existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                        logger.info(f"In update_graph callback, \n\texecuted handle_annotation_to_csv function and \n\t\tretrieved existing_values = \n{existing_values}\n")
                        fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value, existing_values=existing_values, click_data=clicks['Indices']) # Assume this function exists and works
                        return fig
                
                    else:
                        logger.info(f"\nOn 2 clicks, no valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                        waveform_data = [] # Assume this function exists and works
                        Title_Color = 'orange'
                        plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
                        logger.info(f"\nOn 2 clicks, 'else condition': waveform_data length: {len(waveform_data)}\n")
                        fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value) # Assume this function exists and works
                        return fig
                
                else:
                    raise PreventUpdate
            else:
                file_path = file_path_and_channel_data['File-path']
                channel = file_path_and_channel_data['Channel']
                action_to_take = Action_var['Action']
                
                logger.info(f"\n update_graph is redrawing the graph on the request of \n\tAction '{action_to_take}' from {Action_var}\n")
        
                # Use this later once everything is okay
                # waveform_data = extract_waveform(file_path, channel) if file_path and channel else []
                # fig = plot_waveform(waveform_data, "ECG Waveform", 'green', labels_pipe_value)

                # Check if either file_path or channel is None or empty

                if file_path and channel:
                    existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                    logger.info(f"In update_graph callback, \n\texecuted handle_annotation_to_csv function and \n\t\tretrieved existing_values = \n{existing_values}\n")

                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f"ecg_analysis_{user_id}",  # This is the group name that your consumer should be listening to
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
                    logger.info(f"\n'if condition' waveform_data length: {len(waveform_data)}\n")
                    fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value, existing_values=existing_values)
                    return fig
                
                # Check if either file_path or channel is None or empty
                else:
                    logger.info(f"\nNo valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                    waveform_data = []
                    Title_Color = 'orange'
                    plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
                    logger.info(f"\n'else condition' waveform_data length: {len(waveform_data)}\n")
                    fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value) # Assume this function exists and works
                    return fig
                
        elif trigger_id in ('cancel-button', 'dummy-output', 'Labels_Pipe'):
            file_path = file_path_and_channel_data['File-path']
            channel = file_path_and_channel_data['Channel']
            
            logger.info(f"\n update_graph is redrawing the graph on the request of \n\t{trigger_id}.\n")

            # Use this later once everything is okay
            # waveform_data = extract_waveform(file_path, channel) if file_path and channel else []
            # fig = plot_waveform(waveform_data, "ECG Waveform", 'green', labels_pipe_value)

            # Check if either file_path or channel is None or empty

            if file_path and channel:
                existing_values = handle_annotation_to_csv(full_file_path=file_path, selected_channel=channel, task_to_do='retrieve')
                logger.info(f"In update_graph callback, \n\texecuted handle_annotation_to_csv function and \n\t\tretrieved existing_values = \n{existing_values}\n")

                logger.info(f"\nUpdating graph in DjangoDash with \n-file path: {file_path} \n-and channel: {channel}\n")
                waveform_data = extract_waveform(file_path, channel) # Assume this function exists and works
                plot_title = f"Remove after debugging. Time: {str(datetime.datetime.now())}"
                Title_Color = 'green'
                logger.info(f"\n'if condition' waveform_data length: {len(waveform_data)}\n")
                fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value, existing_values=existing_values)

                # if trigger_id == 'Labels_Pipe':
                #     channel_layer = get_channel_layer()
                #     async_to_sync(channel_layer.group_send)(
                #         f"ecg_analysis_{user_id}",  # This is the group name that your consumer should be listening to
                #         {
                #             "type": "retrieved_data",  # This should match a method in your consumer
                #             "Existing_Data": existing_values,
                #         }
                #     )
                #     logger.info(f"async_to_sync was executed to send Retrieved Data to Django.\n")
                
                return fig
            
            # Check if either file_path or channel is None or empty
            else:
                logger.info(f"\nNo valid file path or channel data received in DjangoDash: \n-file_path: '{file_path}' (type: {type(file_path)}) \n-and channel: '{channel}' (type: {type(channel)})\n")
                waveform_data = []
                Title_Color = 'orange'
                plot_title = f"No Data Available. Time: {str(datetime.datetime.now())}"
                logger.info(f"\n'else condition' waveform_data length: {len(waveform_data)}\n")
                fig = plot_waveform(waveform_data, plot_title, Title_Color, labels_pipe_value) # Assume this function exists and works
                return fig
    else:
        raise PreventUpdate

#----------------------------------------------------------------------------------------------------------

# Function to plot waveform data using Plotly
def plot_waveform(data, plot_title, Title_Color, labels_pipe_value, existing_values=None, click_data=None):
    logger.info(f"plot_waveform function was called!\n")
    # Initialize figure with layout that supports animations and small ECG-like grids

    # x_range = len(data) if data else 100  
    # y_range = max(data) - min(data) if data else 10 
    # dtick_x = x_range / 100 
    # dtick_y = y_range / 10 
    fig = go.Figure(
        layout={
            'xaxis': {
                'title': 'Sample Index',
                'color': 'yellow',
                'autorange': True,  # Ensure axis range adjusts to fit the data
                # 'uirevision': 'constant'  # Maintain user interactions like zoom/pan
                'showgrid': True,   # Show grid lines
                'gridcolor': '#404040',  # A dark grey color of the vertical grid lines
                'gridwidth': 1,     # Make the grid lines thin
                'dtick': 50,       # Smaller grid spacing for ECG
            },
            'yaxis': {
                'title': 'Amplitude',
                'color': 'lightgreen',
                'autorange': True,  # Ensure axis range adjusts to fit the data
                # 'uirevision': 'constant'  # Maintain user interactions
                'showgrid': True,   # Show grid lines
                'gridcolor': '#404040',  # A dark grey color of the horizontal grid lines
                'gridwidth': 1,     # Make the grid lines thin
                'dtick': 10,       # Smaller grid spacing for ECG
            },
            'title': {'text': plot_title, 'font': {'size': 24, 'color': Title_Color, 'family': 'Arial, sans-serif'}},
            'paper_bgcolor': '#27293d',
            'plot_bgcolor': 'rgba(0,0,0,0)',
            'transition': {'duration': 300, 'easing': 'cubic-in-out'},
            'legend': { # Adding legend configuration
                'font': {
                    'color': 'Black',  # Legend text color
                    'size': 14,      # Legend font size
                    'family': 'Arial, sans-serif',  # Font family
                    # 'family': 'Arial Black, sans-serif'  # Choose a bold font family
                },
                # 'bgcolor': 'LightSteelBlue',  # Optional: Legend background color
                'bgcolor': 'white', # Optional: Legend background color
                'bordercolor': 'Black',  # Optional: Legend border color
                'borderwidth': 2  # Optional: Legend border width
            }
        }
    )

    def get_display_status(segment_name):
        for label_data in labels_pipe_value:
            if label_data['value'] == segment_name:
                # Retrieve the display status (default to False if 'display' key is missing)
                return label_data.get('display', 0) == 1
        return False

    def plot_segments(existing_values, data, color_override=None):
        for item in existing_values:
            start_index = int(item['Start Index'])
            end_index = int(item['End Index'])
            color = color_override if color_override else item['Color']
            label_name = item['Label']
            segment_name = f"Item {item['Item Number']}: {item['Label']}"  # Use the label from the item for the trace name
            display_status = get_display_status(label_name)  # Retrieve display status for this segment
            # logger.info(f"Display value: {display_status}")
            if display_status:
                # Plot only the annotated segments (they'll overlay on the full plot)
                segment = data[start_index:end_index+1]
                x_values = list(range(start_index, end_index+1))
                fig.add_trace(go.Scatter(
                    x=x_values, 
                    y=segment, 
                    line=dict(color=color),  # Use color from annotations
                    mode='lines',
                    name=f"<span style='color:{color}'>{segment_name}</span>",  # Custom name with color
                ))
            else:
                logger.info(f"Skipping segment: {segment_name} due to display being set to 0")
    
    # Plot annotations over the full waveform
    if data:
        logger.info(f"In plot_segments function, \n\t\t\tif data == True\n")

        # First, draw the entire waveform with the default color
        x_values_full = list(range(len(data)))
        fig.add_trace(go.Scatter(
            x=x_values_full, 
            y=data, 
            line=dict(color='#4fa1ee'),  # Default color for the entire line
            mode='lines',
            # name='Default',  # Custom trace name
            name=f"<span style='color:{'#4fa1ee'}'>{'Default'}</span>"  # Custom name with color
        ))

        if existing_values:
            logger.info(f"In plot_segments function, \n\t\t\trebuilding annotations from existing_values\n")
            plot_segments(existing_values, data)

        if click_data:
            x1, x2 = sorted(click_data)
            logger.info(f"In plot_segments function, \n\t\t\tif click_data = True ({click_data})\n")
            # Plot the clicked segment (it will overlay the default line)
            segment = data[x1:x2+1]
            x_values = list(range(x1, x2+1))
            fig.add_trace(go.Scatter(
                x=x_values, 
                y=segment, 
                line=dict(color='green'),  # Highlight the new segment
                mode='lines'
            ))
            logger.info(f"\n\nThe [x1, x2] segment from click_data was updated.\n\n")

    else:
        fig.add_trace(go.Scatter(
            y=[],
            mode='lines',
            line=dict(color='red')
        ))

    # fig.frames = [go.Frame(data=[go.Scatter(y=data)])] # Looks like this can be removed.
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

# Function to select the color
def select_segment_color(sanitized_input):
    # List of options
    options = get_list_of_labels()

    options = [item['value'] for item in options]

    print(f"\nList of Options was extracted: \n{options}\n")

    # List of colors
    colors = [
        "#ff7f0e",  # orange
        "#d62728",  # red
        "#9467bd",  # purple
        "#8c564b",  # brown
        "#e377c2",  # pink
        "#7f7f7f",  # gray
        "#bcbd22",  # yellow-green
        "#17becf",  # cyan
        "#1a55FF",  # deep blue
        "#db7100",  # dark orange
        "#ffbb78",  # light orange
        "#ff9896",  # light red
        "#c5b0d5",  # light purple
        "#c49c94",  # light brown
        "#f7b6d2",  # light pink
        "#c7c7c7",  # light gray
        "#dbdb8d",  # light yellow-green
        "#9edae5",  # light cyan
        "#aec7e8"   # light blue
    ]

    # Default color
    # default_color = "#4fa1ee"
    default_color = "#9467bd" # purple

    # Ensure the list of colors is at least as long as the list of options
    assert len(colors) >= len(options), "Not enough colors provided for the options"
    
    try:
        # Get the index of the selected option 
        index = options.index(sanitized_input)
        # Return the corresponding color
        return colors[index]
    except ValueError:
        # If the input is not in the options list, fall back to the default color
        return default_color
