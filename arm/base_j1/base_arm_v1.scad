// ============================================================
//  ROBO-ARM  v1  - BASE J1 (rotate) + SHOULDER J2 (tilt) + LINK1
//  Palletizer-style, double-support shoulder. Parametric.
//  Colors: orange = printed | blue = gearbox/link | dark = motor
//          gray = bearing/metal | green = rotating platform
//  Dims from measurements 2026-07-31 (approx where noted).
//  ASCII only (OpenSCAD 2021.01 GUI dislikes non-ASCII).
// ============================================================
$fn = 64;

// ---- POSE (deg) - move the joints ----
j1 = 25;    // base rotation
j2 = 40;    // shoulder tilt (0 = link straight up)
cutaway = false;

// ---- MEASURED dims (mm) ----
motor       = 42.3;   // NEMA17 frame
motor_len   = 40;
gb_body     = 40;     // gearbox body dia
gb_len      = 47;     // gearbox length
gb_outflg   = 36;     // output flange OD (CM36)
gb_boss     = 19;     // rotating boss
gb_shaft    = 6;      // output shaft (has flat)
gb_shaft_l  = 18;

// ---- BASE (printed) ----
base_d      = 120;
base_wall   = 6;
base_h      = 70;
base_top    = 8;
bbrg_od     = 104;    // big support bearing (pick real later)
bbrg_id     = 74;
bbrg_th     = 12;
plat_d      = 112;
plat_th     = 8;

// ---- SHOULDER (printed yoke) ----
wall_x      = 54;
wall_th     = 9;
wall_h      = 70;
gap         = 58;     // between yoke walls (Y)
axis_h      = 44;     // J2 axis height above platform
link_w      = 12;     // link plate thickness (X)
link_len    = 170;    // link length (up)

// ============================================================
module motor()  { color("#333333") translate([0,0,-motor_len]) cube([motor,motor,motor_len], center=true); }
module gearbox() {
  color("#22409a") cylinder(d=gb_body, h=gb_len);
  color("#8a8f96") translate([0,0,gb_len])    cylinder(d=gb_outflg, h=3);   // output flange (rotates)
  color("#c9c9c9") translate([0,0,gb_len+3])  cylinder(d=gb_boss, h=3);
  color("#e6e6e6") translate([0,0,gb_len+6])  cylinder(d=gb_shaft, h=gb_shaft_l);
}
module mgb() { gearbox(); motor(); }          // output along local +Z
module ring(od,id,h) { color("#9aa4ad") difference(){ cylinder(d=od,h=h); translate([0,0,-1]) cylinder(d=id,h=h+2);} }

// ---- FIXED BASE ----
module base_housing() {
  color("#e0912b") difference() {
    union() { cylinder(d=base_d,h=base_h); translate([0,0,base_h]) cylinder(d=base_d,h=base_top); }
    translate([0,0,base_wall]) cylinder(d=base_d-2*base_wall, h=base_h);
    translate([0,0,base_h-1]) cylinder(d=gb_outflg+8, h=base_top+2);
  }
}

// ---- ROTATING GROUP (J1) : platform + shoulder + link ----
module link() {
  // flat plate going UP (+Z), spanning between yoke walls (Y)
  color("#3a78d6") translate([-link_w/2, -(gap-6)/2, 0]) cube([link_w, gap-6, link_len]);
}

module shoulder() {
  // yoke walls (two plates at Y = +/- gap/2)
  for (s=[-1,1])
    color("#d9822b") translate([-wall_x/2, s*gap/2 - wall_th/2, 0]) cube([wall_x, wall_th, wall_h]);
  translate([0,0,axis_h]) {
    // gearbox2 on LEFT wall, axis along Y, output flange at inner face
    translate([0, -gap/2, 0]) rotate([90,0,0]) mgb();
    // bearing on RIGHT wall
    translate([0,  gap/2, 0]) rotate([-90,0,0]) ring(gb_boss+6, gb_shaft+1, wall_th);
    // link rotates about Y by j2
    rotate([0, j2, 0]) link();
  }
}

module rotating_group() {
  color("#3fae57") cylinder(d=plat_d, h=plat_th);
  translate([0,0,plat_th]) shoulder();
}

// ============================================================
module assembly() {
  base_housing();
  translate([0,0, base_h - gb_len]) mgb();                 // gearbox1 inside, output up
  translate([0,0, base_h + base_top]) ring(bbrg_od,bbrg_id,bbrg_th);
  rotate([0,0,j1]) translate([0,0, base_h + base_top + bbrg_th]) rotating_group();
}

module cut_box() { translate([0,-400,-120]) cube([400,400,600]); }

if (cutaway) { difference() { assembly(); cut_box(); } }
else { assembly(); }
