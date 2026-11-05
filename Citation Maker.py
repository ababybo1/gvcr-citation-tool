# ─────────────────────────────────────────────────────────────────────────────
#  GVCR Citation Tool v2.3  ·  by x3alpy and ababyboi
#  if you use this code without my permission I will take your soul
#  Greenville Community Roleplay  ·  Public Services
# ─────────────────────────────────────────────────────────────────────────────
import os, sys
if getattr(sys, "frozen", False):
    os.chdir(os.path.dirname(sys.executable))

import subprocess, importlib, re, base64, io, time, threading, urllib.request, queue, json, datetime, difflib

def ensure(pkg, imp=None):
    try: importlib.import_module(imp or pkg)
    except ImportError:
        si = None; kw = {}
        if sys.platform == "win32":
            si = subprocess.STARTUPINFO()
            si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
            si.wShowWindow = subprocess.SW_HIDE
            kw["creationflags"] = subprocess.CREATE_NO_WINDOW
        subprocess.check_call([sys.executable, "-m", "pip", "install", pkg, "--quiet"],
                              startupinfo=si, **kw)

ensure("pyperclip")

import tkinter as tk
from tkinter import messagebox
import pyperclip

# ── Embedded Logo ─────────────────────────────────────────────────────────────
LOGO_B64_48  = "LOGO48"
LOGO_B64_110 = "LOGO110"

# ── Theme Presets ──────────────────────────────────────────────────────────────
# Semantic colors (classification / branding) stay constant across all themes
# so meaning never changes. Only the "look" palette below is swappable.
GREEN    = "#22c55e"
GREEN_D  = "#052e16"
ORANGE   = "#f97316"
ORANGE_D = "#431407"
RED      = "#ef4444"
RED_D    = "#3b0a0a"
YELLOW   = "#eab308"
CYAN     = "#06b6d4"
GOLD     = "#b45309"
GOLD_H   = "#fde047"

THEMES = {
    "Midnight Blue": dict(BG="#05070d", PANEL="#080e1a", CARD="#0c1423", CARD2="#0f192c",
                           BORDER="#162035", BORDER2="#1c2d48", ACCENT="#3b82f6", ACCENT_H="#60a5fa",
                           INDIGO="#6366f1", INDIGO_H="#818cf8", TEXT="#f1f5f9", TEXT2="#94a3b8",
                           MUTED="#475569", MUTED2="#1e293b", SEL="#1e3a5f", INPUT_BG="#080f1e"),
    "Slate":        dict(BG="#0a0a0c", PANEL="#131316", CARD="#18181c", CARD2="#1e1e23",
                           BORDER="#2a2a30", BORDER2="#34343c", ACCENT="#71717a", ACCENT_H="#a1a1aa",
                           INDIGO="#8b8b95", INDIGO_H="#adadb8", TEXT="#f4f4f5", TEXT2="#a1a1aa",
                           MUTED="#52525b", MUTED2="#27272a", SEL="#3f3f46", INPUT_BG="#0f0f12"),
    "Emerald":      dict(BG="#04100a", PANEL="#08170f", CARD="#0b1f14", CARD2="#0f2819",
                           BORDER="#173a26", BORDER2="#1d4a2f", ACCENT="#10b981", ACCENT_H="#34d399",
                           INDIGO="#0d9488", INDIGO_H="#2dd4bf", TEXT="#ecfdf5", TEXT2="#a7f3d0",
                           MUTED="#3f6a52", MUTED2="#1a3324", SEL="#155e3f", INPUT_BG="#061a10"),
    "Crimson":      dict(BG="#10040a", PANEL="#180810", CARD="#1f0b15", CARD2="#280f1b",
                           BORDER="#3a1727", BORDER2="#4a1d31", ACCENT="#e11d48", ACCENT_H="#fb7185",
                           INDIGO="#be123c", INDIGO_H="#f43f5e", TEXT="#fff1f2", TEXT2="#fda4af",
                           MUTED="#6a3f4c", MUTED2="#331a24", SEL="#5e1530", INPUT_BG="#1a0610"),
    "Cyberpunk":    dict(BG="#08040f", PANEL="#100819", CARD="#160b21", CARD2="#1c0f2a",
                           BORDER="#2d1642", BORDER2="#3a1c56", ACCENT="#ec4899", ACCENT_H="#f472b6",
                           INDIGO="#8b5cf6", INDIGO_H="#a78bfa", TEXT="#faf5ff", TEXT2="#d8b4fe",
                           MUTED="#5b4a6f", MUTED2="#241333", SEL="#4c1d6e", INPUT_BG="#12081c"),
    "Sunset":       dict(BG="#100a04", PANEL="#180f08", CARD="#20140a", CARD2="#291a0d",
                           BORDER="#3d2712", BORDER2="#4d3117", ACCENT="#f97316", ACCENT_H="#fb923c",
                           INDIGO="#ea580c", INDIGO_H="#f97316", TEXT="#fff7ed", TEXT2="#fed7aa",
                           MUTED="#6f5138", MUTED2="#33220f", SEL="#5c3416", INPUT_BG="#180d05"),
}
THEME_ORDER = ["Midnight Blue", "Slate", "Emerald", "Crimson", "Cyberpunk", "Sunset"]

def apply_theme(name):
    """Reassigns the swappable palette globals in-place. Every widget-building
    function/method reads these as plain global names at call time (not as
    frozen default-argument values), so a full UI rebuild after this call
    picks up the new colors everywhere."""
    globals().update(THEMES.get(name, THEMES["Midnight Blue"]))

# Initialize default palette at import time (Midnight Blue) so the module
# has valid BG/CARD/etc. before App.__init__ runs apply_theme() from settings.
apply_theme("Midnight Blue")

CLASS_COLOR = {"Citation": GREEN,   "Misdemeanor": ORANGE,  "Felony": RED}
CLASS_BG    = {"Citation": GREEN_D, "Misdemeanor": ORANGE_D, "Felony": RED_D}
CLASS_BORDER= {"Citation": "#166534","Misdemeanor": "#9a3412","Felony": "#991b1b"}

# ── Application Data (settings / history) ─────────────────────────────────────
def get_appdata_dir():
    """OS-appropriate app data folder — never the desktop or app folder."""
    if sys.platform == "win32":
        base = os.getenv("APPDATA", os.path.expanduser("~"))
    elif sys.platform == "darwin":
        base = os.path.expanduser("~/Library/Application Support")
    else:
        base = os.getenv("XDG_DATA_HOME", os.path.expanduser("~/.local/share"))
    d = os.path.join(base, "GVCRCitationTool")
    try: os.makedirs(d, exist_ok=True)
    except Exception: pass
    return d

APPDATA_DIR    = get_appdata_dir()
SETTINGS_PATH  = os.path.join(APPDATA_DIR, "settings.json")
HISTORY_PATH   = os.path.join(APPDATA_DIR, "history.json")
HISTORY_LIMIT  = 200

DEFAULT_SETTINGS = {
    "officer_name": "",
    "badge_number": "",
    "callsign":     "",
    "division":     "",
    "theme":        "Midnight Blue",
    "greeting_template": "Hi, this is Officer {officer} with {division}, do you know why I am stopping you today?",
}

def load_settings():
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict): raise ValueError
        merged = DEFAULT_SETTINGS.copy(); merged.update(data)
        return merged
    except Exception:
        save_settings(DEFAULT_SETTINGS.copy())
        return DEFAULT_SETTINGS.copy()

def save_settings(settings):
    try:
        with open(SETTINGS_PATH, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=2)
        return True
    except Exception:
        return False

def load_history():
    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list): raise ValueError
        return data
    except Exception:
        save_history([])
        return []

def save_history(items):
    try:
        with open(HISTORY_PATH, "w", encoding="utf-8") as f:
            json.dump(items, f, indent=2)
        return True
    except Exception:
        return False

def append_history(entry_type, content):
    items = load_history()
    items.append({
        "type": entry_type,
        "content": content,
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    })
    items = items[-HISTORY_LIMIT:]
    save_history(items)

def self_heal():
    """Inspect + repair app data folder, settings file, history file.
    Never deletes user history/settings unless they're actually unreadable."""
    report = []
    try:
        os.makedirs(APPDATA_DIR, exist_ok=True)
        report.append(("ok", f"Application data folder OK  ({APPDATA_DIR})"))
    except Exception as e:
        report.append(("fail", f"Could not create app data folder: {e}"))

    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict): raise ValueError("not a dict")
        missing = [k for k in DEFAULT_SETTINGS if k not in data]
        if missing:
            merged = DEFAULT_SETTINGS.copy(); merged.update(data)
            save_settings(merged)
            report.append(("warn", f"Settings file was missing keys {missing} — restored"))
        else:
            report.append(("ok", "Settings file OK"))
    except Exception:
        save_settings(DEFAULT_SETTINGS.copy())
        report.append(("warn", "Settings file was missing/corrupted — recreated with defaults"))

    try:
        with open(HISTORY_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, list): raise ValueError("not a list")
        report.append(("ok", f"History file OK  ({len(data)} entries)"))
    except Exception:
        save_history([])
        report.append(("warn", "History file was missing/corrupted — reset to empty"))

    return report

# ── Vehicle image queue (thread-safe Tkinter image loading) ───────────────────
_img_queue   = queue.Queue()
_img_cache   = {}

def _fetch_vehicle_img(url, size, cb_name, root_ref):
    if url in _img_cache:
        _img_queue.put((None, url, cb_name))
        return
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = r.read()
        _img_cache[url] = data
        _img_queue.put((data, url, cb_name))
    except Exception:
        _img_queue.put((None, url, cb_name))

def vehicle_img_url(path_part, w=165, h=110):
    return (f"https://static.wikia.nocookie.net/greenville-wisconsin/images/"
            f"{path_part}/revision/latest/smart/width/{w}/height/{h}")

# ── Quick Phrases ─────────────────────────────────────────────────────────────
# Values starting with "__DYNAMIC_" are computed live at click/display time
# from the current citation board + settings — never hardcoded copies.
QUICK_PHRASES = {
    "🚔  Traffic Stop": [
        ("✨ Custom Greeting",      "__DYNAMIC_GREETING__"),
        ("License & Registration",  "Can I please see your license and registration?"),
        ("Proof of Insurance",      "Do you have proof of insurance?"),
        ("Reason for Stop",         "Do you know why I pulled you over today?"),
        ("Step Out",                "Sir/Ma'am, please step out of the vehicle."),
        ("Hands on Wheel",          "Keep your hands on the steering wheel please."),
        ("Where headed?",           "Where are you headed today?"),
        ("Speed aware?",            "Are you aware of how fast you were going?"),
        ("Any weapons?",            "Do you have any weapons in the vehicle?"),
        ("Any drugs?",              "Are there any drugs or contraband in the vehicle?"),
        ("Being cited for",         "__DYNAMIC_CITED__"),
    ],
    "🚨  Arrest": [
        ("Miranda Rights",          "You have the right to remain silent. Anything you say can and will be used against you in a court of law. You have the right to an attorney."),
        ("Under Arrest",            "You are under arrest. Please do not resist."),
        ("Hands Behind Back",       "Please put your hands behind your back."),
        ("Do Not Resist",           "Stop resisting. Do not resist arrest."),
        ("Detained",                "You are being detained. You are not free to leave."),
        ("Cuffing",                 "I am placing you in handcuffs for both our safety."),
        ("Search Consent",          "Do I have your consent to search the vehicle?"),
    ],
    "📋  Citation": [
        ("Sign Here",               "I need your signature here — signing is not an admission of guilt."),
        ("Drive Safe",              "Please drive safely. Have a good day."),
        ("License Suspended",       "Your license is suspended. You may not operate a vehicle."),
        ("Vehicle Impounded",       "Your vehicle is being impounded. You may retrieve it at the impound lot."),
        ("Warrant Check",           "I am running a warrant check. Please be patient."),
        ("Run Plates",              "I am running your plates. One moment please."),
        ("All Clear",               "All clear. You are free to go. Have a safe day."),
        ("Stay in Vehicle",         "Please remain in your vehicle."),
    ],
}

