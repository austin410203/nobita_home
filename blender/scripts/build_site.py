# Lot, block wall, gate, carport, trees, street, utility poles, lighting, game helpers
import bpy, math, random
from mathutils import Vector
exec(open(LIB).read())
init_materials()
root = coll("NobitaHouse")
C = coll("Site_Exterior", root)
CW = coll("House_Floors_Walkable", root)
random.seed(7)

# ground & street (lot x -2..11, y -4..13)
mesh_obj("Ground_Lot", [(-2, -4, -0.1, 11, 13, 0)], "Grass", CW)
mesh_obj("Street", [(-10, -12, -0.15, 20, -4, -0.03)], "Asphalt", CW)
mesh_obj("Street_Line", [(-10, -8.1, -0.03, 20, -7.95, -0.025)], "White", C)
mesh_obj("Path_Stones", [(3.1, -3.85 + 0.6 * k, 0, 4.4, -3.85 + 0.6 * k + 0.5, 0.03) for k in range(4)], "Granite", CW)
mesh_obj("Porch", [(2.85, -1.75, 0, 4.65, -0.9, 0.13)], "Concrete", CW)
mesh_obj("Carport_Slab", [(8.5, -3.85, 0, 10.85, -0.3, 0.03)], "Concrete", CW)

# concrete block wall (h 1.6, like the reference) with main gate + side gate openings
H = 1.6
def bwall(name, ax, a1, a2, c1, c2, ops=()):
    wall(name, ax, a1, a2, c1, c2, 0, H, "Block", C, [(o1, o2, 0, H + 1) for o1, o2 in ops])
    segs = []; cur = a1
    for o1, o2 in sorted(ops):
        segs.append((cur, o1)); cur = o2
    segs.append((cur, a2))
    mesh_obj(name + "_Cap", [(p1, c1 - 0.02, H, p2, c2 + 0.02, H + 0.05) if ax == "x" else (c1 - 0.02, p1, H, c2 + 0.02, p2, H + 0.05)
                             for p1, p2 in segs], "Concrete", C)
GATE = (2.9, 4.6)
SIDE_GATE = (8.6, 9.8)
bwall("BlockWall_Front", "x", -2, 11, -4, -3.85, [GATE, SIDE_GATE])
bwall("BlockWall_West", "y", -3.85, 13, -2, -1.85)
bwall("BlockWall_East", "y", -3.85, 13, 10.85, 11)
bwall("BlockWall_Back", "x", -1.85, 10.85, 12.85, 13)
# decorative openwork blocks (hana-block)
mesh_obj("BlockWall_Openwork", [(x, -4.01, z, x + 0.36, -3.84, z + 0.36) for x in (-1.4, 0.1, 1.6, 5.6, 7.1, 10.1) for z in (0.25,)]
         + [(x, -4.01, 0.95, x + 0.36, -3.84, 1.31) for x in (0.85, 6.35)], "Concrete", C)
# gate pillars, nameplate + mailbox on the right pillar, double gate
mesh_obj("Gate_Pillars", [(GATE[0] - 0.42, -4.06, 0, GATE[0], -3.79, 1.8), (GATE[1], -4.06, 0, GATE[1] + 0.42, -3.79, 1.8),
                          (GATE[0] - 0.45, -4.08, 1.8, GATE[0] + 0.03, -3.77, 1.86), (GATE[1] - 0.03, -4.08, 1.8, GATE[1] + 0.45, -3.77, 1.86)], "Block", C)
mesh_obj("Gate_Nameplate", [(GATE[1] + 0.06, -4.08, 1.2, GATE[1] + 0.36, -4.06, 1.46)], "White", C)
mesh_obj("Gate_Mailbox", [(GATE[1] + 0.06, -4.13, 0.78, GATE[1] + 0.36, -4.06, 1.08), (GATE[1] + 0.09, -4.135, 0.98, GATE[1] + 0.33, -4.13, 1.0)], "Black", C)
lw = (GATE[1] - GATE[0]) / 2 - 0.02
def gate_leaf(name, hx, sgn, width):
    nb = int(width / 0.1)
    bars = [(0, -0.02, 0.06, width, 0.02, 0.12), (0, -0.02, 1.36, width, 0.02, 1.42), (0, -0.02, 0.7, width, 0.02, 0.74)]
    bars += [(0.04 + width / nb * k, -0.015, 0.06, 0.065 + width / nb * k, 0.015, 1.42) for k in range(nb)]
    ob = mesh_obj(name, bars, "Black", C, origin=None)
    ob.location = (hx, -3.92, 0)
    ob.rotation_euler.z = 0 if sgn > 0 else math.pi
    ob["door"] = True; ob["open_angle"] = 90.0 * sgn
    ob["openable"] = "hinge"; ob["closed_rot_z"] = ob.rotation_euler.z
