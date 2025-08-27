import os
import speech_recognition as sr
import subprocess
import tkinter as tk
from tkinter import filedialog

def convert_to_wav(source_path, output_path):
    """Convierte un archivo de audio a .wav usando ffmpeg."""
    command = ['ffmpeg', '-y', '-i', source_path, output_path]
    subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def transcribe_wav_file(wav_path, output_txt_path, recognizer):
    """Transcribe un archivo .wav y lo guarda en un archivo .txt."""
    try:
        print("  - Transcribiendo audio...")
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language='es-CO')
        
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        print(f"  - ÉXITO: Transcripción guardada en '{os.path.basename(output_txt_path)}'")
    except sr.UnknownValueError:
        print("  - ERROR: No se pudo entender el audio.")
    except sr.RequestError as e:
        print(f"  - ERROR: No se pudo conectar con el servicio de transcripción; {e}")

def process_file(audio_file_path, recognizer):
    """Maneja la conversión y transcripción de un solo archivo de audio."""
    base_name_with_ext = os.path.basename(audio_file_path)
    base_name = os.path.splitext(base_name_with_ext)[0]
    output_dir = os.path.dirname(audio_file_path)
    
    print(f"\n[+] Procesando: {base_name_with_ext}")

    is_wav = audio_file_path.lower().endswith('.wav')
    temp_wav_path = os.path.join(output_dir, f"{base_name}_temp.wav")
    path_to_transcribe = audio_file_path if is_wav else temp_wav_path

    # Conversión
    if not is_wav:
        try:
            convert_to_wav(audio_file_path, temp_wav_path)
        except FileNotFoundError:
            print("  - ERROR: ffmpeg no está instalado o no se encuentra en el PATH del sistema.")
            return
        except subprocess.CalledProcessError:
            print(f"  - ERROR: Fallo en la conversión de {base_name_with_ext}.")
            return

    # Transcripción
    transcription_filename = f"transcripcion_{base_name}.txt"
    transcription_filepath = os.path.join(output_dir, transcription_filename)
    transcribe_wav_file(path_to_transcribe, transcription_filepath, recognizer)

    # Limpieza
    if not is_wav and os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)

def main():
    """Función principal para seleccionar y procesar archivos de audio."""
    root = tk.Tk()
    root.withdraw()

    source_files = filedialog.askopenfilenames(
        title="Seleccione los archivos de audio para transcribir",
        filetypes=[("Archivos de audio", "*.wav *.mp3 *.opus *.m4a *.flac *.ogg *.aac"), ("Todos los archivos", "*.*")])

    if not source_files:
        print("No se seleccionaron archivos. Finalizando programa.")
        return

    print("Iniciando proceso de transcripción...")
    recognizer = sr.Recognizer()
    for audio_file_path in source_files:
        process_file(audio_file_path, recognizer)

    print("\n[+] Proceso completado.")
    print("Nota: Cada archivo de transcripción se ha guardado en la misma carpeta que el archivo de audio original.")

if __name__ == "__main__":
    main()
