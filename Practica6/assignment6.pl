% --------------------------
% Vocabulario como hechos
% --------------------------

lex(det, la, f-sg).
lex(det, las, f-pl).
lex(det, el, m-sg).
lex(det, los, m-pl).
lex(det, una, f-sg).
lex(det, unas, f-pl).
lex(det, un, m-sg).
lex(det, unos, m-pl).

lex(n, perra, f-sg).
lex(n, perras, f-pl).
lex(n, perro, m-sg).
lex(n, perros, m-pl).
lex(n, hueso, m-sg).
lex(n, huesos, m-pl).
lex(n, estudiante, f-sg).
lex(n, estudiante, m-sg).

lex(adj, bonita, f-sg).
lex(adj, bonito, m-sg).
lex(adj, bonitas, f-pl).
lex(adj, bonitos, m-pl).

lex(vt, muerde, sg).
lex(vt, muerden, pl).

lex(vi, ladra, sg).
lex(vi, ladran, pl).

% --------------------------
% Gramática usando DCG
% --------------------------

s --> np(Num), vp(Num).

% Sintagma nominal: con o sin adjetivo
np(Num) --> det(Gen, Num), n(Gen, Num).
np(Num) --> det(Gen, Num), n(Gen, Num), adj(Gen, Num).

% Sintagma verbal: transitivo o intransitivo
vp(Num) --> vi(Num).
vp(Num) --> vt(Num), np(_).

% Reglas léxicas enlazadas al vocabulario
det(Gen, Num) --> [Word], { lex(det, Word, Gen-Num) }.
n(Gen, Num) --> [Word], { lex(n, Word, Gen-Num) }.
adj(Gen, Num) --> [Word], { lex(adj, Word, Gen-Num) }.
vt(Num) --> [Word], { lex(vt, Word, Num) }.
vi(Num) --> [Word], { lex(vi, Word, Num) }.

% --------------------------
% Evaluación directa de oraciones
% --------------------------

oraciones([ 
    oracion('Correcta 1', [la, estudiante, bonita, muerde, una, perra], true),
    oracion('Correcta 2', [el, perro, muerde, unos, huesos], true),
    oracion('Correcta 3', [una, perra, ladra], true),
    oracion('Correcta 4', [los, perros, bonitos, muerden, las, perras], true),
    oracion('Correcta 5', [un, estudiante, muerde, una, perra], true),
    oracion('Correcta 6', [la, perra, bonita, ladra], true),
    oracion('Incorrecta 1', [los, perras, muerden, un, estudiante], false),
    oracion('Incorrecta 2', [un, perro, ladra, un, hueso], false),
    oracion('Incorrecta 3', [una, bonita, perra], false),
    oracion('Incorrecta 4', [perro, muerde, una, perra], false),
    oracion('Incorrecta 5', [el, estudiantes, muerde, la, perra], false),
    oracion('Incorrecta 6', [los, perros, bonitos, muerden, perras], false)
]).

evaluar_oraciones :- 
    oraciones(Oraciones),
    nl, writeln('--- Resultados de evaluación ---'), nl,
    evaluar_lista(Oraciones),
    nl, writeln('--- Fin de evaluación ---'), nl.

evaluar_lista([]).
evaluar_lista([oracion(Nombre, Palabras, Esperado)|Resto]) :- 
    ( phrase(s, Palabras) -> 
        Resultado = true
    ; 
        Resultado = false
    ), 
    format("~w: ~w => ~w (~w)~n", [Nombre, Palabras, Resultado, Esperado]),
    evaluar_lista(Resto).

:- evaluar_oraciones.
