from audioop import add
from cgitb import enable
from email.policy import default
from gc import callbacks
from heapq import heappush
from subprocess import call
from turtle import color, title, width
from typing import List
import dearpygui.dearpygui as dpg
from pymitter import EventEmitter
from Manager import Manager
""" 
parser = CC.ConanParser()
VersionList = parser.GetVersionsList("Alpha.Server-Distro")


def ShowBuilds(sender, app_data, user_data):
    BuildingsList = parser.GetBuildings(str(user_data))
    with dpg.window(label="Tutorial"):
        with dpg.table(header_row=False, row_background=True,
                    borders_innerH=True, borders_outerH=True, borders_innerV=True,
                    borders_outerV=True):

            dpg.add_table_column()

            for p in BuildingsList:
                with dpg.table_row():
                    with dpg.table_cell():
                        dpg.add_button(label=p)
def ShowVersions(sender, app_data, user_data):
    with dpg.window(label="Tutorial"):
        with dpg.table(header_row=False, row_background=True,
                    borders_innerH=True, borders_outerH=True, borders_innerV=True,
                    borders_outerV=True,  tag="but"):

            dpg.add_table_column()

            for p in VersionList:
                with dpg.table_row():
                    with dpg.table_cell():
                        dpg.add_button(label=p, callback=ShowBuilds, user_data=p)

"""

