from __future__ import annotations;
from dataclasses import dataclass;
import time;
import threading;
import pyMeow;
import dearpygui.dearpygui as UI;

PROCESSNAME = "RealRTCW.x64.exe";
QAGAMEDLL = "qagame_sp_x64.dll";

WINDOWWIDTH, WINDOWHEIGHT = 630, 335;
TABPANELWIDTH, TABPANELHEIGHT = 110, 308;
TABWIDTH, TABHEIGHT = 505, 308;
TABBUTTONWIDTH, TABBUTTONHEIGHT = 95, 20;

Weapons = { 0: "None", 1: "Knife", 2: "Luger", 3: "Luger Silencer", 4: "Colt", 8: "Dual Colt", 5: "TT33", 9: "Dual TT33", 6: "1905 Revolver", 7: "HDM", 10: "MP40", 14: "MP34", 12: "Sten", 11: "Thompson", 13: "PPSH41", 15: "Kar98", 43: "Kar98", 16: "Snooper Rifle", 44: "Snooper Rifle", 17: "Mosin Nagant", 23: "FG42", 47: "FG42", 22: "Stg44", 24: "BAR", 34: "Grenades", 35: "Pineapples", 36: "Dynamite", 39: "Poison Gas", 25: "Ithaca", 20: "G43", 19: "M1 Garand", 48: "M1 Garand Grenade", 30: "Panzerfaust", 31: "Flamethrower", 28: "Browning", 29: "MG42", 32: "Venom Gun", 33: "Tesla" };
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

@dataclass
class WeaponOffsets:
    Bullets: int;
    Ammo: int | None = None;

Offsets = {
    "Health": 0x1861B4, "Armor": 0x12B618, "CurrentWeapon": 0x12B5E4, "Stamina": 0x12BA94, "WeaponAction": 0x12B56C,
    "Weapons": {
        # Knives
        "Knife": WeaponOffsets(0x12B814, 0x12B814),
        # Pistols
        "Luger": WeaponOffsets(0x12B818, 0x12B718), "Luger Silencer": WeaponOffsets(0x12B81C, 0x12B718), "Colt": WeaponOffsets(0x12B820, 0x12B720),
        "Dual Colt": WeaponOffsets(0x12B830, 0x12B720), "TT33": WeaponOffsets(0x12B824, 0x12B724), "Dual TT33": WeaponOffsets(0x12B834, 0x12B724),
        "1905 Revolver": WeaponOffsets(0x12B828, 0x12B728), "HDM": WeaponOffsets(0x12B82C, 0x12B72C),
        # SMGs
        "MP40": WeaponOffsets(0x12B838, 0x12B718), "MP34": WeaponOffsets(0x12B848, 0x12B718), "Sten": WeaponOffsets(0x12B840, 0x12B718),
        "Thompson": WeaponOffsets(0x12B83C, 0x12B720), "PPSH41": WeaponOffsets(0x12B844, 0x12B724),
        # Rifles
        "Kar98": WeaponOffsets(0x12B84C, 0x12B74C), "Snooper Rifle": WeaponOffsets(0x12B850, 0x12B750), "Mosin Nagant": WeaponOffsets(0x12B854, 0x12B754),
        # Assault Rifles
        "FG42": WeaponOffsets(0x12B86C, 0x12B74C), "Stg44": WeaponOffsets(0x12B868, 0x12B768), "BAR": WeaponOffsets(0x12B870, 0x12B75C),
        # Grenades
        "Grenades": WeaponOffsets(0x12B898, 0x12B898), "Pineapples": WeaponOffsets(0x12B89C, 0x12B89C), "Dynamite": WeaponOffsets(0x12B8A0, 0x12B8A0),
        "Poison Gas": WeaponOffsets(0x0, 0x0), # I currently don't have this item since it is given in a specific chapter and the saves are gone.
        # Shotguns
        "Ithaca": WeaponOffsets(0x12B874, 0x12B774),
        # Automatic Rifles
        "G43": WeaponOffsets(0x12B860, 0x12B74C), "M1 Garand": WeaponOffsets(0x12B85C, 0x12B75C), "M1 Garand Grenade": WeaponOffsets(0x12B8D4, 0x12B7D4),
        # Heavy Weapons
        "Panzerfaust": WeaponOffsets(0x12B888, 0x12B788), "Flamethrower": WeaponOffsets(0x12B88C, 0x12B88C), "MG42": WeaponOffsets(0x12B884, 0x12B784),
        "Browning": WeaponOffsets(0x12B880, 0x12B784),
        # Secret Weapons
        "Venom Gun": WeaponOffsets(0x12B890, 0x12B784), "Tesla": WeaponOffsets(0x12B894, 0x12B894)
    },
    "Inventory": {

    },
};

