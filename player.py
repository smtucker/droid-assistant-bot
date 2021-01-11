"""
Droid Bot Assistant > player.py | Classes and functions for managing & tracking player characters.
Copyright (C) Shelby Tucker 2020

This file is part of 'Droid Assistant Bot', which is released under the MIT license.
Please see the license file that was included with this software.
"""

from os import name
from typing import NewType
from PyPDF2 import PdfFileReader, PdfFileWriter
from PyPDF2.generic import StreamObject, BooleanObject, NameObject, IndirectObject
from time import strftime, localtime
from pathlib import Path

#Create custom Exceptions so we can handle errors without catching them all.
class Error(Exception):
    """Base class for our new Exceptions"""
    pass
class PlayerError(Error):
    """General and generic Exception we can raise from here so the callers can handle
    errors from here without trying to handle something catatrophic. Saving this so
    if we need to later pass more that a basic error message we can.
    """
    pass

#Setup our own types to differentiate between them.
#   This may become irrelevant if we switch to keep stats in a class instead of a dict.
skill = NewType('SkillStat', list) #[Rank, Pro, Ability], all ints
characteristic = NewType('CharacteristicStat', int)
dynamic = NewType('DynamicStat', list) #Threshold first, current second, both ints

class Talent(object):
    """
    Class to hold talents and their parts.
    """
    def __init__(self, name = str(), rank = int(), description = str()) -> None:
        self.name = name
        self.rank = rank
        self.description = description


#Saving these here to make it easier to follow down below. Used in the update function in player classes.
CHARS=[
    'Brawn' ,
    'Agility' ,
    'Intellect' ,
    'Cunning' ,
    'Willpower' ,
    'Presence' ,
    'Force Rank' ,
    'Soak']

#Dynamics are loaded manually in PlayerCharacter.__load_dynams__()

SKILLS=[
    'Astrogation', 'Athletics', 'Charm', 'Coercion',
    'Computers', 'Cool', 'Coordination', 'Deception',
    'Discipline', 'Leadership', 'Mechanics', 'Medicine',
    'Negotiation', 'Perception', 'PilotingPlanetary',
    'PilotingSpace', 'Resilience', 'Skullduggery', 'Stealth',
    'Streetwise', 'Survival', 'Vigilance', 'Brawl', 'Gunnery',
    'Lightsaber', 'Melee', 'RangedLight', 'RangedHvy',
    'CoreWorlds', 'Education', 'Lore', 'OuterRim',
    'Underworld', 'Warfare', 'Xenology']

