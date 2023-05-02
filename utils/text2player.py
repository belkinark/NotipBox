import dataset

async def get_data(players: list, table_players: dataset.Table, lobby: dict) -> dict:
    data = {}
    questions = []
    for i in range(len(players)):
        player_db = table_players.find_one(user=players[i], game=lobby.get("code"))
        questions.append(list(player_db.get("data")))
                
    questions = [elem[0] for elem in questions]

    for question in questions:
        answers = {}
        for player in players:
            try:
                answers[player] = table_players.find_one(user=player).get("data")[question]
            except KeyError:...
        data[question] = answers
    
    return data

