'''

Imports

'''

import discord 
import os
from discord.ext import commands 

from .core import Logger, DataStore
from .help import Help
from .constants import COGS_DIR, DATA_DIR, INVITE, PREFIXES, TOKEN


'''

Logger Setup

'''

  
logger = Logger(__name__, os.path.basename(__file__))()


'''

Prefix Callable

'''


def get_prefix(bot, message):
    """
    Adding in hardcoded prefix defaults from .env with inbuilt defaults! 
    Also adding in guild specific prefixes! 
    """

    # Adding in bot mention prefixes (in case a user forgets any of the other prefixes)
    prefixes = PREFIXES + [f'<@!{bot.user.id}> ', f'<@{bot.user.id}> ', f'<@!{bot.user.id}>', f'<@{bot.user.id}>']
    
    # Checking if message is from a guild
    if message.guild:
        # Synchronous request for data due to being in a function! 
        prefixes += bot._prefixes.get_value(str(message.guild.id)) or list()

    return prefixes


'''

Discord Bot

'''


class Bot(commands.Bot):

    def __init__(self, **options):
        """
        Initialising bot with state variables and setting attributes
        """

        # Checking if TOKEN is provided in .env 

        if not TOKEN:
            raise OSError('TOKEN is not set in .env! ')
        

        # Super classing default setup for the following settings: prefixes, case sensitivity, timeout, intents and adding in help command

        super().__init__(
            command_prefix = get_prefix,
            case_insensitive = True, # Makes all commands case insensitive to make it easier for users. 
            heartbeat_timeout = 150.0, # Setting a longer timeout for the longer commands before socket closes.
            intents = discord.Intents.all(),  # Allowing bot to access all data it may need! 
            help_command = Help(), # Custom help commands with desired styling  
            **options
        )

        # Hardcoding relevant runtime constants

        self.token = TOKEN
        self.invite_url = INVITE

        # All JSON Managers below
        
        self._prefixes = DataStore(f'{DATA_DIR}/prefixes.json')
        self._settings = DataStore(f'{DATA_DIR}/settings.json')
        self._roomdata = DataStore(f'{DATA_DIR}/roomdata.json')

        self._games = dict()

        # Adding in bot logger

        self._logger = logger

        
    def run(self, *args, **kwargs):
        """
        Overriding run method to handle token within class. 
        Also adds all cogs before launch! 
        """
        # Checking whether COGS_DIR was passed in accurately
        if os.path.exists(f'{COGS_DIR}'):
            folder = COGS_DIR.split('\\')[::-1][0]
            for cog in os.listdir(COGS_DIR):
                # Verifying that it is a python file
                if cog.endswith('.py'):
                    # Stripping the ".py" part and loading cog
                    self.load_extension(f'{folder}.{cog[:-3]}')

        else: 
            logger.critical('Cog Dir Path Does Not Exist')
        
        return super().run(self.token, *args, **kwargs)


    async def on_ready(self):
        """
        On ready event to indicate a connection has been succesfully made. 
        """
        print(f'{self.user.name} is online! ')
        logger.info(f'{self.user.name} is online! ')

    async def on_command_error(self, context, exception):
        """
        Catching all errors and logging them directly!         
        """
        print(exception)
        logger.error(exception)
        return await super().on_command_error(context, exception)