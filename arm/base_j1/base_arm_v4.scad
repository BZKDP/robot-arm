// ============================================================
//  ROBO-ARM v4 : ZERO-PRINT build.
//  J1: motor+gearbox hang under the METAL sandwich plate
//      (comes with gearbox, clamps between motor and gearbox).
//      User mounts the plate on his own supports (grey = "yours").
//  Rotating carrier (2 tapped holes) bolts the tall U-channel web.
//  Hall sensor GLUED on static gearbox face, magnet in web hole.
//  J2: gearbox outside wall; arm = 2 beams on a BOUGHT flange
//      coupling D8; far side D8 rod in BOUGHT KFL08 pillow block.
//  Printed parts: NONE (paper drill templates only).
// ============================================================
$fn = 60;

// ---------------- POSE ----------------
j1 = 30;
j2 = 30;
cutaway = false;

// ---------------- MEASURED ----------------
MOT=42.3; MOT_L=47;
GB_D=36;  GB_L=35;
CAR_D=19; CAR_L=4;  CAR_BC=13;      // APPROX
SH_D=8;   SH_AF=5.9; SH_L=11; TIP_D=5; TIP_L=3;
SP=56;    SP_T=3;   SP_BC=48;       // sandwich plate (APPROX)

// ---------------- CHANNEL / BEAM (APPROX) ----------------
CH_T=2.5; PITCH=8; GRID_D=4.2; BIGH=14;
TU_X=48; TU_Y=48; TU_H=96;
BEAM_W=8; BEAM_T=4; BEAM_L=184;

// ---------------- BOUGHT PARTS ----------------
// flange coupling 8mm: hub D18 L10 + flange D25 T2.5, 4x M3 BC17
FC_HUB=18; FC_HL=10; FC_FD=25; FC_FT=2.5; FC_BC=17;
// KFL08: diamond flange bearing, bore 8, bolts 2x M4 @ 37
KFL_L=55; KFL_W=18; KFL_T=11; KFL_CC=37;

// ---------------- STACK ----------------
SUP_H=55;                       // user support height (under plate)
PLATE_Z=SUP_H;                  // sandwich plate 55..58
FACE1=PLATE_Z+SP_T+GB_L;        // 93 gearbox face
WEB1=FACE1+CAR_L+0.6;           // 97.6 channel web bottom
AX=WEB1+60;                     // J2 axis
WI=TU_Y/2-CH_T;
echo("face1",FACE1," web1",WEB1," AX",AX," shaft_top",FACE1+CAR_L+SH_L+TIP_L);

