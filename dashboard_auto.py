import os
import subprocess
import time
import bluetooth
import re
import serial
import vlc
import sys
import time



from PyQt5.QtWidgets import (
    QApplication, QPushButton, QWidget, QLabel, QVBoxLayout, QHBoxLayout,
    QGridLayout, QStackedWidget, QFileSystemModel, QTreeView, QHeaderView,
    QListWidget, QSpacerItem, QSizePolicy, QSlider
)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QTimer, QTime, QDate, Qt, QSize, QUrl, QProcess, QObject, pyqtSlot
from PyQt5.QtWebEngineWidgets import QWebEngineView, QWebEnginePage
from PyQt5.QtWebChannel import QWebChannel

# Inizializza l'applicazione PyQt5
app = QApplication([])

# Finestra principale
window = QWidget()
window.setWindowTitle("Dashboard Auto")
window.setStyleSheet("""
    QWidget {
        background: qlineargradient(
            x1: 0, y1: 0, x2: 1, y2: 1,
            stop: 0 #1e5799, stop: 1 #7db9e8
        );
    }
""")

# Layout principale
main_layout = QHBoxLayout(window)

# Barra laterale fissa
sidebar = QWidget()
sidebar.setFixedWidth(250)
sidebar.setStyleSheet("background-color: #0a4275;")
sidebar_layout = QVBoxLayout(sidebar)

# Label per data, ora, tensione, consumo e temperatura con HTML
label_date = QLabel("Data:<br>--/--/----")
label_time = QLabel("Ora:<br>--:--:--")
label_voltage = QLabel("Tensione:<br>--V")
label_consumption = QLabel("Consumo:<br>--kWh")
label_temperature = QLabel("Temperatura:<br>--°C")

# Imposta l'allineamento al centro per ogni label e usa HTML per l'interruzione di riga
for label in [label_date, label_time, label_voltage, label_consumption, label_temperature]:
    label.setStyleSheet("color: white; font-size: 30px; font-weight: bold;")
    label.setAlignment(Qt.AlignCenter)
    sidebar_layout.addWidget(label)

# Aggiungiamo la barra laterale al layout principale
main_layout.addWidget(sidebar)

# Area centrale che cambierà dinamicamente
stacked_widget = QStackedWidget()
main_layout.addWidget(stacked_widget)

# Layout per la dashboard (le icone principali)
dashboard_widget = QWidget()
dashboard_layout = QGridLayout(dashboard_widget)
stacked_widget.addWidget(dashboard_widget)

# Funzione per creare pulsanti rotondi con dimensioni personalizzabili
def create_round_button(icon_path, size=180):  # Assicurati che il size qui corrisponda a quello dei pulsanti
    button = QPushButton()
    button.setIcon(QIcon(icon_path))
    button.setIconSize(QSize(size - 40, size - 40))  # Regola l'icona per adattarsi bene al pulsante
    button.setFixedSize(size, size)  # Imposta dimensioni quadrate per rotondità
    button.setStyleSheet(f"""
        QPushButton {{
            border-radius: {size // 2}px;  /* Imposta il raggio per essere rotondo */
            border: 0px;
            background-color: rgba(0, 0, 0, 0.5);
        }}
        QPushButton:hover {{
            background-color: rgba(255, 255, 255, 0.2);
        }}
    """)
    return button


# Funzione per mostrare la dashboard
def show_dashboard():
    stacked_widget.setCurrentIndex(0)

# Funzione per eseguire le applicazioni browser, maps e youtube nella schermata centrale
def run_app_in_central_area(app_name):
    app_widget = QWidget()
    layout = QVBoxLayout(app_widget)

    if app_name == 'browser':
        browser = QWebEngineView()
        browser.setUrl(QUrl("https://www.google.com"))
        layout.addWidget(browser)
    elif app_name == 'youtube':
        youtube_browser = QWebEngineView()
        youtube_browser.setUrl(QUrl("https://www.youtube.com"))
        layout.addWidget(youtube_browser)
    elif app_name == 'maps':
        map_view = QWebEngineView()
        map_view.setUrl(QUrl("https://www.openstreetmap.org"))

        # Aggiungi del CSS per raddoppiare le dimensioni delle icone
        map_view.page().runJavaScript("""
            var style = document.createElement('style');
            style.innerHTML = `
                .leaflet-control-zoom-in, .leaflet-control-zoom-out {
                    font-size: 48px !important; /* Raddoppia la dimensione delle icone di zoom */
                }
            `;
            document.head.appendChild(style);
        """)

        # Funzione per aprire la tastiera virtuale quando si fa clic nella barra di ricerca
        map_view.page().runJavaScript("""
            document.querySelector('input[type="search"]').addEventListener('focus', function() {
                pyOpenKeyboard();
            });
        """)

        layout.addWidget(map_view)

    # Aggiungi il widget al layout
    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)

    # Pulsante per tornare alla dashboard
    back_button = create_round_button("/home/a/Documenti/home.png", size=200)
    back_button.clicked.connect(show_dashboard)
    layout.addWidget(back_button)

    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)


