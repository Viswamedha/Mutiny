'''

Imports

'''

from re import A
from discord.ext import commands 
import os 
import random 

from core import Bot, Logger, Embed
from game import *
from game.menus import PickAnOption, ToggleState 


'''

Logger Setup

'''


logger = Logger(__name__, os.path.basename(__file__))()


'''

Main Cog

'''


class Main(commands.Cog):


    def __init__(self, bot: Bot):
        self.bot: Bot = bot 
    
    
    @commands.command(name = 'new', aliases = ['newgame'])
    async def _newgame(self, context: commands.Context):
        '''
        
        Creating a new game if one does exist for guild and setting trigger user as owner
        
        '''

        if self.bot._games.get(context.guild.id) is not None: # Ensuring game does not exist
            return 
        
        self.bot._games[context.guild.id] = Game(self.bot, context.guild, context.channel, context.author)
        
        embed = Embed(
            title = f'Game created for {context.guild.name}', 
            description = f'A new game has been created for this server! Only one game can be created per server!\nThis channel {context.channel.mention} will be the trigger channel till the game starts! The rest of the pre-game commands must be triggered from this channel except when ending the game.\n\n{context.author.mention}, you are the host for this game and the only one who can change the game settings. '
        )
        
        await context.reply(embed = embed)


    @commands.command(name = 'set')
    @host_only()
    @state(States.CREATED)
    async def _settings(self, context: commands.Context):
        '''
        
        Changing settings of game 
        
        '''

        game: Game = self.bot._games.get(context.guild.id)


    @commands.command(name = 'open')
    @host_only()
    @state(States.CREATED)
    async def _open(self, context: commands.Context):
        '''
        
        Host can open game for players to join
        
        '''

        game: Game = self.bot._games.get(context.guild.id)

        rooms = await self.bot._roomdata.all() # Fetching JSON data
        category: discord.CategoryChannel = await context.guild.create_category('Mutiny') # All channels here
        game.game_category = category

        for room in rooms: # Generating all core rooms with 0 energy
            if rooms[room]['energy'] == 0:
                game += Room(
                    game, room, description = rooms[room]['description'], role = rooms[room]['role']
                )
                await game.rooms[room].setup_channels(ecs = rooms[room]['settings']['ecs'], ect = rooms[room]['settings']['ect'], rcs = rooms[room]['settings']['rcs'], rct = rooms[room]['settings']['rct'])

        await context.reply(f'{context.author.mention}, game is now open! Players can join the game! ')
        game.state = States.OPENED
        await context.invoke(self.bot.get_command('join')) # Automatically adding in host to game

    @commands.command(name = 'join')
    @state(States.OPENED)
    async def _join(self, context: commands.Context):
        '''
        
        Players can join game
        
        '''

        game: Game = self.bot._games.get(context.guild.id)

        game += context.author.id 
        await context.author.add_roles(game.rooms['deck'].role)

        embed = Embed(title = 'Players in Game', description = '\n'.join([f'{counter+1}) {player.user}' for counter, player in enumerate(game.players.values())]))
        embed.set_footer(text = f'Players: {len(game.players)}/{game.max_players}')
        
        await context.reply(f'{context.author.mention}, you have joined the game! Please wait till the game is started! ', embed = embed)


    @commands.command(name = 'leave')
    @state(States.OPENED)
    async def _leave(self, context: commands.Context):
        '''
        
        Players can leave game 
        
        '''

        game: Game = self.bot._games.get(context.guild.id)

        game -= context.author.id 
        await context.author.remove_roles(game.rooms['deck'].role)

        await context.reply(f'{context.author.mention}, you have left the game!')


    @commands.command()
    async def addplayers(self, context: commands.Context, members: commands.Greedy[discord.Member]):
        '''

        Shortcut to add all players

        '''
        for member in members:
            context.author = member
            await context.invoke(self.bot.get_command('join'))


    @commands.command(name = 'confirm')
    @host_only()
    @state(States.OPENED)
    @channel_specific('lobby')
    async def _confirm(self, context: commands.Context):
        '''
        
        Host can solidify players
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        if len(game.players) < MIX_PLAYERS:
            await context.reply(f'{context.author.mention}, not enough players! ')
        
        game.state = States.GENERATED

        await game.rooms['deck'].set_permissions(view = True, interact = True)
        
        await context.reply(f'{context.author.mention}, players are locked in and cannot leave, you may select the rooms for the game with the settings provided! ')


    @commands.command(name = 'setup')
    @host_only()
    @state(States.GENERATED)
    @channel_specific('lobby')
    async def _setup(self, context: commands.Context):
        '''
        
        Host can select game rooms
        
        '''
        
        game: Game = self.bot._games.get(context.guild.id)

        rooms = await self.bot._roomdata.all()
        game_rooms = [room for room in rooms if rooms[room]['energy'] != 0] # Filtering for game rooms
        game_names = [rooms[room]['name'] for room in game_rooms] # Rooms by name
        rsgm = ToggleState(context, context.channel, 'Select which rooms should be present in the game! ', game_names, defaults = [True for _ in game_names]) # True defaults
        await rsgm.start(context, wait = True)
        
        choices = rsgm.collect()
        print(choices) # Checking that rooms were selected
        if not choices:
            return await context.send('You did not select any rooms! ')
        
        # Add confirmation 
        choices = [choices[0][i] for i in range(len(choices[0])) if choices[1][i]]
        chosen = [room for room in rooms if rooms[room]['name'] in choices]
        
        for room in chosen: # Generating selected room
            game += Room(
                game, room, description = rooms[room]['description'], base_energy = rooms[room]['energy'][str(len(game.players))], max_players = rooms[room]['players'][str(len(game.players))]
            )
            await game.rooms[room].setup_channels(ecs = False, ect = False, rcs = False, rct = False)

        await context.send('Setup complete, do not run this command again! You may start the game! ')




    @commands.command(name = 'start')
    @host_only()
    @state(States.GENERATED)
    @channel_specific('lobby')
    async def _start(self, context: commands.Context):
        '''
                
        All setups complete and host can start

        '''

        game: Game = self.bot._games.get(context.guild.id)

        game.state = States.STARTED

        for player in game.players.values():
            player: Player 
            player.edit(energy = game.starting_energy, alive = True, captain = False)
        
        player_set = list(game.players.copy().values())
        for _ in range(ALIGNMENT_MAPPING[len(game.players)]['Mutineers']):
            player: Player = random.choice(player_set)
            player.good = False 
            player_set.remove(player)
        
        for player in player_set:
            player.good = True 
        
        player = random.choice(player_set)
        player.captain = True

        # Notifying players
        for player in game.players.values():
            if player.good:
                embed = Embed(title = 'Your Profile', description = 'You are the captain!' if player.captain else discord.Embed.Empty)
                embed.add_field(name = 'Alignment2', value = 'Buccaneer')
            else:
                embed = Embed(title = 'Your Profile')
                embed.add_field(name = 'Alignment2', value = 'Mutineer')
                game.rooms['mutineer-chat'] += player
                
            await player.member.send(embed = embed)
        
        await game.rooms['mutineer-chat'].set_permissions(view = True, interact = True)
        await game.rooms['mutineer-chat'].text_channel.send('Mutineers, use this channel for plotting against the buccaneers! ')

        await game.rooms['lobby'].set_permissions()

        game += Day(game, 1)
        print(game.days)
        await context.send('Starting day 1')
    

    @commands.command(name = 'choose')
    @state(States.STARTED)
    @channel_specific('deck')
    async def _choose_room(self, context: commands.Context):
        '''
        
        Allowing player to choose a room to go to
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]
        options = [room.name for room in game.game_rooms.values() if player.energy_required(room) >= 0] 
        pao = PickAnOption('Which room would you prefer to go to? ', options, timeout = 30)
        context.channel = context.author.dm_channel
        choice = await pao.start(context)
        
        if choice == None: 
            return await context.send('You didnt select a room!')

        game.today.add_choice(context.author.id, game.rooms[choice])
        
        await context.author.send(f'You have selected `{choice}`!')


    @commands.command(name = 'night')
    @state(States.STARTED)
    @channel_specific('deck')
    @night_only(night = False)
    async def _night(self, context: commands.Context):
        '''
        
        Sets mode to night after doing post-daytime checks
        
        '''
        
        game: Game = self.bot._games.get(context.guild.id)

        if len(game.days) > 1:
            day: Day = game.today
            h = day.count_votes()

            if len(h) == 0:
                await context.send('No votes!')
            elif len(h) > 1:
                # Drawn votes - no plank
                await context.send('Tied votes, no player has to walk the plank! ')
            else:

                target: Player = game.players[h[0]]
                target.alive = False 

                await context.send(f'{target.member.mention} has walked the plank! ')
                await self.game.rooms['deck'].set_permissions()
                await self.game.rooms['dj-locker'].set_permissions()

                remaining_players = [player for player in game.players.values() if player.alive]
                good_players = [player.good for player in remaining_players]
                
                if all(remaining_players):
                    await context.send('Game has ended! No mutineers present in game. ')
                    embed = Embed(title = 'Remaining Players', description = '\n'.join([player.name for player in remaining_players]))
                    await context.send(embed = embed)
                    game.state = States.ENDED
        

        # All empty rooms without choices
        rooms_to_be_set = {
            room: list()
            for room in game.game_rooms
        }
        # Adding in all the choices
        [
            rooms_to_be_set[room.name].append(user_id)
            for user_id, room in game.today.choices.items()
        ]
        # Rooms that have the perfect number of players
        finalised_rooms = {
            room: rooms_to_be_set[room]
            for room in rooms_to_be_set
            if game.rooms[room].max_players >= len(rooms_to_be_set[room])
        }
        # Rooms with an excess number of players
        rooms_to_be_set = {
            room: rooms_to_be_set[room]
            for room in rooms_to_be_set
            if room not in finalised_rooms
        }
        # Rooms with space for excess players
        free_rooms = {
            room: game.game_rooms[room].max_players - len(finalised_rooms[room])
            for room in game.game_rooms
            if room not in rooms_to_be_set and game.game_rooms[room].max_players - len(finalised_rooms[room]) > 0
        }
        # Fetching excess players
        excess_players = list()
        for room_name, user_list in rooms_to_be_set.items():
            xs = game.game_rooms[room_name].max_players - len(user_list)
            xs_players = user_list[xs:]
            excess_players += xs_players
            rooms_to_be_set[room_name] = [user_id for user_id in rooms_to_be_set[room_name] if user_id not in xs_players]
        # Adding full rooms to finalised rooms
        finalised_rooms.update(rooms_to_be_set)
        # Adding excess players to free rooms
        for user_id in excess_players:
            choices = {
                game.rooms[room]: game.players[user_id].energy_required(game.rooms[room])
                for room in free_rooms
            }
            highest_room, highest_energy = sorted(list(choices.items()),key=lambda l:l[1], reverse=True)[0]
            finalised_rooms[highest_room.name].append(user_id)
        # All players should be assigned to a room by now

        for room in game.game_rooms:
            print(game.rooms[room].players)
        for room_name, user_set in finalised_rooms.items():
            print(room_name, user_set)
            
        # print('\n')
        # game.rooms['armoury'] += list(game.players.values())[0]
        # print(game.rooms['crows-nest'].players)
        # print(hex(id(game.rooms['crows-nest'].players)))
        # print(hex(id(game.rooms['armoury'].players)))
        # return 
        # Adding players to rooms
        for room_name, user_set in finalised_rooms.items():
            for user_id in user_set:
                game.rooms[room_name] += user_id
        
        # Locking deck
        await game.rooms['deck'].set_permissions()

        await context.reply(f'{context.author.mention}, moving players to rooms. ')
        
        # Allowing access to rooms
        for room in game.game_rooms:
            await game.rooms[room].set_permissions(view = True, interact = True)

        game.night = True

        await asyncio.sleep(20)

        await game.host.send('You may use the day command to move onto the next day now!')

        await game.rooms['deck'].text_channel.set_permissions(context.author, view_channel = True, send_messages = True)
        await game.rooms['deck'].voice_channel.set_permissions(context.author, view_channel = True, connect = True, speak = True)


    @commands.command(name = 'day')
    @channel_specific('deck')
    @night_only()
    @state(States.STARTED)
    async def _day(self, context: commands.Context):
        '''
        
        Starting the next day

        '''

        game: Game = self.bot._games.get(context.guild.id)
        
        if True:
            
            # Crows nest
            if game.today.crow_spy is not None:
                players = game.today.crow_spy_room.players
                if len(players) > 0:
                    asleep = 0
                    for player in players:
                        if player in game.today.asleep:
                            asleep += 1 
                    await game.today.crow_spy.member.send(f'There were {len(players)} players and {asleep} were asleep in {game.today.crow_spy_room.name}')
                else:
                    await game.today.crow_spy.member.send(f'There was noone present in {game.today.crow_spy_room.name}')
                
            if len(game.days) >= 2:
                last_night: Day = game.days[len(game.days)]
                night_before: Day = game.days[len(game.days) - 1]

                if not last_night.oar_rowed and not night_before.oar_rowed:
                    game.moving = False 
                
                if last_night.chart_captain and night_before.chart_captain:
                    game.turns_to_shore -= 1 
                
                if last_night.chart_mutineer and night_before.chart_mutineer:
                    game.moving = False
                
                if not(last_night.capt_captain or night_before.capt_captain):
                    game.moving = False
                else:
                    game.moving = True

                if last_night.armed:
                    if random.randint(0, 1000) <= 20:
                        player: Player = random.choice(last_night.armed)
                        player += 1 
                
            
            if game.moving == False:
                await context.send('The ship has stopped moving! ')
                for player in game.players.values():
                    if player.good == False:
                        player += 1
            
            else:
                game.turns_to_shore -= 1

        game += Day(game, len(game.days) + 1)

        for room in game.game_rooms.values():
            await room.reset_channels()
        
        game.night = False

        await game.rooms['deck'].set_permissions(view = True, interact = True)
        await game.rooms['deck'].text_channel.send('Discussion phase begins! ')
        

    @commands.command(name = 'vote')
    @state(States.STARTED)
    async def _vote(self, context: commands.Context):
        '''
        
        Allowing player to choose a player to vote on
        
        '''

        game: Game = self.bot._games.get(context.guild.id)
        options = [player.user for player in game.players if player.alive]
        pao = PickAnOption('Which player would you like to vote? ', options, timeout = 30)
        context.channel = context.author.dm_channel
        choice = await pao.start(context)
        
        if choice == None: 
            return await context.send('You didnt select a choice')

        for player in game.players:
            if game.players[player].name == choice:
                selected = player

        game.today.add_choice(context.author.id, selected)
        
        await context.reply(f'You have selected `{choice}`!')
    

    @commands.command(name = 'me', help = 'Status report of the request player')
    @state(States.STARTED)
    async def _me(self, context: commands.Context):
        '''
        
        Status Report

        '''

        game: Game = self.bot._games.get(context.guild.id)
        player: Player = game.players[context.author.id]

        embed = Embed(title = f"{context.author.name}'s Profile")
        if player.captain:
            embed.description = 'You are also the captain!'
        if not player.good:
            embed.description = 'The other mutineers are: `' + ', '.join([player.name for player in game.player.values() if not player.good]) + '`'
        embed.add_field(name = 'Team', value = 'Buccaneer' if player.good else 'Mutineer')
        embed.add_field(name = 'Energy', value = f'`{player.energy}`')
        v = "\n".join(player.visits)
        embed.add_field(name = 'Visits', value = f'`{v}`')
        await context.author.send(embed = embed)

    '''
    
    Testing commands - remove for production use
    
    '''

    @commands.command()
    async def randomvotes(self, context: commands.Context):
        
        game: Game = self.bot._games.get(context.guild.id)
        for player in game.players:
            choice = random.choice([p.user_id for p in list(game.players.values()) if p.alive])
            game.today.add_vote(player, choice)
        await context.send('done')


    @commands.command()
    async def randomchoices(self, context: commands.Context):
        
        game: Game = self.bot._games.get(context.guild.id)
        for player in game.players.values():
            choice = random.choice([room.name for room in game.game_rooms.values() if player.energy_required(room) >= 0] )
            game.today.add_choice(player.user_id, game.rooms[choice])
        await context.send('done')
        

  

def setup(bot: Bot):
    bot.add_cog(
        Main(
            bot
        )
    )


