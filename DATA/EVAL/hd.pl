hd(T,R,S,P,C,D):-
            T>R,
            R>S,
            S>P,
            payoff(C,C,R,R),
            payoff(C,D,S,T),
            payoff(D,C,T,S),
            payoff(D,D,P,P).
