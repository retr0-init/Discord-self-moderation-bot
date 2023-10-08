import discord
from discord.ext import commands
from discord.ext.commands import Bot, has_permissions

from voting import voteDB
from react_decorators import *
from voting.symbols import symbols
from voting.parsers import *


# Main poll class, mainly a wrapper around Vote
from voting.vote_manager import VoteManager

import asyncio
import numpy as np
import re
import datetime

timeConst = 24 * 7 * (1 - np.exp(-1))
pattern = re.compile(r"\b[0-9]*\.[0-9]+[hdw]\b")
pattern1 = re.compile(r"\b[0-9]*[hdw]\b")
pollTimeUnban = 3600

class VoteModerate(commands.Cog):
    bot: Bot

    def __init__(self, bot):
        self.bot = bot
        self.vm = VoteManager(bot)


    @commands.command(name="createban", aliases=["ban", "moderate"], help=poll_parser.format_help())
    @commands.guild_only()
    @wait_react
    async def create_ban_poll(self, ctx: Context, user_to_ban: discord.Member, time_to_ban: str):
        '''
        Create a timeout of the user. The time can be specified in hour (h), day (d) or week (w).
        The time must be integer and there is no space between the timer value and the unit. e.g.
        +ban @user 3d
        The length of the poll will be determined by the timeout period. The longer the timeout is,
         the longer the poll length will be.
        '''
        try:
            if user_to_ban.is_timed_out():
                await ctx.send("This user has already been banned!")
            else:
                print("Parsing args")

                options = [f"Are we going to ban user {user_to_ban.display_name} for {time_to_ban}?", "Yes", "No"]

                def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                    if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                    if args.winners <= 0: raise argparse.ArgumentError(win_arg, f"Cannot select less than 1 winner.")
                    if args.limit < 0: raise argparse.ArgumentError(lim_arg, f"Cannot have limit less than 1.")
                    for op in args.options:
                        if len(op) > 50: raise argparse.ArgumentError(opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

                args = run_parser(poll_parser, options, extra_checks)
                # Send feedback or run vote
                idl = []
                flag, timeBan = self.parseTimeout(ctx, time_to_ban)
                if not flag:
                    await ctx.send("""Timeout value format error. The examples are like below:
                    +ban @user 3h
                    +ban @user 1d
                    +ban @user 1w""")
                elif timeBan <= 0:
                    await ctx.send("Timeout value should be greater than 0!")
                else:
                    pollPeriod = self.calcPollPeriod(timeBan)
                    print(f"{pollPeriod} minutes")
                    if isinstance(args, str): await ctx.send(args)
                    else:
                        await self.vm.std_moderate_vote(ctx, args, user_to_ban.mention, idl=idl, pollTime=pollPeriod)

                    await asyncio.sleep(int(pollPeriod * 60))
                    await self.close_poll(ctx, idl[0])

                    if await self.isProgress(ctx, 1, 0):
                        await ctx.send(f"Decision: Timeout {user_to_ban.mention} for {time_to_ban}.")
                        await user_to_ban.timeout(datetime.timedelta(hours=timeBan), reason=f"Vote to moderate. Raised by {ctx.author}")
    
        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e

    @commands.command(name="createrelease", aliases=["unban", "release"], help=poll_parser.format_help())
    @commands.guild_only()
    @wait_react
    async def create_unban_poll(self, ctx: Context, user_to_unban: discord.Member):
        try:
            if not user_to_unban.is_timed_out():
                await ctx.send("This user is not banned!")
            else:
                print("Parsing args")
                pollTimeUnban = 30

                options = ["Are we going to unban user {}?".format(user_to_unban.display_name), "Yes", "No"]

                def extra_checks(args):  # Extra checks past the parser's basic ones. These are caught and forwarded in run_parser
                    if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                    if args.winners <= 0: raise argparse.ArgumentError(win_arg, f"Cannot select less than 1 winner.")
                    if args.limit < 0: raise argparse.ArgumentError(lim_arg, f"Cannot have limit less than 1.")
                    for op in args.options:
                        if len(op) > 50: raise argparse.ArgumentError(opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

                args = run_parser(poll_parser, options, extra_checks)
                # Send feedback or run vote
                idl = []
                if isinstance(args, str): await ctx.send(args)
                else:
                    await self.vm.std_moderate_vote(ctx, args, user_to_unban.mention, idl=idl, pollTime=pollTimeUnban)

                await asyncio.sleep(pollTimeUnban)
                await self.close_poll(ctx, idl[0])

                if await self.isProgress(ctx, 1, 0):
                    await ctx.send(f"Decision: Revoke timeout for {user_to_unban.mention}.")
                    await user_to_unban.timeout(None, reason="Vote to revoke moderation")

        # Catch any exception, to ensure the bot continues running for other votes
        # and to give error message due to error messages in async blocks not being reported otherwise
        except Exception as e:
            print(e)
            raise e
    '''
    @commands.command(name="stvpoll", help=("Runs a STV poll.\n" + stv_parser.format_help()))
    @commands.guild_only()
    @wait_react
    async def create_stv_poll(self, ctx: Context, *options):
        try:
            print("Parsing args")

            def extra_checks(args):
                if len(args.options) < 2 or len(symbols) < len(args.options): raise argparse.ArgumentError(opt_arg, f"Between 2 and {len(symbols)} options must be supplied.")
                if args.winners <= 0: raise argparse.ArgumentError(win_arg, f"Cannot select less than 1 winner.")
                if args.limit < 0: raise argparse.ArgumentError(lim_arg, f"Cannot have limit less than 1.")
                for op in args.options:
                    if len(op) > 50: raise argparse.ArgumentError(opt_arg, f"Option {op} is too long. Lines can be no longer than 50 characters (current length {len(op)}))")

            args = run_parser(stv_parser, options, extra_checks)
            if isinstance(args, str): await ctx.send(args)
            else:
                await self.vm.stv_vote(ctx, args)

        except Exception as e:
            print(e)
            raise e
    '''

    @commands.command(name="closem", aliases=["closempoll", "closemvote"], help="Ends a poll with ID `pid`")
    @commands.has_permissions(administrator=True)
    @done_react
    @wait_react
    async def close_poll(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            await self.vm.close(vid)
        else: await ctx.send("You cannot end this poll")


    @commands.command(name="voters", help="Gets the number of people who have voted in a poll.")
    @wait_react
    async def voters(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            voters = voteDB.getVoterCount(vid)
            await ctx.send(f"{voters} people have voted so far in vote {vid}.")


    @commands.command(name="myvotes", help="Will DM with your current votes for vote `vid`.")
    @wait_react
    @done_react
    async def myvotes(self, ctx: Context, vid: int):
        user = ctx.author
        await user.create_dm()

        options = [x[1] for x in voteDB.getOptions(vid)]
        uvs = voteDB.getUserVotes(vid, user.id)

        if not uvs: await user.dm_channel.send(f"Poll {vid}: You have no votes so far.")
        else: await user.dm_channel.send(
                f"Poll {vid}: Your current votes are:\n\t\t" +
                '\n\t\t'.join(f"{symbols[i]} **{options[i]}**" for i, _ in uvs)
            )



    @commands.command(name="halt", help="Ends a vote early with no results page.")
    @commands.has_permissions(administrator=True)
    @wait_react
    @done_react
    async def halt(self, ctx: Context, vid: int):
        if voteDB.allowedEnd(vid, ctx.author.id):
            await self.vm.halt(vid)


    @commands.Cog.listener()
    @commands.guild_only()
    async def on_raw_reaction_add(self, reaction: discord.RawReactionActionEvent):
        # user = self.bot.get_user(reaction.user_id)
        user = reaction.member
        emoji = str(reaction.emoji)

        guild: discord.Guild = self.bot.get_guild(reaction.guild_id)
        if not guild: return  # In DM, ignore
        channel: discord.TextChannel = guild.get_channel(reaction.channel_id)
        message: discord.Message = await channel.fetch_message(reaction.message_id)

        if user.bot: return
        await self.vm.on_reaction_add(reaction, emoji, message, user)

    @commands.Cog.listener()
    @commands.guild_only()
    async def on_raw_reaction_remove(self, reaction: discord.RawReactionActionEvent):
        # user = self.bot.get_user(reaction.user_id)
        # user = reaction.member
        emoji = str(reaction.emoji)

        guild: discord.Guild = self.bot.get_guild(reaction.guild_id)
        user = guild.get_member(reaction.user_id)
        if not guild: return  # In DM, ignore
        channel: discord.TextChannel = guild.get_channel(reaction.channel_id)
        message: discord.Message = await channel.fetch_message(reaction.message_id)

        if user.bot: return
        await self.vm.on_reaction_remove(reaction, emoji, message, user)

    @staticmethod
    def calcPollPeriod(time_to_ban_in_min: np.float64) -> np.float64:
        return np.ceil((1 - np.exp(-time_to_ban_in_min/timeConst)) * 1440)
    
    @staticmethod
    def parseTimeout(ctx: Context, timeout: str) -> (bool, np.float64):
        if bool(pattern.match(timeout)) or bool(pattern1.match(timeout)):
            timeValue = np.float64(timeout[:-1])
            timeUnit = timeout[-1]
            if timeUnit == "h":
                timeValue *= 1
            elif timeUnit == "d":
                timeValue *= 24
            elif timeUnit == "w":
                timeValue *= 168
            else:
                timeValue = 0
                
        else:
            return False, 0

        if timeValue <= 0:
            timeValue = 0

        return True, timeValue

    @staticmethod
    async def isProgress(ctx: Context, yes: int, no: int) -> bool:
        return True


# Register module with bot
async def setup(bot):
    await bot.add_cog(VoteModerate(bot))

