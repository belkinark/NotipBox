import os
import torch
import inspect
from transliterate import translit

device = torch.device("cpu")
torch.set_num_threads(4)

async def spitch_de(text: str) -> str:
    local_file = "utils/models/model_de.pt"
    digits = {'0': 'ноль', '1': 'один', '2': 'два', '3': 'три', '4': 'четыре', '5': 'пять', '6': 'шесть', '7': 'семь', '8': 'восемь', '9': 'девять'}
    result = ''
    for char in text:
        if char.isdigit():
            result += digits[char] + ' '
        else:
            result += char
    text = result
    text = translit(text, 'ru', reversed=True)

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file("https://models.silero.ai/models/tts/de/v3_de.pt", local_file)

    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

    sample_rate = 48000
    speaker = "random" # bernd_ungerer

    return model.save_wav(audio_path="utils/speak.wav", text=text, speaker=speaker, sample_rate=sample_rate)

async def spitch_ru(text: str) -> str:
    local_file = "utils/models/model_ru.pt"
    digits = {'0': 'ноль', '1': 'один', '2': 'два', '3': 'три', '4': 'четыре', '5': 'пять', '6': 'шесть', '7': 'семь', '8': 'восемь', '9': 'девять',
              'A': 'а', 'B': 'б', 'C': 'ц', 'D': 'д', 'E': 'и', 'F': 'ф', 'G': 'г', 'H': 'х', 'I': 'и', 'J': 'дж', 'K': 'к', 'L': 'л', 'M': 'м', 'N': 'н', 'O': 'о', 'P': 'п', 'Q': 'кью', 'R': 'р', 'S': 'с', 'T': 'ти', 'U': 'ю', 'V': 'в', 'W': 'ю', 'X': 'кс', 'Y': 'у', 'Z': 'з'}
    result = ''
    for char in text.upper():
        try:
            result += digits[char] + ' '
        except:
            result += char
    text = result

    if not os.path.isfile(local_file):
        torch.hub.download_url_to_file("https://models.silero.ai/models/tts/ru/v3_1_ru.pt", local_file)

    model = torch.package.PackageImporter(local_file).load_pickle("tts_models", "model")
    model.to(device)

    sample_rate = 48000
    speaker = "aidar" # aidar, baya, kseniya, xenia, eugene, random

    return model.save_wav(audio_path="utils/speak.wav", text=text, speaker=speaker, sample_rate=sample_rate)

# spitch_de("831 magomed привет")
# spitch_ru("Для каждого я создал ветку, где вы должны ответить на серъёзные вопросы. ................... Ну чего стоим? Приступам у вас 1 минута")