from __future__ import annotations;
from dataclasses import dataclass;
from Dumper import Dumper;
import os;
import json;
import time;
import threading;
import pyMeow;
import dearpygui.dearpygui as UI;

ProcessName = "RealRTCW.x64.exe";
QaGameDLL = "qagame_sp_x64.dll";

WindowWidth, WindowHeight = 630, 335;
TabPanelWidth, TabPanelHeight = 110, 308;
TabWidth, TabHeight = 505, 308;
TabButtonWidth, TabButtonHeight = 95, 20;

Weapons = { 0: "None", 1: "Knife", 2: "Luger", 3: "Luger Silencer", 4: "Colt", 8: "Dual Colt", 5: "TT33", 9: "Dual TT33", 6: "1905 Revolver", 7: "HDM", 10: "MP40", 14: "MP34", 12: "Sten", 11: "Thompson", 13: "PPSH41", 15: "Kar98", 44: "Kar98", 16: "Snooper Rifle", 45: "Snooper Rifle", 17: "Mosin Nagant", 23: "FG42", 47: "FG42", 22: "Stg44", 24: "BAR", 34: "Grenades", 35: "Pineapples", 36: "Dynamite", 39: "Poison Gas", 25: "Ithaca", 20: "G43", 19: "M1 Garand", 48: "M1 Garand Grenade", 30: "Panzerfaust", 31: "Flamethrower", 28: "Browning", 29: "MG42", 32: "Venom Gun", 33: "Tesla" };
Ammos = { ("Luger Silencer", "MP40", "MP34", "Sten"): 2, ("Dual Colt", "Thompson"): 4, ("Dual TT33", "PPSH41"): 5, ("Kar98", "FG42", "G43"): 15, ("BAR"): 19, ("Browning", "Venom Gun"): 29 }
DefaultConfig = {
    "HealthValue": 100,
    "ArmorValue": 100,
    "AmmoValue": 300,
    "StaminaLoopDelay": 0.01,
    "GunMods": {
        "LoopDelay": 0.01,
    },
};

@dataclass
class GameProcess:
    Process: object | None = None;
    ModuleBase: int = 0;
    QaGameBase: int = 0;
    @property
    def IsOpen(self) -> bool:
        return (self.Process is not None);

@dataclass
class TabEntry:
    WindowTag: str;
    ButtonTag: str;

