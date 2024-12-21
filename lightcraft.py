#LightCraft Source Code
#Made by Akash Samanta
#Version 2.8.8

import platform
import asyncio, _thread, os, time, webbrowser, re, subprocess, keyboard, threading, pygame
from moviepy import VideoFileClip
from bleak import BleakClient
from PIL import Image
from customtkinter import * # type: ignore
import tkinter as tk
import tkinter.messagebox as messagebox
from CTkColorPicker import * # type: ignore

from functools import wraps
from lightcraft_cli import repeat, enableRepeat, disableRepeat
from mutagen.mp3 import MP3

root = CTk()
if os.name == 'posix':
    default_address = "EC4A4BDB-FC15-8CC5-FAB1-9EB6181DE9A5"
else:
    default_address = "32:06:C2:00:0A:9E"
char_uuid = "FFD9"
isConnected = False
isOn = False
interval = 5
isFlashing = False
isPulsing = True
linkColour = "white"
isPlaying = False
isLinked = False
isLoaded = False
seekAmount = 0.5
isRepeating = False
repeatCmds, repeatCmdsChild = [],[]
defaultColour = "red"

#Custom Configuration
trailing_flash = leading_flash = trailing_pulse = leading_pulse = trailing_on = leading_on = trailing_off = leading_off =  main_on = main_off = 0
trailing_single = leading_single = order_single = []

validColours = {
    'red': [255, 0, 0],
    'orange': [204, 51, 0],
    'yellow': [153, 102, 0],
    'brown': [153, 153, 0],
    'gold': [204, 204, 0],
    'green': [0, 255, 0],
    'olive': [75, 128, 0],
    'lime': [0, 128, 75],    
    'coral': [0, 128, 128],
    'cyan': [0, 238, 238],
    'blue': [0, 0, 255],
    'teal': [0, 75, 128],
    'indigo': [75, 0, 128],
    'purple': [128, 0, 128],
    'violet': [238, 0, 238],
    'black': [0, 0, 0],
    'white': [255, 255, 255],
    'pink': [255, 0, 40],
    'navy': [255, 0, 128],
    'maroon': [255, 0, 204],
}

validFlashCode = {
    'rgb_flash': 0x62,
    'all_flash': 0x38,
    'white_flash': 0x37,
    'purple_flash': 0x36,
    'cyan_flash': 0x35,
    'yellow_flash': 0x34,
    'blue_flash': 0x33,
    'green_flash': 0x32,
    'red_flash': 0x31,
    'eyesore_flash': 0x30
}

validPulseCode = {
    'gb_pulse': 0x2F,
    'rb_pulse': 0x2E,
    'rg_pulse': 0x2D,
    'white_pulse': 0x2C,
    'purple_pulse': 0x2B,
    'cyan_pulse': 0x2A,
    'yellow_pulse': 0x29,
    'blue_pulse': 0x28,
    'green_pulse': 0x27,
    'red_pulse': 0x26,
    'rgb_pulse': 0x61,
    'all_pulse': 0x25
}

colourToRGB = {
    'red': (255,0,0),
    'green': (0,255,0),
    'blue': (0,0,255),
    'white': (255,255,255)
}

class BluetoothController:
    def __init__(self, address, char_uuid):
        self.address = address
        self.char_uuid = char_uuid
        self.client = None
        self.loop = asyncio.new_event_loop()
        self.connected = False
        asyncio.set_event_loop(self.loop)

    async def connect(self):
        self.client = BleakClient(self.address)
        try:
            await self.client.connect()
            self.connected = True
        except Exception as e:
            print(f"Failed to connect: {e}")
            self.connected = False

    def stop(self):
        if self.loop.is_running():
            self.loop.call_soon_threadsafe(self.loop.stop)

        def close_loop():
            if not self.loop.is_running():
                self.loop.close()

        self.loop.call_soon_threadsafe(close_loop)

    async def disconnect(self):
        if self.client:
            await self.client.disconnect()
            self.client = None

    async def sendCmd(self, data):
        if self.client:
            await self.client.write_gatt_char(self.char_uuid, data)

    def run_coroutine(self, coro):
        return asyncio.run_coroutine_threadsafe(coro, self.loop)

