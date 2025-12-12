import subprocess
import os
import shutil
import threading
import queue

class PrologClient:
    def __init__(self):
        self.process = None
        self.output_queue = queue.Queue()
        self.running = False
        self.start_process()

    def get_prolog_command(self):
        if shutil.which("swipl"):
            return ["swipl", "-q"] # Quiet mode important
        if shutil.which("flatpak"):
            # Nota: Flatpak puede ser confuso con pipes, pero intentamos
            return ["flatpak", "run", "org.swi_prolog.swipl", "-q"]
        return ["swipl", "-q"]

    def start_process(self):
        """Inicia el proceso SWI-Prolog persistente"""
        command = self.get_prolog_command()
        
        # Determinar CWD correcto (carpeta prolog/)
        # Asumimos que __file__ está en python/prolog_client.py
        base_dir = os.path.dirname(os.path.abspath(__file__))
        prolog_dir = os.path.join(os.path.dirname(base_dir), "prolog")
        
        if not os.path.exists(prolog_dir) and os.path.exists("prolog"):
            prolog_dir = os.path.abspath("prolog")

        try:
            # bufsize=1 con text=True habilita line buffering, crucial para interactividad
            self.process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # IMPORTANTE: Ver errores en el mismo pipe
                text=True,
                cwd=prolog_dir,
                bufsize=1 
            )
            self.running = True
            
            # Hilo para leer stdout sin bloquear
            self.reader_thread = threading.Thread(target=self._read_output)
            self.reader_thread.daemon = True
            self.reader_thread.start()
            
            # Cargar archivos iniciales
            # Cargar archivos iniciales EN ORDEN
            self.output_queue.put(f"DEBUG: CWD={prolog_dir}")
            
            # 1. Cargar mundo.pl (hechos dinámicos)
            res_mundo = self.query("consult('mundo.pl')")
            self.output_queue.put(f"DEBUG: Load mundo.pl -> {res_mundo}")
            
            # 2. Cargar agente.pl (reglas)
            res_agente = self.query("consult('agente.pl')")
            self.output_queue.put(f"DEBUG: Load agente.pl -> {res_agente}")
            
        except Exception as e:
            print(f"Error iniciando Prolog: {e}")
            self.output_queue.put(f"Error critico iniciando: {e}")
            self.running = False

    def _read_output(self):
        """Lee línea por línea del stdout de Prolog"""
        while self.running and self.process:
            line = self.process.stdout.readline()
            if line:
                self.output_queue.put(line.strip())
            if not line and self.process.poll() is not None:
                break

    def query(self, prolog_query, wait_for_result=True):
        """
        Envía una consulta y espera la respuesta.
        La consulta DEBE inluir una marca especial para saber cuándo terminar de leer.
        """
        if not self.running:
            return "Error: Prolog no está corriendo."

        # Limpiar cola vieja
        while not self.output_queue.empty():
            self.output_queue.get()

        # Enviar query
        # Usamos un delimitador claro. writeln('END_OF_QUERY').
        full_query = f"{prolog_query}, writeln('__END__').\n"
        
        try:
            self.process.stdin.write(full_query)
            self.process.stdin.flush()
        except BrokenPipeError:
            self.restart()
            return "Error: Pipe roto, reiniciando..."

        if not wait_for_result:
            return "OK"

        # Leer respuesta hasta __END__
        response_lines = []
        while True:
            try:
                line = self.output_queue.get(timeout=2.0) # 2s timeout
                if line == "__END__":
                    break
                # Filtrar prompts y true/false
                if line in ["true.", "false."]:
                    continue
                response_lines.append(line)
            except queue.Empty:
                # Timeout
                break
        
        return "\n".join(response_lines).strip()

    def reiniciar_motor(self):
        """Recarga el archivo del agente para borrar memoria"""
        # Una forma ruda pero efectiva es reiniciar el proceso
        self.stop()
        self.start_process()

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
            except:
                pass

    def __del__(self):
        self.stop()
