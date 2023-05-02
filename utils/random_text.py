import random

async def get_random_texts(mode: str, type: int, players: list) -> list:
    with open(f"interface/texts/{mode}/type_{type}.txt", encoding="utf-8") as filename:
        file = filename.read().split("\n")
        random.shuffle(file)
        random.shuffle(players)

        texts = []
        for i in range(len(players)):
            file[i] = file[i].replace("$p1", players[i])
            file[i] = file[i].replace("$p2", players[i+1] if i != len(players)-1 else players[i-1])
            texts.append(file[i])

        return texts

# for i in range(100000):
#     x = get_random_text("pricolist", 1, ["Belkinark_FX", "HoP_soFaN", "NiceBlox", "Magomed", "ttv ZTB"])
#     if len(x) != 5:
#         print(len(x))
