from os import write
import dearpygui.dearpygui as dpg
import ProjectClass as projClass
import json

'''
Класс работает с JSON файлом, загружает настройки в спец класс ProjectClass или сохраняет их.
'''

class Settings():

    def __init__(self) -> None:

        self.conanStorage = ""
        self.downloadFolder = ""
        self.Repository = ""
        self.OSes = None

        pass

    def loadSettings(self):
        self.projectsList = []
        with open("Settings.json") as json_data:
            data = json.load(json_data)
            self.Repository = data["Repository"]
            self.downloadFolder = data["Path"]
            self.OSes = data["OS"]
            for p in data["Projects"]:
                proj = projClass.ProjectClass(p["name"], p["folder"], p["activePath"])
                self.projectsList.append(proj)
        pass

    def SaveSettings(self, data):
        projs = []
        for p in self.projectsList:
            projs.append(p.CreateJson())
        
        jsonstr = json.dumps(data)
        with open("Settings.json", mode="w") as json_data:
            json_data.write(jsonstr)

        #вызвать перезагрузку настроек
        self.loadSettings()
        pass

    def checkActivePath(self, projName):
        for p in self.projectsList:
            if(projName == p.name):
                return [p.activePath, p.path]
                       
        return False

    def CreateSettingsDict(self):
        projs = []
        for p in self.projectsList:
            projs.append(p.CreateJson())
        d = {}
        d["Repository"] = self.Repository
        d["Path"] = self.downloadFolder
        d["OS"] = self.OSes
        d["Projects"] = projs

        return d
    
    def GetOSEnable(self, nameOS: str):
        return self.OSes[nameOS]

