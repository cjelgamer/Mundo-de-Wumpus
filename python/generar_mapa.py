import json
import random

def generar_mapa(tamano=6):
    mapa = {
        "tamano": tamano,
        "wumpus": [],
        "oro": [],
        "pozos": []
    }
    
    # Zona segura inicial - Solo (1,1) y sus 2 adyacentes inmediatos
    # Esto permite más peligros en el mapa pero garantiza inicio seguro
    seguras = [[1, 1], [1, 2], [2, 1]]
    
    # 1. Colocar Wumpus (evitando seguras, pero puede estar cerca)
    while True:
        w = [random.randint(1, tamano), random.randint(1, tamano)]
        # Wumpus debe estar fuera de zona segura
        if w not in seguras:
            mapa["wumpus"] = w
            break
            
    # 2. Colocar Oro (evitando seguras y wumpus)
    while True:
        o = [random.randint(1, tamano), random.randint(1, tamano)]
        if o not in seguras and o != mapa["wumpus"]:
            mapa["oro"] = o
            break

    # 3. Generar pozos - MÁS POZOS para mundo clásico
    # Lista prohibida: Solo seguras + Wumpus + Oro
    prohibidas = seguras + [mapa["wumpus"], mapa["oro"]]
    
    # Añadir adyacentes a wumpus (para que hedor y brisa no se mezclen)
    wx, wy = mapa["wumpus"]
    ady_wumpus = [[wx+1, wy], [wx-1, wy], [wx, wy+1], [wx, wy-1]]
    prohibidas += ady_wumpus

    for x in range(1, tamano + 1):
        for y in range(1, tamano + 1):
            pos = [x, y]
            if pos in prohibidas:
                continue
            
            # AUMENTADO: 20% de probabilidad de pozo (mundo clásico)
            if random.random() < 0.20:
                mapa["pozos"].append(pos)

    return mapa

def guardar_json(mapa):
    with open("mundo.json", "w") as f:
        json.dump(mapa, f, indent=4)

