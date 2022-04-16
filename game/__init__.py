'''

Imports

'''


import discord 
from discord.ext import commands 
import random 
from core import *
from .settings import * 
from .decorators import *
# Enum

'''

Player Object

'''



class Player:


    def __init__(
        self,
        game,
        user_id: int,
        energy: int = 0,
        good: bool = None,
        captain: bool = None,
        alive: bool = None, 
        visits: list = list(),
        *args,
        **kwargs
    ) -> None:
        self.game = game 
        self.user_id: int = user_id  
        self.user: discord.User = self.game.bot.get_user(user_id)
        self.member: discord.Member = self.game.guild.get_member(user_id)
        self.energy: int = energy
        self.good: bool = good 
        self.captain: bool = captain 
        self.alive: bool = alive 
        self.visits: list = visits


    def __repr__(self):
        '''
        
        Representation of class

        '''
        return f'<{self.__class__.__name__} ID={self.user_id} User={self.user.name}#{self.user.discriminator} Energy={self.energy} Good={self.good} Captain={self.captain} Alive={self.alive}>'
    

    def __add__(self, energy: int):
        '''
        
        Giving player more energy
        
        '''
        self.energy += energy 
        return True 


    def __iadd__(self, energy: int):
        '''
        
        Giving player more energy 
        
        '''
        self.energy += energy 
        return self 
    

    def __sub__(self, energy: int):
        '''
        
        Taking player energy
        
        '''
        if energy <= self.energy:
            self.energy -= energy 
            return True 
        return False 
    

    def __isub__(self, energy: int):
        '''
        
        Taking player energy
        
        '''
        if energy <= self.energy:
            self.energy -= energy 
        return self 


    def edit(self, energy: int = 0, good: bool = None, captain: bool = None, alive: bool = None, visits: list = list()) -> None:
        '''
        
        Setting values for alignment and game
        
        '''
        # Using defaults when needed
        self.energy = energy or self.energy
        self.good = self.good if good is None else good 
        self.captain = self.captain if captain is None else captain 
        self.alive = self.alive if alive is None else alive 
        self.visits = self.visits if not visits else visits 


    def energy_required(self, room) -> int:
        '''
        
        Energy to visit a specific room
        
        '''
        if not self.visits:
            return self.energy - room.base_energy
        last_visit = self.visits[len(self.visits) - 1]
        if last_visit != room.name:
            return self.energy - room.base_energy
            # When the room is not present consequtively
        visit_counter: int = 0 
        for room_name in self.visits[::-1]:
            # Matching consequetive visits
            if room_name == last_visit:
                visit_counter += 1
            else:
                break 
        # Energy left after attempting to go to room
        return self.energy - (room.base_energy + visit_counter)





''' 

Room Object

'''


