from phBot import *
import struct
import QtBind
import json
import os
from threading import Timer
from time import sleep
import re

pName = "Alchemist"
pVersion = '1.0.0'

STONE_NAMES = {
    "Phy Atk": "Attribute stone of courage",
    "Mag Atk": "Attribute stone of philosophy",
    "Phy Def": "Attribute stone of flesh",
    "Mag Def": "Attribute stone of mind",
    "Phy Atk Reinforce": "Attribute stone of warrior",
    "Mag Atk Reinforce": "Attribute stone of meditation",
    "Attack Rate": "Attribute stone of focus",
    "Critical": "Attribute stone of challenge",
    "Block Rate": "Attribute stone of agility",
    "Phy Absorb": "Attribute stone of training",
    "Mag Absorb": "Attribute stone of prayer",
}

IsRunning = False

gui = QtBind.init(__name__,pName)

# --- GUI Setup ---

btnRefresh = QtBind.createButton(gui, 'refresh_items', '                         Refresh Equipments                         ', 20, 20)

QtBind.createLabel(gui, 'Select Equipment:', 20, 50)
ddEquipment = QtBind.createCombobox(gui, 110, 48, 158, 20)


QtBind.createLabel(gui, 'Select Stat:', 20, 75)
ddStatType = QtBind.createCombobox(gui, 110, 75, 158, 20)
for stat in sorted(STONE_NAMES.keys()):
    QtBind.append(gui, ddStatType, stat)
QtBind.setText(gui, ddStatType, "Phy Dmg") # Default selection

QtBind.createLabel(gui, 'Target %:', 20, 100)
ddTargetPerc = QtBind.createCombobox(gui, 110, 100, 158, 20)
for perc in ["0%", "20%", "40%", "60%", "80%", "100%"]:
    QtBind.append(gui, ddTargetPerc, perc)
QtBind.setText(gui, ddTargetPerc, "60%") # Default selection

btnStart = QtBind.createButton(gui, 'btnStart_clicked', '           START           ', 20, 140)

btnStop = QtBind.createButton(gui, 'btnStop_clicked', '          STOP          ', 180, 140)
QtBind.setEnabled(gui, btnStop, False) # Default state



def refresh_items():
    global item_slots
    # Clear the dropdown and our internal tracker
    QtBind.clear(gui, ddEquipment)
    item_slots = {}
    
    inventory = get_inventory()
    items = inventory['items']
    
    for slot in range(13, len(items)):
        item = items[slot]
        
        # Filter: Exists, has a name, and is equipment (Durability > 0)
        if item and item['name'] and item['durability'] > 0:
            # We skip stackables (Potions/Arrows) by checking if quantity is 1 
            # (Stones also have quantity 1, but they don't have durability)
            display_name = f"{item['name']} (Slot {slot})"
            item_slots[display_name] = slot
            QtBind.append(gui, ddEquipment, display_name)

def get_selected_item_slot():
    selected_text = QtBind.text(gui, ddEquipment)
    if selected_text in item_slots:
        return item_slots[selected_text]
    return -1

# --- State Management Helper ---
def update_ui_states(running):
    QtBind.setEnabled(gui, btnRefresh, not running)
    QtBind.setEnabled(gui, ddEquipment, not running)
    QtBind.setEnabled(gui, ddStatType, not running)
    QtBind.setEnabled(gui, ddTargetPerc, not running)
    QtBind.setEnabled(gui, btnStart, not running)
    QtBind.setEnabled(gui, btnStop, running)

# --- Button Logic ---
def btnStart_clicked():
    global IsRunning
    if not IsRunning:
        IsRunning = True
        update_ui_states(True)
        log('Plugin: Started.')
        Fuse()

def btnStop_clicked():
    global IsRunning
    IsRunning = False
    update_ui_states(False)
    log("Plugin: stopped by user.")

def Stop():
    global IsRunning
    IsRunning = False
    update_ui_states(False)

def get_log_path():
    data = get_character_data()
    if not data or not data['name']:
        log('Plugin: Character data not found. Are you logged in?')
        return None

    # File format: Server_Name_Log.txt
    filename = f"{data['server']}_{data['name']}_Log.txt"
    
    # Path: Root/Plugins -> Root/Log
    root_dir = os.path.dirname(os.path.dirname(__file__))
    log_file = os.path.join(root_dir, "Log", filename)
    
    return log_file

def Fuse():
    global IsRunning
    if not IsRunning: return

    # 1. Get the Gear Slot
    equipment_slot_index = get_selected_item_slot()
    if equipment_slot_index == -1:
        log("Plugin: No equipment selected! Refresh and pick an item.")
        stop()
        return

    # 1. Get the current selection from the UI
    selected_stat = QtBind.text(gui, ddStatType)
    stone_name = STONE_NAMES[selected_stat]

    inventory = get_inventory()
    stone_slot_index = -1
    for slot, item in enumerate(inventory['items']):
        if item and stone_name.lower() in item['name'].lower():
            stone_slot_index = slot + 0
            break
    
    if stone_slot_index == -1:
        log(f"Plugin: Stopped: No '{stone_name}' found!")
        stop()
        return

    data = bytearray([0x02, 0x05, 0x02, equipment_slot_index, stone_slot_index])
    inject_joymax(0x7151, data, False)

def check_result_event():
    global IsRunning
    if not IsRunning: return

    path = get_log_path()
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)
            f.seek(max(0, f.tell() - 2000)) # Read last n chars
            lines = f.readlines()
            
            for line in reversed(lines):
                if "Alchemy Stone:" in line and "->" in line:
                    match = re.search(r'->\s*\[(\d+)%\]', line)
                    if match:
                        val = int(match.group(1))
                        target = int(QtBind.text(gui, ddTargetPerc).replace("%",""))
                        
                        if val >= target:
                            log("Plugin: Goal Reached!")
                            Stop()
                        else:
                            Fuse()
                        return
                    else:
                        log("Plugin: Re error")
                        Stop()
    except Exception as e:
        Stop()
        log("Plugin: Log Error: {e}")
        
def handle_joymax(opcode, data):
    global IsRunning
    if IsRunning and opcode == 0xB151:
        Timer(0.005, check_result_event).start()

    return True