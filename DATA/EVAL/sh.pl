sh(R,T,P,S,C,D):-
            R>T,
            T>P,
            P>S,
            payoff(C,C,R,R),
            payoff(C,D,S,T),
            payoff(D,C,T,S),
            payoff(D,D,P,P).
