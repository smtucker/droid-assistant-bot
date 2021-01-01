"""
Droid Bot Assistant > droidassistbot-tg.py | Bot for the Telegram communications app.
Copyright (C) Shelby Tucker 2020

This file is part of 'Droid Assistant Bot', which is released under the MIT license.
Please see the license file that was included with this software.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from telegram.ext import Updater
from telegram.ext import CommandHandler
import logging

from player import PlayerError, PlayerCharacter
from group import Group
from dice import (group_roll, check_roll, group_check_roll, Roll, diceLookup)

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                     level=logging.INFO)

load_dotenv()
TOKEN = os.getenv("TG-TOKEN")
CHARFOLDER = os.getenv("CHARACTER-FOLDER")
if CHARFOLDER == None:
    CHARFOLDER = Path('characters/')
else:
    CHARFOLDER = Path(CHARFOLDER)

updater = Updater(TOKEN, use_context=True)
dispatcher = updater.dispatcher

commandDescriptions = {
    "stat" : "Usage '/stat [player] [stat] ([stat]...)\nLookup the current value of a certain stat or multiple stats. Characteristics, abilites, dynamics, and general like credits or duty.",
    "stat" : "Usage '/stat [stat]\nLookup the current value of a certain stat for the whole group. Characteristics, abilites, dynamics, and general like credits or duty.",
    "initroll" : "Usage: '/initroll [stat]'\nAutomatically rolls the dice for each loaded player and list the results.",
    "highest" : "Usage: '/highest [stat]'\nFind the player with the higest stat in a given skill or characteristic.",
    "sitrep" : "Usage: '/sitrep'\nList the medical and dynamic stats for each player. Current and threshold.",
    "roll" : "Usage: '/roll [dice]'\nPerform a dice roll and show the results. Dice are the first letter of each dice's name. For ex. 'd' for difficulty dice.",
    "check" : "Usage: '/check [player] [skill] [dice]'\nPerform a dice check by automatically looking up the dice for a given player's given skill. Add the dice to check against at the end. Dice are the first letter of each dice's name. For ex. 'd' for difficulty dice.",
    "checkall" : "Usage: /checkall [skill] [dice]'\nPerform a check for all players given skill versus the supplied dice. Dice are the first letter of each dice's name. For ex. 'd' for difficulty dice.",
    "players" : "Usage: '/players'\nList all the currently loaded players.",
    "start" : "Usage: '/start'\nPrepares a new group for a new session. Clears any loaded players if any.",
    "stop" : "Usage: '/stop'\nClears the group and unloads any loaded players.",
    "load" : "Usage: '/load [file]'\nLoads a player from PDF file named [file].",
    "loadall" : "Usage '/loadall'\nScans the set player sheet folder for PDFs and attempt to load them all into the group.",
    "update" : "Usage '/update [name]'\nReloads the player matching the given name. Attemps to load the same file from before once again.",
    "modify" : "Usage '/modify [name] [stat] [modifier]\n Modify player's stat by provided value, a positive or negative number",
    "changelog" : "Usage '/changelog [name]\nShows the log of unsaved changes made to that player. Starting from most recent on.",
    "talent" : "Usage '/talent [name] (selection #, or 'all')'\nIf only the name is given it lists the talents for specified player by number. Otherwise grabs the details of the selected talent by number, or shows them 'all' in detail."
}

def error_callback(update, context):
    try:
        raise context.error
    except PlayerError as error:
        context.bot.send_message(chat_id=update.effective_chat.id, text=str(error))
    except KeyError as error:
        if error.args[0] == 'group':
            context.bot.send_message(chat_id=update.effective_chat.id, text="No group currently loaded. Try /start")
        else:
            raise #Not because the group isnt loaded so dont catch it and reraise the exception
    #TODO: Add telegram error checking

def arg_check(context, args: int) -> None:
    """Check context.args and make sure we have at least args number of... args..."""
    if len(context.args) < args:
        raise PlayerError(f"Error: Expected at least {args} arguments")

def start(update, context) -> None:
    context.bot_data['group'] = Group()
    context.bot.send_message(chat_id=update.effective_chat.id, text="New mayo jar opened...")

def stop(update, context) -> None:
    context.bot_data.clear()
    context.bot.send_message(chat_id=update.effective_chat.id, text="Mayo jar closed...")

def load_player(update, context) -> None:
    arg_check(context, 1)
    for file in context.args:
        try: #Do this inside the loop so that if we fail we can continue to try loading other players.
            file = CHARFOLDER / file
            newPlayer = PlayerCharacter(file)
            context.bot_data['group'].add_player(newPlayer)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Loaded player {newPlayer.name}")
        except PlayerError as err:
            context.bot.send_message(chat_id=update.effective_chat.id, text=str(err))

def load_all(update, context) -> None:
    for file in CHARFOLDER.glob("*.pdf"):
        try:
            newPlayer = PlayerCharacter(file)
            context.bot_data['group'].add_player(newPlayer)
            context.bot.send_message(chat_id=update.effective_chat.id, text=f"Loaded player {newPlayer.name} from {file}...")
        except PlayerError as err:
            context.bot.send_message(chat_id=update.effective_chat.id, text=str(err))


def unload_player(update, context) -> None:
    arg_check(context, 1)
    context.bot_data['group'].remove_player(context.args[0])
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Unloaded player {context.args[0]}")

def update_player(update, context) -> None:
    arg_check(context, 1)
    context.bot_data['group'].get_player(context.args[0]).update() #TODO Add new file argument
    context.bot.send_message(chat_id=update.effective_chat.id, text=f"Updated player {context.args[0]}")

    playerList = context.bot_data['group'].get_loaded_players()
    message = 'Players currently loaded: ' + ', '.join(playerList)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def list_players(update, context) -> None:
    playerList = context.bot_data['group'].get_loaded_players()
    message = f"{len(playerList)} Players currently loaded: " + ', '.join(playerList)
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def stat(update, context) -> None:
    arg_check(context, 2)
    playerName = context.args.pop(0)
    player = context.bot_data['group'].get_player(playerName)
    for arg in context.args:
        try: #Try locally so we can fail each lookup seperately instead of blowing the whole command
            result = player.lookup_stat(arg)
            context.bot.send_message(chat_id=update.effective_chat.id, text=result)
        except PlayerError as err:
            context.bot.send_message(chat_id=update.effective_chat.id, text=str(err))

def highest_stat(update, context) -> None:
    arg_check(context, 1)
    result = context.bot_data['group'].find_highest_stat(context.args[0])
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def situation_report(update, context) -> None:
    if len(context.args) == 0:
        results =  context.bot_data['group'].sit_rep()
        for result in results:
            context.bot.send_message(chat_id=update.effective_chat.id, text=result)
    else:
        for playerName in context.args:
            try: #Try locally so we can fail each lookup seperately instead of blowing the whole command
                player = context.bot_data['group'].get_player(playerName)
                result = player.sit_rep()
                context.bot.send_message(chat_id=update.effective_chat.id, text=result)
            except PlayerError as err:
                context.bot.send_message(chat_id=update.effective_chat.id, text=str(err))
            
def roll_dice(update, context) -> None:
    arg_check(context, 1)
    dice = context.args[0].lower()
    for die in dice:
        if die not in diceLookup.keys():
            raise PlayerError(f"Dice {die!r} not recognized.")
    message = f"{update.effective_user.first_name}'s roll results:\n"
    results = Roll(dice)
    message += results.description + results.breakdown
    #TODO: Other features to grab here. How to handle success or failure.
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def init_roll(update, context) -> None:
    arg_check(context, 1)
    dice = context.bot_data['group'].skill_dice_list(context.args[0])
    result = f"Rolling {context.args[0].lower()} for {len(dice)} players...\n\n"
    result += group_roll(dice)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def stat_all(update, context) -> None:
    arg_check(context, 1)
    #This feels out of order, but this order allows us to fail before we do move memory around.
    stat = context.args[0]
    stats = context.bot_data['group'].stat_list(stat)
    result = f"Looking up {stat} for the whole group...\n"
    result += stats
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def check(update, context) -> None:
    arg_check(context, 3)
    player = context.bot_data['group'].get_player(context.args[0])
    playerDice = player.skill_dice(context.args[1])
    dice = context.args[2].lower()
    for die in dice:
        if die not in 'pabcds':
            raise PlayerError(f"Dice {die!r} not recognized.")
    message = f"{player.name}'s check results:\n"
    results = check_roll(playerDice, dice)
    message += results.description + results.breakdown
    #TODO: Other features to grab here. How to handle success or failure.
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def check_all(update, context) -> None:
    arg_check(context, 2)
    checkDice = context.args[1].lower()
    for die in checkDice:
        if die not in 'pabcds':
            raise PlayerError(f"Dice {die!r} not recognized.")
    skillDice = context.bot_data['group'].skill_dice_list(context.args[0])
    result = f"Making check for {len(skillDice)} players...\n\n"
    result += group_check_roll(skillDice, checkDice)
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def help_command(update, context) -> None:
    message = ""
    if len(context.args) == 0:
        message += "Availible commands:\n"
        message += ', '.join(commandDescriptions.keys())
    else:
        command = context.args[0].lower()
        if command not in commandDescriptions.keys():
            message = f"Command {command!r} not found"
        else:
            message = commandDescriptions[command]
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def modify(update, context) -> None:
    arg_check(context, 3)
    player = context.bot_data['group'].get_player(context.args[0])
    result = player.change(context.args[1], int(context.args[2]))
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def modify_all(update, context) -> None:
    arg_check(context, 2)
    result = context.bot_data['group'].change_all(context.args[0], int(context.args[1]))
    context.bot.send_message(chat_id=update.effective_chat.id, text=result)

def changelog(update, context) -> None:
    if len(context.args) >= 1:
        for each in context.args:
            player = context.bot_data['group'].get_player(each)
            message = f"{player.name}'s changelog this session:\n\n"
            for line in player.changeLog:
                message += f"{line}\n"
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def talent(update, context) -> None:
    arg_check(context, 1)
    playerName = context.args.pop(0)
    player = context.bot_data['group'].get_player(playerName)
    if len(context.args) == 0: #None selected so grab just the names of them all.
        message = player.get_talents()
    elif context.args[0] == 'all': #They want all the details so give a detailed list.
        message = player.get_talents(-1)
    else: #They picked one, so get the details for that one
        message = player.get_talents(int(context.args[0]))
    context.bot.send_message(chat_id=update.effective_chat.id, text=message)

def destiny(update, context) -> None:
    arg_check(context, 1)
    if context.args[0].lower() == 'roll':
        playerList = context.bot_data['group'].get_loaded_players()
        playerCount = len(playerList)
        dice = 'f' * playerCount
        roll = Roll(dice)
        context.bot_data['group'].destiny.clear()
        context.bot_data['group'].destiny.addLight(roll.tally['Lightside'])
        context.bot_data['group'].destiny.addDark(roll.tally['Darkside'])
        message = f"Rolled force die for {playerCount} players:\n"
        message += context.bot_data['group'].destiny.getPoolDesc()
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    elif context.args[0].lower() == 'list':
        message = context.bot_data['group'].destiny.getPoolDesc()
        #TODO: Show tokens used
        context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    elif context.args[0].lower() == 'use':
        arg_check(context, 2)
        if context.args[1].lower() == 'light':
            message = context.bot_data['group'].destiny.useLightside()
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
        if context.args[1].lower() == 'dark':
            message = context.bot_data['group'].destiny.useDarkside()
            context.bot.send_message(chat_id=update.effective_chat.id, text=message)
    else:
        context.bot.send_message(chat_id=update.effective_chat.id, text="Unknown argument. See /help destiny")


load_handler = CommandHandler('load', load_player)
loadall_handler = CommandHandler('loadall', load_all)
unload_handler = CommandHandler('unload', unload_player)
update_handler = CommandHandler('update', update_player)
list_player_handler = CommandHandler('players', list_players)
stat_handler = CommandHandler('stat', stat)
start_handler = CommandHandler('start', start)
stop_handler = CommandHandler('stop', stop)
highest_handler = CommandHandler('highest', highest_stat)
sitrep_handler = CommandHandler('sitrep', situation_report)
roll_handler = CommandHandler('roll', roll_dice)
init_roll_handler = CommandHandler('initroll', init_roll)
stat_all_handler = CommandHandler('statall', stat_all)
check_handler = CommandHandler('check', check)
check_all_handler = CommandHandler('checkall', check_all)
help_command_handler = CommandHandler('help', help_command)
modify_handler = CommandHandler('modify', modify)
modify_all_handler = CommandHandler('modifyall', modify_all)
changelog_handler = CommandHandler('changelog', changelog)
talent_handler = CommandHandler('talent', talent)
destiny_handler = CommandHandler('destiny', destiny)
dispatcher.add_handler(load_handler)
dispatcher.add_handler(loadall_handler)
dispatcher.add_handler(unload_handler)
dispatcher.add_handler(update_handler)
dispatcher.add_handler(list_player_handler)
dispatcher.add_handler(stat_handler)
dispatcher.add_handler(start_handler)
dispatcher.add_handler(stop_handler)
dispatcher.add_handler(highest_handler)
dispatcher.add_handler(sitrep_handler)
dispatcher.add_handler(roll_handler)
dispatcher.add_handler(init_roll_handler)
dispatcher.add_handler(stat_all_handler)
dispatcher.add_handler(check_handler)
dispatcher.add_handler(check_all_handler)
dispatcher.add_handler(help_command_handler)
dispatcher.add_handler(modify_handler)
dispatcher.add_handler(modify_all_handler)
dispatcher.add_handler(changelog_handler)
dispatcher.add_handler(talent_handler)
dispatcher.add_handler(destiny_handler)

dispatcher.add_error_handler(error_callback)

updater.start_polling(poll_interval=0.5)
