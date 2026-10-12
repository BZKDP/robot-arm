// ============================================================
//  ROBO-ARM - BASE J1 (rotating base)  v0.2
//  Parametric model for OpenSCAD. Edit numbers in PARAMS block.
//  Colors: orange = 3D printed | blue = gearbox | dark = motor
//          gray = bearing/metal | green = rotating platform
//  NOTE: gearbox OUTPUT sizes are APPROX (Oxx) - refine after measuring.
//  ASCII only on purpose: OpenSCAD 2021.01 GUI dislikes non-ASCII.
// ============================================================
$fn = 72;

// ---------------- PARAMS (mm) ----------------
cutaway     = true;    // set true + F5 to see inside (section view)

// NEMA17 (standard)
nema        = 42.3;
nema_len    = 40;
nema_pilot  = 22;
nema_shaft  = 5;

// Gearbox CM36 (measured 2026-07-31)
gb_flange     = 41.9;  // G1 input flange (to motor)
gb_body_d     = 40;    // body dia (approx)
gb_len        = 47;    // gearbox length (measured ~47)
gb_out_flange = 36;    // output flange OD (measured 35.9 = "CM36")
gb_out_boss   = 19;    // rotating center boss dia (measured ~19)
gb_out_d      = 6;     // O1 output shaft dia, has FLAT (measured ~6)
gb_out_len    = 18;    // O2 output shaft length (100 total - 82 to face)

// Base (printed)
base_d      = 100;
wall        = 5;
frame_h     = 78;
top_th      = 8;

// Rotating platform (printed)
plat_d      = 92;
plat_th     = 8;

// Support bearing (metal, big) - APPROX, pick real one later
brg_od      = 90;
brg_id      = 60;
brg_th      = 12;

// ---------------- PARTS ----------------
module nema17() {
  color("#3a3a3a") translate([0,0,-nema_len]) cube([nema, nema, nema_len], center=true);
  color("#3a3a3a") cylinder(d=nema_pilot, h=2);
  color("#b0b0b0") cylinder(d=nema_shaft, h=6);
}

module gearbox() {
  color("#2b4a9b") cylinder(d=gb_flange, h=3);                          // input flange (motor)
  color("#2b4a9b") translate([0,0,3]) cylinder(d=gb_body_d, h=gb_len-3); // body
  color("#8a8f96") translate([0,0,gb_len])   cylinder(d=gb_out_flange, h=3); // output flange 36 (FIXED?)
  color("#c9c9c9") translate([0,0,gb_len+3]) cylinder(d=gb_out_boss, h=3);   // rotating boss 19
  color("#e6e6e6") translate([0,0,gb_len+6]) cylinder(d=gb_out_d, h=gb_out_len); // D-shaft 6
}

// motor below, gearbox above, output shaft UP
module motor_gearbox() {
  gearbox();
  rotate([180,0,0]) nema17();
}

module bearing() {
  color("#9aa4ad") difference() {
    cylinder(d=brg_od, h=brg_th);
    translate([0,0,-1]) cylinder(d=brg_id, h=brg_th+2);
  }
}

module base_frame() {
  color("#e0912b") difference() {
    union() {
      cylinder(d=base_d, h=frame_h);
      translate([0,0,frame_h]) cylinder(d=base_d, h=top_th);
    }
    translate([0,0,wall]) cylinder(d=base_d-2*wall, h=frame_h);
    translate([0,0,frame_h-1]) cylinder(d=gb_out_d+6, h=top_th+2);
  }
}

module rotating_platform() {
  color("#3fae57") difference() {
    cylinder(d=plat_d, h=plat_th);
    translate([0,0,-1]) cylinder(d=gb_out_d+0.3, h=plat_th+2);
  }
}

// ---------------- ASSEMBLY ----------------
module assembly() {
  base_frame();
  translate([0,0, frame_h - gb_len]) motor_gearbox();
  translate([0,0, frame_h + top_th]) bearing();
  translate([0,0, frame_h + top_th + brg_th]) rotating_platform();
}

module cut_box() { translate([0,-400,-120]) cube([400,400,600]); } // remove near quadrant (+x,-y)

if (cutaway) {
  difference() { assembly(); cut_box(); }
} else {
  assembly();
}
