<h3 align="center">C++ Module Automatic Precompilation Utility</h3>

<div align="center">

[![Status](https://img.shields.io/badge/status-active-success.svg)]()
[![GitHub Issues](https://img.shields.io/github/issues/bit-creator/autopcm.svg)](https://github.com/bit-creator/autopcm/issues)
[![GitHub Pull Requests](https://img.shields.io/github/issues-pr/bit-creator/autopcm.svg)](https://github.com/bit-creator/autopcm/pulls)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](/LICENSE)

</div>

---

<p align="center"> This utility analyse dependencies in your C++ modules and precompile with your own settings
    <br> 
</p>

## Table of Contents

- [About](#about)
- [Getting Started](#getting_started)
- [Usage](#usage)
- [Contributing](#contributing)
- [Bug tracking](#bug_traking)
- [License](#license)
- [Conclusion](#conclusion)
- [Authors](#authors)

## About <a name = "about"></a>

This utility analyse your source code and build tree of dependencies for you modules, if you accidentally writed recursive import (module A importing module B and at the same time module B importing module A) you receive RecursionError. This is good choice for active develop where reletionships between modules changes very often. Every module precompiling start as soon as ready all imports, this provides a high degree of parallelism and minimizes the overall precompilation time. Also each subsequent run rewriting only changed modules (and all modules which importing changed modules)

## Getting Started <a name = "getting_started"></a>

### Prerequisites

Usually this utility only requires the python3 package,
```
sudo apt-get install python3
```
but for the best autopcm experience, python 3.9 or higher is recommended. 
Also for C++ development with modules you need to have a compiler that supports C++20 in general and C++ modules in particular, de facto this utility only works well enough with clang++ (version 14+) and libc++ but the choice of compiler and standard library is reserved for the future

### Installing

Clone repository 

```
git clone https://github.com/bit-creator/autopcm.git
```

and optionally you can create a symlink to the script to make it easier to work with it

run install script ```python3.9 install.py``` or ```python3 install.py``` depending on the interpreter with which you run the ```install.py``` script, that interpreter will be used to run ```autopcm``` by default, also your may rerun script with other interpreter

or do it manually:

add on first line in ```autopcm.py```
```
"#!path/to/python/interpreter"
```

and create symlink to file like this for example

```
ln -s $PWD/autopcm.py $HOME/bin/autopcm
```

## Usage <a name="usage"></a>

Setup json file for your build for more info looks through to [example.json](https://github.com/bit-creator/autopcm/blob/master/example.json)

Next pass json to autopcm:
```
autopcm --settings=/path/to/json/file
```

for build control your may use next flags:

```--parallel, --no-parallel``` enable multithread build process (default: True)

```--output OUTPUT```           File for compiler output [not supported]

```--rebuild```                 Boolean flag indicate full rebuild [not supported]

```--clean```                   Clean build files [not supported]

## Contributing <a name = "Contributing"></a>

We welcome contributions from everyone, regardless of their experience level. To get started, please follow these steps:

1. Fork the repository
2. Clone the repository to your local machine
3. Create a new branch for your changes
4. Make your changes and commit them
5. Push your changes to your forked repository
6. Create a pull request

Please make sure to read our [CONTRIBUTING.md](https://github.com/bit-creator/autopcm/blob/master/CONTRIBUTING.md) file before making any contributions.

## Bug reports and feature requests <a name = "bug_traking"></a>

If you encounter any bugs or issues while using autopcm, please report them to us. You can create a new issue on our GitHub repository and provide as much information as possible about the issue. We also welcome feature requests and suggestions for improving the autopcm.

## License <a name = "license"></a>

Our project is licensed under the MIT License. This means that anyone can use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software. Please read the LICENSE file for more information.

## Conclusion <a name = "conclusion"></a>

We appreciate your interest in our project and we look forward to working with you. If you have any questions or concerns, please don't hesitate to reach out to us. Together, we can create a great platform for managing tasks and projects.

## Authors <a name = "authors"></a>

- [@Illia Abernikhin](https://github.com/bit-creator)


