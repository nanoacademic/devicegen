import poissonfem.constants as ct
from poissonfem.poisson import Solver
from poissonfem.fem3d.mesh import SubMesh
from poissonfem.fem3d import analysis as an
from poissonfem import io

from device import materials as mt
from device.device import SubDevice
from device.solver_params import SolverParams
from device.gds_parser.device_gen import DeviceGenerator

import os
import numpy as np

script_dir = os.path.dirname(__file__)
file = script_dir + '/example.txt'

# characteristic lengths
char_len=15
dot_char_len=7.5

# z dimensions

# Thickness of each material layer
cap_thick = 10
barrier_thick = 25
dopant_thick = 5
two_deg_thick = 5
substrate_thick = 100-two_deg_thick

# Number of mesh points along growth axis
cap_layers = 10
barrier_layers = 5
dopant_layers = 10
two_deg_layers = 10
substrate_layers = 10

# Applied potentials
Vtop_1 = -0.5
Vtop_2 = -0.5
Vtop_3 = -0.5
Vbottom_1 = -0.5
Vbottom_2 = -0.5
Vbottom_3 = -0.5

# Work function of the metallic gates at midgap of GaAs
barrier = 0.834*ct.e    # n-type Schottky barrier height

# Doping density
doping = 3e18*1e6   # In SI units

# Generating device
dG = DeviceGenerator(file, outfile='example.geo', h=char_len)

# Dot rectangle coordinates in nm
dot_xmin = 499.66900e3;  dot_ymin = 499.73100e3
dot_len_x = 499.80000e3-499.66900e3; dot_len_y = 499.92800e3-499.73100e3
dG.create_dot_rectangle(dot_xmin, dot_ymin, dot_len_x, dot_len_y,
    h=5)

print('Setting up the top layer')
dG.setup_top_layer()

print('Setting up boundary conditions')
dG.relabel_surface('surf2', 'top_1', Vtop_1, barrier, bnd_type='schottky')
dG.relabel_surface('surf3', 'top_2', Vtop_2, barrier, bnd_type='schottky')
dG.relabel_surface('surf1', 'top_3', Vtop_3, barrier, bnd_type='schottky')
dG.relabel_surface('surf6', 'bottom_1', Vbottom_1, barrier, bnd_type='schottky')
dG.relabel_surface('surf4', 'bottom_2', Vbottom_2, barrier, bnd_type='schottky')
dG.relabel_surface('surf5', 'bottom_3', Vbottom_3, barrier, bnd_type='schottky')

print('Setting up heterostructure stack')
dG.new_layer(cap_thick, cap_layers, label='cap', material=mt.GaAs)
dG.new_layer(barrier_thick-dopant_thick, barrier_layers, label='barrier',
    material=mt.AlGaAs)
dG.new_layer(dopant_thick, dopant_layers, label='dopant_layer',
    material=mt.AlGaAs, ndoping=doping, dot_region=True, dot_label=["dopant_dot"])
dG.new_layer(two_deg_thick, two_deg_layers, label='two_deg', material=mt.GaAs,
    dot_region=True, dot_label=["two_deg_dot"])
dG.new_layer(substrate_thick, substrate_layers, label='substrate', 
    material=mt.GaAs, dot_region=True, dot_label=["substrate_dot"])

print('Setting up back gate')
dG.label_bottom('ohmic_bnd', 0, bnd_type='ohmic')

dG.view()

print('Creating device')
d = dG.create_device(inp_dict = {"T": 0.1},band_align=mt.GaAs)

print('Solving non-linear Poisson equation')
solver_params = SolverParams({"tol": 1e-3, "maxiter": 100}, problem="poisson")
solver = Solver(d, solver_params=solver_params)
conv = solver.solve()

##### PLOT THE CONDUCTION BAND EDGE IN eV ######
an.plot_slices(d.mesh, d.cond_band_edge()/ct.e, 
    z=-cap_thick*1e-9-barrier_thick*1e-9-dopant_thick*1e-9-1e-9,
    y=dot_ymin*1e-9+dot_len_y*1e-9/2., title="Conduction band edge (eV)")

print("Getting potential energy from electric potential")
d.get_potential_nrg()

# Save potential energy for later use
io.save(script_dir+"/output/potential_nrg.hdf5",d.V/ct.e)
io.save(script_dir+"/output/potential_nrg.vtu",d.V/ct.e,mesh=d.mesh)

print("Setting up submesh and subdevice")
submesh = SubMesh(d.mesh,['dopant_dot','two_deg_dot','substrate_dot'])
subdevice = SubDevice(d,submesh)

print("Solving Schrodinger's equation")
from device.schrodinger import Solver as SchrodingerSolver
schrod_solver = SchrodingerSolver(subdevice)
schrod_solver.solve()
subdevice.print_energies()

# Save energy levels and eigenfunctions
np.savetxt(script_dir+"/output/nrg_lvls.txt", subdevice.energies/ct.e)
io.save(script_dir+"/output/psi_0.vtu",subdevice.eigenfunctions[:,0],
    mesh=submesh)
io.save(script_dir+"/output/psi_1.vtu",subdevice.eigenfunctions[:,1],
    mesh=submesh)
io.save(script_dir+"/output/psi_2.vtu",subdevice.eigenfunctions[:,2],
    mesh=submesh)

##### PRINT ENERGY LEVELS IN eV ####
subdevice.print_energies()

#### PLOT FIRST TWO ENVELOPE FUNCTIONS IN QUANTUM DOT REGION #####
an.plot_slices(submesh, subdevice.eigenfunctions[:,0], 
    z=-cap_thick*1e-9-barrier_thick*1e-9-dopant_thick*1e-9-1e-9,
    y=dot_ymin*1e-9+dot_len_y*1e-9/2.,
    x=dot_xmin*1e-9+dot_len_x*1e-9/2., title="Ground state wavefunction")

an.plot_slices(submesh, subdevice.eigenfunctions[:,1], 
    z=-cap_thick*1e-9-barrier_thick*1e-9-dopant_thick*1e-9-1e-9,
    y=dot_ymin*1e-9+dot_len_y*1e-9/2.,
    x=dot_xmin*1e-9+dot_len_x*1e-9/2., title="1st excited state wavefunction")