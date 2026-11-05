// SO-ARM102 table clamp — fully printed, no hardware, no holes in the table.
//
// Two identical C-clamps pinch the SO-102 base plate against the tabletop.
// A peg on the upper jaw drops into one of the Ø8.2 mm mounting holes of the
// base, so the base cannot slide; a printed M12 thumbscrew in the lower jaw
// presses up against the underside of the table.
//
// Coordinate frame (body): X = into the table (away from the edge),
// Z = up, table top at Z = 0, table edge face at X = 0.
//
// Render a single part with:  openscad -D part='"body"' -o body.stl so102_table_clamp.scad
// Parts: "body" (uses `side`), "screw", "pad", "assembly" (preview only).
// The upper jaw reaches to the middle of the base, where it has to clear the
// Ø78 mm motor boss, so the two clamps are mirror images: side = 1 or -1.

part = "assembly";
side = 1;

// ---------- what you are clamping ----------
table_t        = 40;    // tabletop thickness [mm]; the screw gives roughly ±8 mm of range around this
base_t         = 10;    // SO-102 base plate thickness
hole_d         = 8.2;   // base mounting hole diameter
hole_from_edge = 22.5;  // hole centre to the base edge that sits at the table edge
                        // back edge (serial-adapter side) = 22.5, front edge = 10, long sides = 40
hole_y         = 40;    // hole centre offset from the base centre line (the two clamps sit at ±hole_y)
base_depth     = 112.5; // base plate size perpendicular to the table edge
boss_x         = 62.5;  // motor boss centre, measured from the table edge (back edge flush)
boss_r         = 39;    // motor boss radius
boss_clear     = 2;     // clearance between jaw and boss

// ---------- clamp body ----------
W          = 26;    // clamp width along the table edge
spine_t    = 14;    // vertical spine thickness
edge_gap   = 1.5;   // clearance between spine and table edge face
jaw_root   = 16;    // upper jaw thickness at the spine
jaw_tip    = 11;    // upper jaw thickness at the tip
jaw_reach  = base_depth / 2;  // upper jaw tip, measured from the table edge (half the base)
jaw_past   = 10;    // how far the lower jaw extends past the screw axis
lower_t    = 16;    // lower jaw thickness
boss_extra = 6;     // extra thread boss below the lower jaw
screw_room = 14;    // nominal gap between table underside and lower jaw top
peg_d      = 7.6;   // peg diameter (0.6 mm under the 8.2 hole)
peg_len    = 8;     // peg length (stays 2 mm short of the table)
corner_r   = 2.5;

// ---------- printed thread ----------
pitch      = 2.5;
thr_major  = 12;
thr_depth  = 1.25;
thr_clear  = 0.3;   // radial clearance of the nut over the screw
thr_len    = 50;    // threaded length of the screw
knob_h     = 12;
tip_neck_d = 8;
tip_neck_h = 3;

$fn = 64;

// ---------- derived ----------
x_in      = -edge_gap;              // spine inner face
x_out     = x_in - spine_t;         // spine outer face
x_reach   = hole_from_edge + jaw_past;   // lower jaw
z_jaw_top = base_t + jaw_root;
z_low_top = -(table_t + screw_room);
z_low_bot = z_low_top - lower_t;
z_boss    = z_low_bot - boss_extra;
x_screw   = hole_from_edge;
r_major   = thr_major / 2;
r_minor   = r_major - thr_depth;

// Thread tooth profile vs angle: 60° flanks with small flats, as a 0..1 shape.
function tooth(a) =
    a < 75  ? 0 :
    a < 180 ? (a - 75) / 105 :
    a < 255 ? 1 :
              1 - (a - 255) / 105;

// One-start helical thread by twisting a radius-modulated 2D section.
module thread(len, r_min, depth, grow = 0, step = 4) {
    linear_extrude(height = len, twist = -360 * len / pitch,
                   slices = ceil(len / pitch * 28), convexity = 10)
        polygon([for (a = [0 : step : 359.999])
                 let(r = r_min + depth * tooth(a) + grow)
                 [r * cos(a), r * sin(a)]]);
}