###############################################################################
# MEJORADO: Generar mundo.pl compatible con sistema avanzado
###############################################################################
def guardar_prolog(mapa):
    """
    Genera mundo.pl con:
    - Predicados dinámicos necesarios
    - Hechos del mundo (wumpus, oro, pozos)
    - Estado inicial del agente
    - Predicados auxiliares
    """
    lineas = []
    
    # Encabezado
    lineas.append("% " + "="*60)
    lineas.append("% MUNDO DE WUMPUS - Predicados Dinámicos y Estado del Mundo")
    lineas.append("% " + "="*60)
    lineas.append("% NOTA: Este archivo es GENERADO por Python (generar_mapa.py)")
    lineas.append("% Los hechos del mundo (wumpus, oro, pozos) se cargan desde aquí")
    lineas.append("% " + "="*60)
    lineas.append("")
    
    # Predicados dinámicos - Estado del Agente
    lineas.append("% " + "-"*46)
    lineas.append("% Predicados dinámicos - Estado del Agente")
    lineas.append("% " + "-"*46)
    lineas.append(":- dynamic posicion_agente/2.")
    lineas.append(":- dynamic agente_dir/1.")
    lineas.append(":- dynamic agente_tiene_flecha/1.")
    lineas.append(":- dynamic agente_tiene_oro/1.")
    lineas.append(":- dynamic agente_vivo/1.")
    lineas.append("")
    
    # Predicados dinámicos - Estado del Mundo
    lineas.append("% " + "-"*46)
    lineas.append("% Predicados dinámicos - Estado del Mundo")
    lineas.append("% " + "-"*46)
    lineas.append(":- dynamic wumpus/2.")
    lineas.append(":- dynamic wumpus_vivo/1.")
    lineas.append(":- dynamic oro/2.")
    lineas.append(":- dynamic pozo/2.")
    lineas.append("")
    
    # Predicados dinámicos - Base de Conocimiento
    lineas.append("% " + "-"*46)
    lineas.append("% Predicados dinámicos - Base de Conocimiento")
    lineas.append("% " + "-"*46)
    lineas.append(":- dynamic visitado/2.")
    lineas.append(":- dynamic seguro/2.")
    lineas.append(":- dynamic peligro/2.")
    lineas.append(":- dynamic posible_pozo/2.")
    lineas.append(":- dynamic posible_wumpus/2.")
    lineas.append("")
    
    # Configuración del Mundo
    lineas.append("% " + "-"*46)
    lineas.append("% Configuración del Mundo (Generado por Python)")
    lineas.append("% " + "-"*46)
    lineas.append(f"tamano({mapa['tamano']}).")
    lineas.append(f"wumpus({mapa['wumpus'][0]}, {mapa['wumpus'][1]}).")
    lineas.append(f"oro({mapa['oro'][0]}, {mapa['oro'][1]}).")
    
    for p in mapa['pozos']:
        lineas.append(f"pozo({p[0]}, {p[1]}).")
    
    lineas.append("")
    
    # Estado inicial del agente
    lineas.append("% " + "-"*46)
    lineas.append("% Estado inicial del agente")
    lineas.append("% " + "-"*46)
    lineas.append("posicion_agente(1, 1).")
    lineas.append("agente_dir(este).")
    lineas.append("agente_tiene_flecha(1).")
    lineas.append("agente_tiene_oro(0).")
    lineas.append("agente_vivo(1).")
    lineas.append("wumpus_vivo(1).")
    lineas.append("")
    
    # Conocimiento inicial
    lineas.append("% " + "-"*46)
    lineas.append("% Conocimiento inicial")
    lineas.append("% " + "-"*46)
    lineas.append("visitado(1, 1).")
    lineas.append("seguro(1, 1).")
    lineas.append("")
    
    # Predicados auxiliares
    lineas.append("% " + "="*60)
    lineas.append("% PREDICADOS AUXILIARES")
    lineas.append("% " + "="*60)
    lineas.append("")
    
    lineas.append("% " + "-"*46)
    lineas.append("% Validación de coordenadas (usa tamano dinámico)")
    lineas.append("% " + "-"*46)
    lineas.append("dentro(X, Y) :- ")
    lineas.append("    tamano(T),")
    lineas.append("    between(1, T, X), ")
    lineas.append("    between(1, T, Y).")
    lineas.append("")
    
    lineas.append("% " + "-"*46)
    lineas.append("% Celdas adyacentes")
    lineas.append("% " + "-"*46)
    lineas.append("adyacente(X, Y, X1, Y) :- ")
    lineas.append("    X1 is X + 1, ")
    lineas.append("    dentro(X1, Y).")
    lineas.append("adyacente(X, Y, X1, Y) :- ")
    lineas.append("    X1 is X - 1, ")
    lineas.append("    dentro(X1, Y).")
    lineas.append("adyacente(X, Y, X, Y1) :- ")
    lineas.append("    Y1 is Y + 1, ")
    lineas.append("    dentro(X, Y1).")
    lineas.append("adyacente(X, Y, X, Y1) :- ")
    lineas.append("    Y1 is Y - 1, ")
    lineas.append("    dentro(X, Y1).")
    lineas.append("")
    lineas.append("% Alias para compatibilidad")
    lineas.append("ady(X, Y, NX, NY) :- adyacente(X, Y, NX, NY).")
    lineas.append("")
    
    lineas.append("% " + "-"*46)
    lineas.append("% Vectores de dirección")
    lineas.append("% " + "-"*46)
    lineas.append("vector_dir(norte, 0, 1).")
    lineas.append("vector_dir(sur, 0, -1).")
    lineas.append("vector_dir(este, 1, 0).")
    lineas.append("vector_dir(oeste, -1, 0).")
    lineas.append("")
    
    lineas.append("% " + "-"*46)
    lineas.append("% Transformaciones de dirección")
    lineas.append("% " + "-"*46)
    lineas.append("girar_izq(norte, oeste).")
    lineas.append("girar_izq(oeste, sur).")
    lineas.append("girar_izq(sur, este).")
    lineas.append("girar_izq(este, norte).")
    lineas.append("")
    lineas.append("girar_der(norte, este).")
    lineas.append("girar_der(este, sur).")
    lineas.append("girar_der(sur, oeste).")
    lineas.append("girar_der(oeste, norte).")
    lineas.append("")
    
    # Utilidades de reinicio
    lineas.append("% " + "="*60)
    lineas.append("% UTILIDADES DE REINICIO")
    lineas.append("% " + "="*60)
    lineas.append("")
    lineas.append("% Reiniciar estado del agente (llamado desde Python al generar nuevo mapa)")
    lineas.append("reiniciar_agente :-")
    lineas.append("    retractall(posicion_agente(_, _)),")
    lineas.append("    retractall(agente_dir(_)),")
    lineas.append("    retractall(agente_tiene_flecha(_)),")
    lineas.append("    retractall(agente_tiene_oro(_)),")
    lineas.append("    retractall(agente_vivo(_)),")
    lineas.append("    retractall(wumpus_vivo(_)),")
    lineas.append("    retractall(visitado(_, _)),")
    lineas.append("    retractall(seguro(_, _)),")
    lineas.append("    retractall(peligro(_, _)),")
    lineas.append("    retractall(posible_pozo(_, _)),")
    lineas.append("    retractall(posible_wumpus(_, _)),")
    lineas.append("    ")
    lineas.append("    assertz(posicion_agente(1, 1)),")
    lineas.append("    assertz(agente_dir(este)),")
    lineas.append("    assertz(agente_tiene_flecha(1)),")
    lineas.append("    assertz(agente_tiene_oro(0)),")
    lineas.append("    assertz(agente_vivo(1)),")
    lineas.append("    assertz(wumpus_vivo(1)),")
    lineas.append("    assertz(visitado(1, 1)),")
    lineas.append("    assertz(seguro(1, 1)).")
    
    # Guardar en la carpeta prolog
    import os
    ruta_prolog = "prolog/mundo.pl"
    if os.path.exists("../prolog"):
        ruta_prolog = "../prolog/mundo.pl"
    
    with open(ruta_prolog, "w") as f:
        f.write("\n".join(lineas))

if __name__ == "__main__":
    mapa = generar_mapa()
    guardar_json(mapa)
    guardar_prolog(mapa)
    print("✓ Mapas generados: mundo.json y prolog/mundo.pl")
    print(f"  Tamaño: {mapa['tamano']}x{mapa['tamano']}")
    print(f"  Wumpus: {mapa['wumpus']}")
    print(f"  Oro: {mapa['oro']}")
    print(f"  Pozos: {len(mapa['pozos'])} pozos")
