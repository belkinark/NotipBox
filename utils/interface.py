import requests
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO

async def start_interface(avatar: list):
    lobby = Image.open("interface/lobby.png")
    locations = [(910, 170), (670, 250), (590, 490), (670, 730), (910, 810), (1150, 730), (1230, 490), (1150, 250)]

    for i in range(len(avatar)):
        if avatar[i] != None:
            response = requests.get(avatar[i])
            user = Image.open(BytesIO(response.content))
        else:
            user = Image.open("interface/player.png")
        lobby.paste(user.resize((100, 100)), locations[i])

    lobby.save("interface/cache/lobby.png")

async def scores_interface(players: list, scores: list):
    locations = [(70, 50), (1274, 50), (70, 374), (672, 374), (1274, 374), (70, 698), (672, 698), (1274, 698)]
    font_text = ImageFont.truetype("interface/font/NotipBox.ttf", size=50)
    font_number = ImageFont.truetype("interface/font/NotipBox.ttf", size=100)
    game = Image.open("interface/scores.png")

    for i in range(len(players)):
        player_map = Image.open("interface/player_map.png")

        player_map_ready = ImageDraw.Draw(player_map)

        font_w = int(font_text.getlength(players[i]))
        player_map_ready.text(((player_map.width - font_w)/2, 50), players[i], font=font_text, fill=("white"))

        font_w = int(font_number.getlength(str(scores[i])))
        player_map_ready.text(((player_map.width - font_w)/2, 150), str(scores[i]), font=font_number, fill=("white"))

        game.paste(player_map, locations[i])

    
    game.save("interface/cache/scores.png")