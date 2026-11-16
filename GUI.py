from typing import List
import dearpygui.dearpygui as dpg
from pymitter import EventEmitter
from Manager import Manager


class GUIManager( ):
    def __init__(self, mng: Manager, eventEmit:EventEmitter) -> None:
        
        # Сначала инициализируем основные объекты
        self.mng = mng
        self.ee = eventEmit

        # Получаем тему из настроек
        theme = self.mng.objSetting.theme
        
        # Если тема пустая (например, при первом запуске), заполняем её дефолтными значениями из GUI.py
        if not theme:
            self.mng.objSetting.theme = {
                "COLOR_HASH_BTN": (32, 164, 71),
                "COLOR_NO_HASH_BTN": (67, 71, 80),
                "COLOR_CHILD_BG": (37, 35, 40),
                "COLOR_TEXT": (255, 255, 255),
                "COLOR_BORDER": (188, 184, 175),
                "COLOR_TABLE_ROW_BG": (35, 34, 33),
                "COLOR_TABLE_ROW_BG_ALT": (45, 44, 43),
                "COLOR_SEPARATOR": (188, 184, 175),
                "COLOR_FRAME_BG": (44, 51, 55),
                "COLOR_BORDER_SHADOW": (0, 0, 0),
                "COLOR_BORDER_LIGHT": (158, 160, 162),
                "COLOR_WINDOW_BG": (133, 135, 138),
                "COLOR_TITLE_BG_COLLAPSED": (63, 70, 138),
                "COLOR_TITLE_BG": (0, 116, 131, 213),
                "COLOR_TITLE_BG_ACTIVE": (14, 100, 179),
                "COLOR_CHECKMARK": (255, 255, 255)
            }
            # Обновляем локальную переменную theme после заполнения
            theme = self.mng.objSetting.theme

        self.COLOR_HASH_BTN = theme.get("COLOR_HASH_BTN")
        self.COLOR_NO_HASH_BTN = theme.get("COLOR_NO_HASH_BTN")
        self.COLOR_CHILD_BG = theme.get("COLOR_CHILD_BG")
        self.COLOR_TEXT = theme.get("COLOR_TEXT")
        self.COLOR_BORDER = theme.get("COLOR_BORDER")
        self.COLOR_TABLE_ROW_BG = theme.get("COLOR_TABLE_ROW_BG")
        self.COLOR_TABLE_ROW_BG_ALT = theme.get("COLOR_TABLE_ROW_BG_ALT")
        self.COLOR_SEPARATOR = theme.get("COLOR_SEPARATOR")
        self.COLOR_FRAME_BG = theme.get("COLOR_FRAME_BG")
        self.COLOR_BORDER_SHADOW = theme.get("COLOR_BORDER_SHADOW")
        self.COLOR_BORDER_LIGHT = theme.get("COLOR_BORDER_LIGHT")
        self.COLOR_WINDOW_BG = theme.get("COLOR_WINDOW_BG")
        self.COLOR_TITLE_BG_COLLAPSED = theme.get("COLOR_TITLE_BG_COLLAPSED")
        self.COLOR_TITLE_BG = theme.get("COLOR_TITLE_BG")
        self.COLOR_TITLE_BG_ACTIVE = theme.get("COLOR_TITLE_BG_ACTIVE")
        self.COLOR_CHECKMARK = theme.get("COLOR_CHECKMARK")

        self.WindowManager = []
        self.DeleteComponentList = []
        self.DeleteQueueItems = []
        self.listVersions = ""
        self.listHashAvailable = []
        self.brandCheckboxes = {} # Changed to dict to support multiple windows
        self.window_data = {}     # To store build/version per window tag
        self.current_build_ref = ""
        self.is_loading = False

        self.load_queue = []
        self.project_buttons = {}

        self.ee.on("ShowItemQueue", self.ShowItemQueue)
        self.ee.on("RefreshQueue", self.RefreshQueue)
        self.ee.on("Login", self.RefreshLogin)
        self.ee.on("OutputLog", self.Logger)
        self.ee.on("ReloadProjects", self.LoadProjects)
        self.ee.on("RefreshInstall", self.GetInstalledComponents)
        self.ee.on("UpdateHistoryOut", self.UpdateHistory)
        
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
                    with dpg.menu(label="Conan storage"):
                        dpg.add_menu_item(label="Size", callback=self.ConanStorageSize)
                        dpg.add_separator()
                        dpg.add_menu_item(label="Open explorer", callback=self.OpenConanStorage)
                        dpg.add_separator()
                dpg.add_separator()
                dpg.add_menu_item(label="Save Queue", callback=self.SaveToFile)
                dpg.add_separator()
                dpg.add_menu_item(label="Load Queue", callback=self.ShowFileDialog)
                dpg.add_separator()
                dpg.add_menu_item(tag="InstCompMenu", label="Installed Components", callback=self.GetInstalledComponents)
                dpg.add_separator()
                
                dpg.add_menu_item(label="Open storage", callback=self.OpenStorage)
                dpg.add_separator()
                

            with dpg.group(horizontal=True):
                with dpg.child_window(width=450, height=600):
                    with dpg.child_window(height=65):
                        with dpg.group(tag="LoginPanel"):
                            dpg.add_input_text(tag="outputLogin", enabled=False, width=-1)
                            dpg.add_button(tag="loginButton", label="login", callback=lambda: dpg.configure_item("loginWindow", show=True))

                    with dpg.child_window(horizontal_scrollbar=True):
                        with dpg.group(tag="LeftPanelGroup"):
                            pass


                with dpg.child_window(width=350, height=600):
                    with dpg.group(tag="MidPanelGroup"):
                        # Фильтр теперь в отдельной группе сверху с фиксированной высотой
                        with dpg.child_window(height=40):
                            dpg.add_input_text(tag="FilterField", label="Filter", callback=self.FilterVersions, width=-45)
                        
                        # Таблица версий теперь в child_window, который занимает всё оставшееся место
                        with dpg.child_window(height=-1):
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
                        

            with dpg.group(horizontal=True):
                with dpg.child_window(tag="OutputLogger", height=-2, width=500):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="Logger")
                        dpg.add_button(label="Save", callback=self.SaveLog)
                        dpg.add_button(label="Clear", callback=lambda: dpg.set_value("log_out", ""))

                    dpg.add_separator()
                    with dpg.child_window(tag="above_log_out", width=-1):
                        dpg.add_text(tag="log_out", wrap=0, tracked=True, track_offset=1)
                        
                with dpg.child_window(tag="History", height=-2, width=-1):
                    with dpg.group(horizontal=True):
                        dpg.add_text(default_value="History")
                        dpg.add_button(label="Clear", callback=self.ClearHistory)
                        dpg.add_text(tag="IndiLabel", default_value="Download ", show=False)
                        dpg.add_loading_indicator(tag="IndiLoad", radius=2, circle_count=10, show=False, color=(255,255,255,255), secondary_color=(43,198,245,255))

                    dpg.add_separator()
                    with dpg.child_window(tag="above_history", width=-1):
                        dpg.add_input_text(tag="history_out", track_offset=1, multiline=True, height=-1, readonly=True)

                    
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
            with dpg.child_window(tag="Conan settings", height=160, no_scrollbar=True):
                with dpg.group():
                    dpg.add_input_text(label="Conan repository", tag="RepoOut")
                    dpg.add_input_text(label="Download Folder", tag="PathOut")
                    dpg.add_checkbox(label="Daily", tag="DailyOut")
                    dpg.add_separator()
                    with dpg.group():
                        dpg.add_checkbox(label="Windows", tag="checkWindowsOut")
                        dpg.add_checkbox(label="Linux", tag="checkLinuxOut")
            with dpg.child_window(tag="ProjectsWindowOut", height=-35):
                with dpg.group(tag="ProjectsWindowOutGroup", horizontal=True, horizontal_spacing=10):
                    dpg.add_button(label="Add Project", tag="AddProjButton", callback=self.AddNewInputProject)
                    dpg.add_button(label="Add Separator", tag="AddSepButton", callback=self.AddNewSeparator)
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
        with dpg.theme() as self.hash_btn_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.COLOR_HASH_BTN, category=dpg.mvThemeCat_Core)

        with dpg.theme() as self.no_hash_btn_theme:
            with dpg.theme_component(dpg.mvButton):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.COLOR_NO_HASH_BTN, category=dpg.mvThemeCat_Core)

        with dpg.theme() as global_theme:
            with dpg.theme_component(dpg.mvAll):
                dpg.add_theme_color(dpg.mvThemeCol_Button, self.COLOR_NO_HASH_BTN, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_ChildBg, self.COLOR_CHILD_BG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Text, self.COLOR_TEXT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, self.COLOR_BORDER, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBg, self.COLOR_TABLE_ROW_BG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TableRowBgAlt, self.COLOR_TABLE_ROW_BG_ALT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Separator, self.COLOR_SEPARATOR, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_FrameBg, self.COLOR_FRAME_BG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_BorderShadow, self.COLOR_BORDER_SHADOW, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_Border, self.COLOR_BORDER_LIGHT, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_WindowBg, self.COLOR_WINDOW_BG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgCollapsed, self.COLOR_TITLE_BG_COLLAPSED, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBg, self.COLOR_TITLE_BG, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_TitleBgActive, self.COLOR_TITLE_BG_ACTIVE, category=dpg.mvThemeCat_Core)
                dpg.add_theme_color(dpg.mvThemeCol_CheckMark, self.COLOR_CHECKMARK, category=dpg.mvThemeCat_Core)


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
            children = dpg.get_item_children("LeftPanelGroup", 1)
            for b in children:
                dpg.delete_item(b)
            self.project_buttons.clear()

        self.listHashAvailable.clear()

        listProjs = self.mng.ProjectsList()
        for p in listProjs:
            if ("===" in p):
                dpg.add_text(default_value=p, color=(43,198,245,255), parent="LeftPanelGroup")
            elif ("---" in p):
                dpg.add_text(default_value=p, color=(255,62,67,255), parent="LeftPanelGroup")
            elif ("___" in p):
                dpg.add_text(default_value=p, color=(181,230,29,255), parent="LeftPanelGroup")
            else:
                with dpg.group(horizontal=True, parent="LeftPanelGroup"):
                    idx = dpg.add_button(label="Cache", callback=self.LoadHashVersions, user_data=p)
                    prod_btn = dpg.add_button(label=p, callback=self.LoadVersions, user_data=p)
                    self.project_buttons[p] = prod_btn
                    for n in self.mng.hashVersions:
                        if n['Name'] == p:
                            dpg.bind_item_theme(idx, self.hash_btn_theme)
                            break
                        else: 
                            dpg.bind_item_theme(idx, self.no_hash_btn_theme)

                    # Подсветка кнопки продукта, если он сейчас загружен
                    if p == self.mng.CurrentProductName:
                        dpg.bind_item_theme(prod_btn, self.hash_btn_theme)

                    self.listHashAvailable.append({"Projs": p, "id": idx})
                    
        pass

    def LoadVersions(self, sender, app_data, user_data):
        self.load_queue.append(("version", user_data))
        self.process_load_queue()

    def LoadHashVersions(self, sender, app_data, user_data):
        self.load_queue.append(("hash", user_data))
        self.process_load_queue()

    def process_load_queue(self):
        if self.is_loading or not self.load_queue:
            return
        
        task_type, product_name = self.load_queue.pop(0)
        self.is_loading = True
        try:
            if task_type == "version":
                self.listVersions = []
                # dpg.set_value("FilterField", "") # Удалено, так как виджет удален
                loader = dpg.add_loading_indicator(before="VersionsTable", circle_count=10, secondary_color=(43,198,245,255), color=(250,250,255,255))
                self.Logger("Load versions for " + product_name)
                dpg.hide_item("VersionsTable")
                self.listVersions = self.mng.Loadversions(product_name)

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
                self.Logger("Finish download versions for " + product_name)

                for node in self.listHashAvailable:
                    if node['Projs'] == product_name:
                        dpg.bind_item_theme(node['id'], self.hash_btn_theme)

            else: # hash type
                self.listVersions = []
                # dpg.set_value("FilterField", "") # Удалено, так как виджет удален
                self.Logger("Loading cache for " + product_name)
                dpg.hide_item("VersionsTable")
                self.listVersions = self.mng.LoadHashversions(product_name)
                rows = dpg.get_item_children("VersionsTable", 1)
                for row in rows:
                    dpg.delete_item(row)

                if (self.listVersions == ""):
                    # Сброс подсветки всех кнопок, если кеш пуст
                    for name, btn in self.project_buttons.items():
                        dpg.bind_item_theme(btn, self.no_hash_btn_theme)
                    
                    dpg.show_item("VersionsTable")
                    self.Logger("Cache is empty for " + product_name)
                    return
                
                for p in self.listVersions:
                    with dpg.table_row(tag=p, parent="VersionsTable"):
                        with dpg.table_cell():
                            dpg.add_button(label=p, callback=self.LoadBuilds, user_data=p)
                
                dpg.show_item("VersionsTable")
                self.Logger("Finish loading cache for " + product_name)

            # Update highlighting without reloading the whole list
            for name, btn in self.project_buttons.items():
                if name == product_name:
                    dpg.bind_item_theme(btn, self.hash_btn_theme)
                else:
                    dpg.bind_item_theme(btn, self.no_hash_btn_theme)

        finally:
            self.is_loading = False
            # Process next item in queue if any
            self.process_load_queue()

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
        table_uuid = dpg.generate_uuid()
        brand_group_tag = dpg.generate_uuid() # Generate unique tag first!
        buttonsBuild = []
        for p in BuildingsList:
            rowuuid = dpg.generate_uuid()
            buttonsBuild.append({"Uid": rowuuid, "Label": p})

        mousepos = dpg.get_mouse_pos()
        mousepos[0] += 200
        with dpg.window(label=f"{self.mng.CurrentProductName} - {user_data}", tag=f"Win_{user_data}_{brand_group_tag}", pos=mousepos, height=550, width=250):
            
            # Фильтр сверху с фиксированной высотой
            with dpg.child_window(height=40):
                dpg.add_input_text(label="Filter Builds", callback=self.FilterBuilds, width=-45, user_data=buttonsBuild)

            # Таблица в child_window, занимающая всё свободное место
            with dpg.child_window(height=-1):
                with dpg.table(tag = table_uuid, header_row=False, row_background=True,
                               borders_innerH=True, borders_outerH=True, borders_innerV=True,
                               borders_outerV=True):
                    dpg.add_table_column()

                    for i, p in enumerate(BuildingsList):
                        item = buttonsBuild[i]
                        with dpg.table_row(tag=item["Uid"]):
                            with dpg.table_cell():
                                # Pass the brand_group_tag as a 3rd element in user_data
                                dpg.add_button(label=p, callback=self.ShowBrandSelection, user_data=[p, user_data, brand_group_tag])
                
            # Блок выбора брендов снизу
            with dpg.child_window(height=-1):
                dpg.add_text("Brand Selection:")
                with dpg.group(horizontal=True, tag=brand_group_tag):
                    # Placeholder for checkboxes
                    pass
                # Pass the brand_group_tag to this button as well
                dpg.add_button(label="Add Selected Brands", callback=self.AddSelectedBrandsToQueue, user_data=brand_group_tag)

        pass

    def ShowBrandSelection(self, sender, app_data, user_data):
        build_ref = user_data[0]
        version = user_data[1]
        # group_tag is no longer needed for checkboxes as we are using buttons now
        
        brands = self.mng.GetBrandsForBuild(build_ref)
        if not brands:
            self.ee.emit("OutputLog", "No brands found for this build.")
            return

        window_tag = f"Win_Brands_{dpg.generate_uuid()}"
        mousepos = dpg.get_mouse_pos()
        mousepos[0] += 200
        
        with dpg.window(label=f"Brands for {build_ref}", tag=window_tag, pos=mousepos, height=350, width=200):
            # Таблица занимает всё свободное место окна (фильтр удален)
            with dpg.child_window(height=-1):
                table_uuid = dpg.generate_uuid()
                buttons_brands = []
                with dpg.table(tag=table_uuid, header_row=False, row_background=True,
                               borders_innerH=True, borders_outerH=True, borders_innerV=True,
                               borders_outerV=True):
                    dpg.add_table_column()

                    for brand in brands:
                        rowuuid = dpg.generate_uuid()
                        buttons_brands.append({"Uid": rowuuid, "Label": brand})
                        with dpg.table_row(tag=rowuuid):
                            with dpg.table_cell():
                                dpg.add_button(label=brand, 
                                                callback=lambda s, a, b=brand: self.AddBrandToQueue(b, build_ref, version, window_tag),
                                                user_data=brand)
                
            with dpg.child_window(height=-1):
                dpg.add_text("Click a brand to add it to the queue.")

    def AddBrandToQueue(self, brand, build_ref, version, window_tag):
        self.mng.AddItemQueue(build_ref, version, [brand])
        # dpg.configure_item(window_tag, show=False) # Removed to allow multiple selections

    def FilterBrands(self, sender, app_data, user_data):
        if user_data is None:
            return
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
        for x in self.DeleteQueueItems:
            dpg.delete_item(x)
        self.mng.LoadDistrs()
        self.DeleteQueueItems.clear()

    def ManualAddItemQueue(self, sender, app_data, user_data):
        ref = dpg.get_value("AddManualItemQueue")
        if(ref.find("/build") == -1):
            self.ee.emit("OutputLog", "Invalid reference wasn't added")
        else:
            self.mng.AddRawReference(ref)
        
        dpg.set_value("AddManualItemQueue", "")
    
    def AddItemQueue(self, sender, app_data, user_data):
        self.mng.AddItemQueue(user_data)
        pass

    def ShowItemQueue(self, ref:str, error:str = ""):
        with dpg.group(parent="Queue", horizontal=True):
            self.DeleteQueueItems.append(
                dpg.add_button(label='X', width=20, height=20, callback=self.DeleteItemQueue, user_data=ref)
            )

            size = dpg.get_text_size(ref)[0] + 20
            dpg.add_input_text(default_value=ref, enabled=False, width=size)
            print(self.DeleteQueueItems)

    def DeleteItemQueue(self, sender, app_data, user_data):
        self.DeleteQueueItems.remove(sender)
        print(self.DeleteQueueItems)
        self.mng.DeleteItemQueue(user_data)
        pass

    def ClearQueue(self, sender, app_data, user_data):
        self.mng.CleareQueue()
        pass
    
    def RefreshQueue(self, queue: List):
        try:
            self.DeleteQueueItems.clear()
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
        dpg.set_value("DailyOut", setDict["Daily"])

        OSes = setDict["OS"]
        windows = OSes["Windows"]
        linux = OSes["Linux"]

        dpg.set_value("checkWindowsOut", windows)
        dpg.set_value("checkLinuxOut", linux)

        projs = setDict["Projects"]

        for p in projs:
            t = []
            with dpg.group(before="ProjectsWindowOutGroup"):
                t.append(dpg.add_input_text(label="Name", default_value=p["name"]))
                t.append(dpg.add_input_text(label="Custom Path", default_value=p["folder"]))
                t.append(dpg.add_checkbox(label="Enable Custom Path", default_value=p["activePath"]))
                with dpg.group(before=t[0], horizontal=True):
                    t.append(dpg.add_button(label="X", width=20, height=20, callback=self.DeleteProjectSettings))
                    t.append(dpg.add_button(label="^", width=20, height=20, callback=self.UpProjectSettings))
                    t.append(dpg.add_button(label="v", width=20, height=20, callback=self.DownProjectSettings))
                t.append(dpg.add_separator())
            self.SettingsID.append(t)
                
        dpg.configure_item("SettingsWindow", show=True)
        pass
    
    def DeleteProjectSettings(self, sender, app_data, user_data):
        for i in self.SettingsID:
            if (sender in i):
                for e in i:
                    dpg.delete_item(e)
                self.SettingsID.remove(i)
                return
        pass

    def UpProjectSettings(self, sender, app_data, user_data):
        for i in self.SettingsID:
            if (sender in i):
                idx = self.SettingsID.index(i)
                if (idx > 0):
                    self.SettingsID[idx - 1], self.SettingsID[idx] = self.SettingsID[idx], self.SettingsID[idx-1]
                    self.SaveSettings("", "", "")
                    self.OpenSettings("", "", "")   
                return
        pass

    def DownProjectSettings(self, sender, app_data, user_data):
        for i in self.SettingsID:
            if (sender in i):
                idx = self.SettingsID.index(i)
                if (idx < len(self.SettingsID) - 1):
                    self.SettingsID[idx], self.SettingsID[idx + 1] = self.SettingsID[idx + 1], self.SettingsID[idx]
                    self.SaveSettings("", "", "")
                    self.OpenSettings("", "", "")   
                return
        

    def Logger(self, text:str):
        dpg.set_value("log_out", dpg.get_value("log_out") + "\n" + text)
        

    def AddNewInputProject(self, sender, app_data, user_data):
        data =[]
        with dpg.group(before="ProjectsWindowOutGroup"):
            data.append(dpg.add_input_text(label="Name"))
            data.append(dpg.add_input_text(label="Custom Path"))
            data.append(dpg.add_checkbox(label="Enable Custom Path"))
            with dpg.group(before=data[0], horizontal=True):
                data.append(dpg.add_button(label="X", width=20, height=20, callback=self.DeleteProjectSettings))
                data.append(dpg.add_button(label="^", width=20, height=20, callback=self.UpProjectSettings))
                data.append(dpg.add_button(label="v", width=20, height=20, callback=self.DownProjectSettings))
            data.append(dpg.add_separator())
        self.SettingsID.append(data)
        

    def AddNewSeparator(self, sender, app_data, user_data):
        data =[]
        with dpg.group(before="ProjectsWindowOutGroup"):
            data.append(dpg.add_input_text(label="Name", default_value="==============Name=============="))
            data.append(dpg.add_input_text(label="Custom Path"))
            data.append(dpg.add_checkbox(label="Enable Custom Path", default_value=False))
            with dpg.group(before=data[0], horizontal=True):
                data.append(dpg.add_button(label="X", width=20, height=20, callback=self.DeleteProjectSettings))
                data.append(dpg.add_button(label="^", width=20, height=20, callback=self.UpProjectSettings))
                data.append(dpg.add_button(label="v", width=20, height=20, callback=self.DownProjectSettings))
            data.append(dpg.add_separator())
        self.SettingsID.append(data)
        
    
    def SaveSettings(self, sender, app_data, user_data):
        projs = []
        for p in self.SettingsID:
            projs.append({"name":dpg.get_value(p[0]), "folder":dpg.get_value(p[1]), "activePath":dpg.get_value(p[2])})

        d = {}
        d["Repository"] = dpg.get_value("RepoOut")
        d["Path"] = dpg.get_value("PathOut")
        d["Daily"] = dpg.get_value("DailyOut")
        d["OS"] = {"Windows": dpg.get_value("checkWindowsOut"), "Linux": dpg.get_value("checkLinuxOut")}
        d["Projects"] = projs
        # Сохраняем текущую тему из настроек
        d["Theme"] = self.mng.objSetting.theme

        self.mng.SaveSettings(d)

        for i in dpg.get_item_children("ProjectsWindowOut", 1):
            if (dpg.get_item_alias(i) != "ProjectsWindowOutGroup"):  
                dpg.delete_item(i)

        self.SettingsID = []

        dpg.configure_item("SettingsWindow", show=False)
        
        

    def Login(self, sender, app_data, user_data):
        self.mng.UserLogin(dpg.get_value("LoginInput"), dpg.get_value("PasswordInput"))
        dpg.configure_item("loginWindow", show=False)
        
        

    def RefreshLogin(self):
        dpg.set_value("outputLogin", self.mng.GetUserName())
        
    
    def GetInstalledComponents(self, sender="", app_data="", user_data=""):
        self.DeleteComponentList.clear()
        iComp = self.mng.GetInstalledComponents()

        if(len(iComp) <= 0):
            return

        dpg.delete_item("InstalledList", children_only=True)

        for comp in iComp:
            with dpg.group(parent="InstalledList", horizontal=True, horizontal_spacing=15):
                dpg.add_checkbox(callback=self.SetUnistallQueue, user_data=comp["name"])
                dpg.add_input_text(default_value=comp["name"], readonly=True, width=-2)
            dpg.add_separator(parent="InstalledList")
        with dpg.group(horizontal=True, parent="InstalledList"):
            dpg.add_button(label="Delete", callback=self.UninstallComponents)
            dpg.add_button(tag="SaveInstComp", label="Save", callback=self.SaveInstallComponentToFile)
            dpg.add_button(tag="CopyInstComp", label="Copy", callback=self.SetInstallComponentToClipboard)

        dpg.configure_item("InstalledComponent", show=True)
        dpg.configure_item("RefreshUninst", enabled=True)
        dpg.configure_item("InstCompMenu", enabled=True)
        dpg.configure_item("SaveInstComp", enabled=True)
        

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

    def SetInstallComponentToClipboard(self, sender, app_data, user_data):
        if (len(self.DeleteComponentList) > 0):
            self.mng.CopyInstallToClipboard(self.DeleteComponentList)
        else:
            self.ee.emit("OutputLog", "Uninstall Queue is empty!")
        pass


    def OpenStorage(self):
        self.mng.OpenStorage()
        

    def SaveToFile(self):
        self.mng.SaveComponentToFile()
        

    def LoadFromFile(self, sender, app_data):
        pathFile = app_data['file_path_name']
        listRefs = self.mng.LoadComponentFromFile(pathFile)
        for r in listRefs:
            self.mng.AddRawReference(r)
        pass

    def SaveLog(self):
        self.mng.SaveLog(dpg.get_value("log_out"))

    def ConanStorageSize(self):
        size = self.mng.GetConanStorageSize()
        self.Logger(f"Conan storage size: {size} gb")
    
    def OpenConanStorage(self):
        self.mng.OpenConanStorage()
        
    def UpdateHistory(self):
        temp: str = ""
        for node in self.mng.history:
            temp = f"{node['id']}| {node['ref']} |{node['os']}| {node['active']} \n" + temp

        dpg.set_value("history_out", temp)
        if ("loading" in temp) | ("waiting" in temp):
            dpg.configure_item("IndiLoad", show=True)
            dpg.configure_item("IndiLabel", show=True)
        else:
            dpg.configure_item("IndiLoad", show=False)
            dpg.configure_item("IndiLabel", show=False)
        pass

    def ClearHistory(self):
        self.mng.ClearHistoryList()
        pass

    def Run(self):
        self.MainWindow()
        self.LoadProjects()
        pass

    def FilterBuilds(self, sender, app_data, user_data):
        if user_data is None:
            return
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
    
    def AddSelectedBrandsToQueue(self, sender, app_data, user_data):
        # Placeholder logic since checkboxes are not yet implemented in the UI group
        self.ee.emit("OutputLog", "Selection mechanism for brands is not yet implemented.")

    def ShowFileDialog(self):
        dpg.configure_item("fileDialog", show=True)
