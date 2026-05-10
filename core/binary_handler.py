"""
Binary Reader/Writer für MED9.1 Steuergeräte-Flashdateien.
Liest und schreibt Rohwerte an ECU-Adressen mit Byteorder-Support.
"""

import struct
import shutil
import os
from typing import Optional
from dataclasses import dataclass
from core.a2l_parser import DataType, Characteristic, CompuMethod, CharType, RecordLayout


@dataclass
class RawValue:
    address: int
    raw: float | int | list
    phys: float | list
    unit: str = ""


class BinaryHandler:
    """
    Liest/Schreibt MED9.1 BIN-Dateien.
    Unterstützt Little-Endian (Standard Bosch MED9.x).
    """

    BYTE_ORDER = "<"  # Little-Endian

    def __init__(self):
        self._data: bytearray = bytearray()
        self._filepath: str = ""
        self._base_address: int = 0  # Flash-Basisadresse (z.B. 0x80000000)
        self._original_data: bytes = b""
        self.is_loaded: bool = False

    def load(self, filepath: str, base_address: int = 0) -> bool:
        try:
            with open(filepath, "rb") as f:
                raw = f.read()
            self._data = bytearray(raw)
            self._original_data = bytes(raw)
            self._filepath = filepath
            self._base_address = base_address
            self.is_loaded = True
            print(f"BIN geladen: {len(raw):,} Bytes ({len(raw)/1024:.1f} KB)")
            return True
        except Exception as e:
            print(f"BIN Ladefehler: {e}")
            return False

    def _addr_to_offset(self, address: int) -> int:
        """Konvertiert ECU-Adresse zu Datei-Offset."""
        offset = address - self._base_address
        if offset < 0:
            # Fallback: Direkt als Offset interpretieren
            offset = address
        return offset

    def _get_datatype_info(self, dtype: DataType) -> tuple:
        """Gibt (format_string, size) zurück."""
        return (self.BYTE_ORDER + dtype.fmt, dtype.size)

    def read_value(self, address: int, dtype: DataType) -> Optional[float]:
        """Liest einen skalaren Wert."""
        offset = self._addr_to_offset(address)
        fmt, size = self._get_datatype_info(dtype)

        if offset < 0 or offset + size > len(self._data):
            return None

        try:
            value = struct.unpack_from(fmt, self._data, offset)[0]
            return float(value)
        except Exception as e:
            print(f"Read error @{hex(address)}: {e}")
            return None

    def write_value(self, address: int, dtype: DataType, value: float) -> bool:
        """Schreibt einen skalaren Wert."""
        offset = self._addr_to_offset(address)
        fmt, size = self._get_datatype_info(dtype)

        if offset < 0 or offset + size > len(self._data):
            return False

        try:
            if dtype in (DataType.FLOAT32_IEEE, DataType.FLOAT64_IEEE):
                packed = struct.pack(fmt, float(value))
            elif dtype in (DataType.UBYTE, DataType.UWORD, DataType.ULONG):
                packed = struct.pack(fmt, int(round(value)))
            else:
                packed = struct.pack(fmt, int(round(value)))
            self._data[offset:offset + size] = packed
            return True
        except Exception as e:
            print(f"Write error @{hex(address)}: {e}")
            return False

    def read_array(self, address: int, dtype: DataType, count: int) -> Optional[list]:
        """Liest ein Array von Werten (für Kurven/Kennfelder)."""
        offset = self._addr_to_offset(address)
        fmt, size = self._get_datatype_info(dtype)

        if offset < 0 or offset + size * count > len(self._data):
            return None

        try:
            values = []
            for i in range(count):
                v = struct.unpack_from(fmt, self._data, offset + i * size)[0]
                values.append(float(v))
            return values
        except Exception as e:
            print(f"Array read error @{hex(address)}: {e}")
            return None

    def write_array(self, address: int, dtype: DataType, values: list) -> bool:
        """Schreibt ein Array."""
        offset = self._addr_to_offset(address)
        fmt, size = self._get_datatype_info(dtype)

        if offset < 0 or offset + size * len(values) > len(self._data):
            return False

        try:
            for i, v in enumerate(values):
                if dtype in (DataType.FLOAT32_IEEE, DataType.FLOAT64_IEEE):
                    packed = struct.pack(fmt, float(v))
                else:
                    packed = struct.pack(fmt, int(round(float(v))))
                self._data[offset + i * size:offset + (i + 1) * size] = packed
            return True
        except Exception as e:
            print(f"Array write error @{hex(address)}: {e}")
            return False

    def get_diff(self) -> list:
        """Gibt alle geänderten Bytes als Liste zurück."""
        diffs = []
        for i, (orig, new) in enumerate(zip(self._original_data, self._data)):
            if orig != new:
                diffs.append((i + self._base_address, orig, new))
        return diffs

    def save(self, filepath: str = None) -> bool:
        """Speichert die modifizierte Binary."""
        target = filepath or self._filepath
        if not target:
            return False
        try:
            # Backup erstellen
            backup = target + ".bak"
            if not os.path.exists(backup):
                shutil.copy2(self._filepath, backup)
            with open(target, "wb") as f:
                f.write(self._data)
            # Original für diff-Tracking aktualisieren
            self._original_data = bytes(self._data)
            return True
        except Exception as e:
            print(f"Save error: {e}")
            return False

    def save_as(self, filepath: str) -> bool:
        return self.save(filepath)

    def discard_changes(self):
        """Verwirft alle Änderungen."""
        self._data = bytearray(self._original_data)

    @property
    def size(self) -> int:
        return len(self._data)

    @property
    def has_changes(self) -> bool:
        return self._data != self._original_data

    @property
    def change_count(self) -> int:
        return len(self.get_diff())


