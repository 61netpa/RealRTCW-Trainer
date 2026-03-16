from __future__ import annotations;
from dataclasses import dataclass;
import time;
import threading;
import pyMeow;
import dearpygui.dearpygui as UI;

PROCESSNAME = "RealRTCW.x64.exe";
QAGAMEDLL = "qagame_sp_x64.dll";
Weapons = { 0: "None", 1: "Knife", 2: "Luger", 3: "Luger Silencer", 4: "Colt", 5: "TT33", 6: "1905 Revolver", 7: "HDM", 10: "MP40", 14: "MP34", 12: "Sten", 11: "Thompson", 13: "PPSH41", 15: "Kar98", 43: "Kar98", 16: "Snooper Rifle", 44: "Snooper Rifle", 17: "Mosin Nagant", 23: "FG42", 47: "FG42", 22: "Stg44", 24: "BAR", 33: "Grenades", 34: "Pineapples", 35: "Dynamite", 39: "Poison Gas", 25: "Ithaca", 20: "G43", 19: "M1 Garand", 48: "M1 Garand Grenade", 29: "Panzerfaust", 30: "Flamethrower", 27: "Browning", 28: "MG42", 31: "Venom Gun", 32: "Tesla" };
DualWeapons = { 8: "Dual Colt", 9: "Dual TT33" };

WINDOWWIDTH, WINDOWHEIGHT = 630, 335;
TABPANELWIDTH, TABPANELHEIGHT = 110, 308;
TABWIDTH, TABHEIGHT = 505, 308;
TABBUTTONWIDTH, TABBUTTONHEIGHT = 95, 20;
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
    windowTag: str;
    buttonTag: str;

@dataclass
class WeaponOffsets:
    Bullets: int;
    Ammo: int | None = None;