# ── Penal Codes, Code Notes and Radio Language ──────────────────────────────────────
PENAL_CODES = {
    "Section 1: Traffic Violations": [
        ("(1)01","Speeding 6-15 MPH Over the Speed Limit","$250","Citation"),
        ("(1)02","Speeding 16-24 MPH Over the Speed Limit","$650","Citation"),
        ("(1)03","Speeding 25+ MPH Over the Speed Limit","$1,250 + 30 Seconds of Jail Time","Misdemeanor"),
        ("(1)04","Unsafe Speed for Conditions","$500","Citation"),
        ("(1)05","Slowing/Stopping Without Reason","$300","Citation"),
        ("(1)06","Impeding Traffic","$700","Citation"),
        ("(1)07","Unsafe Lane Change","$300","Citation"),
        ("(1)08","Unsafe Passing","$300","Citation"),
        ("(1)09","Failure to Maintain Lanes","$300","Citation"),
        ("(1)10","Driving into Oncoming Traffic","$1,250 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(1)11","Unsafe Following Distance","$250","Citation"),
        ("(1)12","Unsafe Turn","$300","Citation"),
        ("(1)13","Illegal U-Turn","$350","Citation"),
        ("(1)14","Rolling a Stop Sign","$250","Citation"),
        ("(1)15","Running a Red Light","$500","Citation"),
        ("(1)16","Excessive Revving","$300","Citation"),
        ("(1)17","Excessive Honking","$500","Citation"),
        ("(1)18","Excessive Sounds/Music","$300","Citation"),
        ("(1)19","Reckless Driving","$2,000 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(1)20","Burnout","$400","Citation"),
        ("(1)21","Drifting on a Public Road","$500","Citation"),
        ("(1)22","Drifting in a Parking Lot","$250","Citation"),
        ("(1)23","Failure to Yield","$200","Citation"),
        ("(1)24","Failure to Yield to Pedestrian","$250","Citation"),
        ("(1)25","Failure to Yield to Emergency Vehicles","$500","Citation"),
        ("(1)26","Failure to Follow Move Over Law","$550","Citation"),
        ("(1)27","Failure to Obey Traffic Signal","$250","Citation"),
        ("(1)28","Road Rage","$500","Misdemeanor"),
        ("(1)29","Distracted Driving","$300","Citation"),
        ("(1)30","Parking In a No Parking Zone","$150 + Impoundment of Vehicle","Citation"),
        ("(1)31","Parking In a Handicap Parking Spot","$120","Citation"),
        ("(1)32","Illegal Parking","$250","Citation"),
        ("(1)33","Hit and Run","$500 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(1)34","Headlight Violation","$400","Citation"),
        ("(1)35","Street Racing","$550","Misdemeanor"),
        ("(1)36","Jaywalking","$400","Citation"),
        ("(1)37","Blank Plate","$1,000","Misdemeanor"),
        ("(1)38","Failure to Signal","$200","Citation"),
        ("(1)39","Brake Checking","$250","Citation"),
        ("(1)40","Improper Reversing","$750","Citation"),
        ("(1)41","Unroadworthy Vehicle","$500 + Impoundment of Vehicle","Misdemeanor"),
        ("(1)42","Failure to Stop for School Bus With Flashing Lights","$750","Citation")
    ],
    "Section 2: Documentation": [
        ("(2)01","Driving on Learner's Permit Without Supervision","$500 + Impoundment of Vehicle","Misdemeanor"),
        ("(2)02","Driving with No / Invalid Vehicle Insurance","$750 + Impoundment of Vehicle","Misdemeanor"),
        ("(2)03","Driving with No / Invalid Vehicle Registration","$500 + Impoundment of Vehicle","Misdemeanor"),
        ("(2)04","Driving on a Suspended License","$1,000 + 60 Seconds of Jail Time + Impoundment of the Vehicle","Felony"),
        ("(2)05","Failure to Sign a Citation","$1,000 + 30 Seconds of Jail Time","Misdemeanor"),
        ("(2)06","Operating Without a Valid License","$7,500 + 180 Seconds of Jail Time","Felony")
    ],
    "Section 3: Crime Against Property": [
        ("(3)01","Vandalism","$1,000 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(3)02","Arson","$1,250 + 100 Seconds of Jail Time","Felony"),
        ("(3)03","Shoplifting","$300 + 30 Seconds of Jail Time","Misdemeanor"),
        ("(3)04","Destruction of Government Property","$2,000 + 120 Seconds of Jail Time","Felony"),
        ("(3)05","Destruction of Civilian Property","$1,000 + 30 Seconds of Jail Time","Misdemeanor"),
        ("(3)06","Robbery","$1,000 + 90 Seconds of Jail Time","Felony"),
        ("(3)07","Armed Robbery","$1,500 + 120 Seconds of Jail Time","Felony"),
        ("(3)08","Burglary","$500 + 30 Seconds of Jail Time","Felony"),
        ("(3)09","Armed Burglary","$1,000 + 60 Seconds of Jail Time","Felony"),
        ("(3)10","Theft","$1,000 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(3)11","Grand Theft","$5,000 + 90 Seconds of Jail Time","Felony"),
        ("(3)12","Grand Theft Auto","$10,000 + 120 Seconds of Jail Time","Felony"),
        ("(3)13","Trespassing","$500 + 90 Seconds of Jail Time","Misdemeanor"),
        ("(3)14","At Fault of Injury","$2,000 + 60 Seconds of Jail Time","Felony"),
        ("(3)15","At Fault of Death","$10,000 + 200 Seconds of Jail Time","Felony"),
        ("(3)16","Possession of Stolen Property","$1,000 + 60 Seconds of Jail Time","Felony")
    ],
    "Section 4: Crimes Involving Deadly Weapons And Equipment": [
        ("(4)01","Illegal / Unlicensed Weapon","$1,000 + 120 Seconds of Jail Time","Felony"),
        ("(4)02","Recklessly Firing a Firearm","$2,250 + 200 Seconds of Jail Time","Felony"),
        ("(4)03","Possesion of a Stolen Firearm","$1,500 + 90 Seconds of Jail Time","Felony"),
        ("(4)04","Unlawful Selling of a Firearm","$1,500 + 200 Seconds of Jail Time","Misdemeanor")
    ],
    "Section 5: Crime Against People and Peace": [
        ("(5)01","Kidnapping","120 Seconds of Jail Time","Felony"),
        ("(5)02","Child Endangerment","$10,000 + 60 Seconds of Jail Time","Felony"),
        ("(5)03","Public Endangerment","$10,000 + 120 Seconds of Jail Time","Felony"),
        ("(5)04","Criminal Threats","60 Seconds of Jail Time","Misdemeanor"),
        ("(5)05","Encouraging to Riot","120 Seconds of Jail Time","Misdemeanor"),
        ("(5)06","Disturbing the Peace","$750","Misdemeanor"),
        ("(5)07","Assault","$1,000 + 60 Seconds of Jail Time","Felony"),
        ("(5)08","Assault with a Deadly Weapon","$1,000 + 90 Seconds of Jail Time","Felony"),
        ("(5)09","Assault on a Peace Officer","$1,000 + 120 Seconds of Jail Time","Felony"),
        ("(5)10","Assault with a Motored Vehicle","$4,000 + 60 Seconds of Jail Time","Felony"),
        ("(5)11","Attempted Murder","$1,000 + 60 Seconds of Jail Time","Felony"),
        ("(5)12","1st Degree Intentional Homicide","$7,500 + 200 Seconds of Jail Time","Felony"),
        ("(5)13","2nd Degree Intentional Homicide","$5,000 + 180 Seconds of Jail Time","Felony"),
        ("(5)14","1st Degree Reckless Homicide","$3,500 + 150 Seconds of Jail Time","Felony"),
        ("(5)15","2nd Degree Reckless Homicide","$2,500 + 120 Seconds of Jail Time","Felony"),
        ("(5)16","Negligent Homicide","$5,000 + 180 Seconds of Jail Time","Felony"),
        ("(5)17","Felony Murder","$10,000 + 200 Seconds of Jail Time","Felony"),
        ("(5)18","Stalking","$400 + 100 Seconds of Jail Time","Felony"),
        ("(5)19","Disorderly Conduct","$1,500 + 90 Seconds of Jail Time","Misdemeanor"),
        ("(5)20","Battery","$1,500 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(5)21","Loitering","$1,250","Misdemeanor")
    ],
    "Section 6: Crime Against Justice": [
        ("(6)01","Bribery","$7,500 + 60 Seconds of Jail Time","Felony"),
        ("(6)02","Resisting Arrest","$1,250 + 30 Seconds of Jail Time","Felony"),
        ("(6)03","Evading a Peace Officer","$450 + 100 Seconds of Jail Time","Misdemeanor"),
        ("(6)04","Felony Evading a Peace Officer","$600 + 120 Seconds of Jail Time","Felony"),
        ("(6)05","Impersonation of a Peace Officer","$1,250 + 60 Seconds of Jail Time","Felony"),
        ("(6)06","Filing a False Police Report","$700 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(6)07","Avoiding / Evading a Lawful Traffic Stop","$750 + 50 Seconds of Jail Time","Felony"),
        ("(6)08","Failure to Identify to a Peace Officer","$500 + 30 Seconds of Jail Time","Misdemeanor"),
        ("(6)09","Failure to Comply with a Lawful Order","$500 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(6)10","Escape from Custody","$1,000 + 120 Seconds of Jail Time","Felony"),
        ("(6)11","Prisoner Breakout","$10,000 + 90 Seconds of Jail Time","Felony"),
        ("(6)12","Obstruction of Justice","$1,000 + 60 Seconds of Jail Time","Felony"),
        ("(6)13","Cop Baiting","$2,500 + 120 Seconds of Jail Time","Misdemeanor"),
        ("(6)14","Lying to a Law Enforcement Officer","$3,000 + 60 Seconds of Jail Time","Misdemeanor"),
        ("(6)15","Aiding and Abetting","$2,500 + 60 Seconds of Jail Time","Misdemeanor")
    ]
}

CODE_NOTES = {
    "(5)07": "An intentional act that creates a reasonable fear or apprehension of immediate harmful or offensive contact.",
    "(5)11": "The attempt to kill someone with a specific intent to cause their death, but failing to complete the act because of an outside interference or factor.",
    "(5)12": "Causing the death of another person with intent.",
    "(5)13": "Intentional killing caused by circumstances like adequate provocation or self-defense; equivalent to voluntary manslaughter.",
    "(5)14": "Causing death with utter disregard for human life; equivalent to involuntary manslaughter.",
    "(5)15": "Causing death through reckless conduct; equivalent to involuntary manslaughter.",
    "(5)16": "Negligent control of a vicious animal, negligent use of a weapon/firearm, and/or intoxicated or reckless driving.",
    "(5)17": "Causing a death while committing certain dangerous underlying felonies, such as battery, assault, kidnapping, arson, or burglary.",
    "(5)20": "The intentional and unlawful use of force, violence, or unwanted physical contact against another person."
}

RADIO_CODES_DATA = {
    "10-Codes": [
        "10-1 Receiving Poorly / Switch Voice Channels [Tac / Scene]",
        "10-2 Receiving Well",
        "10-3 Stop Transmitting",
        "10-4 O.K. / Affirm",
        "10-5 Relay",
        "10-6 Busy",
        "10-7 Out Of Service",
        "10-8 In Service",
        "10-9 Repeat",
        "10-10 Fight in progress",
        "10-11 Traffic Stop",
        "10-12 Active Ride Along",
        "10-13 Shots Fired",
        "10-15 Subject in custody en route to Station",
        "10-16 Stolen Vehicle",
        "10-17 Suspicious Person",
        "10-20 Location",
        "10-22 Disregard",
        "10-23 Arrived on Scene",
        "10-25 Domestic Dispute",
        "10-26 ETA",
        "10-27 Driver's License Check for Valid",
        "10-28 Vehicle License Plate Check",
        "10-29 NCIC Warrant Check",
        "10-30 Wanted Person",
        "10-31 Not Wanted No Warrants",
        "10-32 Request Backup (Code 1-2-3)",
        "10-35 Wrap The Scene Up",
        "10-41 Beginning Tour of Duty",
        "10-42 Ending Tour of Duty",
        "10-43 Information",
        "10-49 Homicide",
        "10-50 Vehicle Accident: PD: Property Damage Only, PI: Person/s Injured, F: Fatal",
        "10-51 Request Towing Service",
        "10-52 Request EMS",
        "10-53 Request Fire Department",
        "10-55 Intoxicated Driver",
        "10-56 Intoxicated Pedestrian",
        "10-60 Armed with a Gun",
        "10-61 Armed with a Knife",
        "10-62 Kidnapping",
        "10-65 Escorting Prisoner",
        "10-66 Reckless Driver",
        "10-67 Fire",
        "10-68 Armed Robbery",
        "10-70 Foot Pursuit",
        "10-71 Request/Active Supervisor",
        "10-73 Advice Status",
        "10-80 Vehicle Pursuit",
        "10-97 In Route",
        "10-99 Officer In Distress Extreme Emergency Only",
        "11-44 Person Deceased"
    ],
    "Signals": [
        "Signal 11 Running Radar (10-20 Location) - Stationary while checking peoples speeds",
        "Signal 100 Hold all but emergency traffic - Do not Transmit if you are not part of the emergency traffic like; Priorities"
    ],
    "Codes": [
        "Code 1 Routine Response",
        "Code 2 Expedite // Emergency Lights ONLY",
        "Code 3 Response using lights and Siren",
        "Code 4 Cancel Responding Units",
        "Code 5 High-Risk Stop // Felony Stop (10-32 recommended)",
        "Code 6 Responding From A Long Distance",
        "Code 9 Set Up A RoadBlock"
    ],
    "NATO Phonetic Alphabet": [
        "A - Alpha", "B - Bravo", "C - Charlie", "D - Delta", "E - Echo",
        "F - Foxtrot", "G - Golf", "H - Hotel", "I - India", "J - Juliet",
        "K - Kilo", "L - Lima", "M - Mike", "N - November", "O - Oscar",
        "P - Papa", "Q - Quebec", "R - Romeo", "S - Sierra", "T - Tango",
        "U - Uniform", "V - Victor", "W - Whiskey", "X - X-ray", "Y - Yankee", "Z - Zulu"
    ]
}

# ── Utility: parse penalty ────────────────────────────────────────────────────
def parse_penalty(p):
    money=0; jail=0; imp=False
    m=re.search(r'\$([0-9,]+)',p)
    if m: money=int(m.group(1).replace(',',''))
    j=re.search(r'(\d+)\s+Seconds? of Jail',p,re.I)
    if j: jail=int(j.group(1))
    if re.search(r'impound',p,re.I): imp=True
    return money,jail,imp

def build_penalty(charges):
    tm=0;tj=0;ti=False
    for _,_,p,_ in charges:
        m,j,i=parse_penalty(p); tm+=m; tj+=j
        if i: ti=True
    parts=[f"${tm:,}"] if tm else []
    if tj: parts.append(f"{tj} Seconds of Jail Time")
    if ti: parts.append("Vehicle Impoundment")
    return " + ".join(parts) if parts else "N/A"

# ── Widget Helpers ────────────────────────────────────────────────────────────
def FONT():
    return "Segoe UI" if sys.platform == "win32" else "Helvetica"

def btn(parent, text, cmd, bg=None, fg=None, hbg=None,
        fs=9, bold=True, padx=14, pady=9, **kw):
    bg = bg if bg is not None else ACCENT
    fg = fg if fg is not None else TEXT
    def _l(h):
        r,g,b=int(h[1:3],16),int(h[3:5],16),int(h[5:7],16)
        return f"#{min(255,r+32):02x}{min(255,g+32):02x}{min(255,b+32):02x}"
    hb=hbg or _l(bg)
    w=tk.Button(parent,text=text,command=cmd,bg=bg,fg=fg,
                activebackground=hb,activeforeground=fg,
                font=(FONT(), fs,"bold" if bold else "normal"),
                relief="flat",bd=0,cursor="hand2",padx=padx,pady=pady,**kw)
    w.bind("<Enter>",lambda e:w.configure(bg=hb))
    w.bind("<Leave>",lambda e:w.configure(bg=bg))
    return w