def connect_bluetooth():
    app_widget = QWidget()
    main_layout = QVBoxLayout(app_widget)  # Layout principale verticale

    # Etichetta per lo stato della connessione
    connection_status = QLabel("Seleziona un dispositivo per connetterti...")
    connection_status.setStyleSheet("color: white; font-size: 25px;")
    main_layout.addWidget(connection_status)

    # Lista dei dispositivi Bluetooth
    devices_list = QListWidget()
    main_layout.addWidget(devices_list)

    # Funzione per eseguire la scansione dei dispositivi Bluetooth
    def scan_bluetooth_devices():
        devices_list.clear()
        scan_process = subprocess.Popen("bluetoothctl devices", shell=True, stdout=subprocess.PIPE)
        output, error = scan_process.communicate()
        if output:
            devices = output.decode("utf-8").strip().split("\n")
            for device in devices:
                devices_list.addItem(device)
        else:
            connection_status.setText("Nessun dispositivo trovato. Riprova.")

    # Esegue una scansione iniziale
    scan_bluetooth_devices()

    # Funzione per connettersi al dispositivo selezionato
    def connect_to_device():
        selected_device = devices_list.currentItem()
        if selected_device:
            selected_text = selected_device.text()
            mac_address = selected_text.split(" ")[1]
            connection_process = subprocess.Popen(["bluetoothctl", "connect", mac_address], stdout=subprocess.PIPE)
            connection_status.setText(f"Connessione avviata a {selected_text}...")
            show_bluetooth_audio_controls()

    # Creazione dei pulsanti con dimensione 160
    connect_button = create_round_button("/home/a/Documenti/connect.png", size=200)
    connect_button.clicked.connect(connect_to_device)

    scan_button = create_round_button("/home/a/Documenti/ricerca.png", size=200)
    scan_button.clicked.connect(scan_bluetooth_devices)

    back_button = create_round_button("/home/a/Documenti/home.png", size=200)
    back_button.clicked.connect(show_dashboard)

    # Layout per i pulsanti in basso
    button_layout = QHBoxLayout()
    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    button_layout.addWidget(connect_button)
    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    button_layout.addWidget(scan_button)
    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))
    button_layout.addWidget(back_button)
    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

    # Sposta i pulsanti in basso
    main_layout.addStretch()  # Aggiunge uno spazio flessibile
    main_layout.addLayout(button_layout)  # Aggiungi il layout dei pulsanti in fondo

    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)
    
  


def get_connected_device_mac():
    # Usa bluetoothctl per trovare i dispositivi connessi
    try:
        output = subprocess.check_output("bluetoothctl info", shell=True).decode("utf-8")
        # Cerca l'indirizzo MAC con una regex
        mac_address_match = re.search(r"Device ([0-9A-F:]{17})", output)
        if mac_address_match:
            mac_address = mac_address_match.group(1)
            print(f"MAC address trovato: {mac_address}")
            return mac_address
        else:
            print("Nessun dispositivo Bluetooth connesso trovato.")
            return None
    except subprocess.CalledProcessError as e:
        print("Errore eseguendo bluetoothctl:", e)
        return None

def send_hci_command():
    mac_address = get_connected_device_mac()
    if not mac_address:
        print("Non è possibile inviare il comando. Nessun dispositivo connesso.")
        return

    # Collega e invia il comando play/pausa
    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((mac_address, 1))
        print(f"Connesso a {mac_address}")

        # Comando HCI play/pausa: Personalizzato, dipende dal dispositivo
        play_pause_command = b'\x00\x44\x4F\x00'  # Es. simbolico
        sock.send(play_pause_command)

        print("Comando Play/Pausa inviato")
        sock.close()

    except bluetooth.btcommon.BluetoothError as err:
        print(f"Errore nella connessione: {err}")