gate_leaf("Gate_L", GATE[0] + 0.02, 1, lw)
gate_leaf("Gate_R", GATE[1] - 0.02, -1, lw)
gate_leaf("Gate_Side", SIDE_GATE[0] + 0.02, 1, SIDE_GATE[1] - SIDE_GATE[0] - 0.04)
# street-side planter with a small tree (left of the gate, outside the wall)
mesh_obj("Planter_Street", [(0.9, -4.6, -0.03, 1.9, -4.08, 0.4)], "Concrete", C)
cyl("Planter_Tree_Trunk", 1.4, -4.34, 0.4, 1.2, 0.06, "Trunk", C, seg=10)
for k, (dx, dz, r) in enumerate(((0, 1.35, 0.5), (-0.3, 1.1, 0.38), (0.32, 1.15, 0.36), (0.05, 1.7, 0.36))):
    sphere("Planter_Tree_Leaves%d" % k, 1.4 + dx, -4.34, dz, r, "Leaf", C, sz=0.85)# Japanese nameplate text
try:
    fnt = bpy.data.fonts.load(r"C:\Windows\Fonts\msgothic.ttc", check_existing=True)
except Exception:
    fnt = None
cu = bpy.data.curves.new("Nameplate_Text", "FONT"); cu.body = "野比"; cu.size = 0.14; cu.align_x = "CENTER"
if fnt: cu.font = fnt
cu.extrude = 0.003
tob = bpy.data.objects.new("Nameplate_Text", cu); tob.location = (GATE[1] + 0.21, -4.085, 1.28); tob.rotation_euler.x = math.pi / 2
cu.materials.append(M["Black"]); C.objects.link(tob)

# bicycle shelter (駐輪場)
mesh_obj("Carport_Posts", [(x, y, 0, x + 0.08, y + 0.08, 2.2) for x in (8.6, 10.6) for y in (-3.6, -0.6)], "Metal", C)
slab_quad("Carport_Roof", [(8.4, -3.8, 2.25), (10.85, -3.8, 2.25), (10.85, -0.4, 2.45), (8.4, -0.4, 2.45)], 0.03, "Glass", C)
import bmesh
def _tubes_mesh(name, segs, r, m, sides=10):
    """One mesh made of round tubes, segs = [(p1, p2), ...] in world space."""
    bm = bmesh.new()
    for p1, p2 in segs:
        p1, p2 = Vector(p1), Vector(p2); d = p2 - p1
        res = bmesh.ops.create_cone(bm, cap_ends=True, segments=sides, radius1=r, radius2=r, depth=d.length)
        q = Vector((0, 0, 1)).rotation_difference(d.normalized())
        bmesh.ops.rotate(bm, verts=res["verts"], cent=(0, 0, 0), matrix=q.to_matrix())
        bmesh.ops.translate(bm, verts=res["verts"], vec=(p1 + p2) / 2)
    me = bpy.data.meshes.new(name); bm.to_mesh(me); bm.free()
    me.materials.append(M[m]); ob = bpy.data.objects.new(name, me); C.objects.link(ob)
    return ob

def _wheel(name, c, R=0.33):
    """Tyre (torus) + spokes + hub, wheel plane = YZ."""
    bm = bmesh.new(); seg, rs, r = 40, 8, 0.022
    rings = [[bm.verts.new((r * math.sin(2 * math.pi * j / rs), (R + r * math.cos(2 * math.pi * j / rs)) * math.cos(2 * math.pi * i / seg),
                            (R + r * math.cos(2 * math.pi * j / rs)) * math.sin(2 * math.pi * i / seg))) for j in range(rs)] for i in range(seg)]
    for i in range(seg):
        for j in range(rs):
            bm.faces.new((rings[i][j], rings[i][(j + 1) % rs], rings[(i + 1) % seg][(j + 1) % rs], rings[(i + 1) % seg][j]))
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    me = bpy.data.meshes.new(name + "_Tyre"); bm.to_mesh(me); bm.free()
    me.materials.append(M["Black"]); t = bpy.data.objects.new(name + "_Tyre", me); C.objects.link(t); t.location = c
    sp = [((c[0], c[1], c[2]), (c[0], c[1] + (R - 0.02) * math.cos(a), c[2] + (R - 0.02) * math.sin(a)))
          for a in [2 * math.pi * k / 16 for k in range(16)]]
    sp.append(((c[0] - 0.05, c[1], c[2]), (c[0] + 0.05, c[1], c[2])))
    _tubes_mesh(name + "_Spokes", sp, 0.003, "Metal", sides=4)

