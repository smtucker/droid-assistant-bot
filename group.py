"""
Droid Bot Assistant > group.py | Classes and functions for managing a tracking a group of players.
Copyright (C) Shelby Tucker 2020

This file is part of 'Droid Assistant Bot', which is released under the MIT license.
Please see the license file that was included with this software.
"""

from player import PlayerError, PlayerCharacter, CHARS, SKILLS

class TokenPool(list):
    """
    This class holds the destiny pool for the group. It inherits a list, becomes a list of strs.
    With 'Light' and 'Dark' respectively. We can thus quickly use len() and
    sum() to get info and make decisions, and list's builtin count() to get a tally.
    """
    def __init__(self, lightside = 0, darkside = 0) -> None:
        self.lightUsed = 0
        self.darkUsed = 0
        pool = list()
        pool += ['Light'] * lightside
        pool += ['Dark'] * darkside
        super().__init__(pool)

    def define(self, points: str) -> None:
        self.clear()
        points = points.lower()
        self.extend(['Light'] * points.count('l'))
        self.extend(['Dark'] * points.count('d'))

    def clear(self):
        """
        Intercept the call to list.clear() so we can also clear our custom fields.
        """
        self.lightUsed = 0
        self.darkUsed = 0
        super().clear()

    def getPoolDesc(self):
        self.sort() #Sort them all so they are in order
        self.reverse() #Then reverse so lightside is first
        message = f"[ {'-'.join(self)} ]"
        return message

    def useLightside(self):
        if self.count('Light') > 0:
            self.remove('Light')
            self.append('Dark')
            self.lightUsed +=1
            return f"Used a lightside token. There are {self.count('Light')} remaining."
        else:
            return "No lightside tokens available to be used."

    def useDarkside(self):
        if self.count('Dark') > 0:
            self.remove('Dark')
            self.append('Light')
            return f"Used a darkside token. There are {self.count('Dark')} remaining."
        else:
            return "No darkside tokens available to be used."

    def addLight(self, count: int) -> None:
        newLight = ['Light'] * count
        self += newLight

    def addDark(self, count: int) -> None:
        newDark = ['Dark'] * count
        self += newDark

