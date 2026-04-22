from termcolor import colored
#import rich
from colorama import Back, Fore, Style
import time
#import keyboard
#import readchar
from fireflypad.utils.getch import getch
import sys
import subprocess
import os

def echooff():
    subprocess.run(['stty', '-echo'], check=True)
def echoon():
    subprocess.run(['stty', 'echo'], check=True)

CSI = "\033["

def back_color_256(n):
    return "\033[48;5;"+str(n)+"m"

def fore_color_256(n):
    return "\033[38;5;"+str(n)+"m"


STYLES = {
    "selected": f"{Back.BLUE}{Fore.LIGHTBLUE_EX}", 
    "choosed" : f"{Back.BLUE}"+fore_color_256(189),#147), 
    "unchoosed" : back_color_256(235) + fore_color_256(239),
    "normal1"  : back_color_256(237) + f"{Fore.LIGHTWHITE_EX}",
    "normal2"  : back_color_256(236) + f"{Fore.LIGHTWHITE_EX}",
    "reset"   : f"{Style.RESET_ALL}"
}


KEYS = {
    "up": CSI + "A",
    "down": CSI + "B",
    "right": CSI + "C",
    "left": CSI + "D",
}


def get_items_height(items):
    res = 0
    for item in items:
        res = res + item.count("\n") + 1
    return res


def draw_menu(items, selected_no = None, choosed_no = None):
    #max_len = max(map(len, items))

    print("\r", end = "")

    item_index = 0
    for item in items:
        item_index = item_index + 1

        style = "normal1"
        if item_index % 2 == 1:
            style = "normal1"
        if type(choosed_no) == int:
            style = "unchoosed"
        if item_index == selected_no:
            style = "selected"
        if item_index == choosed_no:
            style = "choosed"

        #item_text = ("{:%ds}" % max_len).format(item)
        #item_text = f"  {item_text}  "
        #item_text = " "*2 + STYLES[style] + item_text + STYLES["reset"]
        item_text = item
        item_text = item_text.replace("\001", STYLES[style])
        item_text = item_text.replace("\002", STYLES["reset"])

        print(item_text)

    
    N = get_items_height(items)
    print(CSI+str(N)+"A" + CSI+"2C", end = "", flush=True)



def _menu(items):


    print()
    key = ""
    selected_item = 1
    res = None
    while not (key in ["", "q"]):

        draw_menu(items, selected_item)

        N = get_items_height(items[:selected_item]) - 1 #selected_item - 1
        N = N - items[selected_item-1].count("\n")

        print("\n" * N + KEYS["right"]*2, end = "")
        key = getch()
        print(KEYS["up"] * N, end = "")


        if key == KEYS["down"]: selected_item = selected_item + 1
        if key == KEYS["up"  ]: selected_item = selected_item - 1
        if (key == "\n") or (key == '\r'):
            draw_menu(items, None, selected_item)
            res = selected_item
            break
        selected_item = (selected_item-1) % len(items) + 1 
        #print("pressed:" + repr(key), flush=True)

    print("\n" * get_items_height(items), end="")
    return res


def wrap(s, max_len, min_len):
    lines = []
    line = ""

    words = s.split(" ")

    N = 0
    for word in words:
        if len(line + word) < max_len:
            line = line + word + " "
        else:
            lines = lines + [line.rstrip(" ")]
            line = word + " "

    if line:
        lines = lines + [line]

    res = ""
    N = 0
    for line in lines:
        N = N + 1
        str = line
        str = ("{:%ds}" % min_len).format(str)
        str = "  \001  "+str+"\002\n"
        res = res + str

    res = res.rstrip("\n")

    return res

    res = ("{:%ds}" % min_len).format(res)
    res = res + "\002"
    return res

def menu(items_):

    if type(items_) == dict:
        items = list(items_.values())
    else:
        items = items_.copy()

    max_width =  os.get_terminal_size().columns - 10
    max_len = max(map(len, items))+2
    if max_len > max_width:
        max_len = max_width

    for i in range(0, len(items)):
        str = items[i]
        items[i] = wrap(str, max_width, max_len)

    try:
        echooff()
        res=_menu(items)
        if res and type(items_) == dict:
            res = list(items_.items())[res-1][0]
    finally:
        echoon()

    return res


if __name__ == "__main__":
    items = ["This is my very long long item1", "My Item2", "Item3 is mult"]
    res = menu(items)
    print(res)

    print("Now selecting from dictionary:")

    items = {"key1": "This is my very long long item1", "key2": "My Item2", "key3": "Item3 is mult"}
    res = menu(items)
    print(res)

