import os
import sys
import dearpygui.dearpygui as dpg

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

def dpg_fonts_init():
    # add a font registry
    with dpg.font_registry():
        # first argument ids the path to the .ttf or .otf file
        with dpg.font(resource_path("consola.ttf"), 14, tag='odeplr_default_font') as default_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            _cyrillic_character_remap()
        """with dpg.font("Consola.ttf", 13, tag='odeplr_small_font') as small_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Cyrillic)
            _cyrillic_character_remap()"""
    dpg.bind_font(default_font)


def _cyrillic_character_remap():
    #Аа
    dpg.add_char_remap(0x00C0, 0x0410)
    dpg.add_char_remap(0x00E0, 0x0430) 
    #Бб
    dpg.add_char_remap(0x00C1, 0x0411)
    dpg.add_char_remap(0x00E1, 0x0431)
    #Вв
    dpg.add_char_remap(0x00C2, 0x0412)
    dpg.add_char_remap(0x00E2, 0x0432)
    #Гг
    dpg.add_char_remap(0x00C3,0x0413)
    dpg.add_char_remap(0x00E3,0x0433)
    #Дд
    dpg.add_char_remap(0x00C4, 0x0414)
    dpg.add_char_remap(0x00E4, 0x0434)
    #Ее
    dpg.add_char_remap(0x00C5,0x0415)
    dpg.add_char_remap(0x00E5,0x0435)
    #Ёё
    dpg.add_char_remap(0x00A8,0x0401)
    dpg.add_char_remap(0x00B8,0x0451)
    #Жж
    dpg.add_char_remap(0x00C6, 0x0416)
    dpg.add_char_remap(0x00E6, 0x0436)
    #Зз
    dpg.add_char_remap(0x00C7,0x0417)
    dpg.add_char_remap(0x00E7,0x0437)
    #Ии
    dpg.add_char_remap(0x00C8, 0x0418)
    dpg.add_char_remap(0x00E8, 0x0438)
    #Йй
    dpg.add_char_remap(0x00C9,0x0419)
    dpg.add_char_remap(0x00E9,0x0439)
    #Кк
    dpg.add_char_remap(0x00CA,0x041A)
    dpg.add_char_remap(0x00EA,0x043A)
    #Лл
    dpg.add_char_remap(0x00CB, 0x041B)
    dpg.add_char_remap(0x00EB, 0x043B)
    #Мм
    dpg.add_char_remap(0x00CC, 0x041C)
    dpg.add_char_remap(0x00EC, 0x043C)
    #Нн
    dpg.add_char_remap(0x00CD,0x041D)
    dpg.add_char_remap(0x00ED,0x043D)
    #Оо
    dpg.add_char_remap(0x00CE, 0x041E)
    dpg.add_char_remap(0x00EE, 0x043E)
    #Пп
    dpg.add_char_remap(0x00CF, 0x041F)
    dpg.add_char_remap(0x00EF, 0x043F)
    #Рр
    dpg.add_char_remap(0x00D0, 0x0420)
    dpg.add_char_remap(0x00F0, 0x0440)
    #Сс
    dpg.add_char_remap(0x00D1, 0x0421)
    dpg.add_char_remap(0x00F1, 0x0441)
    #Тт
    dpg.add_char_remap(0x00D2, 0x0422)
    dpg.add_char_remap(0x00F2, 0x0442)
    #Уу
    dpg.add_char_remap(0x00D3,0x0423)
    dpg.add_char_remap(0x00F3,0x0443)
    #Фф
    dpg.add_char_remap(0x00D4, 0x0424)
    dpg.add_char_remap(0x00F4, 0x0444)
    #Хх
    dpg.add_char_remap(0x00D5,0x0425)
    dpg.add_char_remap(0x00F5,0x0445)
    #Цц
    dpg.add_char_remap(0x00D6,0x0426)
    dpg.add_char_remap(0x00F6,0x0446)
    #Чч
    dpg.add_char_remap(0x00D7, 0x0427)
    dpg.add_char_remap(0x00F7, 0x0447)
    #Шш
    dpg.add_char_remap(0x00D8,0x0428)
    dpg.add_char_remap(0x00F8,0x0448)
    #Щщ
    dpg.add_char_remap(0x00D9,0x0429)
    dpg.add_char_remap(0x00F9,0x0449)
    #Ъъ
    dpg.add_char_remap(0x00DA,0x042A)
    dpg.add_char_remap(0x00FA,0x044A)
    #Ыы
    dpg.add_char_remap(0x00DB, 0x042B)
    dpg.add_char_remap(0x00FB, 0x044B)
    #Ьь
    dpg.add_char_remap(0x00DC, 0x042C)
    dpg.add_char_remap(0x00FC, 0x044C)
    #Ээ
    dpg.add_char_remap(0x00DD, 0x042D)
    dpg.add_char_remap(0x00FD, 0x044D)
    #Юю
    dpg.add_char_remap(0x00DE, 0x042E)
    dpg.add_char_remap(0x00FE, 0x044E)
    #Яя
    dpg.add_char_remap(0x00DF, 0x042F)
    dpg.add_char_remap(0x00FF, 0x044F)
