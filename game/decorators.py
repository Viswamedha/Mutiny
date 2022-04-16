'''

Imports

'''

from discord.ext import commands 
from core import *



'''

Decorators

'''



def host_only():
    # To only allow host of game
    def decorator(function):
        async def wrapper(self, context: commands.Context, *args, **kwargs):
            if (game:=context.bot._games.get(context.guild.id)) is not None:
                if game.host == context.author:
                    return await function(self, context, *args, **kwargs)
            return False 
        return wrapper 
    return decorator


def state(state: str, inverse: bool = False):
    # Checking if a state is the current state of the game for a command to run
    # Inverse switches the condition
    def decorator(function):
        async def wrapper(self, context: commands.Context, *args, **kwargs):
            if (game:=context.bot._games.get(context.guild.id)) is not None:
                if (game.state == state) == (not inverse):
                    return await function(self, context, *args, **kwargs)
            return False 
        return wrapper 
    return decorator


def channel_specific(name: str):
    # Command can only run in the channel specified
    def decorator(function):
        async def wrapper(self, context: commands.Context, *args, **kwargs):
            if context.channel.name == name:
                return await function(self, context, *args, **kwargs)
            return False 
        return wrapper 
    return decorator


def night_only(night: bool = True):
    # Command can only run when game is in the night phase
    def decorator(function):
        async def wrapper(self, context: commands.Context, *args, **kwargs):
            if (game:=context.bot._games.get(context.guild.id)) is not None:
                if game.night == night:
                    return await function(self, context, *args, **kwargs)
            return False 
        return wrapper 
    return decorator


