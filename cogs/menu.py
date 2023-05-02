import nextcord
import dataset

from nextcord.ext import commands, application_checks
from configs.config_menager import config_get, message_get

db = dataset.connect("sqlite:///database/db.db")
table_games = db["games"]
table_players = db["players"]


class Modal(nextcord.ui.Modal):
    def __init__(self, messages: list, bot: commands.Bot, **kwargs: nextcord.ui.text_input.TextInput):
        self.bot = bot
        self.kwargs = kwargs
        super().__init__(messages["modal"])
        [self.add_item(val) for val in self.kwargs.values()]

    async def callback(self, interaction: nextcord.Interaction):
        color = config_get("color")
        command = [self.kwargs.get(key).custom_id for key in self.kwargs.keys()]
        values = [self.kwargs.get(key).value for key in self.kwargs.keys()]

        if "join" in command:
            lobby = table_games.find_one(code=values[0].upper())

            if lobby != None:
                user = interaction.user
                if table_players.find_one(user=user.id) == None and lobby.get("step") == "lobby":
                    lobby.get("players").append(user.id)
                    table_games.update(dict(code=lobby.get("code"), players=lobby.get("players")), ["code"])
                    table_players.insert(dict(user=user.id, score=0, game=lobby.get("code"), mode="pricolist"))
                    messages = message_get("join")
                    emb = nextcord.Embed(title=messages["title"],
                                        color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                    buttons = [
                        [messages["btn1"], None, nextcord.ButtonStyle.secondary, None, 1, f"https://discord.com/channels/{interaction.guild.id}/{lobby.get('channels')['channel']}", False]
                    ]
                    await interaction.send(embed=emb, view=ViewButton(self.bot, buttons), ephemeral=True)
                    await self.bot.get_cog("Pricolist").join_game(lobby, interaction)
                else:
                    messages = message_get("error_4")
                    emb = nextcord.Embed(title=messages["title"],
                                        description=messages["desc"],
                                        color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                    emb.set_image(messages["img"])
                    await interaction.send(embed=emb, ephemeral=True)

            else:
                messages = message_get("error_1")
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["desc"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(messages["img"])
                await interaction.send(embed=emb, ephemeral=True)


class Button(nextcord.ui.Button["ViewButton"]):
    def __init__(self, bot: commands.Bot, *args):
        super().__init__(label=args[0], emoji=args[1], style=args[2], custom_id=args[3], row=args[4], url=args[5], disabled=args[6])
        self.bot = bot

    async def callback(self, interaction: nextcord.Interaction):
        command = self.custom_id
        color, messages = config_get("color"), message_get(command)
        user = interaction.user

        if command == "create":
            emb = nextcord.Embed(title=messages["title"],
                                 description=messages["desc"],
                                 color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
            [emb.add_field(name=messages[f"field{i}"], value=messages[f"value{i}"], inline=False) for i in range(3)]
            emb.set_image(messages["img"])
            buttons = [
                [messages["btn1"], None, nextcord.ButtonStyle.secondary, "pricolist", 1, None, False],
                [messages["btn2"], None, nextcord.ButtonStyle.secondary, "create1", 1, None, True],
                [messages["btn3"], None, nextcord.ButtonStyle.secondary, "join", 1, None, True],
            ]
            await interaction.send(embed=emb, view=ViewButton(self.bot, buttons), ephemeral=True)

        elif command == "join":
            await interaction.response.send_modal(Modal(messages, self.bot,
                                                  emOne=nextcord.ui.TextInput(label=messages["label"], min_length=4, max_length=4, required=True, custom_id="join")))

        elif command == "pricolist":
            if table_players.find_one(user=user.id) == None:
                await self.bot.get_cog("Pricolist").create_game(interaction)
            else:
                messages = message_get("error_4")
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["desc"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(messages["img"])
                await interaction.send(embed=emb, ephemeral=True)


class ViewButton(nextcord.ui.View):
    def __init__(self, bot: commands.Bot, elem: list):
        super().__init__(timeout = None)
        [self.add_item(Button(bot, elem[i][0], elem[i][1], elem[i][2], elem[i][3], elem[i][4], elem[i][5], elem[i][6])) for i in range(len(elem))]


class Menu(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        for lobby in list(table_games):
            code, channels = lobby.get("code"), lobby.get("channels")
            [await self.bot.guilds[0].get_channel(channels[channel]).delete() for channel in channels]
            table_games.delete(code=code)
            table_players.delete(game=code)
        custom_ids = ["create", "join", "pricolist"]
        [self.bot.add_view(ViewButton(bot=self.bot, elem=[[None, None, None, i, 1, None, None]])) for i in custom_ids]

    @nextcord.slash_command()
    @application_checks.is_owner()
    async def menu_setting(self, interaction: nextcord.Interaction):
        color, messages = config_get("color"), message_get("menu")
        emb = nextcord.Embed(title=messages["title"],
                             description=messages["desc"],
                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
        emb.set_thumbnail(messages["tub"])
        emb.set_image(messages["img"])
        buttons = [
            [messages["btn1"], None, nextcord.ButtonStyle.secondary, "create", 1, None, False],
            [messages["btn2"], None, nextcord.ButtonStyle.secondary, "join", 1, None, False],
        ]
        await interaction.channel.send(embed=emb, view=ViewButton(self.bot, buttons))


def setup(bot):
    bot.add_cog(Menu(bot))