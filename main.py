import nextcord
import os

from nextcord.ext import commands
from configs.config_menager import config_get


class Bot(commands.Bot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

def main():
    intents = nextcord.Intents.default()
    intents.message_content = True

    bot = Bot(intents=intents)
    for fn in os.listdir("./cogs"):
        if fn.endswith(".py") and fn != "code.py":
            bot.load_extension(f"cogs.{fn[:-3]}")

    bot.run(config_get("token"))

if __name__ == "__main__":
    main()
