from device_generators.device_gen_hanson import DeviceGeneratorHanson
import os

# Constants
## z dimensions
### Thickness of each material layer
cap_thick = 30 * 1e-3
dopant_thick = 20 * 1e-3
barrier_thick = 40 * 1e-3
two_deg_thick = 5 * 1e-3
substrate_thick = 80 * 1e-3 - two_deg_thick
nsubstrate_thick = 20 * 1e-3

### Number of mesh points along growth axis
cap_layers = 10
barrier_layers = 5
dopant_layers = 5
two_deg_layers = 10
substrate_layers = 20
nsubstrate_layers = 5

# Initializing the DeviceGenerator
script_dir = os.path.dirname(__file__)
file = script_dir + '/layouts/Hanson_qd.geo'
dG = DeviceGeneratorHanson(file)

# Relabelling surfaces
print('Relabelling surfaces...')
dG.relabel_surface('surf1', 'cap_surface')
dG.relabel_surface('surf2', 'etched_surface')

# Heterostructure stack
print('Setting up heterostructure stack...')
dG.new_layer(dopant_thick, dopant_layers, label='dopant_layer')
dG.new_layer(barrier_thick-dopant_thick, barrier_layers, label='barrier')
dG.new_layer(two_deg_thick, two_deg_layers, label='two_deg')
dG.new_layer(substrate_thick, substrate_layers, label='substrate')
dG.new_layer(nsubstrate_thick, nsubstrate_layers, label='doped_substrate')
# Cap layer
dG.new_cap_layer('cap_surface', cap_thick, npts=cap_layers, 
                vol_label="cap", bnd_label='cap_bnd')

print('Setting up back gate...')
dG.label_bottom('back_gate')

# Display final layout
dG.view()

# Save mesh
dG.save_mesh(mesh_name = script_dir + '/meshes/Hanson_dot.msh2')