# Funzione per mostrare i controlli di riproduzione Bluetooth nella schermata centrale
def show_bluetooth_audio_controls():
    app_widget = QWidget()
    layout = QVBoxLayout(app_widget)

    label = QLabel("Controlli di Riproduzione Audio Bluetooth")
    label.setStyleSheet("color: white; font-size: 25px;")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)

    controls_layout = QHBoxLayout()

    # Funzione di controllo per i pulsanti play/pausa, volume
    def toggle_play_pause():
        send_hci_command()  # Usa la funzione per inviare il comando

    def increase_volume():
        subprocess.run("pactl set-sink-volume @DEFAULT_SINK@ +5%", shell=True)

    def decrease_volume():
        subprocess.run("pactl set-sink-volume @DEFAULT_SINK@ -5%", shell=True)

    # Pulsante Volume Su
    volume_up_b_button = create_round_button("/home/a/Documenti/volume_up.png", size=200)
    volume_up_b_button.clicked.connect(increase_volume)
    controls_layout.addWidget(volume_up_b_button)

    # Pulsante Volume Giù
    volume_down_b_button = create_round_button("/home/a/Documenti/volume_down.png", size=200)
    volume_down_b_button.clicked.connect(decrease_volume)
    controls_layout.addWidget(volume_down_b_button)

    layout.addLayout(controls_layout)

    # Pulsante per tornare alla dashboard
    back_button = create_round_button("/home/a/Documenti/home.png", size=200)
    back_button.clicked.connect(show_dashboard)
    layout.addWidget(back_button)

    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)



# Funzione per creare un file explorer nella zona centrale con intestazione "Nome" e font raddoppiato
def select_and_play_music():
    app_widget = QWidget()
    layout = QVBoxLayout(app_widget)

    model = QFileSystemModel()
    model.setRootPath('/home/a/Musica')  # Cartella Musica
    tree_view = QTreeView()
    tree_view.setModel(model)
    tree_view.setRootIndex(model.index('/home/a/Musica'))
    
    tree_view.header().setSectionResizeMode(0, QHeaderView.Stretch)
    tree_view.setColumnHidden(1, True)
    tree_view.setColumnHidden(2, True)
    tree_view.setColumnHidden(3, True)
    tree_view.header().setStyleSheet("background-color: #0a4275; color: white; font-size: 25px;")

    tree_view.setStyleSheet("""
        QTreeView {
            background-color: #1e5799;
            color: white;
            font-size: 30px;
        }
    """)

    tree_view.doubleClicked.connect(lambda index: play_music(model.filePath(index)))
    layout.addWidget(tree_view)

    back_button = create_round_button("/home/a/Documenti/home.png", size=200)
    back_button.clicked.connect(show_dashboard)
    layout.addWidget(back_button)

    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)


