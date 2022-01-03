import asyncio
import logging

import discord
import inspirobot
from discord.ext import tasks
from redbot.core import commands

log = logging.getLogger("red.cbd-cogs.tube")


class Vibe(commands.Cog):
    flow = None
    flow_generator = None
    """ InspiroBot Flow API client for Red """
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    @commands.bot_has_permissions(embed_links=True)
    async def vibe(self, ctx: commands.Context, speed: str = "normal"):
        """ Start (or stop) vibing
        
        Available speeds: pause/stop, glacial, slow, normal, fast, dizzy """
        # Get the numeric representation for the speed divisor
        numeric_speed = {
            "pause"     : 0,
            "stop"      : 0,
            "glacial"   : 0.2,
            "slow"      : 0.6,
            "normal"    : 1.0,
            "fast"      : 1.4,
            "dizzy"     : 1.8
        }.get(speed, 1.0)
        # Speeds greater than 0 start the flow
        if numeric_speed > 0:
            # Make sure the wave machine is ready
            if self.flow_generator is None:
                log.info(f"Starting flow generator")
                self.flow_generator = self.infinite_flow()
            if self.vibe_loop.is_running():
                self.vibe_loop.restart(ctx, numeric_speed)
                log.info(f"Flow speed divisor changed to {numeric_speed}")
            else:
                self.vibe_loop.start(ctx, numeric_speed)
                log.info(f"Flow started with speed divisor {numeric_speed}")
        # A speed of 0 will temporarily pause the flow
        else:
            log.info("Pausing flow")
            self.vibe_loop.cancel()

    async def new_wave(self, ctx: commands.Context, speed: float):
        """ Send the next wave """
        # Get next wave from the wave generator
        wave = await self.flow_generator.__anext__()
        # Build a beautiful embed with text and colors and pictures yay
        embed = discord.Embed(url=wave.image.url,
                              description=wave.text,
                              color=await ctx.embed_color())
        embed.set_image(url=wave.image.url)
        # Ship it!
        await ctx.send(embed=embed)
        # Sleep until next wave, enforcing a minimum wave duration
        await asyncio.sleep(max(6/speed, wave.duration)/speed)

    async def infinite_flow(self):
        """ Infinite flow wave generator """
        while True:
            await self.refresh_flow()
            for wave in self.flow:
                log.info("Generated new wave")
                yield wave

    async def refresh_flow(self):
        """ Start an inspirobot flow """
        loop = asyncio.get_running_loop()
        if self.flow is None:
            # Initialize new flow
            self.flow = await loop.run_in_executor(None, inspirobot.flow)
            log.info("Flow initialized")
        else:
            # Refresh already initialized flow
            await loop.run_in_executor(None, self.flow.new)
            log.info("Flow refreshed")

    def cog_unload(self):
        """ Clean up for unload """
        self.vibe_loop.cancel()

    @tasks.loop(seconds=1)
    async def vibe_loop(self, ctx: commands.Context, speed: float):
        """ Never stop vibing """
        await self.new_wave(ctx, speed)

    @vibe_loop.before_loop
    async def wait_for_red(self):
        """ Wait for runway clearance """
        await self.bot.wait_until_red_ready()
