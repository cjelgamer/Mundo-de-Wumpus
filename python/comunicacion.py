import subprocess
import json
import os

PROLOG_COMMAND = None

def get_prolog_command():
    global PROLOG_COMMAND
    if PROLOG_COMMAND:
        return PROLOG_COMMAND
    
    import shutil
    # 1. Intentar 'swipl' nativo
    if shutil.which("swipl"):
        PROLOG_COMMAND = ["swipl"]
        return PROLOG_COMMAND
    
    # 2. Intentar flatpak
    # Comprobar si flatpak está instalado
    if shutil.which("flatpak"):
        PROLOG_COMMAND = ["flatpak", "run", "org.swi_prolog.swipl"]
        return PROLOG_COMMAND
        
    # Default fallback
    PROLOG_COMMAND = ["swipl"]
    return PROLOG_COMMAND

def consulta_prolog(predicado, argumentos=[]):
    """
    Llama a Prolog y obtiene un resultado en texto.
    Ejecuta el proceso EN el directorio 'prolog/' para que imports relativos funcionen.
    """
    import os
    
    # Detectar directorios
    # __file__ es .../python/comunicacion.py
    base_dir = os.path.dirname(os.path.abspath(__file__))
    prolog_dir = os.path.join(os.path.dirname(base_dir), "prolog")
    
    # Si no existe (ej. ejecutando desde root), intentar buscarlo
    if not os.path.exists(prolog_dir):
        if os.path.exists("prolog"):
            prolog_dir = os.path.abspath("prolog")
    
    # Archivo relativo a prolog_dir
    archivo_pl = "agente.pl"

    # Formatear argumentos
    args_str = []
    for arg in argumentos:
        if isinstance(arg, list):
            items = ",".join(str(x) for x in arg)
            args_str.append(f"[{items}]")
        else:
            args_str.append(str(arg))
            
    args_unidos = ", ".join(args_str)
    query = f"{predicado}({args_unidos}, R), write(R)."

    cmd_base = get_prolog_command()
    comando = cmd_base + [
        "-q",
        "-s", archivo_pl,
        "-g", query,
        "-t", "halt"
    ]

    try:
        resultado = subprocess.run(
            comando,
            cwd=prolog_dir, # IMPORTANTE: Ejecutar contexto en carpeta prolog
            capture_output=True,
            text=True
        )
        
        if resultado.returncode != 0:
            print(f"Error Prolog (stderr): {resultado.stderr}")
            return "error"
            
        return resultado.stdout.strip()
    except FileNotFoundError:
        print(f"Error: No se encontró el comando '{cmd_base[0]}'.")
        return "error"
    except OSError as e:
        print(f"Error ejecutando Prolog: {e}")
        return "error"
