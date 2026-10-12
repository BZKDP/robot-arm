// ============================================================
//  ROBO-ARM v3.1 : METAL-FIRST. Tall U-channel = platform+yoke.
//  J1: gearbox face-bolted under static plate (4 tapped face holes),
//      carrier (2 tapped holes, rotates) bolts the channel web.
//  J2: gearbox outside left wall, arm(2 beams) on carrier disc,
//      far side 8mm rod in 608ZZ block. Index magnet+Hall on J1.
//  Measured: motor 42x42x47, gb D36 L35, carrier D19x4,
//  shaft D8 flats 5.9 L11, tip D5 L3. Channels APPROX.
// ============================================================
$fn = 60;

// ---------------- POSE ----------------
j1 = 30;
j2 = 30;
cutaway = false;

// ---------------- MEASURED ----------------
MOT=42.3; MOT_L=47;
GB_D=36;  GB_L=35;
CAR_D=19; CAR_L=4;  CAR_BC=13;      // 2 tapped holes spacing (APPROX)
SH_D=8;   SH_AF=5.9; SH_L=11; TIP_D=5; TIP_L=3;
FACE_BC=27;                          // 4 static tapped holes circle (APPROX)

// ---------------- CHANNEL / BEAM (APPROX) ----------------
CH_T=2.5; PITCH=8; GRID_D=4.2; BIGH=14;
TU_X=48; TU_Y=48; TU_H=96;           // tall U: web 48x48, walls 96 up
BEAM_W=8; BEAM_T=4; BEAM_L=184;

// ---------------- STACK ----------------
BASE_T=6; SHELL_D=120; SHELL_W=6;
FACE1=94;                            // J1 gearbox face z
PLT_T=4;  PLT_TOP=FACE1+PLT_T;       // 98 (= carrier face level)
WEB1=PLT_TOP+4;                      // web on 4mm spacers (hall fits under)
AX=WEB1+60;                          // J2 axis z, aligned to wall hole row
WI=TU_Y/2-CH_T;                      // wall inner face |y|=21.5
echo("motor1_bottom",FACE1-GB_L-MOT_L," shaft1_top",FACE1+CAR_L+SH_L+TIP_L," AX",AX);

// ============================================================
module wallx(D,H,t) {                // wall in XZ, thickness t along Y
  difference() {
    cube([D,t,H]);
    for (x=[PITCH:PITCH:D-4]) for (z=[PITCH:PITCH:H-4])
      translate([x,-1,z]) rotate([-90,0,0]) cylinder(d=GRID_D,h=t+2,$fn=14);
    for (z=[32:28:H-14]) translate([D/2,-1,z]) rotate([-90,0,0]) cylinder(d=BIGH,h=t+2,$fn=30);
  }
}
module uchannel_tall() {             // origin corner [0,0,0], web z0..CH_T
  color("#c8ccd2") {
    difference() {
      translate([0,CH_T,0]) cube([TU_X,TU_Y-2*CH_T,CH_T]);
      for (x=[PITCH:PITCH:TU_X-4]) for (y=[PITCH:PITCH:TU_Y-4])
        translate([x,y,-1]) cylinder(d=GRID_D,h=CH_T+2,$fn=14);
      translate([TU_X/2,TU_Y/2,-1]) cylinder(d=SH_D+0.3,h=CH_T+2,$fn=30); // shaft hole
    }
    wallx(TU_X,TU_H,CH_T);
    translate([0,TU_Y-CH_T,0]) wallx(TU_X,TU_H,CH_T);
  }
}
module beam_v() {                    // beam along +Z, thickness along Y
  color("#d4d8de") difference() {
    translate([-BEAM_W/2,0,0]) cube([BEAM_W,BEAM_T,BEAM_L]);
    for (z=[4:PITCH:BEAM_L-3]) translate([0,-1,z]) rotate([-90,0,0]) cylinder(d=GRID_D,h=BEAM_T+2,$fn=14);
  }
}
module mgb3() {                      // origin = static face center, +Z out
  color("#2f2f2f") translate([-MOT/2,-MOT/2,-GB_L-MOT_L]) cube([MOT,MOT,MOT_L]);
  color("#22409a") translate([0,0,-GB_L]) cylinder(d=GB_D,h=GB_L);
  color("#9aa4ad") cylinder(d=GB_D,h=1.2);
  color("#c9c9c9") difference() {
    cylinder(d=CAR_D,h=CAR_L);
    for (s=[-1,1]) translate([s*CAR_BC/2,0,-1]) cylinder(d=3,h=CAR_L+2,$fn=14);
  }
  color("#e6e6e6") difference() {
    translate([0,0,CAR_L]) cylinder(d=SH_D,h=SH_L);
    for (s=[-1,1]) translate([s>0?SH_AF/2:-SH_AF/2-8,-5,CAR_L+3]) cube([8,10,SH_L]);
  }
  color("#e6e6e6") translate([0,0,CAR_L+SH_L]) cylinder(d=TIP_D,h=TIP_L);
}

