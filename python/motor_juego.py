import json
from comunicacion import consulta_prolog

def cargar_mapa():
    with open("mundo.json") as f:
        return json.load(f)

def ejecutar_turno(percepcion):
    accion = consulta_prolog("decidir_accion", [percepcion])
    print("Agente decidió:", accion)
    return accion

if __name__ == "__main__":
    mapa = cargar_mapa()

    print("Mapa cargado:", mapa)

    while True:
        percepcion = input("Percepción actual (lista): ")
        if percepcion == "salir":
            break

        ejecutar_turno(percepcion)