class Trainer:
    def __init__(self) -> None:
        self.Game = GameProcess();
        self.Tabs: dict[str, TabEntry] = {};
        self.Data: dict =  { "Weapons": Weapons, "Ammos": Ammos };
        self.Offsets: dict = self.GetOffsets();
        self.Options: dict[str, str] = {};
        self.Config: dict = DefaultConfig;
        self.Window: dict = { "Dragging": False, "UpdateTime": time.time() };

    def Attach(self) -> bool:
        try:
            self.Game.Process = pyMeow.open_process(ProcessName);
            self.Game.ModuleBase = pyMeow.get_module(self.Game.Process, ProcessName)["base"];
            self.Game.QaGameBase = pyMeow.get_module(self.Game.Process, QaGameDLL)["base"];
            return True;
        except: return False;

    def IsAddressValid(self, Address) -> bool:
        try:
            pyMeow.r_byte(self.Game.Process, Address);
            return True;
        except: return False;

    def GetOffsets(self) -> dict:
        try:
            Dumper().Run();
            Path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Offsets.json");
            if (os.path.exists(Path)):
                with open(Path) as File:
                    return json.load(File);
            return {};
        except Exception as Error:
            print(f"Couldn't get offsets, Error: {Error}");
            return {};

    def SetHealth(self, Value: int) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase or self.Offsets == {}): return;
        try:
            Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["HealthPointer"]);
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address + self.Offsets["Health"], Value);
        except Exception as Error:
            print(f"Couldn't set health, Error: {Error}");
            return;

    def SetArmor(self, Value: int) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase or self.Offsets == {}): return;
        try:
            Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address + self.Offsets["Armor"], Value);
        except Exception as Error:
            print(f"Couldn't set armor, Error: {Error}");
            return;

    def GetCurrentWeapon(self) -> str:
        if (not self.Game.IsOpen or not self.Game.QaGameBase or self.Offsets == {}): return "Unknown";
        try:
            Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
            if (self.IsAddressValid(Address)):
                Weapon = pyMeow.r_int(self.Game.Process, Address + self.Offsets["CurrentWeapon"]);
                if (Weapon is not None):
                    return Weapons[Weapon];
            return "Unknown";
        except Exception as Error:
            print(f"Couldn't get the current weapon, Error: {Error}");
            return "Unknown";

    def SetAmmo(self, Value: int, Type: str) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase or self.Offsets == {}): return;
        try:
            Weapon = self.GetCurrentWeapon();
            if (not Weapon or Weapon in ("None", "Unknown")): return;
            Index = next((Index for (Index, Name) in self.Data["Weapons"].items() if (Name == Weapon)), None)
            if (Index is None): return;
            if (Type in ("Bullets", "Both")):
                Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
                if (self.IsAddressValid(Address)):
                    BulletsAddress = Address + self.Offsets["BulletsArray"] + Index * 4;
                    if (self.IsAddressValid(BulletsAddress)):
                        pyMeow.w_int(self.Game.Process, BulletsAddress, Value);
            if Type in ("Ammo", "Both"):
                Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
                AmmoIndex = Index;
                for (WeaponTuple, AmmoValue) in Ammos.items():
                    if (Weapon in WeaponTuple):
                        AmmoIndex = AmmoValue;
                        break;
                AmmoAddress = Address + self.Offsets["AmmoArray"] + AmmoIndex * 4;
                if (self.IsAddressValid(AmmoAddress)):
                    pyMeow.w_int(self.Game.Process, AmmoAddress, Value);
        except Exception as Error:
            print(f"Couldn't set ammo, Error: {Error}");
            return;

    def SetStamina(self, Value: int) -> None:
        if (not self.Game.Process or not self.Game.QaGameBase or self.Offsets == {}): return;
        try:
            Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address + self.Offsets["Stamina"], Value);
        except Exception as Error:
            print(f"Couldn't set stamina, Error: {Error}");

    def SetWeaponActionValue(self, Value: int) -> None:
        if (not self.Game.Process or not self.Game.QaGameBase or self.Offsets == {}): return;
        try:
            Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address + self.Offsets["WeaponAction"], Value);
        except Exception as Error:
            print(f"Couldn't set weapon action value, Error: {Error}");

    def SetWeaponSpread(self, Value: int) -> None:
        if (not self.Game.Process or not self.Game.QaGameBase or self.Offsets == {}): return;
        try:
            Address = pyMeow.r_int64(self.Game.Process, self.Game.QaGameBase + self.Offsets["PlayerPointer"]);
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address + self.Offsets["Spread"], Value);
        except Exception as Error:
            print(f"Couldn't set spread, Error: {Error}");

    @staticmethod
    def OnExit() -> None:
        UI.destroy_context();

    def OpenTab(self, Name: str) -> None:
        UI.show_item(Name);

    def HideAllTabs(self) -> None:
        for Entry in self.Tabs.values():
            UI.hide_item(Entry.WindowTag);

    def SwitchTab(self, Name: str) -> None:
        self.HideAllTabs();
        self.OpenTab(Name);

    def CreateTab(self, Name: str) -> str | None:
        if (Name in self.Tabs): return None;
        WindowTag = f"Tab_{Name}";
        ButtonTag = f"Button_{Name}";
        UI.add_child_window(label = Name, tag = WindowTag, width = TabWidth, height = TabHeight, pos = (120, 22));
        UI.add_button(label = Name, tag = ButtonTag, parent = "TabHolder", width = TabButtonWidth, height = TabButtonHeight, callback = lambda: self.SwitchTab(WindowTag));
        self.Tabs[Name] = TabEntry(WindowTag, ButtonTag);
        return WindowTag;

    def DeleteTab(self, Name: str) -> None:
        if (Name not in self.Tabs): return;
        Entry = self.Tabs.pop(Name);
        UI.delete_item(Entry.WindowTag);
        UI.delete_item(Entry.ButtonTag);

    def AddToggle(self, Parent: str, Tag: str, Label: str) -> str | None:
        if (not Tag or Tag in self.Options): return None;
        self.Options[Tag] = UI.add_checkbox(parent = Parent, tag = Tag, label = Label);
        return Tag;

    def AddSlider(self, Parent: str, Tag: str, Args: dict) -> str | None:
        if (not Tag or Tag in self.Options): return None;
        self.Options[Tag] = UI.add_slider_int(parent = Parent, tag = Tag, **Args);
        return Tag;

    def AddInputInt(self, Parent: str, Tag: str, Args: dict) -> str | None:
        if (not Tag or Tag in self.Options): return None;
        self.Options[Tag] = UI.add_input_int(parent = Parent, tag = Tag, **Args);
        return Tag;

    def AddInputFloat(self, Parent: str, Tag: str, Args: dict) -> str | None:
        if (not Tag or Tag in self.Options): return None;
        self.Options[Tag] = UI.add_input_float(parent = Parent, tag = Tag, **Args);
        return Tag;

    def AddButton(self, Parent: str, Args: dict) -> str:
        return UI.add_button(parent = Parent, **Args);

    def AddLabel(self, Parent: str, Tag: str, Label: str) -> str | None:
        return UI.add_text(parent = Parent, tag = Tag, default_value = Label);

    def AddDropdown(self, Parent: str, Tag: str, Args: dict) -> str | None:
        if (Tag in self.Options): return None;
        self.Options[Tag] = UI.add_combo(parent = Parent, tag = Tag, **Args);
        return self.Options[Tag];

    def AddDivider(self, Parent: str):
        return UI.add_separator(parent = Parent);

    def GetValue(self, Tag: str) -> str | int | None:
        if (not Tag or Tag not in self.Options): return None;
        return UI.get_value(Tag);

    def LoopHealth(self):
        while UI.is_dearpygui_running():
            if (self.GetValue("HealthToggle")):
                self.SetHealth(self.GetValue("HealthValue"));
            time.sleep(0.01);

    def LoopArmor(self):
        while UI.is_dearpygui_running():
            if (self.GetValue("ArmorToggle")):
                self.SetArmor(self.GetValue("ArmorValue"));
            time.sleep(0.01);

    def LoopAmmo(self):
        while UI.is_dearpygui_running():
            UI.set_value("CurrentWeaponLabel", f"Current Weapon: {self.GetCurrentWeapon()}");
            if (self.GetValue("AmmoToggle")):
                self.SetAmmo(self.GetValue("AmmoValue"), self.GetValue("AmmoType"));
            time.sleep(0.1);

    def LoopGunMods(self):
        while UI.is_dearpygui_running():
            if (self.GetValue("WeaponModsTimerToggle")):
                self.SetWeaponActionValue(0);
            if (self.GetValue("WeaponModsMinimumSpreadToggle")):
                self.SetWeaponSpread(-0);
            time.sleep(self.GetValue("WeaponModsLoopDelay"));

    def LoopStamina(self):
        while UI.is_dearpygui_running():
            if (self.GetValue("InfiniteStaminaToggle")):
                self.SetStamina(20000);
            time.sleep(self.GetValue("InfiniteStaminaLoopDelay"));

    def BuildPlayerTab(self, Tab: str) -> None:
        self.AddLabel(Tab, "", "Health Changer");
        self.AddInputInt(Tab, "HealthValue", { "label": "Value", "min_value": 0, "max_value": 16959, "max_clamped": True, "min_clamped": True, "default_value": self.Config["HealthValue"], "width": 150 });
        self.AddButton(Tab, { "label": "Change", "width": 150, "height": TabButtonHeight, "callback": lambda: self.SetHealth(self.GetValue("HealthValue"))});
        self.AddToggle(Tab, "HealthToggle", "Loop");
        self.AddDivider(Tab);
        self.AddLabel(Tab, "", "Armor Changer");
        self.AddInputInt(Tab, "ArmorValue", { "label": "Value", "min_value": 0, "max_value": 16959, "max_clamped": True, "min_clamped": True, "default_value": self.Config["ArmorValue"], "width": 150 });
        self.AddButton(Tab, {"label": "Change", "width": 150, "height": TabButtonHeight, "callback": lambda: self.SetArmor(self.GetValue("ArmorValue"))});
        self.AddToggle(Tab, "ArmorToggle", "Loop");
        self.AddDivider(Tab);
        self.AddLabel(Tab, "", "Infinite Stamina");
        self.AddToggle(Tab, "InfiniteStaminaToggle", "Enabled");
        self.AddInputFloat(Tab, "InfiniteStaminaLoopDelay", { "label": "Stamina Loop Delay", "min_value": 0.001, "min_clamped": True, "step": 0.001, "step_fast": 0.01, "default_value": self.Config["StaminaLoopDelay"], "format": "%.3f", "width": 150 });

    def BuildWeaponTab(self, Tab: str) -> None:
        self.AddLabel(Tab, "", "Ammo Changer");
        self.AddInputInt(Tab, "AmmoValue", { "label": "Ammo Value", "min_value": 0, "max_value": 16959, "max_clamped": True, "min_clamped": True, "default_value": self.Config["AmmoValue"], "width": 150 });
        self.AddDropdown(Tab, "AmmoType", { "label": "Ammo Type", "items": ("Ammo", "Bullets", "Both"), "default_value": "Ammo", "width": 150 });
        self.AddLabel(Tab, "CurrentWeaponLabel", "Current Weapon: None");
        self.AddButton(Tab, { "label": "Set Ammo", "width": 150, "height": TabButtonHeight, "callback": lambda: self.SetAmmo(self.GetValue("AmmoValue"), self.GetValue("AmmoType"))});
        self.AddToggle(Tab, "AmmoToggle", "Loop");
        self.AddDivider(Tab);
        self.AddLabel(Tab, "WeaponModsTitle", "Gun Mods");
        self.AddInputFloat(Tab, "WeaponModsLoopDelay", { "label": "Gun Mods Loop Delay", "min_value": 0.001, "min_clamped": True, "step": 0.001, "step_fast": 0.01, "default_value": self.Config["GunMods"]["LoopDelay"], "format": "%.3f", "width": 150 });
        self.AddToggle(Tab, "WeaponModsTimerToggle", "Gun Timer");
        self.AddToggle(Tab, "WeaponModsMinimumSpreadToggle", "Minimum Spread");

    def BuildSettingsTab(self, Tab: str) -> None:
        UI.set_item_pos("Button_Settings", [8, 280]);

    def BuildUI(self) -> None:
        UI.create_context();
        Viewport = UI.create_viewport(title = "RealRTCW Trainer", width = WindowWidth, height = WindowHeight, decorated = False, resizable = False);
        UI.setup_dearpygui();
        UI.show_viewport();
        with UI.window(label = "RealRTCW Trainer", tag = "MainWindow", width = WindowWidth, height = WindowHeight, no_title_bar = False, no_resize = True, no_move = True, no_collapse = True, no_scroll_with_mouse = True, no_scrollbar = True, on_close = self.OnExit):
            UI.add_child_window(label = "Tabs", tag = "TabHolder", width = TabPanelWidth, height = TabPanelHeight, pos = (5, 22));
            PlayerTab = self.CreateTab("Player");
            WeaponTab = self.CreateTab("Weapon");
            SettingsTab = self.CreateTab("Settings");
            self.BuildPlayerTab(PlayerTab);
            self.BuildWeaponTab(WeaponTab);
            self.BuildSettingsTab(SettingsTab);
            self.SwitchTab(PlayerTab);

            def CheckDrag(_, Data: dict):
                if (UI.is_mouse_button_down(0)):
                    Y = Data[1];
                    if (-2 <= Y <= 19 and not self.Window["Dragging"]):
                        self.Window["Dragging"] = True;
                else:
                    self.Window["Dragging"] = False;

            def Drag(_, Data: dict):
                if (self.Window["Dragging"]):
                    Current = time.time();
                    CalculatedTime = Current - self.Window["UpdateTime"];
                    if (CalculatedTime >= 0):
                        Position = UI.get_viewport_pos();
                        X = Data[1];
                        Y = Data[2];
                        TargetX = Position[0] + X;
                        TargetY = Position[1] + Y;
                        DeltaX = (TargetX - Position[0]) * 0.25;
                        DeltaY = (TargetY - Position[1]) * 0.25;
                        FinalX = Position[0] + DeltaX;
                        FinalY = Position[1] + DeltaY;
                        UI.configure_viewport(Viewport, x_pos = FinalX, y_pos = FinalY);
                        self.Window["UpdateTime"] = Current;

            def HideViewport():
                UI.minimize_viewport();

            with UI.handler_registry():
                UI.add_key_press_handler(key = 161, callback = HideViewport);
                UI.add_mouse_drag_handler(0, callback = Drag);
                UI.add_mouse_move_handler(callback = CheckDrag);

            HealthLoopThread = threading.Thread(target = self.LoopHealth, daemon = True);
            ArmorLoopThread = threading.Thread(target = self.LoopArmor, daemon = True);
            WeaponActionThread = threading.Thread(target = self.LoopGunMods, daemon = True);
            LabelThread = threading.Thread(target = self.LoopAmmo, daemon = True);
            InfiniteStaminaThread = threading.Thread(target = self.LoopStamina, daemon = True);
            HealthLoopThread.start();
            ArmorLoopThread.start();
            WeaponActionThread.start();
            LabelThread.start();
            InfiniteStaminaThread.start();

    def Run(self) -> None:
        if (not self.Attach()):
            print("Game process not found.");
            return;
        self.BuildUI();
        UI.start_dearpygui();

if (__name__ == "__main__"):
    Trainer().Run();
