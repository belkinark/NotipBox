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

                for type in range(1, 4):
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


class Pricolist(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_ready(self):
        custom_ids = ["start", "delete"]
        [self.bot.add_view(ViewButton(bot=self.bot, elem=[[None, None, None, i, 1, None, None]])) for i in custom_ids]

    @commands.Cog.listener()
    async def on_message(self, message: nextcord.message.Message):
        color, messages = config_get("color"), message_get("pricolist")["thread"]
        player = table_players.find_one(user=message.author.id)

        if player != None and player.get("mode") == "pricolist" and player.get("thread") == message.channel.id:
            if message.attachments == [] and len(message.content) <= 100 and len(message.content) > 0:
                for question in list(player.get("data").keys()):
                    if player.get("data")[question] == None:
                        player.get("data")[question] = message.content
                        break
                table_players.update(dict(user=message.author.id, data=player.get("data")), ["user"])
                await message.channel.purge(limit = 1)

                if None in list(player.get("data").values()):
                    msg = await message.channel.fetch_message(player.get("message"))
                    print(player.get("step"))
                    print(type(player.get("step")))
                    if player.get("step") == 3:
                        emb = nextcord.Embed(title=messages["title"],
                                             description=messages["type_3"],
                                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                        emb.set_image(url=[q for q in player.get('data') if player.get('data')[q] == None][0])
                        emb.set_footer(text=messages["footer"])
                    else:
                        emb = nextcord.Embed(title=messages["title"],
                                             description=f"```{[q for q in player.get('data') if player.get('data')[q] == None][0]}```",
                                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                        emb.set_footer(text=messages["footer"])

                else:
                    await message.channel.edit(locked=True)
                    messages = message_get("pricolist")["finally"]
                    msg = await message.channel.fetch_message(player.get("message"))
                    emb = nextcord.Embed(title=messages["title"],
                                        description=messages["desc"],
                                        color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                    emb.set_image(url=messages["img"])

                await msg.edit(f"<@{message.author.id}>", embed=emb)

            else:
                await message.channel.purge(limit = 1)

                messages = message_get("error_3")
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["desc"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=messages["img"])
                await message.channel.send(embed=emb)

                await asyncio.sleep(3)
                await message.channel.purge(limit = 1)

    async def create_game(self, interaction: nextcord.Interaction):
        color, messages = config_get("color"), message_get("pricolist")["lobby"]
        guild, user = interaction.guild, interaction.user
        
        emb = nextcord.Embed(title=messages["message"],
                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
        msg = await interaction.send(embed=emb, ephemeral=True)

        code = ''.join(random.choice(ascii_uppercase) for i in range(4)) # Допилить исключения
        create = datetime.now()
        table_players.insert(dict(user=user.id, score=0, game=code, mode="pricolist"))

        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(read_messages=False, send_messages=False),
            await guild.fetch_member(user.id): nextcord.PermissionOverwrite(read_messages=True, send_messages=False)
        }
        category = await guild.create_category(name=messages["category"]+code, overwrites=overwrites, position=0)
        channel = await guild.create_text_channel(name=messages["text"], category=category, overwrites=overwrites, default_thread_slowmode_delay=5)
        voice = await guild.create_voice_channel(name=messages["voice"], category=category, overwrites=overwrites)

        await start_interface([user.avatar])
        file = nextcord.File("interface/cache/lobby.png", "lobby.png")
        emb = nextcord.Embed(title=messages["title"],
                             description=messages["desc"] + f"\n```{code}```",
                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
        emb.set_image(url="attachment://lobby.png")
        emb.set_footer(text=messages["footer"])
        emb.timestamp = datetime.now() + timedelta(minutes=5)
        buttons = [
            [messages["btn1"], None, nextcord.ButtonStyle.secondary, "start", 1, None, True],
            [messages["btn2"], None, nextcord.ButtonStyle.danger, "delete", 1, None, False],
        ]
        message = await channel.send(embed=emb, view=ViewButton(self.bot, buttons), file=file)

        channels = {
            "category": category.id,
            "channel": channel.id,
            "voice": voice.id,
        }
        table_games.insert(dict(host=user.id, code=code, step="lobby", message=message.id, create=create, channels=channels, players=[user.id]))

        buttons = [
            [messages["btn3"], None, nextcord.ButtonStyle.secondary, None, 1, f"https://discord.com/channels/{guild.id}/{channel.id}", False]
        ]
        await msg.edit(view=ViewButton(self.bot, buttons))

        if self.bot.voice_clients == []:
            await voice.connect()

        await Pricolist.timeout_lobby(self, code, guild)

    async def join_game(self, lobby: dict, interaction: nextcord.Interaction):
        guild = interaction.guild

        messages = message_get("pricolist")["lobby"]
        channel = guild.get_channel(lobby.get("channels")["channel"])
        voice = guild.get_channel(lobby.get("channels")["voice"])
        message = await channel.fetch_message(lobby.get("message"))

        players = [(await self.bot.fetch_user(user)) for user in lobby.get("players")]
        avatars = [(await self.bot.fetch_user(user)).avatar for user in lobby.get("players")]

        overwrites = {
            player: nextcord.PermissionOverwrite(read_messages=True, send_messages=False) for player in players
        }
        overwrites[guild.default_role] = nextcord.PermissionOverwrite(read_messages=False, send_messages=False)
        await channel.edit(overwrites=overwrites)
        await voice.edit(overwrites=overwrites)
        await start_interface(avatars)

        file = nextcord.File("interface/cache/lobby.png", "lobby.png")
        if len(avatars) >= 3:
            buttons = [
                [messages["btn1"], None, nextcord.ButtonStyle.primary, "start", 1, None, False],
                [messages["btn2"], None, nextcord.ButtonStyle.danger, "delete", 1, None, False],
            ]
        else:
            buttons = [
                [messages["btn1"], None, nextcord.ButtonStyle.secondary, "start", 1, None, True],
                [messages["btn2"], None, nextcord.ButtonStyle.danger, "delete", 1, None, False],
            ]

        await message.edit(view=ViewButton(self.bot, buttons), file=file)

    async def timeout_lobby(self, code: str, guild: nextcord.guild.Guild):
        await asyncio.sleep(300)
        lobby = table_games.find_one(code=code)
        if lobby != None and lobby.get("step") == "lobby":
            [await guild.get_channel(lobby.get("channels")[channel]).delete() for channel in lobby.get("channels")]
            table_games.delete(code=code, message=lobby.get("message"))

    async def speak(self, lang: str, text: str, vc: nextcord.VoiceClient) -> int:
        if vc != None:
            file = await spitch_ru(text) if lang == "ru" else await spitch_de(text)
            source = nextcord.FFmpegPCMAudio(file)
            vc.play(source)
            with wave.open('utils/speak.wav', 'r') as wav_file:
                return round(wav_file.getnframes() / wav_file.getframerate())
        return 10

    async def write_answer(message: nextcord.Message, player: dict, content: str):
        color, messages = config_get("color"), message_get("pricolist")["thread"]

        for question in list(player.get("data").keys()):
            if player.get("data")[question] == None:
                player.get("data")[question] = content
                break
        table_players.update(dict(user=message.author.id, data=player.get("data")), ["user"])
        await message.channel.purge(limit = 1)

        if None in list(player.get("data").values()):
            msg = await message.channel.fetch_message(player.get("message"))
            if player.get("step") == "3":
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["type_3"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=[q for q in player.get('data') if player.get('data')[q] == None][0])
            else:
                emb = nextcord.Embed(title=messages["title"],
                                     description=f"```{[q for q in player.get('data') if player.get('data')[q] == None][0]}```",
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))

        else:
            await message.channel.edit(locked=True)
            messages = message_get("pricolist")["finally"]
            msg = await message.channel.fetch_message(player.get("message"))
            emb = nextcord.Embed(title=messages["title"],
                                 description=messages["desc"],
                                 color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
            emb.set_image(url=messages["img"])

        await msg.edit(f"<@{message.author.id}>", embed=emb)

    async def game_start(self, user: nextcord.Member, msg: nextcord.Message):
        color, messages = config_get("color"), message_get("pricolist")["start"]
        table_games.update(dict(host=user.id, step="game"), ["host"])

        emb = nextcord.Embed(title=messages["title"],
                             description=messages["desc"],
                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
        emb.set_image(url="https://media.discordapp.net/attachments/1097195738187960492/1097869721124208751/Sprite-00015.png?width=809&height=455")
        await msg.edit(embed=emb, files=[], view=[])

    async def game_round(self, lobby: dict, msg: nextcord.Message, round_type: int):
        color, messages = config_get("color"), message_get("pricolist")["round"]
        table_games.update(dict(code=lobby.get("code"), step=round_type), ["code"])
        emb = nextcord.Embed(title=messages["title"],
                             description=messages["desc"],
                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
        emb.set_image(url=messages[str(round_type)])
        await msg.edit(embed=emb, files=[])

    async def game_show_responses(self, lobby: dict, channel: nextcord.TextChannel, msg: nextcord.Message, vc: nextcord.VoiceClient):
        color, messages, emoji, voice = config_get("color"), message_get("pricolist")["responses"], message_get("emoji"), message_get("pricolist")["voice"]

        players = lobby.get("players")
        for player in players:
            thread = channel.get_thread(table_players.find_one(user=player).get("thread"))
            await thread.delete()

        data = await get_data(players, table_players, lobby)

        for question in list(data):
            """ SHOW RESPONSES """
            if lobby.get("step") == "3":
                duration = await Pricolist.speak(self, lang="ru", text=messages["type_3"], vc=vc)
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["type_3"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=question)
            else:
                duration = await Pricolist.speak(self, lang="ru", text=question, vc=vc)
                emb = nextcord.Embed(title=messages["title"],
                                    description=f"```{question}```",
                                    color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
            await msg.edit(embed=emb)
            await asyncio.sleep(duration)

            selects = []
            for player in list(data[question]):
                if data[question][player] == None:
                    data[question][player] = "Нет ответа"
                duration = await Pricolist.speak(self, lang="de", text=data[question][player], vc=vc)
                emb.add_field(name="> ---", value=f"```{data[question][player]}```", inline=False)
                random_emoji = self.bot.get_emoji(random.choice(list(emoji.values())))
                selects.append(nextcord.SelectOption(label=data[question][player], value=player, emoji=random_emoji))
                await msg.edit(embed=emb)
                await asyncio.sleep(duration)

            await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["voting_answers"][random.randint(0, len(voice["voting_answers"])-1)], vc=vc))

            """ VOTING """
            await msg.edit(view=ViewSelect(self.bot, messages["voting"], selects, 1, 1))
            await asyncio.sleep(15)
            await msg.edit(view=[])
            for player in list(data[question]):
                db_player = table_players.find_one(user=player)
                table_players.update(dict(user=player, score=db_player.get("score")+len(db_player.get("votes"))*100, votes=[]), ["user"])
            await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["show_players"][random.randint(0, len(voice["show_players"])-1)], vc=vc))

            """ SHOW PLAYERS """
            if lobby.get("step") == "3":
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["type_3"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=question)
            else:
                emb = nextcord.Embed(title=messages["title"],
                                     description=f"```{question}```",
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
            for player in list(data[question]):
                emb.add_field(name=f"> {(await self.bot.fetch_user(player)).name}", value=f"```{data[question][player]}```", inline=False)
            await msg.edit(embed=emb)

            await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["next_answers"][random.randint(0, len(voice["next_answers"])-1)], vc=vc))

    async def game_show_scores(self, lobby: dict, msg: nextcord.Message, vc: nextcord.VoiceClient):
        color, messages, voice = config_get("color"), message_get("pricolist")["scores"], message_get("pricolist")["voice"]
        players_db = list(table_players.find(game=lobby.get("code")))

        players = [(await self.bot.fetch_user(player.get("user"))).name for player in players_db]
        socres = [player.get("score") for player in players_db]
        await scores_interface(players, socres)

        file = nextcord.File("interface/cache/scores.png", "scores.png")
        emb = nextcord.Embed(title=messages["title"],
                             description=messages["desc"],
                             color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
        emb.set_image(url="attachment://scores.png")
        await msg.edit(embed=emb, file=file)

        await asyncio.sleep(await Pricolist.speak(self, lang="ru", text=voice["scores"][random.randint(0, len(voice["scores"])-1)], vc=vc))

    async def game_create_thread(self, lobby: dict, channel: nextcord.TextChannel, round_type: int):
        color, messages = config_get("color"), message_get("pricolist")["thread"]
        players = lobby.get("players")
        data = {"questions": None, "answers": []}
        texts = await get_random_texts("pricolist", round_type, [(await self.bot.fetch_user(players[i])).name for i in range(len(players))])
        random.shuffle(players)

        for i in range(len(players)):
            thread = await channel.create_thread(name=messages["name"],
                                                 auto_archive_duration=1440,
                                                 type=nextcord.ChannelType.private_thread,
                                                 reason=None)

            data = {}
            if i+1 != len(players):
                data[texts[i]], data[texts[i+1]] = None, None
            else:
                data[texts[i]], data[texts[0]] = None, None

            if round_type == 3:
                emb = nextcord.Embed(title=messages["title"],
                                     description=messages["type_3"],
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
                emb.set_image(url=texts[i])
            else:
                emb = nextcord.Embed(title=messages["title"],
                                     description=f"```{texts[i]}```",
                                     color=nextcord.Color.from_rgb(r=color[0], g=color[1], b=color[2]))
            emb.set_footer(text=messages["footer"])
            
            message = await thread.send(f"<@{players[i]}>", embed=emb)

            table_players.update(dict(user=players[i], votes=[], step=round_type, thread=thread.id, message=message.id, data=data), ["user"])


def setup(bot):
    bot.add_cog(Pricolist(bot))