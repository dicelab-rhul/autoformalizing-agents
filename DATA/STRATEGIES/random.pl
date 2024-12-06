select(_P, _O, Ms, M):-
	random(0, 1.0, RN),                                  % Generate random number
	round_to_decimal_places(RN, 3, floor, RRN),          % Round it down.
	length(Ms, L),                                       % Find length of list
	Thresh is  1 / L,    			             % Find threashold
	round_to_decimal_places(Thresh, 3, floor, RThresh),  % Round it
	once((
		idxmember(I, Ms, M),
		UL is I*RThresh,
		round_to_decimal_places(UL, 3, floor, RUL),  % Check it succeeds
		RRN < RUL
	)).

idxmember(I, L, El):-
	nth0(Ii, L, El),
	I is Ii + 1.

% Library for random strategy.

round_to_decimal_places(Number, DecimalPlaces, RoundingFunction, RoundedNumber) :-
    Multiplier is 10^DecimalPlaces,            % Multiplier for the specified decimal places
    call(RoundingFunction, Number * Multiplier, Temp), % Apply the rounding function (ceil or floor)
    RoundedNumber is Temp / Multiplier.        % Divide to get the result