# Funzione per riprodurre il file audio selezionato con controlli multimediali
def play_music(file_path):
    if os.path.isfile(file_path) and file_path.endswith(('.mp3', '.wav', '.flac')):
        instance = vlc.Instance()
        player = instance.media_player_new()
        media = instance.media_new(file_path)
        player.set_media(media)
        player.play()

        app_widget = QWidget()
        layout = QVBoxLayout(app_widget)

        label = QLabel(f"Riproducendo: {file_path.split('/')[-1]}")
        label.setStyleSheet("color: white; font-size: 25px;")
        label.setAlignment(Qt.AlignCenter)
        layout.addWidget(label)

        controls_layout = QHBoxLayout()

        # Pulsante Play/Pausa
        play_button = create_round_button("/home/a/Documenti/play.png", size=200)
        
        def toggle_play():
            if player.get_state() == vlc.State.Ended:  # Se la traccia è completata, riavvia
                player.stop()
                player.play()
            elif player.is_playing():
                player.pause()
            else:
                player.play()

        play_button.clicked.connect(toggle_play)
        controls_layout.addWidget(play_button)

        # Pulsante Volume Su
        volume_up_button = create_round_button("/home/a/Documenti/volume_up.png", size=160)
        volume_up_button.clicked.connect(lambda: player.audio_set_volume(min(player.audio_get_volume() + 10, 100)))
        controls_layout.addWidget(volume_up_button)

        # Pulsante Volume Giù
        volume_down_button = create_round_button("/home/a/Documenti/volume_down.png", size=200)
        volume_down_button.clicked.connect(lambda: player.audio_set_volume(max(player.audio_get_volume() - 10, 0)))
        controls_layout.addWidget(volume_down_button)

        # Cursore per controllare la posizione della traccia
        slider = QSlider(Qt.Horizontal)
        controls_layout.addWidget(slider)

        # Funzione per aggiornare la posizione del cursore
        def update_slider_position():
            if player.get_length() > 0:
                current_time = player.get_time()
                duration = player.get_length()
                slider.setValue(int((current_time / duration) * 100))
            if player.get_state() == vlc.State.Ended:
                slider.setValue(0)  # Resetta lo slider alla fine della traccia

        # Collega il cursore alla funzione di aggiornamento
        def set_position(value):
            if player.get_length() > 0:
                new_time = int((value / 100) * player.get_length())
                player.set_time(new_time)

        slider.valueChanged.connect(set_position)

        # Timer per aggiornare il cursore ogni 100 ms
        timer = QTimer()
        timer.timeout.connect(update_slider_position)
        timer.start(100)

        # Pulsante per tornare alla selezione delle tracce
        back_to_tracks_button = create_round_button("/home/a/Documenti/back.png", size=200)
        back_to_tracks_button.clicked.connect(lambda: stop_and_select_music(player))
        controls_layout.addWidget(back_to_tracks_button)

        layout.addLayout(controls_layout)

        # Pulsante per tornare alla dashboard
        back_button = create_round_button("/home/a/Documenti/home.png", size=200)
        back_button.clicked.connect(show_dashboard)
        layout.addWidget(back_button)

        stacked_widget.addWidget(app_widget)
        stacked_widget.setCurrentWidget(app_widget)

def stop_and_select_music(player):
    player.stop()
    select_and_play_music()    




def open_android_auto():
    try:
        # Esegui il comando per avviare OpenAuto
        subprocess.Popen(["sudo", "/home/a/openauto/bin/autoapp"])
    except Exception as e:
        print(f"Errore durante l'avvio di Android Auto: {e}", file=sys.stderr)

    # Creazione dell'interfaccia utente
    app_widget = QWidget()
    layout = QVBoxLayout(app_widget)

    label = QLabel("Android Auto in esecuzione...")
    label.setStyleSheet("color: white; font-size: 25px;")
    label.setAlignment(Qt.AlignCenter)
    layout.addWidget(label)

    back_button = create_round_button("/home/a/Documenti/home.png", size=200)
    back_button.clicked.connect(show_dashboard)
    layout.addWidget(back_button)

    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)






# Funzione per aprire la tastiera virtuale
def pyOpenKeyboard():
    print("Apertura della tastiera virtuale...")
    os.system("matchbox-keyboard --geometry 800x300+0+500 --orientation landscape &")


# Classe per gestire i segnali del canale WebChannel
class JSHandler(QObject):
    @pyqtSlot()
    def openKeyboard(self):
        print("Apertura della tastiera da JavaScript...")
        pyOpenKeyboard()

# Funzione per configurare il WebChannel
def setup_web_channel(view):
    channel = QWebChannel(view.page())
    handler = JSHandler()
    channel.registerObject("handler", handler)
    view.page().setWebChannel(channel)

    # Carica il JavaScript per rilevare il focus degli input
    script = """
    // Verifica che il QWebChannel sia incluso nella pagina
    if (typeof QWebChannel === "undefined") {
        console.error("QWebChannel non è definito!");
    } else {
        new QWebChannel(qt.webChannelTransport, function(channel) {
            window.handler = channel.objects.handler;

            document.querySelectorAll('input[type="text"], input[type="search"], textarea').forEach(function(input) {
                input.addEventListener('focus', function() {
                    console.log("Campo di input selezionato");
                    handler.openKeyboard();
                });
                input.addEventListener('blur', function() {
                    console.log("Campo di input deselezionato");
                });
            });
        });
    }
    """
    view.page().runJavaScript(script)


