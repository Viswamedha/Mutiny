'''

Imports

'''

import asyncio
from discord.ext import commands, menus
import discord 
from core import Embed


'''

Toggle State Menu

'''

TOGGLES = {
    True : '✔️',
    False: '❌',
    '❌': False,
    '✔️': True,
}




class ToggleState(menus.Menu):

    def __init__(
        self, 
        context: commands.Context,
        channel: discord.TextChannel,

        content: str,
        options: list,
        defaults: list = list(),
        timeout: int = 30.0,

        *args, 
        **kwargs
    ):
        self.context = context
        self.channel = channel
        self.content = content

        self.options = options 
        self.selected = options[0]

        # Setting up default states for all options if not specified
        if not defaults:
            defaults = [
                False for _ in options
            ]
        self.defaults = [
            TOGGLES[_] for _ in defaults
        ]
        
        super().__init__(
            timeout = timeout,
            delete_message_after = True,
            clear_reactions_after = True
        )
    
    
    async def send_initial_message(self, context: commands.Context, channel: discord.TextChannel):
        return await self.channel.send(embed = self.get_embed())
    

    def get_embed(self):
        # Generating embed with all options present
        embed = Embed(
            title = self.content,
            description = '```' + '\n'.join(
                [
                    f'{option} : {self.defaults[count]}' for count, option in enumerate(self.options)
                ]
            ) + '```'
        )
        # Highlights the current selection
        embed.add_field(
            name = 'Selected',
            value = self.selected
        )

        return embed 

    async def update_message(self):
        # Updating old embed data with the new embed
        await self.message.edit(embed = self.get_embed()) 


    @menus.button('☝️')
    async def up(self, payload):
        current_count = self.options.index(self.selected)
        # Getting item above or bottom item if current item is the top one
        new_count = (len(self.options) - 1) if (current_count == 0) else (current_count - 1)
        self.selected = self.options[new_count]
        await self.update_message()
    
    @menus.button('👇')
    async def down(self, payload):
        current_count = self.options.index(self.selected)
        # Getting item below or top item if current item is the bottom one
        new_count = 0 if (current_count == len(self.options) - 1) else (current_count + 1)
        self.selected = self.options[new_count]
        await self.update_message()


    @menus.button('🔄')
    async def stoggle(self, payload):
        # Switches the state of the item with the dictionary present
        self.defaults[self.options.index(self.selected)] = TOGGLES[False] if self.defaults[self.options.index(self.selected)] == TOGGLES[True] else TOGGLES[True]
        await self.update_message()
        
    @menus.button('✔️')
    async def confirm(self, payload):
        # Deletes menu and stops event listeners
        self.stop()
        await self.message.delete()
    
    def collect(self):
        # Passing back final toggle state data
        return self.options, [TOGGLES[_] for _ in self.defaults]


'''

Confirm Menu

'''


class ConfirmMenu(menus.Menu):

    def __init__(self, message, timeout_error_message):
        super().__init__(timeout=20.0, delete_message_after=True)
        # Clearing message after menu stops
        self.timeout_error_message = timeout_error_message
        self.msg = message
        self.result = False


    async def send_initial_message(self, context, channel):
        self.channel = channel
        return await channel.send(self.msg)

    @menus.button('👍')
    async def yes(self, payload):
        self.result = True
        self.stop()

    @menus.button('👎')
    async def no(self, payload):
        self.result = False
        self.stop()

    async def prompt(self, context):
        await self.start(context, wait=True)
        # Attempting to delete if the menu does not get a response
        try:
            await self.message.delete()
        except:
            pass
        return self.result

    async def finalize(self, timed_out):
        if timed_out:
            await self.channel.send(self.timeout_error_message, delete_after = 10)
            # Producing an error if the user does not pick an option
        return await super().finalize(timed_out)



'''

Pick An Option Menu

'''


CHOICES = [
    '1️⃣',
    '2️⃣',
    '3️⃣',
    '4️⃣',
    '5️⃣',
    '6️⃣',
    '7️⃣',
    '8️⃣',
    '9️⃣'
]



class PickAnOption:

    def __init__(self, message: str, options: list, timeout = 20.0):
        self.message_content = message 
        self.options = {
            CHOICES[counter]: value
            for counter, value in enumerate(options)
        }
        self.timeout = timeout
    
    async def start(self, context: commands.Context):
        embed = Embed(
            title = self.message_content,
            description = '\n'.join(
                [
                    f'{key} : {value}'
                    for key, value in self.options.items()
                ]
            )
        )
        # Generating embed as needed
        self.message: discord.Message = await context.send(embed = embed)
        for reaction in self.options.keys():
            await self.message.add_reaction(reaction)
        # Adding in as many reactions as needed
    
        def check(reaction, user):
            return user == context.author and str(reaction.emoji) in self.options
        # Callable for the conditions required to end the menu
        try:
            reaction, user = await context.bot.wait_for('reaction_add', timeout = self.timeout, check=check)
            # Async event loop
        except asyncio.TimeoutError:
            choice = None
        else:
            choice = self.options[str(reaction)]
        finally:
            await self.message.delete()
            return choice 
        