// ============================================================
module base_static() {
  color("#e0912b") {
    cylinder(d=150,h=BASE_T);
    difference() {                                    // shell with window
      cylinder(d=SHELL_D,h=FACE1);
      translate([0,0,-1]) cylinder(d=SHELL_D-2*SHELL_W,h=FACE1+2);
      translate([-30,-SHELL_D/2-1,18]) cube([60,SHELL_D+2,55]);
    }
    difference() {                                    // top plate
      translate([0,0,FACE1]) cylinder(d=SHELL_D,h=PLT_T);
      translate([0,0,FACE1-1]) cylinder(d=CAR_D+2,h=PLT_T+2);
      for (a=[45:90:315]) rotate([0,0,a]) translate([FACE_BC/2,0,FACE1-1])
        cylinder(d=3.4,h=PLT_T+2,$fn=14);
    }
  }
  color("#1b7f3b") translate([17.5,-2,PLT_TOP]) cube([5,4,1.6]); // hall flat on plate
}

module bearing608() {
  color("#9aa4ad") difference(){ cylinder(d=22,h=7); translate([0,0,-1]) cylinder(d=8,h=9);}
}

// ---- rotating group ----
module platform_yoke() {
  difference() {
    translate([-TU_X/2,-TU_Y/2,WEB1]) uchannel_tall();
    // axis pass holes D20.5 in both walls (drill in real part)
    translate([0,-TU_Y/2-1,AX]) rotate([-90,0,0]) cylinder(d=20.5,h=TU_Y+2,$fn=30);
  }
  color("#c02626") translate([20,0,WEB1-2]) cylinder(d=3,h=2);   // index magnet under web
}
module arm_link() {                  // origin = J2 axis point
  // printed carrier-adapter disc
  color("#e0912b") rotate([-90,0,0]) translate([0,0,-20])
    difference(){ cylinder(d=32,h=6); translate([0,0,-1]) cylinder(d=SH_D+0.2,h=8,$fn=30); }
  // two beams doubled, from axis up
  translate([0,-14,-20]) beam_v();
  translate([0,-14+BEAM_T,-20]) beam_v();
  // far-side rod 8mm into 608
  color("#b9bec6") rotate([-90,0,0]) translate([0,0,7]) cylinder(d=8,h=WI-7+13);
  // printed 608 housing block on right wall inner face
  color("#e0912b") translate([-15,WI-9,-15]) difference() {
    cube([30,9,30]);
    translate([15,-1,15]) rotate([-90,0,0]) cylinder(d=22.2,h=8,$fn=30);
  }
}

module assembly() {
  base_static();
  translate([0,0,FACE1]) mgb3();
  rotate([0,0,j1]) {
    platform_yoke();
    translate([0,-TU_Y/2,AX]) rotate([-90,0,0]) mgb3();           // J2 drive, shaft +Y inward
    translate([0,WI-8.5,AX]) rotate([-90,0,0]) bearing608();
    translate([0,0,AX]) rotate([0,j2,0]) arm_link();
  }
}
module cut_box(){ translate([0,-400,-120]) cube([400,400,700]); }
if (cutaway) { difference(){ assembly(); cut_box(); } } else assembly();
