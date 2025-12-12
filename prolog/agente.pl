% ============================================================
% MUNDO DE WUMPUS - Agente Simple y Funcional
% ============================================================
% VERSIÓN ULTRA-SIMPLIFICADA SIN BUGS
% ============================================================

% ============================================================
% PERCEPCIONES
% ============================================================

hay_hedor :-
    posicion_agente(X, Y),
    wumpus_vivo(1),
    wumpus(WX, WY),
    adyacente(X, Y, WX, WY), !.
hay_hedor :- fail.

hay_brisa :-
    posicion_agente(X, Y),
    pozo(PX, PY),
    adyacente(X, Y, PX, PY), !.
hay_brisa :- fail.

hay_brillo :-
    posicion_agente(X, Y),
    oro(X, Y), !.
hay_brillo :- fail.

obtener_percepciones(Lista) :-
    findall(P, ( 
        (P = hedor, hay_hedor) ; 
        (P = brisa, hay_brisa) ; 
        (P = brillo, hay_brillo)
    ), Ps),
    sort(Ps, Lista).

% ============================================================
% BASE DE CONOCIMIENTO INTELIGENTE
% ============================================================

marcar_seguro(X, Y) :-
    ( (posible_pozo(X, Y) ; posible_wumpus(X, Y)) ->
        true  % No marcar como segura si tiene peligros
    ; seguro(X, Y) -> 
        true 
    ; 
        assertz(seguro(X, Y))
    ).

marcar_visitado(X, Y) :-
    ( visitado(X, Y) -> true 
    ; assertz(visitado(X, Y)) ).

agregar_posible_pozo(X, Y) :-
    ( posible_pozo(X, Y) -> 
        true 
    ; 
        (assertz(posible_pozo(X, Y)),
         retractall(seguro(X, Y))) 
    ).

agregar_posible_wumpus(X, Y) :-
    ( posible_wumpus(X, Y) -> 
        true 
    ; 
        (assertz(posible_wumpus(X, Y)),
         retractall(seguro(X, Y))) 
    ).

% Actualizar KB desde percepciones - SISTEMA INTELIGENTE
actualizar_kb_desde_percepciones :-
    posicion_agente(X, Y),
    obtener_percepciones(Ps),
    
    % Marcar celda actual como visitada y segura
    marcar_visitado(X, Y),
    marcar_seguro(X, Y),
    
    % RAZONAMIENTO SOBRE BRISA
    ( member(brisa, Ps) ->
        % HAY brisa -> Hay pozo en alguna adyacente
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), Adj),
        forall(member((AX,AY), Adj), agregar_posible_pozo(AX,AY))
    ;
        % NO hay brisa -> Adyacentes NO tienen pozos
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), Adj2),
        forall(member((AX,AY), Adj2), (
            retractall(posible_pozo(AX,AY)),
            ( posible_wumpus(AX,AY) -> true ; marcar_seguro(AX,AY) )
        ))
    ),
    
    % RAZONAMIENTO SOBRE HEDOR
    ( member(hedor, Ps) ->
        % HAY hedor -> Hay Wumpus en alguna adyacente
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), AdjW),
        forall(member((AX,AY), AdjW), agregar_posible_wumpus(AX,AY))
    ;
        % NO hay hedor -> Adyacentes NO tienen Wumpus
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), Adj3),
        forall(member((AX,AY), Adj3), (
            retractall(posible_wumpus(AX,AY)),
            ( posible_pozo(AX,AY) -> true ; marcar_seguro(AX,AY) )
        ))
    ).

% ============================================================
% DECISIÓN DEL AGENTE - SISTEMA INTELIGENTE
% ============================================================

% Verificar si celda es completamente segura
es_segura(X, Y) :-
    seguro(X, Y),
    \+ posible_pozo(X, Y),
    \+ posible_wumpus(X, Y).

% Candidatos adyacentes
candidato_adyacente((AX,AY)) :-
    posicion_agente(X,Y),
    adyacente(X,Y,AX,AY).