// ---------- body ----------
module body_profile() {
    offset(r = corner_r) offset(r = -corner_r) union() {
        // spine
        translate([x_out, z_boss]) square([spine_t, z_jaw_top - z_boss]);
        // upper jaw, tapering towards the tip
        polygon([[x_out, base_t], [jaw_reach, base_t],
                 [jaw_reach, base_t + jaw_tip], [x_out, z_jaw_top]]);
        // lower jaw
        translate([x_out, z_low_bot]) square([x_reach - x_out, lower_t]);
        // thread boss under the lower jaw
        translate([x_screw - 11, z_boss]) square([22, boss_extra + 1]);
        // gusset under the table, spine to lower jaw
        polygon([[x_in - 1, z_low_top - 1], [x_in + 8, z_low_top - 1], [x_in - 1, z_low_top + 8]]);
    }
}

module body(side = side) {
    difference() {
        union() {
            rotate([90, 0, 0]) linear_extrude(height = W, center = true, convexity = 10) body_profile();
            // locating peg into the base hole, chamfered tip
            translate([x_screw, 0, base_t + 0.01]) mirror([0, 0, 1])
                hull() {
                    cylinder(d = peg_d, h = peg_len - 1);
                    cylinder(d = peg_d - 2, h = peg_len);
                }
        }
        // scallop so the long upper jaw clears the motor boss on the inner side
        translate([boss_x, -side * hole_y, base_t - 1]) cylinder(r = boss_r + boss_clear, h = 100);
        // threaded hole for the screw
        translate([x_screw, 0, z_boss - 1])
            thread(len = lower_t + boss_extra + 2, r_min = r_minor, depth = thr_depth, grow = thr_clear);
        // lead-in chamfers on both ends of the thread
        translate([x_screw, 0, z_boss - 0.01]) cylinder(d1 = thr_major + 2, d2 = r_minor * 2, h = 1.5);
        translate([x_screw, 0, z_low_top - 1.49]) cylinder(d1 = r_minor * 2, d2 = thr_major + 2, h = 1.5);
    }
}

// ---------- thumbscrew ----------
module knob() {
    lobes = 6;
    difference() {
        union() {
            cylinder(d = 26, h = knob_h);
            for (i = [0 : lobes - 1]) rotate(i * 360 / lobes) translate([13, 0, 0]) cylinder(d = 9, h = knob_h);
        }
        // bottom chamfer ring
        translate([0, 0, -0.01]) difference() {
            cylinder(d = 40, h = 1.2);
            cylinder(d1 = 32, d2 = 36, h = 1.2);
        }
    }
}

module screw() {
    knob();
    translate([0, 0, knob_h - 0.01]) cylinder(d = r_minor * 2, h = 1.5);
    translate([0, 0, knob_h + 1]) intersection() {
        thread(len = thr_len, r_min = r_minor, depth = thr_depth);
        // chamfer the thread run-out at the top so it starts easily in the nut
        hull() {
            cylinder(d = thr_major + 0.2, h = thr_len - 1.5);
            translate([0, 0, thr_len - 1.5]) cylinder(d1 = thr_major + 0.2, d2 = thr_major - 3, h = 1.5);
        }
    }
    translate([0, 0, knob_h + 1 + thr_len - 0.01]) cylinder(d = tip_neck_d, h = tip_neck_h);
}

// Optional swivel pad on the screw tip, spreads the load on the table.
module pad() {
    difference() {
        hull() {
            cylinder(d = 22, h = 4.5);
            translate([0, 0, 4.5]) cylinder(d = 20, h = 0.5);
        }
        translate([0, 0, -0.01]) cylinder(d = tip_neck_d + 0.5, h = tip_neck_h + 0.3);
    }
}

// ---------- preview ----------
module assembly() {
    color("tomato") body(1);
    // screw screwed in to the nominal table thickness
    color("gold") translate([x_screw, 0, -table_t - tip_neck_h - thr_len - knob_h - 1]) screw();
    color("gray") translate([x_screw, 0, -table_t]) mirror([0, 0, 1]) pad();
    // the table, as a ghost
    %translate([0, -40, -table_t]) cube([80, 80, table_t]);
    // base plate, as a ghost: the clamp at +hole_y, the hole, and the motor boss
    %translate([0, -hole_y - 40, 0]) difference() {
        cube([base_depth, 2 * hole_y + 80, base_t]);
        translate([hole_from_edge, hole_y + 40, -1]) cylinder(d = hole_d, h = base_t + 2);
    }
    %translate([boss_x, -hole_y, base_t]) cylinder(r = boss_r, h = 17);
}

if (part == "body")     body(side);
if (part == "screw")    screw();
if (part == "pad")      pad();
if (part == "assembly") assembly();
if (part == "section")  difference() { assembly(); translate([-100, 0, -200]) cube([400, 100, 400]); }
