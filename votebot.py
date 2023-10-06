import datetime
import os
from typing import Optional

import discord
from discord.ext.commands import when_mentioned_or, CommandNotFound, has_permissions, NoPrivateMessage, Bot, \
    ExpectedClosingQuoteError

from react_decorators import *
from voting import voteDB

import asyncio

TOKEN = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.reactions = True
intents.members = True
intents.bans            = True
intents.moderation      = True
intents.message_content = True
intents.messages        = True
intents.emojis          = True

if not os.path.exists("data/temp"):
    os.makedirs("data/temp")


def get_prefix(bot, message: discord.Message):
    prefix = voteDB.getPrefix(message.guild.id if message.guild else -1)
    return when_mentioned_or(prefix)(bot, message)


bot = Bot(command_prefix=get_prefix, intents=intents)


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord')
    await resume_posting()


async def resume_posting():
    # TODO
    pass


# Prefix get/set command
@has_permissions(administrator=True)
@bot.command(name='prefix', help='Changes prefix on the server')
async def prefix(ctx, prefix: Optional[str]):
    if prefix is None:
        prefix = voteDB.getPrefix(ctx.guild.id)
        await ctx.send(f"Current prefix is `{prefix}`")
    else:
        voteDB.setPrefix(ctx.guild.id, prefix)
        await ctx.send(f"Prefix changed to `{prefix}`")


@has_permissions(administrator=True)
@bot.command(name="purge", help="Removes messages older than the given number of days. Limited to checking 100 messages per call.")
@done_react
@wait_react
async def purge(ctx: Context, days: int, limit: int = 100):
    date = ctx.message.created_at - datetime.timedelta(days=days)

    def check(m: discord.Message, deleted=[0]):
        if deleted[0] >= limit: return False
        r = m.created_at <= date
        if r: deleted[0] += 1
        return r

    print(f"Purging {limit} messages before {date}.")
    await ctx.channel.purge(limit=100, check=check)


# VC
@bot.event
async def on_voice_state_update(member, before, after):
    if not before.channel and after.channel:
        role = discord.utils.get(member.guild.roles, name="talking")
        await member.add_roles(role)
    elif before.channel and not after.channel:
        role = discord.utils.get(member.guild.roles, name="talking")
        await member.remove_roles(role)


@bot.event
async def on_error(ctx, err, *args, **kwargs):
    if err == "on_command_error":
        await args[0].send("Something went wrong")
    raise


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, CommandNotFound):
        pass
    elif isinstance(error, NoPrivateMessage):
        await ctx.send("Cannot run this command in DMs")
    elif isinstance(error, ExpectedClosingQuoteError):
        await ctx.send(f"Mismatching quotes, {str(error)}")
    elif hasattr(error, "original"):
        raise error.original
    else: raise error


# Load poll functionality
async def main():
    async with bot:
        await bot.load_extension("voting.vote_moderation_commands")
        await bot.start(TOKEN)

asyncio.run(main())
