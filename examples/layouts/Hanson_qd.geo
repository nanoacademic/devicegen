SetFactory("OpenCASCADE");

Point(1) = {0, 0, 0, 0.015}; 
Point(2) = {0.5, 0, 0, 0.015}; 
Point(3) = {0.5, 0.5, 0, 0.015}; 
Point(4) = {0, 0.5, 0, 0.015}; 

Line(1) = {1, 2}; 
Line(2) = {2, 3}; 
Line(3) = {3, 4}; 
Line(4) = {4, 1}; 
Curve Loop(1) = {1, 2, 3, 4};
Plane Surface(1) = {1};

Point(5) = {0.1, 0.1, 0, 0.015};  
Point(6) = {0.4, 0.1, 0, 0.015}; 
Point(7) = {0.4, 0.4, 0, 0.015}; 
Point(8) = {0.1, 0.4, 0, 0.015};  

Line(5) = {5, 6}; 
Line(6) = {6, 7}; 
Line(7) = {7, 8}; 
Line(8) = {8, 5}; 
Curve Loop(2) = {5, 6, 7, 8};
Plane Surface(2) = {2};

