'''Прослойка между GUI и бекэндом для подготовки отображаемых данных и обработки передаваемых команд. '''
import Settings
import ProjectClass as pclass
import ConanConnection as CC
from pymitter import EventEmitter

class Manager():

    def __init__(self, ee: EventEmitter) -> None:
        self.objSetting = Settings.Settings()
        self.ee = ee
        
        self.parser = CC.ConanParser(self.ee)
        self.objSetting.loadSettings()
        self.objSetting.conanStorage = self.parser.GetConanStorage()

        self.Repo = self.objSetting.Repository
        self.CurrentProject = None
        self.downloadQueue = []
        self.uninstallQueue = []

        self.userName = self.parser.GetUserName(self.Repo)

        self.ee.on("Logger", self.Logger)
        self.ee.on("ThreadEnd", self.ClearUninstallQueue)

    def ProjectsList(self):
        lp = []
        for p in self.objSetting.projectsList:
            lp.append(p.name)
        return lp

    def Loadversions(self, name: str):
        for p in self.objSetting.projectsList:
            if (p.name == name):
                self.CurrentProject = p
                pass

        vList = self.parser.GetVersionsList(name, self.Repo)

        if (len(vList) <= 0):
            return "Login Error"
        return vList

    def LoadBuilds(self, name: str):
        listB = []
        for l in self.parser.GetBuilds(name, self.CurrentProject.name):
            idx = l.find(r'/')
            listB.append(l[idx + 1:])
        return listB
        

    def LoadDistrs(self):
        """Должны знать куда скачивать, хеш, репозиторий"""
        if (len(self.downloadQueue) <= 0):
            self.ee.emit("OutputLog", "The queue is emtpy")
            return

        self.ee.emit("OutputLog", "The download started")
        for ref in self.downloadQueue:
            folder = self.objSetting.downloadFolder
            a_idx = ref.find("/")
            projName = ref[:a_idx]

            proj = self.objSetting.checkActivePath(projName)

            if(type(proj) is bool):
                if(proj == False):
                    self.ee.emit("OutputLog", "Download failed! Unknown name project!")
                    return

            if(proj[0]):
                folder += "\\" + proj[1]



            #берем инфу о необходимых ОС из настроек
            if (self.objSetting.GetOSEnable("Windows")): 
                text = self.parser.DownloadDistrs(ref, "Windows", self.Repo, folder)
                self.ee.emit("OutputLog", text)
                
            if (self.objSetting.GetOSEnable("Linux")):
                text = self.parser.DownloadDistrs(ref, "Linux", self.Repo, folder)
                self.ee.emit("OutputLog", text)
                
        
    def AddItemQueue(self, build, FullRef: bool = False):
        if (FullRef):
            self.downloadQueue.append(build[0])
            self.ee.emit("ShowItemQueue", build[0])
            return

        full_ref = ""
        for r in self.parser.path:
            if (r.rfind(build[0]) != -1):
                if (r.rfind(build[1]) != -1):
                    full_ref = r
            pass
        
        if(full_ref == ""):
            self.ee.emit("OutputLog", "Unable to add " + build + ". Not found in artifactory.")
            return

        self.downloadQueue.append(full_ref)

        self.ee.emit("ShowItemQueue", full_ref)

    def DeleteItemQueue(self, ref: str):
        if (len(self.downloadQueue) <= 0):
            return
        self.downloadQueue.remove(ref)
        self.ee.emit("RefreshQueue", self.downloadQueue)

    def CleareQueue(self):
        self.downloadQueue.clear()
        self.ee.emit("RefreshQueue", self.downloadQueue)
        pass

    def UserLogin(self, name:str, password:str):
        self.parser.login(name, password, self.Repo)
        self.userName = name
        self.ee.emit("Login")
        pass

    def GetUserName(self):
        return self.userName

#Прослойка между бэком и фронтом. Чтобы не завязываться на прямой передачи данных
#По событию в conanConnection вызывает событие в GUI.
    def Logger(self, text:str): 
        self.ee.emit("OutputLog", text)
        pass


    def OpenSettings(self):
        setDict = self.objSetting.CreateSettingsDict()

        return setDict

    def SaveSettings(self, data):
        self.objSetting.SaveSettings(data)


        self.ee.emit("ReloadProjects", True)
        pass


    def GetInstalledComponents(self):
        return self.parser.GetInstalledComponents()

    def SetUninstallComponent(self, compName):
        for i in self.parser.installedComponents:
            if(compName == i["name"]):
                self.uninstallQueue.append(compName)
                return
            
                
        self.ee.emit("OutputLog", "Component isn't installed! You're wizard!")
        pass

    def RemoveUninstallComponent(self, compName):
        try:
            self.uninstallQueue.remove(compName)
        except:
            self.ee.emit("OutputLog", "Component isn't in Queue! You're wizard!")
        pass
    
    def SaveInstallToFile(self, compName):
        self.parser.SaveInstallComponentToFile(compName, self.objSetting.downloadFolder)
        pass



    def ClearUninstallQueue(self):
        self.uninstallQueue.clear()
        self.ee.emit("RefreshInstall")
        pass

    def Uninstall(self, uninstComList):
        self.uninstallQueue = uninstComList.copy()
        self.parser.UninstallComponents(self.uninstallQueue)

    def OpenStorage(self):
        self.parser.OpenExplorer(self.objSetting.downloadFolder)
        pass

    def SaveComponentToFile(self):
        if(len(self.downloadQueue) <= 0):
            self.ee.emit("OutpuLog", "Errore! Queue is empty!")
            return
        
        self.parser.SaveQueueToFile(self.downloadQueue, self.objSetting.downloadFolder)
        pass

    def LoadComponentFromFile(self, pathFile):
        return self.parser.LoadQueueFromFile(pathFile)
