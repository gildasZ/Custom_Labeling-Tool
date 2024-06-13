
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
        logger.info("\nWebSocket connect called.\n")
        # Initialize instance variables: channels extracted from xml files, current file path, reset condition 
        # for consecutive 'undo' or 'refresh' clicks, the consecutive excution count number, and past action.
        self.channels_values = None
        self.current_file_path = None
        self.handle_condition = False
        self.count_number = 0
        self.past_action = None
        # Join the group that will receive messages from DjangoDash
        await self.channel_layer.group_add("ecg_analysis_group", self.channel_name)
        # await self.accept()
        try:
            await self.accept()
        except asyncio.CancelledError:
            await self.close(code=1001)  # Indicates that the server is shutting down

    async def disconnect(self, close_code):
        # Leave the group on disconnect
        await self.channel_layer.group_discard("ecg_analysis_group", self.channel_name)
        logger.info(f"\nWebSocket disconnect called with close code {close_code}.\n")

    async def receive(self, text_data):
        logger.info(f"\nDjango Received data through WebSocket: {text_data}.\n")
        data = json.loads(text_data)

        #______________________________________________________________________________
        if data['type'] == 'processXML':
            # Sending message to Pipe in DjangoDash ###################################
            Data_to_Send = {'File-path': None, 'Channel': None}
            await async_send_to_pipe_channel(
                        channel_name = 'Receive_Django_Message_Channel',  # Fixed channel name for the first pipe
                        label = 'Path_and_Channel_label',  # Fixed label for the first pipe
                        value = Data_to_Send)
            logger.info(f"\n+++++ Django sent empty Message Channel data to dpd.Pipe: {Data_to_Send}")

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
                        channel_name = 'Receive_Django_Message_Channel',  # Fixed channel name for the second pipe
                        label = 'All-Channels',  # Fixed label for the second pipe
                        value = Data_to_Send)
                logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}")

            # Store the current file path in the instance variable
            self.current_file_path = convert_path(html.unescape(data['filePath']))
            # Update reset condition on receiving a new file path
            self.handle_condition = False

        #______________________________________________________________________________
        elif data['type'] == 'DashDisplayWaveform':
            path_variable = convert_path(html.unescape(data['fullFilePath']))
            logger.info(f"\nDjango received \n-full file path: {path_variable} \n-and selected channel: {data['channel']}\n")

            # Sending message to Pipe in DjangoDash 
            Data_to_Send = {'File-path': path_variable, 'Channel': data['channel']}
            await async_send_to_pipe_channel(
                        channel_name = 'Receive_Django_Message_Channel',  # Fixed channel name for the second pipe
                        label = 'Path_and_Channel_label',  # Fixed label for the second pipe
                        value = Data_to_Send)
            logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}")

            # Update reset condition on receiving a new file path
            self.handle_condition = True

            if self.count_number == 1:
                # This logic handles cases where you click reset only once for a selected channel of a given file, then
                # because the received count_number by DjangoDash store_click_data callback is '0', when you click on
                # refresh for another selected channel, the count should be different from '0' to trigger the callback.
                self.count_number = 1
            else:
                # Update reset condition on receiving a new file path
                self.count_number = 0

        #______________________________________________________________________________
        elif data['type'] == 'Refresh_Save_Undo':
            action_var = data['Action_var']
            logger.info(f"\nDjango received \n\t-Action_var: {action_var}\n")

            if action_var in ('refresh', 'undo'):
                logger.info(f"\t\t\tConditional executed:\n\t\t\t\t\t\t-Action_var: {action_var}\n")
                # Only send data if self.handle_condition is True
                if self.handle_condition:
                    if self.past_action != action_var:
                        # Store the current sent action as past action
                        self.past_action = action_var
                        self.count_number = 0
                    # Sending message to Pipe in DjangoDash 
                    Data_to_Send = {'Action': action_var, 'Click_Order': self.count_number}
                    await async_send_to_pipe_channel(
                                channel_name = 'Receive_Django_Message_Channel',  # Fixed channel name for the second pipe
                                label = 'This-Action',  # Fixed label for the second pipe
                                value = Data_to_Send)
                    logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}")
                    # Increment the click count for the next consecutive click
                    self.count_number += 1

            elif action_var == 'save':
                logger.info(f"\t\t\tConditional executed:\n\t\t\t\t\t\t-Action_var: {action_var}\n")
                logger.info(f"\tCurrent file path: {self.current_file_path}")
                logger.info(f"\tCurrent extracted channels: {self.channels_values}")
                if self.current_file_path:
                    message, status = handle_annotation_to_csv(full_file_path=self.current_file_path, task_to_do='save')
                    await self.send(text_data=json.dumps({
                                                        'type': 'Save_Feedback',
                                                        'Message': message,
                                                        'Status': status
                                                    }))
                    
            elif action_var == 'SaveAll':
                logger.info(f"\t\t\tConditional executed:\n\t\t\t\t\t\t-Action_var: {action_var}\n")
                if self.current_file_path:
                    message, status = handle_annotation_to_csv(full_file_path=self.current_file_path, task_to_do='SaveAll')
                    await self.send(text_data=json.dumps({
                                                        'type': 'Save_Feedback',
                                                        'Message': message,
                                                        'Status': status
                                                    }))
            else:
                logger.info(f"\t\t\tThe received 'Action variable' is not valid. \n\t\t\taction_var = {action_var}\n")

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
        click_indices = event.get('click_indices', ['Start_index', 'End_index'])
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
