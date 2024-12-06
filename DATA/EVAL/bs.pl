bs(S2, S1, D, F, O):-
            S2>S1,
            S1>D,
            payoff(F,F,S1,S2),
            payoff(F,O,D,D),
            payoff(O,F,D,D),
            payoff(O,O,S2,S1).
