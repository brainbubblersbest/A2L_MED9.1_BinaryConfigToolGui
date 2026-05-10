# MED9.1 ECU Konfigurator

## Windows .exe herunterladen – Schritt für Schritt

### Einmalige Einrichtung (~10 Minuten, danach automatisch)

**1. GitHub-Account erstellen** (kostenlos)
→ https://github.com/signup

**2. Neues Repository anlegen**
- Auf github.com: grüner Button **"New"** oben links
- Name: `med91-konfigurator`
- Sichtbarkeit: **Private** (empfohlen)
- **"Create repository"** klicken

**3. Dieses ZIP hochladen**
- Im neuen Repository: **"uploading an existing file"** klicken
- Alle Dateien aus diesem ZIP per Drag & Drop ins Browser-Fenster ziehen
- **Commit changes** klicken

**4. Build startet automatisch**
- Oben im Repository auf den Tab **"Actions"** klicken
- Du siehst "Build Windows Installer" mit einem orangen Kreis (läuft)
- Nach ca. 3–5 Minuten: grüner Haken ✓

**5. EXE herunterladen**
- Auf den grünen Build-Eintrag klicken
- Ganz unten: **"Artifacts"** → **"MED91_Konfigurator_Windows"** klicken
- ZIP herunterladen → darin liegt:
  - `MED91_Konfigurator_Setup_v1.0.0.exe` ← **das ist der Installer**
  - `MED91_Konfigurator.exe` ← portable, direkt startbar

---

### Was der Installer macht (für Endnutzer)

Doppelklick auf `MED91_Konfigurator_Setup_v1.0.0.exe`:
- Setup-Wizard mit Haftungsausschluss
- Installation ohne Admin-Rechte (in Benutzerordner)
- Desktop-Icon (optional)
- Startmenü-Eintrag
- Deinstallation über Windows "Apps & Features"

### Bei jedem Update

Dateien ändern → committen → GitHub baut automatisch neue .exe.

---

## Programm-Bedienung

1. **Öffnen**: A2L-Datei wählen, dann Binary (.bin)
2. **Navigation**: Linker Baum → Kategorie wählen
   - 📡 Sensoren (HFM, Lambda, Temperaturen, Druck...)
   - ⚙ Aktoren (Drosselklappe, Einspritzung, Zündung, HDP...)
   - 🔄 Programmablauf (Kennfelder, Momente, CAN, Diagnose...)
3. **Editieren**: Characteristic anklicken → Wert ändern → Übernehmen
4. **Speichern**: Strg+S (erstellt automatisch .bak Backup)
5. **Hex-Diff**: Alle Änderungen vor dem Speichern prüfen

## ⚠ Hinweis zur Flash-Basisadresse

MED9.1 verwendet typisch `0x80000000`.  
Falls Werte nicht lesbar: in `ui/main_window.py` anpassen:
```python
base_addr = 0x80000000
```
