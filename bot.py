
import json
import os
import random

import sys
import telepot
import time
from telepot.loop import MessageLoop

# --- Funktionen zum Speichern von Daten --- #

def save_status(obj):
    with open('chats.json', 'w') as f:
        f.write(json.dumps(obj))

def save_allowed(s):
    with open('allowed.json', 'w') as f:
        f.write(json.dumps(list(s)))

def save_keys(obj):
    with open('keys.json', 'w') as f:
        f.write(json.dumps(obj))

def save_dooropen(s):
    with open('dooropen.json', 'w') as f:
        f.write(json.dumps(s))

def save_shoplist(list):
    with open('shoplist.json', 'w') as f:
        f.write(json.dumps(list))

# --- Funktion zum Senden zufälliger Nachrichten --- #

def random_message(chat_id, messagelist):
    bot.sendMessage(chat_id, random.choice(messagelist))

# --- Dateien erstellen, wenn noch nicht erstellt --- #

if not os.path.isfile('chats.json'):
    save_status({})

if not os.path.isfile('allowed.json'):
    save_allowed(set())

if not os.path.isfile('keys.json'):
    save_keys({})

if not os.path.isfile('dooropen.json'):
    save_dooropen(False)

if not os.path.isfile('shoplist.json'):
    save_shoplist([])

# --- Globale Variablen --- #

chats = {}
allowed = []
keys = {}
shoplist = []
dooropen = False
TOKEN = ""
PASSWORD = "changeme"

with open('chats.json', 'r') as f:
    chats = json.load(f)

with open('allowed.json', 'r') as f:
    allowed = set(json.load(f))

with open('keys.json', 'r') as f:
    keys = json.load(f)

with open('dooropen.json', 'r') as f:
    dooropen = json.load(f)

with open('shoplist.json', 'r') as f:
    shoplist = json.load(f)

if os.path.isfile('config.json'):
    with open('config.json', 'r') as f:
        config = json.load(f)
        if config['token'] == "":
            sys.exit("No token defined. Define it in a file called token.txt.")
        if config['password'] == "":
            print("WARNING: Empty Password for registering to use the bot." +
                  " It could be dangerous, because anybody could use this bot" +
                  " and forward messages to the channels associated to it")
        TOKEN = config['token']
        PASSWORD = config['password']
else:
    sys.exit("No config file found. Remember changing the name of config-sample.json to config.json")

def is_allowed(msg):
    if msg['chat']['type'] == 'channel':
        return True #all channel admins are allowed to use the bot (channels don't have sender info)
    return 'from' in msg and msg['from']['id'] in allowed

