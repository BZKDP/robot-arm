// ============================================================
//  ROBO-ARM v2 : BASE J1 (rotate) + SHOULDER J2 (tilt) + LINK1
//  Fully calculated stack-up. All measured dims 2026-07-31.
//  Mounting: gearbox BODY CLAMP (printed split collar + 2x M4)
//  J2 far side: alu 8mm stub in 608ZZ + magnet cap + AS5600.
//  Big bearing J1: 6815ZZ 75x95x10 (BUY).
//  ASCII only (OpenSCAD 2021.01).
// ============================================================
$fn = 72;

// ---------------- POSE ----------------
j1 = 30;        // base rotation, deg
j2 = 35;        // shoulder tilt, deg (0 = link up)
cutaway = false;

// ---------------- MEASURED ----------------
MOT    = 42.3;  // NEMA17 frame
MOT_L  = 40;    // motor length
GB_D   = 36;    // gearbox body dia (measured 35.9)
GB_L   = 42;    // gearbox length: 82 total - 40 motor
BOSS_D = 19;    // rotating boss
BOSS_L = 4;
SH_D   = 6;     // output shaft (has flat)
SH_L   = 14;    // shaft beyond boss (total 18 with boss)
ASB    = 20;    // AS5600 board 20x20

// ---------------- HARDWARE (buy/have) ----------------
BRG_OD = 95;  BRG_ID = 75;  BRG_T = 10;   // 6815ZZ - BUY
B6_OD  = 22;  B6_ID  = 8;   B6_T  = 7;    // 608ZZ  - HAVE
STUB_D = 8;                               // alu rod 8mm - HAVE

// ---------------- LAYOUT J1 (computed) ----------------
BP_T    = 6;                    // ground plate
SHELL_D = 130; SHELL_W = 5;     // housing shell
FACE_Z  = 94;                   // gearbox1 output face height
PLATE_T = 8;
TP      = FACE_Z + PLATE_T;     // 102 top plate surface
SEAT_OD = 112;  SEAT_H = 6;     // bearing seat ring
PLAT_B  = TP + BRG_T;           // 112 platform bottom
PLAT_T2 = 8;
PLAT_TOP= PLAT_B + PLAT_T2;     // 120
PLAT_OD = 126;
SPIG_L  = 8;                    // spigot into bearing bore
HUB_D   = 20;                   // platform D-hub boss
COL_OD  = 48; COL_L = 24;       // clamp collar J1 (under plate)

// ---------------- LAYOUT J2 ----------------
WALL_T = 8;  GAP = 44;          // yoke: inner faces at +/-22
WALL_X = 64; WALL_H = 84;       // walls 120..204
AX     = PLAT_TOP + 52;         // 172 J2 axis height
WO     = GAP/2 + WALL_T;        // 30 wall outer face
C2_OD  = 46; C2_L = 24;         // clamp collar J2 (on left wall)
HUB2_D = 44; HUB2_T = 10;       // link drive hub
LINK_T = 14; LINK_W = 56; LINK_L = 180;

echo("motor1 bottom z=", FACE_Z-GB_L-MOT_L);
echo("shaft1 z=", FACE_Z+BOSS_L, "..", FACE_Z+BOSS_L+SH_L);
echo("bearing z=", TP, "..", TP+BRG_T, " platform=", PLAT_B, "..", PLAT_TOP);
echo("J2 axis z=", AX);

// ============================================================
//  COMMON PARTS
// ============================================================
module mgb_up() {                 // origin = output face center, shaft +Z
  color("#2f2f2f") translate([-MOT/2,-MOT/2,-GB_L-MOT_L]) cube([MOT,MOT,MOT_L]);
  color("#22409a") translate([0,0,-GB_L]) cylinder(d=GB_D, h=GB_L);
  color("#8a8f96") cylinder(d=BOSS_D, h=BOSS_L);
  color("#d8d8d8") difference() {
    translate([0,0,BOSS_L]) cylinder(d=SH_D, h=SH_L);
    translate([2.5,-5,BOSS_L+4]) cube([10,10,SH_L]);   // flat
  }
}
module ring(od,id,t) { difference(){ cylinder(d=od,h=t); translate([0,0,-1]) cylinder(d=id,h=t+2);} }

// ============================================================
//  STATIC BASE (printed, one piece)
// ============================================================
module base_static() {
  color("#e0912b") {
    // ground plate + 4 bolt tabs
    cylinder(d=150, h=BP_T);
    for (a=[45:90:315]) rotate([0,0,a]) translate([78,0,0])
      difference(){ cylinder(d=22,h=BP_T); translate([0,0,-1]) cylinder(d=4.6,h=BP_T+2); }
    // shell with 2 service windows
    difference() {
      cylinder(d=SHELL_D, h=FACE_Z);
      translate([0,0,-1]) cylinder(d=SHELL_D-2*SHELL_W, h=FACE_Z+2);
      for (s=[-1,1]) translate([s*65-25,-27,28]) cube([50,54,58]);  // windows
    }
    // top plate + bearing seat + J1 clamp collar under plate
    difference() {
      union() {
        translate([0,0,FACE_Z]) cylinder(d=SHELL_D, h=PLATE_T);
        translate([0,0,TP]) ring(SEAT_OD, BRG_OD+0.4, SEAT_H);        // seat
        translate([0,0,FACE_Z-COL_L]) cylinder(d=COL_OD, h=COL_L);    // collar
      }
      translate([0,0,FACE_Z-COL_L-1]) cylinder(d=GB_D+0.4, h=COL_L+2);  // collar bore 36.4
      translate([0,0,FACE_Z-0.01])    cylinder(d=BOSS_D+2, h=PLATE_T+1); // boss+shaft pass
      translate([-1.7,8,FACE_Z-COL_L-1]) cube([3.4,30,COL_L+2]);      // clamp slit (+2x M4)
    }
  }
}

