% Select a move that is the opposite of the default move.
select(P, _, S, M) :-
    % Retrieve the default move for player P in state S
    holds(default_move(P, DefaultMove), S),
    % Generate a possible move M for player P in state S
    possible(move(P, M), S),
    % Ensure M is not the default move
    M \= DefaultMove.