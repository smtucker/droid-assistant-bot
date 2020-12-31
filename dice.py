"""
Droid Bot Assistant > dice.py | Classes and functions for virtual dice rolling.
Copyright (C) Shelby Tucker 2020

This file is part of 'Droid Assistant Bot', which is released under the MIT license.
Please see the license file that was included with this software.
"""

from random import randrange
from collections import Counter

class Dice(str):
    def __new__(cls, sides): #Recieve all the possible sides from the inherited class.
        side = sides[randrange(len(sides))] #Every time a new dice is created Dice.side points to the rolled result.
        return super(Dice, cls).__new__(cls, side)
        #self.data = self.sides[randrange(len(self.sides))]

class ProDice(Dice):
    def __new__(cls):
        cls.sides = ['','a','aa','aa','s','s','ss','ss','sa','sa','sa','x'] #Triumph is 'x', 't' is for threat
        return super().__new__(cls, cls.sides)

class AbilityDice(Dice):
    def __new__(cls):
        cls.sides = ['','a','a','aa','s','s','sa','ss']
        return super().__new__(cls, cls.sides)

class DiffDice(Dice):
    def __new__(cls):
        cls.sides = ['','t','t','t','tt','tf','f','ff']
        return super().__new__(cls, cls.sides)

class ChalDice(Dice):
    def __new__(cls):
        cls.sides = ['','t','t','tt','tt','f','f','tf','tf','ff','ff','d']
        return super().__new__(cls, cls.sides)

class BoostDice(Dice):
    def __new__(cls):
        cls.sides = ['','','a','as','aa','s']
        return super().__new__(cls, cls.sides)

class SetBackDice(Dice):
    def __new__(cls):
        cls.sides = ['','','t','t','f','f']
        return super().__new__(cls, cls.sides)

class ForceDice(Dice):
    def __new__(cls):
        #b for darkside, l for lightside
        cls.sides = ['b', 'b', 'b', 'b', 'b', 'b', 'l', 'l', 'll', 'll', 'll', 'bb']
        return super().__new__(cls, cls.sides)

diceLookup = {'p' : ProDice, 'a' : AbilityDice, 'd' : DiffDice, 'c' : ChalDice,
            'b' : BoostDice, 's' : SetBackDice, 'f' : ForceDice}

resultLookupName = {'a' : 'Advantage', 's' : 'Success', 'd' : 'Dispair', 'x' : 'Triumph',
            't' : 'Threat', 'f' : 'Failure', 'b' : 'Darkside', 'l' : 'Lightside'}

class Roll(list):
    def __init__(self, dice: str) -> None:
        for die in dice:
            self.append(diceLookup[die]())
        result = str()
        for die in self:
            result += die
        self.string = result
        self.tally = Counter()
        for letter in result:
            self.tally[resultLookupName[letter]] += 1
        self.success = self.tally['Success'] + self.tally['Triumph'] > self.tally['Failure'] + self.tally['Dispair']
        self.threat = self.tally['Threat'] > self.tally['Advantage']
        self.advantage = self.tally['Advantage'] > self.tally['Threat']
        self.description = ''
        self.description += f"{'SUCCEEDED' if self.success else 'FAILED'} "
        if self.threat:
            self.description += f"with {self.tally['Threat'] - self.tally['Advantage']} threat"
        if self.advantage:
            self.description += f"with {self.tally['Advantage'] - self.tally['Threat']} advantage"
        self.breakdown = f"\nTriumph: {self.tally['Triumph']}, Success: {self.tally['Success']}, Advantage: {self.tally['Advantage']},\n" + \
            f"Dispair: {self.tally['Dispair']}, Failure: {self.tally['Failure']}, Threat: {self.tally['Threat']}" 
        if 'f' in dice:
            self.breakdown += f"\nLightside: {self.tally['Lightside']}, Darkside: {self.tally['Darkside']}"

def check_roll(skillDice: list, checkDice: str) -> Roll:
    """
    Returns a roll using dice depending on the list give for a players skill in [pro, ability] form,
    in combination with a str holding the rest of the dice to check against.
    """
    hand = ''
    hand += 'p' * skillDice[0]
    hand += 'a' * skillDice[1]
    hand += checkDice
    roll = Roll(hand)
    return roll

#TODO: Clean the mess outta these next two little guys... 
def group_roll(groupDiceList: dict) -> str:
    """
    This function is given the results of Player.Group.skill_dice_list(). Which is a dict of player names to a specific skill, [pro, ability].
    It rolls the amount of dice each player has in that skill and returns a formatted string with the results.
    """
    rolls = dict()
    for player in groupDiceList:
        hand = ''
        hand += 'p' * groupDiceList[player][0]
        hand += 'a' * groupDiceList[player][1]
        rolls[player] = Roll(hand)
    result = str()
    for name in rolls: 
        result += f"T: {rolls[name].tally['Triumph']} | S: {rolls[name].tally['Success']} | A: {rolls[name].tally['Advantage']} ({name})\n"
    return result

def group_check_roll(groupDiceList: dict, checkDice: str) -> str:
    rolls = dict()
    for player in groupDiceList:
        hand = checkDice
        for x in range(groupDiceList[player][0]):
            hand += 'p'
        for x in range(groupDiceList[player][1]):
            hand += 'a'
        rolls[player] = Roll(hand)
    result = str()
    for name in rolls: 
        result += f"{name}: {rolls[name].description}\n"
    return result