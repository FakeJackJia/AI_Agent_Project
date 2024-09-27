import telebot
import urllib
import requests
import json
import os, asyncio

bot = telebot.TeleBot('7229557238:AAEkaL4pIAIt9WSUAnjX2-23VkMxrmvbW6Q')

@bot.message_handler(commands=['start'])
def start_message(message):
    bot.send_message(message.chat.id, '你好我是陈瞎子，欢迎光临!')

@bot.message_handler(func=lambda message:True)
def echo_all(message):
    try:
        encoded_text = urllib.parse.quote(message.text)
        response = requests.post("http://192.168.1.89:8000/chat?query=" + encoded_text, timeout=100)
        if response.status_code == 200:
            rsp = json.loads(response.text)
            if "msg" in rsp:
                bot.reply_to(message, rsp['msg']["output"])
                audio_path = f"{rsp['id']}.mp3"
                asyncio.run(check_audio(message, audio_path))
            else:
                bot.reply_to(message, "对不起，我不知道怎么回复你")
    except requests.RequestException as e:
        bot.reply_to(message, "对不起，我不知道怎么回复你")

async def check_audio(message, audio_path):
    while True:
        if os.path.exists(audio_path):
            with open(audio_path, 'rb') as f:
                bot.send_audio(message.chat.id, f)
            os.remove(audio_path)
            break
        else:
            print("waiting")
            await asyncio.sleep(1) # wait 1 second

bot.infinity_polling()