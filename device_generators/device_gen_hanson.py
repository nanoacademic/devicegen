import gmsh
from numpy import e
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
    
    def new_cap_layer(self, surface_name, thickness, npts=10, vol_label=None,
        bnd_label=None, material=None, pdoping=0, ndoping=0, 
        bnd_type=None, **bnd_params):

        """ Creates a cap layer by extruding a surface on the top of the
        device.

        Args:
        ---
        surface_name (string): Physical name of surface to extrude.
        thickness (scalar): Thickness of the new layer.
        npts (int): number of points along the extruded dimension. 
        vol_label (string): Label (physical name) for the layer. If None, 
            generic name used: 'cap_volume'
        bnd_label (string): Label (physical name) for the surface on top of
            the cap. If None, generic name used: 'cap_bnd'
        material (material object): Material the dot region is made of. To be 
            used if the goal is to create a device. Defaults to silicon.
            The material object may be a string, or an object used in an 
            external finite element library to specify materials.
        pdoping (scalar): The density of acceptors in cm^-3.
                Default: 0.
        ndoping (scalar): The density of donors in cm^-3.
                Default: 0.
        bnd_type (string): Type of boundary condition to enforce at the top surface
            of the cap. The possibilities are schottky, gate, or ohmic.
        **bnd_params: key word arguments for type of boundary condition under 
            consideration. 
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

        # Label cap volume
        cap_vol_tag = self._label_cap_volume(extr_surf, vol_label, 
                                            material, pdoping, ndoping) 
        # Label cap boundary
        self._label_cap_bnd(extr_surf, cap_vol_tag, bnd_label,
                            bnd_type, **bnd_params)                                  
        

    def _label_cap_volume(self, extr_surf, vol_label, mat, p, n):
        """ Labels the cap volume.

            Args:
            ---
            extr_surf (list of tuples): List of dimtags for the entities created
                by the extrude to generate the cap.
            vol_label (string): Label (physical name) for the layer. If None, 
                generic name used: 'cap_volume'
            mat (material object): Material the dot region is made of. To be 
                used if the goal is to create a device. Defaults to silicon.
                The material object may be a string, or an object used in an 
                external finite element library to specify materials.
            p (scalar): The density of acceptors in cm^-3.
                    Default: 0.
            n (scalar): The density of donors in cm^-3.
                    Default: 0.

            Returns
            ---
            cap_vol_tag (list of ints): List of the entity tags of the volumes
                created by the extrude to form cap. 
            """

        # Volume entity tag of cap layer
        cap_vol_tag = [e[1] for e in extr_surf if e[0]==3]
        # Create the physical volume
        cap_physical_volume = gmsh.model.addPhysicalGroup(3, cap_vol_tag)

        # Naming cap volume
        if vol_label is None: # generic name
            vol_label=f'cap_volume'
        gmsh.model.setPhysicalName(3, cap_physical_volume, vol_label)

        # Store material properties
        self.material_dict[vol_label] = {
            'material': mat,
            'pdoping':p,
            'ndoping':n
            }

        gmsh.model.occ.synchronize()  

        return cap_vol_tag

    def _label_cap_bnd(self, extr_surf, cap_vol_tag, bnd_label, 
        bnd_type=None, **bnd_params):
        """ Labels the cap boundary.

        Args:
        ---
        extr_surf (list of tuples): List of dimtags for the entities created
            by the extrude to generate the cap.
        cap_vol_tag (list of ints): List of the entity tags of the volumes
            created by the extrude to form cap.
        bnd_label (string): Label (physical name) for the surface on top of
            the cap. If None, generic name used: 'cap_bnd'
        bnd_type (string): Type of boundary condition to enforce at the top surface
            of the cap. The possibilities are schottky, gate, or ohmic.
        **bnd_params: key word arguments for type of boundary condition under 
            consideration. 
        """

        # Volume indeces
        vol_indeces = [extr_surf.index((3, v)) for v in cap_vol_tag]
        # Boundary entity tags
        bnd_tag = [extr_surf[i-1][1] for i in vol_indeces]
        
        # Create the physical surface
        bnd_physical_surface = gmsh.model.addPhysicalGroup(2, bnd_tag)

        # Naming cap volume
        if bnd_label is None: # generic name
            bnd_label=f'cap_bnd'
        gmsh.model.setPhysicalName(2, bnd_physical_surface, bnd_label)

        # Storing boundary conditions
        if bnd_type is not None:
            self.bnd_dict[bnd_label] = {
                'type': bnd_type,
                **bnd_params
            }

        gmsh.model.occ.synchronize()  