def handle(msg):
    # define global variables
    global shoplist
    global chats

    print("Message: " + str(msg))
    # Add person as allowed
    content_type, chat_type, chat_id = telepot.glance(msg)
    txt = ""
    if 'text' in msg:
        txt = txt + msg['text']
    elif 'caption' in msg:
        txt = txt + msg['caption']
    # Addme and rmme only valid on groups and personal chats.
    if msg['chat']['type'] != 'channel':
        if "/addme" == txt.strip()[:6]:
            if msg['chat']['type'] != 'private':
                bot.sendMessage(chat_id, "Dieser Befehl kann nur in privaten Chats verwendet werden.")
            else:
                used_password = " ".join(txt.strip().split(" ")[1:])
                if used_password == PASSWORD:
                    allowed.add(msg['from']['id'])
                    save_allowed(allowed)
                    bot.sendMessage(chat_id, msg['from']['first_name'] + ", du hast nun die Berechtigung den Bot zu benutzen.")
                else:
                    bot.sendMessage(chat_id, "Leider falsches Passwort.")
        if "/rmme" == txt.strip()[:5]:
            allowed.remove(msg['from']['id'])
            save_allowed(allowed)
            bot.sendMessage(chat_id, "Deine Berechtigung den Bot zu benutzen wurde entfernt.")
    if is_allowed(msg):
        if txt != "":
            # Gibt Personen die Zugriffsrechte auf den Bot
            if "/add " == txt[:5]:
                txt_split = txt.strip().split(" ")
                if len(txt_split) == 2 and "#" == txt_split[1][0]:
                    tag = txt_split[1].lower()
                    name = ""
                    if msg['chat']['type'] == "private":
                        name = name + "Personal chat with " + msg['chat']['first_name'] + ((" " + msg['chat']['last_name']) if 'last_name' in msg['chat'] else "")
                    else:
                        name = msg['chat']['title']
                    chats[tag] = {'id': chat_id, 'name': name}
                    bot.sendMessage(chat_id, name + " added with tag " + tag)
                    save_status(chats)
                else:
                    bot.sendMessage(chat_id, "Leider hast du das Falsche Format benutzt, bitte versuche es erneut mit _/add #{tag}_", parse_mode="Markdown")
            # Löscht die Zugriffsrechte auf den Bot
            elif "/rm " == txt[:4]:
                txt_split = txt.strip().split(" ")
                if len(txt_split) == 2 and "#" == txt_split[1][0]:
                    tag = txt_split[1].lower()
                    if tag in chats:
                        if chats[tag]['id'] == chat_id:
                            del chats[tag]
                            bot.sendMessage(chat_id, "Tag "+tag+" deleted from taglist.")
                            save_status(chats)
                            return
                        else:
                            bot.sendMessage(chat_id, "Du kannst leider keine Tags von anderen Chats löschen.")
                    else:
                        bot.sendMessage(chat_id, "Dieser Tag exstiert nicht in der /taglist")
                else:
                    bot.sendMessage(chat_id, "Leider hast du das Falsche Format benutzt, bitte versuche es erneut mit _/add #{tag}_", parse_mode="Markdown")
            # Gibt eine Liste aller verfügbaren Tags aus
            elif "/tagliste" ==  txt.strip()[:9]:
                tags_names = []
                for tag in chats:
                    tags_names.append((tag, chats[tag]['name']))
                response = "<b>#-Gruppen</b>"
                for (tag, name) in sorted(tags_names):
                    response = response + "\n<b>" + tag + "</b>: <i>" + name + "</i>"
                response = response + "\n\n<b>#-Funktionen</b>" + "\n<b>#offen:</b> <i>Türe offen</i>\n<b>#zu:</b> <i>Türe zu</i>\n<b>#tür:</b> <i>Ist die Türe offen?</i>"

                bot.sendMessage(chat_id, response, parse_mode="HTML")
            # Fügt eine Person zur Schlüsselträgerliste zu
            elif "/addschlüssel" == txt[:13]:
                if msg['chat']['type'] != "private":
                    bot.sendMessage(chat_id, "Dieser Befehl kann nur in privaten Chats verwendet werden.")
                print(msg['from']['id'])
                keys[msg['from']['id']] = msg['from']['first_name']
                save_keys(keys)
                bot.sendMessage(msg['from']['id'], msg['from']['first_name'] + ", du wurdest als Schlüsselträger hinzugefügt.")
            # Löscht eine eine Person aus der Schlüsselträgerliste
            elif "/rmschlüssel" == txt[:12]:
                if msg['chat']['type'] != 'private':
                    bot.sendMessage(chat_id, "Dieser Befehl kann nur in privaten Chats verwendet werden.")
                del keys[msg['from']['id']]
                save_keys(keys)
                bot.sendMessage(msg['from']['id'], msg['from']['first_name'] + ", du wurdest als Schlüsselträger entfernt.")
            # Gibt eine Liste aus der Einkäufe
            elif "/geteinkäufe" == txt[:12]:
                output = "Auf der Einkaufsliste sind:\n\n"
                for i in range(len(shoplist)):
                    output = output + str(i+1) + ". " + shoplist[i] + "\n"
                output = output + "\nVielen Dank für deinen fleißigen Einsatz!"

                bot.sendMessage(msg['from']['id'], output)
            # Leert die Einkaufsliste
            elif "/cleareinkäufe" == txt[:14]:
                txt_split = txt.strip().split(" ")

                if(len(txt_split) > 1):

                    try:
                        if len(txt_split) == 2:
                            del shoplist[int(txt_split[1])-1]
                            save_shoplist(shoplist)
                            bot.sendMessage(msg['from']['id'], shoplist[int(txt_split[1])-1] + " wurde von der Einkaufsliste gelöscht")
                        elif len(txt_split) == 3:
                            del shoplist[int(txt_split[1])-1:int(txt_split[2])]
                            save_shoplist(shoplist)
                            bot.sendMessage(msg['from']['id'], "Die von dir spezifizierten Einträge wurden von der Einkaufsliste gelöscht")
                    except ValueError:
                        bot.sendMessage(msg['from']['id'], "Bitte sei nicht so gemein zu mir. Ich brauche Zahlen, um deine Liste zu löschen. Halte dich doch bitte an folgende Formen:\n/cleareinkäufe\n/cleareinkäufe [Nummer des zu löschenden Eintrags]\n/cleareinkäufe [Beginn des zu löschenden] [Ende des zu löschenden]")
                    except IndexError:
                        bot.sendMessage(msg['from']['id'], "Bitte sei nicht so gemin zu mir. Ich brauche Zahlen, um deine Liste zu löschen. Halte dich doch bitte an folgende Formen:\n/cleareinkäufe\n/cleareinkäufe [Nummer des zu löschenden Eintrags]\n/cleareinkäufe [Beginn des zu löschenden] [Ende des zu löschenden]")
                else:
                    shoplist.clear()
                    save_shoplist(shoplist)
                    bot.sendMessage(msg['from']['id'], "Die Einkaufsliste ist jetzt wieder leer")

            # Legt die Hilfe-Funktion fest
            elif "/hilfe" == txt[:6] or "/?" == txt[:2]:
                txt_split = txt.strip().split(" ")
                bot.sendMessage(msg['from']['id'], "FaustBüropkratbot:\nDieser Bot hilft dir die Kommunitkation im Faust zu organisiern.\n\n#-Tag für Gruppen:\n#bar - du schreibst in die Bar Gruppe\n#einkauf - du schreibst in die Einkaufsgruppe\n#events - du schreibst in die Eventrgruppe\n#finanzen - du schreibst in die Finazengruppe\n#getränke - du schreibst in die Getränkegruppe\n#lager - du schreibst an die Lagergruppe\n#publicitiy - Du schreibst an Öffenlichkeitsarbeit\n#schlüssel - du schreibst an alle Schlüsselträger\n#schriftverkehr - du schreibst an die Schriftverkehrgruppe\n#spiele - du schreibst an die Spielegruppe\n#technik - du schreibst an die Technikgruppe\n\n#-Funktionen:\n#offen - du schließt das Faust auf\n#tür - sagt die, ob das Faust offen ist\n#zu - du schließt das Faust zu\n\n /-Funktion:\n/addschlüssel - du wirst neuer Schlüsselträger\n/geteinkäufe - die Getränkeliste\n/rmschlüssel - du bist kein Schlüsselträger\n/tagliste - zeigt die alle verfügbaren Tags an")

            # Legt die Tag Funktion fest
            elif "#" == txt[0]:
                txt_split =txt.strip().split(" ")
                i = 0
                tags = []
                while i < len(txt_split) and txt_split[i][0] == "#":
                    tags.append(txt_split[i].lower())
                    i+=1

                # check if message consists exclusively of ignoretags
                ignoretags = ["#zu", "#offen", "#tür", "#schlüssel", "#einkaufsliste"]
                ignoremessage = True
                amountmessages = 0
                for tag in tags:
                    if not (tag in ignoretags):
                        ignoremessage = False
                        break
                    else:
                        amountmessages += 1
                if amountmessages > 1:
                    bot.sendMessage(chat_id, "Du verwirrst mich, hör auf damit!! Jetzt hab ich vergessen, ob die Tür offen oder zu war.")
                    bot.sendMessage(chat_id, "Versuchs bitte nochmal. Und diesmal nur mit einem Tag.")
                    save_dooropen(bool(random.getrandbits(1)))
                    return

                if i != len(txt_split) or ignoremessage or 'reply_to_message' in msg:
                    approved = []
                    rejected = []
                    for tag in tags:
                        if tag in chats:
                            if chats[tag]['id'] != chat_id:
                                approved.append(chats[tag]['name'])
                                bot.forwardMessage(chats[tag]['id'], chat_id, msg['message_id'])
                                if 'reply_to_message' in msg:
                                    bot.forwardMessage(chats[tag]['id'], chat_id, msg['reply_to_message']['message_id'])
                        elif tag in ignoretags:
                        # Stellt die Variable der Türe auf zu
                            if tag == "#zu":
                                save_dooropen(False)
                                dooropen = False
                                random_message(chat_id,
                                ("Schade das du schon gehst, ich werde die traurige Nachricht weiterleiten", "Du gehst?, what the f.", "Schame on you, wir werden dich vermissen", "Danke fürs Aufräumen und einen schönen Abend noch", "Jea alle Bierpong Becher wurden aufgeräumt, du hast die Misson erfolgerich abgeschlossen", "Wir sind sehr schade dich gehen zu sehen", "Auch die Besten müssen eines Tages einmal weiterziehen", "Captain über Board, Captain über Bort", "Auch du musst einmal schlafen, viel Glück mit dem ganzen Alkohol im Blut", "Schnell dein Bus kommt, die andern räumen das Morgen schon auf", "Das Faust und seine Mitglieder drücken hiermit unser Beileit über diesen Verlust aus", "STOP!! ist wirklich alles schon aufgeräumt? Naja, wenn nicht, dann auch egal, Soroush macht das morgen."))
                            # Stellt die Variable der Türe auf offen
                            elif tag == "#offen":
                                random_message(chat_id,
                                ("Viele Dank fürs aufmachen.", "Die anderne werden sich rießig über die Nachricht freuen. Du hast gerade das Faust aufgeschlossen", "Uhhhh Jea hiermit erkläre ich das Faust für eröffnet.", "Danke das du die Tür geöffnet hast. Sicherlich wirst du nicht lange alleine bleiben.", "Du hast soeben das Tor zur Hölle geöffnet, verusche nichts anzufassen, es ist mit Absicht nicht aufgeräumt.", "Das Kollegtiv Freundes des Faustes freut sich über ihre Teilnahme und bedankt sich für das öffnen der Tür.", "Du hat dem Faust einen großen Dienst erwiesen. Jeder sollte so fleißig Türen öffnen wie du.", "Doors open, step in.", "Türe offen, bitte Schuhe ausziehen!", "Türe offen, bitte aufjedenfall beim gehen alle Lichter und Musik anlassen, so bleibt es kuschlig für den Nächsten.", "Türe offen, die erste werden die letzten sein :)", "Türe offen, auch du hast heute schon eine gute Tat vollbracht."))
                                save_dooropen(True)
                                dooropen = True
                            # Fragt ab, ob die Tür offen ist
                            elif tag == "#tür":
                                with open('dooropen.json', 'r') as f:
                                    dooropen = json.load(f)
                                if dooropen:
                                    random_message(chat_id, ("Das Faust ist offen! Komm her und räum deinen Scheiß auf :P", "OFFEN! OFFEN! OFFEN!"))
                                else:
                                    print("Türen sind zu")
                                    bot.sendMessage(chat_id, "Das Faust ist zu. Du musst deinen Alkohol leider bei Lidl kaufen.")
                            # Fügt einen Artikel zur Einkaufsliste hinzu
                            elif tag == "#einkaufsliste":
                                shoplist.append(msg['text'][15:])
                                save_shoplist(shoplist)
                                bot.sendMessage(chat_id, "Okay, ich habe <i>" + msg['text'][14:] + "</i> zur Einkaufsliste hinzugefügt.", parse_mode="HTML")
                            # Sende eine Nachricht an jeden Schlüsselträger
                            elif tag == "#schlüssel":
                                liste = ""
                                for id in keys:
                                    liste = liste + "\n " + keys[id]
                                    bot.forwardMessage(id, chat_id, msg['message_id'])
                                    if 'reply_to_message' in msg:
                                        bot.forwardMessage(id, chat_id, msg['reply_to_message']['message_id'])

                                bot.sendMessage(chat_id, "Hey, " + msg['from']['first_name'] + "! Deine Nachricht wurde weitergelet an:" + liste)
                        else:
                            rejected.append(tag)
                    # Gibt eine Fehlernachricht, welche Tags falsch sind
                    if len(rejected) > 0:
                        bot.sendMessage(chat_id, "Ich konnte leider an folgende Tags keine Nachricht senden: <i>" + ", ".join(rejected) + "</i>" + "\nBitte benutze /hilfe oder /? um Hilfe zu bekommen", parse_mode="HTML" )
                # Gibt eine Fehlernachricht
                else:
                    bot.sendMessage(chat_id, "Leider hab ich dich nicht verstanden.\nBitte benutze /hilfe oder /? um Hilfe zu bekommen")
            # Gibt eine Fehlernachricht
            else:
                bot.sendMessage(msg['from']['id'], "Leider hab ich dich nicht verstanden.\nBitte benutze /hilfe oder /? um Hilfe zu bekommen")

bot = telepot.Bot(TOKEN)

MessageLoop(bot, handle).run_as_thread()
print('Ich lese mit ...')
# Keep the program running.
while 1:
    time.sleep(10)
