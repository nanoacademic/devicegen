import functools
import operator
import copy

import gmsh

from device_generators.gds_parser import Parser

class DeviceGenerator:
    """ Class used to generate QTCAD device objects.

    Attributes:
    ---
    first_layer (boolean): If True, the method new layer has not yet been run. 
        Only a 2D layout is loaded into gmsh.
    bottom_surface (list): Tags for the bottom-most surfaces that are extruded 
        to create new layers.
    layer_counter (int): counter for layers created. Used for generatic names of
        physical groups.
    s_counter (int): counter for surfaces created. Used for generatic names of
        physical groups.
    vol_entities (dictionary): keeps track of volume entities tags under each
        surface of the layout
    dot_tag (list): Tags of bottom most surfaces in x-y plane where we expect
        electrons/holes to be localized.
    dot_volume (list): Contains the tags of the different volumes that we expect
        to contain dots.
    dot_counter (int): counter for dots created. Used for generating names of
        physical groups for dots.
    field_counter (int): counter for mesh fields created.
    scale (scalar): Factor by which node coordinates are multiplied for conversion 
        to SI units.
    material_dict (dictionary): Contains the material properties of each physical volume
        of the generated mesh/device 
    bnd_dict (dictionary): Contains the boundary conditions that are to be enforced for 
        the generated mesh/device 

    Methods:
    ---
    view: Opens gmsh GUI to visualize device.
    save_mesh: Saves the generated mesh.
    new_dot_rectangle: Creates a rectangle where we expect an electron/hole 
        to be localized in the x and y directions.
    relabel_surface: Relabel surface using their old label. This function 
        can also be used to set the boundary condition on the surface being 
        relabelled.
    label_bottom: Label the bottom surface of the device.
    new_layer: Creates a layer by extruding the bottom-most surface.
    label_surface: Gives a physical name to a volume entity.
    label_volume: Gives a physical name to a volume entity.
    new_box_field: Create a box field
    min_field: Uses the minimum of all defined fields as the background mesh
        field.
    split_surface: Splits a physical surface into seperate physical surfaces 
        for each entity
    get_volumes: Get the volumes under a surface with a given name
    get_surfaces: Get the surfaces under a surface with a given name
    """

    def label_bottom(self, label, *bnd_params, bnd_type=None):
        """ Label the bottom surface of the device

        Args:
        ---
        label (string): Label for the bottom surface. 
        *bnd_params: arguments for type of boundary condition under consideration.
            See device.py for types boundary conditions available
        bnd_type (string): Type of boundary condition to enforce. The possibilities are
            schottky, gate, or ohmic.
        """
        # Check that we are not trying to label the top surface
        if self.first_layer:
            raise ValueError("This is the first layer, not the bottom!")
        
        # Label the bottom surface
        tags = [tag[1] for tag in self.bottom_surface]
        physical_surface = gmsh.model.addPhysicalGroup(2, tags, tag=-1)
        gmsh.model.setPhysicalName(2, physical_surface, label)

        gmsh.model.occ.synchronize()

        # Storing boundary condition
        if bnd_type is not None:
            self.bnd_dict[label] = {
                'type': bnd_type,
                'params': bnd_params
            }

    def label_volume(self, ent_tags, new_name, material=None, 
        pdoping=0, ndoping=0):
        """ Gives a physical name to a volume entity.
        
        Args:
        ---
        ent_tags (list): Entities to name.
        new_name (string): Phsysical name
        material (material object): Material the dot region is made of. To be used if 
            the goal is to create a device. Defaults to silicon.
        pdoping (scalar): The density of acceptors in cm^-3.
                Default: 0.
        ndoping (scalar): The density of donors in cm^-3.
                Default: 0.
        """

        # Label volume
        new_phys_group = self.label_entity(3, ent_tags, new_name)

        # Store material properties
        self.material_dict[new_name] = {
            'material': material,
            'pdoping':pdoping,
            'ndoping':ndoping
            }
    
        return new_phys_group


    def label_surface(self, ent_tags, new_name, *bnd_params, bnd_type=None):
        """ Gives a physical name to a surface entity.
        
        Args:
        ---
        ent_tags (list): Entities to name.
        new_name (string): Phsysical name
        *bnd_params: arguments for type of boundary condition under consideration.
            See device.py for types boundary conditions available
        bnd_type (string): Type of boundary condition to enforce. The 
            possibilities are schottky, gate, or ohmic.
        """
        # Label surface
        new_phys_group = self.label_entity(2, ent_tags, new_name)

        # Storing boundary conditions
        if bnd_type is not None:
            self.bnd_dict[new_name] = {
                'type': bnd_type,
                'params': bnd_params
                }
    
        return new_phys_group

    def label_entity(self, dim, ent_tags, new_name, verbose=False):
        """ Gives a physical name to an entity.

        Args:
        ---
        dim (2 or 3): dimension of the entity to be named.
        ent_tags (list): Entities to name.
        new_name (string): Phsysical name
        verbose (boolean): If warning should be printed or not
        """
        for tag in ent_tags:
            # Get the pysical group
            phys_tags = gmsh.model.getPhysicalGroupsForEntity(dim, tag)
            if len(phys_tags) != 0:
                phys_tag = phys_tags[0]
                # Get entites of this physical group
                ent_list = gmsh.model.getEntitiesForPhysicalGroup(dim, phys_tag)
                # Remove name and phyiscal group
                name = gmsh.model.getPhysicalName(dim, phys_tag)
                gmsh.model.removePhysicalGroups([(dim,phys_tag)])
                gmsh.model.removePhysicalName(name)
                gmsh.model.occ.synchronize()

                # Remove the entity of interest from the list
                ent_list = list(ent_list)
                ent_list.remove(tag)
                # If we are not using the name and the there are entities left
                if (name != new_name) and ent_list != []: 
                    # Give back name to remaining entities 
                    phys_group = gmsh.model.addPhysicalGroup(dim, ent_list)
                    gmsh.model.setPhysicalName(dim, phys_group, name)
                else:
                    m=f'Warning new name {new_name} already in use'
                    if verbose:
                        print(m)

        # Give new name to phys_group
        new_phys_group = gmsh.model.addPhysicalGroup(dim, ent_tags)
        gmsh.model.setPhysicalName(dim, new_phys_group, new_name)
        gmsh.model.occ.synchronize()

        return new_phys_group

    def min_field(self):
        """ Uses the minimum of all defined fields as the background mesh
        field.
        """
        # Create the min field
        field_tag = self.field_counter
        gmsh.model.mesh.field.add("Min", field_tag)
        gmsh.model.mesh.field.setNumbers(field_tag,
                                         "FieldsList",
                                         [i for i in range(1, field_tag)])
        # Apply the min field
        gmsh.model.mesh.field.setAsBackgroundMesh(field_tag)

        # Update counter
        self.field_counter+=1

    def new_box_field(self, xmin, xmax, ymin, ymax, VIn, VOut=None):
        """ Create a box field

        Args:
        ---
        VIn (scalar): characteristic length of field inside box.
        VOut (scalar): characteristic length of field outside box.
        xmin (scalar): minimal x value of box.
        xmax (scalar): maximal x value of box.
        ymin (scalar): minimal y value of box.
        ymax (scalar): maximal y value of box.
        """
        # Clear any meshes already present
        gmsh.model.mesh.clear(dimTags=[])

        # Create Box field
        gmsh.model.mesh.field.add("Box", self.field_counter)
        gmsh.model.mesh.field.setNumber(self.field_counter, "VIn", VIn)
        gmsh.model.mesh.field.setNumber(self.field_counter, "XMin", xmin)
        gmsh.model.mesh.field.setNumber(self.field_counter, "XMax", xmax)
        gmsh.model.mesh.field.setNumber(self.field_counter, "YMin", ymin)
        gmsh.model.mesh.field.setNumber(self.field_counter, "YMax", ymax)
        if VOut is not None:
            gmsh.model.mesh.field.setNumber(self.field_counter, "VOut", VOut)

        gmsh.model.mesh.field.setAsBackgroundMesh(self.field_counter)
        # Increase field count
        self.field_counter += 1
        # Synchronize
        gmsh.model.occ.synchronize()

    def new_layer(self, thickness, npts=10, label=None, dot_region=False, dot_label=None,
        material=None, pdoping=0, ndoping=0):
        """ Creates a layer by extruding the bottom-most surface.

        Args:
        ---
        thickness (scalar): Thickness of the new layer.
        npts (int): number of points along the extruded dimension. 
        label (string): Label (physical name) for the layer. If None, generic name used,
            e.g. 'Volume1'
        dot_region (boolean): If True, will consider the volume when creating the 
            dot region under the 'dot_rectangles'
        dot_label (string): Physical name for the dot region in the given layer. If
            None, a generic name is used.
        material (material object): Material the dot region is made of. To be used if 
            the goal is to create a device. Defaults to silicon.
        pdoping (scalar): The density of acceptors in cm^-3.
                Default: 0.
        ndoping (scalar): The density of donors in cm^-3.
                Default: 0.

        """

        self.first_layer = False
        surf_to_extrude = self.bottom_surface

        extr_surf = gmsh.model.occ.extrude(surf_to_extrude, 0, 0, -thickness, numElements=[npts])
        # Update attribute vol_entities.
        self._update_vol_entities(surf_to_extrude, extr_surf, self.vol_entities)

        # keep track of bottom surfaces in case an additional layer is added
        self.bottom_surface = self.track_surface(extr_surf)
        # Update regions related to dots    
        self._update_dot_region(self.dot_tag, self.dot_volume, extr_surf, dot_region, 
            label=dot_label, material=material, pdoping=pdoping, ndoping=ndoping)

        # Tags of all volumes part of dot volume
        flat_dot_vol = functools.reduce(operator.iconcat, self.dot_volume, [])

        # Check which are not part of dot volumes
        V = [e for e in extr_surf if e[0]==3] # Volumes generated from extrusion
        volumes = [vol[1] for vol in V if vol[1] not in flat_dot_vol]

        gmsh.model.occ.synchronize()  

        # Add a physical name.
        physical_volume = gmsh.model.addPhysicalGroup(3, volumes, tag=-1)

        if label is None: # generic name
            label=f'volume{self.layer_counter}'
        gmsh.model.setPhysicalName(3, physical_volume, label)
        self.layer_counter += 1

        # Store material properties
        self.material_dict[label] = {
            'material': material,
            'pdoping':pdoping,
            'ndoping':ndoping
            }
    
        gmsh.model.occ.synchronize()  

    
    def get_volumes(self, name, layer=None):
        """ Get the volumes under a surface with a given name
        Args:
        ---
        name (string): name of surface under which we want the volume entity
            tags
        layer (None or int): Specifies the layer for which we want the volume 
            entity tags. If None, returns volumes for all layers.     
        """
        # Entitity tags for a certain surface naem
        ents = self.vol_entities[name][1::2]
        # If layer is specified, get volumes for a specific layer
        if layer is not None:
            ents = ents[layer]
        # If layer is unspecified get all volumes. 
        if layer is None:
            ents = [item for sublist in ents for item in sublist]
            
        return [e[1] for e in ents]
      
    def get_surfaces(self, name, layer=None):
        """ Get the surfaces under a surface with a given name
        Args:
        ---
        name (string): name of surface under which we want the surface entity
            tags
        layer (None or int): Specifies the layer for which we want the surface 
            entity tags. If None, returns surfaces between all layers.

        Note:
        If layer = 0 then the output is the surfaces named name.     
        """
        # Entitity tags for a certain surface name
        ents = self.vol_entities[name][0::2]
        # If layer is specified, get volumes for a specific layer
        if layer is not None:
            ents = ents[layer]
        # If layer is unspecified get all volumes. 
        if layer is None:
            ents = [item for sublist in ents for item in sublist]
            
        return [e[1] for e in ents]

    def _update_vol_entities(self, surf_to_extr, extr_surf, vol_entities):
        """ Update attribute vol_entities to include the volumes and surfaces
        generate by creating a new layer.
        Args:
        ---
        surf_to_extr (list): List of surface entities that are extruded.
        extr_surf (list): List of entities generated by the extrusion in the 
            method new_layer.
        vol_entities (dictionary): Dictionary keeping track of volumes.
        
        """
        vols = [e for e in extr_surf if e[0] == 3]

        for key in vol_entities:
            # Get the bottom-most surface for key
            surfs = vol_entities[key][-1]
            # Create a list of volumes under the surface with physical name
            # given by the key
            vol_list = []
            for s in surfs:
                id = surf_to_extr.index(s)
                vol_list.append(vols[id])
                # Update attribute
            vol_entities[key] = vol_entities[key] + [vol_list]

            # Get the bottom-most volume for key
            new_vols = vol_entities[key][-1]
            # Create a list of the surfaces generated by the extrude under the
            # surface with physical name given by the key
            new_surfs = []
            for v in new_vols:
                id = extr_surf.index(v) - 1
                new_surfs.append(extr_surf[id])
            # Update attribute
            vol_entities[key] = vol_entities[key] + [new_surfs]
    

    def track_surface(self, extr_surf):
        """ Keep track of surface entities.
        Args:
        ---
        extr_surf (list): Entities created by an extrusion.
        """
        surface = []
        # Volumes generated from extrusion
        V = [e for e in extr_surf if e[0]==3] 
        for v in V:
            id_vol = extr_surf.index(v)
            surface.append(extr_surf[id_vol - 1] )
        return surface


    def _update_dot_region(self, dot_tags, dot_volume, extr_surf, dot_region, label=None,
        material=None, pdoping=0, ndoping=0):
        """ Updates the attributes dot_volume and dot_tag and labels dot region.
        Args:
        ---
        dot_tag (list): Tags of bottom most surfaces in x-y plane where we expect
            electrons/holes to be localized.
        dot_volume (list): Tags of the different volumes that we expect
            to contain dots.
        surf_to_extrude (list of gmsh entities): list of surfaces that are extruded.
        extr_surf (list of gmsh entities): entities created from gmsh's extrusion 
            operation
        dot_region (boolean): If true, the attribute dot_volume is modified.
            The volumes created in the layer by extruding the surfaces in dot_tag 
            are appended.
        label (string): Physical name for the dot region in the given layer. If
            None, a generic name is used. 
        material (material object): Material the dot region is made of. To be used if 
            the goal is to create a device. Defaults to silicon.
        pdoping (scalar): The density of acceptors in cm^-3.
                Default: 0.
        ndoping (scalar): The density of donors in cm^-3.
                Default: 0.
        """
        gmsh.model.occ.synchronize()
        # Convert label to a list if it is a string.  
        if isinstance(label, str):
            label = [label]

        # loop over all entites tagged created by the create_dot_rectangle() method
        for i, dot in enumerate(dot_tags): 
            
            # Find Volume corresponding to dot region
            V = [e for e in extr_surf if e[0]==3] # All volumes created
            for v in V:
                if (2, dot[-1]) in gmsh.model.getBoundary([v], oriented=False):
                    vol_id = extr_surf.index(v)
                    break
            # Find bottom surface of volume
            dot.append(extr_surf[vol_id - 1][1])

            if dot_region:
                # Include the create volume in the dot volumes
                dot_volume[i].append(extr_surf[vol_id][1])

                if label is None:
                    dot_label = f'dot{i}-{self.layer_counter}'
                else:
                    dot_label = label[i]
                # Add a physical name.
                phys_volume = gmsh.model.addPhysicalGroup(3, [extr_surf[vol_id][1]], tag=-1)
                gmsh.model.setPhysicalName(3, phys_volume, dot_label)
                
                # Store material properties
                self.material_dict[dot_label] = {
                    'material': material,
                    'pdoping':pdoping,
                    'ndoping':ndoping
                    }
                       
    def get_tag_from_name(self, name, dim=2):
        """ Get the physical tags associated with a physical name.
        
        Args:
        ---
        name (string or list of strings): Names for which we want the 
            physical tags.

        Returns:
        ---
        tags (int or list of ints): Physical tags associated with the 
            physical names.
        """
        # Check if input is a string or a list
        single = False
        if isinstance(name, str):
            name  = [name]
            single = True

        # Get tags associated with each name
        tags = []
        for N in name:
            for tag in gmsh.model.getPhysicalGroups(dim=dim):
                if N == gmsh.model.getPhysicalName(dim, tag[1]):
                    tags.append(tag[1])
                    break
        
        # If input was a single string output a single int
        if single:
            return tags[0]
        else:
            return tags
    
    def get_ent_tag_from_name(self, name, dim=2):
        """ Get the entity tags associated with a physical name.
        
        Args:
        ---
        name (string or list of strings): Names for which we want the 
            entity tags.

        Returns:
        ---
        tags (int or list of ints): Entity tags associated with the 
            physical names.
        """
        # Get physical tags from name
        phys_tag = self.get_tag_from_name(name, dim)

        if isinstance(phys_tag, int):
            phys_tag = [phys_tag]
        # Get entity tags from physical tags
        ent_tag = []
        for tag in phys_tag:
            ent_tag += list(gmsh.model.getEntitiesForPhysicalGroup(dim,tag))

        return ent_tag


    def save_mesh(self, dim=3, mesh_name='mesh.msh2'):
        """ Saves the generated mesh.
        
        Args:
        ---
        dim (1, 2, or 3): dimension of the mesh to generate.
        mesh_name (string): name of output mesh. The extension will determine
            the mesh file type. QTCAD currently supports .msh2
        """
        # Create the mesh
        gmsh.model.mesh.generate(dim=dim)
        gmsh.write(mesh_name)


    def relabel_surface(self, old_label, new_label, *bnd_params, bnd_type=None):
        """Relabel surface using their old label. This function can also be 
            used to set the boundary condition on the surface being relabelled.
        
        Args:
        ---
        old_label (string or list of strings): Current labels of surfaces
        new_label (string): String we with to relabel with
        *bnd_params: arguments for type of boundary condition under consideration.
            See device.py for types boundary conditions available
        bnd_type (string): Type of boundary condition to enforce. The 
            possibilities are schottky, gate, or ohmic.

        Note:
        ---
        By using a list of strings for the old_label argument, multiple 
            physical surfaces can be grouped together under a single physical 
            name
        """

        # If non new_label provided, remove physical groups
        if new_label is None:
            self.remove_phys_groups(old_label)

        else:
            # Get physical tags
            phys_tags = self.get_tag_from_name(old_label)
            if isinstance(phys_tags, int):
                phys_tags = [phys_tags]

            # Get entity tags
            ent_tags = self.get_ent_tag_from_name(old_label)

            # Destroying the old physical group
            phys_tags = [(2, pt) for pt in phys_tags]
            gmsh.model.removePhysicalGroups(phys_tags)
            # Creating the new one
            physical_surface = gmsh.model.addPhysicalGroup(2, ent_tags)
            gmsh.model.setPhysicalName(2, physical_surface, new_label)
            
            gmsh.model.occ.synchronize()

            # Storing boundary conditions
            if bnd_type is not None:
                self.bnd_dict[new_label] = {
                    'type': bnd_type,
                    'params': bnd_params
                }
        
        # update attribute vol_entities
        self._update_vol_entity_keys(ent_tags, old_label, new_label)

        return ent_tags


    def split_surface(self, name):
        """ Splits a physical surface into seperate physical surfaces for each
            entity
        Args:
        ---
        name (string): name of physical surface to split.
        """
        # Entities associated with name
        ents = self.get_ent_tag_from_name(name)
        if len(ents) == 1:
            return
        # Remove physical group and name
        phys_tag = self.get_tag_from_name(name)
        gmsh.model.removePhysicalGroups(dimTags=[(2, phys_tag)])
        gmsh.model.removePhysicalName(name)

        # Set new physical groups and names
        for i, ent in enumerate(ents):
            tag = gmsh.model.addPhysicalGroup(2, [ent])
            # Set the new name
            new_name = f'{name}-{i}'
            gmsh.model.setPhysicalName(2, tag, new_name)
            self.vol_entities[new_name] = [[(2, ent)]]
            self.vol_entities_top[new_name] = [[(2, ent)]]


        # Update self.vol_entities
        self.vol_entities.pop(name, None)
        self.vol_entities_top.pop(name, None)


    def _update_vol_entity_keys(self, ent_tags, old_label, new_label):
        """Update the keys of the attribute vol_entities as the names of 
        the surfaces change.

        Args:
        ---
        ent_tags (list of entities): Entities labelled with old_label.
        old_label (string or list of strings): Physical groups being relabeled
        new_label (string): New label for physical group.
        """
        # If old_label is a string, recast as list
        if isinstance(old_label, str):
            old_label = [old_label]
        # Remove old physical names from model and attribute
        for label in old_label:
            gmsh.model.removePhysicalName(label)
            self.vol_entities.pop(label, None)
        # Update attribute
        self.vol_entities[new_label] = []
        self.vol_entities[new_label].append([(2,e) for e in ent_tags])
        self.vol_entities_top[new_label] = []
        self.vol_entities_top[new_label].append([(2,e) for e in ent_tags])

    def remove_phys_groups(self, label):
        """ Remove physical groups from the model.
        Args:
        ---
        label(string or list of strings): Names of the physical groups we 
            wish to remove from the model.
        """
        # If single label, recast as list
        if isinstance(label, str):
            label = [label]

        # Get physical tags
        phys_tags = self.get_tag_from_name(label)
        if isinstance(phys_tags, int):
            phys_tags = [phys_tags]
        phys_tags = [(2, p) for p in phys_tags]
        # Remove names 
        for l in label:
            gmsh.model.removePhysicalName(l)
        # Remove groups
        gmsh.model.removePhysicalGroups(phys_tags)

    def new_dot_rectangle(self, x, y, dx, dy, h=None):
        """ Creates a rectangle where we expect an electron/hole to be
        localized in the x and y directions.

        Args:
        ---
        x (float): Left most position of rectangle i.e. smallest x coordinate.
        y (float): Bottom most position of rectangle i.e. smallest y coordinate.
        dx (float): x + dx is the largest x coordinate of a point in the rectangle
        dy (float): y + dy is the largest y coordinate of a point in the rectangle
        h (float): characteristic length of mesh inside dot rectangle.

        Return:
        ---
        tag (int): Tag of the rectangle.
        
        """

        # # Using gmsh python API to create rectangle
        surf = gmsh.model.occ.addRectangle(x, y, 0, dx, dy)
        # refine mesh in dot region
        if h is not None:
            self.new_box_field(x, x+dx, y, y+dy, h)
        # Allow entities to be accessed outside model
        gmsh.model.occ.synchronize()
        
        # Keep track of dot tags
        self.dot_tag.append([surf])
        self.dot_volume.append([])

        # Reset top layer
        self.setup_top_layer()

        return surf


    def get_names(self, dim):
        """ Get names of all the physical groups of a given dimension.

        Arg:
        ---
        dim (int): dimension of the physical groups for which the names are wanted

        Returns:
        ---
        names (list): List of names
        
        """
        
        # Get all the physical groups of a given dimension
        phys_groups = gmsh.model.getPhysicalGroups(dim)
        # Get all the names for the groups of the given dimension
        phys_names = []
        for pg in phys_groups: # Loop through the groups.
            name = gmsh.model.getPhysicalName(dim, pg[1])
            phys_names.append(name)
        
        return phys_names

    def _label_surfaces(self):
        """ Gives generic name to all surfaces generated from the layout file
        """
        # Initialize attribute that keeps track of volume entities
        self.vol_entities = {}
        self.vol_entities_top = {}

        # Get all entities
        entities = gmsh.model.getEntities(2)
        # Loop over all entities and assign a generic name: 'surf1', 'surf2', ...
        for e in entities:
            name = f'surf{self.s_counter}'
            phys_surf = gmsh.model.addPhysicalGroup(2, [e[1]])
            gmsh.model.setPhysicalName(2, phys_surf, name)

            self.vol_entities[name] = [[e]]
            self.vol_entities_top[name] = [[e]]

            self.s_counter += 1

            gmsh.model.occ.synchronize()


    def setup_top_layer(self):
        """ Set up top 'mask' layer of device
        """
        # Make sure only that no additional layers have been created
        if not self.first_layer:
            raise ValueError('Must setup top layer before adding new layers')

        # Remove all physical groups and names from the model
        names = self.get_names(2)
        for name in names:
            gmsh.model.removePhysicalName(name)
        gmsh.model.removePhysicalGroups(dimTags=[])

        # Reset surface counter
        self.s_counter = 1 

        # Create a conformal mesh accross all surfaces
        surfaces = gmsh.model.getEntities(2)
        surf1 = surfaces[:1]
        surf2 = surfaces[1:]
        # Use Bolean fragments
        gmsh.model.occ.fragment(surf1, surf2)
        gmsh.model.occ.synchronize()

        # store surfaces as a device attribute
        self.bottom_surface = copy.deepcopy(gmsh.model.getEntities(2))
        self.top_surface = copy.deepcopy(gmsh.model.getEntities(2))

        # Label surfaces
        self._label_surfaces()
        
        # Synchronize
        gmsh.model.occ.synchronize()

    def view(self):
        """ Open gmsh GUI to visualize.
        """
        gmsh.fltk.run()

    def __init__(self, file_path, outfile='parsed.geo', h=10, to_terminal=False):
        """ Constructor for the DeviceGenerator class.
        Args:
        ---
        file_path (string): Path to .gds file where 2D gate pattern is saved.
        outfile (string): Path to .geo file that is created from .gds file and that
            will be loaded into gmsh.
        h (scalar): Characteristic length at nodes that are not added by the solver.
            Default value is 10 microns.
        to_terminal (boolean): whether or not to print gmsh outputs to terminal
        """
        # Since no layers have been created, we are at the first layer
        self.first_layer = True
        # No bottom surface yet
        self.bottom_surface = []
        # No top surface yet
        self.top_surface = []
        
        # Initializeing counters, used for naming conventions
        self.layer_counter = 1 # layers
        self.s_counter = 1 # surfaces
        self.dot_counter = 1 # dots
        self.field_counter = 1 # fields

        # Initializing attributes used for creating dots. 
        self.dot_tag = [] # entity tag for bottom most layer of dot surface
        self.dot_volume = [] # volumes making up dots

        # Parsing input file 
        # .gds/.txt files
        if file_path[-4:] == '.gds' or file_path[-4:] == '.txt':
            P = Parser(file_path, outfile, h)
            P.parse()
            geo_file = outfile
        # .geo files
        elif file_path[-4:] == '.geo':
            geo_file = file_path
        
        # Length scales
        self.scale = 1e-6
        self.h = h
        
        # Dictionary used to store material properties and boundary conditions 
        # of a generated device
        self.material_dict = {}
        self.bnd_dict = {}

        # Initializing the gmsh kernel
        gmsh.initialize()
        # Print gmsh outputs to terminal or not
        gmsh.option.setNumber("General.Terminal", int(to_terminal))
        # Set up layout and min mesh size
        gmsh.option.setNumber('Mesh.MeshSizeMax', h)
        gmsh.open(geo_file)
        gmsh.model.occ.synchronize()
        
        # Setup top layer
        self.setup_top_layer()    