"""
A2L / ASAP2 Parser für MED9.1 Steuergerätebeschreibungen.
Unterstützt: MEASUREMENT, CHARACTERISTIC (VALUE, CURVE, MAP), COMPU_METHOD, RECORD_LAYOUT
"""

import re
import struct
from dataclasses import dataclass, field
from typing import Optional
from enum import Enum


class CharType(Enum):
    VALUE = "VALUE"
    CURVE = "CURVE"
    MAP = "MAP"
    VAL_BLK = "VAL_BLK"
    ASCII = "ASCII"


class DataType(Enum):
    UBYTE = ("UBYTE", "B", 1)
    SBYTE = ("SBYTE", "b", 1)
    UWORD = ("UWORD", "H", 2)
    SWORD = ("SWORD", "h", 2)
    ULONG = ("ULONG", "I", 4)
    SLONG = ("SLONG", "i", 4)
    FLOAT32_IEEE = ("FLOAT32_IEEE", "f", 4)
    FLOAT64_IEEE = ("FLOAT64_IEEE", "d", 8)

    def __init__(self, name, fmt, size):
        self._name = name
        self.fmt = fmt
        self.size = size

    @classmethod
    def from_str(cls, s: str):
        for m in cls:
            if m._name == s.upper():
                return m
        return cls.UWORD


@dataclass
class CompuMethod:
    name: str
    method: str = "IDENTICAL"  # LINEAR, TAB_VERB, IDENTICAL, RAT_FUNC
    unit: str = ""
    coeffs: list = field(default_factory=list)  # für LINEAR: [a, b] → y = ax + b
    tab: dict = field(default_factory=dict)       # für TAB_VERB

    def convert(self, raw) -> float:
        if self.method == "LINEAR" and len(self.coeffs) >= 2:
            return self.coeffs[0] * raw + self.coeffs[1]
        elif self.method == "RAT_FUNC" and len(self.coeffs) == 6:
            a, b, c, d, e, f = self.coeffs
            # y = (axx + bx + c) / (dxx + ex + f)
            num = a * raw * raw + b * raw + c
            den = d * raw * raw + e * raw + f
            return num / den if den != 0 else 0.0
        return float(raw)

    def inverse(self, phys) -> float:
        if self.method == "LINEAR" and len(self.coeffs) >= 2:
            a, b = self.coeffs[0], self.coeffs[1]
            return (phys - b) / a if a != 0 else 0.0
        elif self.method == "RAT_FUNC" and len(self.coeffs) == 6:
            a, b, c, d, e, f = self.coeffs
            # Für einfache RAT_FUNC: a=0,d=0 → linear: y=(bx+c)/(ex+f)
            if a == 0 and d == 0:
                num = phys * f - c
                den = b - phys * e
                return num / den if den != 0 else 0.0
        return float(phys)


@dataclass
class RecordLayout:
    name: str
    fnc_values: tuple = None   # (position, datatype, index_mode, addressing)
    axis_pts_x: tuple = None
    axis_pts_y: tuple = None


@dataclass
class Characteristic:
    name: str
    long_id: str
    char_type: CharType
    address: int
    record_layout: str
    max_diff: float
    compu_method: str
    lower_limit: float
    upper_limit: float
    # Achsen für CURVE/MAP
    axis_x: Optional['AxisDescr'] = None
    axis_y: Optional['AxisDescr'] = None
    # Aufgelöste Referenzen
    unit: str = ""
    description: str = ""
    # Kategorisierung
    category: str = "Sonstiges"
    subcategory: str = ""


@dataclass
class AxisDescr:
    name: str
    input_quantity: str
    compu_method: str
    lower_limit: float
    upper_limit: float
    max_axis_points: int
    address: int = 0
    axis_pts_ref: str = ""  # Referenz auf AXIS_PTS


