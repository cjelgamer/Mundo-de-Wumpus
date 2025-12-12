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

marcar_seguro(X, Y) :-
    ( (posible_pozo(X, Y) ; posible_wumpus(X, Y)) ->
        true  
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

actualizar_kb_desde_percepciones :-
    posicion_agente(X, Y),
    obtener_percepciones(Ps),
    
    marcar_visitado(X, Y),
    marcar_seguro(X, Y),
    
    ( member(brisa, Ps) ->
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), Adj),
        forall(member((AX,AY), Adj), agregar_posible_pozo(AX,AY))
    ;
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), Adj2),
        forall(member((AX,AY), Adj2), (
            retractall(posible_pozo(AX,AY)),
            ( posible_wumpus(AX,AY) -> true ; marcar_seguro(AX,AY) )
        ))
    ),
    
    ( member(hedor, Ps) ->
        ( celda_con_hedor(X, Y) -> true ; assertz(celda_con_hedor(X, Y)) ),
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), AdjW),
        forall(member((AX,AY), AdjW), agregar_posible_wumpus(AX,AY)),
        deducir_ubicacion_wumpus
    ;
        findall((AX,AY), (adyacente(X,Y,AX,AY), \+ visitado(AX,AY)), Adj3),
        forall(member((AX,AY), Adj3), (
            retractall(posible_wumpus(AX,AY)),
            ( posible_pozo(AX,AY) -> true ; marcar_seguro(AX,AY) )
        ))
    ).

deducir_ubicacion_wumpus :-
    ubicacion_wumpus_confirmada(_, _), !.

deducir_ubicacion_wumpus :-
    findall((HX, HY), celda_con_hedor(HX, HY), CeldasConHedor),
    length(CeldasConHedor, NumHedores),
    NumHedores >= 2,
    CeldasConHedor = [(X1, Y1), (X2, Y2)|_],
    findall((WX, WY), 
            (adyacente(X1, Y1, WX, WY), 
             adyacente(X2, Y2, WX, WY),
             \+ visitado(WX, WY)),
            Candidatos),
    Candidatos = [(ConfX, ConfY)],
    assertz(ubicacion_wumpus_confirmada(ConfX, ConfY)),
    format('🎯 WUMPUS LOCALIZADO EN (~w, ~w)!~n', [ConfX, ConfY]), !.

deducir_ubicacion_wumpus.

es_segura(X, Y) :-
    seguro(X, Y),
    \+ posible_pozo(X, Y),
    \+ posible_wumpus(X, Y),
    \+ ubicacion_wumpus_confirmada(X, Y).

candidato_adyacente((AX,AY)) :-
    posicion_agente(X,Y),
    adyacente(X,Y,AX,AY).

celdas_seguras_no_visitadas(Lista) :-
    findall((AX,AY), 
            (candidato_adyacente((AX,AY)), 
             es_segura(AX,AY), 
             \+ visitado(AX,AY)),
            L0),
    sort(L0, Lista).

existen_celdas_seguras_globales :-
    seguro(X, Y),
    \+ visitado(X, Y),
    es_segura(X, Y), !.

celdas_visitadas_adyacentes(Lista) :-
    findall((AX,AY),
            (candidato_adyacente((AX,AY)),
             visitado(AX,AY)),
            L0),
    sort(L0, Lista).

% Entry point for decision making
decidir_accion(Percepciones, Accion) :-
    actualizar_kb_desde_percepciones,
    tomar_decision(Percepciones, Accion).

% DECISION PRIORITIES

tomar_decision(Percepciones, accion(agarrar)) :-
    member(brillo, Percepciones), !.

tomar_decision(_Percepciones, accion(disparar, WX, WY)) :-
    ubicacion_wumpus_confirmada(WX, WY),
    agente_tiene_flecha(1),
    wumpus_vivo(1),
    posicion_agente(X, Y),
    puede_disparar_a(X, Y, WX, WY), !.

