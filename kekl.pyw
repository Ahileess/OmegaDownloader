
import threading
from time import sleep
import dearpygui.dearpygui as dpg
import dearpygui.demo as dpgDemo
import GUI as mgui
import Manager
from pymitter import EventEmitter
from pynput import keyboard

toggle:bool = True

def on_press(key):
    #TODO: пока не пофиксили это: https://github.com/hoffstadt/DearPyGui/issues/1800
    global wm
    global hm
    global pos
    global toggle
    #применять макс значения до максимайза, а потом возвращать к исходным
    if(key == keyboard.Key.ctrl_r): # сохранять макс значения 
        if (toggle):
            wm = dpg.get_viewport_max_width()
            hm = dpg.get_viewport_max_height()
            pos = dpg.get_viewport_pos()
            dpg.minimize_viewport()
            dpg.set_viewport_max_height(Def_h)
            dpg.set_viewport_max_width(Def_w)
            toggle = False
        else:
            dpg.maximize_viewport()
            dpg.toggle_viewport_fullscreen()
            dpg.toggle_viewport_fullscreen()
            dpg.set_viewport_pos(pos)
            sleep(0.8)
            dpg.set_viewport_max_height(hm)
            dpg.set_viewport_max_width(wm)
            toggle = True
    pass

def listen():
    with keyboard.Listener(on_press=on_press) as listener:
        listener.join()

def mainfunc():
    global Def_w
    global Def_h
    Def_w = 1100
    Def_h = 1000

    threading.Thread(target=listen, daemon=True).start()

    dpg.create_context()
    #dpg.configure_app(manual_callback_management=True)
    dpg.create_viewport(title='Omega.Downloader', width=Def_w, height=Def_h, small_icon="test.ico", large_icon="test.ico")

    #dpgDemo.show_demo()
    #dpg.show_item_registry()

    ee = EventEmitter()
    manager = Manager.Manager(ee)
    
    gui = mgui.GUIManager(manager, ee)
    gui.Run()

    #dpg.show_style_editor()
    dpg.set_primary_window('MainWindow', True)
    dpg.setup_dearpygui()
    dpg.show_viewport()
    
    
    while dpg.is_dearpygui_running():
        #jobs = dpg.get_callback_queue() # retrieves and clears queue
        #dpg.run_callbacks(jobs)
        dpg.render_dearpygui_frame()
 
    dpg.destroy_context()


if __name__ == "__main__":
    mainfunc()