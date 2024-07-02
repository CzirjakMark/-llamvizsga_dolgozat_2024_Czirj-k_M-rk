import can
import time
import threading
import tkinter as tk
import math
import json
from datetime import datetime, timedelta
from tkinter import *
import random


#Konstans értékek inicializálása
max_speed = 250
max_rpm = 8000
acceleration_rate = 5
down_shift_deceleration_rate = 3
up_shift_decelerate_rpm_rate = 150
deceleration_rate = 0.4

current_speed = 0
current_rpm = 1100
previous_pedal_pos = 0
delta_time = 0.2
previous_gear = 0
down_shift_dec_counter = 10
up_shift_dec_counter = 10
released_pedal_counter = 5

down_shift = False
up_shift = False


#CAN busz inicializálása
can_interface = 'can0'
bus = can.interface.Bus(can_interface, bustype='socketcan', bitrate=500000)

#A JSON fájl elemeit tároló listák
distance_list = []
speed_list = []
str_wheel_angle_list = []
rpm_list = []


#Adatmentésre szolgáló JSON fájlok
distance_json_file = 'tavolsagok.json'
speed_json_file = 'sebesseg.json'
wheel_json_file = 'kormanyszog.json'
rpm_json_file = 'fordulatszam.json'

last_save_time = None



#A fordulatszámokat tartalmazó JSON fájl megnyitása és kiolvasása
def load_existing_rpm_data():
    global rpm_list
    if rpm_json_file and rpm_json_file != '':
        with open(rpm_json_file, 'r') as file:
            try:
                rpm_list = json.load(file)
            except json.JSONDecodeError:
                pass
    return rpm_list

#A távolságokat tartalmazó JSON fájl megnyitása és kiolvasása
def load_existing_distance_data():
    global distance_list
    if distance_json_file and distance_json_file != '':
        with open(distance_json_file, 'r') as file:
            try:
                distance_list = json.load(file)
            except json.JSONDecodeError:
                pass
    return distance_list

#A sebességet tartalmazó JSON fájl megnyitása és kiolvasása
def load_existing_speed_data():
    global speed_list
    if speed_json_file and speed_json_file != '':
        with open(speed_json_file, 'r') as file:
            try:
                speed_list = json.load(file)
            except json.JSONDecodeError:
                pass
    return speed_list

#A kormányszöget tartalmazó JSON fájl megnyitása és kiolvasása
def load_existing_angle_data():
    global str_wheel_angle_list
    if wheel_json_file and wheel_json_file != '':
        with open(wheel_json_file, 'r') as file:
            try:
                str_wheel_angle_list = json.load(file)
            except json.JSONDecodeError:
                pass
    return str_wheel_angle_list