tomar_decision(_Percepciones, accion(salir)) :-
    posicion_agente(1, 1),
    agente_tiene_oro(1), !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    agente_tiene_oro(1),
    posicion_agente(X, Y),
    (X, Y) \= (1, 1),
    adyacente(X, Y, NX, NY),
    visitado(NX, NY),
    DistActual is abs(X - 1) + abs(Y - 1),
    DistNueva is abs(NX - 1) + abs(NY - 1),
    DistNueva =< DistActual, !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    celdas_seguras_no_visitadas(Seguras),
    Seguras \= [],
    Seguras = [(NX, NY)|_], !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    seguro(GX, GY),
    \+ visitado(GX, GY),
    es_segura(GX, GY),
    member((NX, NY), Visitadas),
    es_segura(NX, NY),
    posicion_agente(X, Y),
    DistActual is abs(X - GX) + abs(Y - GY),
    DistNueva is abs(NX - GX) + abs(NY - GY),
    DistNueva =< DistActual, !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    member((NX, NY), Visitadas),
    es_segura(NX, NY), !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    \+ existen_celdas_seguras_globales,
    posicion_agente(X, Y),
    findall(Riesgo-(CX,CY),
            (adyacente(X, Y, CX, CY),
             \+ visitado(CX, CY),
             calcular_riesgo(CX, CY, Riesgo)),
            Riesgos),
    Riesgos \= [],
    keysort(Riesgos, [_MinRiesgo-(NX,NY)|_]), !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    Visitadas = [(NX, NY)|_], !.

tomar_decision(_Percepciones, accion(ir, NX, NY)) :-
    \+ existen_celdas_seguras_globales,
    celdas_visitadas_adyacentes(Visitadas),
    Visitadas \= [],
    Visitadas = [(NX, NY)|_], !.

tomar_decision(_, accion(girar)).

calcular_riesgo(X, Y, Riesgo) :-
    ( posible_pozo(X, Y) -> P = 1 ; P = 0 ),
    ( posible_wumpus(X, Y) -> W = 1 ; W = 0 ),
    Riesgo is P + W.

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

actualizar_posicion(NX, NY) :-
    retractall(posicion_agente(_, _)),
    assertz(posicion_agente(NX, NY)),
    (visitado(NX, NY) -> true ; assertz(visitado(NX, NY))).

puede_disparar_a(X, Y, TX, TY) :-
    X =:= TX, Y =\= TY, !.
puede_disparar_a(X, Y, TX, TY) :-
    Y =:= TY, X =\= TX, !.

direccion_hacia(X, Y, TX, TY, Dir) :-
    DX is TX - X,
    DY is TY - Y,
    ( DX > 0 -> Dir = este
    ; DX < 0 -> Dir = oeste
    ; DY > 0 -> Dir = norte
    ; DY < 0 -> Dir = sur
    ; Dir = este
    ).

% Acción de disparar
disparar(TX, TY) :-
    posicion_agente(X, Y),
    agente_tiene_flecha(1),
    puede_disparar_a(X, Y, TX, TY),
    !, % Cut para evitar fallbacks si las condiciones se cumplen
    
    % Calcular dirección
    
    direccion_hacia(X, Y, TX, TY, DirObjetivo),
    
    agente_dir(DirActual),
    ( DirActual = DirObjetivo ->
        true
    ;
        girar_hacia(DirActual, DirObjetivo)
    ),
    
    retract(agente_tiene_flecha(1)),
    assertz(agente_tiene_flecha(0)),
    format('🏹 DISPARANDO FLECHA hacia (~w, ~w)...~n', [TX, TY]),
    
    ( wumpus(TX, TY) ->
        retract(wumpus_vivo(1)),
        assertz(wumpus_vivo(0)),
        retractall(posible_wumpus(TX, TY)),
        retractall(ubicacion_wumpus_confirmada(TX, TY)),
        marcar_seguro(TX, TY),
        forall(adyacente(TX, TY, AX, AY), (
            retractall(posible_wumpus(AX, AY)),
            ( posible_pozo(AX, AY) -> true ; marcar_seguro(AX, AY) )
        )),
        writeln('💀 ¡WUMPUS ELIMINADO! Ahora es seguro explorar.')
    ;
        writeln('❌ Fallaste... No había Wumpus ahí.')
    ).

% Fallback debug clauses
disparar(_, _) :-
    \+ agente_tiene_flecha(1),
    writeln('❌ FALLO DISPARO: No tengo flechas.'), fail.

disparar(TX, TY) :-
    posicion_agente(X, Y),
    \+ puede_disparar_a(X, Y, TX, TY),
    format('❌ FALLO DISPARO: No estoy alineado. Pos: (~w,~w) Obj: (~w,~w)~n', [X, Y, TX, TY]), fail.