def bike(name, x, y, paint):
    """Japanese mamachari: step-through frame, front basket, rear carrier. Points along +Y."""
    rh, fh = (x, y - 0.52, 0.33), (x, y + 0.52, 0.33)
    _wheel(name + "_Rear", rh); _wheel(name + "_Front", fh)
    B = (x, y - 0.08, 0.30); S = (x, y - 0.24, 0.82); Hb = (x, y + 0.40, 0.70); Ht = (x, y + 0.36, 0.92)
    bend = (x, y + 0.22, 0.42)
    _tubes_mesh(name + "_Frame", [(B, S), (B, bend), (bend, Hb), (Hb, Ht), (B, rh), ((x, y - 0.22, 0.74), rh),
                                  ((x + 0.03, y + 0.40, 0.70), (x + 0.03, fh[1], fh[2])), ((x - 0.03, y + 0.40, 0.70), (x - 0.03, fh[1], fh[2])),
                                  ((x, y - 0.24, 0.80), (x, y - 0.75, 0.72)), ((x, y - 0.75, 0.72), (x, y - 0.55, 0.45)),  # carrier
                                  ((x, y - 0.72, 0.36), (x, y - 0.55, 0.0))], 0.018, paint)
    _tubes_mesh(name + "_Handlebar", [(Ht, (x, y + 0.32, 0.98)), ((x - 0.28, y + 0.24, 0.98), (x + 0.28, y + 0.24, 0.98)),
                                      ((x - 0.28, y + 0.24, 0.98), (x - 0.32, y + 0.10, 0.99)), ((x + 0.28, y + 0.24, 0.98), (x + 0.32, y + 0.10, 0.99))],
                0.012, "Metal")
    mesh_obj(name + "_Grips", [(x - 0.35, y + 0.06, 0.975, x - 0.29, y + 0.14, 1.005), (x + 0.29, y + 0.06, 0.975, x + 0.35, y + 0.14, 1.005)], "Black", C)
    mesh_obj(name + "_Saddle", [(x - 0.09, y - 0.36, 0.83, x + 0.09, y - 0.12, 0.89)], "Black", C)
    mesh_obj(name + "_Carrier", [(x - 0.09, y - 0.78, 0.71, x + 0.09, y - 0.36, 0.73)], "Metal", C)
    # wire front basket (open box)
    bx, by, bz = x, y + 0.60, 0.80
    mesh_obj(name + "_Basket", [(bx - 0.17, by - 0.14, bz, bx + 0.17, by + 0.14, bz + 0.01),
                                (bx - 0.17, by - 0.14, bz, bx - 0.16, by + 0.14, bz + 0.22), (bx + 0.16, by - 0.14, bz, bx + 0.17, by + 0.14, bz + 0.22),
                                (bx - 0.17, by - 0.14, bz, bx + 0.17, by - 0.13, bz + 0.22), (bx - 0.17, by + 0.13, bz, bx + 0.17, by + 0.14, bz + 0.22)],
             "Metal", C)
    mesh_obj(name + "_Fenders", [(x - 0.04, y - 0.9, 0.62, x + 0.04, y - 0.5, 0.64), (x - 0.04, y + 0.5, 0.62, x + 0.04, y + 0.85, 0.64)], paint, C)
mat("BikeTeal", (0.18, 0.55, 0.62), 0.35)
mat("BikeRed", (0.80, 0.18, 0.15), 0.35)
bike("Bicycle_1", 9.2, -2.0, "BikeRed"); bike("Bicycle_2", 9.95, -2.15, "BikeTeal")

