import os
import speech_recognition as sr
import subprocess
import tkinter as tk
from tkinter import ttk, filedialog, scrolledtext
import threading
import concurrent.futures
import queue
import json

CONFIG_FILE = "config.json"
DEFAULT_LANGUAGE_NAME = "Español (Colombia)"

# --- Lógica de Transcripción ---

def convert_to_wav(source_path, output_path, log_queue, item_id):
    try:
        log_queue.put({'type': 'status', 'item_id': item_id, 'status': 'Convirtiendo...'})
        command = ['ffmpeg', '-y', '-i', source_path, output_path]
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except FileNotFoundError:
        log_queue.put({'type': 'log', 'message': f"ERROR ({os.path.basename(source_path)}): ffmpeg no está instalado."})
        return False
    except subprocess.CalledProcessError:
        log_queue.put({'type': 'log', 'message': f"ERROR ({os.path.basename(source_path)}): Fallo en la conversión."})
        return False

def transcribe_wav_file(wav_path, output_txt_path, language, recognizer, log_queue, item_id):
    try:
        log_queue.put({'type': 'status', 'item_id': item_id, 'status': 'Transcribiendo...'})
        with sr.AudioFile(wav_path) as source:
            audio_data = recognizer.record(source)
            text = recognizer.recognize_google(audio_data, language=language)
        
        with open(output_txt_path, 'w', encoding='utf-8') as f:
            f.write(text)
        log_queue.put({'type': 'log', 'message': f"ÉXITO ({os.path.basename(item_id)}): Transcripción guardada."})
        return True
    except sr.UnknownValueError:
        log_queue.put({'type': 'log', 'message': f"ERROR ({os.path.basename(item_id)}): No se pudo entender el audio."})
        return False
    except sr.RequestError as e:
        log_queue.put({'type': 'log', 'message': f"ERROR ({os.path.basename(item_id)}): Sin conexión al servicio; {e}"})
        return False

def process_file(item_id, output_dir, language, recognizer, log_queue):
    base_name = os.path.splitext(os.path.basename(item_id))[0]
    is_wav = item_id.lower().endswith('.wav')
    temp_wav_path = os.path.join(output_dir, f"{base_name}_temp.wav")
    path_to_transcribe = item_id if is_wav else temp_wav_path

    if not is_wav:
        if not convert_to_wav(item_id, temp_wav_path, log_queue, item_id):
            log_queue.put({'type': 'status', 'item_id': item_id, 'status': 'Error Conversión'})
            return

    if transcribe_wav_file(path_to_transcribe, os.path.join(output_dir, f"transcripcion_{base_name}.txt"), language, recognizer, log_queue, item_id):
        log_queue.put({'type': 'status', 'item_id': item_id, 'status': 'Completado'})
    else:
        log_queue.put({'type': 'status', 'item_id': item_id, 'status': 'Error Transcripción'})

    if not is_wav and os.path.exists(temp_wav_path):
        os.remove(temp_wav_path)

# --- Interfaz Gráfica ---

LANGUAGES = {
    DEFAULT_LANGUAGE_NAME: "es-CO", "Español (España)": "es-ES", "Español (México)": "es-MX",
    "Inglés (EE.UU.)": "en-US", "Inglés (Reino Unido)": "en-GB", "Francés (Francia)": "fr-FR",
    "Alemán (Alemania)": "de-DE", "Italiano (Italia)": "it-IT", "Portugués (Brasil)": "pt-BR"
}

class TranscriptionApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Transcriptor de Audio")
        self.root.geometry("700x650")
        self.root.resizable(False, False)

        self.output_dir = tk.StringVar(value=os.getcwd())
        self.language_name = tk.StringVar(value=DEFAULT_LANGUAGE_NAME)
        self.log_queue = queue.Queue()
        self.processing_thread = None

        self.load_settings()
        self.create_widgets()
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        files_frame = ttk.LabelFrame(main_frame, text="1. Archivos a Procesar", padding="10")
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        tree_cols = ("Archivo", "Estado")
        self.tree = ttk.Treeview(files_frame, columns=tree_cols, show="headings", height=7)
        self.tree.heading("Archivo", text="Archivo")
        self.tree.heading("Estado", text="Estado")
        self.tree.column("Archivo", width=400)
        self.tree.column("Estado", width=150, anchor='center')
        self.tree.pack(fill=tk.BOTH, expand=True)

        file_buttons_frame = ttk.Frame(main_frame)
        file_buttons_frame.pack(fill=tk.X, pady=5)
        self.add_files_button = ttk.Button(file_buttons_frame, text="Añadir Archivos", command=self.select_files)
        self.add_files_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0,5))
        self.remove_files_button = ttk.Button(file_buttons_frame, text="Quitar Seleccionados", command=self.remove_selected_files)
        self.remove_files_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5,5))
        self.clear_button = ttk.Button(file_buttons_frame, text="Limpiar Finalizadas", command=self.clear_completed_tasks)
        self.clear_button.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(5,0))

        options_frame = ttk.LabelFrame(main_frame, text="2. Configurar Opciones", padding="10")
        options_frame.pack(fill=tk.X, pady=5)
        lang_label = ttk.Label(options_frame, text="Idioma:")
        lang_label.pack(side=tk.LEFT, padx=(0, 5))
        self.lang_combobox = ttk.Combobox(options_frame, textvariable=self.language_name, values=list(LANGUAGES.keys()), state="readonly", width=20)
        self.lang_combobox.pack(side=tk.LEFT, padx=(0, 20))
        output_label = ttk.Label(options_frame, text="Carpeta de Salida:")
        output_label.pack(side=tk.LEFT, padx=(0, 5))
        self.output_entry = ttk.Entry(options_frame, textvariable=self.output_dir, state="readonly")
        self.output_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        self.output_button = ttk.Button(options_frame, text="Seleccionar...", command=self.select_output_dir)
        self.output_button.pack(side=tk.LEFT)

        self.start_button = ttk.Button(main_frame, text="Iniciar Proceso", command=self.start_transcription_thread, style='Accent.TButton')
        self.start_button.pack(fill=tk.X, pady=10, ipady=5)
        style = ttk.Style()
        style.configure('Accent.TButton', font=('Helvetica', 10, 'bold'))

        self.progress_bar = ttk.Progressbar(main_frame, orient='horizontal', mode='determinate')
        self.progress_bar.pack(fill=tk.X, pady=5)

        log_frame = ttk.LabelFrame(main_frame, text="Registro de Eventos", padding="10")
        log_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.log_text = scrolledtext.ScrolledText(log_frame, wrap=tk.WORD, state='disabled', height=5)
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def select_files(self):
        new_files = filedialog.askopenfilenames(title="Seleccione audios", filetypes=[("Archivos de audio", "*.wav *.mp3 *.opus *.m4a *.flac *.ogg *.aac"), ("Todos los archivos", "*.*")])
        if not new_files:
            return

        for f_path in new_files:
            if not self.tree.exists(f_path):
                self.tree.insert('', 'end', iid=f_path, values=(os.path.basename(f_path), 'Pendiente'))
        
        self.log(f"{len(new_files)} archivo(s) añadidos a la lista.")

    def remove_selected_files(self):
        selected_items = self.tree.selection()
        for item_id in selected_items:
            if self.tree.item(item_id, 'values')[1] == 'Pendiente':
                self.tree.delete(item_id)

    def clear_completed_tasks(self):
        final_states = ["Completado", "Error Conversión", "Error Transcripción", "Ya Completado"]
        for item_id in self.tree.get_children():
            status = self.tree.item(item_id, 'values')[1]
            if status in final_states:
                self.tree.delete(item_id)

    def select_output_dir(self):
        directory = filedialog.askdirectory(title="Seleccione carpeta de destino")
        if directory:
            self.output_dir.set(directory)
            self.log(f"Carpeta de salida establecida en: {directory}")

    def log(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.config(state='disabled')
        self.log_text.see(tk.END)

    def poll_log_queue(self):
        try:
            while True:
                item = self.log_queue.get_nowait()
                if item['type'] == 'log':
                    self.log(item['message'])
                elif item['type'] == 'status':
                    if self.tree.exists(item['item_id']):
                        self.tree.set(item['item_id'], 'Estado', item['status'])
                elif item['type'] == 'progress':
                    self.progress_bar.step()
                elif item['type'] == 'done':
                    self.set_controls_state(False)
                    return
        except queue.Empty:
            pass
        finally:
            self.root.after(100, self.poll_log_queue)

    def set_controls_state(self, processing):
        state = 'disabled' if processing else 'normal'
        self.add_files_button.config(state=state)
        self.remove_files_button.config(state=state)
        self.clear_button.config(state=state)
        self.start_button.config(state=state)
        self.lang_combobox.config(state=state)

    def start_transcription_thread(self):
        self.log("\n>>> Iniciando proceso...")
        out_dir = self.output_dir.get()
        files_to_process = []

        for item_id in self.tree.get_children():
            base_name = os.path.splitext(os.path.basename(item_id))[0]
            output_filename = f"transcripcion_{base_name}.txt"
            output_filepath = os.path.join(out_dir, output_filename)

            if os.path.exists(output_filepath):
                self.tree.set(item_id, 'Estado', 'Ya Completado')
                self.log(f"INFO ({os.path.basename(item_id)}): La transcripción ya existe.")
            else:
                self.tree.set(item_id, 'Estado', 'Pendiente')
                files_to_process.append(item_id)

        if not files_to_process:
            self.log("No hay archivos nuevos para procesar.")
            return

        self.progress_bar['value'] = 0
        self.progress_bar['maximum'] = len(files_to_process)
        self.set_controls_state(processing=True)
        
        self.processing_thread = threading.Thread(target=self.run_transcription, args=(files_to_process,))
        self.processing_thread.daemon = True
        self.processing_thread.start()
        self.poll_log_queue()

    def run_transcription(self, files_to_process):
        recognizer = sr.Recognizer()
        lang_code = LANGUAGES[self.language_name.get()]
        out_dir = self.output_dir.get()
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=os.cpu_count()) as executor:
            future_to_item = {executor.submit(process_file, item_id, out_dir, lang_code, recognizer, self.log_queue): item_id for item_id in files_to_process}

            for future in concurrent.futures.as_completed(future_to_item):
                try:
                    future.result()
                except Exception as e:
                    item_id = future_to_item[future]
                    self.log_queue.put({'type': 'status', 'item_id': item_id, 'status': 'Error Inesperado'})
                    self.log_queue.put({'type': 'log', 'message': f"ERROR ({os.path.basename(item_id)}): {e}"})
                finally:
                    self.log_queue.put({'type': 'progress'})
        
        self.log_queue.put({'type': 'log', 'message': "\n>>> Proceso completado."})
        self.log_queue.put({'type': 'done'})

    def save_settings(self):
        settings = {
            'language_name': self.language_name.get(),
            'output_dir': self.output_dir.get()
        }
        try:
            with open(CONFIG_FILE, 'w') as f:
                json.dump(settings, f, indent=4)
        except IOError as e:
            self.log(f"Error al guardar configuración: {e}")

    def load_settings(self):
        try:
            with open(CONFIG_FILE, 'r') as f:
                settings = json.load(f)
                self.language_name.set(settings.get('language_name', DEFAULT_LANGUAGE_NAME))
                self.output_dir.set(settings.get('output_dir', os.getcwd()))
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def on_closing(self):
        self.save_settings()
        self.root.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = TranscriptionApp(root)
    root.mainloop()