% Encontrar celdas seguras no visitadas ADYACENTES
celdas_seguras_no_visitadas(Lista) :-
    findall((AX,AY), 
            (candidato_adyacente((AX,AY)), 
             es_segura(AX,AY), 
             \+ visitado(AX,AY)),
            L0),
    sort(L0, Lista).

% Encontrar celdas seguras no visitadas en TODO EL MAPA (global)
existen_celdas_seguras_globales :-
    seguro(X, Y),
    \+ visitado(X, Y),
    es_segura(X, Y), !.

% Encontrar celdas visitadas adyacentes (para retroceder)
celdas_visitadas_adyacentes(Lista) :-
    findall((AX,AY),
            (candidato_adyacente((AX,AY)),
             visitado(AX,AY)),
            L0),
    sort(L0, Lista).

% ============================================================
% ESTRATEGIA DE DECISIÓN
% ============================================================

% PRIORIDAD 1: Si hay brillo, agarrar oro
decidir_accion(Percepciones, accion(agarrar)) :-
    member(brillo, Percepciones), !.

% PRIORIDAD 2: Si tengo oro y estoy en (1,1), SALIR
decidir_accion(_Percepciones, accion(salir)) :-
    posicion_agente(1, 1),
    agente_tiene_oro(1), !.

% PRIORIDAD 3: Si tengo oro, regresar a (1,1)
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    agente_tiene_oro(1),
    posicion_agente(X, Y),
    (X, Y) \= (1, 1),
    % Buscar celda adyacente que me acerque a (1,1)
    adyacente(X, Y, NX, NY),
    visitado(NX, NY),
    % Preferir movimientos que reduzcan distancia a (1,1)
    DistActual is abs(X - 1) + abs(Y - 1),
    DistNueva is abs(NX - 1) + abs(NY - 1),
    DistNueva =< DistActual, !.

% PRIORIDAD 4: Ir a celda SEGURA no visitada
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    actualizar_kb_desde_percepciones,
    celdas_seguras_no_visitadas(Seguras),
    Seguras \= [],
    Seguras = [(NX, NY)|_], !.

% PRIORIDAD 5: Retroceder a celda visitada segura para navegar hacia celdas seguras globales
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    actualizar_kb_desde_percepciones,
    existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    % Encontrar una celda segura global como objetivo
    seguro(GX, GY),
    \+ visitado(GX, GY),
    es_segura(GX, GY),
    % Elegir celda visitada adyacente que nos acerque al objetivo
    member((NX, NY), Visitadas),
    es_segura(NX, NY),
    posicion_agente(X, Y),
    % Calcular distancias (permitir movimientos que mantienen distancia)
    DistActual is abs(X - GX) + abs(Y - GY),
    DistNueva is abs(NX - GX) + abs(NY - GY),
    DistNueva =< DistActual, !.

% PRIORIDAD 5.5: Si hay celdas seguras globales pero no puedo acercarme, retroceder a cualquier visitada segura
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    member((NX, NY), Visitadas),
    es_segura(NX, NY), !.

% PRIORIDAD 6: TOMAR RIESGO CALCULADO - Solo si NO hay celdas seguras en TODO el mapa
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    actualizar_kb_desde_percepciones,
    % IMPORTANTE: Solo arriesgar si no hay MÁS celdas seguras EN TODO EL MAPA
    \+ existen_celdas_seguras_globales,
    posicion_agente(X, Y),
    % Encontrar celdas adyacentes no visitadas (incluyendo peligrosas)
    findall(Riesgo-(CX,CY),
            (adyacente(X, Y, CX, CY),
             \+ visitado(CX, CY),
             calcular_riesgo(CX, CY, Riesgo)),
            Riesgos),
    Riesgos \= [],
    % Ordenar por riesgo (menor primero)
    keysort(Riesgos, [_MinRiesgo-(NX,NY)|_]), !.