class Trainer:
    def __init__(self) -> None:
        self.Game = GameProcess();
        self.Tabs: dict[str, TabEntry] = {};
        self.Options: dict[str, str] = {};
        self.Config: dict = DefaultConfig;
        self.Window: dict = { "Dragging": False, "UpdateTime": time.time() };

    def Attach(self) -> bool:
        try:
            self.Game.Process = pyMeow.open_process(PROCESSNAME);
            self.Game.ModuleBase = pyMeow.get_module(self.Game.Process, PROCESSNAME)["base"];
            self.Game.QaGameBase = pyMeow.get_module(self.Game.Process, QAGAMEDLL)["base"];
            return True;
        except: return False;

    def IsAddressValid(self, Address):
        try:
            pyMeow.r_byte(self.Game.Process, Address);
            return True;
        except: return False;

    def SetHealth(self, Value: int) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase): return;
        try:
            HealthAddress = self.Game.QaGameBase + Offsets["Health"];
            if (self.IsAddressValid(HealthAddress)):
                pyMeow.w_int(self.Game.Process, HealthAddress, Value);
        except Exception as ex:
            print(f"Couldn't set health, Error: {ex}");
            return;

    def SetArmor(self, Value: int) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase): return;
        try:
            ArmorAddress = self.Game.QaGameBase + Offsets["Armor"];
            if (self.IsAddressValid(ArmorAddress)):
                pyMeow.w_int(self.Game.Process, ArmorAddress, Value);
        except Exception as ex:
            print(f"Couldn't set armor, Error: {ex}");
            return;

    def GetCurrentWeapon(self) -> str:
        if (not self.Game.IsOpen or not self.Game.QaGameBase): return "Unknown";
        try:
            WeaponAddress = self.Game.QaGameBase + Offsets["CurrentWeapon"];
            if (self.IsAddressValid(WeaponAddress)):
                Weapon = pyMeow.r_int64(self.Game.Process, WeaponAddress);
                if (Weapon in Weapons):
                    return Weapons[Weapon];
            return "Unknown";
        except Exception as ex:
            print(f"Couldn't get the current weapon, Error: {ex}");
            return "Unknown";

    def SetAmmo(self, WeaponValue: int | None, Value: int, Type: str) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase): return;
        try:
            Weapon = self.GetCurrentWeapon();
            if (Weapon and Weapon is not None and Weapon != "Unknown"):
                if (Type != "Both"):
                    CurrentWeaponAddress = self.Game.QaGameBase + getattr(Offsets["Weapons"][Weapon], Type);
                    if (self.IsAddressValid(CurrentWeaponAddress)):
                        pyMeow.w_int(self.Game.Process, CurrentWeaponAddress, Value);
                else:
                    CurrentBulletsWeaponAddress = self.Game.QaGameBase + Offsets["Weapons"][Weapon].Bullets;
                    if (self.IsAddressValid(CurrentBulletsWeaponAddress)):
                        pyMeow.w_int(self.Game.Process, CurrentBulletsWeaponAddress, Value);
                    CurrentAmmoWeaponAddress = self.Game.QaGameBase + Offsets["Weapons"][Weapon].Ammo;
                    if (self.IsAddressValid(CurrentAmmoWeaponAddress)):
                        pyMeow.w_int(self.Game.Process, CurrentAmmoWeaponAddress, Value);
        except Exception as ex:
            print(f"Couldn't set ammo, Error: {ex}");
            return;

    def SetWeaponActionValue(self, Value: int) -> None:
        if (not self.Game.Process or not self.Game.QaGameBase): return;
        try:
            Address = self.Game.QaGameBase + Offsets["WeaponAction"];
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address, Value);
        except Exception as ex:
            print(f"Couldn't set weapon action value, Error: {ex}");

    def SetStamina(self, Value: int) -> None:
        if (not self.Game.Process or not self.Game.QaGameBase): return;
        try:
            Address = self.Game.QaGameBase + Offsets["Stamina"];
            if (self.IsAddressValid(Address)):
                pyMeow.w_int(self.Game.Process, Address, Value);
        except Exception as ex:
            print(f"Couldn't set stamina, Error: {ex}");

    @staticmethod
    def OnExit() -> None:
        UI.destroy_context();

    def OpenTab(self, Name: str) -> None:
        UI.show_item(Name);

    def HideAllTabs(self) -> None:
        for entry in self.Tabs.values():
            UI.hide_item(entry.WindowTag);

    def SwitchTab(self, Name: str) -> None:
        self.HideAllTabs();
        self.OpenTab(Name);

    def CreateTab(self, Name: str) -> str | None:
        if (Name in self.Tabs): return None;
        WinTag = f"Tab_{Name}";
        BtnTag = f"Button_{Name}";
        UI.add_child_window(label = Name, tag = WinTag, width = TABWIDTH, height = TABHEIGHT, pos = (120, 22));
        UI.add_button(label = Name, tag = BtnTag, parent = "TabHolder", width = TABBUTTONWIDTH, height = TABBUTTONHEIGHT, callback = lambda: self.SwitchTab(WinTag));
        self.Tabs[Name] = TabEntry(WinTag, BtnTag);
        return WinTag;

    def DeleteTab(self, Name: str) -> None:
        if (Name not in self.Tabs): return;
        entry = self.Tabs.pop(Name);
        UI.delete_item(entry.WindowTag);
        UI.delete_item(entry.ButtonTag);

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
                self.SetAmmo(1, self.GetValue("AmmoValue"), self.GetValue("AmmoType"));
            time.sleep(0.1);

    def LoopGunMods(self):
        while UI.is_dearpygui_running():
            if (self.GetValue("WeaponModsTimerToggle")):
                self.SetWeaponActionValue(0);
            time.sleep(self.GetValue("WeaponModsLoopDelay"));

    def LoopStamina(self):
        while UI.is_dearpygui_running():
            if (self.GetValue("InfiniteStaminaToggle")):
                self.SetStamina(20000);
            time.sleep(self.GetValue("InfiniteStaminaLoopDelay"));

    def BuildPlayerTab(self, Tab: str) -> None:
        self.AddLabel(Tab, "", "Health Changer");
        self.AddInputInt(Tab, "HealthValue", { "label": "Value", "min_value": 0, "max_value": 16959, "max_clamped": True, "min_clamped": True, "default_value": self.Config["HealthValue"], "width": 150 });
        self.AddButton(Tab, { "label": "Change", "width": 150, "height": TABBUTTONHEIGHT, "callback": lambda: self.SetHealth(self.GetValue("HealthValue")) });
        self.AddToggle(Tab, "HealthToggle", "Loop");
        self.AddDivider(Tab);
        self.AddLabel(Tab, "", "Armor Changer");
        self.AddInputInt(Tab, "ArmorValue", { "label": "Value", "min_value": 0, "max_value": 16959, "max_clamped": True, "min_clamped": True, "default_value": self.Config["ArmorValue"], "width": 150 });
        self.AddButton(Tab, {"label": "Change", "width": 150, "height": TABBUTTONHEIGHT, "callback": lambda: self.SetArmor(self.GetValue("ArmorValue"))});
        self.AddToggle(Tab, "ArmorToggle", "Loop");
        self.AddDivider(Tab);
        self.AddLabel(Tab, "", "Infinite Stamina");
        self.AddToggle(Tab, "InfiniteStaminaToggle", "Enabled");
        self.AddInputFloat(Tab, "InfiniteStaminaLoopDelay", { "label": "Stamina Loop Delay", "min_value": 0, "min_clamped": True, "default_value": self.Config["StaminaLoopDelay"], "format": "%.2f", "width": 150 });

    def BuildWeaponTab(self, Tab: str) -> None:
        self.AddLabel(Tab, "", "Ammo Changer");
        self.AddInputInt(Tab, "AmmoValue", { "label": "Ammo Value", "min_value": 0, "max_value": 16959, "max_clamped": True, "min_clamped": True, "default_value": self.Config["AmmoValue"], "width": 150 });
        self.AddDropdown(Tab, "AmmoType", { "label": "Ammo Type", "items": ("Ammo", "Bullets", "Both"), "default_value": "Ammo", "width": 150 });
        self.AddLabel(Tab, "CurrentWeaponLabel", "Current Weapon: None");
        self.AddButton(Tab, { "label": "Set Ammo", "width": 150, "height": TABBUTTONHEIGHT, "callback": lambda: self.SetAmmo(1, self.GetValue("AmmoValue"), self.GetValue("AmmoType")) } );
        self.AddToggle(Tab, "AmmoToggle", "Loop");
        self.AddDivider(Tab);
        self.AddLabel(Tab, "WeaponModsTitle", "Gun Mods");
        self.AddInputFloat(Tab, "WeaponModsLoopDelay", { "label": "Gun Mods Loop Delay", "min_value": 0, "min_clamped": True, "default_value": self.Config["GunMods"]["LoopDelay"], "format": "%.3f", "width": 150 });
        self.AddToggle(Tab, "WeaponModsTimerToggle", "Gun Timer Enabled");

    def BuildSettingsTab(self, Tab: str) -> None:
        UI.set_item_pos("Button_Settings", [8, 280]);

    def BuildUI(self) -> None:
        UI.create_context();
        Viewport = UI.create_viewport(title = "RealRTCW Trainer", width = WINDOWWIDTH, height = WINDOWHEIGHT, decorated = False, resizable = False);
        UI.setup_dearpygui();
        UI.show_viewport();
        with UI.window(label = "RealRTCW Trainer", tag = "MainWindow", width = WINDOWWIDTH, height = WINDOWHEIGHT, no_title_bar = False, no_resize = True, no_move = True, no_collapse = True, no_scroll_with_mouse = True, no_scrollbar = True, on_close = self.OnExit):
            UI.add_child_window(label = "Tabs", tag = "TabHolder", width = TABPANELWIDTH, height = TABPANELHEIGHT, pos = (5, 22));
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

            def ToggleViewport():
                UI.minimize_viewport();

            with UI.handler_registry():
                UI.add_key_press_handler(key = 161, callback = ToggleViewport)
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
        if (not self.Attach()): return;
        self.BuildUI();
        UI.start_dearpygui();

if (__name__ == "__main__"):
    Trainer().Run();