# Funzione per aprire la radio web
def open_web_radio():
    app_widget = QWidget()
    main_layout = QVBoxLayout(app_widget)

    # Carica il portale web per le radio
    web_radio_view = QWebEngineView()
    web_radio_view.setUrl(QUrl("https://www.radio.net/"))

    # Configura il WebChannel
    setup_web_channel(web_radio_view)  # La funzione ora è definita

    # Layout principale
    main_layout.addWidget(web_radio_view)

    # Layout orizzontale per i pulsanti in basso
    button_layout = QHBoxLayout()
    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

    # Pulsante per aprire la tastiera virtuale
    keyboard_button = QPushButton("Apri Tastiera")  # Usa QPushButton o la funzione customizzata
    keyboard_button.clicked.connect(pyOpenKeyboard)  # Collega la funzione pyOpenKeyboard
    button_layout.addWidget(keyboard_button)

    button_layout.addSpacerItem(QSpacerItem(40, 20, QSizePolicy.Expanding, QSizePolicy.Minimum))

    # Pulsante per tornare alla dashboard
    back_button = QPushButton("Torna alla Dashboard")
    back_button.clicked.connect(show_dashboard)  # Presumendo che show_dashboard sia definito
    button_layout.addWidget(back_button)

    main_layout.addLayout(button_layout)

    stacked_widget.addWidget(app_widget)
    stacked_widget.setCurrentWidget(app_widget)








# Indirizzo MAC fisso del dispositivo OBD-II
obd_mac = "00:1D:A5:68:98:8A"
obd_uuid = "00001101-0000-1000-8000-00805f9b34fb"  # UUID del servizio Serial Port

def show_obd_interface():
    stacked_widget.setCurrentWidget(obd_widget)  # Mostra la schermata OBD
    connect_to_obd()  # Connette automaticamente all'OBD

def find_obd_channel():
    services = bluetooth.find_service(address=obd_mac)
    print("Servizi trovati:", services)  # Debug

    if not services:
        print("Nessun servizio trovato per l'indirizzo MAC:", obd_mac)  # Debug
        return None

    for svc in services:
        print(f"Servizio: {svc}")  # Stampa dettagli del servizio trovato
        if svc["service-classes"] and obd_uuid in svc["service-classes"]:
            print(f"Canale trovato: {svc['port']}")  # Debug
            return svc["port"]

    print("Nessun canale OBD trovato.")  # Debug
    return None

def connect_to_obd():
    global sock
    channel = find_obd_channel()  # Trova il canale usando l'UUID
    if channel is None:
        print("Utilizzo canale statico 1")  # Debug
        channel = 1  # Prova con il canale 1

    try:
        sock = bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        sock.connect((obd_mac, channel))
        status_label.setText("Connesso all'OBD.")
        start_obd_data_timer()
    except bluetooth.btcommon.BluetoothError as e:
        status_label.setText(f"Errore di connessione: {str(e)} - Riprovo in 5 secondi")
        print(f"Errore di connessione: {str(e)}")  # Debug
        QTimer.singleShot(5000, connect_to_obd)

def start_obd_data_timer():
    timer = QTimer()
    timer.timeout.connect(update_obd_data)
    timer.start(2000)  # Aggiorna i dati ogni 2 secondi

def update_obd_data():
    global sock
    try:
        # Lettura velocità (PID 0D)
        sock.send(b'010D\r')
        time.sleep(1)  # Aumenta il tempo di attesa
        speed_response = sock.recv(1024).decode().strip()
        speed = process_obd_response(speed_response)
        speed_label.setText(f"Velocità: {speed} km/h" if speed else "Velocità: -- km/h")

        # Lettura giri motore (PID 0C)
        sock.send(b'010C\r')
        time.sleep(1)
        rpm_response = sock.recv(1024).decode().strip()
        rpm = process_obd_response(rpm_response)
        rpm_label.setText(f"Giri motore: {rpm} rpm" if rpm else "Giri motore: -- rpm")

        # Lettura temperatura liquido refrigerante (PID 05)
        sock.send(b'0105\r')
        time.sleep(1)
        coolant_temp_response = sock.recv(1024).decode().strip()
        coolant_temp = process_obd_response(coolant_temp_response)
        coolant_temp_label.setText(f"Temp. Liquido: {coolant_temp} °C" if coolant_temp else "Temp. Liquido: -- °C")

    except bluetooth.btcommon.BluetoothError as e:
        status_label.setText("OBD disconnesso. Riconnessione in corso...")
        print(f"Errore Bluetooth: {str(e)}")  # Debug
        sock.close()  # Chiude il socket precedente
        connect_to_obd()  # Riprova a connettersi

