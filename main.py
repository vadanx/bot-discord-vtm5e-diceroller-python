#!/usr/bin/env python3

import os
import re
from random import randint
import discord

DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
COMMAND_PREFIX = '/r'
RE_MATCH = rf'^\{COMMAND_PREFIX}\s(\d+)\s(\d+)\s(\d+)$'
FAILURE = 1
SUCCESS = 6
CRITICAL = 10


def usage():
    return """Usage: `/vtm5e <integer_dice_pool> <integer_hunger_pool> <integer_difficulty>`\nExample: `/vtm5e 5 2 3`"""


def validate_command(command):
    return bool(re.match(RE_MATCH, command))


def parse_args(command):
    re_groups = re.match(RE_MATCH, command)
    return [re_groups[1], re_groups[2], re_groups[3]]


def sort_dice(extra_args):
    dice_sorted = {
        'black_pool': {
            'count': int(extra_args[0])
        },
        'red_pool': {
            'count': int(extra_args[1])
        },
        'difficulty': int(extra_args[2])
    }
    dice_sorted['recalc_b_pool'] = dict()
    dice_sorted['recalc_b_pool']['count'] = max(
        dice_sorted['black_pool']['count'] - dice_sorted['red_pool']['count'],
        0
    )
    dice_sorted['recalc_r_pool'] = dict()
    dice_sorted['recalc_r_pool']['count'] = min(
        dice_sorted['black_pool']['count'],
        dice_sorted['red_pool']['count']
    )
    return dice_sorted


def roll_dice(dice_sorted):
    dice_rolled = dice_sorted
    dice_rolled['recalc_b_pool']['rolls'] = list()
    for black_roll in range(dice_rolled['recalc_b_pool']['count']):
        dice_rolled['recalc_b_pool']['rolls'].append(randint(1, 10))
    dice_rolled['recalc_r_pool']['rolls'] = list()
    for red_roll in range(dice_rolled['recalc_r_pool']['count']):
        dice_rolled['recalc_r_pool']['rolls'].append(randint(1, 10))
    return dice_rolled


def calculate_dice(dice_rolled):
    dice_calc = dice_rolled
    dice_calc['recalc_b_pool']['crits'] = sum(
        1 for roll in dice_calc['recalc_b_pool']['rolls'] if roll >= CRITICAL
    )
    dice_calc['recalc_r_pool']['crits'] = sum(
        1 for roll in dice_calc['recalc_r_pool']['rolls'] if roll >= CRITICAL
    )
    dice_calc['crits'] = sum(
        [
            dice_calc['recalc_b_pool']['crits'],
            dice_calc['recalc_r_pool']['crits']
        ]
    )
    dice_calc['recalc_r_pool']['fails'] = sum(
        1 for roll in dice_calc['recalc_r_pool']['rolls'] if roll <= FAILURE
    )
    dice_calc['recalc_b_pool']['successes'] = sum(
        1 for roll in dice_calc['recalc_b_pool']['rolls'] if roll >= SUCCESS
        )
    dice_calc['recalc_r_pool']['successes'] = sum(
        1 for roll in dice_calc['recalc_r_pool']['rolls'] if roll >= SUCCESS
        )
    dice_calc['successes'] = sum(
        [
            dice_calc['recalc_b_pool']['successes'],
            dice_calc['recalc_r_pool']['successes'],
            (dice_calc['crits'] // 2 * 2)
        ]
    )
    return dice_calc


def evaluate_dice(calculated_dice):
    dice_evaluated = calculated_dice
    successes = dice_evaluated['successes']
    difficulty = dice_evaluated['difficulty']
    red_failures = dice_evaluated['recalc_r_pool']['fails']
    criticals = dice_evaluated['crits']
    red_criticals = dice_evaluated['recalc_r_pool']['crits']
    if successes < difficulty and red_failures > 0:
        dice_evaluated['outcome'] = "messy failure 👹 👎"
    elif successes >= difficulty and criticals >= 2 and red_criticals > 0:
        dice_evaluated['outcome'] = "messy critical success 👹 💥"
    elif successes >= difficulty and criticals >= 2:
        dice_evaluated['outcome'] = "critical success 💥"
    elif successes >= difficulty and criticals < 2:
        dice_evaluated['outcome'] = "success 👍"
    else:
        dice_evaluated['outcome'] = "failure 👎"
    return dice_evaluated


def format_response(dice_evaluated):
    response_formatted = str()
    b_pool = dice_evaluated['recalc_b_pool']['rolls']
    r_pool = dice_evaluated['recalc_r_pool']['rolls']
    successes = dice_evaluated['successes']
    difficulty = dice_evaluated['difficulty']
    outcome = dice_evaluated['outcome']
    response_formatted += "black: {}\n".format(
        ', '.join(
            list(
                map(
                    str,
                    [d if d >= SUCCESS else "~~{}~~".format(d) for d in b_pool]
                )
            )
        )
    )
    response_formatted += "red: {}\n".format(
        ', '.join(
            list(
                map(
                    str,
                    [d if d >= SUCCESS else "~~{}~~".format(d) for d in r_pool]
                )
            )
        )
    )
    response_formatted += f"successes: {successes} / {difficulty}\n"
    response_formatted += f"outcome: {outcome}"
    return response_formatted


client = discord.Client()


@client.event
async def on_message(message):
    if message.author.id == client.user.id:
        return
    if not message.content.startswith(COMMAND_PREFIX):
        return
    elif not validate_command(message.content):
        await message.reply(
            usage(),
            mention_author=True
        )
    else:
        args_parsed = parse_args(message.content)
        dice_sorted = sort_dice(args_parsed)
        dice_rolled = roll_dice(dice_sorted)
        dice_calc = calculate_dice(dice_rolled)
        dice_evaluated = evaluate_dice(dice_calc)
        await message.reply(
            format_response(dice_evaluated),
            mention_author=True
        )


client.run(DISCORD_TOKEN)
