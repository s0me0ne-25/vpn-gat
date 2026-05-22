#!/usr/bin/env python3

#######
## VPN Google Anti-Teleport (GAT)
##
## 0) Why?
##    Because fuck heuristic GeoIP, that's why.
##    THY SHALL OBEY WHAT WHOIS PROPHECIED
##
## 1) ADJUST FIRST for country of your VPN service (see config below)
##    - Dicts pre-shipped for Amsterdam and Paris
##
##    - If needed, use any top-grade LLM AI (Grok, Gemini, Claude etc.) to generate the
##      national dict you need, then feel free to contribute it to project github
##
##    - Enter your WAN IP to be cleaned up into the corresponding variable
##
##    - Measure the target city lat/lon rectangle using any online map and populate
##      the corresponding config vars
##
## 2) Run either in cron, or in infinite loop with delay
##    Recommended intervals:
##    - 2-5m for cleaning already misteleported IP
##    - 10-15m for clean IP to prevent further teleportation
##
## Vibecoded in Grok 4 by s0me0ne-25
##
## Non-Copyrighted: AI Work
## (Creative Commons CC0, if above is not
## applicable in your jurisdiction)
#######

import threading
import random
import time
import subprocess
import os
import json
import urllib.request
import websocket
from urllib.parse import quote
import argparse
import sys
from datetime import datetime

# ==================== CONFIGURATION ====================
QUERY_FILE = "queries.txt"                           ## Better compact with:
                                                     ##   ./minify-dict.sh full_dict_file > ./queries.txt
                                                     ## but full ones also work
                                                     
URL_TEMPLATE = "https://www.google.fr/search?q={}"   ## Use national google domain here if exists
DELAY_SECONDS = 40                                   ## Terminate the browser after XX sec
EXPECTED_WAN_IP = "YourExtIPHere"                    ## Populate yourself for your proxy
PROFILES_DIR = "/home/user/vpngat"
PROF_PER_SCREEN = 3
#LAT_MIN, LAT_MAX = 52.29, 52.42        ## Amsterdam NL
#LON_MIN, LON_MAX = 4.80, 4.99          ## Amsterdam NL
LAT_MIN, LAT_MAX = 48.78, 48.95        ## Paris FR
LON_MIN, LON_MAX = 2.21, 2.59          ## Paris FR

RESOLUTIONS = [
    (1280, 720),   # 16:9 HD
    (1366, 768),   # 16:9
    (1600, 900),   # 16:9
    (1920, 1080),  # 16:9 Full HD
    (1280, 960),   # 4:3
    (1400, 1050),  # 4:3
    (1024, 768),   # 4:3
    (1280, 1024)   # 4:3
]

# Change to "chromium-browser" if needed on your system
CHROMIUM_CMD = "chromium"

# ======================================================

def debug(*objects, sep=' ', end='\n', file=None, flush=False):
    timestamp = datetime.now().strftime('[%H:%M:%S] ')
    message = sep.join(str(obj) for obj in objects)
    print(timestamp + message, end=end, file=file, flush=flush)

class BackgroundScroller:
    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.stop_event = threading.Event()
        self.thread = None
        self.ws = None

    def _scroll_loop(self, delta_min: int, delta_max: int,
                     interval_min: float, interval_max: float):
        while not self.stop_event.is_set():
            delta_y = random.randint(delta_min, delta_max)

            try:
                cmd = {
                    "id": random.randint(10000, 999999),
                    "method": "Input.dispatchMouseEvent",
                    "params": {
                        "type": "mouseWheel",
                        "x": 800,          # safe center-ish position
                        "y": 700,
                        "deltaY": delta_y,
                        "deltaX": 0
                    }
                }
                self.ws.send(json.dumps(cmd))
                _ = self.ws.recv()     # consume response (important!)
                #debug(f"[Scroller] Sent mouseWheel deltaY={delta_y}")
            except Exception as e:
                debug(f"[BackgroundScroller] CDP send error: {e}")
                break

            sleep_time = random.uniform(interval_min, interval_max)
            time.sleep(sleep_time)

    def start(self,
              delta_min: int = 300,
              delta_max: int = 900,
              interval_min: float = 1.2,
              interval_max: float = 4.8):
        if self.thread and self.thread.is_alive():
            debug("BackgroundScroller is already running")
            return

        self.stop_event.clear()

        try:
            self.ws = websocket.create_connection(self.ws_url, timeout=10)
            #debug("BackgroundScroller: WebSocket connected successfully")
        except Exception as e:
            debug(f"Failed to connect to CDP websocket: {e}")
            return

        self.thread = threading.Thread(
            target=self._scroll_loop,
            args=(delta_min, delta_max, interval_min, interval_max),
            daemon=True
        )
        self.thread.start()

        debug(f"BackgroundScroller STARTED → delta {delta_min}-{delta_max}px, "
              f"interval {interval_min}-{interval_max}s")

    def stop(self):
        if not self.thread or not self.thread.is_alive():
            debug("BackgroundScroller is not running")
            return

        self.stop_event.set()
        if self.ws:
            try:
                self.ws.close()
            except:
                pass
        self.thread.join(timeout=3.0)
        debug("BackgroundScroller STOPPED")