// ============================================================
//  ROTATING GROUP (platform + yoke, printed one piece)
// ============================================================
module platform_yoke() {
  color("#3fae57") {
    difference() {
      union() {
        translate([0,0,PLAT_B]) cylinder(d=PLAT_OD, h=PLAT_T2);            // platform
        translate([0,0,PLAT_B-SPIG_L]) ring(BRG_ID-0.2, BRG_ID-12, SPIG_L); // spigot into 6815
        translate([0,0,PLAT_B-9]) cylinder(d=HUB_D, h=9);                   // D-hub boss
        for (s=[-1,1]) translate([-WALL_X/2, s*GAP/2 - (s<0?WALL_T:0), PLAT_TOP])
          cube([WALL_X, WALL_T, WALL_H]);                                   // yoke walls
      }
      // D-bore for shaft1 (6.15 + flat)
      difference() {
        translate([0,0,PLAT_B-10]) cylinder(d=SH_D+0.15, h=10.01);
        translate([2.55,-5,PLAT_B-10]) cube([10,10,11]);
      }
      // left wall: boss pass hole ; right wall: 608 pocket + thru
      translate([0,-GAP/2+1, AX]) rotate([90,0,0])  cylinder(d=BOSS_D+1.5, h=WALL_T+2);
      translate([0, GAP/2-1, AX]) rotate([-90,0,0]) cylinder(d=B6_OD+0.1, h=B6_T+1);
      translate([0, GAP/2+B6_T-1, AX]) rotate([-90,0,0]) cylinder(d=9, h=WALL_T);
    }
    // J2 clamp collar on left wall (outboard)
    difference() {
      translate([0,-WO,AX]) rotate([90,0,0]) cylinder(d=C2_OD, h=C2_L);
      translate([0,-WO+1,AX]) rotate([90,0,0]) cylinder(d=GB_D+0.4, h=C2_L+2);
      translate([-1.7,-WO-C2_L-1,AX+8]) cube([3.4,C2_L+2,18]);          // slit
    }
    // support pillar under motor2
    translate([-9,-101,PLAT_TOP]) cube([18,18,30]);
    // AS5600 bracket on right wall (2 standoffs + note screws M3)
    for (sx=[-1,1]) translate([sx*13-2.5, WO, AX-2.5]) cube([5,8.5,5]);
  }
}

// ============================================================
//  LINK (printed) + metal bits
// ============================================================
module link_j2() {                         // origin at J2 axis, rotates about Y
  color("#3a78d6") difference() {
    union() {
      translate([0,-GAP/2+0.5,0]) rotate([-90,0,0]) cylinder(d=HUB2_D, h=HUB2_T);   // drive hub
      translate([-LINK_W/2, -GAP/2+HUB2_T+0.5, -HUB2_D/2]) cube([LINK_W, LINK_T, LINK_L+HUB2_D/2]); // plate
      translate([0, -GAP/2+HUB2_T+LINK_T+0.5, 0]) rotate([-90,0,0]) cylinder(d=22, h=8); // stub boss
    }
    // D-bore for shaft2
    difference() {
      translate([0,-GAP/2-1,0]) rotate([-90,0,0]) cylinder(d=SH_D+0.15, h=HUB2_T+2);
      translate([2.55,-GAP/2-1,-5]) cube([10,HUB2_T+2,10]);
    }
    // stub socket 8mm
    translate([0, -GAP/2+HUB2_T+LINK_T-0.5, 0]) rotate([-90,0,0]) cylinder(d=STUB_D+0.05, h=9);
    // top mounting holes for next cartridge (20x20 pattern, M4)
    for (px=[-10,10]) for (pz=[LINK_L-25, LINK_L-5])
      translate([px, -GAP/2+HUB2_T-1, pz]) rotate([-90,0,0]) cylinder(d=4.3, h=LINK_T+2);
  }
  // alu stub 8mm through 608 + magnet cap + AS5600 board
  color("#c9c9c9") translate([0, -GAP/2+HUB2_T+LINK_T-6, 0]) rotate([-90,0,0]) cylinder(d=STUB_D, h=GAP/2+WALL_T-HUB2_T-LINK_T+9);
  color("#8a2be2") translate([0, WO+0.5, 0]) rotate([-90,0,0]) cylinder(d=11, h=2.5);   // magnet cap
  color("#c02626") translate([0, WO+3, 0])   rotate([-90,0,0]) cylinder(d=6, h=2.5);    // magnet
}

// ============================================================
//  ASSEMBLY
// ============================================================
module assembly() {
  base_static();
  translate([0,0,FACE_Z]) mgb_up();                             // J1 drive
  color("#9aa4ad") translate([0,0,TP]) ring(BRG_OD, BRG_ID, BRG_T);  // 6815ZZ
  rotate([0,0,j1]) {
    platform_yoke();
    translate([0,-WO,AX]) rotate([-90,0,0]) mgb_up();           // J2 drive (shaft +Y)
    color("#9aa4ad") translate([0,GAP/2,AX]) rotate([-90,0,0]) ring(B6_OD,B6_ID,B6_T); // 608
    // AS5600 board J2 (static on wall, chip toward magnet)
    color("#1b7f3b") translate([-ASB/2, WO+6.5, AX-ASB/2]) cube([ASB,1.6,ASB]);
    translate([0,0,AX]) rotate([0,j2,0]) translate([0,0,-AX]) translate([0,0,AX]) link_j2();
  }
}

module cut_box() { translate([0,-400,-120]) cube([400,400,600]); }
if (cutaway) { difference(){ assembly(); cut_box(); } } else assembly();
