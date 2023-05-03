# DeviceGen release notes

## devicegen 1.0.0

- Improved devicegen packaging (it is now possible to import a standard DeviceGenerator using ``from devicegen import DeviceGenerator``).
- Allow second order meshing when producing and saving meshes.
- Added feature that provides the ability to set the Gmsh GUI display color for device layers.
- Fixed a minor bug which resulted in multiple surface names for the same surface.
- Added the capability to label side surfaces after extrusion.

## devicegen 0.6.2

Added the possibility to create a dot region from layout surfaces.

## devicegen 0.6.1

- Added support for layouts defined in the .geo_unrolled format.
- Added top layer to the tutorial.
- Fixed bugs related to top layer usage.
- Fixed bug related to Gmsh version in the conda environment.

## devicegen 0.6.0

Added new_top_layer method to the device generator class to create, e.g., an oxide layer
and a global top gate by extruding a volume above the layout.

## devicegen 0.5.3

Modified the gated quantum dot example and tutorial to add an undoped AlGaAs spacer between the dopant (AlGaAs) and 2DEG (GaAs) regions.

## devicegen 0.5.2

- Allow dot regions that overlap with gates.
- Modified gated_qd.gds so that its coordinates coincide with gated_qd.txt in the examples/layouts folder.

## devicegen 0.5.1

Added a picture and short description of the device to build in the the tutorial.

## devicegen 0.5.0

First official beta release of devicegen.