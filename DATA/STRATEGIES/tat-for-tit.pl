select(P, O, S, M):-
    \+ holds(last_move(O, _LMo), S),
    holds(default_move(P, M), S).
select(_P, O, S, M):-
    holds(last_move(O, Mo), S),
    opposite_move(Mo, M).