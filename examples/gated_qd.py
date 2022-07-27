from device_generators.device_gen import DeviceGenerator
import pathlib

# Constants
## Mesh characteristic lengths
char_len = 15 * 1e-3
dot_char_len = char_len/2

## z dimensions
### Thickness of each material layer
cap_thick = 10 * 1e-3
barrier_thick = 25 * 1e-3
dopant_thick = 5 * 1e-3
spacer_thick = 5 * 1e-3
two_deg_thick = 5 * 1e-3
substrate_thick = 100 * 1e-3 - two_deg_thick
top_layer_thick = 10e-3

### Number of mesh points along growth axis
cap_layers = 5
barrier_layers = 5
dopant_layers = 10
spacer_layers = 10
two_deg_layers = 10
substrate_layers = 10
top_layers = 10

# Initializing the DeviceGenerator
path = pathlib.Path(__file__).parent.resolve()
file = str(path/'layouts/gated_qd.txt')
outfile=str(path/'layouts/gated_qd.geo')
dG = DeviceGenerator(file, outfile=outfile, h=char_len)

# Display layout
dG.view()

# Dot rectangle coordinates in microns
dot_xmin = 0.16900;  dot_ymin = 0.23100
dot_len_x = 0.131; dot_len_y = 0.197
dG.new_dot_rectangle(dot_xmin, dot_ymin, dot_len_x, dot_len_y, 
    h=dot_char_len)

# Display layout with dot region
dG.view()

# Relabelling surfaces
print('Relabelling surfaces...')
dG.relabel_surface('surf2', 'top_gate_1')
dG.relabel_surface('surf3', 'top_gate_2')
dG.relabel_surface('surf1', 'top_gate_3')
dG.relabel_surface('surf6', 'bottom_gate_1')
dG.relabel_surface('surf4', 'bottom_gate_2')
dG.relabel_surface('surf5', 'bottom_gate_3')

# Display layout with relabelled surfaces
dG.view()

# Heterostructure stack
print('Setting up heterostructure stack...')
dG.new_layer(cap_thick, cap_layers, label='cap')
dG.new_layer(barrier_thick-dopant_thick-spacer_thick, barrier_layers, label='barrier')
dG.new_layer(dopant_thick, dopant_layers, label='dopant_layer')
dG.new_layer(spacer_thick, spacer_layers, label='spacer_layer', 
    dot_region=True, dot_label="spacer_dot")
dG.new_layer(two_deg_thick, two_deg_layers, label='two_deg',
    dot_region=True, dot_label="two_deg_dot")
dG.new_layer(substrate_thick, substrate_layers, label='substrate', 
    dot_region=True, dot_label="substrate_dot")

# Display heterostructure stack
dG.view()
print('Setting up back gate...')

# Back gate
dG.label_bottom('back_gate')
dG.view()

# Top gate
dG.new_top_layer(
    top_layer_thick, npts=top_layers, bnd_label='top_gate', label='top'
    )

# Display final layout
dG.view()

# Save mesh
dG.save_mesh(mesh_name = str(path/'meshes/gated_dot.msh2'))