class Room:

    '''
    
    Base energy of 0 means it is a core room using roles
    Max players takes no effect when base energy is 0
    
    
    '''
    
    def __init__(
        self,
        game, 
        name: str, 
        description: str = None,
        role: discord.Role = None, 
        base_energy: int = 0,
        max_players: int = 20,
        players: list = None,
        category_channel: discord.CategoryChannel = None,
        text_channel: discord.TextChannel = None,
        voice_channel: discord.VoiceChannel = None,
    ) -> None:
        self.game = game 
        self.name: str = name 
        self.description: str = description
        self.role: discord.Role = role 
        self.base_energy: int = base_energy
        self.max_players: int = max_players
        self.players: list = players if players else list() 
        self.category_channel: discord.CategoryChannel = category_channel
        self.text_channel: discord.TextChannel = text_channel
        self.voice_channel: discord.VoiceChannel = voice_channel

    
    def __repr__(self):
        '''
        
        Representation of class

        '''
        return f'<{self.__class__.__name__} Name={self.name} Energy={self.base_energy} Limit={self.max_players}>'


    def __add__(self, player: Player):
        '''
        
        Adding player to room 

        '''
        if isinstance(player, int):
            player = self.game.players.get(player, None)
            if player is None:
                return False
        if (player not in self.players) and player.energy_required(self):
            self.players.append(player)
            player -= self.base_energy
            player.visits.append(self.name)
            return True 
        return False 
    

    def __iadd__(self, player: Player):
        '''
        
        Adding player to room 

        '''
        if isinstance(player, int):
            player = self.game.players.get(player, None)
            if player is None:
                return self
        if (player not in self.players) and player.energy_required(self):
            self.players.append(player)
            player -= self.base_energy
            player.visits.append(self.name)
        return self

    
    def __sub__(self, player: Player):
        '''
        
        Removing player from room
        
        '''
        if isinstance(player, int):
            player = self.game.players.get(player, None)
            if player is None:
                return False
        if player in self.players:
            self.players.remove(player)
            return True 
        return False 
    

    def __isub__(self, player: Player):
        '''
        
        Removing player from room
        
        '''
        if isinstance(player, int):
            player = self.game.players.get(player, None)
            if player is None:
                return self
        if player in self.players:
            self.players.remove(player)
        return self 


    @property
    def space_left(self):
        '''
        
        Is there space for more players?
        
        '''
        return len(self.players) < self.max_players


    async def setup_channels(self, ecs: bool = False, ect: bool = False, rcs: bool = True, rct: bool = True):
        '''
        
        Creating all channels and roles based on type of room
        
        '''
        # Generating channels
        self.text_channel = await self.game.guild.create_text_channel(self.name, category = self.game.game_category)
        self.voice_channel = await self.game.guild.create_voice_channel(self.name, category = self.game.game_category)
        self.category_channel = self.game.game_category
        # Setting default permissions
        await self.text_channel.set_permissions(self.game.guild.default_role, view_channel = ecs, send_messages = ect)
        await self.voice_channel.set_permissions(self.game.guild.default_role, view_channel = ecs, connect = ect, speak = ect)
        if self.role is not None:
            if isinstance(self.role, str):
                # Type check to ensure that role does not get recreated
                if (role := discord.utils.get(self.game.guild.roles, name = self.role)) is None:
                    # Role being fetched and set using a walrus operator
                    role = await self.game.guild.create_role(name = self.role, colour = discord.Color.random())
                    # Generating a new role with a random colour
                self.role = role
            # Setting role specific permissions
            await self.text_channel.set_permissions(self.role, view_channel = rcs, send_messages = rct)
            await self.voice_channel.set_permissions(self.role, view_channel = rcs, connect = rct, speak = rct)


    async def set_permissions(self, view: bool = False, interact: bool = False, move: bool = True):
        '''
        
        Changing users to interact in the room
        
        '''

        if self.role is not None:
            # Setting permissions for role specified
            await self.text_channel.set_permissions(self.role, view_channel = view, send_messages = interact)
            await self.voice_channel.set_permissions(self.role, view_channel = view, connect = interact, speak = interact)
            if move:
                if interact:
                    # Moving users from their present voice channel to this one
                    [
                        await member.move_to(self.voice_channel) 
                        for member in self.role.members
                        if member.voice 
                    ]
                else:
                    # Disconnecting users from their voice channels
                    [
                        await member.move_to(None) 
                        for member in self.role.members
                        if member.voice 
                    ]

            return 
        # Setting permissions manually per user
        for player in self.players:
            await self.text_channel.set_permissions(player.member, view_channel = view, send_messages = interact)
            await self.voice_channel.set_permissions(player.member, view_channel = view, connect = interact, speak = interact)


    async def reset_channels(self, ecs: bool = False, ect: bool = False, rcs: bool = True, rct: bool = True):
        '''
        
        Resetting perms for channel
        
        '''
        # Attempting to delete channels
        try:
            await self.text_channel.delete()
        except:
            pass
        try:
            await self.voice_channel.delete()
        except:
            pass
        # Recreating the channels
        await self.setup_channels(ecs = ecs, ect = ect, rcs = rcs, rct = rct)


    

'''

Day Object

'''

class Day:

    
    def __init__(
        self,
        game,
        day: int,

    ):
        self.game = game 
        self.day: int = day 
        self.choices: dict = dict()
        self.votes: dict = dict()
        
        # Day specifics for rooms 
        self.crow_spy: Player = None
        self.crow_spy_room: Room = None

        self.oar_rowed: bool = False

        self.chart_captain: bool = False 
        self.chart_mutineer: bool = False

        self.capt_captain: bool = False 

        self.armed: list = list()

        self.asleep: list = list()



    def add_choice(self, user_id: int, room: Room):
        '''
        
        User can choose a room
        
        '''
        self.choices[user_id] = room 
    

    # def verify_choices(self):
    #     '''
        
    #     Provide all rooms without conflicts and reassign extras to rooms with space and energy
        
    #     '''
    #     room_choices: dict = {
    #         game_room: list()
    #         for game_room in self.game.game_rooms
    #     }
    #     [room_choices[room.name].append(self.game.players[player_id]) for player_id, room in self.choices.items()]









        # REDO THIS
        # room_choices: dict = {
        #     game_room: list()
        #     for game_room in self.game.game_rooms
        # }
        # [room_choices[room.name].append(self.game.players[player_id]) for player_id, room in self.choices.items()]

        # assigned: dict = {
        #     game_room: player_set
        #     for game_room, player_set in room_choices.items()
        #     if self.game.rooms[game_room].max_players >= len(player_set)
        # }

        # unassigned: dict = {
        #     game_room: player_set
        #     for game_room, player_set in room_choices.items()
        #     if game_room not in assigned
        # }

        # removed = list()
        # for game_room, player_set in unassigned.items():
        #     extras: int = self.game.rooms[game_room].max_players - len(player_set)
        #     for _ in range(extras):
        #         choice = random.choice(player_set)
        #         player_set.remove(choice)
            
        # available = [game_room for game_room in self.game.game_rooms if self.game.rooms[game_room].space_left]
        # random.shuffle(available)

        # for game_room in available:
        #     spaces: int = self.game.rooms[game_room] - len(self.game.rooms[game_room].players)
        #     unassigned[game_room] 
        #     if spaces < len(removed):
        #         for _ in range(spaces):
        #             extra = random.choice(removed)
        #             removed.remove(extra)
        #     if removed:
        #         while self.game.rooms[game_room].space_left:
        #             self.game.rooms[game_room] += removed.pop(0)
                

    

    def fill_choices(self):
        '''
        
        Random choice for users who have not updated their choice
        
        '''
        for user_id, player in self.game.players.items():
            if user_id not in self.choices:
                # Adding in a random choice from available choices to the player
                choice = random.choice([room.name for room in self.game.game_rooms.values() if player.energy_required(room) >= 0] )
                self.add_choice(player, self.game.rooms[choice])


    
    def add_vote(self, user_id: int, target_id: int):
        '''
        
        Votes for all users
        
        '''
        self.votes[user_id] = target_id


    def count_votes(self):
        '''
        
        Getting all players with the higest votes
        
        '''

        # Counting votes here
        votes: dict = dict()

        if not votes:
            return list()

        for voter, target in self.votes.items():
            votes[target] = 1 + votes.get(target, 0)
            
            # Captain - double votes
            if self.game.players[voter].captain:
                votes[target] += 1
        
        # Player(s) with highest votes
        highest_vote = max(list(votes.values()))
        highest_voted = list()
        for voted, count in votes.items():
            if count == highest_vote:
                highest_voted.append(voted)
        
        return [self.game.players.get(player_id) for player_id in highest_voted]





    # Assume all players select a room



