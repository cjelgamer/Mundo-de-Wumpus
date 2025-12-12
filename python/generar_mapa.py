import json
import random

def generar_mapa(tamano=6):
    mapa = {
        "tamano": tamano,
        "wumpus": [],
        "oro": [],
        "pozos": []
    }
    
    # Zonas seguras donde NO puede haber peligros (inicio y adyacentes)
    seguras = [[1, 1], [1, 2], [2, 1]]
    
    # 1. Colocar Wumpus (evitando seguras)
    while True:
        w = [random.randint(1, tamano), random.randint(1, tamano)]
        if w not in seguras:
            mapa["wumpus"] = w
            break
            
    # 2. Colocar Oro (evitando seguras y wumpus, aunque wumpus+oro es posible en reglas, mejor separar para jugabilidad)
    while True:
        o = [random.randint(1, tamano), random.randint(1, tamano)]
        if o not in seguras and o != mapa["wumpus"]:
            mapa["oro"] = o
            break

    # 3. Generar pozos (probabilidad 15%, evitando seguras, wumpus, oro Y ADYACENTES A WUMPUS)
    # Lista prohibida para pozos: Seguras + Wumpus + Oro + AdyacentesWumpus
    prohibidas = seguras + [mapa["wumpus"], mapa["oro"]]
    
    # Añadir adyacentes a wumpus a prohibidas para que brisa y hedor no se mezclen
    wx, wy = mapa["wumpus"]
    ady_wumpus = [[wx+1, wy], [wx-1, wy], [wx, wy+1], [wx, wy-1]]
    prohibidas += ady_wumpus

    for x in range(1, tamano + 1):
        for y in range(1, tamano + 1):
            pos = [x, y]
            if pos in prohibidas:
                continue
            
            # 15% de probabilidad de pozo
            if random.random() < 0.15:
                mapa["pozos"].append(pos)

    return mapa

def guardar_json(mapa):
    import json 
    with open("mundo.json", "w") as f:
        json.dump(mapa, f, indent=4)

###############################################################################
# NUEVO: Generar también el archivo .pl para que Prolog lo lea directamente
###############################################################################
def guardar_prolog(mapa):
    cuerpo = []
    
    # Hechos básicos - RENAMED agent -> posicion_agente
    cuerpo.append(f":- dynamic posicion_agente/2.")
    cuerpo.append(f":- dynamic wumpus/2.")
    cuerpo.append(f":- dynamic oro/2.")
    cuerpo.append(f":- dynamic pozo/2.")
    cuerpo.append(f":- dynamic visitado/2.")
    cuerpo.append(f":- dynamic seguro/2.")
    cuerpo.append(f":- dynamic peligro/2.")
    cuerpo.append("")
    
    cuerpo.append(f"tamano({mapa['tamano']}).")
    cuerpo.append(f"wumpus({mapa['wumpus'][0]}, {mapa['wumpus'][1]}).")
    cuerpo.append(f"oro({mapa['oro'][0]}, {mapa['oro'][1]}).")
    
    for p in mapa['pozos']:
        cuerpo.append(f"pozo({p[0]}, {p[1]}).")

    # Estado inicial del agente
    cuerpo.append("posicion_agente(1, 1).")
    cuerpo.append("visitado(1, 1).") 
    cuerpo.append("seguro(1, 1).")

    # Guardar en la carpeta prolog (ajustar path según estructura)
    # Asumimos que se ejecuta desde la raiz del proyecto o python/
    import os
    ruta_prolog = "prolog/mundo.pl"
    # Si estamos en python/, subir un nivel
    if os.path.exists("../prolog"):
        ruta_prolog = "../prolog/mundo.pl"
    
    with open(ruta_prolog, "w") as f:
        f.write("\n".join(cuerpo))

if __name__ == "__main__":
    mapa = generar_mapa()
    guardar_json(mapa)
    guardar_prolog(mapa)
    print("Mapas generados: mundo.json y mundo.pl")