// ============================================================
module wallx(D,H,t) {
  difference() {
    cube([D,t,H]);
    for (x=[PITCH:PITCH:D-4]) for (z=[PITCH:PITCH:H-4])
      translate([x,-1,z]) rotate([-90,0,0]) cylinder(d=GRID_D,h=t+2,$fn=14);
    for (z=[32:28:H-14]) translate([D/2,-1,z]) rotate([-90,0,0]) cylinder(d=BIGH,h=t+2,$fn=30);
  }
}
module uchannel_tall() {
  color("#c8ccd2") {
    difference() {
      translate([0,CH_T,0]) cube([TU_X,TU_Y-2*CH_T,CH_T]);
      for (x=[PITCH:PITCH:TU_X-4]) for (y=[PITCH:PITCH:TU_Y-4])
        translate([x,y,-1]) cylinder(d=GRID_D,h=CH_T+2,$fn=14);
      translate([TU_X/2,TU_Y/2,-1]) cylinder(d=SH_D+0.3,h=CH_T+2,$fn=30);
    }
    wallx(TU_X,TU_H,CH_T);
    translate([0,TU_Y-CH_T,0]) wallx(TU_X,TU_H,CH_T);
  }
}
module beam_v() {
  color("#d4d8de") difference() {
    translate([-BEAM_W/2,0,0]) cube([BEAM_W,BEAM_T,BEAM_L]);
    for (z=[4:PITCH:BEAM_L-3]) translate([0,-1,z]) rotate([-90,0,0]) cylinder(d=GRID_D,h=BEAM_T+2,$fn=14);
  }
}
module mgb3() {                      // origin = static face, +Z out
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
module sandwich_plate() {            // metal, comes with gearbox
  color("#b7bcc4") difference() {
    translate([-SP/2,-SP/2,0]) cube([SP,SP,SP_T]);
    translate([0,0,-1]) cylinder(d=23,h=SP_T+2);
    for (a=[45:90:315]) rotate([0,0,a]) translate([SP_BC/2*sqrt(2)/1.414,0,-1])
      cylinder(d=4.6,h=SP_T+2,$fn=16);
  }
}
module flange_coupling() {           // BUY: 8mm flange coupling, +Z out
  color("#7f8790") difference() {
    union(){ cylinder(d=FC_HUB,h=FC_HL); translate([0,0,FC_HL]) cylinder(d=FC_FD,h=FC_FT); }
    translate([0,0,-1]) cylinder(d=SH_D+0.1,h=FC_HL+FC_FT+2,$fn=30);
    for (a=[0:90:270]) rotate([0,0,a]) translate([FC_BC/2,0,FC_HL-1])
      cylinder(d=3.2,h=FC_FT+2,$fn=14);
  }
}
module kfl08() {                     // BUY: pillow block, bore +Z
  color("#8f979f") difference() {
    hull(){ translate([-KFL_CC/2,0,0]) cylinder(d=KFL_W,h=KFL_T);
            translate([ KFL_CC/2,0,0]) cylinder(d=KFL_W,h=KFL_T); }
    translate([0,0,-1]) cylinder(d=SH_D+0.1,h=KFL_T+2,$fn=30);
    for (s=[-1,1]) translate([s*KFL_CC/2,0,-1]) cylinder(d=4.3,h=KFL_T+2,$fn=14);
  }
  color("#6f7780") cylinder(d=16,h=KFL_T+2);   // bearing boss visual
}

// ============================================================
//  STATIC: user supports (any) + plate + J1 drive
// ============================================================
module static_j1() {
  color("#8a8a8a") for (s=[-1,1]) translate([s*35-10,-25,0]) cube([20,50,SUP_H]); // "YOUR supports"
  translate([0,0,PLATE_Z]) sandwich_plate();
  translate([0,0,FACE1]) mgb3();
  color("#1b7f3b") translate([12,-3,FACE1+1.2]) cube([6,4,1.6]);   // Hall glued on face
}

// ---- rotating ----
module platform_yoke() {
  difference() {
    translate([-TU_X/2,-TU_Y/2,WEB1]) uchannel_tall();
    translate([0,-TU_Y/2-1,AX]) rotate([-90,0,0]) cylinder(d=20.5,h=TU_Y+2,$fn=30);
  }
  color("#c02626") translate([15,0,WEB1-2]) cylinder(d=3,h=2);     // index magnet under web
}
module arm_link() {                  // origin = J2 axis
  rotate([-90,0,0]) translate([0,0,-20]) flange_coupling();        // on carrier shaft
  translate([0,-20+FC_HL+FC_FT,-20]) beam_v();                     // 2 beams on flange
  translate([0,-20+FC_HL+FC_FT+BEAM_T,-20]) beam_v();
  color("#b9bec6") rotate([-90,0,0]) translate([0,0,4]) cylinder(d=8,h=WI+CH_T+14);  // rod
}

module assembly() {
  static_j1();
  rotate([0,0,j1]) {
    platform_yoke();
    translate([0,-TU_Y/2,AX]) rotate([-90,0,0]) mgb3();
    translate([0,TU_Y/2+KFL_T,AX]) rotate([90,0,0]) kfl08();       // KFL08 outside right wall
    translate([0,0,AX]) rotate([0,j2,0]) arm_link();
  }
}
module cut_box(){ translate([0,-400,-120]) cube([400,400,700]); }
if (cutaway) { difference(){ assembly(); cut_box(); } } else assembly();