def main():
    global controller, loop_thread
    pygame.init()
    def debounce(wait):
        def decorator(fn):
            last_call = [0]

            @wraps(fn)
            def debounced(*args, **kwargs):
                now = time.time()
                if now - last_call[0] >= wait:
                    last_call[0] = now # type: ignore
                    return fn(*args, **kwargs)
            return debounced
        return decorator
    
    #Connection Functions
    def connect():
        global isConnected
        if isConnected:
            isConnected = False
            link_button.configure(state="disabled",fg_color=("#2b6b8f","#0f4d67"),hover_color=("#2b6b8f","#0f4d67"))
            connect_button.configure(image=None,text="Connect", state="normal",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            radio_button_1.configure(state="disabled")
            radio_button_2.configure(state="disabled")
            radio_button_3.configure(state="disabled")
            radio_button_4.configure(state="disabled")
            alertButton.configure(state="disabled")
            alertText.configure(text="Please connect your LED Strips first")
            macInput.configure(state="normal")
            macInputButton.configure(state="normal")
            uuidInput.configure(state="normal")
            uuidInputButton.configure(state="normal")
            resetButton.configure(state="normal")
            disconnect()
        else:
            future = controller.run_coroutine(controller.connect())
            connect_button.configure(image=None,text="Connecting", state="disabled",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            macInput.configure(state="disabled")
            macInputButton.configure(state="disabled")
            uuidInput.configure(state="disabled")
            uuidInputButton.configure(state="disabled")
            resetButton.configure(state="disabled")
            root.after(20, lambda: check_connection(future))

    def check_connection(future):
        global isConnected
        if future.done():
            if controller.connected:
                isConnected = True
                connect_button.configure(image=imgtk_bluetooth,text="Connected", fg_color="green", hover_color="#005500", state="normal")
                if isLoaded:
                    link_button.configure(state="normal",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
                if settings[4][:-1] == "1":
                    togglePower()
                radio_button_1.configure(state="normal")
                radio_button_2.configure(state="normal")
                radio_button_3.configure(state="normal")
                radio_button_4.configure(state="normal")
                alertButton.configure(state="normal")
                alertText.configure(text="This feature mimics real-life sounds. Use at your own risk.")
                macInput.configure(state="disabled")
                macInputButton.configure(state="disabled")
                uuidInput.configure(state="disabled")
                uuidInputButton.configure(state="disabled")
                resetButton.configure(state="disabled")
            else:
                connect_button.configure(image=None,text="Reconnect", fg_color="#AA0000", hover_color="#880000", state="normal")
                messagebox.showerror("Connection Failure", "LightCraft failed to connect with your LED Strips. Please make sure that your Bluetooth is turned on and that your LED Strips are not bonded with another device. Verify the MAC Address in Settings.")
                macInput.configure(state="normal")
                macInputButton.configure(state="normal")
                uuidInput.configure(state="normal")
                uuidInputButton.configure(state="normal")
                resetButton.configure(state="normal")
        else:
            root.after(20, lambda: check_connection(future))

    def disconnect():
        controller.run_coroutine(controller.disconnect())

    def togglePower():
        global isOn
        if not isOn:
            isOn = True
            power_button.configure(image=imgtk2)
            data = bytearray([trailing_on,main_on,leading_on])
        else:
            isOn = False
            power_button.configure(image=imgtk3)
            data = bytearray([trailing_off,main_off,leading_off])
        controller.run_coroutine(controller.sendCmd(data))

    #Commands
    def swapPulseFlash():
        global isPulsing, isFlashing
        if isPulsing:
            isPulsing = False
            isFlashing = True
            pulseflash_var.set(pulseflash_var.get().replace("pulse","flash"))
        else:
            isPulsing = True
            isFlashing = False
            pulseflash_var.set(pulseflash_var.get().replace("flash","pulse"))

    def sliderColourFun(sliderColour):
        if sliderColour in ["all","rgb"]:
            sliderColour = "white"
        intervalSlider.configure(progress_color=sliderColour)
        colorpicker.slider.configure(progress_color=sliderColour)
        colorpicker.label.configure(fg_color=sliderColour)

    def setBrightness(isUp):
        curr_value = colorpicker.slider.get()
        if isUp:
            new_value = curr_value + 10
            if new_value > 255:
                new_value = 255
        else:
            new_value = curr_value - 10
            if new_value < 0:
                new_value = 0
        colorpicker.slider.set(new_value)
        colorpicker.update_colors()
        sendHex(colorpicker.label.cget("text"))
    
    def setInterval(isUp):
        curr_value = intervalSlider.get()
        if isUp:
            new_value = curr_value + 1
            if new_value > 10:
                new_value = 10
        else:
            new_value = curr_value - 1
            if new_value < 0:
                new_value = 0
        intervalSlider.set(new_value)
        updateInterval()

    @debounce(0.1)
    def sendHex(data):
        global trailing_single, leading_single, order_single
        intervalSlider.configure(progress_color=data)
        data = data[1:]
        r = int(data[0:2], 16)
        g = int(data[2:4], 16)
        b = int(data[4:6], 16)
        color_map = {'r': r, 'g': g, 'b': b}
        rearranged_values = [color_map[color.lower()] for color in order_single]
        data = bytearray(trailing_single + rearranged_values + leading_single)
        controller.run_coroutine(controller.sendCmd(data))
    
    def sendHexMusic(data):
        data = data[1:]
        data = bytearray([0x56, int(data[0:2], 16), int(data[2:4], 16), int(data[4:6], 16), 0x00, 0xf0, 0xaa])
        controller.run_coroutine(controller.sendCmd(data))

    def sendColourMusic(data):
        hex_value = '#{:02x}{:02x}{:02x}'.format(*validColours[data])
        sendHexMusic(hex_value)
    
    @debounce(1)
    def sendRepeatMusic(data,times):
        global isRepeating, threadRepeat
        isRepeating = True
        start = int(data.split("-")[0])-1
        end = int(data.split("-")[1])-1
        threadRepeat = _thread.start_new_thread(sendRepeatMusicThread, (start, end, int(times)))
    
    def sendRepeatMusicThread(start, end, times):
        global isRepeating, cmds
        c = start
        f = 0
        while isRepeating:
            if c+1 <= end:
                delay = (int(data[c+1].split(",")[1])-int(data[c].split(",")[1]))/1000
            else:
                c = start
                f += 1
                if f == times:
                    isRepeating = False
                    break
                else:
                    continue
            cmd = cmds[c]
            func_name, args_str = cmd[:-1].split('(')
            args = args_str.split('.') if args_str else []
            command_functions[func_name](*args)
            time.sleep(delay)
            c += 1

    @debounce(0.1)
    def sendColourCB(button,index):
        global settings
        if keyboard.is_pressed("shift"):
            button.configure(fg_color="#FFFFFF")
            colorpicker.slider.configure(progress_color="#FFFFFF")
            colorpicker.label.configure(text="#FFFFFF",fg_color="#FFFFFF")
            sendHex("#FFFFFF")
            settings[index] = "#FFFFFF\n"
            writesettings()
        else:
            if colorpicker.dragging == True:
                colorpicker.dragging = False
                button.configure(fg_color=colorpicker.label.cget("text"))
                sendHex(colorpicker.label.cget("text"))
                settings[index] = colorpicker.label.cget("text") + "\n"
                writesettings()
            else:
                colorpicker.slider.configure(progress_color=settings[index][:-1])
                colorpicker.label.configure(text=settings[index][:-1],fg_color=settings[index][:-1])
                sendHex(settings[index][:-1])
    
    @debounce(0.1)
    def sendColourWB(r,g,b):
        global linkColour
        if (r==255 and g==255 and b==255):
            linkColour = "white"
        elif (r==255 and g==0 and b==0):
            linkColour = "red"
        elif (r==0 and g==255 and b==0):    
            linkColour = "green"
        elif (r==0 and g==0 and b==255):
            linkColour = "blue"
        else:
            linkColour = "unset"
        if linkColour!="unset":
            if isPulsing:
                pulseflash_var.set(linkColour+"_pulse")
            if isFlashing:
                pulseflash_var.set(linkColour+"_flash")
        colorpicker.update_colors(r,g,b)
        sendHex(colorpicker.label.cget("text"))

    @debounce(0.1)
    def sendPulse(isSet=False):
        global isPulsing, isFlashing, linkColour
        isPulsing = True
        isFlashing = False
        if isSet==False:
            data = bytearray([trailing_pulse,validPulseCode[pulseflash_var.get()],int(interval),leading_pulse])
            linkColour = "unset"
            sliderColourFun(pulseflash_var.get().split("_")[0]) 
        else:
            data = bytearray([trailing_pulse,validPulseCode[linkColour+"_pulse"],int(interval),leading_pulse])
        controller.run_coroutine(controller.sendCmd(data))

    def sendPulseMusic(colour, freq):
        if colour == "rainbow":
            colour = "all"
        elif colour == "primary":
            colour = "rgb"
        elif colour == "red blue":
            colour = "rb"
        elif colour == "green blue":
            colour = "gb"
        elif colour == "red green":
            colour = "rg"
        data = bytearray([trailing_pulse,validPulseCode[colour+"_pulse"],10-int(freq),leading_pulse])
        controller.run_coroutine(controller.sendCmd(data))

    @debounce(0.1)
    def sendFlash(isSet=False):
        global isPulsing, isFlashing, linkColour
        isPulsing = False
        isFlashing = True
        if isSet==False:
            data = bytearray([trailing_flash,validFlashCode[pulseflash_var.get()],int(interval),leading_flash])
            linkColour = "unset"
            sliderColourFun(pulseflash_var.get().split("_")[0])
        else:
            data = bytearray([trailing_flash,validFlashCode[linkColour+"_flash"],int(interval),leading_flash])
        controller.run_coroutine(controller.sendCmd(data))

    def sendFlashMusic(colour, freq):
        if colour == "rainbow":
            colour = "all"
        elif colour == "primary":
            colour = "rgb"
        data = bytearray([trailing_flash,validFlashCode[colour+"_flash"],10-int(freq),leading_flash])
        controller.run_coroutine(controller.sendCmd(data))

    @debounce(0.1)
    def updateInterval():
        global interval
        interval = 10 - intervalSlider.get()
        if isPulsing:
            sendPulse(linkColour!="unset")
        if isFlashing:
            sendFlash(linkColour!="unset")
    
    def sgButton(frame,row,col,colour):
        global customColour1, customColour2, customColour3, customColour4, customColour5
        r, g, b = map(int, validColours[colour])
        if col == 4:
            match row:
                case 0:
                    customColour1 = CTkButton(frame,text="", fg_color=settings[7][:-1], hover=False, font=CTkFont(size=bsize), width=sgwidth, corner_radius=sgradius, height=sgheight, command=lambda: sendColourCB(customColour1,7))
                    customColour1.grid(row=row,column=col,padx=(10,0),pady=(10,0))
                case 1:
                    customColour2 = CTkButton(frame,text="", fg_color=settings[8][:-1], hover=False, font=CTkFont(size=bsize), width=sgwidth, corner_radius=sgradius, height=sgheight, command=lambda: sendColourCB(customColour2,8))
                    customColour2.grid(row=row,column=col,padx=(10,0),pady=(10,0))
                case 2:
                    customColour3 = CTkButton(frame,text="", fg_color=settings[9][:-1], hover=False, font=CTkFont(size=bsize), width=sgwidth, corner_radius=sgradius, height=sgheight, command=lambda: sendColourCB(customColour3,9))
                    customColour3.grid(row=row,column=col,padx=(10,0),pady=(10,0))
                case 3:
                    customColour4 = CTkButton(frame,text="", fg_color=settings[10][:-1], hover=False, font=CTkFont(size=bsize), width=sgwidth, corner_radius=sgradius, height=sgheight, command=lambda: sendColourCB(customColour4,10))
                    customColour4.grid(row=row,column=col,padx=(10,0),pady=(10,0))
                case 4:
                    customColour5 = CTkButton(frame,text="", fg_color=settings[11][:-1], hover=False, font=CTkFont(size=bsize), width=sgwidth, corner_radius=sgradius, height=sgheight, command=lambda: sendColourCB(customColour5,11))
                    customColour5.grid(row=row,column=col,padx=(10,0),pady=(10,0))
        else:
            CTkButton(frame,text="", fg_color="#{:02x}{:02x}{:02x}".format(r, g, b), hover=False, font=CTkFont(size=bsize), width=sgwidth, corner_radius=sgradius, height=sgheight, command=lambda: sendColourWB(r,g,b)).grid(row=row,column=col,padx=(10,0),pady=(10,0))

    #Settings Functions
    def macInputSave():
        global settings, address
        address = macInputVar.get()
        if os.name == 'posix' and platform.system() == 'Darwin':
            settings[2] = macInputVar.get() + "\n"
            writesettings()
            recreate_controller()
            macInputButton.configure(state="disabled", text="Saved", fg_color="green")
            macInputButton.after(1000, lambda: macInputButton.configure(state="normal", text="Save", fg_color="#1f6aa5"))
        elif validate_mac_address(macInputVar.get()):
            settings[2] = macInputVar.get() + "\n"
            writesettings()
            recreate_controller()
            macInputButton.configure(state="disabled", text="Saved", fg_color="green")
            macInputButton.after(1000, lambda: macInputButton.configure(state="normal", text="Save", fg_color="#1f6aa5"))
        else:
            messagebox.showerror("Invalid MAC Address", "Please enter a valid MAC address.")

    def validate_mac_address(mac_address):
        # MAC address format: XX:XX:XX:XX:XX:XX
        mac_regex = r'^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$'
        if re.match(mac_regex, mac_address):
            return True
        else:
            return False

    def uuidInputSave():
        global settings, char_uuid
        char_uuid = uuidInputVar.get()
        if len(uuidInputVar.get()) == 4:
            settings[3] = uuidInputVar.get() + "\n"
            writesettings()
            recreate_controller()
            uuidInputButton.configure(state="disabled", text="Saved", fg_color="green")
            uuidInputButton.after(1000, lambda: uuidInputButton.configure(state="normal", text="Save", fg_color="#1f6aa5"))
        else:
            messagebox.showerror("Invalid UUID", "Please enter a UUID with exactly 4 characters.")

    def start_event_loop(controller):
        asyncio.set_event_loop(controller.loop)
        controller.loop.run_forever()

    def recreate_controller():
        global controller, loop_thread,address, char_uuid
        # Stop the previous controller and thread, if they exist
        if 'controller' in globals() and controller is not None:
            controller.stop()
            if loop_thread.is_alive():
                loop_thread.join()
        # Start the new controller
        controller = BluetoothController(address, char_uuid)
        loop_thread = threading.Thread(target=start_event_loop, args=(controller,))
        loop_thread.start()

    def toggleAutoCS():
        global settings
        settings[4] = str(autoCSVar.get()) + "\n"
        writesettings()

    def toggleKeyBind():
        global settings
        settings[5] = str(keyBindVar.get()) + "\n"
        if keyBindVar.get()==0:
            unbindAll()
        else:
            updateTab()
        writesettings()

    def toggleLoaded():
        global settings
        if loadedVar.get()==0:
            settings[12] = "Save\n"
        settings[6] = str(loadedVar.get()) + "\n"
        writesettings()

    def toggleTheme():
        global settings
        settings[14] = str(darkModeVar.get()) + "\n"
        messagebox.showinfo("Theme Change","The theme will change after you restart LightCraft.")
        writesettings()

    def showMusic():
        config_dir = os.path.join(os.getcwd(), "Configurations")
        if not os.path.exists(config_dir):
            os.makedirs(config_dir)
        if os.name == 'nt':
            os.startfile(config_dir)
        elif os.name == 'posix':
            subprocess.Popen(['open', config_dir])
        else:
            messagebox.showerror("Unsupported OS", "This feature is not supported on your operating system.")    
    def updateDefaultColour(value):
        global defaultColour
        defaultColour = defaultColourVar.get().lower()
        settings[15] = defaultColourVar.get() + "\n"
        writesettings()
        if isConnected:
            sendColourMusic(defaultColour)

    def openManual():
        webbrowser.open(r"www.github.com/akashcraft/LED-Controller/wiki")
    
    def openSettings():
        if os.path.exists("Settings.txt"):
            if os.name == 'nt':
                subprocess.Popen(["Settings.txt"], shell=True)
            elif os.name == 'posix':
                subprocess.Popen(['open', 'Settings.txt'])
            else:
                messagebox.showerror("Unsupported OS", "This feature is not supported on your operating system.")
        else:
            messagebox.showerror("Unable to Load Configuration", "The settings file seems to be missing. LightCraft will attempt to restore default settings.")

    #Alert Functions
    def playAlert():
        global interval
        if not isOn:
            togglePower()
        enableRepeat()
        alert = alert_var.get()
        pulseflash_var.set("red_pulse")
        match alert:
            case 0:
                pygame.mixer.music.load(r"./Resources/italyAlert.mp3")
                loop_thread1 = threading.Thread(target=lambda: asyncio.run(repeat(controller.client, char_uuid, '["0.3 red","0.3 pink"]', 100)))
                loop_thread1.start()
            case 1:
                pygame.mixer.music.load(r"./Resources/japanAlert.mp3")
                interval = 0
                sendPulse()
            case 2:
                pygame.mixer.music.load(r"./Resources/franceAlert.mp3")
                interval = 1
                sendPulse()
            case 3:
                pygame.mixer.music.load(r"./Resources/usaAlert.mp3")
                interval = 6
                sendPulse()
        intervalSlider.set(10-interval)
        pygame.mixer.music.play()
        alertButton.configure(text="Stop Alert", fg_color="#AA0000", hover_color="#880000", command=stopAlert)

    def stopAlert():
        pygame.mixer.music.stop()
        pygame.mixer.music.unload()
        disableRepeat()
        sendColourMusic(defaultColour)
        alertButton.configure(text="Play Alert",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"), command=playAlert)

    #Music Functions
    def get_vlength(video_path):
        with VideoFileClip(video_path) as video:
            duration = video.duration
        return duration

    def extract_av(video_path, audio_path):
        video = VideoFileClip(video_path)
        audio = video.audio
        if audio is not None:
            audio.write_audiofile(audio_path)

    def clearload():
        global repeatCmdsChild, repeatCmds, prohibited_times
        repeatCmds, repeatCmdsChild, prohibited_times = [],[],[]
        load_button.configure(fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
        heading3.configure(text="No Media Loaded")
        if (isLinked and isConnected):
            link_button.configure(fg_color="green", hover_color="#005500")
        elif isConnected:
            link_button.configure(fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
        else:
            link_button.configure(state="disabled",fg_color=("#2b6b8f","#0f4d67"))
        play_button.configure(state="disabled",fg_color=("#2b6b8f","#0f4d67"))
        add_button.configure(state="disabled",fg_color=("#2b6b8f","#0f4d67"))
        seek_button.configure(state="disabled",fg_color=("#2b6b8f","#0f4d67"))
        stop_button.configure(state="disabled",fg_color=("#2b6b8f","#0f4d67"))
        music_slider.set(0)
        music_slider.configure(state="disabled")
        total_time.configure(text="00:00.0")
        actual_time.configure(text="00:00.0")
        musicframechild.grid_forget()

    def load(autoload=False):
        global isLoaded, music_length, position, config_file_path, data, music, next_index, last_pos, isVideo
        if isLoaded and isPlaying:
            stop()
            pygame.mixer.music.unload()
        if not autoload:
            music = filedialog.askopenfilename(filetypes=[("Media Files", "*.mp3 *.mp4")])
            if music == "":
                isLoaded = False
                return
            else:
                clearload()
        else:
            music = settings[12][:-1]
        for child in musicframechild.grid_slaves():
            child.grid_remove()
        musicframe.event_generate("<MouseWheel>", delta=1000*120)
        try:
            #Load Successful
            config_dir = os.path.join(os.getcwd(), "Configurations")
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
            
            music_name = os.path.basename(music).split(".")[0]
            config_file_path = os.path.join(config_dir, f"{music_name} LightCraft.txt")
            if not os.path.exists(config_file_path):
                fobj = open(config_file_path, "w")
                fobj.close()
            fobj = open(config_file_path, "r")
            data = fobj.readlines()
            fobj.close()

            #Config Load Successful
            isLoaded = True
            musicframechild.grid(row=0,column=0,padx=0,pady=0, sticky='nsew')
            video = music
            if music.endswith(".mp3"):
                audio = MP3(music)
                music_length = audio.info.length
                isVideo = False
            elif music.endswith(".mp4"):
                music_length = get_vlength(music)
                isVideo = True
                try:
                    if not os.path.exists(os.path.join(config_dir, f"{music_name} LightCraft.mp3")):
                        messagebox.showinfo("Extracting Audio","LightCraft needs to extract the audio from the selected video. This may take a few seconds.")
                        extract_av(music, os.path.join(config_dir, f"{music_name} LightCraft.mp3"))
                except:
                    messagebox.showerror("Unable to Extract Audio","LightCraft was unable to extract the audio from the selected video. Please make sure that the file is not corrupted and that it is a valid video file. Try a different video and if the problem persists, please contact the developer.")
                    clearload()
                    isLoaded = False
                    return
                music = os.path.join(config_dir, f"{music_name} LightCraft.mp3")
            else:
                music_length = 0
            loadConfig()
            load_button.configure(fg_color="green", hover_color="#005500")
            heading3.configure(text=music_name)
            music_slider.configure(state="normal",to=int(music_length*1000))
            play_button.configure(state="normal",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            add_button.configure(state="normal",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            seek_button.configure(state="normal", text=str(seekAmount).rstrip('0').rstrip('.') + "s",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            stop_button.configure(state="normal",fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            total_time.configure(text=time.strftime("%M:%S", time.gmtime(music_length))+"."+format_ms(int(music_length*1000)))
            pygame.mixer.music.load(music)
            pygame.mixer.music.play()
            pygame.mixer.music.pause()
            last_pos = 0
            position = 0
            next_index = 0
            if settings[6][:-1] == "1":
                if isVideo:
                    settings[12] = video + "\n"
                else:
                    settings[12] = music + "\n"
                writesettings()    
        except:
            #Load Failed
            clearload()
            isLoaded = False
            messagebox.showerror("Unable to Load Media","LightCraft was unable to load the selected media. Please make sure that the file is not corrupted and that it is a valid media file. Delete any corrupted configuration file. Try a different media and if the problem persists, please contact the developer.")

    command_functions = {'sendColourMusic': sendColourMusic,'sendFlashMusic': sendFlashMusic,'sendPulseMusic': sendPulseMusic,'sendHexMusic': sendHexMusic,'sendRepeatMusic':sendRepeatMusic}

    def update_music_slider():
        global isPlaying, position, cmds, isRepeating, next_index
        if isPlaying:
            position = last_pos + pygame.mixer.music.get_pos()
            music_slider.set(position)
            if abs(position - (music_length * 1000)) < 300:
                root.after(300, stop)
                music_slider.set(int(music_length * 1000))
                actual_time.configure(text=time.strftime("%M:%S", time.gmtime(music_length))+"."+format_ms(int(music_length*1000)))
            else:
                actual_time.configure(text=time.strftime("%M:%S", time.gmtime(position // 1000)) + "." + format_ms(position % 1000))

            if isLinked and next_index != -1:
                try:
                    if abs(position-prohibited_times[next_index]) < 200:
                        cmd = cmds[next_index]
                        func_name, args_str = cmd[:-1].split('(')
                        args = args_str.split('.') if args_str else []
                        command_functions[func_name](*args)
                        next_index += 1
                        if next_index == len(prohibited_times):
                            next_index = -1
                except:
                    next_index = -1
            root.after(100, update_music_slider)
        else:
            return

    def set_music_slider(offset=0):
        global position, isRepeating, next_index, last_pos
        isRepeating = False
        if isLinked:
            sendColourMusic(defaultColour)
        if offset == 0:
            new_pos = music_slider.get()
        else:
            new_pos = position + (offset * 1000)
            if new_pos < 0:
                new_pos = 0
            elif new_pos > (music_length * 1000):
                new_pos = music_length * 1000
        pygame.mixer.music.play(0, new_pos//1000)
        if not isPlaying:
            pygame.mixer.music.pause()
            music_slider.set(new_pos)
        last_pos = new_pos
        position = int(new_pos)
        for i in range(len(prohibited_times)):
            if position <= prohibited_times[i]:
                next_index = i
                break
        else:
            next_index = -1
        actual_time.configure(text=time.strftime("%M:%S", time.gmtime(position/1000))+"."+format_ms(position%1000))

    def format_ms(ms):
        if ms < 100:
            return "0"
        else:
            return str(ms)[:1]

    def play():
        global isPlaying, isRepeating, next_index, position
        isRepeating = False
        for i in range(len(prohibited_times)):
            if position <= prohibited_times[i]:
                next_index = i
                break
        else:
            next_index = -1
        if not isPlaying:
            isPlaying = True
            play_button.configure(image=imgtk_pause)
            pygame.mixer.music.unpause()
            update_music_slider()
        else:
            isPlaying = False
            if isLinked:
                sendColourMusic(defaultColour)
            play_button.configure(image=imgtk_play)
            pygame.mixer.music.pause()

    @debounce(0.3)
    def stop():
        global isPlaying, position, isRepeating, last_pos, player_main
        last_pos = 0
        isRepeating = False
        position = 0
        actual_time.configure(text="00:00.0")
        music_slider.set(0)
        if isLinked:
            sendColourMusic(defaultColour)
        play_button.configure(image=imgtk_play)
        pygame.mixer.music.play()
        pygame.mixer.music.pause()
        isPlaying = False

    def loadConfig():
        global cmd_frames, prohibited_times, fobj, data, cmds, repeatCmds, repeatCmdsChild
        cmd_frames, prohibited_times, cmds = [],[],[]
        flag = 0
        for i in range(len(data)):
            cmd = data[i].split(",")
            index = int(cmd[0])-1
            prohibited_times.append(int(cmd[1]))
            newFrame = CTkFrame(musicframechild, corner_radius=5, fg_color=("#ebebeb","#515151"))
            newFrame.grid_columnconfigure(6, weight=1)
            newFrame.grid(row=index,column=0,padx=(0,5),pady=1, sticky='ew')
            label1 = CTkLabel(newFrame, text=cmd[0], font=CTkFont(size=13), width=15, height=5)
            label1.grid(row=0,column=0,padx=(10,0),pady=5, sticky='w')
            label2 = CTkLabel(newFrame, text=cmd[2], font=CTkFont(size=13), height=5)
            label2.grid(row=0,column=1,padx=(10,5),pady=5, sticky='w')
            controlType = tk.StringVar(value=cmd[3])
            if controlType.get() == "Repeat":
                if i not in repeatCmds:
                    repeatCmds.append(i)
                newFrame.configure(fg_color=("#c8c8c8","#3a3a3a"))
                secondControl = tk.StringVar(value=cmd[4])
                start = int(secondControl.get().split("-")[0])-1
                end = int(secondControl.get().split("-")[1])-1
                for j in range(start, end+1):
                    if j not in repeatCmdsChild:
                        repeatCmdsChild.append(j)
            if (flag < 3):
                combo1 = CTkComboBox(newFrame,variable=controlType, values=["Single","Hex","RGB","Pulse","Flash"], width=70, height=10, border_width=0, corner_radius=3, command=lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
                flag = flag + 1
            else:
                combo1 = CTkComboBox(newFrame,variable=controlType, values=["Single","Hex","RGB","Pulse","Flash","Repeat"], width=70, height=10, border_width=0, corner_radius=3, command=lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo1.grid(row=0,column=3,padx=(5,0),pady=0, sticky='w')
            combo1.bind("<FocusIn>", lambda e: root.focus_set())
            combo2, combo3, save_button, del_button, copy_button = frameCreator(newFrame, index, cmd, controlType.get())
            cmds.append(cmd[7])   
            cmd_frames.append([newFrame, combo1, combo2, combo3, save_button, del_button, copy_button, label1])
        for i in repeatCmdsChild:
            cmd_frames[i][1].configure(values=["Single","Hex","RGB","Pulse","Flash"])
            cmd_frames[i][5].configure(state="disabled", image=imgtk_del_no)
            cmd_frames[i][0].configure(fg_color=("#c8c8c8","#3a3a3a"))

    def frameCreator(newFrame, index, cmd, controlType):
        secondControl= tk.StringVar(value=cmd[4])
        thirdControl = tk.StringVar(value=cmd[5])
        save_button = CTkButton(newFrame, text="", image=imgtk_save, fg_color="transparent", width=5, height=5)
        copy_button = CTkButton(newFrame, text="", image=imgtk_copy, fg_color="transparent", width=5, height=5)
        if controlType == "Single":
            combo2 = CTkComboBox(newFrame, variable=secondControl, values=[color.capitalize() for color in validColours.keys()], width=70, height=10, border_width=0, corner_radius=3, command= lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo2.grid(row=0,column=4,padx=(5,0),pady=0, sticky='w')
            combo3 = None
        elif controlType == "Flash":
            combo2 = CTkComboBox(newFrame, variable=secondControl, values=['Rainbow', 'Primary', 'Red', 'Green', 'Blue', 'White', 'Purple', 'Cyan', 'Yellow'], width=70, height=10, border_width=0, corner_radius=3, command= lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo2.grid(row=0,column=4,padx=(5,0),pady=0, sticky='w')
            combo3 = CTkComboBox(newFrame, variable=thirdControl, values=['0','1','2','3','4','5','6','7','8','9','10'], width=70, height=10, border_width=0, corner_radius=3, command= lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo3.grid(row=0,column=5,padx=(5,0),pady=0, sticky='w')
        elif controlType == "Pulse":
            combo2 = CTkComboBox(newFrame, variable=secondControl, values=['Rainbow', 'Primary', 'Red', 'Green', 'Blue', 'Green Blue', 'Red Blue', 'Red Green', 'White', 'Purple', 'Cyan', 'Yellow'], width=70, height=10, border_width=0, corner_radius=3, command= lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo2.grid(row=0,column=4,padx=(5,0),pady=0, sticky='w')
            combo3 = CTkComboBox(newFrame, variable=thirdControl, values=['0','1','2','3','4','5','6','7','8','9','10'], width=70, height=10, border_width=0, corner_radius=3, command= lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo3.grid(row=0,column=5,padx=(5,0),pady=0, sticky='w')
        elif controlType == "Repeat":
            combo3 = CTkComboBox(newFrame, variable=thirdControl, values=['1','2','3','4','5','6','7','8','9','10','11','12','13','14','15'], width=70, height=10, border_width=0, corner_radius=3, command= lambda value, index=index, cmd=cmd: editCmd(index, cmd, value))
            combo3.grid(row=0,column=5,padx=(5,0),pady=0, sticky='w')
        elif controlType == "RGB":
            t = secondControl.get()
            r = int(t[0:2], 16)
            g = int(t[2:4], 16)
            b = int(t[4:6], 16)
            secondControl.set(f"{r} {g} {b}")
        if controlType not in ["Hex","RGB","Repeat"]:
            combo2.bind("<FocusIn>", lambda e: root.focus_set())
        else:
            combo2 = CTkEntry(newFrame, textvariable=secondControl, width=70, height=10, border_width=0, corner_radius=3)
            combo2.grid(row=0,column=4,padx=(5,0),pady=0, sticky='w')
            save_button.configure(command= lambda value=combo2.get(), index=index, cmd=cmd: editCmd(index, cmd, value))
            save_button.grid(row=0,column=7,padx=0,pady=0, sticky='e')
            combo3 = None
            combo2.bind("<FocusIn>", lambda e: unbindAll())
            combo2.bind("<FocusOut>", lambda e: bindMusic())
            combo2.bind("<Return>", lambda e: save_button.invoke())
        if combo3!=None:
            combo3.bind("<FocusIn>", lambda e: root.focus_set())
        del_button = CTkButton(newFrame, text="", image=imgtk_del, fg_color="transparent", hover_color="dark red", width=5, height=5, command= lambda index=index, cmd=cmd: delCmd(index, cmd))
        del_button.grid(row=0,column=9,padx=(0,5),pady=0, sticky='e')
        copy_button = CTkButton(newFrame, text="", image=imgtk_copy, fg_color="transparent", hover_color="#877c00", width=5, height=5, command= lambda cmd=cmd: addCmd(True, cmd))
        copy_button.grid(row=0,column=8,padx=0,pady=0, sticky='e')
        return combo2, combo3, save_button, del_button, copy_button

    def delCmd(index, cmd):
        global data, repeatCmds, repeatCmdsChild
        del data[index]
        if cmd[3] == "Repeat":
            repeatCmds.remove(index)
            start = int(cmd[4].split("-")[0])-1
            end = int(cmd[4].split("-")[1])-1
            for i in range(start, end+1):
                repeatCmdsChild.remove(i)

        for i in range(index, len(data)):
            cmd = data[i].split(",")
            cmd[0] = str(i+1)
            data[i] = ','.join(cmd)
        refreshCmds()
    
    def refreshCmds():
        fobj = open(config_file_path, "w")
        fobj.writelines(data)
        fobj.close()
        for child in musicframechild.grid_slaves():
            child.grid_remove()
        musicframe.event_generate("<MouseWheel>", delta=1000*120)
        loadConfig()

    def editCmd(index, cmd, value):
        global data, fobj, cmds, repeatCmds, prohibited_times, repeatCmdsChild
        cmd_frame = cmd_frames[index]
        controlType = cmd[3]
        if value in ["Single","Hex","RGB","Pulse","Flash","Repeat"]: #Major Change
            if value != controlType:
                cmd[3] = value
                cmd_frame[2].grid_forget()
                if cmd_frame[3] != None:
                    cmd_frame[3].grid_forget()
                cmd_frame[4].grid_forget()
                cmd_frame[5].grid_forget()
                if value == "Single":
                    cmd[4] = "Red"
                    cmd[7] = "sendColourMusic(red)"
                elif value == "Flash":
                    cmd[4] = "Red"
                    cmd[5] = "10"
                    cmd[7] = "sendFlashMusic(red.10)"
                elif value == "Pulse":
                    cmd[4] = "Red"
                    cmd[5] = "10"
                    cmd[7] = "sendPulseMusic(red.10)"
                elif value == "Hex":
                    cmd[4] = "FF0000"
                    cmd[7] = "sendHexMusic(#FF0000)"
                elif value == "RGB":
                    cmd[4] = "FF0000"
                    cmd[7] = "sendHexMusic(#FF0000)"
                elif value == "Repeat":
                    cmd[4] = "1-3"
                    cmd[5] = "1"
                    cmd[7] = "sendRepeatMusic(1-3)"
                    if index not in repeatCmds:
                        repeatCmds.append(index)
                    cmd_frame[0].configure(fg_color=("#c8c8c8","#3a3a3a"))
                    root.focus_set()
                    for i in range(0,3):
                        cmd_frames[i][1].configure(values=["Single","Hex","RGB","Pulse","Flash"])
                        cmd_frames[i][5].configure(state="disabled",image=imgtk_del_no)
                        cmd_frames[i][0].configure(fg_color=("#c8c8c8","#3a3a3a"))
                        if i not in repeatCmdsChild:
                            repeatCmdsChild.append(i)
                        
                combo2, combo3, save_button, del_button, copy_button = frameCreator(cmd_frame[0], index, cmd, value)
                cmd_frame[2] = combo2
                cmd_frame[3] = combo3
                cmd_frame[4] = save_button
                cmd_frame[5] = del_button  
                cmd_frame[6] = copy_button
        else: #Minor Change
            if controlType == "Single":
                cmd[4] = value
                cmd[7] = "sendColourMusic("+value.lower()+")"
            elif controlType == "Flash":
                if value.isnumeric():
                    cmd[5] = value
                    cmd[7] = "sendFlashMusic("+cmd[4].lower()+"."+value+")"
                else:
                    cmd[4] = value
                    cmd[7] = "sendFlashMusic("+value.lower()+"."+cmd[5]+")"
            elif controlType == "Pulse":
                if value.isnumeric():
                    cmd[5] = value
                    cmd[7] = "sendPulseMusic("+cmd[4].lower()+"."+value+")"
                else:
                    cmd[4] = value
                    cmd[7] = "sendPulseMusic("+value.lower()+"."+cmd[5]+")"
            elif controlType == "Hex":
                value = cmd_frame[2].get()
                if len(value) == 6 and re.match(r'^[0-9a-fA-F]+$', value):
                    int(value, 16)
                    cmd[4] = value
                    cmd[7] = "sendHexMusic(#"+value.lower()+")"
                    root.focus_set()
                    cmd_frame[4].configure(image=imgtk_save_success)
                    root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                else:
                    cmd_frame[4].configure(image=imgtk_save_fail)
                    root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                    messagebox.showerror("Invalid Hex Colour","Please enter a valid Hex colour.")
                    cmd_frame[2].focus_set()
                    return            
            elif controlType == "RGB":
                value = cmd_frame[2].get()
                if value.split(" ")[0].isnumeric() and value.split(" ")[1].isnumeric() and value.split(" ")[2].isnumeric() and len(value.split(" ")) == 3 and all(0 <= int(i) <= 255 for i in value.split(" ")):
                    rgb_values = value.split(" ")
                    hex_value = '{:02x}{:02x}{:02x}'.format(int(rgb_values[0]), int(rgb_values[1]), int(rgb_values[2]))
                    cmd[4] = hex_value
                    cmd[7] = "sendHexMusic(#" + hex_value.lower() + ")"
                    root.focus_set()
                    cmd_frame[4].configure(image=imgtk_save_success)
                    root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                else:
                    cmd_frame[4].configure(image=imgtk_save_fail)
                    root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                    messagebox.showerror("Invalid RGB Colour","Please enter a valid RGB colour separated with spaces.")
                    cmd_frame[2].focus_set()
                    return
            elif controlType == "Repeat":
                fvalue = cmd_frame[2].get()
                start = int(fvalue.split("-")[0])
                end = int(fvalue.split("-")[1])
                if not (re.match(r'^([1-9]\d*|0)-([1-9]\d*|0)$', fvalue) and start <= end):
                    cmd_frame[4].configure(image=imgtk_save_fail)
                    root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                    messagebox.showerror("Invalid Range","Please enter a valid range. It must be two numbers separated by a hyphen. For example, 1-9. The first number cannot exceed the second number and the second number cannot exceed the total number of commands excluding Repeat commands.")
                    cmd_frame[2].focus_set()
                    return
                for i in range(start-1, end):
                    if i in repeatCmds:
                        cmd_frame[4].configure(image=imgtk_save_fail)
                        root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                        messagebox.showerror("Nested Repeats","You cannot set a range that has another Repeat command within it.")
                        cmd_frame[2].focus_set()
                        return
                if value.isnumeric():
                    cmd[5] = value
                    cmd[7] = "sendRepeatMusic("+cmd[4].lower()+"."+value+")"
                else:
                    oldstart = int(cmd[4].split("-")[0])-1
                    oldend = int(cmd[4].split("-")[1])-1
                    for i in range(oldstart,oldend+1):
                        if i not in list(x for x in range(start-1,end)):
                            repeatCmdsChild.remove(i)
                            if i not in [0,1,2]:
                                cmd_frames[i][1].configure(values=["Single","Hex","RGB","Pulse","Flash","Repeat"])
                            cmd_frames[i][5].configure(state="normal",image=imgtk_del)
                            cmd_frames[i][0].configure(fg_color=("#ebebeb","#515151"))
                    cmd[4] = fvalue
                    cmd_frame[0].configure(fg_color=("#c8c8c8","#3a3a3a"))
                    cmd[7] = "sendRepeatMusic("+fvalue+"."+cmd[5]+")"
                    root.focus_set()
                    cmd_frame[4].configure(image=imgtk_save_success)
                    root.after(1000, lambda: cmd_frame[4].configure(image=imgtk_save))
                    for i in range(start-1,end):
                        cmd_frames[i][1].configure(values=["Single","Hex","RGB","Pulse","Flash"])
                        cmd_frames[i][5].configure(state="disabled",image=imgtk_del_no)
                        cmd_frames[i][0].configure(fg_color=("#c8c8c8","#3a3a3a"))
                        if i not in repeatCmdsChild:
                            repeatCmdsChild.append(i)
        cmds[index] = cmd[7]
        data[index] = ','.join(cmd)
        fobj = open(config_file_path, "w")
        fobj.writelines(data)
        fobj.close()

    def addCmd(copy=False, copy_data=None):
        global data, cmd_frames, prohibited_times
        if position not in prohibited_times:
            index = 0
            for i in data:
                ipos = int(i.split(",")[1])
                if ipos > position:
                    break
                index += 1
            if index in repeatCmdsChild:
                messagebox.showerror("Repeat Block Found","You cannot add or copy a command into a Repeat block range. Try deleting the Repeat block first.")
                return
            if copy == False:
                data.insert(index, f"{index+1},{int(position)},{time.strftime("%M:%S", time.gmtime(position//1000))+"."+format_ms(position%1000)},Single,Red,0,0,sendColourMusic(red),\n")
            else:
                data.insert(index, f"{index+1},{int(position)},{time.strftime("%M:%S", time.gmtime(position//1000))+"."+format_ms(position%1000)},{copy_data[3]},{copy_data[4]},{copy_data[5]},{copy_data[6]},{copy_data[7]},\n") # type: ignore
            for i in range(index, len(data)):
                cmd = data[i].split(",")
                cmd[0] = str(i+1)
                data[i] = ','.join(cmd)
            refreshCmds()
        else:
            messagebox.showerror("Duplicate Command","A command already exists in the configuration at that timestamp.")

    def link():
        global isLinked
        if not isLinked:
            isLinked = True
            link_button.configure(fg_color="green", hover_color="#005500")
        else:
            isLinked = False
            link_button.configure(fg_color=("#3b8ed0","#1f6aa5"),hover_color=("#36719f","#144870"))
            if isConnected:
                sendColourMusic(defaultColour)

    def seekBack():
        set_music_slider(-seekAmount) # type: ignore
    
    def seekForward():
        set_music_slider(seekAmount) # type: ignore

    def seekAdjust(manual=False, invert=False):
        global seekAmount
        seeks = [0.1, 0.5, 1, 2, 5, 10, 30]
        index = seeks.index(seekAmount)
        if invert:
            index -= 1
            if index == -1:
                index = 0
        else:
            index += 1
            if index == 7:
                if manual:
                    index = 0
                else:
                    index = 6
        seekAmount = seeks[index]
        settings[13] = str(seekAmount) + "\n"
        writesettings()
        seek_button.configure(text=str(seekAmount) + "s")

    #Page Functions
    def unbindAll():
        root.unbind("<KeyRelease-o>")
        root.unbind("<KeyRelease-s>")
        root.unbind("<KeyRelease-l>")
        root.unbind("<KeyRelease-a>")
        root.unbind("<KeyRelease-r>")
        root.unbind("<KeyRelease-g>")
        root.unbind("<KeyRelease-b>")
        root.unbind("<KeyRelease-w>")
        root.unbind("<KeyRelease-p>")
        root.unbind("<KeyRelease-c>")
        root.unbind("<space>")
        root.unbind("<Right>")
        root.unbind("<Left>")
        root.unbind("<Up>")
        root.unbind("<Down>")
        root.unbind("<KeyRelease-1>")
        root.unbind("<KeyRelease-2>")
        root.unbind("<KeyRelease-3>")
        root.unbind("<KeyRelease-4>")
        root.unbind("<KeyRelease-5>")
        root.unbind("<KeyRelease-6>")
        root.unbind("<KeyRelease-7>")
        root.unbind("<KeyRelease-8>")
        root.unbind("<KeyRelease-9>")
        root.unbind("<KeyRelease-0>")
        root.unbind("<KeyRelease-`>")
        root.bind("<Tab>")
    
    def bindBasic():
        unbindAll()
        root.bind("<KeyRelease-r>",lambda e:sendColourWB(255,0,0))
        root.bind("<KeyRelease-g>",lambda e:sendColourWB(0,255,0))
        root.bind("<KeyRelease-b>",lambda e:sendColourWB(0,0,255))
        root.bind("<KeyRelease-w>",lambda e:sendColourWB(255,255,255))
        root.bind("<KeyRelease-p>",lambda e:sendColourWB(255,0,40))
        root.bind("<KeyRelease-c>",lambda e:connect())
        root.bind("<KeyRelease-`>",lambda e:swapPulseFlash())
        root.bind("<space>",lambda e:togglePower())
        root.bind("<Right>",lambda e:setBrightness(True))
        root.bind("<Left>",lambda e:setBrightness(False))
        root.bind("<Up>",lambda e:setInterval(True))
        root.bind("<Down>",lambda e:setInterval(False))
        root.bind("<KeyRelease-1>",lambda e:rainbowPulse.invoke())
        root.bind("<KeyRelease-2>",lambda e:rainbowFlash.invoke())
        root.bind("<KeyRelease-3>",lambda e:rgbPulse.invoke())
        root.bind("<KeyRelease-4>",lambda e:rgbFlash.invoke())
        root.bind("<KeyRelease-5>",lambda e:redPulse.invoke())
        root.bind("<KeyRelease-6>",lambda e:redFlash.invoke())
        root.bind("<KeyRelease-7>",lambda e:greenPulse.invoke())
        root.bind("<KeyRelease-8>",lambda e:greenFlash.invoke())
        root.bind("<KeyRelease-9>",lambda e:bluePulse.invoke())
        root.bind("<KeyRelease-0>",lambda e:blueFlash.invoke())
        root.bind("<Tab>",lambda e:nextTab())

    def bindAlert():
        unbindAll()
        root.bind("<KeyRelease-c>",lambda e:connect())
        root.bind("<KeyRelease-1>",lambda e:radio_button_1.invoke())
        root.bind("<KeyRelease-2>",lambda e:radio_button_2.invoke())
        root.bind("<KeyRelease-3>",lambda e:radio_button_3.invoke())
        root.bind("<KeyRelease-4>",lambda e:radio_button_4.invoke())
        root.bind("<Tab>",lambda e:nextTab())
        root.bind("<space>",lambda e: alertButton.invoke())

    def bindMusic():
        unbindAll()
        root.bind("<KeyRelease-c>",lambda e:connect())
        root.bind("<KeyRelease-o>",lambda e:load_button.invoke())
        root.bind("<KeyRelease-s>",lambda e:stop_button.invoke())
        root.bind("<KeyRelease-l>",lambda e:link_button.invoke())
        root.bind("<KeyRelease-a>",lambda e:add_button.invoke())
        root.bind("<Tab>",lambda e:nextTab())
        root.bind("<space>",lambda e: play_button.invoke())
        root.bind("<Left>",lambda e:seekBack())
        root.bind("<Right>",lambda e:seekForward())
        root.bind("<Up>",lambda e:seekAdjust())
        root.bind("<Down>",lambda e:seekAdjust(invert=True))

    def bindSettings():
        unbindAll()
        root.bind("<KeyRelease-c>",lambda e:connect())
        root.bind("<Tab>",lambda e:nextTab())

    def nextTab():
        if settings[5][:-1]=="1":
            tab = mainframe.get()
            if tab=="Remote":
                mainframe.set("Alert")
            elif tab=="Alert":
                mainframe.set("Player")
            elif tab=="Player":
                mainframe.set("Settings")
            else:
                mainframe.set("Remote")
            updateTab()

    def updateTab():
        global isLoaded
        stopAlert()
        if isConnected and isLinked:
            link_button.configure(fg_color="green", hover_color="#005500")
        tab = mainframe.get()
        macInput.configure(state="disabled")
        uuidInput.configure(state="disabled")
        if tab=="Remote":
            bindBasic()
        elif tab=="Alert":
            bindAlert()
        elif tab=="Player":
            bindMusic()
            if isLoaded:
                pygame.mixer.music.load(music)
                pygame.mixer.music.play()
                pygame.mixer.music.pause()
                play_button.configure(image=imgtk_play)
            connect_button.grid_forget()
            power_button.grid_forget()
            headinglogo.grid_forget()
            heading1.grid_forget()
            heading2.grid_forget()
            mcontrolframe.grid(row=0,column=0,rowspan=2,columnspan=4,padx=10,pady=(5,0),sticky='nsew')
        else:
            if not isConnected:
                macInput.configure(state="normal")
                uuidInput.configure(state="normal")
            bindSettings()
        if tab!="Player":
            pygame.mixer.music.unload()
            connect_button.grid(row=0,column=2,rowspan=2,padx=0, sticky='e')
            power_button.grid(row=0,column=3,rowspan=2,padx=10, sticky='e')
            headinglogo.grid(row=0,column=0,rowspan=2,pady=10, sticky='w')
            heading1.grid(row=0,column=1,pady=0, sticky='sw')
            heading2.grid(row=1,column=1,pady=0, sticky='nw')
            mcontrolframe.grid_forget()
            
    #Settings Validation and Reset
    def createsettings():
        try:
            f=open("Settings.txt","w")
        except PermissionError:
            messagebox.showerror("Administrator Privileges Needed","Because of the nature of this LightCraft install, you will need to launch as administrator. To prevent this behaviour, please install LightCraft again on a user directory.")
            quit()
        f.write(f"LightCraft Settings - Any corruption may lead to configuration loss\nMade by Akash Samanta\n{default_address}\nFFD9\n0\n1\n1\n#FFFFFF\n#FFFFFF\n#FFFFFF\n#FFFFFF\n#FFFFFF\nSave\n5\n1\nRed\n\nCustom Operation Codes\nEdit the following values which correspond to the data packet being sent to the LED. Useful for different LED Models. NO SPACES. Must end with comma.\n\nFlash\ntrailing,bb,\nrgb_flash,62,\nall_flash,38,\nwhite_flash,37,\npurple_flash,36,\ncyan_flash,35,\nyellow_flash,34,\nblue_flash,33,\ngreen_flash,32,\nred_flash,31,\neyesore_flash,30,\nleading,44,\n\nPulse\ntrailing,BB,\ngb_pulse,2F,\nrb_pulse,2E,\nrg_pulse,2D,\nwhite_pulse,2C,\npurple_pulse,2B,\ncyan_pulse,2A,\nyellow_pulse,29,\nblue_pulse,28,\ngreen_pulse,27,\nred_pulse,26,\nrgb_pulse,61,\nall_pulse,25,\ntrailing,44,\n\nOn\ntrailing_code,CC,\nmain,23,\nleading,33,\n\nOff\ntrailing_code,CC,\nmain,24,\nleading,33,\n\nSingle\ntrailing,56,\norder,r,g,b,\nleading,00,F0,AA,\n")
        f.close()

    #Quit or Relaunch Application
    def destroyer():
        global root, isPlaying, isRepeating
        isRepeating = False
        if isPlaying:
            stop()
        disconnect()
        root.destroy()
        controller.loop.call_soon_threadsafe(controller.loop.stop)
        loop_thread.join()

    #For other functions to write Settings
    def writesettings():
        global settings
        f=open("Settings.txt","w")
        f.writelines(settings)
        f.close()

    #Normal Reset from Application
    def resetsettings():
        global isLoaded
        ans=messagebox.askyesno("Reset Settings","You will also lose any custom operation codes that you have defined. Are you sure you want to reset settings?")
        if ans:
            if isLoaded:
                clearload()
            isLoaded = False
            autoCSwitch.deselect()
            keyBindSwitch.select()
            loadedSwitch.select()
            macInputVar.set(default_address)
            uuidInputVar.set("FFD9")
            customColour1.configure(fg_color="#FFFFFF")
            customColour2.configure(fg_color="#FFFFFF")
            customColour3.configure(fg_color="#FFFFFF")
            customColour4.configure(fg_color="#FFFFFF")
            customColour5.configure(fg_color="#FFFFFF")
            macInputSave()
            uuidInputSave()
            updateTab()
            createsettings()
            applysettings()

    #Settings Corruption Reset
    def resetsettings2():
        createsettings()
        applysettings()

    #Boot and apply settings
    def applysettings():
        global settings, address, char_uuid, seekAmount, defaultColour, validFlashCode, validPulseCode, leading_flash, trailing_flash, leading_pulse, trailing_pulse, trailing_off, leading_off, trailing_on, leading_on, trailing_single, leading_single, main_on, main_off, order_single
        f=open("Settings.txt","a+")
        f.seek(0)
        settings=f.readlines()
        check=[['LightCraft Settings - Any corruption may lead to configuration loss'],['Made by Akash Samanta'],[],[],['0','1'],['0','1'],['0','1'],['Hex'],['Hex'],['Hex'],['Hex'],['Hex'],[],['0.1','0.5','1','2','5','10','30'],['0','1'],[color.capitalize() for color in validColours.keys()],[],['Custom Operation Codes'],[],[],['Flash'],[],[],[],[],[],[],[],[],[],[],[],[],[],['Pulse'],[],[],[],[],[],[],[],[],[],[],[],[],[],[],[],['On'],[],[],[],[],['Off'],[],[],[],[],['Single'],[],[],[]]
        #print(len(settings),len(check)) #For Debug Only
        #print(settings) #For Debug Only
        for i in range(len(check)):
            try:
                if check[i]!=[]:
                    if check[i]==['Hex']:
                        #print(settings[i],check[i]) #For Debug Only
                        if settings[i][:-1][0]!="#" or len(settings[i][:-1])!=7:
                            messagebox.showerror("Unable to Load Settings","The settings file seems corrupted, possibly due to file tampering. LightCraft will attempt to restore default settings.")
                            resetsettings2()
                    elif settings[i][:-1] not in check[i]:
                        messagebox.showerror("Unable to Load Settings","The settings file seems corrupted, possibly due to file tampering. LightCraft will attempt to restore default settings.")
                        #print(settings[i][:-1],"and",check[i]) #For Debug Only
                        resetsettings2()
            except:
                messagebox.showerror("Unable to Load Settings","The settings file seems corrupted, possibly due to file tampering. LightCraft will attempt to restore default settings.")
                #print("FAIL") #For Debug Only
                resetsettings2()
        try:
            trailing_flash = int(settings[21].split(",")[1], 16)
            validFlashCode = {
                'rgb_flash': int(settings[22].split(",")[1], 16),
                'all_flash': int(settings[23].split(",")[1], 16),
                'white_flash': int(settings[24].split(",")[1], 16),
                'purple_flash': int(settings[25].split(",")[1], 16),
                'cyan_flash': int(settings[26].split(",")[1], 16),
                'yellow_flash': int(settings[27].split(",")[1], 16),
                'blue_flash': int(settings[28].split(",")[1], 16),
                'green_flash': int(settings[29].split(",")[1], 16),
                'red_flash': int(settings[30].split(",")[1], 16),
                'eyesore_flash': int(settings[31].split(",")[1], 16)
            }
            leading_flash = int(settings[32].split(",")[1], 16)
            trailing_pulse = int(settings[35].split(",")[1], 16)
            validPulseCode = {
                'gb_pulse': int(settings[36].split(",")[1], 16),
                'rb_pulse': int(settings[37].split(",")[1], 16),
                'rg_pulse': int(settings[38].split(",")[1], 16),
                'white_pulse': int(settings[39].split(",")[1], 16),
                'purple_pulse': int(settings[40].split(",")[1], 16),
                'cyan_pulse': int(settings[41].split(",")[1], 16),
                'yellow_pulse': int(settings[42].split(",")[1], 16),
                'blue_pulse': int(settings[43].split(",")[1], 16),
                'green_pulse': int(settings[44].split(",")[1], 16),
                'red_pulse': int(settings[45].split(",")[1], 16),
                'rgb_pulse': int(settings[46].split(",")[1], 16),
                'all_pulse': int(settings[47].split(",")[1], 16)
            }
            leading_pulse = int(settings[48].split(",")[1], 16)
            trailing_on = int(settings[51].split(",")[1], 16)
            main_on = int(settings[52].split(",")[1], 16)
            leading_on = int(settings[53].split(",")[1], 16)
            trailing_off = int(settings[56].split(",")[1], 16)
            main_off = int(settings[57].split(",")[1], 16)
            leading_off = int(settings[58].split(",")[1], 16)
            trailing_single = [int(x, 16) for x in settings[61].split(",")[1:-1]]
            order_single = settings[62].split(",")[1:-1]
            leading_single = [int(x, 16) for x in settings[63].split(",")[1:-1]]
        except:
            messagebox.showerror("Invalid Custom Operation Codes","The custom operation codes in the settings file are invalid. LightCraft will attempt to restore default operation codes.")
            resetsettings2()
        address=settings[2][:-1]
        char_uuid=settings[3][:-1]
        seekAmount=float(settings[13][:-1])
        defaultColour=settings[15][:-1].lower()
        if settings[14][:-1]=="1":
            set_appearance_mode("dark")
        else:
            set_appearance_mode("light")
        f.close()

    #Getting settings
    if not os.path.exists("Settings.txt"):
        createsettings()

    #Making the Application
    root.title("LightCraft")
    root.protocol("WM_DELETE_WINDOW", destroyer)
    root.iconbitmap(r"./Resources/logo2.ico")
    applysettings()
    userwinx = root.winfo_screenwidth()
    userwiny = root.winfo_screenheight()
    x = (userwinx)//3
    y = (userwiny)//3
    root.geometry(f"750x420+{x}+{y}")
    root.minsize(750,420)
    root.resizable(False,True)

    #Start Controller
    controller = BluetoothController(address, char_uuid)
    loop_thread = threading.Thread(target=start_event_loop, args=(controller,))
    loop_thread.start()

    #Frames
    mainframe=CTkTabview(root, command=updateTab)
    mainframe.add("Remote")
    mainframe.add("Alert")
    mainframe.add("Player")
    mainframe.add("Settings")
    settingschild=CTkScrollableFrame(mainframe.tab("Settings"), fg_color="transparent")
    sgframe=CTkFrame(mainframe.tab("Remote"), fg_color="transparent")
    mgframe=CTkFrame(mainframe.tab("Remote"), fg_color="transparent")
    alertframe=CTkFrame(mainframe.tab("Alert"))
    mcontrolframe=CTkFrame(root, fg_color="transparent")

    #Button Scaling
    bsize=16
    bheight=35
    bwidth=150
    sgwidth=37
    sgheight=37
    sgradius=50

    #Images
    try:
        image1 = Image.open(r"./Resources/logo.png")
        image2 = Image.open(r"./Resources/onButton.png")
        image3 = Image.open(r"./Resources/offButton.png")
        image4 = Image.open(r"./Resources/pulseHint.png")
        image5 = Image.open(r"./Resources/flashHint.png")
        image6 = Image.open(r"./Resources/italy.png")
        image7 = Image.open(r"./Resources/japan.png")
        image8 = Image.open(r"./Resources/france.png")
        image9 = Image.open(r"./Resources/usa.png")
        image11 = Image.open(r"./Resources/play.png")
        image12 = Image.open(r"./Resources/pause.png")
        image13 = Image.open(r"./Resources/stop.png")
        image14 = Image.open(r"./Resources/link.png")
        image16 = Image.open(r"./Resources/add.png")
        image17 = Image.open(r"./Resources/folder.png")
        image18 = Image.open(r"./Resources/save.png")
        image15 = Image.open(r"./Resources/saveSuccess.png")
        image19 = Image.open(r"./Resources/delete.png")
        image20 = Image.open(r"./Resources/copy.png")
        image21 = Image.open(r"./Resources/saveFail.png")
        image22 = Image.open(r"./Resources/bluetooth.png")
        image23 = Image.open(r"./Resources/deleteNo.png")
    except:
        tk.messagebox.showerror("Missing Resources","LightCraft could not find critical resources. The Resources folder may have been corrupted or deleted. Please re-install LightCraft from official sources.") # type: ignore #Missing Resources
        quit()
    imgtk1 = CTkImage(light_image=image1,size=(60,60))
    imgtk2 = CTkImage(light_image=image2,size=(25,25))
    imgtk3 = CTkImage(light_image=image3,size=(25,25))
    imgtk4 = CTkImage(light_image=image4,size=(25,25))
    imgtk5 = CTkImage(light_image=image5,size=(25,25))
    imgtk6 = CTkImage(light_image=image6,size=(160,90))
    imgtk7 = CTkImage(light_image=image7,size=(160,90))
    imgtk8 = CTkImage(light_image=image8,size=(160,90))
    imgtk9 = CTkImage(light_image=image9,size=(160,90))
    imgtk_play = CTkImage(light_image=image11,size=(24,24))
    imgtk_pause = CTkImage(light_image=image12,size=(24,24))
    imgtk_stop = CTkImage(light_image=image13,size=(24,24))
    imgtk_add = CTkImage(light_image=image16,size=(24,24))
    imgtk_link = CTkImage(light_image=image14,size=(24,24))
    imgtk_folder = CTkImage(light_image=image17,size=(24,24))
    imgtk_save = CTkImage(light_image=image18,size=(16,16))
    imgtk_save_success = CTkImage(light_image=image15,size=(16,16))
    imgtk_del = CTkImage(light_image=image19,size=(16,16))
    imgtk_del_no = CTkImage(light_image=image23,size=(16,16))
    imgtk_copy = CTkImage(light_image=image20,size=(16,16))
    imgtk_save_fail = CTkImage(light_image=image21,size=(16,16))
    imgtk_bluetooth = CTkImage(light_image=image22,size=(18,18))

    #Remote Elements
    headinglogo = CTkButton(root, text="", width=80, image=imgtk1,command=lambda :webbrowser.open("https://github.com/akashcraft/LED-Controller"), hover=False, fg_color="transparent")
    heading1 = CTkLabel(root, text="LightCraft", font=CTkFont(size=30)) #LightCraft
    heading2 = CTkLabel(root, text="Version 2.8.8 (Stable)", font=CTkFont(size=13)) #Version
    connect_button = CTkButton(root, text="Connect", compound="right",font=CTkFont(size=bsize), width=bwidth, height=bheight, command=connect)
    power_button = CTkButton(root, text="", fg_color=("#dbdbdb","#2b2b2b"), hover_color=("#a0a0a0", "#1c1c1c"), image=imgtk3, font=CTkFont(size=bsize), width=sgwidth, corner_radius=10, height=bheight, command=togglePower)
    colorpicker = CTkColorPicker(mainframe.tab("Remote"), width=257, orientation=HORIZONTAL, command=lambda e: sendHex(e))
    pulseflash_var = tk.StringVar(value='all_pulse')
    rainbowPulse = CTkRadioButton(mgframe, text="Rainbow", command=sendPulse, variable= pulseflash_var, value='all_pulse')
    rgbPulse = CTkRadioButton(mgframe, text="RGB", command=sendPulse, variable= pulseflash_var, value='rgb_pulse')
    redPulse = CTkRadioButton(mgframe, text="Red", command=sendPulse, variable= pulseflash_var, value='red_pulse')
    greenPulse = CTkRadioButton(mgframe, text="Green", command=sendPulse, variable= pulseflash_var, value='green_pulse')
    bluePulse = CTkRadioButton(mgframe, text="Blue", command=sendPulse, variable= pulseflash_var, value='blue_pulse')
    whitePulse = CTkRadioButton(mgframe, text="White", command=sendPulse, variable= pulseflash_var, value='white_pulse')
    rainbowFlash = CTkRadioButton(mgframe, text="Rainbow", command=sendFlash, variable= pulseflash_var, value='all_flash')
    rgbFlash = CTkRadioButton(mgframe, text="RGB", command=sendFlash, variable= pulseflash_var, value='rgb_flash')
    redFlash = CTkRadioButton(mgframe, text="Red", command=sendFlash, variable= pulseflash_var, value='red_flash')
    greenFlash = CTkRadioButton(mgframe, text="Green", command=sendFlash, variable= pulseflash_var, value='green_flash')
    blueFlash = CTkRadioButton(mgframe, text="Blue", command=sendFlash, variable= pulseflash_var, value='blue_flash')
    whiteFlash = CTkRadioButton(mgframe, text="White", command=sendFlash, variable= pulseflash_var, value='white_flash')
    pulseHint = CTkButton(mgframe, text="Pulse", fg_color=("#dbdbdb","#2b2b2b"), width=20, compound="right", image=imgtk4, hover=False, text_color=("black","white"))
    flashHint = CTkButton(mgframe, text="Flash", fg_color=("#dbdbdb","#2b2b2b"), width=20, compound="right", image=imgtk5, hover=False, text_color=("black","white"))
    intervalSlider = CTkSlider(mgframe, from_=0, to=10, orientation="vertical", height=185, width=20, progress_color="white", border_width=0, command=lambda e: updateInterval())

    root.grid_columnconfigure(1,weight=1)
    root.grid_rowconfigure(2,weight=1)
    headinglogo.grid(row=0,column=0,rowspan=2,pady=10, sticky='w')
    heading1.grid(row=0,column=1,pady=0, sticky='sw')
    heading2.grid(row=1,column=1,pady=0, sticky='nw')
    connect_button.grid(row=0,column=2,rowspan=2,padx=0, sticky='e')
    power_button.grid(row=0,column=3,rowspan=2,padx=10, sticky='e')
    mainframe.grid(row=2,column=0,columnspan=4,padx=10, pady=(0,10), sticky='nsew')
    mainframe.tab("Remote").grid_columnconfigure(1,weight=1)
    sgframe.grid(row=0,column=0,padx=10,pady=10, sticky='n')
    sgButton(sgframe, 0, 0, "red")
    sgButton(sgframe, 0, 1, "green")
    sgButton(sgframe, 0, 2, "blue")
    sgButton(sgframe, 0, 3, "maroon")
    sgButton(sgframe, 1, 0, "orange")
    sgButton(sgframe, 1, 1, "olive")
    sgButton(sgframe, 1, 2, "teal")
    sgButton(sgframe, 1, 3, "navy")
    sgButton(sgframe, 2, 0, "yellow")
    sgButton(sgframe, 2, 1, "lime")
    sgButton(sgframe, 2, 2, "indigo")
    sgButton(sgframe, 2, 3, "pink")
    sgButton(sgframe, 3, 0, "brown")
    sgButton(sgframe, 3, 1, "coral")
    sgButton(sgframe, 3, 2, "purple")
    sgButton(sgframe, 3, 3, "black")
    sgButton(sgframe, 4, 0, "gold")
    sgButton(sgframe, 4, 1, "cyan")
    sgButton(sgframe, 4, 2, "violet")
    sgButton(sgframe, 4, 3, "white")
    sgButton(sgframe, 0, 4, "white")
    sgButton(sgframe, 1, 4, "white")
    sgButton(sgframe, 2, 4, "white")
    sgButton(sgframe, 3, 4, "white")
    sgButton(sgframe, 4, 4, "white")
    colorpicker.grid(row=0,column=1,pady=10,sticky='n')
    mgframe.grid(row=0,column=2,padx=(5,10),pady=10, sticky='n')
    pulseHint.grid(row=0,column=0,pady=(5,0), padx=0, ipadx=0, sticky='w')
    flashHint.grid(row=0,column=1,pady=(5,0), sticky='w')
    rainbowPulse.grid(row=1,column=0,pady=(8,0), padx=5, sticky='e')
    rgbPulse.grid(row=2,column=0,pady=(10,0), padx=5, sticky='e')
    redPulse.grid(row=3,column=0,pady=(10,0), padx=5, sticky='e')
    greenPulse.grid(row=4,column=0,pady=(10,0), padx=5, sticky='e')
    bluePulse.grid(row=5,column=0,pady=(10,0), padx=5, sticky='e')
    whitePulse.grid(row=6,column=0,pady=(10,0), padx=5, sticky='e')
    rainbowFlash.grid(row=1,column=1,pady=(10,0), padx=5, sticky='e')
    rgbFlash.grid(row=2,column=1,pady=(10,0), padx=5, sticky='e')
    redFlash.grid(row=3,column=1,pady=(10,0), padx=5, sticky='e')
    greenFlash.grid(row=4,column=1,pady=(10,0), padx=5, sticky='e')
    blueFlash.grid(row=5,column=1,pady=(10,0), padx=5, sticky='e')
    whiteFlash.grid(row=6,column=1,pady=(10,0), padx=5, sticky='e')
    intervalSlider.grid(row=1,column=2,rowspan=6, padx=0, sticky='se')

    #Settings
    mainframe.tab("Settings").grid_columnconfigure(0,weight=1)
    mainframe.tab("Settings").grid_rowconfigure(0,weight=1)
    settingschild.grid(row=0,column=0,padx=0,pady=0, sticky='nsew')
    settingschild.grid_columnconfigure(1,weight=1)
    CTkLabel(settingschild, text="LED MAC Address").grid(row=0,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Characteristic UUID").grid(row=1,column=0,padx=5,pady=(4,0), sticky='w')
    darkModeLabel = CTkLabel(settingschild, text="Dark Mode")
    darkModeLabel.grid(row=2,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Auto Connect").grid(row=3,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Enable Keyboard Shortcuts").grid(row=4,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Remember Loaded Files").grid(row=5,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Media Configurations").grid(row=8,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Edit Operation Codes (Advanced)").grid(row=10,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Reset Settings").grid(row=9,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="User Manual").grid(row=7,column=0,padx=5,pady=(4,0), sticky='w')
    CTkLabel(settingschild, text="Default Colour").grid(row=6,column=0,padx=5,pady=(4,0), sticky='w')
    macInputVar = tk.StringVar(value=settings[2][:-1])
    macInput = CTkEntry(settingschild, placeholder_text="32:06:C2:00:0A:9E", textvariable=macInputVar, height=5, corner_radius=5, justify='right')
    macInput.grid(row=0,column=1,padx=5,pady=(4,0), sticky='e')
    macInputButton= CTkButton(settingschild, text="Save", width=60, height=15, corner_radius=5, command=macInputSave)
    macInputButton.grid(row=0,column=2,padx=8,pady=(4,0), sticky='e')
    uuidInputVar = tk.StringVar(value=settings[3][:-1])
    uuidInput = CTkEntry(settingschild, placeholder_text="FFD9", textvariable=uuidInputVar, height=5, corner_radius=5, justify='right')
    uuidInputButton = CTkButton(settingschild, text="Save", width=60, height=15, corner_radius=5, command=uuidInputSave)
    uuidInputButton.grid(row=1,column=2,padx=8,pady=(4,0), sticky='e')
    uuidInput.grid(row=1,column=1,padx=5,pady=(4,0), sticky='e')
    darkModeVar = tk.IntVar(value=int(settings[14][:-1]))
    darkModeSwitch = CTkCheckBox(settingschild, text="", variable=darkModeVar, checkbox_height=15, checkbox_width=15, border_width=1, corner_radius=5, width=0, command=toggleTheme)
    darkModeSwitch.grid(row=2,column=2,padx=(5,0),pady=(4,0), sticky='e')
    autoCSVar = tk.IntVar(value=int(settings[4][:-1]))
    autoCSwitch = CTkCheckBox(settingschild, text="", variable=autoCSVar, checkbox_height=15, checkbox_width=15, border_width=1, corner_radius=5, width=0, command=toggleAutoCS)
    autoCSwitch.grid(row=3,column=2,padx=(5,0),pady=(4,0), sticky='e')
    keyBindVar = tk.IntVar(value=int(settings[5][:-1]))
    keyBindSwitch = CTkCheckBox(settingschild, text="", variable=keyBindVar, checkbox_height=15, checkbox_width=15, border_width=1, corner_radius=5, width=0, command=toggleKeyBind)
    keyBindSwitch.grid(row=4,column=2,padx=(5,0),pady=(4,0), sticky='e')
    loadedVar = tk.IntVar(value=int(settings[6][:-1]))
    loadedSwitch = CTkCheckBox(settingschild, text="", variable=loadedVar, checkbox_height=15, checkbox_width=15, border_width=1, corner_radius=5, width=0, command=toggleLoaded)
    loadedSwitch.grid(row=5,column=2,padx=(5,0),pady=(4,0), sticky='e')
    defaultColourVar = tk.StringVar(value=settings[15][:-1])
    defaultCombo = CTkComboBox(settingschild, variable=defaultColourVar, values=[color.capitalize() for color in validColours.keys()], width=70, height=20, border_width=0, corner_radius=3, command=updateDefaultColour)
    defaultCombo.grid(row=6,column=2,padx=(8,7), sticky='e')
    defaultCombo.bind("<FocusIn>",lambda e:root.focus_set())
    CTkButton(settingschild, text="Open", width=60, height=15, corner_radius=5, command=showMusic).grid(row=8,column=2,padx=8,pady=(4,0), sticky='e')
    CTkButton(settingschild, text="Edit", width=60, height=15, corner_radius=5, command=openSettings).grid(row=10,column=2,padx=8,pady=(4,0), sticky='e')
    resetButton = CTkButton(settingschild, text="Reset", width=60, height=15, corner_radius=5, command=resetsettings)
    resetButton.grid(row=9,column=2,padx=8,pady=(4,0), sticky='e')
    CTkButton(settingschild, text="Open", width=60, height=15, corner_radius=5, command=openManual).grid(row=7,column=2,padx=8,pady=(4,0), sticky='e')

    #Alert
    mainframe.tab("Alert").grid_columnconfigure(0,weight=1)
    CTkLabel(alertframe,text='',image=imgtk6).grid(row=0,column=0,padx=(10,0),pady=(10,0), sticky='nw')
    CTkLabel(alertframe,text='',image=imgtk7).grid(row=0,column=1,padx=(10,0),pady=(10,0), sticky='nw')
    CTkLabel(alertframe,text='',image=imgtk8).grid(row=0,column=2,padx=(10,0),pady=(10,0), sticky='nw')
    CTkLabel(alertframe,text='',image=imgtk9).grid(row=0,column=3,padx=(10,0),pady=(10,0), sticky='nw')
    alertText = CTkLabel(mainframe.tab("Alert"), text="Please connect your LED Strips first", font=CTkFont(size=12), text_color=("red","yellow"))
    alertText.grid(row=0,column=0,padx=10,pady=(4,0), sticky='nsew')
    alert_var = tk.IntVar(value=0)
    radio_button_1 = CTkRadioButton(alertframe, text="Sapienza, Italy", variable=alert_var, value=0, state="disabled", command=stopAlert)
    radio_button_1.grid(row=1,column=0,padx=10,pady=10, sticky='w')
    radio_button_2 = CTkRadioButton(alertframe, text="Hokkaido, Japan", variable=alert_var, value=1, state="disabled", command=stopAlert)
    radio_button_2.grid(row=1,column=1,padx=10,pady=10, sticky='w')
    radio_button_3 = CTkRadioButton(alertframe, text="Paris, France", variable=alert_var, value=2, state="disabled", command=stopAlert)
    radio_button_3.grid(row=1,column=2,padx=10,pady=10, sticky='w')
    radio_button_4 = CTkRadioButton(alertframe, text="Colorado, US", variable=alert_var, value=3, state="disabled")
    radio_button_4.grid(row=1,column=3,padx=10,pady=10, sticky='w')
    alertframe.grid(row=1,column=0,padx=10,pady=5, sticky='n')
    alertButton = CTkButton(mainframe.tab("Alert"), text="Play Alert", font=CTkFont(size=bsize), width=bwidth, height=bheight, corner_radius=5, command=playAlert, state="disabled")
    alertButton.grid(row=2,column=0,padx=0,pady=(10,0))

    #Music
    mainframe.tab("Player").grid_columnconfigure(0,weight=1)
    mainframe.tab("Player").grid_rowconfigure(0,weight=1)
    mcontrolframe.grid_columnconfigure(1,weight=1)
    heading3 = CTkLabel(mcontrolframe, text="No Media Loaded", font=CTkFont(size=15))
    heading3.grid(row=0,column=1,columnspan=2,padx=10,pady=0,sticky='e')
    mcontrolsframe = CTkFrame(mcontrolframe, fg_color="transparent")
    mcontrolsframe.grid(row=0,column=0,padx=6,pady=7,sticky='w')
    musicframe = CTkScrollableFrame(mainframe.tab("Player"), bg_color="transparent", fg_color="transparent")
    musicframe.grid(row=0,column=0,padx=0,pady=0, sticky='nsew')
    musicframe.grid_columnconfigure(0,weight=1)
    musicframe.grid_rowconfigure(0,weight=1)
    load_button = CTkButton(mcontrolsframe, image=imgtk_folder, text="", width=10, height=8, corner_radius=10, command=load)
    load_button.grid(row=0,column=0,padx=3)
    link_button = CTkButton(mcontrolsframe, image=imgtk_link, text="", width=10, height=8, corner_radius=10, command=link, state="disabled",fg_color=("#2b6b8f","#0f4d67"))
    link_button.grid(row=0,column=1,padx=3)
    add_button = CTkButton(mcontrolsframe, image=imgtk_add, text="", width=10, height=8, corner_radius=10, command=addCmd,state="disabled",fg_color=("#2b6b8f","#0f4d67"))
    add_button.grid(row=0,column=2,padx=3)
    seek_button = CTkButton(mcontrolsframe, text=settings[13][:-1]+"s", font=CTkFont(size=13), width=38, height=32, corner_radius=4, command=lambda: seekAdjust(manual=True), state="disabled",fg_color=("#2b6b8f","#0f4d67"))
    seek_button.grid(row=0,column=3,padx=(3,2))
    stop_button = CTkButton(mcontrolsframe, image=imgtk_stop, text="", width=10, height=8, corner_radius=10, command=stop, state="disabled",fg_color=("#2b6b8f","#0f4d67"))
    stop_button.grid(row=0,column=4,padx=3)
    play_button = CTkButton(mcontrolsframe, image=imgtk_play, text="", width=10, height=8, corner_radius=10, command=play, state="disabled",fg_color=("#2b6b8f","#0f4d67"))
    play_button.grid(row=0,column=5,padx=3)
    music_slider = CTkSlider(mcontrolframe, from_=0, to=100, orientation="horizontal", progress_color="white", border_width=3, height=12, command=lambda e: set_music_slider(), state="disabled")
    music_slider.grid(row=1,column=0,columnspan=8,padx=8,pady=(5,2),sticky='ew')
    music_slider.set(0)
    actual_time = CTkLabel(mcontrolframe, text="00:00.0", font=CTkFont(size=12), height=3)
    actual_time.grid(row=2,column=0,padx=10,pady=(4,0), sticky='w')
    total_time = CTkLabel(mcontrolframe, text="00:00.0", font=CTkFont(size=12), height=3)
    total_time.grid(row=2,column=2,padx=10,pady=(4,0), sticky='e')
    musicframechild = CTkFrame(musicframe, fg_color="transparent")
    musicframechild.grid_columnconfigure(0,weight=1)
    musicframechild.grid_rowconfigure(0,weight=1)

    if settings[4][:-1]=="1":
        root.after(20,connect)
    if settings[5][:-1]=="1":
        bindBasic()
    if settings[6][:-1]=="1" and os.path.exists(settings[12][:-1]):
        load(True)

    root.mainloop()


if __name__ == "__main__":
    main()

