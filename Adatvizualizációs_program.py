import json
import matplotlib.pyplot as plt
from tkinter import *
from tkinter import ttk
from datetime import datetime, timedelta

# Alapértelmezett JSON fájlok
json_files = {
    'Távolságok': 'tavolsagok.json',
    'Sebesség': 'sebesseg.json',
    'Fordulatszám': 'fordulatszam.json',
    'Kormányszög': 'kormanyszog.json'
}

# Alapértelmezett adatforrás
selected_data_source = 'Távolságok'

# Globális változók
data_source_combo = None
root = None
error_message = None


# Alapértelmezett JSON fájlból adatok beolvasása
def load_data():
    selected_source = data_source_combo.get()
    with open(json_files[selected_source], 'r') as file:
        data = json.load(file)
    return data

# A JSON fájl adatainak betöltése
def load_values(data):
    fld_values = [entry['fld'] for entry in data]
    frd_values = [entry['frd'] for entry in data]
    bld_values = [entry['bld'] for entry in data]
    brd_values = [entry['brd'] for entry in data]
    return fld_values, frd_values, bld_values, brd_values

# A beviteli mezők alapján történő vonaldiagram kirajzolásáért felelős függvény
def plot_graph():
    global data_source_combo

    if not data_source_combo:
        return

    # A beviteli mezőben megadott dátumok kiolvasása
    start_date_str = start_date_entry.get()
    end_date_str = end_date_entry.get()

    # Hibaüzenet alaphelyzetbe állítása
    error_message.set("")

    try:
        start_date = datetime.strptime(start_date_str, "%Y-%m-%d %H:%M:%S")
        end_date = datetime.strptime(end_date_str, "%Y-%m-%d %H:%M:%S")

        # A lenyíló listában kiválasztott elem ellenörzése
        if data_source_combo.get() == 'Távolságok':

            data = load_data()

            filtered_data = []
            filtered_x_values = []
            for entry in data:
                if 'timestamp' in entry:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                    if start_date <= entry_date <= end_date:
                        filtered_data.append(entry)
                        filtered_x_values.append(entry_date)

            if not filtered_data:
                raise ValueError("Nem található adat a megadott időintervallumban.")

            # Külön-külön listák a szűrt távolságértékhez
            fld_values_filtered, frd_values_filtered, bld_values_filtered, brd_values_filtered = load_values(
                filtered_data)

            # Ellenőrzés, hogy a megadott dátumra van-e adat
            date_range = []
            date = start_date
            while date <= end_date:
                date_range.append(date.date())
                date += timedelta(days=1)

            for day in date_range:
                found_data = False
                for entry in filtered_data:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S").date()
                    if day == entry_date:
                        found_data = True
                        break
                if not found_data:
                    raise ValueError(f"Nem található adat a következő dátumon: {day}")

            # Vonaldiagram készítése
            plt.figure(figsize=(10, 6))
            plt.plot(filtered_x_values, fld_values_filtered, label='Bal első távolság', marker='o', linestyle='-',
                     linewidth=2)
            plt.plot(filtered_x_values, frd_values_filtered, label='Jobb első távolság', marker='o', linestyle='-',
                     linewidth=2)
            plt.plot(filtered_x_values, bld_values_filtered, label='Bal hátsó távolság', marker='o', linestyle='-',
                     linewidth=2)
            plt.plot(filtered_x_values, brd_values_filtered, label='Jobb hátsó távolság', marker='o', linestyle='-',
                     linewidth=2)

            # Diagram cím és tengelyfeliratok
            plt.title('A távolságok időbeli változása')
            plt.xlabel('Idő')
            plt.ylabel('Távolság')

            plt.legend()

            # Rácsvonalak
            plt.grid(True)

            plt.gca().set_prop_cycle(None)
            plt.plot(filtered_x_values, fld_values_filtered, marker='o', linestyle='-', linewidth=2, alpha=0.7)
            plt.plot(filtered_x_values, frd_values_filtered, marker='o', linestyle='-', linewidth=2, alpha=0.7)
            plt.plot(filtered_x_values, bld_values_filtered, marker='o', linestyle='-', linewidth=2, alpha=0.7)
            plt.plot(filtered_x_values, brd_values_filtered, marker='o', linestyle='-', linewidth=2, alpha=0.7)

        # A lenyíló listában kiválasztott elem ellenörzése
        elif data_source_combo.get() == 'Sebesség':

            data = load_data()

            filtered_data = []
            filtered_x_values = []
            for entry in data:
                if 'timestamp' in entry:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                    if start_date <= entry_date <= end_date:
                        filtered_data.append(entry)
                        filtered_x_values.append(entry_date)

            if not filtered_data:
                raise ValueError("Nem található adat a megadott időintervallumban.")

            # Külön-külön listák a szűrt sebességértékhez
            speed_values_filtered = [entry['speed'] for entry in filtered_data]

            # Ellenőrzés, hogy a megadott dátumra van-e adat
            date_range = []
            date = start_date
            while date <= end_date:
                date_range.append(date.date())
                date += timedelta(days=1)
            # Ellenőrzés, hogy a megadott dátumra van-e adat
            for day in date_range:
                found_data = False
                for entry in filtered_data:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S").date()
                    if day == entry_date:
                        found_data = True
                        break
                if not found_data:
                    raise ValueError(f"Nem található adat a következő dátumon: {day}")

            # Vonaldiagram készítése
            plt.figure(figsize=(10, 6))
            plt.plot(filtered_x_values, speed_values_filtered, label='Sebesség', marker='o', linestyle='-',
                     linewidth=2, color='orange')

            # Diagram cím és tengelyfeliratok
            plt.title('Speed Over Time')
            plt.xlabel('Time')
            plt.ylabel('Speed')

            plt.legend()

            # Rácsvonalak
            plt.grid(True)
        # A lenyíló listában kiválasztott elem ellenörzése
        elif data_source_combo.get() == 'Kormányszög':

            data = load_data()

            filtered_data = []
            filtered_x_values = []
            for entry in data:
                if 'timestamp' in entry:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                    if start_date <= entry_date <= end_date:
                        filtered_data.append(entry)
                        filtered_x_values.append(entry_date)

            if not filtered_data:
                raise ValueError("Nem található adat a megadott időintervallumban.")

            # Külön-külön listák a szűrt sebességértékhez
            speed_values_filtered = [entry['angle'] for entry in filtered_data]

            # Ellenőrzés, hogy a megadott dátumra van-e adat
            date_range = []
            date = start_date
            while date <= end_date:
                date_range.append(date.date())
                date += timedelta(days=1)

            for day in date_range:
                found_data = False
                for entry in filtered_data:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S").date()
                    if day == entry_date:
                        found_data = True
                        break
                if not found_data:
                    raise ValueError(f"Nem található adat a következő dátumon: {day}")

            # Vonaldiagram készítése
            plt.figure(figsize=(10, 6))
            plt.plot(filtered_x_values, speed_values_filtered, label='Kormányszög', marker='o', linestyle='-',
                     linewidth=2, color='blue')

            # Diagram cím és tengelyfeliratok
            plt.title('Angle Over Time')
            plt.xlabel('Idő')
            plt.ylabel('Kormányszög')

            plt.legend()

            # Rácsvonalak
            plt.grid(True)

        # A lenyíló listában kiválasztott elem ellenörzése
        elif data_source_combo.get() == 'Fordulatszám':

            data = load_data()

            filtered_data = []
            filtered_x_values = []
            for entry in data:
                if 'timestamp' in entry:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S")
                    if start_date <= entry_date <= end_date:
                        filtered_data.append(entry)
                        filtered_x_values.append(entry_date)

            if not filtered_data:
                raise ValueError("Nem található adat a megadott időintervallumban.")

            # Külön-külön listák a szűrt sebességértékhez
            speed_values_filtered = [entry['rpm'] for entry in filtered_data]

            date_range = []
            date = start_date
            while date <= end_date:
                date_range.append(date.date())
                date += timedelta(days=1)

            for day in date_range:
                found_data = False
                for entry in filtered_data:
                    entry_date = datetime.strptime(entry['timestamp'], "%Y-%m-%d %H:%M:%S").date()
                    if day == entry_date:
                        found_data = True
                        break
                if not found_data:
                    raise ValueError(f"Nem található adat a következő dátumon: {day}")

            # Vonaldiagram készítése
            plt.figure(figsize=(10, 6))
            plt.plot(filtered_x_values, speed_values_filtered, label='Fordulatszám', marker='o', linestyle='-',
                     linewidth=2, color='red')

            # Diagram cím és tengelyfeliratok
            plt.title('RPM Over Time')
            plt.xlabel('Idő')
            plt.ylabel('RPM')

            plt.legend()

            # Rácsvonalak
            plt.grid(True)

        # Diagram megjelenítése
        plt.tight_layout()
        plt.show()


    # Hibaüzenet kiírása a terminálra
    except ValueError as e:
        error_message.set(f"Error: {e}")
        print(f"Error: {e}")


