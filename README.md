# TJ Othello Tournament

### How to set up:
 * Clone this repository onto all machines/vms you will use
 * Use a virtualenv, conda, or system pip to install `requirements.md`

### How to run:
 * Launch the Django half with `python manage.py runserver 10770` or however else you run your Django server
   * Settings found in `othello/settings.py`
 * Launch the GameScheduler half with `python run_gamescheduler_server.py`
   * Settings found in `othello/gamescheduler/settings.py`
 * Read `run_tournament.md` for instructions on how to run a tournament

### How to develop:
 * Read all the comments that say `DEVEL` in `othello/settings.py`
 * Read `run_ai_layout.md` for an overview of how games are played
