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
        # 1. Попытка точного совпадения (для ссылок без префикса бренда)
        for p in self.projectsList:
            if(projName == p.name.strip()):
                return [p.activePath, p.path]
                       
        # 2. Если точного совпадения нет и в имени есть точка (префикс бренда),
        # пытаемся найти проект по части названия после последней точки (например, HMI-Distro)
        if '.' in projName:
            product_part = projName.rsplit('.', 1)[-1].strip()
            for p in self.projectsList:
                p_name = p.name.strip()
                if p_name.endswith(product_part):
                    return [p.activePath, p.path]
                       
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
        d["Projects"] = projs

        return d
    
    def GetOSEnable(self, nameOS: str):
        return self.OSes[nameOS]
