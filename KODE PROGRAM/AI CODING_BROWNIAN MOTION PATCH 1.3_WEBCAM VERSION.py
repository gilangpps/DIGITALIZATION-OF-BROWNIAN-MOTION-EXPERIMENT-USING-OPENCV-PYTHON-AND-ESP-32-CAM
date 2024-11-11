import cv2
import pandas as pd
import numpy as np
import time
from tkinter import Tk, Label, StringVar, Button, filedialog, Frame
import threading
from PIL import Image, ImageTk
import matplotlib.pyplot as plt  # Tambahkan ini untuk plotting

# Konstanta fisik
k_B = 1.380649e-23  # Konstanta Boltzmann dalam J/K
T = 302  # Suhu dalam Kelvin
eta = 0.0008145  # Viskositas dalam Pa.s

# Inisialisasi data pergerakan untuk 5 objek
data_pergerakan_objek = [[] for _ in range(5)]
msd_data = [None] * 5

# Konstanta kalibrasi: 1 piksel = 6e-8 meter
kalibrasi_meter_per_piksel = 6e-8

# Variabel untuk menyimpan posisi terakhir objek
posisi_terakhir_objek = [None] * 5

# Warna untuk masing-masing objek (Merah, Kuning, Hijau, Biru, Ungu)
warna_kontur = [(0, 0, 255), (0, 255, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)]

# Variabel global untuk menampung label tampilan video
video_label = None
cap = None  # Variabel global untuk capture video

# Fungsi untuk menghitung MSD
def hitung_msd(data):
    if len(data) > 1:
        diffs = [(p[1] - data[0][1]) ** 2 + (p[2] - data[0][2]) ** 2 for p in data]
        return np.mean(diffs)
    return 0

# Fungsi untuk menyimpan data ke dalam file Excel
def simpan_data_excel():
    root = Tk()
    root.withdraw()
    file_path = filedialog.asksaveasfilename(defaultextension=".xlsx", filetypes=[("Excel files", "*.xlsx")])
    
    with pd.ExcelWriter(file_path) as writer:
        for i in range(5):
            df = pd.DataFrame(data_pergerakan_objek[i], columns=["Waktu (s)", "Posisi X (m)", "Posisi Y (m)"])
            df.to_excel(writer, sheet_name=f"Objek {i+1}", index=False)

    print(f"Data disimpan ke {file_path}")

