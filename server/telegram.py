from os import getenv
from telebot.async_telebot import AsyncTeleBot
from datetime import datetime
import pytz

from .mongo import EventsMongoDB, M5StickEvent
from .util import load_command_template

# Load bot token from env and create async bot instance
# Commands are added using functional approach
AlarmBot = AsyncTeleBot(getenv("TG_BOT_TOKEN"))
AlarmBot.users = getenv("TG_USERS").split(",")
AlarmBot.webhook_url = None  # Set the webhook URL here once the service is started

# Status trackers
AlarmBot.system_status = "Disarmed" # Set initial status to disarmed
AlarmBot.sensor_status_cache = {}  # There is no initial sensor status, set once updates are received

# Instantiate MongoDB connection
Mongo = EventsMongoDB()


# ------------------- BOT COMMANDS ------------------- #

# Handle /help command
@AlarmBot.message_handler(commands=['help'])
async def on_help(message):
    bot_details = await AlarmBot.get_me()
    await AlarmBot.reply_to(message, load_command_template("help").format(bot_name=bot_details.first_name, 
                                                                          user_name=message.from_user.first_name),
                            parse_mode="Markdown")
    
# Handle /status command
@AlarmBot.message_handler(commands=['status'])
async def on_status(message):
    """Get the current status of the system, armed or disarmed"""
    emoji = "🛑🔒" if AlarmBot.system_status == "Armed" else "🟢🔓"
    await AlarmBot.reply_to(message, f"*Current System Status:*\n\n{emoji} {AlarmBot.system_status}", parse_mode="Markdown")
    
# Handle /arm command
@AlarmBot.message_handler(commands=['arm'])
async def on_arm(message):
    text = "🛑🔒 System is now *armed*. You will be alerted for any new events."
    AlarmBot.system_status = "Armed"
    await AlarmBot.reply_to(message, text, parse_mode="Markdown")
    
    
# Handle /disarm command
@AlarmBot.message_handler(commands=['disarm'])
async def on_disarm(message):
    text = "🟢🔓 System is now *disarmed*. You will no longer be alerted for new events."
    AlarmBot.system_status = "Disarmed"
    await AlarmBot.reply_to(message, text, parse_mode="Markdown")
    

# Send alerts when the system is triggered
async def handle_event(data: dict) -> None:
    last_sensor_status = AlarmBot.sensor_status_cache.get(data['location'], None)
    if data['sensor_status'] == last_sensor_status:
        # if the sensor status has not changed, do nothing
        return 
    
    # append the system status to the request data
    data["system_status"] = AlarmBot.system_status
    event = M5StickEvent(**data)
    
    # add event to mongoDB
    Mongo.add_event(event)
    
    # Prepare and send the alert if the system is armed
    if AlarmBot.system_status == "Armed":
        # Convert Unix timestamp to a datetime object and apply the CST timezone
        localized_dt = datetime.fromtimestamp(event.timestamp, 
                                              tz=pytz.timezone('US/Central'))

        # create alert text
        alert = load_command_template("alert").format(status=event.sensor_status.upper(),
                                                      datetime=localized_dt.strftime('%Y-%m-%d %I:%M %p %Z'),
                                                      location=event.location)
        
        # send the alert
        for user in AlarmBot.users:
            await AlarmBot.send_message(user, text=alert, parse_mode="Markdown")
            
    # set the last sensor status to the current one
    AlarmBot.sensor_status_cache[data['location']] = data['sensor_status']