class GUIManager( ):
    def __init__(self, mng: Manager, eventEmit:EventEmitter) -> None:
        self.WindowManager = []
        self.DeleteComponentList = []
        self.DeleteQueueItems = []
        self.mng = mng
        self.ee = eventEmit
        self.listVersions = ""

        self.ee.on("ShowItemQueue", self.ShowItemQueue)
        self.ee.on("RefreshQueue", self.RefreshQueue)
        self.ee.on("Login", self.RefreshLogin)
        self.ee.on("OutputLog", self.Logger)
        self.ee.on("ReloadProjects", self.LoadProjects)
        self.ee.on("RefreshInstall", self.GetInstalledComponents)
        
        #dpg.configure_app(docking=True, docking_space=False) TODO: Пока не сделают нормальный докинг, выключаем в dpg
        pass

    def MainWindow(self):
        with dpg.window(label="Main", tag="MainWindow"):
            with dpg.menu_bar():
                dpg.add_separator()
                with dpg.menu(label="File"):
                    dpg.add_menu_item(label="Settings", callback=self.OpenSettings)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Exit")
                dpg.add_separator()
                with dpg.menu(label="Options"):
                    dpg.add_menu_item(label="Save Queue", callback=self.SaveToFile)
                    dpg.add_separator()
                    dpg.add_menu_item(label="Load Queue", callback=lambda: dpg.show_item("fileDialog"))
                    dpg.add_separator()
                    dpg.add_menu_item(tag="InstCompMenu", label="Installed Components", callback=self.GetInstalledComponents)
                    dpg.add_separator()
                dpg.add_separator()
                dpg.add_menu_item(label="Storage", callback=self.OpenStorage)
                dpg.add_separator()
                


            with dpg.group(horizontal=True):
                with dpg.child_window(width=200, height=600):
                    with dpg.child_window(height=65):
                        with dpg.group(tag="LoginPanel"):
                            dpg.add_input_text(tag="outputLogin", enabled=False, width=-1)
                            dpg.add_button(tag="loginButton", label="login", callback=lambda: dpg.configure_item("loginWindow", show=True))

                    with dpg.child_window():
                        with dpg.group(tag="LeftPanelGroup"):
                            pass


                with dpg.child_window(width=300, height=600):
                    with dpg.group(tag="MidPanelGroup"):
                        dpg.add_input_text(tag="FilterField", label="Filter", callback=self.FilterVersions, width=-45)
                        with dpg.table(header_row=False, row_background=True,
                            borders_innerH=True, borders_outerH=False, borders_innerV=True,
                            borders_outerV=False, tag="VersionsTable"):
                            
                            dpg.add_table_column(label="Versions")
                            pass       


                with dpg.child_window(width=-1, height=600):
                    with dpg.group(tag="RightPanelGroup"):
                        with dpg.group(tag="Queue"):
                            pass
                        
                        with dpg.group():
                            dpg.add_separator()
                            with dpg.group(horizontal=True):
                                dpg.add_input_text(tag="AddManualItemQueue", no_spaces=True, height=-100)
                                dpg.add_button(label="Add", callback=self.ManualAddItemQueue)
                        with dpg.group(horizontal=True):
                            dpg.add_button(label="Download",callback=self.LoadDistrs)
                            dpg.add_button(label="Clear", callback=self.ClearQueue)
                        

            with dpg.group():
                with dpg.child_window(tag="OutputLogger", height=-2):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="Logger")
                        dpg.add_button(label="Clear", callback=lambda: dpg.set_value("log_out", ""))
                        dpg.add_text(tag="IndiLabel" ,default_value="Download ", show=False)
                        dpg.add_loading_indicator(tag="Loggerindi", style=1, radius=2, circle_count=10, show=False, color=(255,255,255,255))

                    dpg.add_separator()
                    with dpg.child_window(tag="above_log_out", width=-1, horizontal_scrollbar=True):
                        dpg.add_text(tag="log_out")
                    pass

        self.RefreshLogin()

        #Окно Логина
        with dpg.window(label="Login", tag="loginWindow", modal=True, width=300, height=150, show=False):
            with dpg.group():
                li = dpg.add_input_text(label="login", tag="LoginInput")
                pi = dpg.add_input_text(label="password", password=True, tag="PasswordInput")
                dpg.add_button(label="OK", tag="OkButton", callback=self.Login)
                dpg.add_button(label="Cancel", callback=lambda: dpg.configure_item("loginWindow", show=False))
        
        #Окно ошибки Логина
        with dpg.window(tag="LoginErrorPopup", label="Error Conan login", modal=True, width=300, height=100, show=False):
            with dpg.group():
                dpg.add_text(default_value="Please login with valid credentionals")
                dpg.add_button(label="Close", callback=lambda: dpg.configure_item("LoginErrorPopup", show=False))


        #Окно настроек
        with dpg.window(tag="SettingsWindow", label="Settings", modal=True, show=False, width=500, height=500, no_close=True):
            with dpg.child_window(tag="Conan settings", height=130, no_scrollbar=True):
                with dpg.group():
                    dpg.add_input_text(label="Conan repository", tag="RepoOut")
                    dpg.add_input_text(label="Download Folder", tag="PathOut")
                    with dpg.group():
                        dpg.add_checkbox(label="Windows", tag="checkWindowsOut")
                        dpg.add_checkbox(label="Linux", tag="checkLinuxOut")
            with dpg.child_window(tag="ProjectsWindowOut", height=-35):
                dpg.add_button(label="Add Project", tag="AddProjButton", callback=self.AddNewInputProject)
            with dpg.group(horizontal=True, horizontal_spacing=10):
                dpg.add_button(label="OK", callback=self.SaveSettings, width=50, height=25)
        
        #Окно установленных компонентов
        with dpg.window(tag="InstalledComponent", label="Installed Component", show=False, width=500, height= 500):
            dpg.add_button(tag="RefreshUninst", label="Refresh", callback=self.GetInstalledComponents)
            with dpg.child_window():
                with dpg.group(tag="InstalledList"):
                    pass
        
        with dpg.file_dialog(tag="fileDialog", directory_selector=False, show=False, callback=self.LoadFromFile, width=600, height=600):
            dpg.add_file_extension(".txt", color=(150, 255, 150, 255), custom_text="[Text]")



        #Описание темы для UI
        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, (67, 71, 80), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, (255,255,255), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (188,184,175), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, (35,34,33), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, (45,44,43), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Separator, (188,184,175), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (44,51,55), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, (0,0,0), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, (158,160,162), category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (133,135,138), category=dpg.mvThemeCat_Core)


                dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 12, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_CellPadding, x=3, y=5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, x=7, y=10, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_ScrollbarSize, 15, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_FrameBorderSize, 1, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_WindowTitleAlign, x=0.5, y=0.5, category=dpg.mvThemeCat_Core)
                dpg.add_theme_style(dpg.mvStyleVar_TabRounding, 12, category=dpg.mvThemeCat_Core)
                
        dpg.bind_theme(global_theme)
    
    def LoadProjects(self, reload: bool = False):
        if (reload):
            for b in dpg.get_item_children("LeftPanelGroup", 1):
                dpg.delete_item(b)

        listProjs = self.mng.ProjectsList()
        for p in listProjs:
            dpg.add_button(label=p, parent="LeftPanelGroup", callback=self.LoadVersions, user_data=p)
        pass

    def LoadVersions(self, sender, app_data, user_data):
        self.listVersions = []
        dpg.set_value("FilterField", "")
        loader = dpg.add_loading_indicator(before="VersionsTable", circle_count=10, secondary_color=(43,198,245,255), color=(250,250,255,255))
        self.Logger("Load versions for " + user_data)
        dpg.hide_item("VersionsTable")
        self.listVersions = self.mng.Loadversions(user_data)

        rows = dpg.get_item_children("VersionsTable", 1)
        for row in rows:
            dpg.delete_item(row)

        if (self.listVersions == "Login Error"):
            dpg.configure_item("LoginErrorPopup", show=True)
            dpg.delete_item(loader)
            dpg.show_item("VersionsTable")
            return

            
        for p in self.listVersions:
                with dpg.table_row(tag=p, parent="VersionsTable"):
                    with dpg.table_cell():
                        dpg.add_button(label=p, callback=self.LoadBuilds, user_data=p)

        dpg.delete_item(loader)
        dpg.show_item("VersionsTable")
        self.Logger("Finish download versions for " + user_data)
        pass

    def FilterVersions(self):
        if (self.listVersions == "Login Error"):
            return

        filter = dpg.get_value("FilterField")

        if (filter == ""):
            for i in self.listVersions:
                dpg.configure_item(i, show=True)
            return

        for i in self.listVersions:
            if (i.find(filter) == -1):
                dpg.configure_item(i, show=False)
            else:
                dpg.configure_item(i, show=True)
        pass



    def LoadBuilds(self, sender, app_data, user_data):
        BuildingsList = self.mng.LoadBuilds(user_data)
        uuid = dpg.generate_uuid()
        buttonsBuild = []
        mousepos = dpg.get_mouse_pos()
        mousepos[0] += 200
        with dpg.window(label=user_data, pos=mousepos, height=390):
            
            with dpg.table(tag = uuid, header_row=False, row_background=True,
                        borders_innerH=True, borders_outerH=True, borders_innerV=True,
                        borders_outerV=True):
                dpg.add_table_column()

                for p in BuildingsList:
                    rowuuid = dpg.generate_uuid()
                    buttonsBuild.append({"Uid": rowuuid, "Label": p})
                    with dpg.table_row(tag=rowuuid):
                        with dpg.table_cell():
                            (dpg.add_button(label=p, callback=self.AddItemQueue, user_data=[p, self.mng.CurrentProject.name]))
        
        dpg.add_input_text(before=uuid, callback=self.FilterBuilds, user_data=buttonsBuild, width=-5)
        pass

    def FilterBuilds(self, sender, app_data, user_data):
        filter = dpg.get_value(sender)

        if (filter == ""):
            for i in user_data:
                dpg.configure_item(i["Uid"], show=True)
            return

        for i in user_data:
            lbl = i["Label"]
            if (lbl.find(filter) == -1):
                dpg.configure_item(i["Uid"], show=False)
            else:
                dpg.configure_item(i["Uid"], show=True)
        pass
    
    def LoadDistrs(self, sender, app_data, user_data):
        dpg.configure_item("Loggerindi", show=True)
        dpg.configure_item("IndiLabel", show=True)
        for x in self.DeleteQueueItems:
            dpg.configure_item(x, show=False)
        
        self.mng.LoadDistrs()
        self.ClearQueue(sender, app_data, user_data)

        dpg.configure_item("Loggerindi", show=False)
        dpg.configure_item("IndiLabel", show=False)
    
    def ManualAddItemQueue(self, sender, app_data, user_data):
        ref = dpg.get_value("AddManualItemQueue")
        if(ref.find("/build") == -1):
            self.ee.emit("OutputLog", "Invalid reference wasn't added")
        else:
            self.mng.AddItemQueue([ref, ""], True)
        
        dpg.set_value("AddManualItemQueue", "")
    
    def AddItemQueue(self, sender, app_data, user_data):
        self.mng.AddItemQueue(user_data)
        pass

    def ShowItemQueue(self, ref:str, error:str = ""):
        self.DeleteQueueItems.clear()
        with dpg.group(parent="Queue", horizontal=True):
            self.DeleteQueueItems.append(
                dpg.add_button(label='X', width=20, height=20, callback=self.DeleteItemQueue, user_data=ref)
            )

            size = dpg.get_text_size(ref)[0] + 20
            dpg.add_input_text(default_value=ref, enabled=False, width=size)

    def DeleteItemQueue(self, sender, app_data, user_data):
        self.mng.DeleteItemQueue(user_data)
        pass

    def ClearQueue(self, sender, app_data, user_data):
        self.mng.CleareQueue()
        pass
    
    def RefreshQueue(self, queue: List):
        try:
            rows = dpg.get_item_children("Queue", 1)
            for n in rows:
                dpg.delete_item(n)

            if(len(queue) > 0):
                for i in queue:
                    self.ShowItemQueue(i)
        except:
            pass    

    def OpenSettings(self, sender, app_data, user_data):
        self.SettingsID = []
        setDict = self.mng.OpenSettings()
        dpg.set_value("RepoOut", setDict["Repository"])
        dpg.set_value("PathOut", setDict["Path"])

        OSes = setDict["OS"]
        windows = OSes["Windows"]
        linux = OSes["Linux"]

        dpg.set_value("checkWindowsOut", windows)
        dpg.set_value("checkLinuxOut", linux)

        projs = setDict["Projects"]

        for p in projs:
            t = []
            with dpg.group(before="AddProjButton"):
                t.append(dpg.add_input_text(label="Name", default_value=p["name"]))
                t.append(dpg.add_input_text(label="Custom Path", default_value=p["folder"]))
                t.append(dpg.add_checkbox(label="Enable Custom Path", default_value=p["activePath"]))
                t.append(dpg.add_button(label="X", width=20, height=20, callback=self.DeleteProjectSettings, before=t[0]))
                t.append(dpg.add_separator(before=t[3]))
            self.SettingsID.append(t)
                
        dpg.configure_item("SettingsWindow", show=True)
        pass
    
    def DeleteProjectSettings(self, sender, app_data, user_data):
        for i in self.SettingsID:
            if (sender in i):
                for e in i:
                    dpg.delete_item(e)
                self.SettingsID.remove(i)
        
        pass

    def Logger(self, text:str):
        dpg.set_value("log_out", dpg.get_value("log_out") + "\n" + text)

        with dpg.mutex():
            max_scroll = dpg.get_y_scroll_max("above_log_out")
            dpg.set_y_scroll("above_log_out", max_scroll+1)

        pass

    def AddNewInputProject(self, sender, app_data, user_data):
        data =[]
        with dpg.group(before="AddProjButton"):
            data.append(dpg.add_input_text(label="Name"))
            data.append(dpg.add_input_text(label="Custom Path"))
            data.append(dpg.add_checkbox(label="Enable Custom Path"))
            data.append(dpg.add_button(label="X", width=20, height=20,  callback=self.DeleteProjectSettings, before=data[0]))
            data.append(dpg.add_separator(before=data[3]))
            self.SettingsID.append(data)
        pass
    
    def SaveSettings(self, sender, app_data, user_data):
        projs = []
        for p in self.SettingsID:
            projs.append({"name":dpg.get_value(p[0]), "folder":dpg.get_value(p[1]), "activePath":dpg.get_value(p[2])})

        d = {}
        d["Repository"] = dpg.get_value("RepoOut")
        d["Path"] = dpg.get_value("PathOut")
        d["OS"] = {"Windows": dpg.get_value("checkWindowsOut"), "Linux": dpg.get_value("checkLinuxOut")}
        d["Projects"] = projs

        self.mng.SaveSettings(d)

        for i in dpg.get_item_children("ProjectsWindowOut", 1):
            if (dpg.get_item_alias(i) != "AddProjButton"):  
                dpg.delete_item(i)

        self.SettingsID = []

        dpg.configure_item("SettingsWindow", show=False)
        
        pass

    def Login(self, sender, app_data, user_data):
        self.mng.UserLogin(dpg.get_value("LoginInput"), dpg.get_value("PasswordInput"))
        dpg.configure_item("loginWindow", show=False)
        pass
        

    def RefreshLogin(self):
        dpg.set_value("outputLogin", self.mng.GetUserName())
        pass
    
    def GetInstalledComponents(self, sender="", app_data="", user_data=""):
        self.DeleteComponentList.clear()
        iComp = self.mng.GetInstalledComponents()

        if(len(iComp) <= 0):
            return

        dpg.delete_item("InstalledList", children_only=True)

        for comp in iComp:
            with dpg.group(parent="InstalledList", horizontal=True, horizontal_spacing=30):
                dpg.add_text(default_value=comp["name"] + " : " + comp["version"])
                dpg.add_checkbox(label="Delete", callback=self.SetUnistallQueue, user_data=comp["name"])
            dpg.add_separator(parent="InstalledList")
        with dpg.group(horizontal=True, parent="InstalledList"):
            dpg.add_button(label="Delete", callback=self.UninstallComponents)
            dpg.add_button(tag="SaveInstComp", label="Save", callback=self.SaveInstallComponentToFile)
        dpg.configure_item("InstalledComponent", show=True)
        dpg.configure_item("RefreshUninst", enabled=True)
        dpg.configure_item("InstCompMenu", enabled=True)
        dpg.configure_item("SaveInstComp", enabled=True)
        pass

    def SetUnistallQueue(self, sender, app_data, user_data):
        if (dpg.get_value(sender)):
            self.DeleteComponentList.append(user_data)
        else:
            self.DeleteComponentList.remove(user_data)
        pass

    def UninstallComponents(self, sender, app_data, user_data):
        if (len(self.DeleteComponentList) > 0):
            dpg.configure_item(sender, enabled=False)
            dpg.configure_item("RefreshUninst", enabled=False)
            dpg.configure_item("InstCompMenu", enabled=False)
            dpg.configure_item("SaveInstComp", enabled=False)
            self.mng.Uninstall(self.DeleteComponentList)
            self.DeleteComponentList.clear()
        else:
            self.ee.emit("OutputLog", "Uninstall Queue is empty!")


    def SaveInstallComponentToFile(self, sender, app_data, user_data):
        if (len(self.DeleteComponentList) > 0):
            self.mng.SaveInstallToFile(self.DeleteComponentList)
        else:
            self.ee.emit("OutputLog", "Uninstall Queue is empty!")
        pass

    def OpenStorage(self):
        self.mng.OpenStorage()
        pass

    def SaveToFile(self):
        self.mng.SaveComponentToFile()
        pass


    def LoadFromFile(self, sender, app_data):
        pathFile = app_data['file_path_name']
        listRefs = self.mng.LoadComponentFromFile(pathFile)
        for r in listRefs:
            self.mng.AddItemQueue([r, ""], True)
        pass


    def Run(self):
        self.MainWindow()
        self.LoadProjects()
        pass