def process_obd_response(response):
    if response.startswith("41"):
        data = response[4:].strip()
        if len(data) >= 2:
            return int(data, 16)  # Converte in decimale
    return None

# Aggiungi il layout OBD
obd_widget = QWidget()
obd_layout = QVBoxLayout(obd_widget)

# Label per lo stato della connessione
status_label = QLabel("Stato connessione: Non connesso")
obd_layout.addWidget(status_label)

# Label per visualizzare i dati OBD
speed_label = QLabel("Velocità: -- km/h")
rpm_label = QLabel("Giri motore: -- rpm")
coolant_temp_label = QLabel("Temp. Liquido: -- °C")

obd_layout.addWidget(speed_label)
obd_layout.addWidget(rpm_label)
obd_layout.addWidget(coolant_temp_label)

# Pulsante per tornare alla dashboard
back_button = QPushButton("Torna alla Dashboard")
back_button.clicked.connect(show_dashboard)
obd_layout.addWidget(back_button)

# Aggiunge la schermata OBD al widget centrale
stacked_widget.addWidget(obd_widget)










# Funzioni per aprire le applicazioni
def open_browser():
    run_app_in_central_area('browser')

def open_youtube():
    run_app_in_central_area('youtube')

def open_maps():
    run_app_in_central_area('maps')

def open_play_music():
    select_and_play_music()

# Funzione per aggiornare l'ora e la data
def update_time_date():
    current_time = QTime.currentTime()
    label_time.setText(f'Ora:<br>{current_time.toString("hh:mm:ss")}')
    
    current_date = QDate.currentDate()
    label_date.setText(f'Data:<br>{current_date.toString("dd/MM/yyyy")}')

# Funzione per aggiornare la tensione e consumo (simulato)
def update_obd_data():
    voltage = 12.5
    consumption = 20
    label_voltage.setText(f'Tensione:<br>{voltage}V')
    label_consumption.setText(f'Consumo:<br>{consumption}kWh')

# Funzione per aggiornare la temperatura (simulato)
def update_temperature():
    temperature = 22.3
    label_temperature.setText(f'Temperatura:<br>{temperature}°C')

# Timer per aggiornare ora e data
timer = QTimer()
timer.timeout.connect(update_time_date)
timer.start(1000)

# Timer per aggiornare dati OBD e temperatura
obd_timer = QTimer()
obd_timer.timeout.connect(update_obd_data)
obd_timer.start(5000)

temp_timer = QTimer()
temp_timer.timeout.connect(update_temperature)
temp_timer.start(5000)

# Aggiungi i pulsanti alla dashboard
button_maps = create_round_button("/home/a/Documenti/maps.png")
button_maps.clicked.connect(open_maps)
dashboard_layout.addWidget(button_maps, 0, 0)

button_music = create_round_button("/home/a/Documenti/music.jpg")
button_music.clicked.connect(open_play_music)
dashboard_layout.addWidget(button_music, 0, 1)

button_browser = create_round_button("/home/a/Documenti/browser.png")
button_browser.clicked.connect(open_browser)
dashboard_layout.addWidget(button_browser, 0, 2)

button_youtube = create_round_button("/home/a/Documenti/youtube.png")
button_youtube.clicked.connect(open_youtube)
dashboard_layout.addWidget(button_youtube, 1, 0)

button_bluetooth = create_round_button("/home/a/Documenti/bluetooth.png")
button_bluetooth.clicked.connect(connect_bluetooth)
dashboard_layout.addWidget(button_bluetooth, 1, 1)

button_android_auto = create_round_button("/home/a/Documenti/android_auto.png")
button_android_auto.clicked.connect(open_android_auto)
dashboard_layout.addWidget(button_android_auto, 1, 2)

# Pulsante per aprire la web radio
button_radio = create_round_button("/home/a/Documenti/webradio.png")  # Assicurati di avere l'icona per la radio
button_radio.clicked.connect(open_web_radio)
dashboard_layout.addWidget(button_radio, 2,0)

button_obd = create_round_button("/home/a/Documenti/obd.png")
button_obd.clicked.connect(show_obd_interface)
dashboard_layout.addWidget(button_obd, 2, 1)

button_exit = create_round_button("/home/a/Documenti/exit.png")
button_exit.clicked.connect(app.quit)
dashboard_layout.addWidget(button_exit, 2, 2)




# Mostra la finestra principale
window.showFullScreen()

app.exec_()