# trees & shrubs
def tree(name, x, y, h=4.5, r=1.4):
    cyl(name + "_Trunk", x, y, 0, h * 0.55, 0.12, "Trunk", C, seg=10)
    for k in range(9):
        a = random.uniform(0, 2 * math.pi); d = random.uniform(0.2, 0.8) * r
        sphere(name + "_Leaves%d" % k, x + d * math.cos(a), y + d * math.sin(a),
               h * 0.58 + random.uniform(0, h * 0.35), r * random.uniform(0.5, 0.8), "Leaf", C, sz=0.75)
tree("Tree_FrontWest", -1.0, -2.5, 4.8, 1.3)
tree("Tree_BackWest", -1.0, 11.5, 5.5, 1.5)
tree("Tree_BackEast", 9.5, 11.5, 4.5, 1.3)
tree("Tree_East", 10.0, 4.0, 3.8, 1.1)
for i, (x, y) in enumerate([(1.0, -3.4), (2.1, -3.4), (5.5, -3.4), (6.5, -3.4), (7.5, -3.4), (0.0, -3.4), (-1.4, 3.0), (-1.4, 5.0), (10.4, 1.5)]):
    sphere("Shrub_%d" % i, x, y, 0.35, 0.5, "Leaf", C, sz=0.8)

# utility poles + wires
for i, (x, y) in enumerate([(-3.0, -4.6), (13.0, -4.6)]):
    cyl("UtilityPole_%d" % i, x, y, 0, 9.0, 0.15, "Concrete", C, r2=0.11)
    mesh_obj("UtilityPole_%d_Arm" % i, [(x - 0.9, y - 0.05, 8.2, x + 0.9, y + 0.05, 8.3)], "Concrete", C)
for dx in (-0.8, 0.0, 0.8):
    p1, p2 = Vector((-3.0 + dx, -4.6, 8.32)), Vector((13.0 + dx, -4.6, 8.32))
    d = p2 - p1
    w = cyl("Wire_%+.1f" % dx, 0, 0, 0, d.length, 0.01, "Black", C, seg=6)
    w.location = p1; w.rotation_mode = "QUATERNION"; w.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())

# ----- lighting / world -----
CL = coll("Lighting", root)
sun = bpy.data.lights.new("Sun", "SUN"); sun.energy = 3.5; sun.angle = math.radians(2)
so = bpy.data.objects.new("Sun", sun); so.rotation_euler = (math.radians(50), 0, math.radians(-35)); CL.objects.link(so)
w = bpy.context.scene.world or bpy.data.worlds.new("World")
bpy.context.scene.world = w; w.use_nodes = True
bg = next(n for n in w.node_tree.nodes if n.type == "BACKGROUND")
bg.inputs[0].default_value = (0.55, 0.72, 0.95, 1); bg.inputs[1].default_value = 0.8
cam = bpy.data.objects.new("Camera_Front", bpy.data.cameras.new("Camera_Front")); CL.objects.link(cam)
cam.location = (-9, -17, 7); cam.data.lens = 32
cam.rotation_euler = (Vector((4.5, 3, 2.5)) - cam.location).to_track_quat("-Z", "Y").to_euler()
bpy.context.scene.camera = cam

# ----- game helpers -----
CG = coll("Game_Helpers", root)
def empty(name, loc, rotz=0):
    e = bpy.data.objects.new(name, None); e.empty_display_type = "ARROWS"; e.empty_display_size = 0.4
    e.location = loc; e.rotation_euler.z = math.radians(rotz); CG.objects.link(e); return e
empty("Spawn_Street", (3.9, -5.5, 0), 0)
empty("Spawn_Genkan", (3.9, 0.7, 0.15), 0)
empty("POI_Nobita_Desk", (1.2, 1.3, 3.0), 90)
empty("POI_Nobita_Futon", (4.9, 1.1, 3.28), 0)
empty("POI_Doraemon_Oshiire", (5.0, 2.4, 3.8), 90)
empty("POI_Living_Sofa", (2.85, 6.2, 0.4), 180)
empty("POI_Dining_Table", (2.55, 7.85, 0.4), 0)
empty("POI_Kitchen", (1.2, 8.6, 0.4), 90)
empty("POI_Toilet_1F", (0.8, 0.9, 0.4), 180)
empty("POI_Parents_Bed", (3.7, 9.6, 3.0), 0)
# 170 cm human scale reference (hidden from render)
ref = cyl("ScaleRef_Human_170cm", 2.2, 2.4, 3.0, 4.7, 0.22, "Teal", CG, seg=16)
ref.hide_render = True
print("site done")
