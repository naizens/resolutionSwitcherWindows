import ctypes
import threading
import customtkinter as ctk
from tkinter import messagebox
import pystray
from pystray import MenuItem as item
from PIL import Image, ImageDraw
import json
import os


class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", ctypes.c_ulong),
        ("DeviceName", ctypes.c_wchar * 32),
        ("DeviceString", ctypes.c_wchar * 128),
        ("StateFlags", ctypes.c_ulong),
        ("DeviceID", ctypes.c_wchar * 128),
        ("DeviceKey", ctypes.c_wchar * 128)
    ]

class DEVMODE(ctypes.Structure):
    _fields_ = [
        ("dmDeviceName", ctypes.c_wchar * 32),
        ("dmSpecVersion", ctypes.c_ushort),
        ("dmDriverVersion", ctypes.c_ushort),
        ("dmSize", ctypes.c_ushort),
        ("dmDriverExtra", ctypes.c_ushort),
        ("dmFields", ctypes.c_ulong),
        ("dmPosition_x", ctypes.c_long),
        ("dmPosition_y", ctypes.c_long),
        ("dmDisplayOrientation", ctypes.c_ulong),
        ("dmDisplayFixedOutput", ctypes.c_ulong),
        ("dmColor", ctypes.c_short),
        ("dmDuplex", ctypes.c_short),
        ("dmYResolution", ctypes.c_short),
        ("dmTTOption", ctypes.c_short),
        ("dmCollate", ctypes.c_short),
        ("dmFormName", ctypes.c_wchar * 32),
        ("dmLogPixels", ctypes.c_ushort),
        ("dmBitsPerPel", ctypes.c_ulong),
        ("dmPelsWidth", ctypes.c_ulong),
        ("dmPelsHeight", ctypes.c_ulong),
        ("dmDisplayFlags", ctypes.c_ulong),
        ("dmDisplayFrequency", ctypes.c_ulong),
        ("dmICMMethod", ctypes.c_ulong),
        ("dmICMIntent", ctypes.c_ulong),
        ("dmMediaType", ctypes.c_ulong),
        ("dmDitherType", ctypes.c_ulong),
        ("dmReserved1", ctypes.c_ulong),
        ("dmReserved2", ctypes.c_ulong),
        ("dmPanningWidth", ctypes.c_ulong),
        ("dmPanningHeight", ctypes.c_ulong),
    ]

# ==================== FUNCTIONS ====================

RES_FILE = "monitor_resolutions.json"

def list_monitors():
    user32 = ctypes.windll.user32
    i = 0
    monitors = []
    while True:
        display = DISPLAY_DEVICE()
        display.cb = ctypes.sizeof(display)
        if not user32.EnumDisplayDevicesW(None, i, ctypes.byref(display), 0):
            break
        if display.StateFlags & 1:
            monitors.append(display.DeviceName)
        i += 1
    return monitors

def set_monitor_resolution(device_name, width, height, hz):
    user32 = ctypes.windll.user32
    dm = DEVMODE()
    dm.dmSize = ctypes.sizeof(DEVMODE)
    dm.dmPelsWidth = width
    dm.dmPelsHeight = height
    dm.dmDisplayFrequency = hz
    DM_PELSWIDTH = 0x80000
    DM_PELSHEIGHT = 0x100000
    DM_DISPLAYFREQUENCY = 0x400000
    dm.dmFields = DM_PELSWIDTH | DM_PELSHEIGHT | DM_DISPLAYFREQUENCY
    result = user32.ChangeDisplaySettingsExW(device_name, ctypes.byref(dm), None, 0, None)
    return result

def get_supported_resolutions(device_name):
    user32 = ctypes.windll.user32
    i = 0
    modes = set()
    devmode = DEVMODE()
    devmode.dmSize = ctypes.sizeof(DEVMODE)
    while user32.EnumDisplaySettingsW(device_name, i, ctypes.byref(devmode)):
        res = (devmode.dmPelsWidth, devmode.dmPelsHeight, devmode.dmDisplayFrequency)
        modes.add(res)
        i += 1
    return list(modes)


def save_resolutions(res_dict):
    with open(RES_FILE, "w") as f:
        json.dump(res_dict, f, indent=4)

def load_resolutions():
    if os.path.exists(RES_FILE):
        with open(RES_FILE, "r") as f:
            return json.load(f)
    return {}

def collect_resolutions():
    monitors = list_monitors()
    res_dict = {}
    for m in monitors:
        modes = get_supported_resolutions(m)
        modes = sorted({(w, h) for w, h, hz in modes}, key=lambda x: (x[0], x[1]), reverse=True)
        res_dict[m] = modes
    save_resolutions(res_dict)
    return res_dict


