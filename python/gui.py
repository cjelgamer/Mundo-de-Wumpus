import tkinter as tk
from tkinter import messagebox, ttk
import json
import os
import sys
import threading
import time

# Asegurar importes locales
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from prolog_client import PrologClient
from generar_mapa import generar_mapa, guardar_json, guardar_prolog

class WumpusGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("Mundo de Wumpus 2.0 - Premium Edition")
        self.root.geometry("900x650")
        
        # Estilos y colores
        self.bg_color = "#2c3e50"
        self.panel_color = "#34495e"
        self.text_color = "#ecf0f1"
        self.accent_color = "#e74c3c"
        
        self.root.configure(bg=self.bg_color)
        
        self.CELL_SIZE = 80
        self.mapa = None
        self.agente_pos = [1, 1]
        self.agente_dir = 'este'  # Dirección del agente
        self.visitadas = set()
        self.prolog = PrologClient()
        self.auto_playing = False
        
        self.setup_ui()
        self.cargar_mapa_existente()

    def setup_ui(self):
        # --- Estilos TTK ---
        style = ttk.Style()
        style.theme_use('clam')
        style.configure("TButton", padding=6, relief="flat", background=self.accent_color, foreground="white", font=("Helvetica", 10, "bold"))
        style.map("TButton", background=[('active', '#c0392b')])
        
        # --- Layout Principal ---
        self.main_container = tk.Frame(self.root, bg=self.bg_color)
        self.main_container.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # --- Panel Izquierdo (Mapa) ---
        self.map_frame = tk.Frame(self.main_container, bg=self.bg_color, bd=2, relief=tk.GROOVE)
        self.map_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.canvas = tk.Canvas(self.map_frame, bg="white", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # --- Panel Derecho (Controles e Info) ---
        self.side_panel = tk.Frame(self.main_container, bg=self.panel_color, width=300)
        self.side_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(10, 0))
        self.side_panel.pack_propagate(False) # Mantener ancho fijo
        
        # Título
        tk.Label(self.side_panel, text="MANDO DE CONTROL", bg=self.panel_color, fg=self.text_color, font=("Helvetica", 14, "bold")).pack(pady=(20, 10))
        
        # Botones
        btn_frame = tk.Frame(self.side_panel, bg=self.panel_color)
        btn_frame.pack(fill=tk.X, padx=20)
        
        ttk.Button(btn_frame, text="🔄 Generar Nuevo Mapa", command=self.nuevo_mapa).pack(fill=tk.X, pady=5)
        ttk.Button(btn_frame, text="👣 Siguiente Paso", command=self.siguiente_paso).pack(fill=tk.X, pady=5)
        self.btn_auto = ttk.Button(btn_frame, text="▶ Juego Automático", command=self.toggle_auto)
        self.btn_auto.pack(fill=tk.X, pady=5)
        
        # Info Estado
        lb_info = tk.Label(self.side_panel, text="Estado del Agente", bg=self.panel_color, fg="#95a5a6", font=("Helvetica", 10, "bold"))
        lb_info.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.status_var = tk.StringVar(value="Esperando...")
        self.status_label = tk.Label(self.side_panel, textvariable=self.status_var, bg="#2c3e50", fg="#2ecc71", font=("Consolas", 10), justify=tk.LEFT, wraplength=260, height=4)
        self.status_label.pack(fill=tk.X, padx=20)

        # Log
        lb_log = tk.Label(self.side_panel, text="Registro Visual", bg=self.panel_color, fg="#95a5a6", font=("Helvetica", 10, "bold"))
        lb_log.pack(pady=(20, 5), anchor="w", padx=20)
        
        self.log_text = tk.Text(self.side_panel, bg="#2c3e50", fg="white", font=("Consolas", 9), height=15, bd=0)
        self.log_text.pack(fill=tk.BOTH, expand=True, padx=20, pady=(0, 20))
        
        # Leyenda
        self.draw_legend()

    def draw_legend(self):
        # Pequeña leyenda en log o frame
        self.log("LEYENDA:\n[ W ] Wumpus  [ $ ] Oro\n[ O ] Pozo    [ A ] Agente\n( ~ ) Hedor   ( = ) Brisa\n🟦 Seguro  ⬛ Desconocido")

    def log(self, msj):
        self.log_text.insert(tk.END, f"> {msj}\n")
        self.log_text.see(tk.END)

    def status(self, msj):
        self.status_var.set(msj)

    def nuevo_mapa(self):
        self.auto_playing = False
        self.btn_auto.config(text="▶ Juego Automático")
        
        self.log("--- Generando Nuevo Mundo ---")
        self.mapa = generar_mapa()
        guardar_json(self.mapa)
        guardar_prolog(self.mapa)
        
        self.agente_pos = [1, 1]
        self.visitadas = set()
        self.visitadas.add((1, 1))
        
        # Reiniciar memoria de Prolog
        self.prolog.reiniciar_motor()
        self.log("Cerebro Prolog reiniciado.")
        
        self.dibujar_mapa()
        self.status("Listo para iniciar.")

    def cargar_mapa_existente(self):
        try:
            with open("mundo.json", "r") as f:
                self.mapa = json.load(f)
            self.agente_pos = [1, 1]
            self.visitadas.add((1, 1))
            self.prolog.reiniciar_motor()
            self.dibujar_mapa()
        except FileNotFoundError:
            self.nuevo_mapa()

    def dibujar_mapa(self):
        self.canvas.delete("all")
        if not self.mapa: return
        
        n = self.mapa['tamano']
        cw = self.canvas.winfo_width()
        ch = self.canvas.winfo_height()
        
        # Calcular tamaño dinámico de celda para ajustar
        sz = min(cw // (n + 1), ch // (n + 1))
        if sz < 40: sz = 40
        self.CELL_SIZE = sz
        
        # Centrar el grid
        offset_x = (cw - (n * sz)) // 2
        offset_y = (ch - (n * sz)) // 2
        
        for x in range(1, n+1):
            for y in range(1, n+1):
                # Conversión coord Prolog (abajo-izq) -> Tkinter (arriba-izq)
                x0 = offset_x + (x - 1) * sz
                y0 = offset_y + (n - y) * sz
                x1 = x0 + sz
                y1 = y0 + sz
                
                # Color base
                fill = "#ecf0f1" # Gris muy claro
                if (x, y) in self.visitadas:
                    fill = "#aed6f1" # Azul claro seguro
                
                # Dibujar rectángulo
                self.canvas.create_rectangle(x0, y0, x1, y1, fill=fill, outline="#bdc3c7", width=2)
                
                # --- Objetos ---
                cx, cy = x0 + sz/2, y0 + sz/2
                
                if [x, y] == self.mapa['wumpus']:
                    if self.mapa.get('wumpus_vivo', True):
                         # Wumpus vivo
                         self.canvas.create_text(cx, cy, text="W", font=("Arial", int(sz*0.5), "bold"), fill="#c0392b")
                    else:
                         # Wumpus muerto
                         self.canvas.create_text(cx, cy, text="💀", font=("Arial", int(sz*0.5), "bold"), fill="gray")
                
                if [x, y] == self.mapa['oro']:
                    self.canvas.create_text(cx, cy+sz*0.2, text="$", font=("Arial", int(sz*0.4), "bold"), fill="#f1c40f")
                
                if [x, y] in self.mapa['pozos']:
                    self.canvas.create_text(cx, cy, text="O", font=("Arial", int(sz*0.5), "bold"), fill="black")
                    
                # --- Percepciones (Debug) ---
                percepciones_txt = ""
                # Hedor
                wx, wy = self.mapa['wumpus']
                if abs(x-wx) + abs(y-wy) == 1:
                    percepciones_txt += "~" # Hedor
                # Brisa
                for px, py in self.mapa['pozos']:
                    if abs(x-px) + abs(y-py) == 1:
                        percepciones_txt += "=" # Brisa
                        break
                
                if percepciones_txt:
                    self.canvas.create_text(x0+5, y0+5, text=percepciones_txt, anchor=tk.NW, font=("Arial", int(sz*0.25), "bold"), fill="purple")

        # Dibujar Agente con dirección
        ax, ay = self.agente_pos
        ax0 = offset_x + (ax - 1) * sz
        ay0 = offset_y + (n - ay) * sz
        # Agente como circulo azul con 'A'
        self.canvas.create_oval(ax0+sz*0.2, ay0+sz*0.2, ax0+sz*0.8, ay0+sz*0.8, fill="#3498db", outline="white", width=2)
        self.canvas.create_text(ax0+sz*0.5, ay0+sz*0.5, text="A", fill="white", font=("Arial", int(sz*0.3), "bold"))
        
        # Flecha indicando dirección
        dir_arrows = {'norte': '↑', 'sur': '↓', 'este': '→', 'oeste': '←'}
        arrow = dir_arrows.get(self.agente_dir, '→')
        self.canvas.create_text(ax0+sz*0.5, ay0+sz*0.15, text=arrow, fill="#e74c3c", font=("Arial", int(sz*0.25), "bold"))
        
        self.root.update_idletasks()

    def obtener_percepciones(self):
        """Calcula percepciones desde Python (más confiable que parsear Prolog)"""
        percepciones = []
        x, y = self.agente_pos
        
        # Hedor si Wumpus está adyacente
        wx, wy = self.mapa['wumpus']
        if abs(x-wx) + abs(y-wy) == 1: 
            percepciones.append("hedor")
        
        # Brisa si hay pozo adyacente
        for px, py in self.mapa['pozos']:
            if abs(x-px) + abs(y-py) == 1: 
                percepciones.append("brisa")
                break
        
        # Brillo si oro está en posición actual (y aún no ha sido recogido)
        if self.mapa['oro'] is not None:
            ox, oy = self.mapa['oro']
            if x == ox and y == oy: 
                percepciones.append("brillo")
        
        return percepciones
    
    def actualizar_estado_visual(self):
        """Actualiza el panel de estado con información del agente"""
        try:
            estado = self.prolog.obtener_estado_agente()
            pos = estado.get('posicion', 'N/A')
            dir_val = estado.get('direccion', 'N/A')
            oro = '✓' if estado.get('tiene_oro') == '1' else '✗'
            flecha = '✓' if estado.get('tiene_flecha') == '1' else '✗'
            vivo = '✓' if estado.get('vivo') == '1' else '✗'
            
            self.agente_dir = dir_val  # Actualizar dirección para visualización
            
            status_text = f"Pos: ({pos})\nDir: {dir_val}\nOro: {oro} | Flecha: {flecha}\nVivo: {vivo}"
            self.status(status_text)
        except:
            # Fallback simple
            self.status(f"Pos: ({self.agente_pos[0]},{self.agente_pos[1]})\nDir: {self.agente_dir}")

    def siguiente_paso(self):
        percepciones = self.obtener_percepciones()
        self.log(f"Percepciones: {percepciones}")
        
        # Formatear lista para Prolog: ['brisa', 'hedor'] -> [brisa,hedor]
        if percepciones:
            args_str = "[" + ",".join(percepciones) + "]"
        else:
            args_str = "[]"
        
        # Llamar a decidir_accion en Prolog
        try:
            query = f"decidir_accion({args_str}, Accion), write(Accion)"
            resultado = self.prolog.query(query)
            self.log(f"Decisión: {resultado}")
        except Exception as e:
            self.log(f"Error en Prolog: {e}")
            resultado = "accion(girar)"  # Fallback
        
        import re
        # Buscar accion(Tipo...)
        if "agarrar" in resultado:
            self.log("¡ORO RECOGIDO!")
            self.mapa['oro'] = None
            if self.agente_pos == [1, 1]:
                self.status("¡VICTORIA! Oro encontrado y escapado.")
                messagebox.showinfo("¡Ganaste!", "El agente encontró el oro y escapó.")
                self.auto_playing = False
                self.btn_auto.config(text="▶ Juego Automático")
        
        elif "disparar" in resultado:
            m = re.search(r"disparar,\s*(\d+),\s*(\d+)", resultado)
            if m:
                wx, wy = int(m.group(1)), int(m.group(2))
                self.log(f"🔫 ¡AGENTE DISPARA A (%d, %d)!" % (wx, wy))
                
                # Ejecutar disparo en Prolog y capturar salida
                res_disparo = self.prolog.query(f"disparar({wx}, {wy})")
                if res_disparo:
                    self.log(f"{res_disparo}")

                # Verificar via texto o estado
                if "WUMPUS ELIMINADO" in res_disparo:
                    self.log("💀 ¡WUMPUS ELIMINADO! Zona segura.")
                    self.status("Wumpus Eliminado")
                    self.mapa['wumpus_vivo'] = False
                elif "FALLO" in res_disparo:
                     self.log("❌ Disparo fallido (Ver detalles arriba).")
                else:
                    # Fallback verification
                    wumpus_vivo = self.prolog.query("wumpus_vivo(V), write(V)")
                    if wumpus_vivo == "0":
                         self.log("💀 ¡WUMPUS ELIMINADO! Zona segura.")
                         self.status("Wumpus Eliminado")
                         self.mapa['wumpus_vivo'] = False
                    else:
                         self.log("❌ Fallo el disparo (Wumpus sigue vivo).")
            else:
                 self.log("Intentando disparar, pero error parseando coords.")

        elif "ir" in resultado:
            m = re.search(r"ir,(\d+),(\d+)", resultado)
            if m:
                nx, ny = int(m.group(1)), int(m.group(2))
                self.mover_agente(nx, ny)
            else:
                m = re.search(r"ir,\s*(\d+),\s*(\d+)", resultado)
                if m:
                    nx, ny = int(m.group(1)), int(m.group(2))
                    self.mover_agente(nx, ny)
                else:
                    self.log("No se pudo parsear movimiento")
            
        elif "girar" in resultado:
            self.log("Agente girando...")
        
        elif "salir" in resultado:
            # Verificar si el agente tiene oro
            try:
                estado = self.prolog.obtener_estado_agente()
                tiene_oro = estado.get('tiene_oro') == '1'
                
                if tiene_oro and self.agente_pos == [1, 1]:
                    self.log("¡VICTORIA! Agente escapó con el oro.")
                    self.status("¡MISIÓN CUMPLIDA!")
                    messagebox.showinfo("¡Victoria!", "El agente encontró el oro y escapó exitosamente.")
                else:
                    self.log("Agente salió de la cueva.")
                    self.status("Agente salió.")
            except:
                self.log("Agente salió de la cueva.")
                self.status("Agente salió.")
            
            self.auto_playing = False
            self.btn_auto.config(text="▶ Juego Automático")
        else:
            self.log(f"Acción desconocida: {resultado}")
            
        self.dibujar_mapa()

    def mover_agente(self, nx, ny):
        # Usar el sistema de movimiento de Prolog
        try:
            # El agente se moverá usando mover_a_celda_adyacente en Prolog
            result = self.prolog.query(f"mover_a_celda_adyacente(({nx},{ny}))")
            
            # Actualizar posición local
            self.agente_pos = [nx, ny]
            self.visitadas.add(tuple(self.agente_pos))
            self.log(f"Movido a ({nx}, {ny})")
            
        except:
            # Fallback: actualización manual
            self.agente_pos = [nx, ny]
            self.visitadas.add(tuple(self.agente_pos))
            self.prolog.query(f"actualizar_posicion({nx}, {ny})")
            self.log(f"Movido a ({nx}, {ny})")
        
        self.dibujar_mapa()
        
        # Verificar muerte
        if self.agente_pos == self.mapa['wumpus']:
            self.log("💀 MUERTE: Wumpus te comió.")
            messagebox.showerror("Game Over", "El Wumpus te ha comido.")
            self.auto_playing = False
            self.btn_auto.config(text="▶ Juego Automático")
        elif self.agente_pos in self.mapa['pozos']:
            self.log("💀 MUERTE: Caíste en pozo.")
            messagebox.showerror("Game Over", "Caíste en un pozo sin fondo.")
            self.auto_playing = False
            self.btn_auto.config(text="▶ Juego Automático")

    def toggle_auto(self):
        if self.auto_playing:
            self.auto_playing = False
            self.btn_auto.config(text="▶ Juego Automático")
        else:
            self.auto_playing = True
            self.btn_auto.config(text="⏸ Pausar")
            self.run_auto()

    def run_auto(self):
        if self.auto_playing:
            self.siguiente_paso()
            # Velocidad ajustada
            self.root.after(800, self.run_auto)

if __name__ == "__main__":
    root = tk.Tk()
    app = WumpusGUI(root)
    # Evento de ventana resize para redibujar
    root.bind("<Configure>", lambda e: app.dibujar_mapa())
    root.mainloop()
