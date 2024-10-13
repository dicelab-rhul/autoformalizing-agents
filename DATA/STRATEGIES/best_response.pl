% Best move according to the behaviour of the opponent
% in the last game.
select(P, O, S, M):-
    \+ holds(last_move(O, _), S),
    holds(default_move(P, M),S).
select(P, O, S, M):-
    holds(last_move(O, LMo), S),
    findall(Ui-Mi, (game(S, F), finally(outcome(P, Mi, Ui, O, LMo, Uo), F), Ui >= Uo), Options),
    sort(0, @>, Options, Ranked),
    highest(Ranked, M).

% assumes a ranked list of pairs of the form 'Utility - Move',
% the rank is according to Utility. Returns the first one, and
% any other ones, if they have the same utility. If the list
% is empty, i.e. there is no best move, then it returns 'nil'.
highest([_-M|_], M).
highest([U-_|R], Mi):-
    member(U-Mi, R).
highest([], nil).