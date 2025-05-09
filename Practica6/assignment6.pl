% LEXICON

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
lex(estudiante, noun(_,  singular)).

lex(bonita,  adjective(feminine,  singular)).
lex(bonitas, adjective(feminine,  plural)).
lex(bonito,  adjective(masculine, singular)).
lex(bonitos, adjective(masculine, plural)).

lex(muerde,  verb(transitive, singular)).
lex(muerden, verb(transitive, plural)).

lex(ladra,   verb(intransitive, singular)).
lex(ladran,  verb(intransitive, plural)).


% GRAMMAR

s  --> np(_, _), vp(_).

np(Gen, Num) --> det(Gen, Num), n(Gen, Num).
np(Gen, Num) --> det(Gen, Num), n(Gen, Num), adj(Gen, Num).

vp(Num) --> v(transitive, Num), np(_, _).
vp(Num) --> v(intransitive, Num).

det(Gen, Num) --> [Word], { lex(Word, det(Gen, Num)) }.
n(Gen, Num) --> [Word], { lex(Word, noun(Gen, Num)) }.
adj(Gen, Num) --> [Word], { lex(Word, adjective(Gen, Num)) }.
v(Type, Num) --> [Word], { lex(Word, verb(Type, Num)) }.
