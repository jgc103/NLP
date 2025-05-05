% --------------------------
% Vocabulario como hechos
% --------------------------

lex(la,   det(feminine,  singular)).
lex(las,  det(feminine,  plural)).
lex(el,   det(masculine, singular)).
lex(los,  det(masculine, plural)).
lex(una,  det(feminine,  singular)).
lex(unas, det(feminine,  plural)).
lex(un,   det(masculine, singular)).
lex(unos, det(masculine, plural)).

lex(perra,      noun(feminine,  singular)).
lex(perras,     noun(feminine,  plural)).
lex(perro,      noun(masculine, singular)).
lex(perros,     noun(masculine, plural)).
lex(hueso,      noun(masculine, singular)).
lex(huesos,     noun(masculine, plural)).
lex(estudiante, noun(feminine,  singular)).
lex(estudiante, noun(masculine, singular)).

lex(bonita,  adjective(feminine,  singular)).
lex(bonitas, adjective(feminine,  plural)).
lex(bonito,  adjective(masculine, singular)).
lex(bonitos, adjective(masculine, plural)).

lex(muerde,  verb(transitive, singular)).
lex(muerden, verb(transitive, plural)).

lex(ladra,   verb(intransitive, singular)).
lex(ladran,  verb(intransitive, plural)).

% --------------------------
% Gramática usando DCG
% --------------------------

s  --> np(_, _), vp(_).

np(Gen, Num) --> det(Gen, Num), n(Gen, Num).
np(Gen, Num) --> det(Gen, Num), n(Gen, Num), adj(Gen, Num).

vp(Num) --> vt(Num), np(_, _).
vp(Num) --> vi(Num).

det(Gen, Num) --> [Word], { lex(Word, det(Gen, Num)) }.
n(Gen, Num) --> [Word], { lex(Word, noun(Gen, Num)) }.
adj(Gen, Num) --> [Word], { lex(Word, adjective(Gen, Num)) }.
vt(Num) --> [Word], { lex(Word, verb(transitive, Num)) }.
vi(Num) --> [Word], { lex(Word, verb(intransitive, Num)) }.

% --------------------------
% Evaluación de oraciones
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
    oraciones(Lista),
    nl, writeln('--- Resultados de evaluación ---'), nl,
    evaluar_lista(Lista),
    nl, writeln('--- Fin de evaluación ---'), nl.

evaluar_lista([]).
evaluar_lista([oracion(Nombre, Palabras, Esperado)|Resto]) :-
    ( phrase(s, Palabras) -> Resultado = true ; Resultado = false ),
    format("~w: ~w => ~w (esperado: ~w)~n",
           [Nombre, Palabras, Resultado, Esperado]),
    evaluar_lista(Resto).

:- evaluar_oraciones.