class PlayerCharacter(object):
    """
    Class to hold the stats and character sheet information of a player charater.
    Takes a file name to load and populate the class with the information. Saves that
    file and allows the class to be updated from it again later.
    """
    def __init__(self, fileName) -> None:
        self.fileName = fileName
        self.update()

    def __read_value__(self, data: dict) -> int:
        """
        dict.get() doesn't work for us because sometimes the key is there but it is 
        empty. This function checks to make sure the '/V' key of the passed dict 
        is there, and also if it is empty before defaulting to 0. 
        Is there a built in way to do this? If so I don't know it...
        """
        if '/V' in data:
            if data['/V'] == '':
                return 0
            else:
                return int(data['/V'])
        else:
            return 0

    def __load_chars__(self, data) -> None:
        """
        __load_chars__(data)
        Saves the characteristics of a player into self.chars, a dict with
        the name of the characteristic as the key.
        Data :  The pdf field data given by PdfFileReader.getFields()


        Characteristics are easy because we can grab them by the key name in
        the data dict, and save them by the same name. (Except the saved key is all lowercase for ease.)
        """
        self.chars = dict() #Clear it because we are reloading.
        for charName in CHARS: #Defined at the begining of the file, list of strings.
            try:
                self.chars[charName.lower()] = characteristic(self.__read_value__(data[charName])) #Convert string to our int type
            except:
                raise PlayerError(f"Error loading {charName} in {self.fileName}")

    def __load_dynams__(self, data) -> None:
        """
        __load_dynams__(data)
        Saves the dynamic artributes of a player into self.dynamics, a dict with
        the name of the dynamic as the key, and our dynamic type of list as the value.
        Data :  The pdf field data given by PdfFileReader.getFields()

        Dynamic stats are more difficult because each pair is a seperate entry in
        the data dict. (Ex. Wounds is 'WT' and 'WT Current') So grab them both
        and put them into our own list type 'dynamic', with the threshold first
        and the current count second.
        """
        self.dynamics = dict()
        try:
            self.dynamics['wounds'] = dynamic([self.__read_value__(data['WT']),
                self.__read_value__(data['WT Current'])])
            self.dynamics['strain'] = dynamic([self.__read_value__(data['ST']),
                self.__read_value__(data['ST Current'])])
            self.dynamics['encumbrance'] = dynamic([self.__read_value__(data['Worn / Generally Carried Encumberance Threshold']),
                self.__read_value__(data['Worn / Generally Carried Encumberance Current'])])
        except:
            raise PlayerError(f"Error loading dynamics in {self.fileName}")

    def __load_abilities__(self, data, pdf):
        """
        __load_abilities__(data, pdf)
        Saves the abilities of a player into self.skills, a dict with
        the name of the skill as the key, and our skill type of list as the value.
        Data :  The pdf field data given by PdfFileReader.getFields()
        pdf :   The pdf file so we can grab the indirectObjects directly
        
        Skills are the tough one. Each has a proficiency rank and ability rank. Saved seperately.
        Then the rank is based on how many of 5 checkboxes are checked.
        Our SkillStat is a list that has them in this order: Rank, pro, ability.
        So we can easily make comparisons in lexicogriphal order.
           
        To make this more difficult these aren't saved in the PDF's fields, but 
        in indirect objects in the PDF we have to retrieve seperately, which are dicts of dicts.
        Additionally, the pro and ability dice seem to be in different orders depending
        on which die exists or if there are both...
        """
        self.skills = dict()
        try:
            for skillName in SKILLS:
                newSkill = skill([0] * 3) #Fill it with blank spaces so we can assign the spaces out of order (range)
                kids = data[skillName]['/Kids'] #Grabs a list of the indirect objects
                for kid in kids:
                    obj = pdf.getObject(kid)
                    if obj['/T'] == 'Proficiency':
                        if '/V' in obj: #Can't use get, because defaulting would create length.
                            newSkill[1] = len(obj['/V']) #It has dice, so how many?
                        else:
                            newSkill[1] = 0
                    if obj['/T'] == 'Ability':
                        if '/V' in obj: #Can't use get, because defaulting would create length.
                            newSkill[2] = len(obj['/V']) #It has dice, so how many?
                        else:
                            newSkill[2] = 0
                    else: #If it's not pro or ability it's one of the rank checkboxes
                        if '/V' in obj and obj['/V'] == '/Yes':
                            newSkill[0] += 1 #For every box found checked increase rank by 1
                self.skills[skillName.lower()] = newSkill #This skill is finished, add it, all lowercase
        except:
            raise PlayerError(f"Error while parsing abilities in {self.fileName}")

    def __load_talents__(self, data) -> None:
        self.talents = list()
        for i in range(1, 37):
            newTalent = Talent()
            if '/V' not in data[f"Character Talents Name {i}"]:
                continue
            if '/V' not in data[f"Character Talents Ranks {i}"]:
                continue
            if '/V' not in data[f"Character Talents Description {i}"]:
                continue
            newTalent.name = data[f"Character Talents Name {i}"]['/V']
            try:
                newTalent.rank = int(data[f"Character Talents Ranks {i}"]['/V'])
            except ValueError: #If it's not a int, just give it rank 1 as a default
                newTalent.rank = 1
            newTalent.description = data[f"Character Talents Description {i}"]['/V']
            self.talents.append(newTalent)

    def __getChangedStr__(self, item, value, old, new) -> str:
        """
        Utility function to get a string that returns a description of how we are
        changing a stat or value
        """
        changed = f"{self.name}'s {item} still at {new}" #TODO: Lame hack to avoid a warning...
        if value == 0:
            raise PlayerError("Can't change stat by 0")
        if value > 0 :
            changed = f"{self.name}'s {item} increased from {old} to {new}" 
        if value < 0:
            changed = f"{self.name}'s {item} decreased from {old} to {new}" 
        return changed

    def update(self, fileName = None) -> None:
        """
        Parse the file and populate the character's information.
        Recieves a filename if we need to switch to a new file to load,
        otherwise it loads the file that we parsed when we initiated the class.
        """
        if fileName == None:
            fileName = self.fileName
        #Otherwise new filename was given so reload the player from a new file
        try:
            file = open(fileName, "rb")
            pdf = PdfFileReader(file)
        except FileNotFoundError:
            raise PlayerError(f"Can't find file: {fileName}")
        try:
            #Load the data. This returns a dict of dicts.
            #   See fields.txt for example data.
            data = pdf.getFields()
            #Not everyone has a single name like Moddona...
            self.fullName = data['Name']['/V']
            name = data['Name']['/V'].split()[0]
            self.name = name.lower()
            #TODO: Load the following safely...
            #self.playerName = data['Player Name']['/V']
            #self.career = data['Career']['/V']

            #TODO: Make this not suck. Assumes everyone uses proper punctuation.
            #Use get incase the overflow lines are blank so we can default without a KeyError
            #self.specializations = data['Specializations']['/V'].split(", ") + \
            #    data['Specializations2'].get('/V', '').split(", ") + \
            #    data['Specializations3'].get('/V', '').split(", ")

            #Save basic number stats in a dict named general. These can be found using
            #   lookup_stat and change, so only include viable stats.
            self.general = dict()
            self.general['credits'] = self.__read_value__(data['Personal Finances Available Credits'])
            self.general['duty'] = self.__read_value__(data['Total Duty'])

            self.availableXp = self.__read_value__(data['Available XP'])
            self.totalXp = self.__read_value__(data['Total XP'])
            
        except KeyError:
            raise PlayerError(f"Error loading general data in: {fileName}")
        self.__load_chars__(data)
        self.__load_dynams__(data)
        self.__load_abilities__(data, pdf)
        self.__load_talents__(data)

        file.close()

        self.changeLog = list()

    def save(self) -> str:
        """
        
        """

        def set_need_appearances_writer(writer: PdfFileWriter):
            # See 12.7.2 and 7.7.2 for more information: http://www.adobe.com/content/dam/acom/en/devnet/acrobat/pdfs/PDF32000_2008.pdf
            try:
                catalog = writer._root_object
                # get the AcroForm tree
                if "/AcroForm" not in catalog:
                    writer._root_object.update({NameObject("/AcroForm"): IndirectObject(len(writer._objects), 0, writer)})
                need_appearances = NameObject("/NeedAppearances")
                writer._root_object["/AcroForm"][need_appearances] = BooleanObject(True)
                # del writer._root_object["/AcroForm"]['NeedAppearances']
                return writer
            except Exception as e:
                print('set_need_appearances_writer() catch : ', repr(e))
                return writer

        try:
            oldFile = open(self.fileName, "rb")
        except:
            raise PlayerError(f"Error: Cannot open {self.fileName}")

        newPath = self.fileName.parent
        tmpPath = newPath / f"{self.name}.tmp"
        newPath = newPath / f"{self.name}.pdf"
        try:
            newFile = open (tmpPath, "wb")
        except:
            raise PlayerError(f"Error: Cannot open {tmpPath} for output")

        inPdf = PdfFileReader(oldFile)
        outPdf = PdfFileWriter()

        trailer = inPdf.trailer["/Root"]["/AcroForm"]
        outPdf._root_object.update({NameObject('/AcroForm'): trailer})

        outPdf.addPage(inPdf.getPage(0))
        #Does this really point to the inPdf?
        outPdf.updatePageFormFieldValues(inPdf.getPage(0), {'ST Current' : str(self.dynamics['strain'][1])})
        outPdf.updatePageFormFieldValues(inPdf.getPage(0), {'WT Current' : str(self.dynamics['wounds'][1])})
        outPdf.updatePageFormFieldValues(inPdf.getPage(0), {'Total XP' : str(self.totalXp)})
        outPdf.updatePageFormFieldValues(inPdf.getPage(0), {'Available XP' : str(self.availableXp)})
        outPdf.addPage(inPdf.getPage(1))
        outPdf.updatePageFormFieldValues(inPdf.getPage(1), {'Total Duty' : str(self.general['duty'])})
        outPdf.addPage(inPdf.getPage(2))
        outPdf.addPage(inPdf.getPage(3))
        outPdf.updatePageFormFieldValues(inPdf.getPage(3), {'Personal Finances Available Credits' : str(self.general['credits'])})
        set_need_appearances_writer(outPdf)
        outPdf.write(newFile)
        newFile.close()
        oldFile.close()

        #Move original to backup, using the newfile name both with '.bkp' extension
        self.fileName.replace(newPath.with_suffix('.bkp'))
        #Change file extension of new temp file.
        tmpPath.replace(newPath)

        self.changelog = list()

        return str(newPath)
    
    def lookup_stat(self, name: str) -> str:
        """
        Tries to find the stat given by name and return it's value as a formatted string
        """
        name = name.lower()
        if name in self.chars.keys():
            stat = self.chars[name]
            return f"{self.name}'s {name} is: {stat!s}"
        if name in self.dynamics.keys():
            stat = self.dynamics[name]
            return f"{self.name}'s {name} is:\nThreshold: {stat[0]!s}\nCurrent: {stat[1]!s}"
        if name in self.skills.keys():
            stat = self.skills[name]
            return f"{self.name}'s {name} is:\nRank: {stat[0]}\nProfficiency: {stat[1]}\nAbility: {stat[2]}"
        if name in self.general.keys():
            stat = self.general[name]
            return f"{self.name}'s {name} is: {stat!s}"
        if name == 'xp':
            return f"{self.name}'s Available XP is {self.availableXp}, with a total XP of {self.totalXp}"
        #If we got this far the stat it was asked us to find does not exist.
        raise PlayerError(f"Unable to find stat named {name!r}")

    def get_talents(self, index = None):
        """
        Return the information for the talent reffered to by the number given,
        if we are given -1 return a detailed list of names and details,
        if no number is given then return the name for all of them.
        """
        def formMsg(talent) -> str:
            message = str()
            message += f"[{index}] {talent.name}\n"
            message += f"Rank: {talent.rank}\n"
            message += f"Desc: {talent.description}\n\n"
            return message
        if index == None:
            index = 1
            message = str()
            for talent in self.talents:
                message += f"[{index}] {talent.name}\n"
                index += 1
        elif index == -1:
            index = 1
            message = str()
            for talent in self.talents:
                message += formMsg(talent)
                index += 1
        else:
            try:
                talent = self.talents[index - 1]
                message = formMsg(talent)
            except IndexError:
                raise PlayerError(f"No talent saved in slot #{index}")

        return message          

    def sit_rep(self) -> str:
        """
        Return a formatted string of the current dynamics health stats for the player.
        """
        report = str()
        report += f"{self.name}:\n"
        report += f"{self.dynamics['wounds'][0]}T, {self.dynamics['wounds'][1]}C < Wounds\n"
        report += f"{self.dynamics['strain'][0]}T, {self.dynamics['strain'][1]}C < Strain\n"
        report += f"{self.dynamics['encumbrance'][0]}T, {self.dynamics['encumbrance'][1]}C < Encumbrance\n"
        return report

    def skill_dice(self, skill: str) -> list:
        """
        Returns a list of haw many dice to roll for a certain stat [pro, ability]
        """
        skill = skill.lower()
        if skill not in self.skills.keys():
            raise PlayerError(f"No such skill: {skill}")
        return [self.skills[skill][1], self.skills[skill][2]]

    def change(self, item: str, value: int) -> str:
        item = item.lower()
        
        if item in self.dynamics.keys():
            oldValue = self.dynamics[item][1]
            self.dynamics[item][1] += value
            if self.dynamics[item][1] < 0:
                self.dynamics[item][1] = 0
            timestamp = strftime("%I:%M:%S | ", localtime())
            record = self.__getChangedStr__(item, value, oldValue, self.dynamics[item][1])
            self.changeLog.insert(0, timestamp + record)
            return record
        if item in self.general.keys():
            oldValue = self.general[item]
            self.general[item] += value
            timestamp = strftime("%I:%M:%S | ", localtime())
            record = self.__getChangedStr__(item, value, oldValue, self.general[item])
            self.changeLog.insert(0, timestamp + record)
            return record
        if item == 'xp':
            oldAvailXp = self.availableXp
            oldTotalXp = self.totalXp
            self.totalXp += value
            self.availableXp += value
            timestamp = strftime("%I:%M:%S | ", localtime())
            record = self.__getChangedStr__('Availible XP', value, oldAvailXp, self.availableXp)
            record2 = self.__getChangedStr__('Total XP', value, oldTotalXp, self.totalXp)
            record += '\n'
            record += record2
            self.changeLog.insert(0, timestamp + record)
            return record

        raise PlayerError(f"Unknown, or unable to change {item} for {self.name}... Stopping...")     
    
class NonPlayerCharater(object):
    """
    Class to (eventually) hold the stats and character sheet information of a non player charater.
    Takes a file name to load and populate the class with the information. Saves that
    file and allows the class to be updated from it again later.
    """
    pass
