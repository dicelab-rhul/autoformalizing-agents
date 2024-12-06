pd(T,R,P,S,C,D):-
            T>R,
            R>P,
            P>S,
            payoff(C,C,R,R),
            payoff(C,D,S,T),
            payoff(D,C,T,S),
            payoff(D,D,P,P).
