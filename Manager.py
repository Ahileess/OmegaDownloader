'''Прослойка между GUI и бекэндом для подготовки отображаемых данных и обработки передаваемых команд. '''
import Settings
from datetime import datetime
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

        self.Repo = self.objSetting.Repository.split(';')
        self.CurrentProject = None
        self.CurrentProductName = None
        self.downloadQueue = []
        self.uninstallQueue = []
        self.history = []
        self.hashVersions = []
        self.NodeIdCount:int = 0
        self.SelectedBuild = None
        self.SelectedBrands = []

        self.userName = self.parser.GetUserName(self.Repo)

        self.ee.on("Logger", self.Logger)
        self.ee.on("ThreadEnd", self.ClearUninstallQueue)
        self.ee.on("UpdateHistory", self.HistoryList)

    def ProjectsList(self):
        lp = []
        for p in self.objSetting.projectsList:
            name_parts = p.name.split('.')
            name = name_parts[-1] if len(name_parts) > 1 else p.name
            if name not in lp:
                lp.append(name)
        return lp

    def Loadversions(self, product_name: str):
        for p in self.objSetting.projectsList:
            if p.name.endswith(product_name):
                self.CurrentProject = p
                break
        
        self.CurrentProductName = product_name

        vList = self.parser.GetVersionsList(product_name, self.Repo)

        if (len(vList) <= 0):
            return "Login Error"
        
        for node in self.hashVersions:
            if node['Name'] == product_name:
                self.hashVersions.remove(node)
        self.hashVersions.append({"Name":product_name, "vlist": vList})

        return vList

    def LoadHashversions(self, name:str):
        for p in self.objSetting.projectsList:
            if (p.name.endswith(name)):
                self.CurrentProject = p
                self.CurrentProductName = name
                break

        for node in self.hashVersions:
            if node['Name'] == name:
                return node['vlist']
        
        return ""


    def LoadBuilds(self, name: str):
        listB = []
        if self.CurrentProductName:
            # Парсер теперь возвращает уникальные строки "Product/Version+Build"
            for l in self.parser.GetBuilds(name, self.CurrentProductName):
                if l not in listB:
                    listB.append(l)
        else:
            # Fallback if CurrentProductName is not set (shouldn't happen in normal flow)
            if self.CurrentProject:
                for l in self.parser.GetBuilds(name, self.CurrentProject.name):
                    if l not in listB:
                        listB.append(l)
        return sorted(listB)
        

    def GetBrandsForBuild(self, build_ref: str):
        return self.parser.GetBrandsForBuild(build_ref)

    def LoadDistrs(self):
        """Должны знать куда скачивать, хеш, репозиторий"""
        if (len(self.downloadQueue) <= 0):
            self.ee.emit("OutputLog", "The queue is emtpy.")
            return
    
        self.ee.emit("OutputLog", "The queue started to download.")
        #Работаем с копией очереди.
        localQueue = self.downloadQueue.copy()

        self.CleareQueue()

        for ref in localQueue:
            folder = self.objSetting.downloadFolder
            if (self.objSetting.dailyFolder):
                today = datetime.now()
                folder += "\\" + today.strftime('%Y_%m_%d')

            a_idx = ref.find("/")
            projName = ref[:a_idx]

            proj = self.objSetting.checkActivePath(projName)

            if(type(proj) is bool):
                if(proj == False):
                    self.ee.emit("OutputLog", f"Download failed! Unknown name project: {projName}")
                    continue # Changed from return to continue to allow processing other items in queue

            if(proj[0]):
                folder += "\\" + proj[1]

            osActive = ""
            if (self.objSetting.GetOSEnable("Windows")):
                osActive = "Windows"
                
            if (self.objSetting.GetOSEnable("Linux")):
                if (osActive == "Windows"):
                    osActive = "Both"
                else:
                    osActive = "Linux"

            self.parser.DownloadDistrs(ref, osActive, self.Repo, folder, self.NodeIdCount)
            self.NodeIdCount += 1
                
        
    def AddItemQueue(self, build_ref, version, brands):
        if not brands:
            self.ee.emit("OutputLog", "Please select at least one brand.")
            return

        for brand in brands:
            # Construct reference: Brand.Product/Version+Build
            # Извлекаем часть продукта (после первой точки), чтобы не дублировать старый бренд
            product_name = self.CurrentProductName
            if '.' in product_name:
                product_name = product_name.split('.', 1)[1]

            # build_ref уже содержит версию и билд (например, 1.5.0+build.456)
            base_ref = f"{brand}.{product_name}/{build_ref}"
            full_ref = ""
            
            # Try to find the correct repo from self.Repo
            for repo in self.Repo:
                candidate = f"{base_ref}@{repo}"
                if candidate in self.parser.path:
                    full_ref = candidate
                    break
            
            # Fallback if not found with explicit @repo
            if full_ref == "":
                for r in self.parser.path:
                    if base_ref in r:
                        full_ref = r
                        break

            if full_ref == "":
                self.ee.emit("OutputLog", f"Unable to construct reference for {brand}.{product_name}")
                continue

            self.downloadQueue.append(full_ref)
            self.ee.emit("ShowItemQueue", full_ref)

    def AddRawReference(self, ref: str):
        """Добавляет в очередь уже готовую ссылку (например, из файла или ручного ввода)."""
        full_ref = ""
        
        # Если ссылка уже содержит репозиторий (@), принимаем её как есть.
        if "@" in ref:
            full_ref = ref
        else:
            # Пытаемся найти правильный репозиторий, если он не указан явно через @
            for repo in self.Repo:
                candidate = f"{ref}@{repo}"
                if candidate in self.parser.path:
                    full_ref = candidate
                    break
            
            # Fallback: ищем в списке путей парсера
            if full_ref == "":
                for r in self.parser.path:
                    if ref in r:
                        full_ref = r
                        break

        if full_ref == "":
            self.ee.emit("OutputLog", f"Unable to construct reference for {ref}")
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
        self.Repo = self.objSetting.Repository.split(';')


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

    def CopyInstallToClipboard(self, compName):
        self.parser.SaveInstallComponentToFile(compName, "")
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
            self.ee.emit("OutpuLog", "Error! Queue is empty!")
            return
        
        self.parser.SaveQueueToFile(self.downloadQueue, self.objSetting.downloadFolder)
        pass

    def LoadComponentFromFile(self, pathFile):
        return self.parser.LoadQueueFromFile(pathFile)

    def SaveLog(self, log):
        self.parser.SaveLogToFile(log, self.objSetting.downloadFolder)

    def GetConanStorageSize(self):
        sbytes = self.parser.ConanStorageSize()
        sbytes = ((sbytes/ 1024) / 1024) / 1024
        return sbytes

    def OpenConanStorage(self):
        self.parser.OpenExplorer(self.parser.GetConanStorage()[:-1])

    def HistoryList(self, Nodeid:int, ref:str, OS:str, active:str): 
        for node in self.history:
            if ((Nodeid == node['id']) & (OS == node['os'])):
                node['active'] = active
                self.ee.emit("UpdateHistoryOut")
                return
            
        self.history.append({"id": Nodeid, "ref": ref, "os": OS, "active": active})
        self.ee.emit("UpdateHistoryOut")
        pass
    
    def ClearHistoryList(self):
        self.history.clear()
        self.ee.emit("UpdateHistoryOut")
        pass
