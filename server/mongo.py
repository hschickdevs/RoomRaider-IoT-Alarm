from dataclasses import dataclass, asdict
from os import getenv
from urllib.parse import quote_plus
from dotenv import find_dotenv, load_dotenv
from pymongo import MongoClient
from bson import ObjectId

from .config import MONGODB_DATABASE, MONGODB_EVENTS_COLLECTION

@dataclass
class M5StickEvent:
    """Models the event from the M5 stick"""
    action: str  # Generic key to specify the action sent to the webhook
    timestamp: int
    location: str  # The location of the sensor (added for scalability)
    sensor_status: str  # "OPEN" or "CLOSED"
    system_status: str  # "ARMED" or "DISARMED"
    _id: ObjectId = None  # The ID of the event in the database, automatically generated
    
    def dict(self):
        return {k: str(v) for k, v in asdict(self).items()}
    

class EventsMongoDB(MongoClient):
    def __init__(self, *args, **kwargs):
        """Connector that contains all methods required to interact with the MongoDB M5Stick Event data.
            
        Warn: Loads connection values from .env or environment, make sure that these are loaded before this is instantiated.
        """
        envpath = find_dotenv(raise_error_if_not_found=True, usecwd=True)
        load_dotenv(dotenv_path=envpath)

        # Construct the connection string
        cxn_string = getenv("MONGODB_CONNECTION_STRING")

        
        super().__init__(cxn_string, *args, **kwargs)
        
        self.uri = cxn_string
        self.database = self[MONGODB_DATABASE]
        self.events = self.database[MONGODB_EVENTS_COLLECTION]
    
    # ------------------ USER METHODS ------------------ #
    
    def get_all_events(self, start: int = None, end: int = None) -> list[M5StickEvent]:
        """
        Fetches all events from the database.
        
        :param start (int): The start timestamp to filter events by.
        :param end (int): The end timestamp to filter events by.
        
        :return list[M5StickEvent]: A list of all events in the database
        """
        query = {}
        
        if start is not None or end is not None:
            timestamp_query = {}
            if start is not None:
                timestamp_query["$gte"] = start
            if end is not None:
                timestamp_query["$lte"] = end
            query["timestamp"] = timestamp_query
            
        return [M5StickEvent(**event) for event in self.events.find(query)]

    
    def add_event(self, event: M5StickEvent) -> M5StickEvent:
        """Adds a user to the MongoDB database only if a user with the same ID doesn't already exist.

        Args:
            user (User): The user to add to the database.
        """
        event_dict = event.dict()
        if "_id" in event_dict:
            del event_dict["_id"]
            
        self.events.insert_one(event_dict)
        
        # Find the event that was just added and load it with the ID
        return M5StickEvent(**self.events.find_one(event_dict))

    # ------------------ CLASS METHODS ------------------ #

    def ping(self, show_cxn: bool = False):
        print(self.admin.command('ping'))
        if show_cxn:
            print(f"You successfully connected to MongoDB at {self.uri}!")
        
    def close(self):
        self.close()
        print(f"Closed connection to MongoDB at {self.uri}.")