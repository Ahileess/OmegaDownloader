import os
import re
import pathlib
import shutil
import threading
import pyperclip
from pymitter import EventEmitter
from windows_tools.installed_software import get_installed_software

class ConanParser:
    
    def __init__(self, ee: EventEmitter) -> None:
        self.path = []
        self.ee = ee
        self.installedComponents =[]
        
        pass

    
    def GetVersionsList(self, projectName, reps):
        try:
            listVer =[]
            for rep in reps:
                stream = os.popen("conan search *" + projectName + "* -r " + rep)
                
                for ref in stream:
                    if(ref.find("Please log") != -1):
                        self.ee.emit("Logger", ref)
                        return []

                    if (ref.find("trei") == -1):
                        self.path.append(ref[:-1])

                    version = re.search(r'/[\dt][\w.+-]*[+.]b\d', ref)
                    if (version):
                        listVer.append(version.group()[1:-3])
                stream.close()

            self.path = list(set(self.path)) 
            result = set(listVer)
        except: 
            self.ee.emit("Logger", "Check your conan in cmd: conan search")
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
        nameRef = ref.split('/')[0]
        print("Name: ", nameRef)
        stream = os.popen("conan info " + ref + " -s os=" + OS)
        print("HASH:")
        for p in stream:
            print(p)
            if (p[:10].rfind("ID: ") != -1):
                hash = p[8:]
                pass

            if (p[:20].find("Remote:") != -1):
                rep = p.split('=')[0].split(':')[1][1:]
                print(rep)
            
            if (p[:20].find("Provides") != -1 and hash != ""):
                if (p.find(nameRef) != -1):
                    break

        stream.close()
        return [hash[:-1], rep]
        

    def DownloadDistrs(self, ref, OS, rep, target_path, NodeId):
        self.ee.emit("Logger", "Download "+ ref)
        self.threadUninst = threading.Thread(target=self.DownloadInit, args=(ref, OS, rep, target_path, NodeId))
        self.threadUninst.start()

    def DownloadInit(self, ref, osActive, rep, target_path, NodeId):
        if (osActive == "Windows"):
            self.DownloadProcess(ref, "Windows", rep, target_path, NodeId)
            return
        if (osActive == "Linux"):
            self.DownloadProcess(ref, "Linux", rep, target_path, NodeId)
            return
        if (osActive == "Both"):
            self.DownloadProcess(ref, "Windows", rep, target_path, NodeId)
            self.DownloadProcess(ref, "Linux", rep, target_path, NodeId)
            return
        pass
        
    def DownloadProcess(self, ref, OS, rep, target_path, NodeId):
        """Скачивает дистрибутив и перекладывает в нужную папку.""" 
        self.ee.emit("UpdateHistory", NodeId, ref, OS, "waiting")
        target_path = pathlib.Path(target_path)
        full_ref = ref
        self.ee.emit("Logger", "Find distr for OS:" + OS)
        if (OS not in self.CheckOSDistr(full_ref, rep)):
            self.ee.emit("Logger", full_ref + " not find distr for OS: " + OS + " in repositories")
            self.ee.emit("UpdateHistory", NodeId, full_ref, OS, "failed")
            return
        try:
            self.ee.emit("Logger", "Try to get a hash and actual repository.")
            hashAndRep = self.GetHash(full_ref, OS) 
            self.ee.emit("Logger", "Successfully received the hash and repository for " + full_ref)
            hash = hashAndRep[0]
            if (hash != ""):
                hash = ":" + hash
            self.ee.emit("Logger", "conan download " + full_ref + hash + " -r " + hashAndRep[1])
            self.ee.emit("UpdateHistory", NodeId, ref, OS, "loading")
            stream = os.popen("conan download " + full_ref + hash + " -r " + hashAndRep[1])
            for i in stream:
                if not ("Downloaded" in i or "Downloading" in i):
                    self.ee.emit("Logger", i)
                    

                if ("ERROR: Binary package not found:" in i):
                    self.ee.emit("Logger", "Binary package not found!")
                    self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
                    return
                
            stream.close()

            self.ee.emit("Logger", "Download finished: " + full_ref + " for OS: " + OS)

            pathCach = self.GetFullDistrPath(full_ref, hash)
            if (pathCach == ""):
                self.ee.emit("Logger", "Distr path wasn't find. Check your conan.")
                self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
                return 
            
            target_path.parent.mkdir(parents=True, exist_ok=True)

            print(pathCach / 'distr//msi')

            if ((pathCach / 'distr//msi').exists()):
                print("pathCach")
                shutil.copytree(pathCach/'distr//msi', target_path/'msi', dirs_exist_ok=True)
            elif ((pathCach / 'msi').exists()):
                shutil.copytree(pathCach/'msi', target_path/'msi', dirs_exist_ok=True)
            elif (OS == "Windows"):
                raise FileNotFoundError('kekl')

            if ((pathCach / 'distr//deb').exists()):
                shutil.copytree(pathCach/'distr//deb', target_path/'deb', dirs_exist_ok=True)
            elif ((pathCach / 'deb').exists()):
                shutil.copytree(pathCach/'deb', target_path/'deb', dirs_exist_ok=True)
            elif (OS == "Linux"):
                raise FileNotFoundError('kekl')

            if ((pathCach / 'distr//rpm').exists()):
                shutil.copytree(pathCach/'distr//rpm', target_path/'rpm', dirs_exist_ok=True)
            elif ((pathCach / 'rpm').exists()):
                shutil.copytree(pathCach/'rpm', target_path/'rpm', dirs_exist_ok=True)
            

        except PermissionError:
            self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
            self.ee.emit("Logger", "Permission error! Can't move the distr from conan storage.")
            return
        except FileExistsError:
            self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
            self.ee.emit("Logger", "Error! File already exists with reference: " + full_ref)
            return
        except FileNotFoundError:
            self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
            self.ee.emit("Logger", "Error! File not found with reference: " + full_ref)
            return
        except OSError:
            self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
            self.ee.emit("Logger", "Rise system error. Have a good day!")
            return
        except:
            self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
            self.ee.emit("Logger", full_ref + " for OS: " + OS + "finished with error")
            return

        self.ee.emit("UpdateHistory", NodeId, ref, OS, "done")
        self.ee.emit("Logger", full_ref + " for OS: " + OS + " has been downloaded.")
        return

    def GetFullDistrPath(self, ref:str, hash:str ):
        self.ee.emit("Logger", "Starting moving files.")
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

    def CheckOSDistr(self, ref:str, reps):
        OSList = set()
        try:
            for repo in reps:
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

    def GetUserName(self, repo):
        user = ""
        try:
            stream = os.popen("conan user")
            for s in stream:
                if (s.find(repo[0]) & s.find("Authenticated")):
                    user = re.search(r': \'\w*\'', s)[0][3:-1]

            stream.close()
        except:
            self.ee.emit("Logger", "Some problems with conan user. Check it in cmd!")

        return user

    def login(self, login:str, password: str, reps:str):
        try:
            for repo in reps:
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
                if (software['name'].find("SUER") != -1):
                    self.installedComponents.append(software)
                if (software['name'].find("AstraRegul") != -1):
                    self.installedComponents.append(software)
                if (software['name'].find("ASOKU") != -1):
                    self.installedComponents.append(software)
                if (software['name'].find("SePlatform") != -1):
                    self.installedComponents.append(software)

            self.installedComponents.sort(key=lambda x:(x["name"]))
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
            refers = ""
            for c in queue:
                idx = c.find(" ")
                if (idx == -1):
                    continue
                name = c[:idx]
                if((".Tools" in name) | (".Alarms" in name) | (".Trends" in name ) |
                ("AlphaPlatform" in name) | (".Licensing.Agent" in name )):
                    continue

                if (name.find("AccessPoint") != -1):
                    name = name.replace("AccessPoint", "Server")

                prefix = ""

                if (c.find("WebViewer") != -1):
                    prefix="-WebViewer"

                if ((".Domain" in name) | (".Security" in name) | ("HMI.Tables" in name) | 
                ("HMI.Security" in name) | ("HMI.Charts" in name)):
                    prefix += "-Distr/"
                else:
                    prefix += "-Distro/"

                var = re.search(r' [\dt].*', c)[0][1:]

                if "Alpha" in name:
                    ref = name+prefix+var+r"@automiq/build" + "\n"
                elif "SUER" in name:
                    ref = name+prefix+var+r"@suer/build" + "\n"
                elif "AstraRegul" in name: 
                    ref = name+prefix+var+r"@reglab/build" + "\n"
                elif "SePlatform" in name: 
                    ref = name+prefix+var+r"@seplatform/build" + "\n"
                elif "ASOKU" in name: 
                    ref = name+prefix+var+r"@sms-automation/build" + "\n"

                refers += ref

            if (path == ""):
                pyperclip.copy(refers)
                self.ee.emit("Logger", "Success! Copy to Clipboard.")
                return
            with open(path + r'\InstalledComponent.txt', 'w') as f:
                f.write(f"{refers}")
            self.ee.emit("Logger", "Success! File saved to " + path + r'\InstalledComponent.txt')
        except:
            self.ee.emit("Logger", "Error! File didn't save.")
        

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
        if (os.path.isfile(filePath)):
            try:
                with open(filePath, 'r') as f:
                    refs = f.readlines()
                    refs = [ref.rstrip() for ref in refs]
                self.ee.emit("Logger", "Load queue from file: " + filePath)
                return refs
            except:
                self.ee.emit("Logger", "Failed! Invalid file: " + filePath)
        return []

    def SaveLogToFile(self, log, path):
        with open(path + r'\Log.txt', 'w') as f:
            f.write(log)
        
        self.ee.emit("Logger", "Log saved to Log.txt" + path + r'\Log.txt')

    def ConanStorageSize(self):
        root_directory = pathlib.Path(self.GetConanStorage()[:-1])
        return sum(f.stat().st_size for f in root_directory.glob('**/*') if f.is_file())