#A sebesség értékének újraszámolására szolgáló függvény
def update_speed(brake_pedal_pos, pedal_position, current_speed, delta_time, gear):
    global previous_gear
    global down_shift
    global down_shift_dec_counter
    global released_pedal_counter

    #Lassulás
    def decelerate(speed, engine_idle):
        if gear == 255:
            return speed - (speed / 50)
        else:
            return speed - deceleration_rate

    #Lassulás visszaváltásnál
    def down_shift_decelerate(speed):
        return speed - down_shift_deceleration_rate

    #Gyorsítás 1-esben
    def accelerate1(speed, pedal_position, brake_pedal_pos, limit, engine_idle):
        if brake_pedal_pos > 0:
            return speed - (brake_pedal_pos / 20)
        deceleration_rate = 0.4
        if speed < limit:
            return speed + (pedal_position / 10)
        return speed

    #Gyorsítás 2-esben
    def accelerate2(speed, pedal_position, brake_pedal_pos, limit, engine_idle):
        if brake_pedal_pos > 0:
            return speed - (brake_pedal_pos / 20)
        deceleration_rate = 0.4
        if speed < limit:
            return speed + (pedal_position / 20)
        return speed

    #Gyorsítás 3-asban
    def accelerate3(speed, pedal_position, brake_pedal_pos, limit, engine_idle):
        if brake_pedal_pos > 0:
            return speed - (brake_pedal_pos / 20)
        deceleration_rate = 0.4
        if speed < limit:
            return speed + (pedal_position / 40)
        return speed

    #Gyorsítás 4-esben
    def accelerate4(speed, pedal_position, brake_pedal_pos, limit):
        if brake_pedal_pos > 0:
            return speed - (brake_pedal_pos / 20)
        deceleration_rate = 0.4
        if speed < limit:
            return speed + (pedal_position / 70)
        return speed

    # Gyorsítás 5-ösben
    def accelerate5(speed, pedal_position, brake_pedal_pos, limit):
        if brake_pedal_pos > 0:
            return speed - (brake_pedal_pos / 20)
        deceleration_rate = 0.4
        if speed < limit:
            return speed + (pedal_position / 80)
        return speed

    # Gyorsítás 6-osban
    def accelerate6(speed, pedal_position, brake_pedal_pos, limit):
        if brake_pedal_pos > 0:
            return speed - (brake_pedal_pos / 45)
        deceleration_rate = 0.4
        if speed < limit:
            return speed + (pedal_position / 90)
        return speed

    # Gyorsítás tolatáskor
    def accelerate_backward(speed, pedal_position, limit):
        if speed < limit:
            return speed + (pedal_position / 100)
        return speed
    # A váltókar, a pedálok állása és az aktuális sebesség alapján itt dől el, hogy az autó hogyan gyorsul vagy lassul ezután
    gear_limits = {
        0: lambda speed, pedal_position, brake_pedal_pos: decelerate(speed, 15),
        1: lambda speed, pedal_position, brake_pedal_pos: accelerate1(speed, pedal_position, brake_pedal_pos, 45, 10),
        2: lambda speed, pedal_position, brake_pedal_pos: accelerate2(speed, pedal_position, brake_pedal_pos, 75, 15),
        3: lambda speed, pedal_position, brake_pedal_pos: accelerate3(speed, pedal_position, brake_pedal_pos, 110, 15),
        4: lambda speed, pedal_position, brake_pedal_pos: accelerate4(speed, pedal_position, brake_pedal_pos, 160),
        5: lambda speed, pedal_position, brake_pedal_pos: accelerate5(speed, pedal_position, brake_pedal_pos, 220),
        6: lambda speed, pedal_position, brake_pedal_pos: accelerate6(speed, pedal_position, brake_pedal_pos, 250),
        255: lambda speed, pedal_position: accelerate_backward(speed, pedal_position, brake_pedal_pos, 45),
    }

    if pedal_position > 0:
        new_speed = gear_limits.get(gear, lambda speed, pedal_position, brake_pedal_pos: speed)(current_speed,
                                                                                                pedal_position,
                                                                                                brake_pedal_pos)
    elif pedal_position == 0 and down_shift == True and gear > 0:
        new_speed = down_shift_decelerate(current_speed)
        down_shift_dec_counter -= 1
        if down_shift_dec_counter == 0:
            down_shift = False
            down_shift_dec_counter = 10
    else:
        new_speed = decelerate(current_speed, 15)

    if brake_pedal_pos > 0:
        new_speed = gear_limits.get(gear, lambda speed, pedal_position, brake_pedal_pos: speed)(current_speed,
                                                                                                pedal_position,
                                                                                                brake_pedal_pos)

    new_speed = max(0, min(new_speed, max_speed))

    return new_speed

