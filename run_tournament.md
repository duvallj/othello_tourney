## Running a Tournament

The main entrypoint for running a tournament is `run_tournament_gamescheduler_server.py`,
which controls what type of tournament to run, timelimits, AIs participating,
etc. Currenly has no support for command-line flags, sorry, that was an
oversight.

#### Description of Variables
The variables in `run_tournament_gamescheduler_server.py` control various types
of behavior about the tournament

 * `AI_LIST`: the list of AIs that will participate in the tournament
 * `TOURNAMENT_NUM`: the "number" of the tournament we are running, used to
   create differently-named output files
 * `TOURNAMENT_TIMELIMIT`: the maximum number of time every AI can have per move
 * `TOURNAMENT_GAMES`: the maximum number of games to run concurrently
 * `TOURNAMENT_FILE`: the file to output to. Is actually just a file prefix
   currently

#### Tournament Logging
I have not implemented logging after each game yet (which would be really easy
to do, not sure why it hasn't been done), but there is a callback you can
provide that will get called with a list of results after the tournament is
over.

For most types of tournaments, this will be a list of `othello.gamescheduler.tournament_utils.SetData`
objects, which can be written to a CSV file using `othello.gamescheduler.tournament_utils.ResultsCSVWriter`.
Each `SetData` object contains information about the names of the AIs that
played in it, the sets those AIs came from, where the winner and loser will go
to, and who the winner was. Please read the code for info on that, I don't know
how to use PanDoc even though that would be really nice.

#### Types of Tournaments
As a note, all supported tournaments use an `othello.gamescheduler.tournament_server.SetTournamentScheduler` 
instead of an `othello.gamescheduler.server.GameScheduler`. The base class `TournamentScheduler` 
simply overrides callbacks to block outside clients from startings games and 
provides a simpler interface for the server to automatically start games. A 
`SetTournamentScheduler` will take in a list of sets to play and start as many 
as possible, keeping track of who won/lost what set to start later sets.

As a consequence of nearly every tournament being run by a `SetTournamentScheduler`,
we simply need an extra variable `SET_LIST` (containing a well-created list of sets)
to pass to the `SetTournamentScheduler` initializer.

 * Round Robin: use `create_round_robin` on `AI_LIST`
 * Everyone vs one person: use `create_everyone_vs(AI_LIST, "person")`
 * Single Elimination Bracket: use `create_single_elim_bracket(AI_LIST)`
 * Swiss-style tournament: use a `SwissTournamentScheduler` instead of a `SetTournamentScheduler`,
   also make sure that `AI_LIST` is passed in ranked order.

#### Analyzing Tournaments
Some simple scripts to analyze tournament results are in `analyze_tournament_csv.py`.
Currently, all you can do is stably re-rank AIs by wins or piece differential 
from the game results of a tournament.
This one does have command line flags, which should help explain things.
