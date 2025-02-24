# QStatic

This is the research prototype for QStatic, a suite a tools for static analysis of OpenQASM, and eventually, other quantum programming languages.

## Current Tools
Currently, QStatic is comprised of two scripts - `parser.py` and `pattern_finder.py`.

## Parser
`parser.py` is a Python script which takes a marked up srcML file of an OpenQASM program and performs execution order analysis on it. It outputs the results to `out.json`.
To use `parser.py`, run the script along with the file you want to analyze - for example:
```
python parser.py examples/hadamard_cnot.qasm.xml
```

## Pattern Finder
`pattern_finder.py` is a Python script which takes in the `out.json` file generated from `parser.py`. This script statically analyzes the source code and identifies the presence of certain patterns and possible refactorings [1]. To run the script, do:
```
python pattern_finder.py
```

Additionally, the script can perform some refactoring of the OpenQASM source code. Running the script with `--refactor-horizontal-itr`, `--refactor-hadamard`, and/or `--refactor-encapsulation` will perform the corresponding refactor(s). The refactored file will be output next to the `.xml` file that was used to generate the `out.json`.

## Examples
Some example files to run the pattern analysis and refactorings are provided in the `examples` folder. These files have been manually marked-up, as full support of OpenQASM by srcML is still underway. 

## Citations
[1] Behler, J.A.C., Al-Ramadan, A.F., Baheri, B., Guan, Q., Maletic, J.I., "Supporting Program Analysis and Transformation of Quantum-Based Languages", in the Proceedings of the IEEE International Conference on Quantum Computing and Engineering (QCE), Montreal, Quebec, Canada, Sept. 15-20, 2024, 7 pages. 
