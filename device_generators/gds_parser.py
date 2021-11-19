def remove_prefix(text, prefix):
    return text[text.startswith(prefix) and len(prefix):]

class Parser:
    """ Class to generate a .geo file corresponding to a given .gds file
    Attributes:
    ---
    file_path (string): Path to .gds file to parse
    outfile (string): Path to output .geo file
    pt_counter (int): Counter of generated points
    line_counter (int): Counter of generated lines
    cl_counter (int): Counter of generated curve loops
    surf_counter (int): Counter of generated surfaces
    h (float): characteristic lenght at each point
    layers (dictionary): elements (or curve loops) associated with each layer
        (from .gds)
    
    Methods:
    ---
    parse: generates the .geo file. 
    """

    def format_point(self, point):
        """ Change the format of points from the .gds convention to the 
        .geo convention

        Arg:
        ---
        point (string): point in the .gds convention

        Returns:
        ---
        out_point (string): string in the .geo convention
        """

        # '':' separates x coordinate from y coordinate
        ix = point.find(':')
        # x coordinate is before the ':'
        x = point[:ix]
        # y coordinate is after the ':'
        # remove new line at end of string
        y = point[ix+1:-1]

        # # nm units
        x = str(round(float(x) * self.units_m * 1e6, 6))
        y = str(round(float(y) * self.units_m * 1e6, 6))
        
        # Output string for .geo file
        pt_str = f'Point({self.pt_counter}) = {{{x}, {y}, 0, {self.h}}}; \n'
        
        return pt_str

    def _create_elements(self, checkpoint, outfile, layer):
        """ Create the various elements (polygons) that make up the gate pattern 
        of a typical device.

        Args:
        ---
        checkpoint (int): checkpoint for poitn counter. First label for points
            in element.
        outfile (file): .geo file being created
        layer (int): layer being created from .gds file
        
        """
        
        # First line created in element
        line_checkpoint = self.line_counter
        # loop over all points of element and create lines between them
        for n in range(checkpoint, self.pt_counter - 1):
            line_str = f'Line({self.line_counter}) = {{{n}, {n+1}}}; \n'
            outfile.write(line_str)
            self.line_counter += 1
        # Link the las point to the first to have a closed element.
        last_pt = self.pt_counter - 1
        first_pt = checkpoint

        loop_close = f'Line({self.line_counter}) = {{{last_pt}, {first_pt}}}; \n'
        outfile.write(loop_close)
        self.line_counter += 1 

        # Create Curve Loop
        line_numbers = [str(n) for n in range(line_checkpoint, self.line_counter)]
        loop = ', '.join(line_numbers)
        curve_loop_str = f'Curve Loop({self.cl_counter}) = {{{loop}}};\n'
        outfile.write(curve_loop_str)

        # Store index for curve loops of different layers
        # (will be used to perform Boolean fragments when creating surfaces)
        self.layers[layer].append(self.cl_counter)

        # Creating surfaces. 
        surface_str = f'Plane Surface({self.surf_counter}) = {{{self.cl_counter}}};\n'
        outfile.write(surface_str)
        self.cl_counter += 1
        self.surf_counter += 1

        outfile.write('\n')

    def _create_surfaces(self, outfile):
        """ Create surfaces from Boolean fragments
        Args:
        ---
        outfile (file): .geo file being created
        """
        # Order the curve loops in the different layers
        l = list(self.layers.keys())
        l.sort()

        # Create Boolean fragment removing elements from layer above from layer below
        for i in range(len(l) - 1):
            surfaces = ', '.join(list(map(str, self.layers[l[i]])) 
                + list(map(str, self.layers[l[i+1]])))
            BF_string = f"BooleanFragments{{ Surface{{{surfaces}}}; Delete; }}{{}}"
            outfile.write(BF_string)

    def _parse_points(self, f, o):
        """ Converts a .gds file to a .geo file.
        Args:
        ---
        f (string): path to input .gds file
        o (string): path to output .geo file      
        """
        for line in f:
            if line.startswith("LAYER"):
                layer = line[-3]

                if layer not in self.layers:
                    self.layers[layer] = []

            if line.startswith("XY"):
                # Remove "XY" prefix
                l = remove_prefix(line, "XY ")
                # Checkpoint for point counter
                count_checkpoint = self.pt_counter
                # Write first line to file
                o.write(self.format_point(l))
                # Update counter (point ids)
                self.pt_counter += 1
                for line in f:
                    if line.startswith("ENDEL"):
                        o.write('\n')
                        self._create_elements(count_checkpoint, o, layer)
                        # stop this inner for loop; outer loop picks up on the next line
                        break 
                    if line != l:
                        o.write(self.format_point(line))
                        self.pt_counter += 1


    def _create_header(self, f, o):
        """ Create header for .geo file. Enforce 'OpenCASCADE'. Also 
        gets units from .gds file

        Args:
        ---
        outfile (file): .geo file being created
        """

        header_line_1 = 'SetFactory("OpenCASCADE");\n'
        o.write(header_line_1)
        o.write('\n')

        for line in f:
            if line.startswith("UNITS"):
                scaling = remove_prefix(line, "UNITS ").split()
                break
       
        # Extract units from .gds header
        self.units_mum = float(scaling[0])
        self.units_m = float(scaling[1])
        
        if self.units_mum != (self.units_m * 1e6):
            ValueError('Units do not match')


    def parse(self, verbose=True):
        """ Function that opens file to be parsed and output file.       
        """
        if verbose:
            print(f"parsing {self.file_path}...")

        # Open .txt (gds2) file
        f = open(self.file_path, 'r')
        # Open .geo file
        o = open(self.outfile, 'w')

        self._create_header(f, o)

        self._parse_points(f, o)

        o.close()

    def __init__(self, file_path, outfile, h):
        """ Constructor for the Parser class.
        Args:
        ---
        file_path (string): path to .gds file containing 2D layout.
        outfile (string): .geo file created from .gds file
        h (scalar): Characteristic length 
        
        """
        self.file_path = file_path
        self.outfile = outfile
        self.h = h
        self.layers = {}

        # Counters for new entities in gmsh
        self.pt_counter = 1
        self.line_counter = 1
        self.cl_counter = 1
        self.surf_counter = 1

    