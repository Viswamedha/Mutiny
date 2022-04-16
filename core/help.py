'''

Imports

'''

from discord.ext import commands 
from .core import Embed


'''

Help Command

'''


class Help(commands.HelpCommand):


    def get_command_signature(self, command: commands.Command, context: commands.Context):
        aliases = "|".join(command.aliases)
        # Providing all aliases
        partial_invoke = f"[{command.name}|{aliases}]" if command.aliases else command.name
        # Constructing command and aliases
        complete_invoke = command.qualified_name.replace(command.name, "")
        # Getting full command and removing name for groups
        signature = f"{context.prefix}{complete_invoke}{partial_invoke} {command.signature}"
        # Combining data to create signature
        return signature

    async def send_bot_help(self, mapping: dict):
        # Default command with 0 parameters
        embed = Embed(
            title = 'Help', 
            description = 'Here is my command set below! Specify a category or command after this command to get more information about each one! '
        )
        # Setting up embed
        none = mapping.pop(None, None)
        mapping = dict(sorted(mapping.items(), key = lambda c: c[0].qualified_name))
        mapping[None] = none
        for cog in mapping:
            # Fetching every cog
            commandset = ', '.join([command.name for command in mapping[cog] if not command.hidden ])
            # Retrieving all commands
            if commandset:
                # Excluding hidden cogs
                embed.add_field(
                    name = cog.qualified_name if cog else (cog or 'Miscellaneous'), 
                    value = '`' + commandset + '`',
                    inline = False
                ) 
                # Adding cog commands to embed
        channel = self.get_destination()
        # Fetching channel and sending help        
        return await channel.send(embed = embed)

    async def send_command_help(self, command):
        # Help specific for commands
        cmd = self.get_command_signature(command, self.context)
        # Signature of a specific command
        embed = Embed(title = f'Help for {command}', description = f'`{cmd}`')
        embed.add_field(name = 'Description', value = command.help)
        channel = self.get_destination()
        # Fetching channel and sending help        
        return await channel.send(embed = embed)

    async def send_group_help(self, group):
        # Specific for group help
        cmd = self.get_command_signature(group, self.context)
        # Signature of a specific group
        embed = Embed(title = f'Help for {group}', description = f'`{cmd}`')
        embed.add_field(name = 'Description', value = group.help)
        subcommands = f'`{", ".join([command.name for command in group.walk_commands() if not command.hidden])}`' if hasattr(group, "all_commands") else None
        # Adding in all subcommands
        embed.add_field(name = 'Subcommands', value = subcommands, inline = False) if subcommands else None
        channel = self.get_destination()
        # Fetching channel and sending help        
        return await channel.send(embed = embed)

    async def send_cog_help(self, cog):
        # Specific for cog help
        cogdata = self.get_bot_mapping()
        cogdata = cogdata[cog]
        # Getting cog data
        embed = Embed(title = f'Help for {cog.qualified_name if cog else cog}')
        embed.add_field(
                name = 'Commands', 
                value = '`'+', '.join([command.name for command in cogdata if not command.hidden])+'`',
                inline = False
            )
        # Listing all cog commands
        channel = self.get_destination()
        # Fetching channel and sending help        
        return await channel.send(embed = embed)

    async def on_help_command_error(self, context, error):
        # Any help commands error
        embed = Embed(
            title = 'Command / Group Not Found! ',
            description = error
        )
        return await context.send(embed = embed)

    async def command_not_found(self, string):
        # When a command does not exist
        embed = Embed(
            title = 'Command / Group Not Found! ',
            description = f'The command or category `{string}` simply does not exist! You may have mispelt the command name! '
        )
        return embed
    
    async def subcommand_not_found(self, command, string):
        # When a subcommand does not exist
        embed = Embed(
            title = 'Subcommand Not Found! ',
            description = f'The subcommand `{string}` simply does not exist! You may have mispelt the subcommand name! '
        )
        return embed

    async def send_error_message(self, error):
        # Sending generated embed on error
        channel = self.get_destination()
        return await channel.send(embed = error)