@dataclass
class Measurement:
    name: str
    long_id: str
    datatype: DataType
    compu_method: str
    lower_limit: float
    upper_limit: float
    address: int
    unit: str = ""
    category: str = "Sonstiges"


class A2LParser:
    """Vollständiger ASAP2-Parser."""

    # Kategorisierungs-Keywords für MED9.1
    CATEGORY_MAP = {
        "Sensoren": {
            "Luftmassenmesser": ["HFM", "LMM", "LUFTMASSE", "MAF", "AIR_MASS"],
            "Lambdasonde": ["LAMBDA", "LSU", "LSH", "LSHK", "BREITBAND", "SPRUNG"],
            "Temperatursensoren": ["TEMP", "TKU", "TKUM", "KÜHLMITTEL", "ANSAUG", "ÖTEMP", "LADELUFT"],
            "Drucksensoren": ["DRUCK", "LADEDRUCK", "SAUGROHRDRUCK", "UMGEBUNGSDRUCK", "PS", "PU"],
            "Kurbelwellensensor": ["KW", "DREHZAHL", "NW", "NOCKENWELLE", "SYNC"],
            "Pedalwertgeber": ["PEDAL", "PWG", "FPW", "FAHRPEDAL"],
            "Klopfsensor": ["KLOPF", "KS", "KNOCK"],
        },
        "Aktoren": {
            "Drosselklappe": ["DK", "DROSSEL", "ETBL", "THROTTLE", "AIRFLAP"],
            "Einspritzventile": ["INJ", "EINSPRITZ", "MFF", "KRAFTSTOFF", "FUEL"],
            "Zündung": ["ZW", "ZÜND", "IGNITION", "ZZP", "ZÜNDWINKEL"],
            "Hochdruckpumpe": ["HDP", "HOCHDRUCK", "KRAFTSTOFFPUMPE", "HPFP"],
            "Ladebewegungsklappe": ["LBK", "LADEBEWEG", "TUMBLE", "SWIRL"],
            "Abgasrückführung": ["AGR", "EGR", "ABGAS"],
            "Turbolader": ["ATL", "VTG", "LADER", "BOOST", "LADEDRUCKREG"],
            "Nockenwelle": ["VANOS", "NWV", "NOCKENWELLENVER", "CAM_PHASING"],
        },
        "Programmablauf": {
            "Abgastemperaturmodell": ["ATMD", "ABGASTEMP", "EXHAUST_TEMP", "EGT"],
            "Momentenkoordination": ["MOME", "TORQUE", "MSTRU", "MRED", "MMAX"],
            "Getriebeabhängig": ["GET", "GEAR", "GANG", "GETRIEBE", "GS"],
            "Motorsteuerung": ["MOT", "ENGINE", "BETRIEB", "MODE"],
            "Diagnose": ["DIAG", "OBD", "DTC", "FEHLER", "ERROR"],
            "CAN-Matrix": ["CAN", "KLEM", "NM_", "BOTSCHAFT", "MESSAGE"],
            "Katalysatorheizung": ["KAT", "CAT", "HEIZ", "CATALYST"],
            "Klopfregelung": ["KLOPF", "KNOCK", "KR_"],
            "Leerlastregelung": ["LL", "IDLE", "LEERLAUF"],
            "Fahrprogramm": ["FAHR", "DRIVE", "MODE", "SPORT", "ECO"],
        },
    }

    def __init__(self):
        self.characteristics: dict[str, Characteristic] = {}
        self.measurements: dict[str, Measurement] = {}
        self.compu_methods: dict[str, CompuMethod] = {}
        self.record_layouts: dict[str, RecordLayout] = {}
        self._raw_text = ""

    def parse_file(self, filepath: str) -> bool:
        try:
            with open(filepath, "r", encoding="latin-1") as f:
                self._raw_text = f.read()
            self._parse()
            self._resolve_references()
            self._categorize()
            return True
        except Exception as e:
            print(f"A2L Parse Error: {e}")
            import traceback; traceback.print_exc()
            return False

    def _parse(self):
        text = self._remove_comments(self._raw_text)
        tokens = self._tokenize(text)
        self._parse_tokens(tokens)

    def _remove_comments(self, text: str) -> str:
        text = re.sub(r'/\*.*?\*/', ' ', text, flags=re.DOTALL)
        text = re.sub(r'//[^\n]*', ' ', text)
        return text

    def _tokenize(self, text: str) -> list:
        return re.findall(r'"[^"]*"|\S+', text)

    def _parse_tokens(self, tokens: list):
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok == "/begin":
                i += 1
                if i >= len(tokens):
                    break
                block = tokens[i]
                if block == "CHARACTERISTIC":
                    char, consumed = self._parse_characteristic(tokens, i + 1)
                    if char:
                        self.characteristics[char.name] = char
                    i += consumed
                elif block == "MEASUREMENT":
                    meas, consumed = self._parse_measurement(tokens, i + 1)
                    if meas:
                        self.measurements[meas.name] = meas
                    i += consumed
                elif block == "COMPU_METHOD":
                    cm, consumed = self._parse_compu_method(tokens, i + 1)
                    if cm:
                        self.compu_methods[cm.name] = cm
                    i += consumed
                elif block == "RECORD_LAYOUT":
                    rl, consumed = self._parse_record_layout(tokens, i + 1)
                    if rl:
                        self.record_layouts[rl.name] = rl
                    i += consumed
                else:
                    # Für bekannte Container (PROJECT, MODULE, A2ML etc.) → einfach weitermachen
                    # Unbekannte Blöcke: überspringe nur wenn sie keine relevanten Sub-Blöcke haben könnten
                    CONTAINERS = {"PROJECT", "MODULE", "IF_DATA", "A2ML", "VARIANT_CODING",
                                  "FRAME", "FUNCTION", "GROUP", "AXIS_PTS", "BLOB"}
                    if block in CONTAINERS:
                        pass  # Weiterlaufen lassen, Inhalt wird geparsed
                    else:
                        depth = 1
                        i += 1
                        while i < len(tokens) and depth > 0:
                            if tokens[i] == "/begin":
                                depth += 1
                            elif tokens[i] == "/end":
                                depth -= 1
                            i += 1
            else:
                i += 1

    def _parse_characteristic(self, tokens, start) -> tuple:
        """Parst einen CHARACTERISTIC Block."""
        i = start
        depth = 1
        block_tokens = []

        while i < len(tokens) and depth > 0:
            if tokens[i] == "/begin":
                depth += 1
                block_tokens.append(tokens[i])
            elif tokens[i] == "/end":
                depth -= 1
                if depth == 0:
                    i += 1  # überspringen "CHARACTERISTIC"
                    break
                block_tokens.append(tokens[i])
            else:
                block_tokens.append(tokens[i])
            i += 1

        consumed = i - start

        if len(block_tokens) < 8:
            return None, consumed

        try:
            idx = 0
            name = block_tokens[idx]; idx += 1
            long_id = block_tokens[idx].strip('"'); idx += 1
            char_type = CharType(block_tokens[idx]); idx += 1
            address = int(block_tokens[idx], 16) if '0x' in block_tokens[idx].lower() else int(block_tokens[idx], 16) if block_tokens[idx].startswith('0x') or block_tokens[idx].startswith('0X') else self._parse_address(block_tokens[idx])
            idx += 1
            record_layout = block_tokens[idx]; idx += 1
            max_diff = float(block_tokens[idx]); idx += 1
            compu_method = block_tokens[idx]; idx += 1
            lower_limit = float(block_tokens[idx]); idx += 1
            upper_limit = float(block_tokens[idx]); idx += 1

            char = Characteristic(
                name=name,
                long_id=long_id,
                char_type=char_type,
                address=address,
                record_layout=record_layout,
                max_diff=max_diff,
                compu_method=compu_method,
                lower_limit=lower_limit,
                upper_limit=upper_limit,
            )

            # Sub-Blöcke parsen (AXIS_DESCR etc.)
            j = idx
            while j < len(block_tokens):
                if block_tokens[j] == "/begin" and j + 1 < len(block_tokens):
                    if block_tokens[j + 1] == "AXIS_DESCR":
                        axis, adv = self._parse_axis_descr(block_tokens, j + 2)
                        if char.axis_x is None:
                            char.axis_x = axis
                        else:
                            char.axis_y = axis
                        j += adv
                    else:
                        j += 1
                else:
                    j += 1

            return char, consumed
        except Exception as e:
            return None, consumed

    def _parse_address(self, s: str) -> int:
        try:
            if s.startswith('0x') or s.startswith('0X'):
                return int(s, 16)
            return int(s)
        except:
            return 0

    def _parse_axis_descr(self, tokens, start) -> tuple:
        i = start
        depth = 1
        block_tokens = []
        while i < len(tokens) and depth > 0:
            if tokens[i] == "/begin":
                depth += 1
            elif tokens[i] == "/end":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            block_tokens.append(tokens[i])
            i += 1

        consumed = i - start + 2

        if len(block_tokens) < 5:
            return None, consumed

        try:
            idx = 0
            input_qty = block_tokens[idx]; idx += 1
            compu_method = block_tokens[idx]; idx += 1
            max_axis = int(block_tokens[idx]); idx += 1
            lower = float(block_tokens[idx]); idx += 1
            upper = float(block_tokens[idx]); idx += 1

            axis = AxisDescr(
                name="",
                input_quantity=input_qty,
                compu_method=compu_method,
                max_axis_points=max_axis,
                lower_limit=lower,
                upper_limit=upper,
            )

            # AXIS_PTS_REF suchen
            for k in range(idx, len(block_tokens) - 1):
                if block_tokens[k] == "AXIS_PTS_REF":
                    axis.axis_pts_ref = block_tokens[k + 1]
                    break

            return axis, consumed
        except:
            return None, consumed

    def _parse_measurement(self, tokens, start) -> tuple:
        i = start
        block_tokens = []
        depth = 1
        while i < len(tokens) and depth > 0:
            if tokens[i] == "/begin":
                depth += 1
            elif tokens[i] == "/end":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            block_tokens.append(tokens[i])
            i += 1
        consumed = i - start

        if len(block_tokens) < 7:
            return None, consumed

        try:
            name = block_tokens[0]
            long_id = block_tokens[1].strip('"')
            datatype = DataType.from_str(block_tokens[2])
            compu_method = block_tokens[3]
            # resolution, accuracy, lower, upper
            idx = 4
            _ = block_tokens[idx]; idx += 1  # resolution
            _ = block_tokens[idx]; idx += 1  # accuracy
            lower = float(block_tokens[idx]); idx += 1
            upper = float(block_tokens[idx]); idx += 1
            address = 0
            for k in range(idx, len(block_tokens) - 1):
                if block_tokens[k] == "ECU_ADDRESS":
                    address = self._parse_address(block_tokens[k + 1])
                    break

            return Measurement(
                name=name, long_id=long_id, datatype=datatype,
                compu_method=compu_method, lower_limit=lower,
                upper_limit=upper, address=address
            ), consumed
        except:
            return None, consumed

    def _parse_compu_method(self, tokens, start) -> tuple:
        i = start
        block_tokens = []
        depth = 1
        while i < len(tokens) and depth > 0:
            if tokens[i] == "/begin":
                depth += 1
            elif tokens[i] == "/end":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            block_tokens.append(tokens[i])
            i += 1
        consumed = i - start

        if len(block_tokens) < 3:
            return None, consumed

        try:
            name = block_tokens[0]
            long_id = block_tokens[1].strip('"')
            method = block_tokens[2]
            unit = block_tokens[4].strip('"') if len(block_tokens) > 4 else ""

            cm = CompuMethod(name=name, method=method, unit=unit)

            # COEFFS_LINEAR oder COEFFS suchen
            for k in range(len(block_tokens) - 1):
                if block_tokens[k] == "COEFFS_LINEAR" and k + 2 < len(block_tokens):
                    try:
                        a = float(block_tokens[k + 1])
                        b = float(block_tokens[k + 2])
                        cm.coeffs = [a, b]
                        cm.method = "LINEAR"
                    except:
                        pass
                elif block_tokens[k] == "COEFFS" and k + 6 < len(block_tokens):
                    try:
                        coeffs = [float(block_tokens[k + j]) for j in range(1, 7)]
                        cm.coeffs = coeffs
                        if method not in ("LINEAR", "RAT_FUNC"):
                            cm.method = "RAT_FUNC"
                    except:
                        pass

            return cm, consumed
        except:
            return None, consumed

    def _parse_record_layout(self, tokens, start) -> tuple:
        i = start
        block_tokens = []
        depth = 1
        while i < len(tokens) and depth > 0:
            if tokens[i] == "/begin":
                depth += 1
            elif tokens[i] == "/end":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            block_tokens.append(tokens[i])
            i += 1
        consumed = i - start

        if not block_tokens:
            return None, consumed

        try:
            name = block_tokens[0]
            rl = RecordLayout(name=name)

            for k in range(1, len(block_tokens) - 2):
                if block_tokens[k] == "FNC_VALUES":
                    try:
                        pos = int(block_tokens[k + 1])
                        dtype = DataType.from_str(block_tokens[k + 2])
                        rl.fnc_values = (pos, dtype)
                    except:
                        pass
                elif block_tokens[k] == "AXIS_PTS_X":
                    try:
                        pos = int(block_tokens[k + 1])
                        dtype = DataType.from_str(block_tokens[k + 2])
                        rl.axis_pts_x = (pos, dtype)
                    except:
                        pass
                elif block_tokens[k] == "AXIS_PTS_Y":
                    try:
                        pos = int(block_tokens[k + 1])
                        dtype = DataType.from_str(block_tokens[k + 2])
                        rl.axis_pts_y = (pos, dtype)
                    except:
                        pass

            return rl, consumed
        except:
            return None, consumed

    def _resolve_references(self):
        """Löst CompuMethod-Referenzen auf und trägt Einheiten ein."""
        for char in self.characteristics.values():
            if char.compu_method in self.compu_methods:
                cm = self.compu_methods[char.compu_method]
                char.unit = cm.unit

    def _categorize(self):
        """Ordnet Characteristics und Measurements den Kategorien zu."""
        for name, char in self.characteristics.items():
            char.category, char.subcategory = self._find_category(name, char.long_id)
        for name, meas in self.measurements.items():
            meas.category, _ = self._find_category(name, meas.long_id)

    def _find_category(self, name: str, long_id: str) -> tuple:
        search = (name + " " + long_id).upper()
        for category, subcats in self.CATEGORY_MAP.items():
            for subcat, keywords in subcats.items():
                for kw in keywords:
                    if kw.upper() in search:
                        return category, subcat
        return "Sonstiges", ""

    def get_categories(self) -> dict:
        """Gibt alle Kategorien mit ihren Characteristics zurück."""
        result = {}
        for char in self.characteristics.values():
            cat = char.category
            sub = char.subcategory or "Allgemein"
            if cat not in result:
                result[cat] = {}
            if sub not in result[cat]:
                result[cat][sub] = []
            result[cat][sub].append(char)
        return result

    def stats(self) -> dict:
        return {
            "characteristics": len(self.characteristics),
            "measurements": len(self.measurements),
            "compu_methods": len(self.compu_methods),
            "record_layouts": len(self.record_layouts),
        }
