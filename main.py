#!/usr/bin/env python3

import os
import re
from random import randint
import discord

DISCORD_TOKEN = os.environ.get('DISCORD_TOKEN')
COMMAND_PREFIX = '/vtm5e'
RE_MATCH = rf'^\{COMMAND_PREFIX}\s(\d+)\s(\d+)\s(\d+)$'
DICE_FAILURE = 1
DICE_SUCCESS = 6
DICE_CRITICAL = 10

def usage():
    return 'Usage:\n```/vtm5e <integer_dice_pool> <integer_hunger_pool> <integer_difficulty>```\nExample: ```/vtm5e 5 2 3```'

def validate_command(command):
    return bool(re.match(RE_MATCH, command))

def parse_args(command):
    re_groups = re.match(RE_MATCH, command)
    return [re_groups[1], re_groups[2], re_groups[3]]

def sort_dice(extra_args):
    dice_sorted = {'black_pool': {'count': int(extra_args[0])}, 'red_pool': {'count': int(extra_args[1])}, 'difficulty': int(extra_args[2])}
    dice_sorted['recalculated_black_pool'] = dict()
    dice_sorted['recalculated_black_pool']['count'] = max(dice_sorted['black_pool']['count'] - dice_sorted['red_pool']['count'], 0)
    dice_sorted['recalculated_red_pool'] = dict()
    dice_sorted['recalculated_red_pool']['count'] = min(dice_sorted['black_pool']['count'], dice_sorted['red_pool']['count'])
    return dice_sorted

def roll_dice(dice_sorted):
    dice_rolled = dice_sorted
    dice_rolled['recalculated_black_pool']['rolls'] = list()
    for black_roll in range(dice_rolled['recalculated_black_pool']['count']):
        dice_rolled['recalculated_black_pool']['rolls'].append(randint(1, 10))
    dice_rolled['recalculated_red_pool']['rolls'] = list()
    for red_roll in range(dice_rolled['recalculated_red_pool']['count']):
        dice_rolled['recalculated_red_pool']['rolls'].append(randint(1, 10))
    return dice_rolled

def calculate_dice(dice_rolled):
    dice_calculated = dice_rolled
    dice_calculated['recalculated_black_pool']['criticals'] = sum(1 for roll in dice_calculated['recalculated_black_pool']['rolls'] if roll >= DICE_CRITICAL)
    dice_calculated['recalculated_red_pool']['criticals'] = sum(1 for roll in dice_calculated['recalculated_red_pool']['rolls'] if roll >= DICE_CRITICAL)
    dice_calculated['criticals'] = dice_calculated['recalculated_black_pool']['criticals'] + dice_calculated['recalculated_red_pool']['criticals']
    dice_calculated['recalculated_red_pool']['failures'] = sum(1 for roll in dice_calculated['recalculated_red_pool']['rolls'] if roll <= DICE_FAILURE)
    dice_calculated['recalculated_black_pool']['successes'] = sum(1 for roll in dice_calculated['recalculated_black_pool']['rolls'] if roll >= DICE_SUCCESS)
    dice_calculated['recalculated_red_pool']['successes'] = sum(1 for roll in dice_calculated['recalculated_red_pool']['rolls'] if roll >= DICE_SUCCESS)
    dice_calculated['successes'] = dice_calculated['recalculated_black_pool']['successes'] + dice_calculated['recalculated_red_pool']['successes'] + (dice_calculated['criticals'] // 2 * 2)
    return dice_calculated

def evaluate_dice(calculated_dice):
    dice_evaluated = calculated_dice
    if dice_evaluated['successes'] < dice_evaluated['difficulty'] and dice_evaluated['recalculated_red_pool']['failures'] > 0:
        dice_evaluated['outcome'] = "messy failure :japanese_ogre: :thumbsdown:"
    elif dice_evaluated['successes'] >= dice_evaluated['difficulty'] and dice_evaluated['criticals'] >= 2 and dice_evaluated['recalculated_red_pool']['criticals'] > 0:
        dice_evaluated['outcome'] = "messy critical success :japanese_ogre: :boom:"
    elif dice_evaluated['successes'] >= dice_evaluated['difficulty'] and dice_evaluated['criticals'] >= 2:
        dice_evaluated['outcome'] = "critical success :boom:"
    elif dice_evaluated['successes'] >= dice_evaluated['difficulty'] and dice_evaluated['criticals'] < 2:
        dice_evaluated['outcome'] = "success :thumbsup:"
    else:
        dice_evaluated['outcome'] = "failure :thumbsdown:"
    return dice_evaluated

def format_response(dice_evaluated):
    response_formatted = str()
    response_formatted += "black: {}\n".format(', '.join(list(map(str, [roll if roll >= DICE_SUCCESS else "~~{}~~".format(roll) for roll in dice_evaluated['recalculated_black_pool']['rolls']]))))
    response_formatted += "red: {}\n".format(', '.join(list(map(str, [roll if roll >= DICE_SUCCESS else "~~{}~~".format(roll) for roll in dice_evaluated['recalculated_red_pool']['rolls']]))))
    response_formatted += f"successes: {dice_evaluated['successes']} / {dice_evaluated['difficulty']}\n"
    response_formatted += f"outcome: {dice_evaluated['outcome']}"
    return response_formatted

def process_command(command):
    args_parsed = parse_args(command)
    dice_sorted = sort_dice(args_parsed)
    dice_rolled = roll_dice(dice_sorted)
    dice_calculated = calculate_dice(dice_rolled)
    dice_evaluated = evaluate_dice(dice_calculated)
    return format_response(dice_evaluated)

client = discord.Client()

@client.event
async def on_message(message):
    if COMMAND_PREFIX not in message.content:
        return
    if message.author == client.user:
        return
    if not validate_command(message.content):
        await message.channel.send(usage())
    else:
        response = process_command(message.content)
        await message.channel.send(response)

if DISCORD_TOKEN:
    client.run(DISCORD_TOKEN)
else:
    print('DISCORD_TOKEN not found in env')