def get_wsurl(target = None, max_retries: int = 8):
    time.sleep(2)   # Waiting for chromium to load

    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen("http://127.0.0.1:9222/json/list", timeout=10) as resp:
                targets = json.loads(resp.read())
            
            if not targets:
                raise Exception("No debug targets found")
            
            if target and type(target) is str:
                for t in targets:
                    if t.get("type") == target:
                        ws_url = t["webSocketDebuggerUrl"]
                        debug(f"Using PAGE target: {ws_url}")
                        return ws_url
            
            # 3. Last resort
            ws_url = targets[0]["webSocketDebuggerUrl"]
            debug(f"Using generic target: {ws_url}")
            return ws_url
            
        except Exception as e:
            debug(f"get_wsurl attempt {attempt+1}/{max_retries} failed: {e}")
            time.sleep(1.0)   # give Chromium time to register the page target
        
    raise Exception("Failed to get valid WebSocket URL after all retries")

def set_geolocation(ws_url):
    latitude  = round(random.uniform(LAT_MIN, LAT_MAX), 6)
    longitude = round(random.uniform(LON_MIN, LON_MAX), 6)
    accuracy  = random.randint(120, 300)
    
    try:
        ws = websocket.create_connection(ws_url, timeout=10)
        cmd = {
            "id": 1,
            "method": "Emulation.setGeolocationOverride",
            "params": {
                "latitude": latitude,
                "longitude": longitude,
                "accuracy": accuracy,
                "setGeolocationOverride": True
            }
        }
        
        ws.send(json.dumps(cmd))
        response = json.loads(ws.recv())
        ws.close()
        
        if "error" in response:
            debug(f"CDP error: {response['error']}")
        else:
            debug(f"CDP Geolocation set to {latitude} / {longitude} ±{accuracy}m")
            
    except Exception as e:
        debug(f"Failed to set geolocation via CDP: {e}")

def check_wan_ip(expected_ip: str):
    debug("Checking WAN IP via https://2ip.ru ...", end=' ')
    try:
        result = subprocess.run(
            ['curl', 'https://2ip.ru'],
            capture_output=True,
            text=True,
            check=True,
            timeout=15
        )
        ip = result.stdout.strip()
        
        if ip != expected_ip:
            print(f"ERROR: Got {ip}")
            sys.exit(1)
        else:
            print(f"PASS")
            
    except subprocess.CalledProcessError as e:
        debug(f"ERROR: curl command failed (exit code {e.returncode}): {e.stderr.strip()}")
        sys.exit(1)
    except subprocess.TimeoutExpired:
        debug("ERROR: curl timed out while checking WAN IP")
        sys.exit(1)
    except FileNotFoundError:
        debug("ERROR: 'curl' command not found. Is curl installed?")
        sys.exit(1)
    except Exception as e:
        debug(f"ERROR: Unexpected error during WAN IP check: {e}")
        sys.exit(1)

def parse_arguments():
    parser = argparse.ArgumentParser(
        description="Launch Chromium with a random query from queries.txt"
    )
    parser.add_argument(
        "--headless",
        nargs="?",
        const=True,
        default=False,
        help="Enable headless mode. "
             "Use --headless alone to run silently (no output). "
             "Use --headless=/path/to/screenshot.png to save a PNG screenshot."
    )
    parser.add_argument(
        "--syncmode",
        action="store_true",
        default=False,
        help="Run in synchronous blocking mode. "
             "Script waits until you manually close Chromium."
    )
    parser.add_argument(
        "--setup",
        nargs="?",
        const="list",
        default=None,
        help="Режим настройки. Без аргументов выводит список профилей. С номером - запускает профиль."
    )
    return parser.parse_args()