def inp(parent, label, placeholder=""):
    tk.Label(parent,text=label,font=(FONT(),8),
             bg=parent.cget("bg"),fg=TEXT2).pack(anchor="w",pady=(0,2))
    wrap=tk.Frame(parent,bg=BORDER2,padx=1,pady=1)
    wrap.pack(fill="x",pady=(0,10))
    inner=tk.Frame(wrap,bg=INPUT_BG)
    inner.pack(fill="both")
    e=tk.Entry(inner,bg=INPUT_BG,fg=TEXT,insertbackground=ACCENT,
               relief="flat",font=(FONT(),10),bd=7)
    e.pack(fill="x")
    e._ph=placeholder
    if placeholder:
        e.insert(0,placeholder); e.configure(fg=MUTED)
        def fi(ev,x=e):
            if x.get()==x._ph: x.delete(0,"end"); x.configure(fg=TEXT)
        def fo(ev,x=e):
            if not x.get(): x.insert(0,x._ph); x.configure(fg=MUTED)
        e.bind("<FocusIn>",fi); e.bind("<FocusOut>",fo)
    return e

def getv(e):
    v=e.get().strip()
    return "" if v==getattr(e,'_ph','') else v

def hline(parent, color=None, pady=(8,8)):
    tk.Frame(parent,bg=(color or BORDER),height=1).pack(fill="x",pady=pady)

# ── Shiny Credit Label ────────────────────────────────────────────────────────
class ShinyLabel(tk.Canvas):
    def __init__(self,parent,text,bg=None,**kw):
        bg = bg if bg is not None else PANEL
        f=kw.pop("font",(FONT(),8,"bold"))
        super().__init__(parent,bg=bg,highlightthickness=0,height=16,cursor="hand2",**kw)
        self._t=text;self._f=f;self._x=-60;self._on=False
        self.bind("<Configure>",self._draw)
        self.bind("<Enter>",self._start)
        self.bind("<Leave>",self._stop)
        self._draw()
    def _draw(self,e=None):
        self.delete("all")
        w=self.winfo_width() or 110; h=self.winfo_height() or 16
        self.create_text(w//2,h//2,text=self._t,font=self._f,fill=GOLD,anchor="center")
    def _start(self,e=None):
        self._on=True; self._x=-60; self._tick()
    def _stop(self,e=None):
        self._on=False; self._draw()
    def _tick(self):
        if not self._on or not self.winfo_exists(): return
        self.delete("all")
        w=self.winfo_width() or 110; h=self.winfo_height() or 16
        for i in range(40):
            b=max(0,200-abs(i-20)*10)
            c=f"#{min(255,170+b//3):02x}{min(255,130+b//4):02x}{20+b//12:02x}"
            self.create_line(self._x+i,0,self._x+i,h,fill=c)
        self.create_text(w//2,h//2,text=self._t,font=self._f,fill=GOLD_H,anchor="center")
        self._x+=10
        if self._x<w+60: self.after(18,self._tick)
        else: self._start()

# ── Animated Bar Chart (reused for severity + history stats) ──────────────────
class AnimatedBarChart(tk.Canvas):
    """Small horizontal bar chart whose bars animate to new values whenever
    set_counts() is called. items = [(label, color), ...] fixed at creation."""
    def __init__(self, parent, items, bg=None, height=None, **kw):
        bg = bg if bg is not None else CARD
        h = height or (len(items) * 24 + 6)
        super().__init__(parent, bg=bg, highlightthickness=0, height=h, **kw)
        self._items = items
        self._targets = {lbl: 0 for lbl,_ in items}
        self._current = {lbl: 0.0 for lbl,_ in items}
        self._animating = False
        self.bind("<Configure>", lambda e: self._redraw())
        self._redraw()

    def set_counts(self, counts):
        for lbl,_ in self._items:
            self._targets[lbl] = counts.get(lbl, 0)
        if not self._animating:
            self._animating = True
            self._animate()

    def _animate(self):
        if not self.winfo_exists():
            self._animating = False
            return
        done = True
        for lbl,_ in self._items:
            t = self._targets[lbl]; c = self._current[lbl]
            if abs(t - c) > 0.05:
                self._current[lbl] = c + (t - c) * 0.25
                done = False
            else:
                self._current[lbl] = t
        self._redraw()
        if not done:
            self.after(16, self._animate)
        else:
            self._animating = False

    def _redraw(self):
        if not self.winfo_exists(): return
        self.delete("all")
        w = self.winfo_width() or 260
        h = self.winfo_height() or (len(self._items) * 24 + 6)
        row_h = h / max(1, len(self._items))
        maxval = max([1] + [self._targets.get(lbl, 0) for lbl,_ in self._items])
        for i, (lbl, color) in enumerate(self._items):
            y = i * row_h
            val = self._current.get(lbl, 0)
            bar_w = (w - 110) * (val / maxval) if maxval else 0
            self.create_text(6, y + row_h/2, text=lbl, font=(FONT(),7), fill=MUTED, anchor="w")
            self.create_rectangle(66, y + row_h*0.28, 66 + max(2,bar_w), y + row_h*0.72,
                                  fill=color, outline="")
            self.create_text(w-6, y + row_h/2, text=str(int(round(self._targets.get(lbl,0)))),
                             font=(FONT(),8,"bold"), fill=TEXT, anchor="e")

def animate_count(label_widget, target, steps=12, delay=18):
    """Animates a plain Label's text from 0 up to an integer target."""
    def step(i=0):
        if not label_widget.winfo_exists(): return
        val = int(round(target * (i/steps))) if steps else target
        label_widget.config(text=str(val))
        if i < steps:
            label_widget.after(delay, lambda: step(i+1))
        else:
            label_widget.config(text=str(target))
    step()

# ── License Plate ─────────────────────────────────────────────────────────────
class PlateWidget(tk.Frame):
    def __init__(self,parent,**kw):
        super().__init__(parent,bg=parent.cget("bg"),**kw)
        tk.Label(self,text="LICENSE PLATE",
                 font=(FONT(),7,"bold"),
                 bg=parent.cget("bg"),fg=TEXT2).pack(anchor="w",pady=(0,4))
        outer=tk.Frame(self,bg="#6b7fa3",padx=3,pady=3)
        outer.pack(anchor="w")
        plate=tk.Frame(outer,bg="#193468",padx=18,pady=10)
        plate.pack()
        top_r=tk.Frame(plate,bg="#193468")
        top_r.pack(fill="x")
        tk.Label(top_r,text="◉",font=("Helvetica",6),bg="#193468",fg="#3d5a8a").pack(side="left")
        tk.Label(top_r,text="GREENVILLE",font=("Helvetica",7,"bold"),
                 bg="#193468",fg="#fbbf24").pack(side="left",expand=True)
        tk.Label(top_r,text="◉",font=("Helvetica",6),bg="#193468",fg="#3d5a8a").pack(side="right")
        self._var=tk.StringVar()
        tk.Entry(plate,textvariable=self._var,
                 font=("Courier New",24,"bold"),bg="#0f2550",fg="#ffffff",
                 insertbackground="#93c5fd",relief="flat",justify="center",
                 bd=4,width=8,highlightthickness=0).pack(pady=(4,4))
        self._var.trace_add("write",self._fmt)
        bot_r=tk.Frame(plate,bg="#193468")
        bot_r.pack(fill="x")
        tk.Label(bot_r,text="◉",font=("Helvetica",6),bg="#193468",fg="#3d5a8a").pack(side="left")
        tk.Label(bot_r,text="★  COMMUNITY ROLEPLAY  ★",font=("Helvetica",6),
                 bg="#193468",fg="#93c5fd").pack(side="left",expand=True)
        tk.Label(bot_r,text="◉",font=("Helvetica",6),bg="#193468",fg="#3d5a8a").pack(side="right")
    def _fmt(self,*a):
        v=self._var.get().upper()
        if len(v)>8: self._var.set(v[:8])
        elif v!=v.upper(): self._var.set(v.upper())
    def get(self): return self._var.get().strip()

# ── Splash ────────────────────────────────────────────────────────────────────
class Splash(tk.Toplevel):
    def __init__(self,parent):
        super().__init__(parent)
        self.overrideredirect(True)
        W,H=460,300
        sw=self.winfo_screenwidth(); sh=self.winfo_screenheight()
        self.geometry(f"{W}x{H}+{(sw-W)//2}+{(sh-H)//2}")
        self.configure(bg=BG)
        self.attributes("-topmost",True)
        border=tk.Frame(self,bg=ACCENT,padx=1,pady=1)
        border.place(relx=0,rely=0,relwidth=1,relheight=1)
        inner=tk.Frame(border,bg=BG)
        inner.pack(fill="both",expand=True)
        try:
            self._logo=tk.PhotoImage(data=LOGO_B64_110)
            tk.Label(inner,image=self._logo,bg=BG).pack(pady=(20,8))
        except Exception:
            tk.Label(inner,text="🚔",font=("Helvetica",36),bg=BG,fg=ACCENT).pack(pady=(20,8))
        F=FONT()
        tk.Label(inner,text="GVCR CITATION TOOL",font=(F,17,"bold"),bg=BG,fg=TEXT).pack()
        tk.Label(inner,text="Greenville Community Roleplay  ·  Public Services",
                 font=(F,9),bg=BG,fg=MUTED).pack(pady=(3,0))
        track=tk.Frame(inner,bg=BORDER,height=3)
        track.pack(fill="x",padx=50,pady=(22,5))
        self._bar=tk.Frame(track,bg=ACCENT,height=3,width=0)
        self._bar.place(x=0,y=0,height=3)
        self._tw=460-100; self._bw=0.0
        self._st=tk.Label(inner,text="Starting...",font=(F,9),bg=BG,fg=MUTED)
        self._st.pack()
        self.update()
    def progress(self,msg,pct):
        try:
            self._st.config(text=msg)
            tgt=self._tw*pct/100; steps=10
            d=(tgt-self._bw)/max(1,steps)
            for _ in range(steps):
                self._bw=min(tgt,self._bw+d)
                self._bar.config(width=int(self._bw))
                self.update()
                time.sleep(0.005)
        except Exception: pass

# ── Scrollable frame helper ───────────────────────────────────────────────────
class ScrollFrame(tk.Frame):
    def __init__(self, parent, bg=None, height=None, **kw):
        bg = bg if bg is not None else CARD
        super().__init__(parent, bg=bg, **kw)
        kw2 = {"height": height} if height else {}
        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, **kw2)

        self.sb = tk.Canvas(self, width=8, bg=bg, highlightthickness=0, cursor="arrow")
        self._thumb_id = None
        self._lo, self._hi = 0.0, 1.0
        self._drag_dy = None

        self.canvas.configure(yscrollcommand=self._on_scroll)
        self.sb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        self.inner = tk.Frame(self.canvas, bg=bg)
        self._win = self.canvas.create_window((0, 0), window=self.inner, anchor="nw")

        self.inner.bind(
            "<Configure>",
            lambda e: (self.canvas.configure(scrollregion=self.canvas.bbox("all")),
                       self._draw_thumb())
        )
        self.canvas.bind(
            "<Configure>",
            lambda e: (self.canvas.itemconfigure(self._win, width=e.width),
                       self._draw_thumb())
        )
        self.sb.bind("<Configure>", lambda e: self._draw_thumb())
        self.sb.bind("<Button-1>", self._sb_press)
        self.sb.bind("<B1-Motion>", self._sb_drag)

    def _on_scroll(self, lo, hi):
        self._lo, self._hi = float(lo), float(hi)
        self._draw_thumb()

    def _draw_thumb(self):
        if not self.sb.winfo_exists(): return
        self.sb.delete("all")
        h = self.sb.winfo_height()
        w = self.sb.winfo_width() or 8
        if h <= 1 or self._hi - self._lo >= 0.999:
            self._thumb_id = None
            return
        y0, y1 = self._lo * h, self._hi * h
        if y1 - y0 < 18:
            mid = (y0 + y1) / 2
            y0, y1 = mid - 9, mid + 9
        self._thumb_id = self.sb.create_rectangle(
            1, y0, w - 1, y1, fill=BORDER2, outline="", width=0
        )

    def _sb_press(self, event):
        coords = self.sb.coords(self._thumb_id) if self._thumb_id else None
        if coords and coords[1] <= event.y <= coords[3]:
            self._drag_dy = event.y - coords[1]
        else:
            self._drag_dy = 0
            h = self.sb.winfo_height()
            if h > 1:
                self.canvas.yview_moveto(max(0.0, min(1.0, event.y / h)))

    def _sb_drag(self, event):
        h = self.sb.winfo_height()
        if h <= 1 or self._thumb_id is None:
            return
        y = event.y - (self._drag_dy or 0)
        self.canvas.yview_moveto(max(0.0, min(1.0, y / h)))

    def _on_mousewheel(self, event):
        self.canvas.yview_scroll(int(-event.delta / 120), "units")

    def _bind_mousewheel(self, event=None):
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind_all("<Button-4>", lambda e: self.canvas.yview_scroll(-1, "units"))
        self.canvas.bind_all("<Button-5>", lambda e: self.canvas.yview_scroll(1, "units"))

    def _unbind_mousewheel(self, event=None):
        self.canvas.unbind_all("<MouseWheel>")
        self.canvas.unbind_all("<Button-4>")
        self.canvas.unbind_all("<Button-5>")

    def bind_scroll(self):
        self.canvas.bind("<Enter>", self._bind_mousewheel)
        self.canvas.bind("<Leave>", self._unbind_mousewheel)
        self.inner.bind("<Enter>", self._bind_mousewheel)
        self.inner.bind("<Leave>", self._unbind_mousewheel)

# ── Settings Window ────────────────────────────────────────────────────────────
class SettingsWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        F = FONT()
        self.title("Settings")
        self.configure(bg=BG)
        self.geometry("500x760")
        self.transient(app)
        self.grab_set()

        canvas_wrap = tk.Frame(self, bg=BG)
        canvas_wrap.pack(fill="both", expand=True)
        sf = ScrollFrame(canvas_wrap, bg=BG)
        sf.pack(fill="both", expand=True)
        sf.bind_scroll()
        outer = tk.Frame(sf.inner, bg=BG, padx=18, pady=16)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="⚙  Settings", font=(F,15,"bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(outer, text="These values auto-fill across the app and are saved between sessions.",
                 font=(F,9), bg=BG, fg=MUTED, wraplength=440, justify="left"
                 ).pack(anchor="w", pady=(2,14))

        card = tk.Frame(outer, bg=CARD, padx=16, pady=14,
                        highlightbackground=BORDER, highlightthickness=1)
        card.pack(fill="x")
        tk.Label(card, text="OFFICER DEFAULTS", font=(F,9,"bold"),
                 bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0,8))

        s = app.settings
        self._e_name  = inp(card, "Officer Name")
        self._e_badge = inp(card, "Badge Number")
        self._e_call  = inp(card, "Callsign")
        self._e_div   = inp(card, "Division")
        for e, key in [(self._e_name,"officer_name"), (self._e_badge,"badge_number"),
                       (self._e_call,"callsign"), (self._e_div,"division")]:
            if s.get(key):
                e.delete(0,"end"); e.insert(0, s[key]); e.configure(fg=TEXT)

        # ── Greeting template ──
        card2 = tk.Frame(outer, bg=CARD, padx=16, pady=14,
                         highlightbackground=BORDER, highlightthickness=1)
        card2.pack(fill="x", pady=(14,0))
        tk.Label(card2, text="CUSTOM GREETING", font=(F,9,"bold"),
                 bg=CARD, fg=CYAN).pack(anchor="w", pady=(0,4))
        tk.Label(card2, text="Used by the \"Custom Greeting\" quick phrase. Placeholders: {officer} {division}",
                 font=(F,8), bg=CARD, fg=MUTED, wraplength=420, justify="left").pack(anchor="w", pady=(0,6))
        self._e_greet = inp(card2, "Greeting Template", DEFAULT_SETTINGS["greeting_template"])
        if s.get("greeting_template"):
            self._e_greet.delete(0,"end"); self._e_greet.insert(0, s["greeting_template"])
            self._e_greet.configure(fg=TEXT)

        btn(outer, "💾  Save Settings", self._save,
            bg=ACCENT, hbg=ACCENT_H, fg=TEXT, fs=10, pady=9
            ).pack(fill="x", pady=(14,0))

        # ── Appearance ──
        tk.Label(outer, text="APPEARANCE", font=(F,9,"bold"),
                 bg=BG, fg=INDIGO).pack(anchor="w", pady=(18,4))
        theme_card = tk.Frame(outer, bg=CARD, padx=16, pady=14,
                              highlightbackground=BORDER, highlightthickness=1)
        theme_card.pack(fill="x")
        tk.Label(theme_card, text="Pick a color scheme. Applies instantly across the whole app.",
                 font=(F,8), bg=CARD, fg=MUTED, wraplength=420, justify="left").pack(anchor="w", pady=(0,8))
        theme_row = tk.Frame(theme_card, bg=CARD)
        theme_row.pack(fill="x")
        current_theme = s.get("theme","Midnight Blue")
        for tname in THEME_ORDER:
            tcolors = THEMES[tname]
            sw_wrap = tk.Frame(theme_row, bg=CARD)
            sw_wrap.pack(side="left", padx=5)
            ring = tcolors["ACCENT"] if tname == current_theme else CARD
            swatch = tk.Label(sw_wrap, text="  ", bg=tcolors["ACCENT"], width=4, height=2,
                              cursor="hand2", highlightthickness=2, highlightbackground=ring,
                              highlightcolor=ring)
            swatch.pack()
            swatch.bind("<Button-1>", lambda e, n=tname: self._pick_theme(n))
            tk.Label(sw_wrap, text=tname, font=(F,7), bg=CARD, fg=MUTED).pack()

        # ── Maintenance ──
        tk.Label(outer, text="MAINTENANCE", font=(F,9,"bold"),
                 bg=BG, fg=ORANGE).pack(anchor="w", pady=(18,4))
        maint = tk.Frame(outer, bg=CARD, padx=16, pady=14,
                         highlightbackground=BORDER, highlightthickness=1)
        maint.pack(fill="both", expand=True)
        tk.Label(maint, text="Self-Heal checks the app's local data files and\nrepairs anything missing or corrupted.",
                 font=(F,9), bg=CARD, fg=MUTED, justify="left").pack(anchor="w", pady=(0,8))
        btn(maint, "🩹  Run Self-Heal", self._run_self_heal,
            bg=ORANGE_D, hbg="#5c1f0a", fg=ORANGE, fs=9, pady=8
            ).pack(fill="x")

        self._heal_out = tk.Text(maint, bg=INPUT_BG, fg=TEXT2, font=("Courier New",9),
                                 relief="flat", wrap="word", padx=8, pady=8, height=6)
        self._heal_out.pack(fill="both", expand=True, pady=(10,0))
        self._heal_out.insert("end", "Click \"Run Self-Heal\" to check app data integrity.")
        self._heal_out.configure(state="disabled")

    def _save(self):
        self.app.settings.update({
            "officer_name": getv(self._e_name),
            "badge_number": getv(self._e_badge),
            "callsign":     getv(self._e_call),
            "division":     getv(self._e_div),
            "greeting_template": getv(self._e_greet),
        })
        save_settings(self.app.settings)
        self.app.apply_officer_defaults()
        self.app._refresh_dynamic_phrases()
        self.app._toast("Settings saved!")

    def _pick_theme(self, name):
        self.app.settings["theme"] = name
        save_settings(self.app.settings)
        apply_theme(name)
        self.app.rebuild_ui()
        self.app._toast(f"Theme set to {name}!")
        self.destroy()

    def _run_self_heal(self):
        report = self_heal()
        self._heal_out.configure(state="normal")
        self._heal_out.delete("1.0","end")
        icons = {"ok":"✓","warn":"⚠","fail":"✗"}
        for status, msg in report:
            self._heal_out.insert("end", f"{icons.get(status,'•')}  {msg}\n")
        self._heal_out.configure(state="disabled")
        self.app._toast("Self-heal complete!")