% PRIORIDAD 7: Retroceder a cualquier celda visitada cuando hay celdas seguras globales (navegación desesperada)
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    Visitadas = [(NX, NY)|_], !.

% PRIORIDAD 8: Retroceder a cualquier celda visitada (último recurso antes de girar)
decidir_accion(_Percepciones, accion(ir, NX, NY)) :-
    \+ existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    Visitadas = [(NX, NY)|_], !.

% FALLBACK: Girar (no hay movimientos)
decidir_accion(_, accion(girar)).

% ============================================================
% CÁLCULO DE RIESGO
% ============================================================

% Calcular nivel de riesgo de una celda
calcular_riesgo(X, Y, Riesgo) :-
    ( posible_pozo(X, Y) -> P = 1 ; P = 0 ),
    ( posible_wumpus(X, Y) -> W = 1 ; W = 0 ),
    Riesgo is P + W.

% ============================================================
% ACCIONES BÁSICAS
% ============================================================

girar_izquierda :-
    agente_dir(D),
    girar_izq(D, ND),
    retract(agente_dir(D)),
    assertz(agente_dir(ND)),
    format('Giro izquierda -> ~w~n', [ND]).

girar_derecha :-
    agente_dir(D),
    girar_der(D, ND),
    retract(agente_dir(D)),
    assertz(agente_dir(ND)),
    format('Giro derecha -> ~w~n', [ND]).

mover :-
    posicion_agente(X, Y),
    agente_dir(D),
    vector_dir(D, DX, DY),
    NX is X + DX,
    NY is Y + DY,
    ( dentro(NX, NY) ->
        retract(posicion_agente(X, Y)),
        assertz(posicion_agente(NX, NY)),
        (visitado(NX, NY) -> true ; assertz(visitado(NX, NY))),
        format('Movido de (~w,~w) a (~w,~w)~n', [X, Y, NX, NY])
    ;
        writeln('BUMP! Pared.')
    ).

agarrar :-
    posicion_agente(X, Y),
    ( oro(X, Y) ->
        retract(oro(X, Y)),
        retract(agente_tiene_oro(0)),
        assertz(agente_tiene_oro(1)),
        writeln('ORO RECOGIDO!')
    ;
        writeln('No hay oro aqui.')
    ).

% ============================================================
% NAVEGACIÓN
% ============================================================

mover_hacia(TX, TY) :-
    posicion_agente(X, Y),
    DX is TX - X,
    DY is TY - Y,
    ( DX > 0 -> Deseado = este
    ; DX < 0 -> Deseado = oeste
    ; DY > 0 -> Deseado = norte
    ; DY < 0 -> Deseado = sur
    ; Deseado = este
    ),
    agente_dir(D),
    ( D = Deseado ->
        mover
    ;
        girar_hacia(D, Deseado),
        mover
    ).

girar_hacia(D, Deseado) :-
    girar_izq(D, L),
    girar_der(D, R),
    ( R = Deseado ->
        girar_derecha
    ; L = Deseado ->
        girar_izquierda
    ;
        girar_derecha,
        girar_derecha
    ).

mover_a_celda_adyacente((AX, AY)) :-
    posicion_agente(X, Y),
    ( adyacente(X, Y, AX, AY) ->
        format('Moviendo a (~w,~w)...~n', [AX, AY]),
        DX is AX - X,
        DY is AY - Y,
        ( DX =:= 1 -> Deseado = este
        ; DX =:= -1 -> Deseado = oeste
        ; DY =:= 1 -> Deseado = norte
        ; DY =:= -1 -> Deseado = sur
        ),
        agente_dir(D),
        ( D = Deseado ->
            mover
        ;
            girar_hacia(D, Deseado),
            mover
        )
    ;
        format('ERROR: (~w,~w) no es adyacente~n', [AX, AY])
    ).

% Actualizar posición
actualizar_posicion(NX, NY) :-
    retractall(posicion_agente(_, _)),
    assertz(posicion_agente(NX, NY)),
    (visitado(NX, NY) -> true ; assertz(visitado(NX, NY))).
