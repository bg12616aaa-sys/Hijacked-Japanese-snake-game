import pygetwindow as gw
import win32gui
import win32con
import pyautogui
import time
import random
import re
import asyncio
import websockets
import subprocess

screen_width, screen_height = pyautogui.size()

orig_x, orig_y = 0, 0
orig_w, orig_h = 1000, 700  # Default layout dimensions fallback
has_stored_position = False
target_window = None
has_restored = False

async def ping_handler(websocket, path):
    try:
        async for message in websocket:
            await websocket.send("active")
    except websockets.exceptions.ConnectionClosed:
        pass

def minimize_via_vbs(window_title):
    """
    Creates a temporary VBScript to activate the browser window 
    and send the native 'Alt + Space, N' keystroke to minimize it cleanly.
    """
    vbs_code = f'''
    Set WshShell = WScript.CreateObject("WScript.Shell")
    If WshShell.AppActivate("{window_title}") Then
        WScript.Sleep 100
        WshShell.SendKeys "% "
        WScript.Sleep 50
        WshShell.SendKeys "n"
    End If
    '''
    try:
        # Execute VBScript directly from Python command line
        subprocess.run(["cscript", "//NoLogo", "//E:vbscript", "-"], input=vbs_code, text=True, capture_output=True)
        print("VBScript minimize command dispatched successfully.")
    except Exception as e:
        print(f"VBScript execution error: {e}")

async def window_control_loop():
    global target_window, has_stored_position, orig_x, orig_y, orig_w, orig_h, has_restored
    
    print("python.py environment engine live. Verifying local ports...")
    print("Awaiting 1st click event on the target browser interface...")

    # --- PHASE 1: VBSCRIPT FOCUS MINIMIZATION ---
    while True:
        all_titles = gw.getAllTitles()
        for title in all_titles:
            if "START_AND_MINIMIZE" in title:
                try:
                    target_window = gw.getWindowsWithTitle(title)[0]
                    hwnd = target_window._hWnd
                    
                    # Un-maximize the window to register clean coordinate tracking later
                    win32gui.ShowWindow(hwnd, win32con.SW_SHOWNORMAL)
                    await asyncio.sleep(0.05)
                    
                    # Capture regular browser size dimensions before minimizing
                    orig_w, orig_h = target_window.width, target_window.height
                    
                    # Trigger the programmatic keystroke minimize
                    minimize_via_vbs("START_AND_MINIMIZE")
                    break
                except Exception as e:
                    print(f"Hook issue: {e}")
        if target_window:
            break
        await asyncio.sleep(0.01)

    # --- PHASE 2: TRACK & OSCILLATE WINDOW FRAME ---
    while True:
        try:
            current_title = target_window.title
            hwnd = target_window._hWnd
            
            match = re.search(r'カウントダウン:\s*(\d+)', current_title)
            if match:
                current_count = int(match.group(1))
                
                # --- RESTORE AT 300 (Snap to Clean Center) ---
                if current_count <= 300 and not has_restored:
                    print("Milestone 300 hit! Restoring browser focus container window.")
                    
                    # Calculate center alignment parameters manually based on screen resolution
                    center_x = (screen_width // 2) - (orig_w // 2)
                    center_y = (screen_height // 2) - (orig_h // 2)
                    
                    # Store exact fixed target baseline positions
                    orig_x, orig_y = center_x, center_y
                    has_stored_position = True
                    has_restored = True
                    
                    # Wake up window and snap it into position
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    target_window.moveTo(center_x, center_y)
                    win32gui.SetForegroundWindow(hwnd)
                    await asyncio.sleep(0.05)
                
                # --- SNAP TO EXACT CENTER AT 0 ---
                if current_count == 0:
                    print("System complete. Aligning interface directly to screen orientation center.")
                    center_x = (screen_width // 2) - (target_window.width // 2)
                    center_y = (screen_height // 2) - (target_window.height // 2)
                    target_window.moveTo(center_x, center_y)
                    break 
                
                # --- CALCULATE SHAKE SCALE ---
                if current_count <= 50: shake_range = 35
                elif current_count <= 100: shake_range = 25
                elif current_count <= 150: shake_range = 18
                elif current_count <= 200: shake_range = 12
                elif current_count <= 250: shake_range = 7
                elif current_count <= 300: shake_range = 3
                else: shake_range = 0
                
                if shake_range > 0 and has_stored_position:
                    offset_x = random.randint(-shake_range, shake_range)
                    offset_y = random.randint(-shake_range, shake_range)
                    target_window.moveTo(orig_x + offset_x, orig_y + offset_y)
                    
        except Exception:
            pass
            
        await asyncio.sleep(0.01)

async def main():
    async with websockets.serve(ping_handler, "localhost", 8765):
        await window_control_loop()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nBackground loops terminated safely.")