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

    
    def GetVersionsList(self, productName, reps):
        try:
            listVer = []
            for rep in reps:
                stream = os.popen("conan search *" + productName + "* -r " + rep)
                
                for ref in stream:
                    ref = ref.strip()
                    if (ref.find("Please log") != -1):
                        self.ee.emit("Logger", ref)
                        return []

                    # Фильтрация для продукта Security-Distr: 
                    # исключаем все ссылки, содержащие "HMI.", чтобы не попадали билды HMI.Security.
                    if productName == "Security-Distr" and "HMI." in ref:
                        continue

                    if (ref.find("trei") == -1):
                        self.path.append(ref)

                    # Извлекаем версию: берем часть после первого слеша, 
                    # убираем данные после @ и отсекаем всё начиная с .b или +b + цифра
                    if '/' in ref:
                        parts = ref.split('/')
                        if len(parts) > 1:
                            version_info = parts[1]
                            if '@' in version_info:
                                version_info = version_info.split('@')[0]
                            
                            # Находим .b или +b с любой цифрой (например, .b1, +b2 и т.д.)
                            match = re.search(r'(\.b\d|\+b\d)', version_info)
                            if match:
                                # Отрезаем всё начиная с точки или плюса перед b
                                version_info = version_info[:match.start()]
                            
                            listVer.append(version_info)
                stream.close()

            self.path = list(set(self.path)) 
            result = set(listVer)
        except: 
            self.ee.emit("Logger", "Check your conan in cmd: conan search")
            return[]
        
        return sorted(list(result))

    #Ситуация говна, подгрузка другого бренда заставляет передавать сюда имя проекта, и получать список с этим именем,
    #а редактировать повторно в менеджере, удаляя имя проекта. Надо подумать, как адекватно работать с разными берндами.
    def GetBuilds(self, version: str, productName: str):
        listBuild = []
        
        for ref in self.path:
            # Проверяем наличие продукта и версии в ссылке
            if '/' in ref and "@" in ref:
                parts = ref.split('/')
                if len(parts) >= 2:
                    try:
                        product_part = parts[0] # Например, "Alpha.HMI-Distro" или "Server"
                        full_version_info = parts[1].split('@')[0] # Версия + билд + ревизия
                        
                        # Очищаем имена от суффиксов для корректного сравнения
                        comp_product_part = product_part.replace("-Distr", "").replace("-Distro", "")
                        comp_product_name = productName.replace("-Distr", "").replace("-Distro", "")

                        is_valid = False
                        # 1. Прямое совпадение (например, "Security-Distr" == "Security-Distr")
                        if comp_product_part == comp_product_name:
                            is_valid = True
                        else:
                            # 2. Проверка на формат Бренд.Продукт (например, "Alpha.HMI.Security-Distr")
                            # Теперь проверяем, заканчивается ли очищенная часть ссылки на ".ИмяПродукта"
                            # Это позволяет корректно обрабатывать продукты с точками в названии (напр. HMI.Security)
                            if comp_product_part.endswith("." + comp_product_name):
                                is_valid = True

                        if is_valid:
                            # Если эта строка начинается с нашей версии, но НЕ совпадает с ней полностью 
                            # (т.е. содержит дополнительные данные билда), значит это валидный билд
                            if full_version_info.startswith(version) and full_version_info != version:
                                # Находим первый маркер сборки/ревизии (.b или +b)
                                match = re.search(r'(\.b\d|\+b\d)', full_version_info)
                                if match:
                                    # Определяем часть строки между концом выбранной версии и началом маркера
                                    start_idx = len(version)
                                    marker_idx = match.start()
                                    extra_info = full_version_info[start_idx:marker_idx]
                                    
                                    # Если в этой части есть буквы (например, .merge или +add), 
                                    # значит это другая ветка/дополнение, и мы его игнорируем.
                                    # Цифры и дефисы разрешены как часть номера версии.
                                    if not re.search(r'[a-zA-Z]', extra_info):
                                        if full_version_info not in listBuild:
                                            listBuild.append(full_version_info)
                    except Exception:
                        continue
        return sorted(listBuild)

    def GetBrandsForBuild(self, build_ref: str, productName: str):
        """Получает список уникальных брендов для конкретного билда из уже загруженных путей."""
        brands = set()
        
        try:
            # Очищаем имя проекта от суффиксов для поиска в строке билда
            cleanProduct = productName.replace("-Distr", "").replace("-Distro", "")
            
            for ref in self.path:
                # Проверяем, содержит ли текущий путь наш билд
                if build_ref in ref:
                    # Извлекаем основную часть имени (до первого слеша) и убираем суффиксы дистрибутива
                    full_name = ref.split('/')[0]
                    base_name = full_name.replace("-Distr", "").replace("-Distro", "")
                    
                    # Находим индекс начала продукта в строке билда
                    idx = base_name.find(cleanProduct)
                    if idx != -1:
                        # Все, что до индекса — это бренд (например, "Alpha." или "ICSP.SCADA.")
                        brand = base_name[:idx].strip()
                        # Удаляем точки в конце бренда
                        brand = brand.strip('.')
                        
                        if brand:
                            brands.add(brand)
                    else:
                        # Резервный вариант на случай, если ключевое слово не найдено (старая логика rsplit)
                        parts = base_name.rsplit('.', 1)
                        if len(parts) > 1:
                            b = parts[0].strip('.')
                            if b:
                                brands.add(b)
        except Exception as e:
            self.ee.emit("Logger", f"Error getting brands for build {build_ref}: {e}")
        
        return sorted(list(brands))

    def GetHash(self, ref:str, OS="Windows"):
        hash = ""
        nameRef = ref.split('/')[0]
        self.ee.emit("Logger", f"Name: {nameRef}")
        stream = os.popen("conan info " + ref + " -s os=" + OS)
        self.ee.emit("Logger", "HASH:")
        for p in stream:
            self.ee.emit("Logger", p)
            if (p[:10].rfind("ID: ") != -1):
                hash = p[8:]
                pass

            if (p[:20].find("Remote:") != -1):
                rep = p.split('=')[0].split(':')[1][1:]
                self.ee.emit("Logger", rep)
            
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
        
        self.ee.emit("Logger", f"DEBUG: Starting download process for {full_ref} (OS: {OS})")
        
        self.ee.emit("Logger", "Find distr for OS:"+OS)
        os_distrs = self.CheckOSDistr(full_ref, rep)
        self.ee.emit("Logger", f"DEBUG: Available distrs for {full_ref}: {os_distrs}")

        if (OS not in os_distrs):
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
            print("1233")
            pathCach = self.GetFullDistrPath(full_ref, hash)
            
            if (pathCach == ""):
                self.ee.emit("Logger", "Distr path wasn't find. Check your conan.")
                self.ee.emit("UpdateHistory", NodeId, ref, OS, "failed")
                return 
            
            self.ee.emit("Logger", f"DEBUG: Cache path found: {pathCach}")
            target_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Logic for moving files
            if ((pathCach / 'distr//msi').exists() and OS == "Windows"):
                self.ee.emit("Logger", f"DEBUG: Copying msi from {pathCach / 'distr//msi'}")
                shutil.copytree(pathCach/'distr//msi', target_path/'msi', dirs_exist_ok=True)
            elif ((pathCach / 'msi').exists() and OS == "Windows"):
                self.ee.emit("Logger", f"DEBUG: Copying msi from {pathCach / 'msi'}")
                shutil.copytree(pathCach/'msi', target_path/'msi', dirs_exist_ok=True)
            elif ((pathCach / 'distr//ru-RU').exists() and OS == "Windows"):
                self.ee.emit("Logger", f"DEBUG: Copying ru-RU from {pathCach / 'distr//ru-RU'}")
                shutil.copytree(pathCach/'distr//ru-RU', target_path/'msi', dirs_exist_ok=True)
            elif ((pathCach / 'distr').exists() and OS == "Windows"):
                self.ee.emit("Logger", f"DEBUG: Copying distr from {pathCach / 'distr'}")
                shutil.copytree(pathCach/'distr', target_path/'msi', dirs_exist_ok=True)
            elif (OS == "Windows"):
                raise FileNotFoundError('kekl')

            if ((pathCach / 'distr//deb').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying deb from {pathCach / 'distr//deb'}")
                shutil.copytree(pathCach/'distr//deb', target_path/'deb', dirs_exist_ok=True)
            elif ((pathCach / 'deb').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying deb from {pathCach / 'deb'}")
                shutil.copytree(pathCach/'deb', target_path/'deb', dirs_exist_ok=True)
            elif ((pathCach / 'distr').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying distr from {pathCach / 'distr'}")
                shutil.copytree(pathCach/'distr', target_path/'deb', dirs_exist_ok=True)
            elif ((pathCach / 'distr//ru-RU').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying ru-RU from {pathCach / 'distr//ru-RU'}")
                shutil.copytree(pathCach/'distr//ru-RU', target_path/'deb', dirs_exist_ok=True)
            elif (OS == "Linux"):
                raise FileNotFoundError('kekl')

            if ((pathCach / 'distr//rpm').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying rpm from {pathCach / 'distr//rpm'}")
                shutil.copytree(pathCach/'distr//rpm', target_path/'rpm', dirs_exist_ok=True)
            elif ((pathCach / 'rpm').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying rpm from {pathCach / 'rpm'}")
                shutil.copytree(pathCach/'rpm', target_path/'rpm', dirs_exist_ok=True)
            elif ((pathCach / 'distr').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying distr from {pathCach / 'distr'}")
                shutil.copytree(pathCach/'distr', target_path/'rpm', dirs_exist_ok=True)
            elif ((pathCach / 'distr//ru-RU').exists() and OS == "Linux"):
                self.ee.emit("Logger", f"DEBUG: Copying ru-RU from {pathCach / 'distr//ru-RU'}")
                shutil.copytree(pathCach/'distr//ru-RU', target_path/'rpm', dirs_exist_ok=True)
            
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
                ("AlphaPlatform" in name) | (".Licensing.Agent" in name) ):
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
