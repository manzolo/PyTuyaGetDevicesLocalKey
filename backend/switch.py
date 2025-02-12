import tinytuya

# Configurazione del dispositivo
DEVICE_IP = "192.168.1.36"  # Sostituisci con l'IP del tuo dispositivo
DEVICE_ID = "bfda9b5d9f31d328923tr5"  # Sostituisci con il Device ID
LOCAL_KEY = "6413c26f8a511d11"  # Sostituisci con la Local Key
DEVICE_VERSION = "3.3"  # Versione del protocollo (3.1 o 3.3)

# Inizializza il dispositivo
device = tinytuya.OutletDevice(DEVICE_ID, DEVICE_IP, LOCAL_KEY)
device.set_version(DEVICE_VERSION)


# Funzione per inviare comandi
def send_command(command):
    try:
        # Invia il comando
        payload = device.generate_payload(tinytuya.CONTROL, {"1": command})
        response = device._send_receive(payload)

        if response:
            print(f"Comando {command} inviato con successo!")
        else:
            print("Errore: Nessuna risposta dal dispositivo.")
    except Exception as e:
        print(f"Errore durante l'invio del comando: {e}")


# Menu di controllo
if __name__ == "__main__":
    while True:
        print("\nMenu:")
        print("1. Accendi")
        print("2. Spegni")
        print("3. Esci")
        choice = input("Seleziona un'opzione: ")

        if choice == "1":
            send_command(True)  # Accendi
        elif choice == "2":
            send_command(False)  # Spegni
        elif choice == "3":
            print("Uscita...")
            break
        else:
            print("Scelta non valida. Riprova.")