class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Monitor Tool")
        self.geometry("460x220")
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(6, weight=1)


        self.monitor_list = list_monitors()
        self.monitor_var = ctk.StringVar(value=self.monitor_list[0] if self.monitor_list else "")

        self.resolutions = load_resolutions()
        if not self.resolutions:
            self.resolutions = collect_resolutions()

        self.chooseMonitorLabel = ctk.CTkLabel(self, text="Monitor auswählen:")
        self.chooseMonitorLabel.grid(row=0, column=0, padx=0, pady=(5, 5), sticky="nsew")
        self.combo_monitor = ctk.CTkComboBox(
            self, values=self.monitor_list, variable=self.monitor_var, width=300,
            command=self.update_resolutions
        )
        self.combo_monitor.grid(row=0, column=1, padx=5, pady=(5, 5), sticky="nsew")

        self.chooseResLabel = ctk.CTkLabel(self, text="Auflösung:")
        self.chooseResLabel.grid(row=1, column=0, padx=0, pady=(5, 5), sticky="nsew")
        self.res_var = ctk.StringVar()
        self.combo_res = ctk.CTkComboBox(self, values=[], variable=self.res_var, width=300)
        self.combo_res.grid(row=1, column=1, padx=5, pady=(5, 5), sticky="nsew")

        self.chooseHzLabel = ctk.CTkLabel(self, text="Bildwiederholrate (Hz):")
        self.chooseHzLabel.grid(row=2, column=0, padx=0, pady=(5, 5), sticky="nsew")
        self.hz_var = ctk.StringVar()
        self.combo_hz = ctk.CTkComboBox(self, values=[], variable=self.hz_var, width=300)
        self.combo_hz.grid(row=2, column=1, padx=5, pady=(5, 5), sticky="nsew")

        self.applySingleButton = ctk.CTkButton(self, text="Apply Single", command=self.apply_single)
        self.applySingleButton.grid(row=3, column=1, padx=5, pady=(5, 5), sticky="nsew")
        
        self.updateResolutionsButton = ctk.CTkButton(self, text="Update Resolutions", fg_color="purple", hover_color="darkmagenta",command=self.update_all_resolutions)
        self.updateResolutionsButton.grid(row=3, column=0, padx=5, pady=(5, 5), sticky="nsew")
        
        self.spacer = ctk.CTkLabel(self, text="")
        self.spacer.grid(row=4, column=0, columnspan=2, pady = (0, 0))
        
        self.desktopModeButton = ctk.CTkButton(self, text="Desktop Mode (All Monitors)", command=self.apply_desktop_mode)
        self.desktopModeButton.grid(row=5, column=0, padx=5, pady=(0, 5), sticky="nsew")
        
        self.iracingModeButton = ctk.CTkButton(self, text="iRacing Mode (All Monitors)", command=self.apply_iracing_mode)
        self.iracingModeButton.grid(row=5, column=1, padx=5, pady=(0, 5), sticky="nsew")

        self.tray_icon = None

        self.protocol("WM_DELETE_WINDOW", self.on_close)
        
        self.update_resolutions(self.monitor_var.get())

    def update_all_resolutions(self):
        self.resolutions = collect_resolutions()  # neu abfragen und speichern
        self.update_resolutions(self.monitor_var.get())  # Combobox neu füllen
        messagebox.showinfo("Resolution Update", "All Monitor resolutions have been updated.")


    def update_resolutions(self, monitor_name):
        modes = self.resolutions.get(monitor_name, [])
        
        hz_set = sorted({hz for w, h, hz in get_supported_resolutions(monitor_name)}, reverse=True)

        res_str = [f"{w}x{h}" for w, h in modes]
        hz_str = [str(hz) for hz in hz_set]

        self.combo_res.configure(values=res_str)
        self.combo_hz.configure(values=hz_str)

        if res_str:
            self.res_var.set(res_str[0])
        if hz_str:
            self.hz_var.set(hz_str[0])

    def apply_single(self):
        monitor = self.monitor_var.get()
        try:
            w, h = self.res_var.get().split("x")
            w, h, hz = int(w), int(h), int(self.hz_var.get())
        except:
            messagebox.showerror("Error", "Invalid selection!")
            return

        result = set_monitor_resolution(monitor, w, h, hz)
        if result == 0:
            messagebox.showinfo("Success", f"Settings applied for:\n{monitor}")
        else:
            messagebox.showerror("Error", f"Windows error code: {result}")

    def apply_iracing_mode(self):
        width, height, hz = 1920, 1080, 165
        errors = []
        for monitor in self.monitor_list:
            result = set_monitor_resolution(monitor, width, height, hz)
            if result != 0:
                errors.append((monitor, result))
        if not errors:
            messagebox.showinfo("iRacing Mode", f"All monitors set to:\n{width}x{height} @ {hz} Hz")
        else:
            msg = "\n".join([f"{m}: Fehler {e}" for m, e in errors])
            messagebox.showerror("Fehler bei einigen Monitoren", msg)

    def apply_desktop_mode(self):
        width, height, hz = 2560, 1440, 165
        errors = []
        for monitor in self.monitor_list:
            result = set_monitor_resolution(monitor, width, height, hz)
            if result != 0:
                errors.append((monitor, result))
        if not errors:
            messagebox.showinfo("Desktop Mode", f"All monitors set to:\n{width}x{height} @ {hz} Hz")
        else:
            msg = "\n".join([f"{m}: Error {e}" for m, e in errors])
            messagebox.showerror("Error on some monitors", msg)

    def create_tray_icon(self):
        image = Image.new('RGB', (64, 64), color=(30, 144, 255))
        d = ImageDraw.Draw(image)
        d.text((10, 25), "M", fill="white")

        menu = (
            item("Desktop Mode 2560x1440 165Hz", lambda: self.apply_desktop_mode()),
            item("iRacing Mode 1920x1080 165Hz", lambda: self.apply_iracing_mode()),
            item("Open Window", lambda: self.show_window()),
            item("Exit", lambda: self.close_all())
        )

        self.tray_icon = pystray.Icon("monitor_tool", image, "Monitor Tool", menu,
                                      on_double_click=lambda icon, item: self.show_window())

    def start_tray(self):
        self.create_tray_icon()
        self.tray_icon.run()

    def hide_to_tray(self):
        self.withdraw()
        threading.Thread(target=self.start_tray, daemon=True).start()

    def show_window(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.deiconify()

    def close_all(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.destroy()

    def on_close(self):
        self.hide_to_tray()

if __name__ == "__main__":
    app = App()
    app.mainloop()
