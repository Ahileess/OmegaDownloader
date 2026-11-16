from os import write
import os
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
        self.dailyFolder = False
        self.projectsList = []
        
        # Тема инициализируется пустой, так как дефолты теперь в GUI.py
        self.theme = {}

        pass

    def loadSettings(self):
        if (os.path.isfile("Settings.json")):
            self.projectsList = []
            with open("Settings.json") as json_data:
                data = json.load(json_data)
                self.Repository = data["Repository"]
                self.downloadFolder = data["Path"]
                if "Daily" in data:
                    self.dailyFolder = data["Daily"]
                self.OSes = data["OS"]
                
                # Загружаем тему из файла, если она там есть
                if "Theme" in data:
                    self.theme = data["Theme"]
                
                for p in data["Projects"]:
                    proj = projClass.ProjectClass(p["name"], p["folder"], p["activePath"])
                    self.projectsList.append(proj)
        else:
            d = {}
            d["Repository"] = "Automiq;Automiq2"
            d["Path"] = "C:\\"
            d["Daily"] = False
            d["OS"] = {"Windows": True, "Linux": False}
            d["Projects"] = []
            # При создании нового файла тема будет пустой (GUI.py подставит свои дефолты)
            d["Theme"] = self.theme
            self.SaveSettings(d)
        pass

    def SaveSettings(self, data):
        jsonstr = json.dumps(data)
        with open("Settings.json", mode="w+") as json_data:
            json_data.write(jsonstr)

        #вызвать перезагрузку настроек
        self.loadSettings()
        pass

    def checkActivePath(self, projName):
        projName = projName.strip()
        best_match = None
        # Ищем наилучшее совпадение (наиболее специфичное имя проекта)
        for p in self.projectsList:
            p_name = p.name.strip()
            # Исправлено: проверяем, содержится ли проект из настроек в строке ссылки 
            # (так как ссылка может содержать префикс бренда, например "Alpha.HMI.Security-Distr")
            if p_name in projName:
                if best_match is None or len(p_name) > len(best_match.name):
                    best_match = p
                       
        if best_match:
            return [best_match.activePath, best_match.path]
                       
        return False

    def CreateSettingsDict(self):
        projs = []
        for p in self.projectsList:
            projs.append(p.CreateJson())
        d = {}
        d["Repository"] = self.Repository
        d["Path"] = self.downloadFolder
        d["Daily"] = self.dailyFolder
        d["OS"] = self.OSes
        d["Theme"] = self.theme
        d["Projects"] = projs

        return d
    
    def GetOSEnable(self, nameOS: str):
        return self.OSes[nameOS]