'''

Game Object

'''



class Game:

    '''
    Game object for holding state data
    
    State Mechanisms
    ---------------
    Created - Game initialised and set up of unlinked settings      - OPEN
    Open - Players can join - CONFIRM
    Generating - Setting up rooms and permissions - START
    Started - Going through days - done via in game win conditions
    Ended - Game over and awaiting deletion 
    
    
    '''


    def __init__(
        self,
        bot: Bot,
        guild: discord.Guild,
        channel: discord.TextChannel,
        host: discord.Member,
        state: str = States.CREATED,
        max_players: int = MAX_PLAYERS,
        starting_energy: int = STARTING_ENERGY,

        ) -> None:

        self.bot: Bot = bot
        self.guild: discord.Guild = guild
        self.channel: discord.TextChannel = channel 
        self.host: discord.Member = host 
        self.state: str = state

        self.rooms: dict = dict()
        self.days: dict = dict()
        self.players: dict = dict()
        
        self.max_players: int = max_players
        self.starting_energy: int = starting_energy
        self.game_category: discord.CategoryChannel = None 

        self._game_rooms: dict = dict()

        self.night: bool = False
        self.turns_to_shore: int = 5
        self.moving: bool = True


    def __repr__(self):
        '''
        
        Representation of class
        
        '''
        return f'<{self.__class__.__name__} Guild={self.guild} Host={self.host} State={self.state}>'


    def __add__(self, obj):
        '''
        
        Adding other objects to game
        
        '''
        if isinstance(obj, int):
            self.players[obj] = Player(self, user_id = obj)
        elif isinstance(obj, Player):
            self.players[obj.user_id] = obj 
        elif isinstance(obj, Room):
            self.rooms[obj.name] = obj 
        elif isinstance(obj, Day):
            self.days[obj.day] = obj
        return True


    def __iadd__(self, obj):
        '''
        
        Adding other objects to game
        
        '''
        if isinstance(obj, int):
            self.players[obj] = Player(self, user_id = obj)
        elif isinstance(obj, Player):
            self.players[obj.user_id] = obj 
        elif isinstance(obj, Room):
            self.rooms[obj.name] = obj 
        elif isinstance(obj, Day):
            self.days[obj.day] = obj 
        return self 
    

    def __sub__(self, obj):
        '''
        
        Removing other objects from game
        
        '''
        if isinstance(obj, int):
            return self.players.pop(obj, None)
        elif isinstance(obj, Player):
            return self.players.pop(obj.user_id, None)
        elif isinstance(obj, Room):
            return self.rooms.pop(obj.name, None) 
        elif isinstance(obj, Day):
            return self.rooms.pop(obj.day, None)
    

    def __isub__(self, obj):
        '''
        
        Removing other objects from game
        
        '''
        if isinstance(obj, int):
            self.players.pop(obj, None)
        elif isinstance(obj, Player):
            self.players.pop(obj.user_id, None)
        elif isinstance(obj, Room):
            self.rooms.pop(obj.name, None) 
        elif isinstance(obj, Day):
            self.rooms.pop(obj.day, None)
        return self 
    

    @property
    def today(self) -> Day:
        '''
        
        Latest day
        
        '''
        return self.days[len(self.days)] if len(self.days) > 0 else None


    @property
    def game_rooms(self):
        '''
        
        Game rooms
        
        '''
        if not self._game_rooms:
            # Checking if the attibute is set so that processing time isn't wasted on recalculating game rooms each time
            self._game_rooms = {
                room: self.rooms[room] 
                for room in self.rooms 
                if self.rooms[room].base_energy > 0
            }
            # Filtering 
        return self._game_rooms


    @property
    def space_left(self):
        '''
        
        Is there space for more players?
        
        '''
        return len(self.players) < self.max_players
