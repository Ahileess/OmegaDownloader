import os
import re
import pathlib
import shutil
import threading
from pymitter import EventEmitter
from windows_tools.installed_software import get_installed_software

class ConanParser:
    
    def __init__(self, ee: EventEmitter) -> None:
        self.path = []
        self.ee = ee
        self.installedComponents =[]
        
        pass

    
    def GetVersionsList(self, projectName, rep: str):
        try:
            stream = os.popen("conan search *" + projectName + "* -r " + rep)
            listVer =[]
            for ref in stream:
                if(ref.find("Please log") != -1):
                    self.ee.emit("Logger", ref)
                    return []

                if (ref.find("trei") == -1):
                    self.path.append(ref[:-1])

                version = re.search(r'/\d[\w.+-]*[+.]b\d', ref)
                if (version):
                    listVer.append(version.group()[1:-3])

            self.path = list(set(self.path))    
            result = set(listVer)
            stream.close()
        except: 
            self.ee.emit("Logger", "Check your conan in cmd: " + "\'conan search *" + projectName + "* -r " + rep + "\'")
            return[]

        return sorted(list(result))

    #Ситуация говна, подгрузка другого бренда заставляет передавать сюда имя проекта, и получать список с этим именем,
    #а редактировать повторно в менеджере, удаляя имя проекта. Надо подумать, как адекватно работать с разными берндами.
    def GetBuilds(self, version: str, projName: str):
        str = projName + r'/' + version.replace("+", "\+") + r'[+.]b[\w]*[.]r\w*@'
        listBuild = []
        for ref in self.path:
            
            build = re.search(str, ref)
            if (build):
                listBuild.append(build.group()[1:-1])
        return sorted(listBuild)

    def GetHash(self, ref:str, OS="Windows"):
        hash = ""
        if(ref.find("DevStudio") != -1):
            return "b71407595d7f34acb3447ec985d93306edf56b75"
        stream = os.popen("conan info " + ref + " -s os=" + OS)
        print("HASH:")
        for p in stream:
            if (p[:10].rfind("ID: ") != -1):
                print(p)
                hash = p[8:]
                pass

        stream.close()
        return hash[:-1]
        

    def DownloadDistrs(self, ref, OS, rep, target_path):
        """Скачивает дистрибутив и перекладывает в нужную папку."""

        target_path = pathlib.Path(target_path)
        full_ref = ref
        
        if (OS not in self.CheckOSDistr(full_ref, rep)):
            return str.format(full_ref + " not find distr for OS: " + OS + " in repo: " + rep)
        try:
            hash = self.GetHash(full_ref, OS)
            if (hash != ""):
                hash = ":" + hash
            self.ee.emit("Logger", "conan download " + full_ref + hash + " -r " + rep)
            stream = os.popen("conan download " + full_ref + hash + " -r " + rep)
            for i in stream:
                self.ee.emit("Logger", i) #Провести валидацию на сообщение "ERROR: Binary package not found:"
                
            stream.close()

            self.ee.emit("Logger", "Download finished: " + full_ref + " for OS: " + OS)

            pathCach = self.GetFullDistrPath(full_ref, hash)
            if (pathCach == ""):
                return "Distr path wasn't find. Check your conan."
            
            target_path.parent.mkdir(parents=True, exist_ok=True)

            print(pathCach / 'distr//msi')

            if ((pathCach / 'distr//msi').exists()):
                print("pathCach")
                shutil.copytree(pathCach/'distr//msi', target_path/'msi', dirs_exist_ok=True)
            elif ((pathCach / 'msi').exists()):
                shutil.copytree(pathCach/'msi', target_path/'msi', dirs_exist_ok=True)

            if ((pathCach / 'distr//deb').exists()):
                shutil.copytree(pathCach/'distr//deb', target_path/'deb', dirs_exist_ok=True)
            elif ((pathCach / 'deb').exists()):
                shutil.copytree(pathCach/'deb', target_path/'deb', dirs_exist_ok=True)

            if ((pathCach / 'distr//rpm').exists()):
                shutil.copytree(pathCach/'distr//rpm', target_path/'rpm', dirs_exist_ok=True)
            elif ((pathCach / 'rpm').exists()):
                shutil.copytree(pathCach/'rpm', target_path/'rpm', dirs_exist_ok=True)
        except PermissionError:
            return "Permission error! Can't move the distr from conan storage."
        except FileExistsError:
            return "Error! File already exists with reference: " + full_ref
        except FileNotFoundError:
            return "Error! File not found with reference: " + full_ref
        except OSError:
            return "Rise system error. Have a good day!"
        except:
            return full_ref + " for OS: " + OS + "finished with error"

        return full_ref + " for OS: " + OS + " has been downloaded."

    def GetFullDistrPath(self, ref:str, hash:str ):
        print("Ref: " + ref + " Hash: " + hash)
        try:
            cachDir = pathlib.Path(self.GetConanStorage()[:-1])
            a_idx = ref.rfind('@')
            cachDir /= ref[:a_idx]
            cachDir /= ref [a_idx+1:]
            cachDir /= 'package'
            cachDir /= hash[1:]

            print ("cache: ")
            print(cachDir)

            conan_link = cachDir / ".conan_link"
            if conan_link.exists():
                cachDir = pathlib.Path(conan_link.read_text(encoding="utf-8"))
        except:
            self.ee.emit("Logger", "The path to distr is invalid. Reference: " + ref + ":" + hash)
            return ""
        return cachDir

    def GetConanStorage(self):
        p = ""
        try:
            stream = os.popen("conan config get storage.path")
            for path in stream:
                if (path != ""):
                    p = path
            stream.close()
        except:
            self.ee.emit("Logger", "Error conan config get storage.path. Check your conan")
            return ""

        return p

    def CheckOSDistr(self, ref:str, repo:str):
        OSList = set()
        try:
            stream = os.popen("conan search " + ref + " -r " + repo)
            for s in stream:
                if(s.find("Windows") != -1):
                    OSList.add("Windows")
                elif (s.find("Linux") != -1):
                    OSList.add("Linux")
                
            stream.close()

        except:
            self.ee.emit("Logger", "Didn't work \'conan search " + ref + " -r " + repo + "\'")
            return set()

        return OSList

    def GetUserName(self, repo: str):
        user = ""
        try:
            stream = os.popen("conan user")
            for s in stream:
                if (s.find(repo) & s.find("Authenticated")):
                    user = re.search(r': \'\w*\'', s)[0][3:-1]

            stream.close()
        except:
            self.ee.emit("Logger", "Some problems with conan user. Check it in cmd!")

        return user

    def login(self, login:str, password: str, repo:str):
        try:
            if (password == ""):
                stream = os.popen("conan user " + login + " -r " + repo)
            else:
                stream = os.popen("conan user " + login + " -p " + password + " -r " + repo)
            for i in stream:
                self.ee.emit("Logger", i)

            stream.close()
        except:
            self.ee.emit("Logger", "Some problems with \"conan user login\". Check it in cmd!")
        pass

    def GetInstalledComponents(self):
        self.installedComponents.clear()
        try:
            for software in get_installed_software():
                if (software['name'].find("Alpha") != -1):
                    self.installedComponents.append(software)
        except:
            self.ee.emit("Logger", "Some problems with rights! Open soft with admin rights.")

        
        return self.installedComponents

    def UninstallComponents(self, listComponents:list):
        self.ee.emit("Logger", "Start uninstall!")
        self.threadUninst = threading.Thread(target=self.UninstallProcess, args=(listComponents,))
        self.threadUninst.start()
        
    
    def UninstallProcess(self, listComponents:list):
        for i in listComponents:
            counter = 0
            self.ee.emit("Logger", "Uninstall " + i)
            stream = os.popen("wmic product where name=\"" + i + "\" call uninstall /nointeractive")
            for s in stream:
                counter += 1
                self.ee.emit("Logger", f"{counter}0%")
            self.ee.emit("Logger", "Uninstall " + i + " finished")
        self.ee.emit("Logger", "Unistall Finished!")
        self.ee.emit("ThreadEnd")
        pass


    def SaveInstallComponentToFile(self, queue, path):
        try:
            with open(path + r'\InstalledComponent.txt', 'w') as f:
                for c in queue:
                    idx = c.find(" ")
                    if (idx == -1):
                        continue
                    name = c[:idx]
                    if((name == "Alpha.Tools") | (name == "Alpha.Alarms") | (name == "Alpha.Trends") |
                    (name == "AlphaPlatform") | (name == "Alpha.Licensing.Agent")):
                        continue

                    if (name.find("AccessPoint") != -1):
                        name = name.replace("AccessPoint", "Server")

                    prefix = ""

                    if (c.find("WebViewer") != -1):
                        prefix="-WebViewer"

                    if ((name == "Alpha.Domain") | (name == "Alpha.Security") | (name == "Alpha.HMI.Tables") | 
                    (name == "Alpha.HMI.Security") | (name == "Alpha.HMI.Charts")):
                        prefix += "-Distr/"
                    else:
                        prefix += "-Distro/"

                    var = re.search(r' [\dt].*', c)[0][1:]
                    ref = name+prefix+var+r"@automiq/build"
                    f.write(f"{ref}\n")
            self.ee.emit("Logger", "Success! File was save!")
        except:
            self.ee.emit("Logger", "Error! File didn't save.")
        pass

    def OpenExplorer(self, path):
        try:
            stream = os.popen("explorer " + path)
            stream.close()
            pass
        except:
            self.ee.emit("Logger", "Can't open explorer!")
            pass
    
    def SaveQueueToFile(self, queue, path):
        with open(path + r'\References.txt', 'w') as f:
            for ref in queue:
                f.write(f"{ref}\n")
        self.ee.emit("Logger", "Save queue to file: " + path + r'\References.txt')
        pass

    def LoadQueueFromFile(self, filePath):
        with open(filePath, 'r') as f:
            refs = f.readlines()
            refs = [ref.rstrip() for ref in refs]
        self.ee.emit("Logger", "Load queue from file: " + filePath)
        return refs
