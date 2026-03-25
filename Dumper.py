import json;
from dataclasses import dataclass;
import requests;
import pyMeow;

ProcessName = "RealRTCW.x64.exe";
QaGameDll = "qagame_sp_x64.dll";

PlayerPointer = 0x004F0D48;

@dataclass
class GameProcess:
    Process: object | None = None;
    ModuleBase: int = 0;
    QaGameBase: int = 0;
    @property
    def IsOpen(self) -> bool:
        return (self.Process is not None);

@dataclass
class Offset:
    Pattern: str;
    Skip: int;

OffsetBase = {};

class Dumper:
    def __init__(self):
        self.Game = GameProcess();
        self.Offsets = OffsetBase;
        self.Patterns: dict = {};
        self.PlayerPointer: int = PlayerPointer;

    def Attach(self) -> bool:
        try:
            self.Game.Process = pyMeow.open_process(ProcessName);
            self.Game.ModuleBase = pyMeow.get_module(self.Game.Process, ProcessName)["base"];
            self.Game.QaGameBase = pyMeow.get_module(self.Game.Process, QaGameDll)["base"];
            return True;
        except: return False;

    def GetPatterns(self):
        try:
            Response = requests.get("https://raw.githubusercontent.com/61netpa/RealRTCW-Trainer/refs/heads/main/Patterns.json");
            if (Response.status_code == 200):
                Patterns = {};
                RawData = Response.json();
                for Index, Value in RawData.items():
                    Patterns[Index] = Offset(Value[0], Value[1]);
                return Patterns;
            return {};
        except Exception as Error:
            print(f"Couldn't get the patterns, Error: {Error}");
            return {};

    def DumpOffset(self, Pattern: Offset, Type: str) -> int | None:
        if (not self.Game.Process or not self.Game.QaGameBase): return None;
        try:
            Address = pyMeow.aob_scan_module(self.Game.Process, QaGameDll, Pattern.Pattern);
            if (Address is None): return None;
            if (Type == "Int"):
                return pyMeow.r_int(self.Game.Process, Address[0] + Pattern.Skip);
            elif (Type == "Byte"):
                return pyMeow.r_byte(self.Game.Process, Address[0] + Pattern.Skip);
        except Exception as Error:
            print(f"Couldn't get the offset, Error: {Error}");
            return None;

    def Run(self) -> None:
        if (not self.Attach()):
            print("Unable to dump offsets due to game process being not found.");
            return;
        try:
            self.Patterns = self.GetPatterns();
            self.Offsets["Health"] = self.DumpOffset(self.Patterns["Health"], "Int");
            self.Offsets["Armor"] = self.DumpOffset(self.Patterns["Armor"], "Int");
            self.Offsets["Stamina"] = self.DumpOffset(self.Patterns["Stamina"], "Int");
            self.Offsets["CurrentWeapon"] = self.DumpOffset(self.Patterns["CurrentWeapon"], "Int");
            self.Offsets["BulletsArray"] = self.DumpOffset(self.Patterns["BulletsArray"], "Int");
            self.Offsets["AmmoArray"] = self.DumpOffset(self.Patterns["AmmoArray"], "Int");
            self.Offsets["WeaponAction"] = self.DumpOffset(self.Patterns["WeaponAction"], "Byte");
            self.Offsets["Spread"] = self.DumpOffset(self.Patterns["Spread"], "Int");
            with open("Offsets.json", "w") as File:
                json.dump({ "HealthPointer": self.PlayerPointer, "PlayerPointer": self.PlayerPointer - 8, **self.Offsets }, File, indent = 4);
            print("Successfully dumped offsets!");
        except Exception as Error:
            print(f"Couldn't dump offsets, Error: {Error}");

if (__name__ == "__main__"):
    Dumper().Run();