class Group(dict):
    """
    Class to hold the current players and relevant group data. self.__players__ is a dict with
    the players name as the kay and the PlayerCharater class as the value.

    Eventually this should hold all the group shared data such as the 
    base of operations information and the starship. Group assets and credits.
    For now though we will use it to hold the list of players. Overkill for now
    but later on it will be good to keep it all together.
    """
    def __init__(self) -> None:
        self.destiny = TokenPool()
        self.__players__ = {}
    def __empty_check__(self) -> None:
        if len(self.__players__) < 1:
            raise PlayerError("No players loaded.")
    def add_player(self, player: PlayerCharacter) -> None:
        """
        Add a new player to the group, after making sure that it's not already loaded.
        """
        if player.name in self.__players__:
            raise PlayerError(f"Player {player.name} is already loaded. Skipping...")
        self.__players__[player.name] = player
    def remove_player(self, name: str) -> None:
        """
        Removes the player from self.__players__ while doing the needed error checking.
        """
        name = name.lower()
        try:
            del self.__players__[name]
        except KeyError:
            raise PlayerError(f"Player {name} is not loaded. Skipping...")
    def get_player(self, name: str) -> PlayerCharacter:
        """
        Returns the PlayerCharacter item saved in self.__players__ under the key of the name given.
        Same as self.__players__[name], but with error catching
        """
        name = name.lower()
        player = self.__players__.get(name)
        if player == None:
            raise PlayerError(f"No player named {name} is loaded.")
        elif isinstance(player, PlayerCharacter) == False:
            raise TypeError(f"player.Group.players[{name!r}] points to a object that is not a PlayerCharacter")
        else:
            return player
    def get_loaded_players(self) -> list:
        """
        Returns all loaded player names, Group.__players__.keys(), as a list.
        """
        self.__empty_check__()
        return list(self.__players__.keys())
    def find_highest_stat(self, stat: str) -> list:
        """
        Is given the name of the stat we want to find out which loaded
        player has the highest of and returns a formatted string for display as result.
        """
        self.__empty_check__()

        #We use the following for each type of stat result below, so def a local function.
        def inner_tied_names(players: list) -> str:
            names = list()
            for player in players:
                names.append(player.name)
            return ', '.join(names)

        stat = stat.lower()
        players = list(self.__players__.values())
        highest = players.pop(0) #Just start with the first player and work through them.
        tied = list()
        tied.append(highest)
        if stat in map(str.lower, CHARS): #It's a characteristic #TODO: Maybe optimize by check against PlayerCharacter.chars.keys()?
            for player in players:
                if player.chars[stat] > highest.chars[stat]:
                    highest = player
                    tied.clear() 
                    tied.append(highest)
                elif player.chars[stat] == highest.chars[stat]:
                    tied.append(player)
            if len(tied) == 1:
                return f"Highest {stat} is {highest.name}'s: {highest.chars[stat]}"
            else:
                result = f"Tied for highest {stat} with {highest.chars[stat]} is:\n"
                names = inner_tied_names(tied)
                return result + names
        elif stat in ['wounds', 'strain', 'encumbrance']:
            for player in players:
                #Highest should find the person most overloaded, so subtract the threshold 
                #   from the current, produce a negative and see who is closest to 0 (most maxed out)
                thisDyn = player.dynamics[stat][1] - player.dynamics[stat][0]
                highDyn = highest.dynamics[stat][1] - highest.dynamics[stat][0]
                if thisDyn > highDyn:
                    highest = player
                    tied.clear() 
                    tied.append(highest)
                elif thisDyn == highDyn:
                    tied.append(player)
            if len(tied) == 1:
                return f"Highest current {stat} is {highest.name} with: Threshold {highest.dynamics[stat][0]}, Current {highest.dynamics[stat][1]}"
            else:
                names = inner_tied_names(tied)
                result = f"Tied for highest current {stat} is: {names}\n\n"
                printout = str()
                for player in tied:
                    printout += f"{player.name}: Threshold {player.dynamics[stat][0]}, Current {player.dynamics[stat][1]}\n"
                return result + printout
        elif stat in map(str.lower, SKILLS): 
            for player in players:
                if player.skills[stat] > highest.skills[stat]: #Lexicogriphal comparison... Rank, pro, then ability.
                    highest = player
                    tied.clear() 
                    tied.append(highest)
                elif player.skills[stat] == highest.skills[stat]:
                    tied.append(player)
            if len(tied) == 1:
                return f"Highest {stat} is {highest.name}'s: Rank {highest.skills[stat][0]}, Pro {highest.skills[stat][1]}, Ability {highest.skills[stat][2]}"
            else:
                names = inner_tied_names(tied)
                result = f"Tied for highest current {stat} is: {names}\n\n"
                printout = str()
                for player in tied:
                    printout += f"{player.name}: Rank {player.skills[stat][0]}, Pro {player.skills[stat][1]}, Ability {player.skills[stat][2]}\n"
                return result + printout
        if stat in highest.general.keys(): #Genreal stats are only saved in the player.general
            for player in players:
                if player.general[stat] > highest.general[stat]:
                    highest = player
                    tied.clear() 
                    tied.append(highest)
                elif player.general[stat] == highest.general[stat]:
                    tied.append(player)
            if len(tied) == 1:
                return f"Highest {stat} is {highest.name}'s: {highest.general[stat]}"
            else:
                result = f"Tied for highest {stat} with {highest.general[stat]} is:\n"
                names = inner_tied_names(tied)
                return result + names
        if stat == 'xp': #XP is saved in both total and availible forms, but so we need to see total from highest?
            for player in players:
                if player.availableXp > highest.availableXp:
                    highest = player
                    tied.clear() 
                    tied.append(highest)
                elif player.availableXp == highest.availableXp:
                    tied.append(player)
            if len(tied) == 1:
                return f"Highest {stat} is {highest.name}'s: {highest.availableXp}"
            else:
                result = f"Tied for highest {stat} with {highest.availableXp} is:\n"
                names = inner_tied_names(tied)
                return result + names
        else:
            raise PlayerError(f"{stat} is not a valid stat.")

    def sit_rep(self) -> str:
        """
        Returns a list of formatted strings showing the medical condition of each loaded player.
        """
        self.__empty_check__()

        result = list()
        for player in self.__players__.values():
            result.append(player.sit_rep())
        return result

    def skill_dice_list(self, skill: str) -> dict:
        """
        Is passed the string of the skill to lookup for each player, and returns a 
        dict of player names to lists of ints. [Pro, Ability]. Useful for
        tabulating groups stats and checks.
        """
        self.__empty_check__()
        skill = skill.lower()
        result = dict()
        try:
            for player in self.__players__.values():
                result[player.name] = [player.skills[skill][1], player.skills[skill][2]]
            return result
        except KeyError: #TODO: this doesn't allow for custom skills that some but not all players have.
            raise PlayerError(f"Can't find skill: {skill}")

    def stat_list(self, stat: str) -> str:
        """
        Given the string name of the stat to lookup and returns a string of all the players value for said stat.
        """
        self.__empty_check__()
        result = str()
        stat = stat.lower()
        #TODO: this doesn't allow for custom skills that some but not all players have. We could use instead player.skills.keys() and etc, per player.
        if stat in ['wounds', 'strain', 'encumbrance']:
            result = self.sit_rep()
        elif stat in map(str.lower, CHARS):
            for player in self.__players__.values():
                result += f"Rank: {player.chars[stat]} - {player.name}\n"
        elif stat in map(str.lower, SKILLS):
            for player in self.__players__.values():
                result += f"Rank: {player.skills[stat][0]}, Pro: {player.skills[stat][1]}, Ability: {player.skills[stat][2]} - {player.name}\n"
        else:
            for player in self.__players__.values():
                result += player.lookup_stat(stat)
                result += '\n'
        return result

    def change_all(self, item: str, value: int) -> str:
        item = item.lower()

        message = str()
        for player in self.__players__.values():
            message += player.change(item, value)
            message += '\n'
        return message