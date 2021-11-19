# Readme for devicegen

## About devicegen

<<<<<<< HEAD
`devicegen` is a gated-quantum-dot device generator targeting. It facilitates the creation of `Gmsh` mesh files corresponding to a gate geometry defined in a GDS layout text file.

## Installation

To install `devicegen`, we recommend first creating the `device_gen` environment with `conda` using:

```bash
$ conda env create -f environment.yml
$ conda activate device_gen
```

and then running:

```bash
$ pip install .
```

in the devicegen repository.
=======
devicegen is a gated quantum dot device generator targeting mainly spin qubit applications. It enables to create Gmsh mesh files corresponding to a gate geometry defined in a GDS layout text file.
>>>>>>> 87d15396486fe9383c47712af6bd5f06940d9a68

## Community

You are welcome to create new features for `devicegen`. To do so, please create a user-owned fork of the devicegen repository and submit a pull request containing your modifications.

## Copyright

`devicegen` is free software: you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation, either version 3 of the License, or (at your option) any later version. See the file COPYING in http://www.gnu.org/licenses/, for a description of the GNU General Public License terms under which you can copy the files.

## Reporting bugs in devicegen

Please report any bug by creating an issue on the devicegen GitHub page: https://github.com/nanoacademic/devicegen/issues.

## Scientific research

If you use `devicegen` in any work leading to a scientific publication, we would love to know ! Please contact us at: info@nanoacademic.com.

## Contacting Nanoacademic Technologies

The devicegen package is developed and maintain by Nanoacademic Technologies. For any question that is not a bug report, please contact us at: info@nanoacademic.com.

## About Gmsh

`devicegen` uses `Gmsh` to create its meshes. `Gmsh` is "an open source 3D finite element mesh generator with a built-in CAD engine and post-processor", which is released under the GPL license. For more information on `Gmsh`, please visit: https://gmsh.info/.
