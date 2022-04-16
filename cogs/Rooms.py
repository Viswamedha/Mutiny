'''

Imports

'''

from discord.ext import commands 
import os 

from core import Bot, Logger
from game import *
from game.menus import PickAnOption


'''

Logger Setup

'''


logger = Logger(__name__, os.path.basename(__file__))()


'''

Rooms Cog

'''


class Rooms(commands.Cog):
    
    def __init__(self, bot: Bot):
        self.bot: Bot = bot 


    @commands.command(name = 'spy')
    @state(States.STARTED)
    @night_only()
    @channel_specific('crows-nest')
    async def _spy(self, context: commands.Context):
        '''
        
        Used by crow's nest
        
        '''
        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        # Selecting an option
        options = [room.name for room in game.game_rooms.values() if player.energy_required(room) >= 0 and room.name != 'crows-nest'] 
        pao = PickAnOption('Which room would you like to spy on? ', options, timeout = 30)
        choice = await pao.start(context)

        if choice == None: 
            return await context.send('You didnt select a room!')

        # Saving choice
        game.today.crow_spy = game.players[context.author.id]
        game.today.crow_spy_room = game.rooms[choice]

        await context.send(f'You have selected {choice} and will receive intel when the next day starts. You many choose to pick another room by using this command again. ')


    @commands.command(name = "row")
    @state(States.STARTED)
    @night_only()
    @channel_specific('oars')
    async def _row(self, context: commands.Context):
        '''
        
        Used by Oars
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        # Editting attibute to show command has been used
        if player.good:      
            game.today.oar_rowed = True

        await context.send('You have chosen to row this night! ')


    @commands.command(name = "navigate")
    @state(States.STARTED)
    @night_only()
    @channel_specific('chart-room')
    async def _navigate(self, context: commands.Context):
        '''
        
        Used by chart room
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        # Condition to check player attibutes
        if player.captain:
            game.today.chart_captain = True
        elif player.good == False:
            game.today.chart_mutineer = True
        
        await context.send(f"It will take another {game.turns_to_shore} days to reach shore.")


    @commands.command(name = 'sleep')
    @state(States.STARTED)
    @night_only()
    async def _sleep(self, context: commands.Context):
        '''
        
        Used in any room
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        # Channel specific methods
        if context.channel.name == 'hammocks' and player.good == False:
            player += 1
        
        if player not in game.today:
            game.today.asleep.append(player)
        
        await context.send('You have chosen to sleep tonight! You are less likely to be killed by a mutineer in the night! ')


    @commands.command(name = 'steer')
    @state(States.STARTED)
    @night_only()
    @channel_specific('captains-quarters')
    async def _steer(self, context: commands.Context):
        '''
        
        Used in captains quarters
        
        '''
        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        # Checking player is the captain
        if player.captain:
            game.today.capt_captain = True 
    

    @commands.command(name = 'arm')
    @state(States.STARTED)
    @night_only()
    @channel_specific('armoury')
    async def _arm(self, context: commands.Context):
        '''
        
        Armoury
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        # Adding player to list after doing a presence check
        if player not in game.today.armed:
            game.today.armed.append(player)

        await context.send('You have chosen to arm yourself!')



def setup(bot: Bot):
    bot.add_cog(
        Rooms(
            bot
        )
    )



