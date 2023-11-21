import asyncio
from aiohttp import web
import ssl
import os
import sys
import json
from telebot import types
import logging
from time import time

from .util import handle_env, get_commands, get_ssl_filepaths

handle_env()

# Import logger and AlarmBot after environment vars have been prepared
from .logger import logger
from .telegram import AlarmBot, handle_event
    
async def set_bot_commands():
    """Set the latest user and admin commands on the bot"""
    logger.warn("Setting bot commands ...")
    
    user_commands = [types.BotCommand(command=command, description=description)
                     for command, description in get_commands().items()]

    # Set commands for all users
    await AlarmBot.set_my_commands(user_commands)
    
    
async def log_start(run_type: str):
    bot_info = await AlarmBot.get_me()
    logger.warn(f"{bot_info.username} {run_type} started with token {AlarmBot.token}")
                
                
# ------------------ WEBHOOK (production environment) ------------------ #

async def on_ping(data: dict):
    """
    Handles Ping events
    
    {"action": "ping"}
    """
    logger.info(f"Ping received: {data}")
    return web.Response(text="Success: Ping received!", status=200)

async def on_sensor_event(data: dict):
    """
    Handles the events from M5 stick. The M5 stick will constantly be sending these updates.
    The request paylod should be formatted like the following example:
    
    {
        "action": "sensor_event",
        "timestamp": 1700188942,
        "location": "Bedroom Door",
        "sensor_status": "OPEN" or "CLOSED"
    }
    """
    logger.info(f"M5Stick Sensor event received: {data}")
    
    # Temporary override since getting datetime on M5Stick is much more complicated
    data["timestamp"] = int(time())
    
    try:
        await handle_event(data)
        return web.Response(text="Success!", status=200)        
    except Exception as err:
        logger.error(f"An error occurred when processing the sensor event: {err}", exc_info=err)
        return web.Response(text=f"Error: {err}", status=500)        

async def handle(request):
    # Handles requests to the webhook
    try:
        request_body = await request.text()
        try:
            data = json.loads(request_body)
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from webhook request: {request_body}")
            raise
        
        # Check if the 'action' key exists and has the value 'ping' to handle uptime monitor
        if data.get('action') == 'ping':
            return await on_ping(data)
        
        # Handle the event from the M5StickCPlus contact sensor
        if data.get('action') == 'sensor_event':
            return await on_sensor_event(data)
        
        # Otherwise handle as Telegram API request
        if request.match_info.get('token') == AlarmBot.token:
            update = types.Update.de_json(request_body)
            await AlarmBot.process_new_updates([update])
            return web.Response()
        else:
            return web.Response(status=403)
    except Exception as err:
        logger.error(f"Error handling webhook request: {err}", exc_info=err)
    
async def setup_webhook():
    """Set up the webhook for the bot"""
    # Set bot commands
    await set_bot_commands()
        
    # Set webhook
    app = web.Application()
    app.router.add_post('/{token}/', handle)
    
    # Get webhook address
    webhook_host = os.getenv("WEBHOOK_HOST")
    webhook_port = os.getenv("WEBHOOK_PORT")
    webhook_listen = os.getenv("WEBHOOK_LISTEN")
    
    webhook_url_base = "https://{}:{}".format(webhook_host, webhook_port)
    webhook_url_path = "/{}/".format(AlarmBot.token)
    webhook_url_full = webhook_url_base + webhook_url_path
    
    # Get ssl certificate files
    ssl_cert, ssl_priv = get_ssl_filepaths()
    
    # Set webhook
    try:
        logger.warn(f"Setting webhook on {webhook_url_full}")
        
        await AlarmBot.remove_webhook()
        await AlarmBot.set_webhook(url=webhook_url_full, certificate=open(ssl_cert, 'r'))
        AlarmBot.webhook_url = webhook_url_full
    except Exception as e:
        logging.error(f"Failed to set up webhook: {e}")
        sys.exit(1)
    
    # Log start of bot
    await log_start(run_type="webhook")
    
    # Return the values to be processed (web.run_app cannot be started inside of async function)
    return app, webhook_listen, webhook_port, ssl_cert, ssl_priv 


if __name__ == "__main__":
    app, host, port, cert, priv = asyncio.run(setup_webhook())  # Get the app and other values

    # Build SSL context
    try:
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(cert, priv)
    except ssl.SSLError as e:
        logging.critical(f"Failed to load SSL certificates", exc_info=e)
        sys.exit(1)
    
    # Start the webhook listener
    try:
        web.run_app(app, host=host, port=port, ssl_context=context)  # Run the app here
    except Exception as err:
        logger.critical(f"An error occurred when running/attempting to run the webhook: {err}", exc_info=err)