# Fungsi untuk mendeteksi pergerakan objek dan memperbarui tampilan video
def deteksi_pergerakan(stop_event):
    global cap
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        fps = 30
    frame_time = 1.0 / fps

    background_subtractor = cv2.createBackgroundSubtractorMOG2(history=100, varThreshold=40)
    start_time = time.time()

    def update_frame():
        if stop_event.is_set():
            return

        ret, frame = cap.read()
        if not ret:
            return

        gray_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        mask = background_subtractor.apply(gray_frame)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)
        largest_contours = contours[:5]

        current_time = time.time() - start_time

        for i, contour in enumerate(largest_contours):
            area = cv2.contourArea(contour)
            if area < 5:
                continue

            (x, y, w, h) = cv2.boundingRect(contour)
            posisi_x_meter = (x + w // 2) * kalibrasi_meter_per_piksel
            posisi_y_meter = (y + h // 2) * kalibrasi_meter_per_piksel

            if posisi_terakhir_objek[i] is None or posisi_terakhir_objek[i] != (posisi_x_meter, posisi_y_meter):
                posisi_terakhir_objek[i] = (posisi_x_meter, posisi_y_meter)
                data_pergerakan_objek[i].append([current_time, posisi_x_meter, posisi_y_meter])

                msd = hitung_msd(data_pergerakan_objek[i])
                difusivitas = msd / (4 * current_time) if current_time > 0 else 0
                jari_jari = k_B * T / (6 * np.pi * eta * difusivitas) if difusivitas > 0 else 0

                label_texts[i][0].set(f"{i+1}")
                label_texts[i][1].set(f"{posisi_x_meter:.2e}")
                label_texts[i][2].set(f"{posisi_y_meter:.2e}")
                label_texts[i][3].set(f"{msd:.2e}")
                label_texts[i][4].set(f"{jari_jari:.2e}")

                cv2.rectangle(frame, (x, y), (x + w, y + h), warna_kontur[i], 2)

        img = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(img)
        img_tk = ImageTk.PhotoImage(image=img)

        video_label.config(image=img_tk)
        video_label.image = img_tk

        video_label.after(10, update_frame)

    update_frame()

# Fungsi untuk menampilkan webcam dengan deteksi pergerakan
def tampilkan_webcam_dengan_tracking(stop_event):
    global cap
    cap = cv2.VideoCapture(1)

    if not cap.isOpened():
        print("Error membuka kamera")
        return

    deteksi_pergerakan(stop_event)

# Fungsi untuk menampilkan grafik posisi X(Y) dan jarak terhadap waktu
def tampilkan_grafik():
    for i in range(5):
        if len(data_pergerakan_objek[i]) > 0:
            # Ambil data x, y, dan waktu
            waktu = [row[0] for row in data_pergerakan_objek[i]]
            posisi_x = [row[1] for row in data_pergerakan_objek[i]]
            posisi_y = [row[2] for row in data_pergerakan_objek[i]]

            # Plot x(y)
            plt.figure(figsize=(8, 6))
            plt.plot(posisi_x, posisi_y, label=f"Objek {i+1}", marker='o')
            plt.xlabel("Posisi X (m)")
            plt.ylabel("Posisi Y (m)")
            plt.title(f"Grafik X(Y) untuk Objek {i+1}")
            plt.legend()
            plt.show()

            # Plot jarak terhadap waktu
            jarak = [np.sqrt(x**2 + y**2) for x, y in zip(posisi_x, posisi_y)]
            plt.figure(figsize=(8, 6))
            plt.plot(waktu, jarak, label=f"Objek {i+1}", marker='o')
            plt.xlabel("Waktu (s)")
            plt.ylabel("Jarak (m)")
            plt.title(f"Grafik Jarak terhadap Waktu untuk Objek {i+1}")
            plt.legend()
            plt.show()

# Fungsi untuk menghentikan tracking dan menampilkan grafik
def stop_tracking():
    global stop_event, cap
    if stop_event:
        stop_event.set()
        cap.release()  # Hentikan penggunaan webcam
        tampilkan_grafik()  # Tampilkan grafik setelah tracking dihentikan

# Fungsi untuk memulai tracking
def start_tracking():
    global stop_event
    stop_event = threading.Event()
    tracking_thread = threading.Thread(target=tampilkan_webcam_dengan_tracking, args=(stop_event,))
    tracking_thread.start()

# Fungsi untuk menjalankan GUI
def run_gui():
    global video_label
    root = Tk()
    root.title("Brownian Motion - AI")

    title_frame = Frame(root)
    title_frame.grid(row=0, column=0, columnspan=2, padx=10, pady=10)
    
    title_label = Label(title_frame, text="Brownian Motion - AI", font=("Helvetica", 16, "bold"))
    title_label.pack()

    button_frame = Frame(root)
    button_frame.grid(row=1, column=0, padx=20, pady=10)

    start_button = Button(button_frame, text="Start", width=10, command=start_tracking)
    start_button.pack(pady=5)

    stop_button = Button(button_frame, text="Stop", width=10, command=stop_tracking)
    stop_button.pack(pady=5)

    save_button = Button(button_frame, text="Save Excel", width=10, command=simpan_data_excel)
    save_button.pack(pady=5)

    table_frame = Frame(root)
    table_frame.grid(row=1, column=1, padx=20, pady=10)

    Label(table_frame, text="Sample", width=10, font=("Helvetica", 12)).grid(row=0, column=0)
    Label(table_frame, text="x (m)", width=10, font=("Helvetica", 12)).grid(row=0, column=1)
    Label(table_frame, text="y (m)", width=10, font=("Helvetica", 12)).grid(row=0, column=2)
    Label(table_frame, text="MSD", width=10, font=("Helvetica", 12)).grid(row=0, column=3)
    Label(table_frame, text="r (m)", width=10, font=("Helvetica", 12)).grid(row=0, column=4)

    global label_texts
    label_texts = [[StringVar(value="-") for _ in range(5)] for _ in range(5)]

    for i in range(5):
        for j in range(5):
            Label(table_frame, textvariable=label_texts[i][j], width=10, font=("Helvetica", 10)).grid(row=i+1, column=j)

    video_label = Label(root)
    video_label.grid(row=2, column=0, columnspan=2, padx=20, pady=10)

    root.mainloop()

run_gui()
