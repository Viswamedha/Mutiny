'''

Imports

'''

import discord 
import logging 
import os
from discord.ext import commands 
from core import Bot, COGS_DIR, Logger

'''

Logger Setup

'''


logger = Logger(__name__, os.path.basename(__file__))()


'''

Owner Cog - All commands within are hidden from help menu

'''

class Owner(commands.Cog, command_attrs = dict(hidden = True)):
    # All commands are hidden from the menu


    def __init__(self, bot: Bot, logger: logging.Logger = None):
        '''

        Setting up reference attribute to bot client object... 
        
        '''
        self.bot = bot

            

    async def cog_check(self, context):
        '''

        Initial check for every command in this cog...

        '''
        return await self.bot.is_owner(context.message.author) # Checking that the command was triggered by the owner, i.e. me :)

        # Only allows commands in this cog to be run if a True is returned! 



    '''
    
    Helper methods

    '''


    def reload_or_load_extension(self, module):
        '''

        Attempts to reload a cog if its already loaded! 

        '''
        try:
            self.bot.reload_extension(f'cogs.{module}')
        except commands.ExtensionNotLoaded:
            self.bot.load_extension(f'cogs.{module}')


    '''
    
    Owner Commands
    
    '''


    @commands.command()
    async def deletecategory(self, context: commands.Context, id: int):
        '''
        
        Deleting a category with all channels in it! 
        
        '''
        c = discord.utils.get(context.guild.categories, id = id)
        for i in c.channels:
            await i.delete()
        await c.delete()


    @commands.command()
    async def deleteallfreechannels(self, context: commands.Context):
        '''
        
        Deleteing every text and voice channel that isnt assigned to a category! 
        
        '''
        for channel in context.guild.text_channels:
            if not channel.category:
                await channel.delete()
        for channel in context.guild.voice_channels:
            if not channel.category:
                await channel.delete()
        await context.send('\N{OK HAND SIGN}')


    @commands.command()
    async def deleteeverythingelse(self, context: commands.Context):
        '''
        
        Deletes everything except the context category and its channels
        
        '''
        for category in context.guild.categories:
            if category != context.channel.category:
                for i in category.channels:
                    await i.delete()
                await category.delete()
        await context.send('\N{OK HAND SIGN}')


    @commands.command()
    async def deleteallroles(self, context: commands.Context):
        '''
        
        Deletes all roles
        
        '''
        for role in context.guild.roles:
            try:
                await role.delete()
            except:
                pass 
        await context.send('\N{OK HAND SIGN}')


    @commands.command(name = 'load')
    async def _load(self, context: commands.Context, *, module: str):
        '''

        Loads a specified cog

        '''
        try:
            async with context.typing(): # Indicating the bot is actually processing the request
                self.reload_or_load_extension(module)
        except commands.ExtensionError as e:
            await context.send(f'{e.__class__.__name__}: {e}')
        else:
            await context.send('\N{OK HAND SIGN}')


    @commands.command(name = 'unload')
    async def _unload(self, context: commands.Context, *, module: str):
        '''

        Unloads a specified cog

        '''
        try:
            async with context.typing(): # Indicating the bot is actually processing the request
                self.bot.unload_extension(module)
        except commands.ExtensionError as e:
            await context.send(f'{e.__class__.__name__}: {e}')
        else:
            await context.send('\N{OK HAND SIGN}')
    

    @commands.group(name = 'reload', invoke_without_command = True)
    async def _reload(self, context: commands.Context, *, module: str):
        '''

        Reloads a specified cog unless the subcommand is used

        '''
        try:
            async with context.typing():
                self.reload_or_load_extension(module)
        except commands.ExtensionError as e:
            await context.send(f'{e.__class__.__name__}: {e}')
        else:
            await context.send('\N{OK HAND SIGN}')

    @_reload.command(name = 'all')
    async def _reload_all(self, context: commands.Context):
        '''

        Reloads all cogs present

        '''
        try:
            async with context.typing():
                for cog in os.listdir(f'./cogs'):
                    # Fetching all cogs from the directory
                    if cog.endswith('.py'):
                        self.reload_or_load_extension(f'{cog[:-3]}')
        except commands.ExtensionError as e:
            await context.send(f'{e.__class__.__name__}: {e}')
        else:
            await context.send('\N{OK HAND SIGN}')


    @commands.command(name = 'shutdown', aliases = ['sd'])
    async def _shutdown(self, context: commands.Context):
        '''
        
        Stopping bot process and closing connection
        
        '''
        await context.send(':wave:')
        await self.bot.close()


def setup(bot: Bot):
    bot.add_cog(
        Owner(
            bot
        )
    )