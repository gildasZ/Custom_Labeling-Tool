
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
            # Sending message to Pipe in DjangoDash #####################################################################
            Data_to_Send = {'File-path': None, 'Channel': None}
            await async_send_to_pipe_channel(
                        channel_name = 'Path_and_Channel_data_channel',  # Fixed channel name for the first pipe
                        label = 'Path_and_Channel_label',  # Fixed label for the first pipe
                        value = Data_to_Send)
            
            logger.info(f"\n+++++ Django sent empty Message Channel data to dpd.Pipe: {Data_to_Send}")

            response = process_xml_data(data['filePath'])
            if 'error' in response:
                # Log the error and send a specific error message to the client
                logger.error(f"\nFailed to process the XML file: {response['error']}\n")
                await self.send(text_data=json.dumps({'error': 'Failed to process the XML file'}))
            else:
                # Send the successful response back to the client
                logger.info(f"\nprocess_xml_data ran successfully: {response}\n")
                await self.send(text_data=json.dumps({
                                                        'type': 'ecgData',
                                                        'severity': response['severity'],
                                                        'channels': response['channels'],
                                                        'statements': response['statements'],
                                                    }))
                await async_send_to_pipe_channel(
                        channel_name = 'Channels_Extracted',  # Fixed channel name for the second pipe
                        label = 'All-Channels',  # Fixed label for the second pipe
                        value = {'all_channels': response['channels']})
        
        #______________________________________________________________________________
        elif data['type'] == 'DashDisplayWaveform':
            path_variable = convert_path(html.unescape(data['fullFilePath']))
            logger.info(f"\nDjango received \n-full file path: {path_variable} \n-and selected channel: {data['channel']}\n")

            # Sending message to Pipe in DjangoDash #####################################################################
            Data_to_Send = {'File-path': path_variable, 'Channel': data['channel']}
            await async_send_to_pipe_channel(
                        channel_name = 'Path_and_Channel_data_channel',  # Fixed channel name for the second pipe
                        label = 'Path_and_Channel_label',  # Fixed label for the second pipe
                        value = Data_to_Send)
            logger.info(f"\n+++++ Django sent Message Channel data to ppd.Pipe: {Data_to_Send}")

        #______________________________________________________________________________
        elif data['type'] == 'Refresh_Save_Undo':
            logger.info(f"\nDjango received \n\t-action_var: {data['Action_var']}\n")
            
        #______________________________________________________________________________
        else:
            logger.error(f"\nUnknown message type received: {data['type']}\n")
            await self.send(text_data=json.dumps({'error': 'Unknown message type'}))

    async def retrieved_data(self, event):
        # This method is called when a message of type 'retrieved_data' is sent to the group
        existing_Data = event['Existing_Data']
        logger.info(f"\n+++++ Django Received Retrieved Data: \n\t\tExisting_Data: {existing_Data}\n\n")

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
        logger.info(f"\n+++++ Django Received form submission: \n-annotation: {annotation} \n-click indices: {click_indices} \n-and item_number: {item_number}\n")

        # # Extract annotation data
        # annotation_data = {
        #     'Start Index': click_indices[0] if len(click_indices) > 0 else '',
        #     'End Index': click_indices[1] if len(click_indices) > 1 else '',
        #     'Label': annotation,
        #     'Color': '#FF6347'  # You can adjust this to be dynamic if needed
        # }

        # # Assuming these values are available
        # full_file_path = "full/path/to/xml/file.xml"  # Must receive it from DjangoDash
        # channels = ['Channel1', 'Channel2', 'Channel3']  # Must receive it from DjangoDash
        # selected_channel = 'Channel1'  # Must receive it from DjangoDash Or create a variable that get updated in another method
        
        # # Add annotation to CSV
        # item_number = add_annotation_to_csv(full_file_path, channels, selected_channel, annotation_data)

        # Send the annotation as a response to the client
        await self.send(text_data=json.dumps({
            'type': 'DjangoDash_message',
            'Annotation_message': annotation,
            'Click_indices': click_indices,
            'Item_number': item_number,
        }))
        logger.info(f"\n----- Django sent form submission annotation, click indices and item number to the client: \n{annotation}, \n{click_indices}, \n{item_number}\n")







        # elif data['type'] == 'formSubmission':
        #     # This block is activated by messages sent from the DjangoDash via the Channels Layer
        #     annotation = data['annotation']
        #     logger.info(f"\n+++++ Django received annotation from DjangoDash: {annotation}\n")