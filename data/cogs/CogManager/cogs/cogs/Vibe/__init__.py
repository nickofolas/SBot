from .vibe import Vibe

async def setup(bot):
    bot.add_cog(Vibe(bot))
