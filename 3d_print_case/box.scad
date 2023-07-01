difference(){
union(){
difference(){
cube([86,49,12]);
translate([2,2,2]) cube([82,45,12]);
}
//add cylinders for screwholes
translate([3,3,0])cylinder(d=6,h=12);
translate([3,46,0])cylinder(d=6,h=12);
translate([83,3,0])cylinder(d=6,h=12);
translate([83,46,0])cylinder(d=6,h=12);
}

//add screwholes
translate([2.5,2.5,0])cylinder(d=2.5,h=12);
translate([2.5,46,0])cylinder(d=2.5,h=12);
translate([83,2.5,0])cylinder(d=2.5,h=12);
translate([83,46,0])cylinder(d=2.5,h=12);

//add usb port
translate([83,10,8])cube([10,10,4]);

//thin wall for RPI2040w
translate([80,4.5,2])cube([5,30,14]);

//thin wall for stuff on the left
translate([0,4.5,2])cube([7,40,14]);


}

//add a side panel to cover the left side
translate([-2,0,0])cube([2,49,12]);
