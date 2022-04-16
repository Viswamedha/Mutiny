'''

Imports

'''
import asyncio
import datetime
import discord
import json 
import logging 
import os 
import sys
import uuid

from discord.ext.buttons import Paginator
from discord.ext import     commands

from .constants import BASE_DIR, LOGS_DIR


'''

Logger

'''


class Logger:

    def __init__(
        self,
        name: str,
        file: str, 
        path: str = LOGS_DIR,
        level = logging.DEBUG,
        *args,
        **kwargs
    ):
        '''
        name: __name__
        file: __file__
        level: logging.DEBUG / logging.INFO / logging.WARNING / logging.ERROR / logging.CRITICAL
        '''
        self.name = name 
        self.file = file 
        self.path = path

        self.level = level 
        
    def __call__(self) -> logging.Logger:

        # Fetching or creating a logger and setting appropriate level
        logger = logging.getLogger(self.name)
        logger.setLevel(self.level)

        # Setting up output file for logs
        if not os.path.exists(self.path):
            os.makedirs(self.path)
        file_handler = logging.FileHandler(f'{self.path}/{self.file[:-3]}.log')
        formatter    = logging.Formatter('%(asctime)s : %(levelname)s : %(name)s : %(message)s')
        file_handler.setFormatter(formatter)

        # Attaching file to logger
        logger.addHandler(file_handler)

        # Passing back logger
        return logger


'''

JSON Data Management Commands

'''


def open_or_create(name: str, default = dict(), indent = 4):
    """
    Attemps to open and read a JSON file. 
    If it doesn't exist, it creates it and fills it with the default!  
    """

    # Checking it exists...
    if os.path.exists(name):

        with open(name, 'r', encoding = 'utf-8') as file:
            data = json.load(file)
        # Loading file data and passing it back directly
        return data 
    
    # If it doesnt...
    with open(name, 'w', encoding = 'utf-8') as file:
        json.dump(default, file, indent = indent)
    # Creating new file with default and passing back default
    return default


def save(name: str, data = dict(), indent = 4):
    """
    Saves provided data to JSON file and atomically replaces it! 
    """

    # Splitting up file name with path
    file = name
    path = None
    if '/' in file:
        path = file.split('/')
        file = path.pop(len(path)-1)
        path = '/'.join(path)
    
    # Generating a unique temporary file name
    temporary_file = f'{uuid.uuid4()}-{file}.tmp'
    if path:
        temporary_file = path + '/' + temporary_file

    # Passing in data to the temporary file
    with open(temporary_file, 'w', encoding = 'utf-8') as open_file:
        json.dump(data, open_file, ensure_ascii = True, indent = indent)
    
    # Atomically moving file to save data
    os.replace(temporary_file, name)

    return data


'''

JSON Data Manager

'''


class DataStore:

    def __init__(self, file_name: str, *args, indent = 4, default = None, **kwargs):
        """
        Setting up required attributes! 
        """

        self.name = file_name 
        self.lock = asyncio.Lock()

        self.indent = indent 
        self.default = default if default else dict()

        self.loop = kwargs.pop('loop', asyncio.get_event_loop())

        # Loading in previous data from file! 
        self.load_from_file()

    """

    Synchronous functions...

    """
    
    def load_from_file(self):
        self.data = open_or_create(self.name, default = self.default, indent = self.indent)
    
    def save_to_file(self):
        save(self.name, self.data, indent = self.indent)
    
    def get_value(self, *keys): # Fetch
        data = self.data 
        for key in keys:
            try:
                data = data.get(key)
            except:
                break 
        return data

    def edit_value(self, key, value): # Edit
        try:
            self.data[key] = value
            self.save_to_file()
            return True 
        except:
            return False 
     
    def remove_key(self, key): # Delete
        try:
            data = self.data.pop(key)
            self.save_to_file()
            return data
        except:
            return False
    
    def get_keys(self):
        return list(self.data.keys())
    
    def get_values(self):
        return list(self.data.values())
    
    def get_all(self):
        return self.data
    
    def get_length(self):
        return len(self.data)

    def clear_file(self): # Flush
        self.data = self.default
        self.save_to_file()
        return self.data

    """

    Asynchronous functions...

    """

    async def load(self):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.load_from_file)
        return data
    
    async def save(self):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.save_to_file)
        return data
    
    async def get(self, *keys):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.get_value, *keys)
        return data
    
    async def edit(self, key, value):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.edit_value, key, value)
        return data

    async def remove(self, key):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.remove_key, key)
        return data
    
    async def keys(self, *args):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.get_keys)
        return data

    async def values(self, *args):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.get_values)
        return data 

    async def all(self, *args):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.get_all)
        return data 

    async def len(self, *args):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.get_length)
        return data

    async def clear(self, *args):
        async with self.lock:
            data = await self.loop.run_in_executor(None, self.clear_file)
        return data


'''

Custom Embed

'''


class Embed(discord.Embed):

    def __init__(self, title = None, description = discord.Embed.Empty, 
    timestamp = datetime.datetime.utcnow(), colour = discord.Colour.random(), **kwargs):
        changes = {
            'timestamp': timestamp,
            'description': description,
            'title': title,
            'colour': colour    
        }
        kwargs.update(**changes)
        super().__init__(**kwargs)

