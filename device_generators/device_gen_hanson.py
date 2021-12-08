import gmsh
from device_generators.device_gen import DeviceGenerator

class DeviceGeneratorHanson(DeviceGenerator):
    """ Class used to generate meshes for quantum dot systems which have 
    a geometry similar to that used by Hanson et al. in 
    W. Hansen, et al. Phys. Rev. Lett. 62, 2168 (1989).

    See also:
    Arvind Kumar, Steven E. Laux, and Frank Stern Phys. Rev. B 42, 5166 (1990)  
    
    Methods:
    ---
    new_cap_layer: Creates a cap layer by extruding a surface on the top
        of the device.
    """ 
    def new_cap_layer(self, surface_name, thickness, npts=10, label=None, 
        material=None, pdoping=0, ndoping=0):

        """ Creates a cap layer by extruding a surface on the top of the
        device.

        Args:
        ---
        surface_name (string): Physical name of surface to extrude.
        thickness (scalar): Thickness of the new layer.
        npts (int): number of points along the extruded dimension. 
        label (string): Label (physical name) for the layer. If None, generic 
            name used: 'cap_volume'
        material (material object): Material the dot region is made of. To be 
            used if the goal is to create a device. Defaults to silicon.
            The material object may be a string, or an object used in an 
            external finite element library to specify materials.
        pdoping (scalar): The density of acceptors in cm^-3.
                Default: 0.
        ndoping (scalar): The density of donors in cm^-3.
                Default: 0.
        """

        # Get entity tag of the surface to eb extruded
        ent_tags = self.get_ent_tag_from_name(surface_name, dim=2)
        ent_dimtags = [(2, e) for e in ent_tags]
        # Perform the extrusion
        extr_surf = gmsh.model.occ.extrude(ent_dimtags, 
                                            0,
                                            0,
                                            thickness,
                                            numElements=[npts]
                                            )
        gmsh.model.occ.synchronize()  

        # Volume entity tag of cap layer
        cap_tag = [e[1] for e in extr_surf if e[0]==3]
        # Create the physical volume
        cap_physical_volume = gmsh.model.addPhysicalGroup(3, cap_tag)

        # Naming cap volume
        if label is None: # generic name
            label=f'cap_volume'
        gmsh.model.setPhysicalName(3, cap_physical_volume, label)

        # Store material properties
        self.material_dict[label] = {
            'material': material,
            'pdoping':pdoping,
            'ndoping':ndoping
            }