def load_queries(filename: str):
    queries = []
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    queries.append(line)
        return queries
    except FileNotFoundError:
        debug(f"Error: File '{filename}' not found.")
        return []
    except Exception as e:
        debug(f"Error reading file: {e}")
        return []

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)

    args = parse_arguments()
    
    # === НОВЫЙ БЛОК: Формируем список всех профилей ===
    all_profiles = []
    
    # Явная сортировка разрешений (сначала по ширине, затем по высоте) 
    # гарантирует строго фиксированный порядок нумерации при любых запусках
    for w, h in sorted(RESOLUTIONS, key=lambda x: (x[0], x[1])):
        for p_num in range(1, PROF_PER_SCREEN + 1):
            all_profiles.append((w, h, p_num))

    # Обработка команды --setup
    if args.setup is not None:
        args.syncmode = True  # Принудительно включаем syncmode
        if args.setup == "list":
            for idx, (w, h, p_num) in enumerate(all_profiles, 1):
                print(f"{idx}. {w}x{h} #{p_num}")
            sys.exit(0)
    # ==================================================
    
    # === ИЗМЕНЕННЫЙ БЛОК: Выбор профиля и URL ===
    
    if args.setup is None:
        # WAN IP check runs BEFORE everything else
        check_wan_ip(EXPECTED_WAN_IP)
    
        queries = load_queries(QUERY_FILE)
        if not queries:
            debug("No valid queries found in queries.txt")
            return

        width, height = random.choice(RESOLUTIONS)
        profile_num = random.randint(1, PROF_PER_SCREEN)

        query = random.choice(queries)
        debug(f"Selected query: {query}")     
        encoded_query = quote(query)
        url = URL_TEMPLATE.format(encoded_query)
    else:
        try:
            prof_idx = int(args.setup) - 1
            if prof_idx < 0 or prof_idx >= len(all_profiles):
                raise ValueError
            width, height, profile_num = all_profiles[prof_idx]
            debug(f"Setup mode: выбран профиль {args.setup} ({width}x{height} #{profile_num})")
        except ValueError:
            print(f"ERROR: Неверный номер профиля. Укажите число от 1 до {len(all_profiles)}.")
            sys.exit(1)
            
        url = "about:blank"  # В режиме setup не открываем URL_TEMPLATE
    # ==============================================

    debug(f"Using viewport size: {width}x{height}", end=' ')

    # Choose random profile for this resolution (1..PROF_PER_SCREEN)
    profile_num = random.randint(1, PROF_PER_SCREEN)
    #profile_num = 1
    profile_path = os.path.join(PROFILES_DIR, f"{width}x{height}", str(profile_num))
    os.makedirs(profile_path, exist_ok=True)
    print(f"profile: {profile_num}")

    # Base Chromium flags (common to both modes)
    cmd = [
        CHROMIUM_CMD,
        f"--user-data-dir={profile_path}",
        f"--window-size={width},{height}",
        "--no-first-run",
        #"--disable-infobars",
        #"--disable-extensions",
        "--disable-translate",
        "--disable-notifications",
        #"--disable-features=TranslateUI,Infobars",
        "--disable-backing-store-limit",
        #"--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        #"--no-sandbox",
        "--remote-debugging-port=9222",
        "--remote-allow-origins=*",   # needed on newer Chromium versions
    ]

    if args.headless:
        debug("Running in HEADLESS mode")
        cmd.append("--headless=new")       # Modern headless mode (Chrome 109+)
        cmd.append("--disable-gpu")
        
        if isinstance(args.headless, str):  # --headless=/path/to/screenshot.png
            screenshot_path = args.headless
            cmd.append(f"--screenshot={screenshot_path}")
            debug(f"Screenshot will be saved to: {screenshot_path}")
        else:
            debug("No screenshot – visual output discarded")
        
        # In headless mode we pass the URL directly (no --app needed)
        cmd.append(url)
        
        # No X11 environment needed
        env = os.environ.copy()
        # Explicitly remove DISPLAY so it truly runs X-less
        env.pop("DISPLAY", None)
        
    else:
        # GUI mode (original behavior)
        debug("Running in GUI mode on DISPLAY=:0")
        #cmd.append("--app=" + url)         # Minimal window decoration
        cmd.append(url)                     # Standard window
        cmd.append("--window-position=0,0")
        
        env = os.environ.copy()
        env["DISPLAY"] = ":0"

        debug(f"Launching Chromium with URL: {url}")
    
    try:
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )
        
        set_geolocation(get_wsurl())
        
        # Запускаем скроллер только если НЕ в режиме setup
        if args.setup is None:
            scroller = BackgroundScroller(get_wsurl("page"))
            scroller.start(
                delta_min=100,
                delta_max=250,
                interval_min=0.7,
                interval_max=2.5
            )
        if args.syncmode:
            debug("SYNC MODE enabled — Chromium stays open until you close it manually.")
            process.wait()                    # block until user closes the window
            debug("Chromium was closed by the user.")
        else:
            debug(f"Waiting {DELAY_SECONDS} seconds for page to load...")
            time.sleep(DELAY_SECONDS)
            
            # Force kill with SIGKILL (-9)
            #debug("Sending SIGKILL to Chromium...")
            process.kill()
            debug("Chromium terminated.")
        
    except FileNotFoundError:
        debug(f"Error: '{CHROMIUM_CMD}' command not found. Is Chromium installed?")
    except Exception as e:
        debug(f"Error: {e}")

    try:
        scroller.stop()
    except NameError:
        pass
    
if __name__ == "__main__":
    main()