Offsets = {
    "Health": 0x184B74, "Armor": 0x12C3D8, "CurrentWeapon": 0x12C3A4, "Stamina": 0x12C814, "WeaponAction": 0x12C32C,
    "Weapons": {
        # Knives
        "Knife": WeaponOffsets(0x12C5D4, 0x12C5D4),
        # Pistols
        "Luger": WeaponOffsets(0x12C5D8, 0x12C4D8), "Luger Silencer": WeaponOffsets(0x12C5DC, 0x12C4D8), "Colt": WeaponOffsets(0x12C5E0, 0x12C4E0),
        "Dual Colt": WeaponOffsets(0x12C5F0, 0x12C4E0), "TT33": WeaponOffsets(0x12C5E4, 0x12C4E4), "Dual TT33": WeaponOffsets(0x12C5F4, 0x12C4E4),
        "1905 Revolver": WeaponOffsets(0x12C5E8, 0x12C4E8), "HDM": WeaponOffsets(0x12C5EC, 0x12C4EC),
        # SMGs
        "MP40": WeaponOffsets(0x12C5F8, 0x12C4D8), "MP34": WeaponOffsets(0x12C5F8, 0x12C4D8), "Sten": WeaponOffsets(0x12C500, 0x12C4D8),
        "Thompson": WeaponOffsets(0x12C5FC, 0x12C4E4), "PPSH41": WeaponOffsets(0x12C604, 0x12C4E4),
        # Rifles
        "Kar98": WeaponOffsets(0x12C60C, 0x12C50C), "Snooper Rifle": WeaponOffsets(0x12C610, 0x12C510), "Mosin Nagant": WeaponOffsets(0x12C614, 0x12C514),
        # Assault Rifles
        "FG42": WeaponOffsets(0x12C62C, 0x12C50C), "Stg44": WeaponOffsets(0x12C628, 0x12C528), "BAR": WeaponOffsets(0x12C630, 0x12C51C),
        # Grenades
        "Grenades": WeaponOffsets(0x12C654, 0x12C654), "Pineapples": WeaponOffsets(0x12C658, 0x12C658), "Dynamite": WeaponOffsets(0x12C65C, 0x12C65C),
        "Poison Gas": WeaponOffsets(0x12C66C, 0x12C66C),
        # Shotguns
        "Ithaca": WeaponOffsets(0x12C634, 0x12C534),
        # Automatic Rifles
        "G43": WeaponOffsets(0x12C620, 0x12C50C), "M1 Garand": WeaponOffsets(0x12C61C, 0x12C51C), "M1 Garand Grenade": WeaponOffsets(0x12C690, 0x12C590),
        # Heavy Weapons
        "Panzerfaust": WeaponOffsets(0x12C644, 0x12C544), "Flamethrower": WeaponOffsets(0x12C648, 0x12C648), "MG42": WeaponOffsets(0x12C640, 0x12C540),
        "Browning": WeaponOffsets(0x12C63C, 0x12C540),
        # Secret Weapons
        "Venom Gun": WeaponOffsets(0x12C64C, 0x12C540), "Tesla": WeaponOffsets(0x12C650, 0x12C650)
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

    def GetCurrentWeapon(self) -> list:
        if (not self.Game.IsOpen or not self.Game.QaGameBase): return ["Unknown", None];
        try:
            WeaponAddress = self.Game.QaGameBase + Offsets["CurrentWeapon"];
            if (self.IsAddressValid(WeaponAddress)):
                Weapon = pyMeow.r_int64(self.Game.Process, WeaponAddress);
                if (Weapon in Weapons):
                    return [Weapons[Weapon], False];
                elif (Weapon in DualWeapons):
                    return [DualWeapons[Weapon], True];
            return ["Unknown", None];
        except Exception as ex:
            print(f"Couldn't get the current weapon, Error: {ex}");
            return ["Unknown", None];

    def SetAmmo(self, WeaponValue: int | None, Value: int, Type: str) -> None:
        if (not self.Game.IsOpen or not self.Game.QaGameBase): return;
        try:
            Weapon = self.GetCurrentWeapon();
            if (Weapon and Weapon[0] and Weapon[0] != "Unknown"):
                if (Type != "Both"):
                    if (Weapon[1]):
                        PrimaryWeaponAddress = self.Game.QaGameBase + getattr(Offsets[Weapon[0]], Type);
                        if (self.IsAddressValid(PrimaryWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, PrimaryWeaponAddress, Value);
                        SecondaryWeaponAddress = self.Game.QaGameBase + getattr(Offsets[Weapon[0].replace("Dual ", "")], Type);
                        if (self.IsAddressValid(SecondaryWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, SecondaryWeaponAddress, Value);
                    else:
                        CurrentWeaponAddress = self.Game.QaGameBase + getattr(Offsets[Weapon[0]], Type);
                        if (self.IsAddressValid(CurrentWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, CurrentWeaponAddress, Value);
                else:
                    if (Weapon[1]):
                        PrimaryBulletsWeaponAddress = self.Game.QaGameBase + Offsets[Weapon[0]].Bullets;
                        if (self.IsAddressValid(PrimaryBulletsWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, PrimaryBulletsWeaponAddress, Value);
                        PrimaryAmmoWeaponAddress = self.Game.QaGameBase + Offsets[Weapon[0]].Ammo;
                        if (self.IsAddressValid(PrimaryAmmoWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, PrimaryAmmoWeaponAddress, Value);
                        SecondaryBulletsWeaponAddress = self.Game.QaGameBase + Offsets[Weapon[0].replace("Dual ", "")].Bullets;
                        if (self.IsAddressValid(SecondaryBulletsWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, SecondaryBulletsWeaponAddress, Value);
                        SecondaryAmmoWeaponAddress = self.Game.QaGameBase + Offsets[Weapon[0].replace("Dual ", "")].Ammo;
                        if (self.IsAddressValid(SecondaryAmmoWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, SecondaryAmmoWeaponAddress, Value);
                    else:
                        CurrentBulletsWeaponAddress = self.Game.QaGameBase + Offsets[Weapon[0]].Bullets;
                        if (self.IsAddressValid(CurrentBulletsWeaponAddress)):
                            pyMeow.w_int(self.Game.Process, CurrentBulletsWeaponAddress, Value);
                        CurrentAmmoWeaponAddress = self.Game.QaGameBase + Offsets[Weapon[0]].Ammo;
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
            UI.hide_item(entry.windowTag);

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
        UI.delete_item(entry.windowTag);
        UI.delete_item(entry.buttonTag);

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
            UI.set_value("CurrentWeaponLabel", f"Current Weapon: {self.GetCurrentWeapon()[0]}");
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

            def CheckDrag(_, Data):
                if UI.is_mouse_button_down(0):
                    Y = Data[1];
                    if (-2 <= Y <= 19 and not self.Window["Dragging"]):
                        self.Window["Dragging"] = True;
                else:
                    self.Window["Dragging"] = False;

            def Drag(_, Data):
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

            with UI.handler_registry():
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

if __name__ == "__main__":
    Trainer().Run();