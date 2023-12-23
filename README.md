# decaf-compiler

### Description
This is a compiler that can compile a Java-like language called Decaf into abstract machine code. It uses the [PLY library](https://www.dabeaz.com/ply/) to tokenize and parse input files. It then employs different strategies to resolve scopes & names, perform type checking, and generating lower level code. The compiler is capable of tackling many concepts that are, but not limited to: scopes, visibility, inheritance, name resolution, and register allocation. *Note: this is a very rudimentary compiler, so some certain Java features like overloaded methods, overloaded constructors, and arrays are not supported.*

### Authors
- Brain Shao ([brian.shao@stonybrook.edu](mailto:brian.shao@stonybrook.edu))
- Yangfa Wu ([yangfa.wu@stonybrook.edu](mailto:yangfa.wu@stonybrook.edu))

### Commands
- use `make install` to get ply
- use `make run` to run [decaf_compiler.py](src/decaf_compiler.py) on all `*.decaf` files inside the [input](input) folder
- use `make clean` to clean repository of ignored output files
