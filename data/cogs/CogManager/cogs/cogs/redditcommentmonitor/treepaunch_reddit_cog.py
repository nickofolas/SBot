import re

import aiohttp
from redbot.core import Config, checks, commands

import discord
from discord.ext import tasks

URL_VALIDATE = re.compile(
    r"https://(www\.)?reddit\.com/r/\w+/comments/[\w\d]+/.*/(?!\.json)", re.I)


class RedditPostMonitor(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.config = Config.get_conf(self, identifier=8364573476)
        self.config.register_guild(**{
            "currently_watching": "",
            "feed_channel": None,
            "indexed_comments": []
        })
        bot.loop.create_task(self.__ainit__())

    async def __ainit__(self):
        self.session = aiohttp.ClientSession()
        self.do_comment_loop.start()

    @commands.command(name="viewredditmonitor")
    async def show_monitor_data(self, ctx):
        data = await self.config.guild(ctx.guild).all()

        embed = discord.Embed(
            title="Server Reddit Monitor Settings",
            description=f"**Post Being Watched** {data['currently_watching']}"
            + f"\n**Feed Channel** <#{data['feed_channel']}>" if data["feed_channel"] else "No Feed Channel",
            color=await ctx.embed_colour()
        )
        await ctx.send(embed=embed)

    @commands.command(name="setredditpost")
    @checks.admin_or_permissions(manage_guild=True)
    async def set_active_post(self, ctx, post_url: str):
        if not URL_VALIDATE.match(post_url):
            return await ctx.send("Please send a proper Reddit post URL")
        await self.config.guild(ctx.guild).currently_watching.set(post_url)
        await self.config.guild(ctx.guild).indexed_comments.set([])
        await ctx.message.add_reaction("☑️")

    @commands.command(name="unsetredditpost")
    @checks.admin_or_permissions(manage_guild=True)
    async def unset_active_post(self, ctx):
        await self.config.guild(ctx.guild).currently_watching.set("")
        await self.config.guild(ctx.guild).indexed_comments.set([])
        await ctx.message.add_reaction("☑️")

    @commands.command(name="setredditchannel")
    @checks.admin_or_permissions(manage_guild=True)
    async def set_active_channel(self, ctx, channel: discord.TextChannel):
        await self.config.guild(ctx.guild).feed_channel.set(channel.id)
        await ctx.message.add_reaction("☑️")

    @commands.command(name="unsetredditchannel")
    @checks.admin_or_permissions(manage_guild=True)
    async def unset_active_channel(self, ctx):
        await self.config.guild(ctx.guild).feed_channel.set(None)
        await ctx.message.add_reaction("☑️")

    @tasks.loop(seconds=300)  # Check every 5 minutes
    async def do_comment_loop(self):
        for guild_id, settings in (await self.config.all_guilds()).items():
            if not settings.get("currently_watching") \
                    or not settings.get("feed_channel"):
                continue
            guild = self.bot.get_guild(guild_id)

            async with self.session.get(settings["currently_watching"] + ".json") as resp:
                data = await resp.json()
                comments = [i["data"] for i in data[1]["data"]["children"]]
                for comment in comments:
                    indexed = await self.config.guild(guild).indexed_comments()
                    if comment["id"] in indexed:
                        continue

                    await self.config.guild(guild).indexed_comments.set(indexed + [comment["id"]])

                    embed = discord.Embed(
                        title="New Comment on Watched Post!",
                        description=comment["body"],
                        color=0xA29BFE,
                        url=settings["currently_watching"]
                    ).set_author(
                        name=f"Comment from {comment['author']}"
                    )
                    channel = self.bot.get_channel(settings["feed_channel"])
                    await channel.send(embed=embed)
