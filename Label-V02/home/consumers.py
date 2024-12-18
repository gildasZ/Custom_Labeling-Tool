
# home/consumers.py
import json
import logging
import html
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from .utils import process_xml_data, convert_path, handle_annotation_to_csv
from django_plotly_dash.consumers import async_send_to_pipe_channel

# Setup logger
logger = logging.getLogger('home')

class ECGConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope["user"]  # Access the user from the scope
        if not self.user.is_authenticated:
            await self.close()
        else:
            logger.info(f"\nWebSocket connect called by {self.user.username}.\n")
            # Initialize instance variables: channels extracted from xml files, current file path, reset condition 
            # for consecutive 'undo' or 'refresh' clicks, the consecutive excution count number, and past action.
            self.channels_values = None
            self.current_file_path = None
            self.handle_condition = False
            self.count_number = 0
            self.count_number_empty_channel = 0
            self.past_action = None

            # Join the group that will receive messages from DjangoDash
            self.User_name = self.user.username
            self.User_id = self.user.id

            # Use this later

            # # Initialize instance variables in a dictionary
            # self.user_data = {
            #     'channels_values': None,
            #     'current_file_path': None,
            #     'handle_condition': False,
            #     'count_number': 0,
            #     'past_action': None,
            #     'count_number_empty_channel': 0
            # }

            self.group_name = f"ecg_analysis_{self.User_name}"
            await self.channel_layer.group_add(self.group_name, self.channel_name)

            try:
                await self.accept()
                # Send user data upon connection
                await self.send(text_data=json.dumps({
                    'type': 'user_data',
                    'User_name': self.User_name,
                    'User_id': self.User_id,
                }))
                logger.info(f"\n----- Django sent to the client: \n\tUser_name: {self.User_name}, \n\tUser_id: {self.User_id}\n")
            except asyncio.CancelledError:
                await self.close(code=1001)  # Indicates that the server is shutting down

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)
        logger.info(f"\nWebSocket disconnect called with close code {close_code} by {self.user.username}.\n")

    async def receive(self, text_data):
        logger.info(f"\nDjango Received data through WebSocket from {self.user.username}: {text_data}.\n")
        data = json.loads(text_data)

        #______________________________________________________________________________
        if data['type'] == 'processXML':
            # Sending message to Pipe in DjangoDash ###################################
            
            # Send the User ID to Pipe
            Data_to_Send = {'User_id': self.User_name}
            await async_send_to_pipe_channel(
                        channel_name = 'User_data_channel',  # Fixed channel name for the first pipe
                        label = 'User_data_Label',  # Fixed label for the first pipe
                        value = Data_to_Send)
            logger.info(f"\n+++++ Django sent Message Channel data to dpd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}\n\tin conditional if data['type'] == 'processXML'")
            
            # Sending empty data to Pipe
            if self.count_number_empty_channel == 0:
                self.count_number_empty_channel += 5
            else:
                self.count_number_empty_channel = 0
            counting = self.count_number_empty_channel
            Data_to_Send = {'No_Count': counting, 'User_id': self.User_name}
            await async_send_to_pipe_channel(
                        channel_name = 'Empty_Django_Message_Channel',  # Fixed channel name for the first pipe
                        label = 'No_Path_and_Channel_label',  # Fixed label for the first pipe
                        value = Data_to_Send)
            # Data_to_Send = {'File-path': None, 'Channel': None}
            # await async_send_to_pipe_channel(
            #             channel_name = 'Receive_Django_Message_Channel',  # Fixed channel name for the second pipe
            #             label = 'Path_and_Channel_label',  # Fixed label for the second pipe
            #             value = Data_to_Send)
            logger.info(f"\n+++++ Django sent empty Message Channel data to dpd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}")

            response = process_xml_data(data['filePath'])
            if 'error' in response:
                # Log the error and send a specific error message to the client
                logger.error(f"\nFailed to process the XML file: {response['error']}\n")
                await self.send(text_data=json.dumps({'error': 'Failed to process the XML file'}))
                # Set to 'None' the extracted channels in the instance variable
                self.channels_values = None
            else:
                # Store the extracted channels in the instance variable
                self.channels_values = response['channels']

                # Send the successful response back to the client
                logger.info(f"\nprocess_xml_data ran successfully: {response}\n")
                await self.send(text_data=json.dumps({
                                                        'type': 'ecgData',
                                                        'severity': response['severity'],
                                                        'channels': self.channels_values,
                                                        'statements': response['statements'],
                                                    }))
                Data_to_Send = {'all_channels': self.channels_values}
                await async_send_to_pipe_channel(
                        channel_name = 'Channels_Extracted',  # Fixed channel name for the second pipe
                        label = 'All-Channels',  # Fixed label for the second pipe
                        value = Data_to_Send)
                logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}")

            # Store the current file path in the instance variable
            self.current_file_path = convert_path(html.unescape(data['filePath']))
            # Update reset condition on receiving a new file path
            self.handle_condition = False

        #______________________________________________________________________________
        elif data['type'] == 'DashDisplayWaveform':
            path_variable = convert_path(html.unescape(data['fullFilePath']))
            logger.info(f"\nDjango received \n-full file path: {path_variable} \n-and selected channel: {data['channel']}\n")

            
            # Send the User ID to Pipe
            Data_to_Send = {'User_id': self.User_name}
            await async_send_to_pipe_channel(
                        channel_name = 'User_data_channel',  # Fixed channel name for the first pipe
                        label = 'User_data_Label',  # Fixed label for the first pipe
                        value = Data_to_Send)
            logger.info(f"\n+++++ Django sent Message Channel data to dpd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}\n\tin conditional elif data['type'] == 'DashDisplayWaveform'")

            # Sending message to Pipe in DjangoDash 
            Data_to_Send = {'File-path': path_variable, 'Channel': data['channel']}
            await async_send_to_pipe_channel(
                        channel_name = 'Receive_Django_Message_Channel',  # Fixed channel name for the second pipe
                        label = 'Path_and_Channel_label',  # Fixed label for the second pipe
                        value = Data_to_Send)
            logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}")

            # Update reset condition on receiving a new file path
            self.handle_condition = True
            
        #______________________________________________________________________________
        elif data['type'] == 'Refresh_Save_Undo_Delete':
            action_var = data['Action_var']
            data_var = data['Data_var']
            logger.info(f"\nDjango received \n\t-Action_var: {action_var}\n\t-Data_var: {data_var}\n")

            if action_var in ('refresh', 'undo'):
                logger.info(f"\t\t\tConditional executed:\n\t\t\t\t\t\t-Action_var: {action_var}\n")
                # Only send data if self.handle_condition is True
                if self.handle_condition:
                    if self.count_number == 0: 
                        self.count_number += 10
                    else:
                        self.count_number = 0
                    # Sending message to Pipe in DjangoDash 
                    Data_to_Send = {'Action': action_var, 'Click_Order': self.count_number}
                    await async_send_to_pipe_channel(
                                channel_name = 'This_Action_Channel',  # Fixed channel name for the second pipe
                                label = 'This_Action',  # Fixed label for the second pipe
                                value = Data_to_Send)
                    logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}")
                    
            elif action_var == 'delete':
                logger.info(f"\t\t\tConditional executed:\n\t\t\t\t\t\t-Action_var: {action_var}\n")
                if self.handle_condition:
                    Data_to_Send = {'Action': action_var, 'Click_Order': data_var}
                    await async_send_to_pipe_channel(
                                channel_name = 'This_Action_Channel',  # Fixed channel name for the second pipe
                                label = 'This_Action',  # Fixed label for the second pipe
                                value = Data_to_Send)
                    logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}\n\tfor self.User_name = {self.User_name}")

            elif action_var in ('save', 'SaveAll'):
                logger.info(f"\t\t\tConditional executed:\n\t\t\t\t\t\t-Action_var: {action_var}\n")
                if self.current_file_path:
                    logger.info(f"\tCurrent file path: {self.current_file_path}")
                    logger.info(f"\tCurrent extracted channels: {self.channels_values}")
                    message, status = handle_annotation_to_csv(full_file_path=self.current_file_path, task_to_do=action_var)
                    await self.send(text_data=json.dumps({
                                                        'type': 'Save_Feedback',
                                                        'Message': message,
                                                        'Status': status
                                                    }))
            else:
                logger.info(f"\t\t\tThe received 'Action variable' is not valid. \n\t\t\taction_var = {action_var}\n")

        #______________________________________________________________________________
        elif data['type'] == 'labels_display_updated':
            label_status = data['updated_labels_status']
            logger.info(f"\nDjango received \n-updated_labels_status: {label_status}\n")

            # Send the updated_labels_status to DjangoDash
            await async_send_to_pipe_channel(
                        channel_name = 'Labels_status_Channel',
                        label = 'Labels_Display_Status',
                        value = label_status)
            logger.info(f"\n+++++ Django sent Message updated_labels_status data to dpd.Pipe: {label_status}\n\tfor self.User_name = {self.User_name}\n\tin conditional elif data['type'] == 'labels_display_updated'")

        #______________________________________________________________________________
        else:
            logger.error(f"\nUnknown message type received: {data['type']}\n")
            await self.send(text_data=json.dumps({'error': 'Unknown message type'}))

    async def retrieved_data(self, event):
        # This method is called when a message of type 'retrieved_data' is sent to the group
        existing_Data = event['Existing_Data']
        logger.info(f"\n+++++ Django Received Retrieved Data: \n\t\tExisting_Data: \n{existing_Data}\n\n")

        # Send the retrieved data to the client
        await self.send(text_data=json.dumps({
            'type': 'DjangoDash_retrieved_data_message',
            'Existing_Data': existing_Data,
        }))
        logger.info(f"\n----- Django sent retrieved_data to the client: \n{existing_Data}\n")

    async def form_submission(self, event):
        # This method is called when a message of type 'form_submission' is sent to the group
        annotation = event['annotation']
        click_indices = event.get('click_indices', ['Start_index', 'End_index'])  # Returns second option as default if first is missing
        item_number = event['item_number']
        segment_color = event['Color']
        logger.info(f"\n+++++ Django Received form submission: \n-annotation: {annotation} \n-click indices: {click_indices} \n-item_number: {item_number}\n-and segment_color: {segment_color}")

        # Send the annotation as a response to the client
        await self.send(text_data=json.dumps({
            'type': 'DjangoDash_message',
            'Annotation_message': annotation,
            'Click_indices': click_indices,
            'Item_number': item_number,
            'Color': segment_color,
        }))
        logger.info(f"\n----- Django sent form submission annotation, click indices and item number to the client: \n{annotation}, \n{click_indices}, \n{item_number}\n")

    async def labels_submission(self, event):
        # This method is called when a message of type 'labels_submission' is sent to the group
        labels_data = event['list_labels_display_status']
        logger.info(f"\n+++++ Django received Labels_Pipe data: \n{labels_data}\n")

        # Send a response to the client, if needed
        await self.send(text_data=json.dumps({
            'type': 'DjangoDash_labels_status',
            'Labels_data': labels_data,
        }))
        logger.info(f"\n----- Django sent Labels_Pipe data to the client: {labels_data}\n")