# Függvény az ablak bezárásához
def quit_app():
    global root
    if root:
        root.destroy()


# Tkinter ablak létrehozása
root = Tk()
root.title("Adatellenőrző")
root.configure(bg='lightblue')  # Fő ablak háttérszínének beállítása

# Frame a beviteli mezőknek
input_frame = ttk.Frame(root, padding="20")
input_frame.grid(row=0, column=0)
input_frame.configure(style="Custom.TFrame")

# Stílus beállítása
style = ttk.Style()
style.configure("Custom.TFrame", background="lightblue")
style.configure("Custom.TLabel", background="lightblue")
style.configure("Quit.TButton", background="red")
style.configure("Plot.TButton", background="green")

# Combobox a JSON fájlok kiválasztásához
data_source_label = ttk.Label(input_frame, text="Megjelenítendő adatforrás kiválasztása:", style="Custom.TLabel")
data_source_label.grid(row=0, column=0, padx=5, pady=5)

data_sources = list(json_files.keys())
data_source_combo = ttk.Combobox(input_frame, values=data_sources, state="readonly")
data_source_combo.grid(row=0, column=1, padx=5, pady=5)

# Alapértelmezett adat kiválasztása
data_source_combo.current(0)

# Kezdeti dátum label létrehozás
start_date_label = ttk.Label(input_frame, text="Kezdeti dátum (ÉÉÉÉ-HH-NN ÓÓ:PP:MM):", style="Custom.TLabel")
start_date_label.grid(row=1, column=0, padx=5, pady=5)
start_date_entry = ttk.Entry(input_frame, width=20)
start_date_entry.grid(row=1, column=1, padx=5, pady=5)

# Végdátum dátum label létrehozás
end_date_label = ttk.Label(input_frame, text="Utolsó dátum (ÉÉÉÉ-HH-NN ÓÓ:PP:MM):", style="Custom.TLabel")
end_date_label.grid(row=2, column=0, padx=5, pady=5)
end_date_entry = ttk.Entry(input_frame, width=20)
end_date_entry.grid(row=2, column=1, padx=5, pady=5)

# Hibaüzenet megjelenítése
error_message = StringVar()
error_label = ttk.Label(input_frame, textvariable=error_message, foreground="red", style="Custom.TLabel")
error_label.grid(row=3, columnspan=2, padx=5, pady=10)

# Diagram készítő gomb
plot_button = Button(input_frame, text="Vonaldiagram megjelenítése", command=plot_graph, bg="green", fg="white")
plot_button.grid(row=4, columnspan=2, padx=5, pady=10)

# Quit gomb az ablak bezárásához
quit_button = Button(input_frame, text="Kilépés", command=quit_app, bg="red", fg="white")
quit_button.grid(row=5, columnspan=2, padx=5, pady=10)

# Tkinter ablak indítása
root.mainloop()