#A fordulatszám értékének újraszámolására szolgáló függvény
def update_rpm(brake_pedal_pos, pedal_position, current_rpm, current_speed, delta_time, gear):
    global previous_gear
    global down_shift
    global up_shift
    global down_shift_dec_counter
    global up_shift_dec_counter
    global released_pedal_counter

    last_gear = gear

    #Fordulatszám csökkenése amikor az autó nincs sebességben
    def rpm_down_in_neutral(rpm):
        if rpm > 1200:
            return rpm - 200
        return rpm

    #Fordulatszám csökkenése amikor nincs lenyomva egy pedál sem
    def rpm_down(rpm, current_speed, idle_rpm, maxrpm, maxspeed):
        if rpm > 1200 and current_speed > 0:
            return rpm - (1000 / current_speed)
        return rpm

    #Fordulatszám csökkenése amikor váltás történik
    def down_shift_rpm(rpm, gear):
        if rpm > 1200:
            return rpm - 90
        return rpm

    #Fordulatszám csökkenése amikor felfele váltás történik
    def up_shift_rpm(rpm):
        if rpm > 1200:
            return rpm - up_shift_decelerate_rpm_rate
        return rpm

    #Fordulatszám növekedése amikor az autó nincs sebességben
    def rpm_up_in_neutral(rpm, pedal_position, brake_pedal_pos):
        return (pedal_position * 70 + 1100)

    #Fordulatszám változása 1-esben
    def rpm_up1(rpm, pedal_position, brake_pedal_pos):
        if brake_pedal_pos > 0 and rpm > 1100:
            return rpm - (brake_pedal_pos * 5)
        return rpm + (pedal_position * 3)

    # Fordulatszám változása 2-esben
    def rpm_up2(rpm, pedal_position, brake_pedal_pos):
        if brake_pedal_pos > 0 and rpm > 1100:
            return rpm - (brake_pedal_pos * 5)
        return rpm + (pedal_position)

    # Fordulatszám változása 3-esben
    def rpm_up3(rpm, pedal_position, brake_pedal_pos):
        if brake_pedal_pos > 0 and rpm > 1100:
            return rpm - (brake_pedal_pos * 5)
        return rpm + (pedal_position)
        # A váltókar, a pedálok állása és az aktuális fordulatszám alapján itt dől el, hogy az autó fordulatszáma hogy nő vagy csökken
    gear_limits = {
        0: lambda rpm, pedal_position, brake_pedal_pos: rpm_up_in_neutral(rpm, pedal_position, brake_pedal_pos),
        1: lambda rpm, pedal_position, brake_pedal_pos: rpm_up1(rpm, pedal_position, brake_pedal_pos),
        2: lambda rpm, pedal_position, brake_pedal_pos: rpm_up2(rpm, pedal_position, brake_pedal_pos),
        3: lambda rpm, pedal_position, brake_pedal_pos: rpm_up3(rpm, pedal_position, brake_pedal_pos),
        4: lambda rpm, pedal_position, brake_pedal_pos: rpm_up3(rpm, pedal_position, brake_pedal_pos),
        5: lambda rpm, pedal_position, brake_pedal_pos: rpm_up3(rpm, pedal_position, brake_pedal_pos),
        6: lambda rpm, pedal_position, brake_pedal_pos: rpm_up3(rpm, pedal_position, brake_pedal_pos),
    }

    if pedal_position > 0:
        new_rpm = gear_limits.get(gear, lambda rpm, pedal_position, brake_pedal_pos: rpm)(current_rpm, pedal_position,
                                                                                          brake_pedal_pos)
    elif pedal_position == 0 and down_shift == True and gear > 1:
        new_rpm = down_shift_rpm(current_rpm, gear)
        if down_shift_dec_counter == 0:
            down_shift = False
            down_shift_dec_counter = 10
    elif pedal_position == 0 and up_shift == True and gear > 1:
        new_rpm = up_shift_rpm(current_rpm)
        up_shift_dec_counter -= 1
        if up_shift_dec_counter == 0:
            up_shift = False
            up_shift_dec_counter = 10

    else:
        if gear == 0:
            new_rpm = rpm_down_in_neutral(current_rpm)
        else:
            new_rpm = rpm_down(current_rpm, current_speed, 1000, 8000, 250)

    if brake_pedal_pos > 0:
        new_rpm = gear_limits.get(gear, lambda rpm, pedal_position, brake_pedal_pos: rpm)(current_rpm, pedal_position,
                                                                                          brake_pedal_pos)

    new_rpm = max(0, min(new_rpm, max_rpm))

    if last_gear != gear:
        new_rpm = new_rpm - 1000

    return new_rpm


show_parking_distances = False


