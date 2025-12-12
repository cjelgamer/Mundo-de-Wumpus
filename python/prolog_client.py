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
                line = self.output_queue.get(timeout=0.3)  # Reducido de 2.0s a 0.3s para más velocidad
                if line == "__END__":
                    break
                # Filtrar prompts y true/false
                if line in ["true.", "false."]:
                    continue
                # Filtrar líneas que contienen __END__ o marcadores de debug
                if "__END__" in line or line.startswith("P=") or line.startswith("ERROR:"):
                    continue
                response_lines.append(line)
            except queue.Empty:
                # Timeout
                break
        
        return "\n".join(response_lines).strip()
    
    def simple_query(self, prolog_query):
        """Query simplificada que limpia mejor la salida"""
        result = self.query(prolog_query, wait_for_result=True)
        # Limpiar cualquier residuo de marcadores
        result = result.replace("__END__", "").replace("P=[].", "").strip()
        return result

    def reiniciar_motor(self):
        """Reinicia COMPLETAMENTE el proceso de Prolog para limpiar caché"""
        # Matar proceso viejo
        self.stop()
        # Esperar un momento
        import time
        time.sleep(0.2)
        # Iniciar proceso nuevo
        self.start_process()
        return "Proceso Prolog reiniciado completamente"

    def restart(self):
        """Alias para reiniciar_motor - usado en manejo de errores"""
        return self.reiniciar_motor()

    def stop(self):
        self.running = False
        if self.process:
            try:
                self.process.terminate()
                self.process.wait(timeout=1.0)
            except subprocess.TimeoutExpired:
                self.process.kill()
            except:
                pass
            finally:
                self.process = None

    # ============================================================
    # MÉTODOS PARA SISTEMA MEJORADO
    # ============================================================

    def obtener_percepciones(self):
        """Obtiene lista de percepciones actuales del agente"""
        result = self.query("obtener_percepciones(P), write(P)")
        # El resultado será algo como: [brisa,hedor] o []
        return result

    def obtener_estado_agente(self):
        """Obtiene el estado completo del agente"""
        # Posición
        pos = self.query("posicion_agente(X,Y), format('~w,~w', [X,Y])")
        
        # Dirección
        dir_result = self.query("agente_dir(D), write(D)")
        
        # Oro
        oro = self.query("agente_tiene_oro(G), write(G)")
        
        # Flecha
        flecha = self.query("agente_tiene_flecha(F), write(F)")
        
        # Vivo
        vivo = self.query("agente_vivo(V), write(V)")
        
        return {
            'posicion': pos,
            'direccion': dir_result,
            'tiene_oro': oro,
            'tiene_flecha': flecha,
            'vivo': vivo
        }

    def ejecutar_accion_basica(self, accion):
        """
        Ejecuta una acción básica del agente
        Acciones: 'mover', 'girar_izquierda', 'girar_derecha', 'agarrar', 'disparar'
        """
        if accion == 'mover':
            return self.query("mover")
        elif accion == 'girar_izquierda':
            return self.query("girar_izquierda")
        elif accion == 'girar_derecha':
            return self.query("girar_derecha")
        elif accion == 'agarrar':
            return self.query("agarrar")
        elif accion == 'disparar':
            return self.query("disparar")
        else:
            return f"Acción desconocida: {accion}"

    def actualizar_kb(self):
        """Actualiza la base de conocimiento desde las percepciones actuales"""
        return self.query("actualizar_kb_desde_percepciones")

    def elegir_siguiente_celda(self):
        """Usa el sistema de decisión avanzado para elegir siguiente movimiento"""
        result = self.query("elegir_siguiente_celda(C), write(C)")
        return result

    def __del__(self):
        self.stop()

