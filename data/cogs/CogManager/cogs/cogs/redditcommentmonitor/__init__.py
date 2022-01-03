from .treepaunch_reddit_cog import RedditPostMonitor


def setup(bot):
    bot.add_cog(RedditPostMonitor(bot))