class CharacteristicIO:
    """
    High-Level Lese-/Schreiboperationen für A2L Characteristics.
    Kombiniert BinaryHandler + A2LParser-Metadaten.
    """

    def __init__(self, binary: BinaryHandler, compu_methods: dict, record_layouts: dict):
        self.binary = binary
        self.compu_methods = compu_methods
        self.record_layouts = record_layouts

    def _get_dtype(self, char: Characteristic) -> DataType:
        """Ermittelt den Datentyp aus dem RecordLayout."""
        rl = self.record_layouts.get(char.record_layout)
        if rl and rl.fnc_values:
            return rl.fnc_values[1]
        return DataType.UWORD  # Fallback

    def _get_compu(self, char: Characteristic) -> Optional[CompuMethod]:
        return self.compu_methods.get(char.compu_method)

    def read_scalar(self, char: Characteristic) -> Optional[RawValue]:
        """Liest einen Skalaren Wert (VALUE)."""
        dtype = self._get_dtype(char)
        raw = self.binary.read_value(char.address, dtype)
        if raw is None:
            return None

        compu = self._get_compu(char)
        phys = compu.convert(raw) if compu else raw

        return RawValue(address=char.address, raw=raw, phys=phys, unit=char.unit)

    def write_scalar(self, char: Characteristic, phys_value: float) -> bool:
        """Schreibt einen physikalischen Wert (konvertiert zu RAW)."""
        dtype = self._get_dtype(char)
        compu = self._get_compu(char)
        raw = compu.inverse(phys_value) if compu else phys_value
        return self.binary.write_value(char.address, dtype, raw)

    def read_curve(self, char: Characteristic) -> Optional[dict]:
        """Liest eine Kennlinie (CURVE): X-Achse + Werte."""
        if char.char_type != CharType.CURVE:
            return None

        dtype = self._get_dtype(char)
        compu = self._get_compu(char)

        # Größe der X-Achse aus AXIS_DESCR
        if not char.axis_x:
            return None

        n = char.axis_x.max_axis_points
        axis_dtype = DataType.UWORD
        rl = self.record_layouts.get(char.record_layout)
        if rl and rl.axis_pts_x:
            axis_dtype = rl.axis_pts_x[1]

        axis_offset = axis_dtype.size * n

        # X-Achse lesen
        x_raw = self.binary.read_array(char.address, axis_dtype, n)
        # Y-Werte lesen (direkt nach X-Achse im Speicher)
        y_raw = self.binary.read_array(char.address + axis_offset, dtype, n)

        if x_raw is None or y_raw is None:
            return None

        axis_compu = self.compu_methods.get(char.axis_x.compu_method)
        x_phys = [axis_compu.convert(v) if axis_compu else v for v in x_raw]
        y_phys = [compu.convert(v) if compu else v for v in y_raw]

        return {
            "n": n,
            "x_raw": x_raw, "x_phys": x_phys,
            "y_raw": y_raw, "y_phys": y_phys,
            "x_unit": char.axis_x.compu_method,
            "y_unit": char.unit,
        }

    def write_curve_y(self, char: Characteristic, y_phys: list) -> bool:
        """Schreibt Y-Werte einer Kennlinie."""
        if char.char_type != CharType.CURVE or not char.axis_x:
            return False

        dtype = self._get_dtype(char)
        compu = self._get_compu(char)
        n = char.axis_x.max_axis_points

        axis_dtype = DataType.UWORD
        rl = self.record_layouts.get(char.record_layout)
        if rl and rl.axis_pts_x:
            axis_dtype = rl.axis_pts_x[1]

        axis_offset = axis_dtype.size * n
        y_raw = [compu.inverse(v) if compu else v for v in y_phys]
        return self.binary.write_array(char.address + axis_offset, dtype, y_raw)

    def read_map(self, char: Characteristic) -> Optional[dict]:
        """Liest ein 2D-Kennfeld (MAP)."""
        if char.char_type != CharType.MAP:
            return None
        if not char.axis_x or not char.axis_y:
            return None

        dtype = self._get_dtype(char)
        compu = self._get_compu(char)
        nx = char.axis_x.max_axis_points
        ny = char.axis_y.max_axis_points

        rl = self.record_layouts.get(char.record_layout)
        axis_dtype_x = rl.axis_pts_x[1] if rl and rl.axis_pts_x else DataType.UWORD
        axis_dtype_y = rl.axis_pts_y[1] if rl and rl.axis_pts_y else DataType.UWORD

        addr = char.address
        x_raw = self.binary.read_array(addr, axis_dtype_x, nx)
        addr += axis_dtype_x.size * nx
        y_raw = self.binary.read_array(addr, axis_dtype_y, ny)
        addr += axis_dtype_y.size * ny
        z_raw = self.binary.read_array(addr, dtype, nx * ny)

        if x_raw is None or y_raw is None or z_raw is None:
            return None

        x_compu = self.compu_methods.get(char.axis_x.compu_method)
        y_compu = self.compu_methods.get(char.axis_y.compu_method) if char.axis_y else None

        x_phys = [x_compu.convert(v) if x_compu else v for v in x_raw]
        y_phys = [y_compu.convert(v) if y_compu else v for v in y_raw]
        z_phys = [[compu.convert(z_raw[i * ny + j]) if compu else z_raw[i * ny + j]
                   for j in range(ny)] for i in range(nx)]

        return {
            "nx": nx, "ny": ny,
            "x_raw": x_raw, "x_phys": x_phys,
            "y_raw": y_raw, "y_phys": y_phys,
            "z_raw": z_raw, "z_phys": z_phys,
            "z_unit": char.unit,
        }