# ── History Window ─────────────────────────────────────────────────────────────
class HistoryWindow(tk.Toplevel):
    def __init__(self, app):
        super().__init__(app)
        self.app = app
        F = FONT()
        self.title("History")
        self.configure(bg=BG)
        self.geometry("640x680")
        self.transient(app)

        outer = tk.Frame(self, bg=BG, padx=16, pady=14)
        outer.pack(fill="both", expand=True)

        tk.Label(outer, text="🕘  Report History", font=(F,15,"bold"),
                 bg=BG, fg=TEXT).pack(anchor="w")

        items = load_history()
        counts = {"Citations":0, "Arrests":0, "Warrants":0, "Shifts":0}
        type_map = {"citation":"Citations", "arrest":"Arrests", "warrant":"Warrants", "shift":"Shifts"}
        for it in items:
            key = type_map.get(it.get("type","?"))
            if key: counts[key] += 1

        stat_row = tk.Frame(outer, bg=BG)
        stat_row.pack(fill="x", pady=(10,8))
        for label, color in [("Citations",GREEN), ("Arrests",RED), ("Warrants",INDIGO), ("Shifts",CYAN)]:
            card = tk.Frame(stat_row, bg=CARD, padx=10, pady=10,
                            highlightbackground=BORDER, highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=2)
            num_lbl = tk.Label(card, text="0", font=(F,18,"bold"), bg=CARD, fg=color)
            num_lbl.pack()
            animate_count(num_lbl, counts[label])
            tk.Label(card, text=label, font=(F,8), bg=CARD, fg=MUTED).pack()

        chart_card = tk.Frame(outer, bg=CARD, padx=14, pady=10,
                              highlightbackground=BORDER, highlightthickness=1)
        chart_card.pack(fill="x", pady=(0,10))
        chart = AnimatedBarChart(chart_card, [("Citations",GREEN),("Arrests",RED),("Warrants",INDIGO),("Shifts",CYAN)],
                                 bg=CARD, height=96)
        chart.pack(fill="x")
        chart.set_counts(counts)

        btn_row = tk.Frame(outer, bg=BG)
        btn_row.pack(fill="x", pady=(0,10))
        btn(btn_row, "🗑  Clear History", self._clear,
            bg=RED_D, hbg="#500d0d", fg=RED, fs=9, pady=7
            ).pack(side="right")

        list_wrap = tk.Frame(outer, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        list_wrap.pack(fill="both", expand=True)
        self._sf = ScrollFrame(list_wrap, bg=CARD)
        self._sf.pack(fill="both", expand=True)
        self._sf.bind_scroll()
        self._populate(items)

    def _populate(self, items):
        for w in self._sf.inner.winfo_children(): w.destroy()
        F = FONT()
        if not items:
            tk.Label(self._sf.inner, text="No history yet — generate a citation, arrest\nreport, or warrant to see it here.",
                     bg=CARD, fg=MUTED, font=(F,9), pady=20, justify="left").pack(anchor="w",padx=10)
            return
        type_colors = {"citation":GREEN, "arrest":RED, "warrant":INDIGO, "shift":CYAN}
        for idx, item in enumerate(reversed(items)):
            t = item.get("type","?")
            c = type_colors.get(t, TEXT)
            preview = item.get("content","").split("\n")[0][:60]
            row_bg = CARD if idx % 2 == 0 else CARD2
            row = tk.Frame(self._sf.inner, bg=row_bg, pady=8, padx=10, cursor="hand2")
            row.pack(fill="x")
            top = tk.Frame(row, bg=row_bg)
            top.pack(fill="x")
            tk.Label(top, text=t.upper(), font=(F,7,"bold"), bg=c, fg=BG,
                     padx=5, pady=1).pack(side="left")
            tk.Label(top, text=item.get("timestamp",""), font=(F,8),
                     bg=row_bg, fg=MUTED).pack(side="right")
            tk.Label(row, text=preview, font=(F,9), bg=row_bg,
                     fg=TEXT2, anchor="w").pack(fill="x", pady=(4,0))
            content = item.get("content","")
            def _copy(content=content):
                pyperclip.copy(content)
                self.app._toast("Copied from history!")
            for w in (row, top):
                w.bind("<Button-1>", lambda e, f=_copy: f())

    def _clear(self):
        if messagebox.askyesno("Clear History","Delete all saved history? This cannot be undone."):
            save_history([])
            self._populate([])
            self.app._toast("History cleared.")

# ── Dispatch command registry ─────────────────────────────────────────────────
# (phrase list, handler method name, human-readable description)
DISPATCH_COMMANDS = [
    (["generate citation","make citation","create citation"], "cmd_gen_citation", "Generate the current citation"),
    (["generate arrest report","make arrest report","create arrest report","generate arrest"], "cmd_gen_arrest", "Generate the arrest report"),
    (["generate warrant","make warrant","create warrant","generate warrant request"], "cmd_gen_warrant", "Generate the warrant request"),
    (["clear charges","clear citation","reset charges"], "cmd_clear", "Clear all added charges"),
    (["copy citation"], "cmd_copy_citation", "Copy the last generated citation"),
    (["open settings","show settings"], "cmd_open_settings", "Open the Settings window"),
    (["open history","show history"], "cmd_open_history", "Open the History window"),
    (["go to citation","switch to citation","citation tab"], "cmd_tab_citation", "Switch to the Citation tab"),
    (["go to arrest","switch to arrest","arrest tab"], "cmd_tab_arrest", "Switch to the Arrest tab"),
    (["go to warrant","switch to warrant","warrant tab"], "cmd_tab_warrant", "Switch to the Warrant tab"),
    (["go to phrases","switch to phrases","phrases tab"], "cmd_tab_phrases", "Switch to the Quick Phrases tab"),
    (["go to shift","switch to shift","shift tab"], "cmd_tab_shift", "Switch to the Shift tab"),
    (["help","commands","what can you do"], "cmd_help", "List available commands"),
]
# ── Main Application ──────────────────────────────────────────────────────────
class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.title("GVCR Tool  ·  by x3alpy")
        self.geometry("1520x940")
        self.minsize(1220,760)

        # State
        self.charges       = []
        self.search_var    = tk.StringVar()
        self._last_cit     = ""
        self._last_arr     = ""
        self._last_war     = ""
        self._pending_imgs = {}
        self._dynamic_phrase_labels = []
        self._current_mode = None
        self.settings      = load_settings()
        apply_theme(self.settings.get("theme","Midnight Blue"))
        self.configure(bg=BG)

        splash=Splash(self)
        splash.progress("Loading penal codes...",30)
        self._build_ui()
        splash.progress("Ready!",100)
        time.sleep(0.12)
        splash.destroy()
        self.deiconify()
        self._post_build_init()
        self._poll_images()

    def _post_build_init(self):
        self._switch_sec(list(PENAL_CODES.keys())[0])
        self._refresh_queue()
        self._refresh_charge_summary()
        self.apply_officer_defaults()

    def rebuild_ui(self):
        """Tears down and rebuilds every widget (used after a theme change).
        self.charges / self.settings are instance state and survive intact."""
        for w in self.winfo_children():
            w.destroy()
        self._frames = {}
        self._dynamic_phrase_labels = []
        self._current_mode = None
        self.configure(bg=BG)
        self._build_ui()
        self._post_build_init()

    # ── Image queue poll (main thread safe) ───────────────────────────────────
    def _poll_images(self):
        try:
            while True:
                data, url, cb_name = _img_queue.get_nowait()
                lbl = self._pending_imgs.get(cb_name)
                if lbl and lbl.winfo_exists():
                    if data and url not in _img_cache:
                        _img_cache[url] = data
                    raw = _img_cache.get(url)
                    if raw:
                        try:
                            img=tk.PhotoImage(data=base64.b64encode(raw))
                            lbl._photo=img
                            lbl.configure(image=img,text="")
                        except Exception: pass
        except queue.Empty: pass
        except Exception: pass
        if self.winfo_exists():
            self.after(200,self._poll_images)

    # ── Build UI ──────────────────────────────────────────────────────────────
    def apply_officer_defaults(self):
        name = self.settings.get("officer_name","").strip()
        if not name: return
        e = getattr(self,"_f_prov",None)
        if not e: return
        cur = getv(e)
        if not cur or cur == getattr(self,"_last_applied_officer",None):
            e.delete(0,"end"); e.insert(0,name); e.configure(fg=TEXT)
            self._last_applied_officer = name

    def _build_ui(self):
        self._build_topbar()
        tk.Frame(self,bg=BORDER,height=1).pack(fill="x")
        self._content=tk.Frame(self,bg=BG)
        self._content.pack(fill="both",expand=True)
        self._frames = {}
        self._build_citation_tab()
        self._build_arrest_tab()
        self._build_warrant_tab()
        self._build_phrases_tab()
        self._build_dispatch_tab()
        self._build_shift_tab()
        self._set_mode("citation")

    def _build_topbar(self):
        bar=tk.Frame(self,bg=PANEL,pady=0)
        bar.pack(fill="x")
        try:
            self._tlogo=tk.PhotoImage(data=LOGO_B64_48)
            tk.Label(bar,image=self._tlogo,bg=PANEL).pack(side="left",padx=(12,8),pady=6)
        except Exception: pass
        tf=tk.Frame(bar,bg=PANEL)
        tf.pack(side="left",pady=9)
        tk.Label(tf,text="GVCR Citation Tool",
                 font=(FONT(),14,"bold"),bg=PANEL,fg=TEXT).pack(anchor="w")
        sub=tk.Frame(tf,bg=PANEL)
        sub.pack(anchor="w")
        tk.Label(sub,text="Greenville Community Roleplay  ·  Public Services  · ",
                 font=(FONT(),8),bg=PANEL,fg=MUTED).pack(side="left")
        ShinyLabel(sub,text="Made by x3alpy",
                   font=(FONT(),8,"bold"),bg=PANEL,width=100).pack(side="left")

        nav=tk.Frame(bar,bg=PANEL)
        nav.pack(side="left",padx=20,pady=10)
        self._mode_btns={}
        for key,lbl in [("citation","🎫  Citation"),("arrest","🚨  Arrest"),
                        ("warrant","📋  Warrant"),("phrases","💬  Phrases"),
                        ("dispatch","🎙  Dispatch"),("shift","⏱️  Shift")]:
            b=btn(nav,lbl,lambda k=key:self._set_mode(k),
                  bg=CARD2,hbg=BORDER,fg=MUTED,fs=9,pady=7,padx=13,bold=False)
            b.pack(side="left",padx=3)
            self._mode_btns[key]=b

        btn(bar,"📻",lambda:self._show_radio_modal(),
            bg=CARD2,hbg=BORDER,fg=TEXT2,fs=11,pady=6,padx=10,bold=False
            ).pack(side="right",padx=(0,6),pady=10)
        btn(bar,"🕘",lambda:HistoryWindow(self),
            bg=CARD2,hbg=BORDER,fg=TEXT2,fs=11,pady=6,padx=10,bold=False
            ).pack(side="right",padx=(0,6),pady=10)
        btn(bar,"⚙",lambda:SettingsWindow(self),
            bg=CARD2,hbg=BORDER,fg=TEXT2,fs=11,pady=6,padx=10,bold=False
            ).pack(side="right",padx=(0,6),pady=10)

        self._cnt_var=tk.StringVar(value="0 charges")
        pill=tk.Frame(bar,bg=BORDER2,padx=10,pady=5)
        pill.pack(side="right",padx=8,pady=12)
        tk.Label(pill,textvariable=self._cnt_var,font=(FONT(),9,"bold"),
                 bg=BORDER2,fg=ACCENT).pack()

        sf=tk.Frame(bar,bg=CARD2,highlightbackground=BORDER2,
                    highlightthickness=1,padx=4,pady=4)
        sf.pack(side="right",padx=8,pady=10)
        tk.Label(sf,text="⌕",bg=CARD2,fg=MUTED,font=(FONT(),12)).pack(side="left",padx=(2,2))
        self._srch_entry=tk.Entry(sf,textvariable=self.search_var,bg=CARD2,fg=TEXT,
                                   insertbackground=ACCENT,relief="flat",
                                   font=(FONT(),10),width=20,bd=0)
        self._srch_entry.pack(side="left",padx=(0,4))

        self._search_timer = None
        def _on_search(*args):
            if getattr(self, "_search_timer", None):
                self.after_cancel(self._search_timer)
            self._search_timer = self.after(300, lambda: self._populate_codes(query=self.search_var.get()))
        self.search_var.trace_add("write", _on_search)

    # ── Animated color helper (used for tab-switch highlight) ─────────────────
    def _animate_color(self, widget, from_hex, to_hex, steps=8, delay=14):
        def hx(c): return int(c[1:3],16),int(c[3:5],16),int(c[5:7],16)
        fr = hx(from_hex); to = hx(to_hex)
        def step(i=0):
            if not widget.winfo_exists(): return
            t = i/steps
            r = int(fr[0]+(to[0]-fr[0])*t)
            g = int(fr[1]+(to[1]-fr[1])*t)
            b = int(fr[2]+(to[2]-fr[2])*t)
            widget.configure(bg=f"#{r:02x}{g:02x}{b:02x}")
            if i < steps:
                widget.after(delay, lambda: step(i+1))
        step()

    def _set_mode(self,mode):
        prev = self._current_mode
        for k,b in self._mode_btns.items():
            if k==mode:
                b.configure(fg=TEXT,font=(FONT(),9,"bold"))
                self._animate_color(b, CARD2, ACCENT)
                b.bind("<Enter>",lambda e,x=b:x.configure(bg=ACCENT_H))
                b.bind("<Leave>",lambda e,x=b:x.configure(bg=ACCENT))
            elif k==prev:
                b.configure(fg=MUTED,font=(FONT(),9))
                self._animate_color(b, ACCENT, CARD2)
                b.bind("<Enter>",lambda e,x=b:x.configure(bg=BORDER))
                b.bind("<Leave>",lambda e,x=b:x.configure(bg=CARD2))
            else:
                b.configure(bg=CARD2,fg=MUTED,font=(FONT(),9))
                b.bind("<Enter>",lambda e,x=b:x.configure(bg=BORDER))
                b.bind("<Leave>",lambda e,x=b:x.configure(bg=CARD2))
        self._current_mode = mode
        for f in self._frames.values(): f.pack_forget()
        self._frames[mode].pack(fill="both",expand=True)

    # ── Citation Tab ──────────────────────────────────────────────────────────
    def _build_citation_tab(self):
        frame=tk.Frame(self._content,bg=BG)
        self._frames["citation"]=frame

        body=tk.Frame(frame,bg=BG)
        body.pack(fill="both",expand=True,padx=12,pady=12)

        left=tk.Frame(body,bg=BG)
        left.pack(side="left",fill="both",expand=True,padx=(0,10))

        tab_strip=tk.Frame(left,bg=CARD,padx=8,pady=7)
        tab_strip.pack(fill="x",pady=(0,8))
        self._sec_btns={}
        self._active_sec=tk.StringVar(value=list(PENAL_CODES.keys())[0])
        for sec in PENAL_CODES:
            num=sec.split(":")[0].strip().split(" ")[-1]
            title=(sec.split(":",1)[1].strip() if ":" in sec else sec)[:14]
            b=btn(tab_strip,f"S{num}  {title}",lambda s=sec:self._switch_sec(s),
                  bg=CARD2,hbg=BORDER,fg=MUTED,fs=8,pady=7,padx=10,bold=False)
            b.pack(side="left",padx=3)
            self._sec_btns[sec]=b

        code_wrap=tk.Frame(left,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
        code_wrap.pack(fill="both",expand=True)
        self._code_scroll=ScrollFrame(code_wrap,bg=CARD)
        self._code_scroll.pack(fill="both",expand=True)
        self._code_scroll.bind_scroll()
        self._code_f=self._code_scroll.inner

        right=tk.Frame(body,bg=BG,width=400)
        right.pack(side="right",fill="y")
        right.pack_propagate(False)

        det=tk.Frame(right,bg=CARD,padx=16,pady=14)
        det.pack(fill="x")
        tk.Label(det,text="CITATION DETAILS",font=(FONT(),9,"bold"),
                 bg=CARD,fg=ACCENT).pack(anchor="w",pady=(0,4))
        hline(det,pady=(0,10))
        self._f_prov=inp(det,"Ticket Provider","Officer name...")
        self._f_off =inp(det,"Offender","Offender name...")

        tot=tk.Frame(right,bg=BG)
        tot.pack(fill="x",pady=(10,2),padx=2)
        tk.Label(tot,text="CHARGES",font=(FONT(),8,"bold"),
                 bg=BG,fg=ACCENT).pack(side="left")
        self._tot_var=tk.StringVar(value="")
        tk.Label(tot,textvariable=self._tot_var,font=(FONT(),8,"bold"),
                 bg=BG,fg=YELLOW).pack(side="right")

        chart_wrap = tk.Frame(right, bg=CARD, highlightbackground=BORDER, highlightthickness=1)
        chart_wrap.pack(fill="x", pady=(4,6))
        self._cit_chart = AnimatedBarChart(
            chart_wrap, [("Citation",GREEN),("Misdemeanor",ORANGE),("Felony",RED)],
            bg=CARD, height=68)
        self._cit_chart.pack(fill="x", padx=6, pady=4)

        q_wrap=tk.Frame(right,bg=CARD,highlightbackground=BORDER,highlightthickness=1)
        q_wrap.pack(fill="x")
        self._q_scroll=ScrollFrame(q_wrap,bg=CARD,height=150)
        self._q_scroll.pack(fill="both",expand=True)
        self._q_scroll.bind_scroll()
        self._q_f=self._q_scroll.inner

        act=tk.Frame(right,bg=BG)
        act.pack(fill="x",pady=(6,0))
        btn(act,"✕  Clear All",self._clear,
            bg=RED_D,hbg="#500d0d",fg=RED,fs=9,pady=9
            ).pack(side="left",fill="x",expand=True,padx=(0,4))
        btn(act,"⚡  Generate",self._gen_citation,
            bg=ACCENT,hbg=ACCENT_H,fg=TEXT,fs=9,pady=9
            ).pack(side="left",fill="x",expand=True,padx=(4,0))
        btn(right,"📋  Copy to Clipboard",self._copy_cit,
            bg=GREEN_D,hbg="#073d1a",fg=GREEN,fs=10,pady=10
            ).pack(fill="x",pady=(5,0))

        tk.Label(right,text="OUTPUT",font=(FONT(),8,"bold"),
                 bg=BG,fg=ACCENT).pack(anchor="w",pady=(10,3))
        out_wrap=tk.Frame(right,bg=BORDER,padx=1,pady=1)
        out_wrap.pack(fill="both",expand=True)
        self._cit_out=tk.Text(out_wrap,bg=CARD,fg=TEXT,
                              font=("Courier New",10),relief="flat",
                              wrap="word",padx=12,pady=10,
                              insertbackground=ACCENT,
                              selectbackground=SEL,selectforeground=TEXT)
        self._cit_out.pack(fill="both",expand=True)
        self._write(self._cit_out,
                    "Add charges from the left,\nfill in the details above,\nthen hit ⚡ Generate.")

    # ── Arrest Tab ────────────────────────────────────────────────────────────
    def _build_arrest_tab(self):
        frame=tk.Frame(self._content,bg=BG)
        self._frames["arrest"]=frame
        body=tk.Frame(frame,bg=BG)
        body.pack(fill="both",expand=True,padx=14,pady=14)

        left=tk.Frame(body,bg=BG)
        left.pack(side="left",fill="both",expand=True,padx=(0,12))

        notice=tk.Frame(left,bg=CARD2,padx=14,pady=10,
                        highlightbackground=ACCENT,highlightthickness=1)
        notice.pack(fill="x",pady=(0,12))
        tk.Label(notice,text="⚡  Charges from the Citation tab are shared automatically.",
                 font=(FONT(),9),bg=CARD2,fg=CYAN).pack(side="left")
        btn(notice,"→ Add Charges",lambda:self._set_mode("citation"),
            bg=ACCENT,hbg=ACCENT_H,fg=TEXT,fs=8,pady=5,padx=10
            ).pack(side="right")

        tk.Label(left,text="REPORT DETAILS",font=(FONT(),9,"bold"),
                 bg=BG,fg=ACCENT).pack(anchor="w",pady=(0,6))
        form=tk.Frame(left,bg=CARD,padx=16,pady=14,
                      highlightbackground=BORDER,highlightthickness=1)
        form.pack(fill="x")
        self._a_off  =inp(form,"Involved Officer(s)","@Officer1, @Officer2")
        self._a_dept =inp(form,"Department(s)","e.g. LCPD, BCSO")
        self._a_susp =inp(form,"Suspect(s)","@Suspect1, @Suspect2")

        tk.Label(left,text="CHARGE BREAKDOWN",font=(FONT(),9,"bold"),
                 bg=BG,fg=ACCENT).pack(anchor="w",pady=(14,6))
        chart_card = tk.Frame(left, bg=CARD, padx=12, pady=10,
                              highlightbackground=BORDER, highlightthickness=1)
        chart_card.pack(fill="x")
        self._arr_chart = AnimatedBarChart(
            chart_card, [("Citation",GREEN),("Misdemeanor",ORANGE),("Felony",RED)],
            bg=CARD, height=68)
        self._arr_chart.pack(fill="x")

        # Vehicle Information — restored for format/compatibility only.
        # Locked: every field is a static "N/A" label, nothing to edit or select.
        tk.Label(left,text="VEHICLE INFORMATION",font=(FONT(),9,"bold"),
                 bg=BG,fg=MUTED).pack(anchor="w",pady=(14,6))
        vcard=tk.Frame(left,bg=CARD,padx=16,pady=14,
                       highlightbackground=BORDER,highlightthickness=1)
        vcard.pack(fill="x")
        tk.Label(vcard,text="This section is fixed to N/A and cannot be edited — "
                 "kept only to preserve the report format.",
                 font=(FONT(),8),bg=CARD,fg=MUTED,wraplength=420,justify="left"
                 ).pack(anchor="w",pady=(0,8))
        for lbl in ["Vehicle Make","Vehicle Model","Vehicle Plate","Vehicle Official Registry"]:
            row=tk.Frame(vcard,bg=CARD)
            row.pack(fill="x",pady=2)
            tk.Label(row,text=lbl+":",font=(FONT(),9),bg=CARD,fg=TEXT2,
                     width=22,anchor="w").pack(side="left")
            tk.Label(row,text="N/A",font=(FONT(),9,"bold"),bg=CARD,fg=MUTED
                     ).pack(side="left")

        right=tk.Frame(body,bg=BG,width=400)
        right.pack(side="right",fill="y")
        right.pack_propagate(False)

        btn(right,"⚡  Generate Arrest Report",self._gen_arrest,
            bg=RED,hbg="#f87171",fg=TEXT,fs=10,pady=11
            ).pack(fill="x",pady=(0,5))
        btn(right,"📋  Copy Report",self._copy_arr,
            bg=GREEN_D,hbg="#073d1a",fg=GREEN,fs=10,pady=10
            ).pack(fill="x",pady=(0,12))
        tk.Label(right,text="OUTPUT",font=(FONT(),8,"bold"),
                 bg=BG,fg=ACCENT).pack(anchor="w",pady=(0,4))
        ow=tk.Frame(right,bg=BORDER,padx=1,pady=1)
        ow.pack(fill="both",expand=True)
        self._arr_out=tk.Text(ow,bg=CARD,fg=TEXT,font=("Courier New",10),
                              relief="flat",wrap="word",padx=12,pady=10,
                              insertbackground=ACCENT,selectbackground=SEL)
        self._arr_out.pack(fill="both",expand=True)
        self._write(self._arr_out,"Fill in the details and hit Generate.")

    # ── Warrant Tab ───────────────────────────────────────────────────────────
    def _build_warrant_tab(self):
        frame=tk.Frame(self._content,bg=BG)
        self._frames["warrant"]=frame
        body=tk.Frame(frame,bg=BG)
        body.pack(fill="both",expand=True,padx=14,pady=14)

        left=tk.Frame(body,bg=BG)
        left.pack(side="left",fill="both",expand=True,padx=(0,12))

        notice=tk.Frame(left,bg=CARD2,padx=14,pady=10,
                        highlightbackground=INDIGO,highlightthickness=1)
        notice.pack(fill="x",pady=(0,12))
        tk.Label(notice,text="⚡  Charges from the Citation tab are shared automatically.",
                 font=(FONT(),9),bg=CARD2,fg=CYAN).pack(side="left")
        btn(notice,"→ Add Charges",lambda:self._set_mode("citation"),
            bg=INDIGO,hbg=INDIGO_H,fg=TEXT,fs=8,pady=5,padx=10
            ).pack(side="right")

        tk.Label(left,text="WARRANT DETAILS",font=(FONT(),9,"bold"),
                 bg=BG,fg=INDIGO).pack(anchor="w",pady=(0,6))
        form=tk.Frame(left,bg=CARD,padx=16,pady=14,
                      highlightbackground=BORDER,highlightthickness=1)
        form.pack(fill="x")
        self._w_off  =inp(form,"Involved Officer(s)","@Officer1, @Officer2")
        self._w_dept =inp(form,"Department(s)","e.g. LCPD, BCSO")
        self._w_susp =inp(form,"Suspect(s)","@Suspect1, @Suspect2")

        right=tk.Frame(body,bg=BG,width=400)
        right.pack(side="right",fill="y")
        right.pack_propagate(False)

        btn(right,"⚡  Generate Warrant Request",self._gen_warrant,
            bg=INDIGO,hbg=INDIGO_H,fg=TEXT,fs=10,pady=11
            ).pack(fill="x",pady=(0,5))
        btn(right,"📋  Copy Warrant",self._copy_war,
            bg=GREEN_D,hbg="#073d1a",fg=GREEN,fs=10,pady=10
            ).pack(fill="x",pady=(0,12))
        tk.Label(right,text="OUTPUT",font=(FONT(),8,"bold"),
                 bg=BG,fg=INDIGO).pack(anchor="w",pady=(0,4))
        ow=tk.Frame(right,bg=BORDER,padx=1,pady=1)
        ow.pack(fill="both",expand=True)
        self._war_out=tk.Text(ow,bg=CARD,fg=TEXT,font=("Courier New",10),
                              relief="flat",wrap="word",padx=12,pady=10,
                              insertbackground=ACCENT,selectbackground=SEL)
        self._war_out.pack(fill="both",expand=True)
        self._write(self._war_out,"Fill in the details and hit Generate.")

    # ── Phrases Tab ───────────────────────────────────────────────────────────
    def _build_phrases_tab(self):
        frame=tk.Frame(self._content,bg=BG)
        self._frames["phrases"]=frame
        outer=tk.Frame(frame,bg=BG)
        outer.pack(fill="both",expand=True,padx=16,pady=14)

        tk.Label(outer,text="Quick Copy Phrases",
                 font=(FONT(),15,"bold"),bg=BG,fg=TEXT).pack(anchor="w")
        tk.Label(outer,text="Click any row to instantly copy that phrase to your clipboard. "
                 "Rows marked (auto) always reflect your current charges and settings.",
                 font=(FONT(),9),bg=BG,fg=MUTED,wraplength=760,justify="left"
                 ).pack(anchor="w",pady=(2,14))

        sf=ScrollFrame(outer,bg=BG)
        sf.pack(fill="both",expand=True)
        sf.bind_scroll()
        grid=sf.inner

        left_col=tk.Frame(grid,bg=BG)
        left_col.pack(side="left",fill="both",expand=True,padx=(0,8))
        right_col=tk.Frame(grid,bg=BG)
        right_col.pack(side="left",fill="both",expand=True,padx=(8,0))

        cats=list(QUICK_PHRASES.items())
        for idx,(cat,phrases) in enumerate(cats):
            col=left_col if idx%2==0 else right_col
            hdr=tk.Frame(col,bg=CARD2,padx=14,pady=9)
            hdr.pack(fill="x",pady=(0,2))
            cat_colors=[ACCENT,RED,INDIGO,CYAN]
            cc=cat_colors[idx%len(cat_colors)]
            tk.Frame(hdr,bg=cc,width=3).pack(side="left",fill="y",padx=(0,8))
            tk.Label(hdr,text=cat,font=(FONT(),10,"bold"),
                     bg=CARD2,fg=TEXT).pack(side="left",anchor="w")
            for label,phrase in phrases:
                self._phrase_row(col,label,phrase,cc)
            tk.Frame(col,bg=BG,height=12).pack()

        summ_frame=tk.Frame(grid,bg=BG)
        summ_frame.pack(fill="x",side="bottom",pady=(10,0))
        self._charge_summ_frame=summ_frame
        self._refresh_charge_summary()

    def _compute_dynamic_phrase(self, key):
        if key == "__DYNAMIC_CITED__":
            if not self.charges:
                return "You are being cited for the following violation(s):\n  (no charges added yet)"
            lines = ["You are being cited for the following violation(s):"]
            for _, code, ref, pen, cls in self.charges:
                lines.append(f"  • {code} {ref} — {pen}")
            return "\n".join(lines)
        if key == "__DYNAMIC_GREETING__":
            officer  = self.settings.get("officer_name","").strip() or "[Officer Name]"
            division = self.settings.get("division","").strip() or "[Department]"
            template = self.settings.get("greeting_template") or DEFAULT_SETTINGS["greeting_template"]
            try:
                return template.format(officer=officer, division=division)
            except Exception:
                return template
        return key

    def _refresh_dynamic_phrases(self):
        for marker, widget in self._dynamic_phrase_labels:
            if widget.winfo_exists():
                widget.config(text=self._compute_dynamic_phrase(marker))

    def _phrase_row(self,parent,label,phrase,accent_color):
        is_dynamic = isinstance(phrase, str) and phrase.startswith("__DYNAMIC_")
        display_label = f"{label}  (auto)" if is_dynamic else label

        row=tk.Frame(parent,bg=CARD,pady=0,cursor="hand2")
        row.pack(fill="x",pady=1)

        accent_bar=tk.Frame(row,bg=CARD,width=3)
        accent_bar.pack(side="left",fill="y")

        inner=tk.Frame(row,bg=CARD)
        inner.pack(side="left",fill="x",expand=True,padx=10,pady=8)

        lbl_w=tk.Label(inner,text=display_label,font=(FONT(),9,"bold"),
                       bg=CARD,fg=(CYAN if is_dynamic else TEXT2),anchor="w",width=22)
        lbl_w.pack(side="left")
        initial_text = self._compute_dynamic_phrase(phrase) if is_dynamic else phrase
        ph_w=tk.Label(inner,text=initial_text,font=(FONT(),9),bg=CARD,
                      fg=MUTED,anchor="w",justify="left",wraplength=450)
        ph_w.pack(side="left",fill="x",expand=True,padx=(8,0))
        if is_dynamic:
            self._dynamic_phrase_labels.append((phrase, ph_w))

        copied_lbl=tk.Label(row,text="",font=(FONT(),8,"bold"),
                            bg=CARD,fg=GREEN,width=8)
        copied_lbl.pack(side="right",padx=8)

        all_w=[row,inner,lbl_w,ph_w,accent_bar,copied_lbl]

        def on_click(p=phrase,cl=copied_lbl,r=row,ab=accent_bar,aw=all_w,ac=accent_color):
            text_to_copy = self._compute_dynamic_phrase(p) if (isinstance(p,str) and p.startswith("__DYNAMIC_")) else p
            pyperclip.copy(text_to_copy)
            cl.config(text="✓ Copied")
            r.configure(bg=SEL)
            for w in aw:
                try: w.configure(bg=SEL)
                except Exception: pass
            ab.configure(bg=ac)
            r.after(1400,lambda: (
                r.configure(bg=CARD),
                cl.config(text=""),
                ab.configure(bg=CARD),
                [w.configure(bg=CARD) for w in aw if w!=ab]
            ))

        def on_enter(e,r=row,ab=accent_bar,aw=all_w,ac=accent_color):
            r.configure(bg=BORDER)
            for w in aw:
                try: w.configure(bg=BORDER)
                except Exception: pass
            ab.configure(bg=ac)

        def on_leave(e,r=row,ab=accent_bar,aw=all_w):
            r.configure(bg=CARD)
            for w in aw:
                try: w.configure(bg=CARD)
                except Exception: pass

        for w in all_w:
            w.bind("<Button-1>",lambda e,f=on_click:f())
            w.bind("<Enter>",on_enter)
            w.bind("<Leave>",on_leave)

    def _refresh_charge_summary(self):
        f=self._charge_summ_frame
        for w in f.winfo_children(): w.destroy()
        if not self.charges:
            tk.Label(f,text="📋  Add charges in the Citation tab — they'll appear here.",
                     font=(FONT(),9),bg=BG,fg=MUTED).pack(anchor="w")
            return
        hdr=tk.Frame(f,bg=BG)
        hdr.pack(fill="x",pady=(0,6))
        tk.Label(hdr,text="CURRENT CHARGES",font=(FONT(),9,"bold"),
                 bg=BG,fg=ACCENT).pack(side="left")
        def _copy_summary():
            lines=["You are being cited for the following:"]
            for _,code,ref,pen,cls in self.charges:
                lines.append(f"  • {code} — {ref} ({pen})")
            pyperclip.copy("\n".join(lines))
            self._toast("Charge summary copied!")
        btn(hdr,"📋 Copy Summary",_copy_summary,
            bg=INDIGO,hbg=INDIGO_H,fg=TEXT,fs=8,pady=4,padx=8
            ).pack(side="right")
        for _,code,ref,pen,cls in self.charges:
            clr=CLASS_COLOR.get(cls,TEXT)
            cbg=CLASS_BG.get(cls,MUTED2)
            row=tk.Frame(f,bg=CARD,pady=7,padx=10)
            row.pack(fill="x",pady=2)
            tk.Label(row,text=code,font=("Courier New",8,"bold"),
                     bg=cbg,fg=clr,padx=6).pack(side="left",padx=(0,8))
            tk.Label(row,text=ref,font=(FONT(),9),bg=CARD,
                     fg=TEXT2,anchor="w").pack(side="left",fill="x",expand=True)
            tk.Label(row,text=cls,font=(FONT(),7,"bold"),
                     bg=cbg,fg=clr,padx=5).pack(side="right")

# ── Radio Modal ─────────────────────────────────────────────────────────
    def _show_radio_modal(self):
        modal = tk.Toplevel(self)
        modal.title("Radio Language Reference")
        modal.geometry("900x700")
        modal.configure(bg=BG)
        modal.transient(self)
        modal.grab_set()

        wrap = tk.Frame(modal, bg=BG, padx=20, pady=20)
        wrap.pack(fill="both", expand=True)

        tk.Label(wrap, text="📻 Radio Language", font=(FONT(), 16, "bold"), 
                 bg=BG, fg=TEXT).pack(anchor="w")
        tk.Label(wrap, text="10-Codes, Signals, Response Codes and Phonetic Alphabet.", 
                 font=(FONT(), 9), bg=BG, fg=MUTED).pack(anchor="w", pady=(0, 15))

        sf = ScrollFrame(wrap, bg=BG)
        sf.pack(fill="both", expand=True)
        sf.bind_scroll()
        grid = sf.inner

        col1 = tk.Frame(grid, bg=BG)
        col1.pack(side="left", fill="both", expand=True, padx=(0, 10))
        col2 = tk.Frame(grid, bg=BG)
        col2.pack(side="left", fill="both", expand=True)

        for idx, (cat, lines) in enumerate(RADIO_CODES_DATA.items()):
            target_col = col1 if idx % 2 == 0 else col2
            card = tk.Frame(target_col, bg=CARD, padx=14, pady=14, highlightbackground=BORDER, highlightthickness=1)
            card.pack(fill="x", pady=(0, 10))
            
            tk.Label(card, text=cat, font=(FONT(), 10, "bold"), bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0, 8))
            
            for line in lines:
                row = tk.Frame(card, bg=CARD)
                row.pack(fill="x", pady=1)
                
                if " " in line:
                    parts = line.split(" ", 1)
                    tk.Label(row, text=parts[0] + " ", font=(FONT(), 9, "bold"), bg=CARD, fg=TEXT2).pack(side="left", anchor="n")
                    tk.Label(row, text=parts[1], font=(FONT(), 9), bg=CARD, fg=MUTED, justify="left", anchor="w", wraplength=280).pack(side="left", fill="x", expand=True)
                else:
                    tk.Label(row, text=line, font=(FONT(), 9), bg=CARD, fg=TEXT2, justify="left", anchor="w", wraplength=280).pack(side="left", fill="x", expand=True)

# ── Shift Tab ────────────────────────────────────────────────────────────
    def _build_shift_tab(self):
        frame = tk.Frame(self._content, bg=BG)
        self._frames["shift"] = frame
        body = tk.Frame(frame, bg=BG)
        body.pack(fill="both", expand=True, padx=14, pady=14)

        left = tk.Frame(body, bg=BG)
        left.pack(side="left", fill="both", expand=True, padx=(0, 12))

        notice = tk.Frame(left, bg=CARD2, padx=14, pady=10, highlightbackground=ACCENT, highlightthickness=1)
        notice.pack(fill="x", pady=(0, 12))
        tk.Label(notice, text="⏱️ 1. Clock In ➔ 2. Clock Out ➔ 3. Fill details ➔ 4. Generate.",
                 font=(FONT(), 9), bg=CARD2, fg=CYAN).pack(side="left")

        timer_card = tk.Frame(left, bg=CARD, padx=16, pady=30, highlightbackground=BORDER, highlightthickness=1)
        timer_card.pack(fill="x", pady=(0, 14))
        
        self._shift_time_var = tk.StringVar(value="00:00:00")
        self._shift_status_var = tk.StringVar(value="Off Duty (OCSO)")
        
        tk.Label(timer_card, textvariable=self._shift_time_var, font=("Courier New", 28, "bold"), bg=CARD, fg=TEXT).pack()
        tk.Label(timer_card, textvariable=self._shift_status_var, font=(FONT(), 10), bg=CARD, fg=MUTED).pack(pady=(0, 15))

        btn_row = tk.Frame(timer_card, bg=CARD)
        btn_row.pack()
        self._btn_clock_in = btn(btn_row, "🟢 Clock In", self._clock_in, bg=ACCENT, hbg=ACCENT_H, fg=TEXT)
        self._btn_clock_in.pack(side="left", padx=5)
        self._btn_clock_out = btn(btn_row, "🔴 Clock Out", self._clock_out, bg=RED, hbg="#f87171", fg=TEXT)
        
        self._shift_details_card = tk.Frame(left, bg=CARD, padx=16, pady=14, highlightbackground=BORDER, highlightthickness=1)
        self._shift_details_card.pack(fill="x")
        
        tk.Label(self._shift_details_card, text="SHIFT DETAILS", font=(FONT(), 9, "bold"), bg=CARD, fg=ACCENT).pack(anchor="w", pady=(0, 6))
        self._shift_user = inp(self._shift_details_card, "Discord Username", "@username")
        self._shift_rank = inp(self._shift_details_card, "Rank", "e.g. Deputy")
        self._shift_notes = inp(self._shift_details_card, "Shift Notes", "What did you do this shift?")
        
        # Set disabled state initially
        self._toggle_shift_details(False)

        right = tk.Frame(body, bg=BG, width=400)
        right.pack(side="right", fill="y")
        right.pack_propagate(False)
        
        self._gen_shift_btn = btn(right, "⚡  Generate Shift Log", self._gen_shift_log, bg=INDIGO, hbg=INDIGO_H, fg=TEXT, fs=10, pady=11)
        self._gen_shift_btn.pack(fill="x", pady=(0, 5))
        self._gen_shift_btn.configure(state="disabled", bg=BORDER, fg=MUTED)
        
        btn(right, "📋  Copy Log", self._copy_shift, bg=GREEN_D, hbg="#073d1a", fg=GREEN, fs=10, pady=10).pack(fill="x", pady=(0, 12))
        
        tk.Label(right, text="SHIFT LOG OUTPUT", font=(FONT(), 8, "bold"), bg=BG, fg=INDIGO).pack(anchor="w", pady=(0, 4))
        ow = tk.Frame(right, bg=BORDER, padx=1, pady=1)
        ow.pack(fill="both", expand=True)
        self._shift_out = tk.Text(ow, bg=CARD, fg=TEXT, font=("Courier New", 10), relief="flat", wrap="word", padx=12, pady=10, insertbackground=ACCENT, selectbackground=SEL)
        self._shift_out.pack(fill="both", expand=True)
        self._write(self._shift_out, "Clock in, clock out, and generate to see the log.")
        
        self._shift_interval = None
        self._shift_start = None
        self._shift_end = None
        self._last_shift = ""

    def _toggle_shift_details(self, enabled):
        state = "normal" if enabled else "disabled"
        bg = CARD if enabled else CARD2
        self._shift_details_card.configure(bg=bg, highlightbackground=BORDER if enabled else MUTED2)
        # Recursively disable inputs
        for child in self._shift_details_card.winfo_children():
            if isinstance(child, tk.Frame):
                child.configure(bg=bg)
                for sub in child.winfo_children():
                    if isinstance(sub, tk.Entry):
                        sub.configure(state=state, disabledbackground=bg, disabledforeground=MUTED)

    def _clock_in(self):
        self._shift_start = datetime.datetime.now()
        self._shift_end = None
        self._shift_status_var.set("On Duty (OCSO)")
        self._shift_status_var.set("On Duty (OCSO)")
        
        # Swap buttons
        self._btn_clock_in.pack_forget()
        self._btn_clock_out.pack(side="left", padx=5)
        
        # Disable details & generate buttons
        self._gen_shift_btn.configure(state="disabled", bg=BORDER, fg=MUTED)
        self._toggle_shift_details(False)
        
        # Clear inputs
        self._shift_user.delete(0, "end")
        self._shift_rank.delete(0, "end")
        self._shift_notes.delete(0, "end")
        
        def tick():
            if self._shift_start:
                delta = datetime.datetime.now() - self._shift_start
                secs = int(delta.total_seconds())
                h, m, s = secs // 3600, (secs % 3600) // 60, secs % 60
                self._shift_time_var.set(f"{h:02d}:{m:02d}:{s:02d}")
                self._shift_interval = self.after(1000, tick)
        tick()
        self._toast("Clocked In to OCSO!")

    def _clock_out(self):
        if self._shift_interval:
            self.after_cancel(self._shift_interval)
        self._shift_end = datetime.datetime.now()
        self._shift_status_var.set("Off Duty (OCSO)")
        
        # Swap buttons
        self._btn_clock_out.pack_forget()
        self._btn_clock_in.pack(side="left", padx=5)
        
        # Enable details & generate buttons
        self._gen_shift_btn.configure(state="normal", bg=INDIGO, fg=TEXT)
        self._toggle_shift_details(True)
        self._toast("Clocked Out! Fill in your details.")

    def _gen_shift_log(self):
        if not self._shift_start or not self._shift_end: return
        
        username = getv(self._shift_user) or "[Username]"
        rank = getv(self._shift_rank) or "[Rank]"
        notes = getv(self._shift_notes) or "[No notes provided]"
        
        start_str = self._shift_start.strftime("%I:%M %p").lstrip("0")
        end_str = self._shift_end.strftime("%I:%M %p").lstrip("0")
        
        delta = self._shift_end - self._shift_start
        secs = int(delta.total_seconds())
        duration = f"{secs // 3600:02d}:{(secs % 3600) // 60:02d}:{secs % 60:02d}"
        
        self._last_shift = (
            "`OUTAGAMIE COUNTY SHERIFF'S OFFICE - SHIFT REPORT`\n\n"
            "`Username:` " + username + "\n"
            "`Rank:` " + rank + "\n"
            "`Shift Duration:` " + duration + " (" + start_str + " - " + end_str + ")\n"
            "`Notes:` " + notes + "\n"
            "`Image Proof:`"
        )
        self._write(self._shift_out, self._last_shift)
        pyperclip.copy(self._last_shift)
        append_history("shift", self._last_shift)
        self._toast("Shift Log generated and copied!")

    def _copy_shift(self):
        if self._last_shift:
            pyperclip.copy(self._last_shift)
            self._toast("Copied!")
        else:
            self._toast("Generate a shift log first.")

    # ── Dispatch Tab ──────────────────────────────────────────────────────────
    def _build_dispatch_tab(self):
        frame=tk.Frame(self._content,bg=BG)
        self._frames["dispatch"]=frame
        outer=tk.Frame(frame,bg=BG,padx=16,pady=14)
        outer.pack(fill="both",expand=True)

        tk.Label(outer,text="🎙  Dispatch",font=(FONT(),15,"bold"),bg=BG,fg=TEXT).pack(anchor="w")
        tk.Label(outer,
                 text='Type a command below — or press Win+H to use Windows dictation and '
                      'speak straight into the box. Try "generate citation", "add reckless driving", '
                      'or "help".',
                 font=(FONT(),9),bg=BG,fg=MUTED,wraplength=760,justify="left"
                 ).pack(anchor="w",pady=(2,12))

        input_row=tk.Frame(outer,bg=CARD,padx=4,pady=4,
                           highlightbackground=BORDER,highlightthickness=1)
        input_row.pack(fill="x",pady=(0,10))
        self._dispatch_var=tk.StringVar()
        entry=tk.Entry(input_row,textvariable=self._dispatch_var,bg=INPUT_BG,fg=TEXT,
                       insertbackground=ACCENT,relief="flat",font=(FONT(),11),bd=8)
        entry.pack(side="left",fill="x",expand=True)
        entry.bind("<Return>", lambda e: self._submit_dispatch())
        btn(input_row,"Send  ⏎",self._submit_dispatch,
            bg=ACCENT,hbg=ACCENT_H,fg=TEXT,fs=9,pady=8
            ).pack(side="right",padx=(6,0))

        log_wrap=tk.Frame(outer,bg=BORDER,padx=1,pady=1)
        log_wrap.pack(fill="both",expand=True)
        self._dispatch_text=tk.Text(log_wrap,bg=CARD,fg=TEXT2,font=("Courier New",10),
                                    relief="flat",wrap="word",padx=12,pady=10,state="disabled")
        self._dispatch_text.pack(fill="both",expand=True)
        self._dispatch_text.tag_config("echo",foreground=TEXT2)
        self._dispatch_text.tag_config("reply",foreground=GREEN)
        self._append_dispatch_log(
            'Dispatch ready. Try "generate citation", "add reckless driving", "open settings", or "help".',
            "reply")

    def _submit_dispatch(self):
        text=self._dispatch_var.get()
        self._dispatch_var.set("")
        self._dispatch_command(text)

    def _append_dispatch_log(self, text, tag):
        w = getattr(self,"_dispatch_text",None)
        if not w or not w.winfo_exists(): return
        w.configure(state="normal")
        w.insert("end", text+"\n\n", tag)
        w.configure(state="disabled")
        w.see("end")

    def _dispatch_echo(self, text):
        self._append_dispatch_log(f"> {text}", "echo")

    def _dispatch_reply(self, text):
        self._append_dispatch_log(text, "reply")
        self._toast(text.split("\n")[0])

    def _find_offense(self, query):
        query = query.strip().lower()
        if not query: return None
        best=None; best_score=0.0
        for sec, entries in PENAL_CODES.items():
            for code, ref, pen, cls in entries:
                rl = ref.lower()
                score = difflib.SequenceMatcher(None, query, rl).ratio()
                if query in rl: score = max(score, 0.85)
                if score > best_score:
                    best_score = score; best=(sec,code,ref,pen,cls)
        return best if best_score >= 0.5 else None

    def _dispatch_command(self, text):
        raw = text.strip()
        if not raw: return
        self._dispatch_echo(raw)
        low = raw.lower()

        if low.startswith("add "):
            match = self._find_offense(low[4:])
            if match:
                sec,code,ref,pen,cls = match
                self._add_charge(sec,code,ref,pen,cls)
                self._dispatch_reply(f"10-4. Added {code} — {ref}.")
            else:
                self._dispatch_reply(f'Copy that, but no offense matched "{raw[4:].strip()}". Try "help".')
            return

        best_score=0.0; best_handler=None
        for phrases, handler, helptext in DISPATCH_COMMANDS:
            for p in phrases:
                score = difflib.SequenceMatcher(None, low, p).ratio()
                if p in low: score = max(score, 0.9)
                if score > best_score:
                    best_score = score; best_handler = handler
        if best_handler and best_score >= 0.55:
            fn = getattr(self, best_handler, None)
            if fn: fn()
            return

        self._dispatch_reply('Copy that? Command not recognized. Type "help" for a list.')

    def cmd_gen_citation(self):
        self._set_mode("citation"); self._gen_citation()
        self._dispatch_reply("10-4. Citation generated and copied.")
    def cmd_gen_arrest(self):
        self._set_mode("arrest"); self._gen_arrest()
        self._dispatch_reply("10-4. Arrest report generated and copied.")
    def cmd_gen_warrant(self):
        self._set_mode("warrant"); self._gen_warrant()
        self._dispatch_reply("10-4. Warrant request generated and copied.")
    def cmd_clear(self):
        self._clear()
        self._dispatch_reply("10-4. Charges cleared.")
    def cmd_copy_citation(self):
        self._copy_cit()
        self._dispatch_reply("10-4. Citation copied.")
    def cmd_open_settings(self):
        SettingsWindow(self)
        self._dispatch_reply("10-4. Opening Settings.")
    def cmd_open_history(self):
        HistoryWindow(self)
        self._dispatch_reply("10-4. Opening History.")
    def cmd_tab_citation(self):
        self._set_mode("citation"); self._dispatch_reply("10-4. Switched to Citation tab.")
    def cmd_tab_arrest(self):
        self._set_mode("arrest"); self._dispatch_reply("10-4. Switched to Arrest tab.")
    def cmd_tab_warrant(self):
        self._set_mode("warrant"); self._dispatch_reply("10-4. Switched to Warrant tab.")
    def cmd_tab_phrases(self):
        self._set_mode("phrases"); self._dispatch_reply("10-4. Switched to Phrases tab.")
    def cmd_tab_shift(self):
        self._set_mode("shift"); self._dispatch_reply("10-4. Switched to Shift tab.")
    def cmd_help(self):
        lines=["Available commands:"]
        for phrases, handler, helptext in DISPATCH_COMMANDS:
            lines.append(f"  • {phrases[0]}  —  {helptext}")
        lines.append('  • add <offense name>  —  Add a charge by name (e.g. "add reckless driving")')
        self._append_dispatch_log("\n".join(lines), "reply")

    # ── Code browser ──────────────────────────────────────────────────────────
    def _switch_sec(self, sec):
        self._active_sec.set(sec)
        if getattr(self, "_search_timer", None):
            self.after_cancel(self._search_timer)
        for s, b in self._sec_btns.items():
            if s == sec:
                b.configure(bg=ACCENT, fg=TEXT, font=(FONT(), 8, "bold"))
                b.bind("<Enter>", lambda e, x=b: x.configure(bg=ACCENT_H))
                b.bind("<Leave>", lambda e, x=b: x.configure(bg=ACCENT))
            else:
                b.configure(bg=CARD2, fg=MUTED, font=(FONT(), 8))
                b.bind("<Enter>", lambda e, x=b: x.configure(bg=BORDER))
                b.bind("<Leave>", lambda e, x=b: x.configure(bg=CARD2))
        self.search_var.set("")
        self._populate_codes(sec)
        self._code_scroll.canvas.yview_moveto(0)

    def _populate_codes(self, sec=None, query=None):
        for w in self._code_f.winfo_children(): w.destroy()
        sec = sec or self._active_sec.get()
        q = (query or self.search_var.get()).strip().lower()

        sections_to_show = []
        if q:
            # Global search across all sections
            for s, codes in PENAL_CODES.items():
                matches = [c for c in codes if any(q in str(x).lower() for x in c)]
                if matches: sections_to_show.append((s, matches))
        else:
            # Standard view for just the active section
            sections_to_show.append((sec, PENAL_CODES.get(sec, [])))

        shown = 0
        for current_sec, codes in sections_to_show:
            hdr=tk.Frame(self._code_f,bg=INDIGO,pady=10,padx=14)
            hdr.pack(fill="x")
            tk.Label(hdr,text=current_sec,font=(FONT(),11,"bold"),bg=INDIGO,fg=TEXT).pack(anchor="w")

            ch=tk.Frame(self._code_f,bg=CARD2,pady=6,padx=6)
            ch.pack(fill="x")
            for t,w in [("CODE",9),("OFFENSE",38),("PENALTY",22),("CLASS",12)]:
                tk.Label(ch,text=t,font=(FONT(),7,"bold"),bg=CARD2,
                         fg=MUTED,width=w,anchor="w").pack(side="left",padx=5)

            for i,(code,ref,penalty,cls) in enumerate(codes):
                shown += 1
                rb=CARD if i%2==0 else CARD2
                clr=CLASS_COLOR.get(cls,TEXT)
                cbg=CLASS_BG.get(cls,MUTED2)
                cbo=CLASS_BORDER.get(cls,BORDER)
                
                # Container for the row + optional note
                row_wrap = tk.Frame(self._code_f, bg=rb)
                row_wrap.pack(fill="x")
                
                row=tk.Frame(row_wrap,bg=rb)
                row.pack(fill="x")

                tk.Frame(row,bg=cbo,width=3).pack(side="left",fill="y")

                badge=tk.Label(row,text=code,font=("Courier New",8,"bold"),
                               bg=cbg,fg=clr,padx=6,pady=6,width=9)
                badge.pack(side="left",padx=(4,6),pady=4)

                ref_fg=YELLOW if q and q in ref.lower() else TEXT2
                rl=tk.Label(row,text=ref,font=(FONT(),9),bg=rb,fg=ref_fg,
                            anchor="w",width=38)
                rl.pack(side="left",padx=(0,4))

                pl=tk.Label(row,text=penalty,font=(FONT(),8),bg=rb,fg=MUTED,
                            anchor="w",width=22)
                pl.pack(side="left",padx=(0,4))

                cl=tk.Label(row,text=cls,font=(FONT(),7,"bold"),
                            bg=cbg,fg=clr,padx=5,pady=2,width=11)
                cl.pack(side="left")

                ab=btn(row,"+ Add",
                       lambda c=code,r=ref,p=penalty,cl=cls,s=current_sec:
                           self._add_charge(s,c,r,p,cl),
                       bg=INDIGO,hbg=INDIGO_H,fg=TEXT,fs=8,pady=4,padx=10)
                ab.pack(side="right",padx=8,pady=4)

                # Inject Code Note if it exists
                if code in CODE_NOTES:
                    note_frame = tk.Frame(row_wrap, bg=rb, padx=15, pady=0)
                    note_frame.pack(fill="x")
                    note_lbl = tk.Label(note_frame, text="↳ " + CODE_NOTES[code], 
                                        font=(FONT(), 8, "italic"), bg=rb, fg=MUTED, 
                                        anchor="w", justify="left", wraplength=750)
                    note_lbl.pack(anchor="w", pady=(0, 6))

                def _he(e,r=row): r.configure(bg=SEL)
                def _hl(e,r=row,b=rb): r.configure(bg=b)
                for ww in (row,badge,rl,pl,cl):
                    ww.bind("<Button-1>",lambda e,c=code,r=ref,p=penalty,cl=cls,s=current_sec:
                        self._add_charge(s,c,r,p,cl))
                    ww.bind("<Enter>",_he); ww.bind("<Leave>",_hl)
                row.bind("<Enter>",_he); row.bind("<Leave>",_hl)

        if not shown:
            tk.Label(self._code_f,text="No results match your search.",
                     bg=CARD,fg=MUTED,font=(FONT(),11),pady=24).pack()

    # ── Charge management ─────────────────────────────────────────────────────
    def _severity_counts(self):
        counts = {"Citation":0,"Misdemeanor":0,"Felony":0}
        for _,_,_,_,cls in self.charges:
            if cls in counts: counts[cls]+=1
        return counts

    def _add_charge(self,sec,code,ref,penalty,cls):
        self.charges.append((sec,code,ref,penalty,cls))
        self._refresh_queue()
        self._refresh_charge_summary()
        self._refresh_dynamic_phrases()

    def _remove_charge(self,i):
        if 0<=i<len(self.charges):
            self.charges.pop(i)
            self._refresh_queue()
            self._refresh_charge_summary()
            self._refresh_dynamic_phrases()

    def _clear(self):
        self.charges.clear()
        self._refresh_queue()
        self._refresh_charge_summary()
        self._refresh_dynamic_phrases()
        self._write(self._cit_out,"Cleared. Add charges and hit Generate.")
        self._last_cit=""

    def _get_sorted_charges(self):
        def sort_key(charge):
            code = charge[1]
            nums = [int(s) for s in re.findall(r'\d+', code)]
            return nums if nums else [999, 999]
        return sorted(self.charges, key=sort_key)

    def _refresh_queue(self):
        for w in self._q_f.winfo_children(): w.destroy()
        n=len(self.charges)
        self._cnt_var.set(f"{n} charge{'s' if n!=1 else ''}")
        counts = self._severity_counts()
        if hasattr(self,"_cit_chart"): self._cit_chart.set_counts(counts)
        if hasattr(self,"_arr_chart"): self._arr_chart.set_counts(counts)
        
        if not self.charges:
            tk.Label(self._q_f,text="No charges added yet.",
                     bg=CARD,fg=MUTED,font=(FONT(),9),pady=14).pack()
            self._tot_var.set("")
            return

        tm=0;tj=0;ti=False
        for _,_,_,p,_ in self.charges:
            m,j,ii=parse_penalty(p); tm+=m; tj+=j
            if ii: ti=True
        parts=[f"${tm:,}"] if tm else []
        if tj: parts.append(f"{tj}s jail")
        if ti: parts.append("Impound")
        self._tot_var.set("  ·  ".join(parts))

        sorted_charges = self._get_sorted_charges()
        for i, (_,code,ref,pen,cls) in enumerate(sorted_charges):
            clr=CLASS_COLOR.get(cls,TEXT)
            cbg=CLASS_BG.get(cls,MUTED2)
            row=tk.Frame(self._q_f,bg=CARD,pady=4)
            row.pack(fill="x",padx=6)
            tk.Label(row,text=code,font=("Courier New",8,"bold"),
                     bg=cbg,fg=clr,width=8,padx=3).pack(side="left",padx=(0,6))
            tk.Label(row,text=ref,font=(FONT(),8),bg=CARD,fg=TEXT2,
                     anchor="w").pack(side="left",fill="x",expand=True)
            rm=tk.Label(row,text="✕",font=(FONT(),9,"bold"),
                        bg=CARD,fg=RED,cursor="hand2")
            rm.pack(side="right",padx=4)

            original_idx = next(idx for idx, c in enumerate(self.charges) if c[1] == code and c[2] == ref)
            rm.bind("<Button-1>",lambda e,idx=original_idx:self._remove_charge(idx))

    # ── Generate functions ────────────────────────────────────────────────────
    def _at(self,s):
        if not s: return s
        return ", ".join("@"+p.strip().lstrip("@") for p in s.split(","))

    def _gen_citation(self):
        if not self.charges:
            messagebox.showwarning("No Charges","Add at least one charge first."); return
        prov=getv(self._f_prov) or "[Officer Name]"
        off =getv(self._f_off)  or "[Offender Name]"
        if not prov.startswith("@"): prov="@"+prov
        if not off.startswith("@"):  off="@"+off
        ct=[(c,r,p,cl) for _,c,r,p,cl in self._get_sorted_charges()]
        self._last_cit=(
            f"Ticket provider: {prov}\n"
            f"Sections: {', '.join(c for c,_,_,_ in ct)}\n"
            f"Reference: {', '.join(r for _,r,_,_ in ct)}\n"
            f"Penalty: {build_penalty(ct)}\n"
            f"Classification: {', '.join(cl for _,_,_,cl in ct)}\n"
            f"Count: {len(ct)}\n"
            f"Offender: {off}"
        )
        self._write(self._cit_out,self._last_cit)
        pyperclip.copy(self._last_cit)
        append_history("citation", self._last_cit)
        self._toast("Citation copied!")

    def _copy_cit(self):
        if not self._last_cit: self._gen_citation(); return
        pyperclip.copy(self._last_cit); self._toast("Copied!")

    def _gen_arrest(self):
        officers=self._at(getv(self._a_off)  or "[Officer(s)]")
        depts   =getv(self._a_dept)           or "[Department(s)]"
        suspects=self._at(getv(self._a_susp) or "[Suspect(s)]")
        if self.charges:
            ct=[(c,r,p,cl) for _,c,r,p,cl in self._get_sorted_charges()]
            codes=", ".join(c for c,_,_,_ in ct)
            refs =", ".join(r for _,r,_,_ in ct)
            clss =", ".join(cl for _,_,_,cl in ct)
            pen  =build_penalty(ct); count=len(ct)
        else:
            codes=refs=clss=pen="[No charges]"; count=0
        self._last_arr=(
            f"Involved Officer(s): {officers}\n"
            f"Department(s): {depts}\n"
            f"Suspect(s): {suspects}\n\n"
            f"----------\n\n"
            f"Penal Code Section: {codes}\n"
            f"Reference(s): {refs}\n"
            f"Penaltie(s): {pen}\n"
            f"Classification(s): {clss}\n"
            f"Count: {count}\n\n"
            f"----------\n\n"
            f"Vehicle Make: N/A\n"
            f"Vehicle Model: N/A\n"
            f"Vehicle Plate: N/A\n"
            f"Vehicle Official Registry: N/A\n\n"
            f"*Attached mugshot(s);*"
        )
        self._write(self._arr_out,self._last_arr)
        pyperclip.copy(self._last_arr)
        append_history("arrest", self._last_arr)
        self._toast("Arrest report copied!")

    def _copy_arr(self):
        if self._last_arr: pyperclip.copy(self._last_arr); self._toast("Copied!")

    def _gen_warrant(self):
        officers=self._at(getv(self._w_off)  or "[Officer(s)]")
        depts   =getv(self._w_dept)           or "[Department(s)]"
        suspects=self._at(getv(self._w_susp) or "[Suspect(s)]")
        if self.charges:
            ct=[(c,r,p,cl) for _,c,r,p,cl in self._get_sorted_charges()]
            codes=", ".join(c for c,_,_,_ in ct)
            refs =", ".join(r for _,r,_,_ in ct)
            clss =", ".join(cl for _,_,_,cl in ct)
            pen  =build_penalty(ct); count=len(ct)
        else:
            codes=refs=clss=pen="[No charges]"; count=0
        self._last_war=(
            f"Involved Officer(s): {officers}\n"
            f"Department(s): {depts}\n"
            f"Suspect(s): {suspects}\n\n"
            f"----------\n\n"
            f"Penal Code Section: {codes}\n"
            f"Reference(s): {refs}\n"
            f"Penaltie(s): {pen}\n"
            f"Classification(s): {clss}\n"
            f"Count: {count}\n\n"
            f"*Attached evidence(s);*"
        )
        self._write(self._war_out,self._last_war)
        pyperclip.copy(self._last_war)
        append_history("warrant", self._last_war)
        self._toast("Warrant request copied!")

    def _copy_war(self):
        if self._last_war: pyperclip.copy(self._last_war); self._toast("Copied!")

    # ── Utility ───────────────────────────────────────────────────────────────
    def _write(self,widget,text):
        widget.configure(state="normal")
        widget.delete("1.0","end")
        widget.insert("end",text)
        widget.configure(state="disabled")

    def _toast(self,msg):
        try:
            t=tk.Toplevel(self)
            t.overrideredirect(True)
            t.attributes("-topmost",True)
            try: t.attributes("-alpha", 0.0)
            except Exception: pass
            t.configure(bg="#071a0d")
            tk.Frame(t,bg=GREEN,height=2).pack(fill="x")
            tk.Label(t,text=f"  ✓  {msg}  ",
                     font=(FONT(),10,"bold"),bg="#071a0d",fg=GREEN,
                     pady=9,padx=6).pack()
            self.update_idletasks()
            x=self.winfo_x()+self.winfo_width()-300
            y=self.winfo_y()+self.winfo_height()-72
            t.geometry(f"+{x}+{y}")
            def fade_in(a=0.0):
                if not t.winfo_exists(): return
                a = min(1.0, a+0.15)
                try: t.attributes("-alpha", a)
                except Exception: pass
                if a < 1.0: t.after(15, lambda: fade_in(a))
            fade_in()
            def fade_out(a=1.0):
                if not t.winfo_exists(): return
                a = max(0.0, a-0.12)
                try: t.attributes("-alpha", a)
                except Exception: pass
                if a > 0.0: t.after(15, lambda: fade_out(a))
                else: t.destroy()
            t.after(1900, fade_out)
        except Exception: pass

App().mainloop()