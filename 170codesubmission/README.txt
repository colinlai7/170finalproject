Instructions for algorithm 1 (k-way greedy):

1.	Put ./inputs folder into root directory (the same directory as solvers) 
2.	run "python greedy2.py" (python 3.4.3 used) to generate outputs into the ./outputs1 folder 
3.	Jump to Instructions for algorithm 2 below
4.	run "python comparer.py" to compare scores between the outputs1 and outputs2 folders and copies the higher score file into ./outputs

Instructions for algorithm 2 (hMETIS):
	The project structure for algorithm 2, where + indicates a directory and = indicates a file, is as follows:
+skeleton
	+all_inputs
		+large
		+medium
		+small
	+hmetis-1.5-linux
	+outputs
		+large
		+medium
		+small
	=output_scorer.py
	=solver_roughdraft3.py
=asdf.py

1.	ensure correct project structure
2.	download and install hmetis from glaros.dtc.umn.edu/gkhome/metis/hmetis/download and follow any relevant installation instructions for hmetis
3.	run solver_roughdraft3.py (python 3.5.2 used) to generate outputs into the ./outputs folder
4.	use mv to move the outputs file (renamed outputs2) into the parent directory of outputs1
5.	Instructions for algorithm 2 completed.  Return to Instructions for algorithm 1.
