# Transcriptor de Audio

Este script de Python permite transcribir archivos de audio a texto de forma sencilla. Utiliza la API de reconocimiento de voz de Google para realizar las transcripciones.

## Descripción

El programa abre una ventana de diálogo para que el usuario seleccione uno o más archivos de audio. Luego, procesa cada archivo, lo transcribe y guarda el texto resultante en un archivo `.txt` individual por cada audio.

El script está diseñado para ser fácil de usar y para mantener el directorio de trabajo limpio, utilizando archivos temporales que se eliminan automáticamente.

## Requisitos

Para poder utilizar este script, necesitas tener instalado lo siguiente en tu sistema:

1.  **Python 3:** [https://www.python.org/downloads/](https://www.python.org/downloads/)
2.  **ffmpeg:** Una herramienta esencial para la conversión de audio.
    *   **Windows:** Descargar desde [gyan.dev](https://www.gyan.dev/ffmpeg/builds/) o [BtbN](https://github.com/BtbN/FFmpeg-Builds/releases) y añadir la carpeta `bin` a la variable de entorno PATH del sistema.
    *   **macOS (usando Homebrew):** `brew install ffmpeg`
    *   **Linux (usando apt):** `sudo apt update && sudo apt install ffmpeg`
3.  **Librerías de Python:** Las dependencias necesarias se pueden instalar a través de `pip`.

## Instalación

1.  Clona o descarga este proyecto en tu máquina local.
2.  Abre una terminal o línea de comandos y navega al directorio del proyecto.
3.  Instala las librerías de Python necesarias ejecutando el siguiente comando:

    ```bash
    pip install SpeechRecognition
    ```

    *Nota: `SpeechRecognition` puede requerir la librería `PyAudio` para algunos casos de uso, aunque para este script (que procesa archivos) no siempre es estrictamente necesaria. Si encuentras problemas, puedes instalarla con `pip install PyAudio`.*

## Uso

1.  Asegúrate de tener todos los requisitos instalados.
2.  Ejecuta el script desde tu terminal:

    ```bash
    python transcriptor_audio.py
    ```

3.  Se abrirá una ventana de selección de archivos. Elige uno o más archivos de audio que desees transcribir (formatos comunes como `.mp3`, `.wav`, `.opus`, `.m4a`, etc., son compatibles).
4.  El script procesará cada archivo y mostrará el progreso en la terminal.
5.  Al finalizar, se generará un archivo `transcripcion_[nombre_del_audio].txt` por cada audio procesado. **Estos archivos de texto se guardarán en la misma carpeta donde se encuentran los archivos de audio originales.**
