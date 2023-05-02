import nextcord
import dataset
import asyncio
import random
import wave

from nextcord.ext import commands, application_checks, tasks
from configs.config_menager import config_get, message_get
from utils.interface import start_interface, scores_interface
from utils.silero import spitch_de, spitch_ru
from utils.random_text import get_random_texts
from utils.text2player import get_data
from datetime import datetime
from datetime import timedelta
from string import ascii_uppercase

db = dataset.connect("sqlite:///database/db.db")
table_games = db["games"]
table_players = db["players"]


class Button(nextcord.ui.Button["ViewButton"]):
    def __init__(self, bot: commands.Bot, *args):
        super().__init__(label=args[0], emoji=args[1], style=args[2], custom_id=args[3], row=args[4], url=args[5], disabled=args[6])
        self.bot = bot

    async def callback(self, interaction: nextcord.Interaction):
        command = self.custom_id
        color, voice = config_get("color"), message_get("pricolist")["voice"]
        guild, channel, user = interaction.guild, interaction.channel, interaction.user

        if command == "start":
            lobby = table_games.find_one(host=user.id)
            if lobby == None:
                messages = message_get("error_2")
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["desc"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=messages["img"])
                return await interaction.send(embed=emb, ephemeral=True)

            msg = await channel.fetch_message(lobby.get("message"))
            vc = interaction.guild.voice_client
            script = random.randint(0, len(voice["start"])-1)

            if lobby != None:
                await Pricolist.game_start(self, user, msg)
                await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=f'{voice["start"][script]}{voice["rules"][random.randint(0, len(voice["rules"])-1)]}', vc=vc))

                for type in range(1, 3):
                    await Pricolist.game_round(self, lobby, msg, type)
                    await Pricolist.game_create_thread(self, lobby, channel, type)

                    await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["round"][random.randint(0, len(voice["round"])-1)], vc=vc))
                    await asyncio.sleep(60)
                    await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["ending_round"][random.randint(0, len(voice["ending_round"])-1)], vc=vc))

                    await Pricolist.game_show_responses(self, table_games.find_one(host=user.id), channel, msg, vc)
                    await Pricolist.game_show_scores(self, table_games.find_one(host=user.id), msg, vc)

                await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["completion"][random.randint(0, len(voice["completion"])-1)] + user.name + voice["end"][script], vc=vc))

                lobby = table_games.find_one(host=user.id)
                [await guild.get_channel(lobby.get("channels")[channel]).delete() for channel in lobby.get("channels")]
                table_games.delete(code=lobby.get("code"), message=lobby.get("message"))
                table_players.delete(game=lobby.get("code"))

        elif command == "delete":
            lobby = table_games.find_one(host=user.id)
            if lobby == None:
                messages = message_get("error_2")
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["desc"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=messages["img"])
                return await interaction.send(embed=emb, ephemeral=True)

            [await guild.get_channel(lobby.get("channels")[channel]).delete() for channel in lobby.get("channels")]
            table_games.delete(host=user.id, message=lobby.get("message"))
            table_players.delete(game=lobby.get("code"))


class Select(nextcord.ui.Select):
    def __init__(self, bot: commands.Bot, placeholder: str, elem: list, min_val: int, max_val: int):
        super().__init__(placeholder=placeholder, min_values=min_val, max_values=max_val, options=elem)

    async def callback(self, interaction: nextcord.Interaction):
        color, messages = config_get("color"), message_get("pricolist")["voiting"]
        user = interaction.user.id

        for row in range(len(list(table_players))):
            player = list(table_players)[row]

            if user in player.get("votes"):
                emb = nextcord.Embed(title=messages["again"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                return await interaction.send(embed=emb, ephemeral=True)

            elif user == int(self.values[0]):
                emb = nextcord.Embed(title=messages["myself"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                return await interaction.send(embed=emb, ephemeral=True)

            elif int(self.values[0]) == player.get("user") and user != player.get("user"):
                player.get("votes").append(user)
                table_players.update(dict(user=int(self.values[0]), votes=player.get("votes")), ["user"])
                emb = nextcord.Embed(title=messages["good"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                return await interaction.send(embed=emb, ephemeral=True)


class ViewButton(nextcord.ui.View):
    def __init__(self, bot: commands.Bot, elem: list):
        super().__init__(timeout = None)
        [self.add_item(Button(bot, elem[i][0], elem[i][1], elem[i][2], elem[i][3], elem[i][4], elem[i][5], elem[i][6])) for i in range(len(elem))]


class ViewSelect(nextcord.ui.View):
    def __init__(self, bot: commands.Bot, placeholder: str, elem: list, min_val: int, max_val: int):
        super().__init__()
        self.add_item(Select(bot, placeholder, elem, min_val, max_val))


class Repbatalia(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        custom_ids = ["start", "delete"]
        [self.bot.add_view(ViewButton(bot=self.bot, elem=[[None, None, None, i, 1, None, None]])) for i in custom_ids]

def setup(bot):
    bot.add_cog(Repbatalia(bot))