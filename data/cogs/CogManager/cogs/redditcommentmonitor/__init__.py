from .commentmonitor import RedditPostMonitor


def setup(bot):
    bot.add_cog(RedditPostMonitor(bot))
