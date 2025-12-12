% ============================================================
% MUNDO DE WUMPUS - Predicados Dinámicos y Estado del Mundo
% ============================================================
% NOTA: Este archivo es GENERADO por Python (generar_mapa.py)
% Los hechos del mundo (wumpus, oro, pozos) se cargan desde aquí
% ============================================================

% ----------------------------------------------
% Predicados dinámicos - Estado del Agente
% ----------------------------------------------
:- dynamic posicion_agente/2.
:- dynamic agente_dir/1.
:- dynamic agente_tiene_flecha/1.
:- dynamic agente_tiene_oro/1.
:- dynamic agente_vivo/1.

% ----------------------------------------------
% Predicados dinámicos - Estado del Mundo
% ----------------------------------------------
:- dynamic wumpus/2.
:- dynamic wumpus_vivo/1.
:- dynamic oro/2.
:- dynamic pozo/2.

% ----------------------------------------------
% Predicados dinámicos - Base de Conocimiento
% ----------------------------------------------
:- dynamic visitado/2.
:- dynamic seguro/2.
:- dynamic peligro/2.
:- dynamic posible_pozo/2.
:- dynamic posible_wumpus/2.
:- dynamic ubicacion_wumpus_confirmada/2.
:- dynamic celda_con_hedor/2.

% ----------------------------------------------
% Configuración del Mundo (Generado por Python)
% ----------------------------------------------
tamano(6).
wumpus(6, 1).
oro(5, 3).
oro(5, 4).
pozo(2, 2).
pozo(1, 3).
pozo(2, 6).
pozo(1, 6).
pozo(6, 4).
pozo(5, 5).

% ----------------------------------------------
% Estado inicial del agente
% ----------------------------------------------
posicion_agente(1, 1).
agente_dir(este).
agente_tiene_flecha(1).
agente_tiene_oro(0).
agente_vivo(1).
wumpus_vivo(1).

% ----------------------------------------------
% Conocimiento inicial
% ----------------------------------------------
visitado(1, 1).
seguro(1, 1).

% ============================================================
% PREDICADOS AUXILIARES
% ============================================================

% ----------------------------------------------
% Validación de coordenadas (usa tamano dinámico)
% ----------------------------------------------
dentro(X, Y) :- 
    tamano(T),
    between(1, T, X), 
    between(1, T, Y).

% ----------------------------------------------
% Celdas adyacentes
% ----------------------------------------------
adyacente(X, Y, X1, Y) :- 
    X1 is X + 1, 
    dentro(X1, Y).
adyacente(X, Y, X1, Y) :- 
    X1 is X - 1, 
    dentro(X1, Y).
adyacente(X, Y, X, Y1) :- 
    Y1 is Y + 1, 
    dentro(X, Y1).
adyacente(X, Y, X, Y1) :- 
    Y1 is Y - 1, 
    dentro(X, Y1).

% Alias para compatibilidad
ady(X, Y, NX, NY) :- adyacente(X, Y, NX, NY).

% ----------------------------------------------
% Vectores de dirección
% ----------------------------------------------
vector_dir(norte, 0, 1).
vector_dir(sur, 0, -1).
vector_dir(este, 1, 0).
vector_dir(oeste, -1, 0).

% ----------------------------------------------
% Transformaciones de dirección
% ----------------------------------------------
girar_izq(norte, oeste).
girar_izq(oeste, sur).
girar_izq(sur, este).
girar_izq(este, norte).

girar_der(norte, este).
girar_der(este, sur).
girar_der(sur, oeste).
girar_der(oeste, norte).

% ============================================================
% UTILIDADES DE REINICIO
% ============================================================

% Reiniciar estado del agente (llamado desde Python al generar nuevo mapa)
reiniciar_agente :-
    retractall(posicion_agente(_, _)),
    retractall(agente_dir(_)),
    retractall(agente_tiene_flecha(_)),
    retractall(agente_tiene_oro(_)),
    retractall(agente_vivo(_)),
    retractall(wumpus_vivo(_)),
    retractall(visitado(_, _)),
    retractall(seguro(_, _)),
    retractall(peligro(_, _)),
    retractall(posible_pozo(_, _)),
    retractall(posible_wumpus(_, _)),
    retractall(ubicacion_wumpus_confirmada(_, _)),
    retractall(celda_con_hedor(_, _)),
    
    assertz(posicion_agente(1, 1)),
    assertz(agente_dir(este)),
    assertz(agente_tiene_flecha(1)),
    assertz(agente_tiene_oro(0)),
    assertz(agente_vivo(1)),
    assertz(wumpus_vivo(1)),
    assertz(visitado(1, 1)),
    assertz(seguro(1, 1)).