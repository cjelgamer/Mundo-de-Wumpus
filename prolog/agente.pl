% :- consult('mundo.pl'). % Cargado explicitamente desde Python

% :- consult('mundo.pl'). % Cargado explicitamente desde Python

% ----------------------------------------------
% Reglas de percepción
% ----------------------------------------------

% Una celda tiene brisa si hay un pozo adyacente
brisa(X, Y) :-
    ady(X, Y, NX, NY),
    pozo(NX, NY).

% Una celda tiene hedor si el wumpus está cerca
hedor(X, Y) :-
    ady(X, Y, NX, NY),
    wumpus(NX, NY).

% ----------------------------------------------
% Movimiento permitido dentro del tablero
% ----------------------------------------------
ady(X, Y, NX, NY) :-
    tamano(T),
    (NX is X + 1, NX =< T, NY = Y;
     NX is X - 1, NX >= 1, NY = Y;
     NY is Y + 1, NY =< T, NX = X;
     NY is Y - 1, NY >= 1, NX = X).

% ----------------------------------------------
% Inferencias básicas
% ----------------------------------------------

% Si NO hay brisa ni hedor → todas las adyacentes son seguras
marcar_seguro(X, Y) :-
    \+ brisa(X, Y),
    \+ hedor(X, Y),
    forall(ady(X, Y, NX, NY),
        (seguro(NX, NY) -> true ; assertz(seguro(NX, NY)))).

% Si hay brisa → alguna adyacente tiene pozo
marcar_peligro(X, Y) :-
    (brisa(X, Y) ; hedor(X, Y)),
    forall(ady(X, Y, NX, NY),
        (peligro(NX, NY) -> true ; assertz(peligro(NX, NY)))).

% ----------------------------------------------
% Decisión del agente
% ----------------------------------------------

procesar_percepciones(X, Y, Percepciones) :-
    (member(brisa, Percepciones) -> marcar_peligro(X,Y) ; true),
    (member(hedor, Percepciones) -> marcar_peligro(X,Y) ; true),
    (\+ member(brisa, Percepciones), \+ member(hedor, Percepciones) ->
        marcar_seguro(X,Y) ; true).

% Estrategia 1: Ir a casilla SEGURA y NO VISITADA (Exploración)
decidir_accion(Percepciones, accion(ir, NX, NY)) :-
    posicion_agente(X, Y),
    procesar_percepciones(X, Y, Percepciones),
    ady(X, Y, NX, NY),
    seguro(NX, NY),
    \+ visitado(NX, NY),
    !.

% Estrategia 2: Si no hay nuevas, volver a casilla SEGURA (Backtracking seguro)
decidir_accion(Percepciones, accion(ir, NX, NY)) :-
    posicion_agente(X, Y),
    % No procesamos de nuevo, ya se hizo arriba si falló el corte? 
    % No, si falló en 'visitado', el corte no se ejecutó.
    ady(X, Y, NX, NY),
    seguro(NX, NY),
    !.

% Fallback: Girar si no hay opciones (raro si hay backtracking)
decidir_accion(_, accion(girar)).

% ----------------------------------------------
% Actualización de Estado (Llamado desde Python al mover)
% ----------------------------------------------
actualizar_posicion(NX, NY) :-
    retractall(posicion_agente(_, _)),
    assertz(posicion_agente(NX, NY)),
    (visitado(NX, NY) -> true ; assertz(visitado(NX, NY))).