#A műszerfal ECU itt fogadja a CAN üzeneteket, amelyek neki vannak szánva, amelyből a sebesség, fordulatszám és kormányelfordulás kiszámítható
def receive_can_messages(bus, rain_label, front_wiper_label, back_wiper_label, gear_label, kormany_label, speedometer,
                         rpm_meter,
                         turn_indicator):
    global show_parking_distances
    global current_speed
    global current_rpm
    global delta_time
    global previous_gear
    global down_shift
    global up_shift
    global down_shift_dec_counter

    front_wiper_on = False
    back_wiper_on = False
    front_wiper_prev = 0
    back_wiper_prev = 0

    while True:
        # A CAN busz figyelése, hogy érkezik-e üzenet
        message = bus.recv()
        if message:
            #A bejövő üzenetek azonosítójának és a benne tárolt jelek számának ellenörzése
            if message.arbitration_id == 0x04 and len(message.data) == 3:
                front_wiper = message.data[1]
                back_wiper = message.data[0]

                gear = message.data[2]
                if previous_gear > gear:
                    down_shift = True
                if previous_gear < gear:
                    up_shift = True
                previous_gear = gear

                if front_wiper == 1:
                    if front_wiper_prev == 0:
                        front_wiper_on = not front_wiper_on
                front_wiper_prev = front_wiper

                if back_wiper == 1:
                    if back_wiper_prev == 0:
                        back_wiper_on = not back_wiper_on
                back_wiper_prev = back_wiper

                front_wiper_label.config(text=f"Front wiper: {'ON' if front_wiper_on else 'OFF'}")
                back_wiper_label.config(text=f"Back wiper: {'ON' if back_wiper_on else 'OFF'}")

                # A váltókar állásának frissítése
                if gear >= 0 and gear < 7:
                    gear_label.config(text=f"{gear}")
                else:
                    gear_label.config(text=f"R")

            # A bejövő üzenetek azonosítójának és a benne tárolt jelek számának ellenörzése
            elif message.arbitration_id == 0x05 and len(message.data) == 3:

                #Az aktuális dátum és idő meghatározása az időbélyeg számára
                current_time = datetime.now()

                #A már elmentett kormányszög adatok betöltése
                str_wheel_angle_list = load_existing_angle_data()

                #Kormányszög beolvasása
                kormany = message.data[0]

                #Kormányszög értékének és az időbélyegnek listához való fűzése
                str_wheel_angle_list.append({
                    "angle": kormany,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                })

                #Ha nagyobb érték érkezik a pedáltól mint 90, akkor az maradjon 90, mert a sebesség számítás maximum 90-es pedálállással van kiszámolva
                if message.data[1] > 90:
                    gaz = 90
                else:
                    gaz = message.data[1]
                fek = message.data[2]
                kormany_label.config(text=f"Angle: {kormany} ")

                pedal_position = gaz
                brake_pedal_pos = fek

                #A már elmentett sebesség és fordulatszám adatok betöltése
                speed_list = load_existing_speed_data()
                rpm_list = load_existing_rpm_data()

                #A sebesség és fordulatszám értékének újraszámolása
                current_speed = update_speed(brake_pedal_pos, pedal_position, current_speed, delta_time, gear)
                current_rpm = update_rpm(brake_pedal_pos, pedal_position, current_rpm, current_speed, delta_time, gear)

                #A sebesség és fordulatszám időbélyeggel való listához fűzése
                speed_list.append({
                    "speed": current_speed,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                })

                rpm_list.append({
                    "rpm": current_rpm,
                    "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                })

                # Adatok hozzáírása a JSON fájl végére
                with open(speed_json_file, 'w') as file:
                    json.dump(speed_list, file, indent=4, separators=(',', ': '))

                with open(rpm_json_file, 'w') as file:
                    json.dump(rpm_list, file, indent=4, separators=(',', ': '))

                with open(wheel_json_file, 'w') as file:
                    json.dump(str_wheel_angle_list, file, indent=4, separators=(',', ': '))
                speedometer.update_speed(current_speed)
                rpm_meter.update_rpm(current_rpm)

                turn_indicator.update_angle(kormany)

#A műszerfal által kiszámolt sebesség érték CAN üzenetben való továbbküldése a Kormány ECU számára
def send_can_messages():
    global current_speed
    while True:
        speed_data = [int(current_speed)]
        message = can.Message(arbitration_id=0x06, data=speed_data, is_extended_id=False)
        try:
            bus.send(message)
            print(f"Sent speed message: {speed_data[0]}")
        except can.CanError as e:
            print(f"Failed to send message: {e}")
        time.sleep(0.1)


#A grafikai megvalósítása a sebességmérőnek
class Speedometer(tk.Canvas):
    def __init__(self, parent, max_speed=250, width=300, height=300, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self.max_speed = max_speed
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.radius = min(self.center_x, self.center_y) - 20

        self.create_oval(20, 20, width - 20, height - 20, width=3)

        self.speed_labels = self.create_speed_labels()

        self.speed_text = self.create_text(self.center_x - 40, self.center_y + 40, text="0 km/h",
                                           font=("Helvetica", 12), fill='red')

        self.pointer = None

        self.update_speed(0)

    def create_speed_labels(self):
        for i in range(0, self.max_speed + 1, 10):
            angle = (i / self.max_speed) * 270
            angle_rad = math.radians(180 - angle)

            if i % 20 == 0:
                label_x = self.center_x + (self.radius - 20) * math.cos(angle_rad)
                label_y = self.center_y - (self.radius - 20) * math.sin(angle_rad)
                self.create_text(label_x, label_y, text=str(i), font=("Helvetica", 8, "bold"))

            tick_start_x = self.center_x + self.radius * math.cos(angle_rad)
            tick_start_y = self.center_y - self.radius * math.sin(angle_rad)
            tick_end_x = self.center_x + (self.radius - 10) * math.cos(angle_rad)
            tick_end_y = self.center_y - (self.radius - 10) * math.sin(angle_rad)
            self.create_line(tick_start_x, tick_start_y, tick_end_x, tick_end_y, width=4)

    def update_speed(self, speed):
        speed = max(0, min(speed, self.max_speed))
        angle = (speed / self.max_speed) * 270

        angle_rad = math.radians(180 - angle)

        pointer_length = self.radius - 10
        end_x = self.center_x + pointer_length * math.cos(angle_rad)
        end_y = self.center_y - pointer_length * math.sin(angle_rad)

        if self.pointer:
            self.delete(self.pointer)

        self.pointer = self.create_line(self.center_x, self.center_y, end_x, end_y, width=3, fill='red')

        self.itemconfig(self.speed_text, text=f"{int(speed)} km/h")


#A grafikai megvalósítása a fordulatszám mérőnek
class RPMMeter(tk.Canvas):
    def __init__(self, parent, max_rpm=8000, width=200, height=200, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self.max_rpm = max_rpm
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.radius = min(self.center_x, self.center_y) - 20

        self.create_oval(20, 20, width - 20, height - 20, width=3)

        self.rpm_labels = self.create_rpm_labels()

        self.rpm_text = self.create_text(self.center_x, self.center_y + 40, text="0 RPM",
                                         font=("Helvetica", 12), fill='red')

        self.create_oval(self.center_x - 10, self.center_y - 10,
                         self.center_x + 10, self.center_y + 10, fill='black')

        self.pointer = None

        self.update_rpm(0)

    def create_rpm_labels(self):
        for i in range(0, self.max_rpm + 1, 1000):
            angle = (i / self.max_rpm) * 180
            angle_rad = math.radians(180 - angle)

            label_x = self.center_x + (self.radius - 23) * math.cos(angle_rad)
            label_y = self.center_y - (self.radius - 23) * math.sin(angle_rad)
            self.create_text(label_x, label_y, text=str(i), font=("Helvetica", 8, "bold"))

            # Calculate tick mark end coordinates
            tick_start_x = self.center_x + self.radius * math.cos(angle_rad)
            tick_start_y = self.center_y - self.radius * math.sin(angle_rad)
            tick_end_x = self.center_x + (self.radius - 10) * math.cos(angle_rad)
            tick_end_y = self.center_y - (self.radius - 10) * math.sin(angle_rad)
            self.create_line(tick_start_x, tick_start_y, tick_end_x, tick_end_y, width=4)

    def update_rpm(self, rpm):
        rpm = max(0, min(rpm, self.max_rpm))
        angle = (rpm / self.max_rpm) * 180

        angle_rad = math.radians(180 - angle)

        pointer_length = self.radius - 10
        end_x = self.center_x + pointer_length * math.cos(angle_rad)
        end_y = self.center_y - pointer_length * math.sin(angle_rad)

        if self.pointer:
            self.delete(self.pointer)

        self.pointer = self.create_line(self.center_x, self.center_y, end_x, end_y, width=3, fill='red')

        self.itemconfig(self.rpm_text, text=f"{int(rpm)} RPM")


#A grafikai megvalósítása a kormányelfordulás mérőnek
class Turn_indicator(tk.Canvas):
    def __init__(self, parent, max_speed=180, width=200, height=200, **kwargs):
        super().__init__(parent, width=width, height=height, **kwargs)
        self.max_speed = max_speed
        self.width = width
        self.height = height
        self.center_x = width // 2
        self.center_y = height // 2
        self.radius1 = min(self.center_x, self.center_y) - 40
        self.radius2 = min(self.center_x, self.center_y) - 20

        self.pointer1 = None
        self.pointer2 = None

        self.update_angle(90)

    def update_angle(self, speed):
        speed = max(0, min(speed, self.max_speed))
        angle = (speed / self.max_speed) * 120 - 60

        angle_rad = math.radians(90 - angle)

        pointer_length = self.radius2
        offset = 20

        end_x1 = self.center_x + pointer_length * math.cos(angle_rad)
        end_y1 = self.center_y - pointer_length * math.sin(angle_rad)

        end_x2 = self.center_x + pointer_length * math.cos(angle_rad)
        end_y2 = self.center_y - pointer_length * math.sin(angle_rad)

        if self.pointer1:
            self.delete(self.pointer1)

        if self.pointer2:
            self.delete(self.pointer2)

        self.pointer1 = self.create_line(self.center_x - offset, self.center_y, end_x1 - offset, end_y1, width=6,
                                         fill='blue')

        self.pointer2 = self.create_line(self.center_x + offset, self.center_y, end_x2 + offset, end_y2, width=6,
                                         fill='blue')

#A grafikai felület fő oldalának és azon belül a sebességet,fordulatszámot, kormányszöget, valamint a távolság indikátorokat tartalmazó oldal létrehozása
class Root(tk.Tk):
    def __init__(self):
        super().__init__()
        self.geometry("800x410")
        self.title("CAN DATA DISPLAY")
        self.first_page = None
        self.initialize_first_page()
        self.second_page_threads = []
        self.stop_event = threading.Event()
        self.top_left_table = []
        self.top_right_table = []
        self.bottom_left_table = []
        self.bottom_right_table = []

    def initialize_first_page(self):
        self.first_page = tk.Frame(self)
        self.first_page.pack(fill=tk.BOTH, expand=True)
        self.create_first_page()

    # A sebességet,fordulatszámot, kormányszöget tartalmazó oldal létrehozása
    def create_first_page(self):
        self.first_page = tk.Frame(self)
        self.first_page.pack(fill=tk.BOTH, expand=True)

        left_frame = tk.Frame(self.first_page, width=200, height=200)
        left_frame.pack(side=tk.LEFT, padx=0, pady=0)

        right_frame = tk.Frame(self.first_page, width=200, height=200)
        right_frame.pack(side=tk.RIGHT, padx=0, pady=0)

        center_frame = tk.Frame(self.first_page, width=200, height=200)
        center_frame.pack(side=tk.LEFT, padx=0, pady=0, expand=True, fill=tk.BOTH)

        canvas_center = tk.Canvas(center_frame, width=200, height=58, highlightthickness=0)
        canvas_center.pack(pady=10)

        arrow_left = canvas_center.create_polygon(26, 30, 45, 30, 45, 15, 60, 37, 45, 60, 45, 45, 26, 45,
                                                  fill='gray')
        arrow_right = canvas_center.create_polygon(174, 30, 155, 30, 155, 15, 140, 37, 155, 60, 155, 45, 174, 45,
                                                   fill='gray')

        canvas_center.move(arrow_right, -140, 0)
        canvas_center.move(arrow_left, 138, 0)

        turn_indicator_frame = tk.Frame(center_frame, borderwidth=7, relief="raised", bg="grey")
        turn_indicator_frame.pack(padx=10, pady=20, anchor=tk.E)
        turn_indicator = Turn_indicator(turn_indicator_frame, max_speed=180, width=200, height=150, )
        turn_indicator.pack()

        gear_label = tk.Label(self, text="Gear: ", font=("Helvetica", 16))
        gear_label.pack(padx=110, pady=0, anchor=tk.W, in_=center_frame)

        parking_button = tk.Button(self, text="Parking", font=("Helvetica", 14), command=self.switch_to_second_page)
        parking_button.pack(padx=85, pady=0, anchor=tk.W, in_=center_frame)

        rain_label = tk.Label(left_frame, text="Rain: ", font=("Helvetica", 16))

        front_wiper_label = tk.Label(left_frame, text="Front wiper state:", font=("Helvetica", 16))

        back_wiper_label = tk.Label(left_frame, text="Back wiper state: ", font=("Helvetica", 16))

        kormany_label = tk.Label(turn_indicator_frame, text="Angle: ", font=("Helvetica", 10))
        kormany_label.pack(side=tk.TOP, padx=60, pady=10)

        rpm_frame = tk.Frame(left_frame)
        rpm_frame.pack(pady=10)
        rpm_meter = RPMMeter(rpm_frame, max_rpm=8000, width=280, height=280)
        rpm_meter.pack()

        speedometer_frame = tk.Frame(right_frame)
        speedometer_frame.pack(pady=10)
        speedometer = Speedometer(speedometer_frame, max_speed=240, width=280, height=280)
        speedometer.pack()

        threading.Thread(target=receive_can_messages, args=(
            bus, rain_label, front_wiper_label, back_wiper_label, gear_label, kormany_label, speedometer, rpm_meter,
            turn_indicator),
                         daemon=True).start()

    def switch_to_second_page(self):
        self.second_page_window = tk.Toplevel(self)
        self.second_page_window.geometry("800x410")
        self.second_page_window.title("Second Page")
        self.create_second_page(self.second_page_window)

    # A távolság indikátorokat tartalmazó oldal létrehozása
    def create_second_page(self, window):

        left_frame = Frame(window, width=100, bg='gray')
        left_frame.pack(side=LEFT, fill=Y)

        right_frame = Frame(window, width=100, bg='gray')
        right_frame.pack(side=RIGHT, fill=Y)

        central_frame = Frame(window, bg='white')
        central_frame.pack(expand=True, fill=BOTH)

        top_frame = Frame(central_frame, bg='white')
        top_frame.pack(side=TOP, fill=X, pady=10)

        top_left_frame = Frame(top_frame, bg='white')
        top_left_frame.pack(side=LEFT, padx=10)

        self.top_left_table = []
        for i in range(4):
            if i == 0:
                cell = Label(top_left_frame, relief="solid", width=10, height=1)
            elif i == 1:
                cell = Label(top_left_frame, relief="solid", width=6, height=1)
            elif i == 2:
                cell = Label(top_left_frame, relief="solid", width=4, height=1)
            elif i == 3:
                cell = Label(top_left_frame, relief="solid", width=2, height=1)
            cell.pack(pady=5, padx=85)
            self.top_left_table.append(cell)

        top_right_frame = Frame(top_frame, bg='white')
        top_right_frame.pack(side=LEFT, padx=10)

        self.top_right_table = []
        for i in range(4):
            if i == 0:
                cell = Label(top_right_frame, relief="solid", width=10, height=1)
            elif i == 1:
                cell = Label(top_right_frame, relief="solid", width=6, height=1)
            elif i == 2:
                cell = Label(top_right_frame, relief="solid", width=4, height=1)
            elif i == 3:
                cell = Label(top_right_frame, relief="solid", width=2, height=1)
            cell.pack(pady=5)
            self.top_right_table.append(cell)

        middle_frame = Frame(central_frame, bg='white')
        middle_frame.pack(side=TOP, fill=X, pady=10)

        bottom_frame = Frame(central_frame, bg='white')
        bottom_frame.pack(side=TOP, fill=X, pady=10)

        bottom_left_frame = Frame(bottom_frame, bg='white')
        bottom_left_frame.pack(side=LEFT, padx=10, pady=30)

        self.bottom_left_table = []
        for i in range(4):
            if i == 0:
                cell = Label(bottom_left_frame, relief="solid", width=2, height=1)
            elif i == 1:
                cell = Label(bottom_left_frame, relief="solid", width=4, height=1)
            elif i == 2:
                cell = Label(bottom_left_frame, relief="solid", width=6, height=1)
            elif i == 3:
                cell = Label(bottom_left_frame, relief="solid", width=10, height=1)
            cell.pack(pady=5, padx=85)
            self.bottom_left_table.append(cell)

        bottom_right_frame = Frame(bottom_frame, bg='white')
        bottom_right_frame.pack(side=LEFT, padx=10, pady=30)

        self.bottom_right_table = []
        for i in range(4):
            if i == 0:
                cell = Label(bottom_right_frame, relief="solid", width=2, height=1)
            elif i == 1:
                cell = Label(bottom_right_frame, relief="solid", width=4, height=1)
            elif i == 2:
                cell = Label(bottom_right_frame, relief="solid", width=6, height=1)
            elif i == 3:
                cell = Label(bottom_right_frame, relief="solid", width=10, height=1)
            cell.pack(pady=5)
            self.bottom_right_table.append(cell)

        parking_done_button = tk.Button(right_frame, text="Parking Done", command=self.close_second_page,
                                        font=("Helvetica", 16))
        parking_done_button.pack(side=tk.TOP, padx=10, pady=180)

        fld_label = tk.Label(right_frame, text="F L Distance: ", font=("Helvetica", 12))
        fld_label.pack(padx=10, pady=10)

        frd_label = tk.Label(right_frame, text="F R Distance: ", font=("Helvetica", 12))
        frd_label.pack(padx=10, pady=10)

        bld_label = tk.Label(right_frame, text="B L Distance: ", font=("Helvetica", 12))
        bld_label.pack(padx=10, pady=10)

        brd_label = tk.Label(right_frame, text="B R Distance: ", font=("Helvetica", 12))
        brd_label.pack(padx=10, pady=10)

        thread = threading.Thread(target=self.receive_can_messages2,
                                  args=(fld_label, frd_label, bld_label, brd_label),
                                  daemon=True)
        thread.start()
        self.second_page_threads.append(thread)

    # A műszerfal ECU itt fogadja azt a CAN üzenetet, amely a távolság indikátorok működéséhez szükséges távolságokay tartalmazza
    def receive_can_messages2(self, fld_label, frd_label, bld_label, brd_label):
        global last_save_time
        while True:
            # A CAN busz figyelése, hogy érkezik-e üzenet
            message = bus.recv()
            if message:
                # A bejövő üzenetek azonosítójának és a benne tárolt jelek számának ellenörzése
                if message.arbitration_id == 0x02 and len(message.data) == 4:

                    # A már elmentett távolság adatok betöltése
                    distance_list = load_existing_distance_data()

                    # A négy távolságérzékelő mért értékenek eltárolása
                    fld = message.data[0]
                    frd = message.data[1]
                    bld = message.data[2]
                    brd = message.data[3]

                    # Az indikátorok kiröltésének és színének változtatása a távolságok függvényében
                    self.update_table_colors(fld, frd, bld, brd)
                    #Időbélyeg eltárolása
                    current_time = datetime.now()

                    # A távolságok időbélyeggel való listához fűzése
                    if last_save_time is None or (current_time - last_save_time) >= timedelta(seconds=1):
                        # Új adat hozzáadása a listához időbélyeggel
                        distance_list.append({
                            "fld": fld,
                            "frd": frd,
                            "bld": bld,
                            "brd": brd,
                            "timestamp": current_time.strftime("%Y-%m-%d %H:%M:%S")
                        })

                        # Távolságok hozzáírása a JSON fájl végére
                        with open(distance_json_file, 'w') as file:
                            json.dump(distance_list, file, indent=4, separators=(',', ': '))

                        # Az utolsó mentés időpontjának frissítése
                        last_save_time = current_time

    #Az indikátorok színének változtatása
    def update_table_colors(self, fld, frd, bld, brd):
        self.update_cell_color(self.top_left_table, fld)
        self.update_cell_color(self.top_right_table, frd)
        self.update_cell_color2(self.bottom_left_table, bld)
        self.update_cell_color2(self.bottom_right_table, brd)

    # Az indikátorokhoz tartozó cellák színének változtatása
    def update_cell_color(self, table, value):
        for i, cell in enumerate(table):
            if value > 15:
                cell.config(bg='green')
            elif 10 < value <= 15:
                if i == 0:
                    cell.config(bg='white')
                else:
                    cell.config(bg='yellow')
            elif 5 < value <= 10:
                if i < 2:
                    cell.config(bg='white')
                else:
                    cell.config(bg='orange')
            else:
                if i < 3:
                    cell.config(bg='white')
                else:
                    cell.config(bg='red')

    # Az indikátorokhoz tartozó cellák színének változtatása 
    def update_cell_color2(self, table, value):
        for i, cell in enumerate(table):
            if value > 15:
                cell.config(bg='green')
            elif 10 < value <= 15:
                if i == 3:
                    cell.config(bg='white')
                else:
                    cell.config(bg='yellow')
            elif 5 < value <= 10:
                if i > 1:
                    cell.config(bg='white')
                else:
                    cell.config(bg='orange')
            else:
                if i > 0:
                    cell.config(bg='white')
                else:
                    cell.config(bg='red')

    def close_second_page(self):
        self.second_page_window.destroy()

#A grafikus interfész létrehozásáért felelős függvény + a CAN üzenet továbbítását végző szál elindítása
def create_GUI():
    root = Root()
    threading.Thread(target=send_can_messages, daemon=True).start()
    root.mainloop()

if __name__ == "__main__":
    try:
        print("Starting to recieve CAN messages...")
        create_GUI()
    except KeyboardInterrupt:
        print("Stopped receiving CAN messages")