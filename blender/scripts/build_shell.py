# Nobita's house shell (layout matched to the reference cutaway):
#   long narrow house, gable + entrance facing the street (-Y), rooms run front -> back along +Y.
#   1F: toilet / genkan + hall | stairs (west wall, rising to the back) beside the living room | dining-kitchen
#   2F: Nobita's room (front, full width) | hall + toilet/closet + storage | parents' bedroom (back)
import bpy, math
from mathutils import Vector
exec(open(LIB).read())

for ob in list(bpy.data.objects):
    bpy.data.objects.remove(ob, do_unlink=True)
for c in list(bpy.data.collections):
    bpy.data.collections.remove(c)
for me in list(bpy.data.meshes):
    bpy.data.meshes.remove(me)
init_materials()

root = coll("NobitaHouse")
C_STRUCT = coll("House_Structure", root)
C_FLOOR = coll("House_Floors_Walkable", root)
C_OPEN = coll("House_Doors_Windows", root)
C_ROOF = coll("House_Roof", root)
C_GAME = coll("Game_Helpers", root)

W, D = 5.6, 11.0                      # footprint (X width x Y depth)
F1, F1C, F2, F2C, TOP = 0.40, 2.80, 3.00, 5.40, 5.50
T = 0.15
XI, YI = W - T, D - T                 # inner faces of east / back walls
H = 0.05
# key lines of the plan
Y_HALL = 1.4      # genkan / toilet  | entrance hall
Y_ST0, Y_ST1 = 3.5, 6.5               # stair run (12 treads x 0.25) along the west wall, x 0.15-1.1
Y_LIV1 = 7.2      # living | dining-kitchen (open plan)
Y_N = 3.45        # 2F: Nobita's room back wall
X_HOLE = 1.15
X_HALL0, X_HALL1 = 2.4, 3.65          # 2F hall between closet/toilet and storage
Y_LAND1 = 7.65    # 2F landing | parents' room wall

# ---------- foundation & floors ----------
# The ground floor front projects PJ forward of the 2F wall and carries its own small gable roof
PJ = 0.9
YF = -PJ + T                          # inner face of the projected 1F front wall
DOMA = (2.9, YF, XI, Y_HALL)
mesh_obj("Foundation", [(T, Y_HALL, 0, XI, YI, 0.38), (T, YF, 0, DOMA[0], Y_HALL, 0.38),
                        (DOMA[0], YF, 0, XI, Y_HALL, 0.13)], "Concrete", C_STRUCT)
z0 = F1 - 0.02
for n, boxes, m in [
        ("1F_Genkan_Doma", [(DOMA[0], YF, 0.13, XI, Y_HALL, 0.15)], "Stone"),
        ("1F_Toilet", [(T, YF, z0, 1.5, Y_HALL, F1)], "Tile"),
        ("1F_Hall", [(1.5, YF, z0, DOMA[0], Y_HALL, F1), (T, Y_HALL, z0, XI, Y_ST0, F1)], "WoodFloor"),
        ("1F_UnderStairs", [(T, Y_ST0, z0, X_HOLE, Y_ST1, F1)], "WoodFloor"),
        ("1F_Living", [(X_HOLE, Y_ST0, z0, XI, Y_LIV1, F1), (T, Y_ST1, z0, X_HOLE, Y_LIV1, F1)], "WoodFloor"),
        ("1F_Dining_Kitchen", [(T, Y_LIV1, z0, XI, YI, F1)], "WoodFloor")]:
    mesh_obj("Floor_" + n, boxes, m, C_FLOOR)
# 1F ceiling / 2F slab with stair hole
mesh_obj("Slab_1F_Ceiling", [(T, YF, F1C, XI, Y_ST0, F2 - 0.02),(X_HOLE, Y_ST0, F1C, XI, Y_ST1, F2 - 0.02),
                             (T, Y_ST1, F1C, XI, YI, F2 - 0.02)], "Ceiling", C_STRUCT)
z2 = F2 - 0.02
for n, boxes, m in [
        ("2F_NobitaRoom_Tatami", [(T, T, z2, XI, Y_N, F2)], "Tatami"),
        ("2F_Hall", [(X_HALL0, Y_N, z2, X_HALL1, Y_ST1, F2), (T, Y_ST1, z2, X_HALL1, Y_LAND1, F2)], "WoodFloor"),
        ("2F_Closet", [(X_HOLE, Y_ST0, z2, X_HALL0, 5.15, F2)], "WoodFloor"),
        ("2F_Toilet", [(X_HOLE, 5.15, z2, X_HALL0, Y_ST1, F2)], "Tile"),
        ("2F_Storage", [(X_HALL1, Y_N, z2, XI, Y_LAND1, F2)], "WoodFloor"),
        ("2F_ParentsRoom", [(T, Y_LAND1, z2, XI, YI, F2)], "WoodFloor")]:
    mesh_obj("Floor_" + n, boxes, m, C_FLOOR)
mesh_obj("Slab_2F_Ceiling", [(T, T, F2C, XI, YI, TOP)], "Ceiling", C_STRUCT)

# ---------- exterior walls ----------
B1, B2 = (0.0, 2.9), (2.9, TOP)
DOOR_F = (2.95, 4.55, 0.15, 2.25)     # wooden double entrance doors
WIN_2F_FRONT = (1.95, 4.05, 4.0, 5.0)  # wide window with a shutter box (tobukuro) on its left
ext = {
    "Front": ("x", 0, W, -PJ, YF,
              [DOOR_F, (0.55, 1.1, 1.8, 2.3), (4.8, 5.25, 1.4, 2.3)],
              []),
    "Front2F": ("x", 0, W, 0, T, None, [WIN_2F_FRONT]),
    "Back": ("x", 0, W, YI, D,
             [(1.6, 3.0, 1.3, 2.5), (3.6, 4.8, 1.3, 2.5)],
             [(1.0, 2.5, 3.9, 5.0), (3.3, 4.6, 3.9, 5.0)]),
    "West": ("y", T, YI, 0, T,
             [(4.6, 5.4, 1.7, 2.5), (7.7, 8.9, 1.6, 2.4)],
             [(0.7, 2.3, 3.9, 5.0), (6.7, 7.4, 4.0, 4.9), (8.4, 9.4, 3.9, 5.0)]),
    "East": ("y", T, YI, XI, W,
             [(4.0, 5.6, F1, 2.4), (8.0, 9.6, 1.3, 2.5)],
             [(5.0, 5.8, 4.0, 4.9), (8.0, 9.4, 3.9, 5.0)]),
}
for side, (ax, a1, a2, c1, c2, o1, o2) in ext.items():
    if o1 is not None:
        s1 = a1 if ax == "x" else YF          # side walls run forward to the projected front on 1F
        wall("ExtWall_%s_1F" % side, ax, s1, a2, c1, c2, *B1, "WallExt", C_STRUCT, o1)
    if o2 is not None and side != "Front":
        wall("ExtWall_%s_2F" % side.replace("Front2F", "Front"), ax, a1, a2, c1, c2, *B2, "WallExt", C_STRUCT, o2)
    for i, (p1, p2, zb, zt) in enumerate((o1 or []) + (o2 or [])):
        if (p1, p2, zb, zt) == DOOR_F:
            continue
        window("Win_%s_%d" % (side, i), ax, p1, p2, c1, c2, zb, zt, C_OPEN)
mesh_obj("BaseBand", [(-0.02, -PJ - 0.02, 0, DOOR_F[0], -PJ, F1), (DOOR_F[1], -PJ - 0.02, 0, W + 0.02, -PJ, F1),
                      (-0.02, D, 0, W + 0.02, D + 0.02, F1), (-0.02, -PJ, 0, 0, D, F1), (W, -PJ, 0, W + 0.02, D, F1)],
         "Concrete", C_STRUCT)
# 2F front: shutter box (tobukuro) beside the window + small tiled canopies over 2F windows
mesh_obj("Tobukuro_2F_Front", [(1.0, -0.2, 3.95, 1.92, T, 5.05, 0)] +
         [(1.03 + 0.15 * k, -0.215, 3.98, 1.03 + 0.15 * k + 0.12, -0.2, 5.02, 1) for k in range(6)], ["WoodLight", "WoodDark"], C_OPEN)
def canopy(name, axis, a1, a2, face, sgn, z, depth=0.5):
    """Small sloped tiled hisashi over a window. face = outer wall plane, sgn = +1/-1 outward direction."""
    if axis == "x":
        e1, e2, sv = (a1, face + sgn * depth, z), (a2, face + sgn * depth, z), (0, -sgn * depth, 0.22)
        deck = [(a1, face + sgn * depth, z), (a2, face + sgn * depth, z), (a2, face, z + 0.22), (a1, face, z + 0.22)]
    else:
        e1, e2, sv = (face + sgn * depth, a1, z), (face + sgn * depth, a2, z), (-sgn * depth, 0, 0.22)
        deck = [(face + sgn * depth, a1, z), (face + sgn * depth, a2, z), (face, a2, z + 0.22), (face, a1, z + 0.22)]
    slab_quad(name, deck, 0.05, "WoodDark", C_ROOF)
    tile_roof(name + "_Tiles", e1, e2, sv, C_ROOF, w=0.25, row=0.2, t=0.025, A=0.03)
canopy("Canopy_2F_Front", "x", 0.85, 4.25, 0.0, -1, 5.12, 0.55)
canopy("Canopy_2F_East_1", "y", 4.85, 5.95, W, 1, 5.02, 0.45)
canopy("Canopy_2F_East_2", "y", 7.85, 9.55, W, 1, 5.12, 0.45)
canopy("Canopy_2F_West_1", "y", 0.55, 2.45, 0.0, -1, 5.12, 0.45)
canopy("Canopy_2F_Back", "x", 0.85, 4.75, D, 1, 5.12, 0.45)

# ---------- interior walls ----------
iw1 = [("IntWall_1F_Toilet_E", "y", T, Y_HALL, 1.5 - H, 1.5 + H, []),
       ("IntWall_1F_Toilet_N", "x", T, 1.5, Y_HALL - H, Y_HALL + H, [(0.45, 1.15, F1, 2.4)]),
       ("IntWall_1F_Hall_Living", "x", X_HOLE, XI, Y_ST0 - H, Y_ST0 + H, [(4.3, 5.1, F1, 2.4)])]
for n, ax, a1, a2, c1, c2, op in iw1:
    wall(n, ax, a1, a2, c1, c2, F1, F1C, "WallInt", C_STRUCT, op)
iw2 = [("IntWall_2F_Nobita_Back", "x", T, XI, Y_N - H, Y_N + H, [(2.6, 3.4, F2, 5.0)]),
       ("IntWall_2F_Hole_E", "y", Y_ST0, Y_ST1, X_HOLE, X_HOLE + 0.1, []),
       ("IntWall_2F_Closet_Toilet_E", "y", Y_ST0, Y_ST1, X_HALL0 - H, X_HALL0 + H, [(3.9, 4.7, F2, 5.0), (5.5, 6.2, F2, 5.0)]),
       ("IntWall_2F_Closet_Toilet", "x", X_HOLE + 0.1, X_HALL0 - H, 5.15 - H, 5.15 + H, []),
       ("IntWall_2F_Toilet_S", "x", X_HOLE, X_HALL0 - H, Y_ST1 - H, Y_ST1 + H, []),
       ("IntWall_2F_Storage_W", "y", Y_N + H, Y_LAND1 - H, X_HALL1 - H, X_HALL1 + H, [(4.6, 5.4, F2, 5.0)]),
       ("IntWall_2F_Landing_Parents", "x", T, XI, Y_LAND1 - H, Y_LAND1 + H, [(1.0, 1.8, F2, 5.0)])]
for n, ax, a1, a2, c1, c2, op in iw2:
    wall(n, ax, a1, a2, c1, c2, F2, F2C, "WallInt", C_STRUCT, op)

# ---------- doors (origin at hinge, closed; animated by animate.py) ----------
DM = (DOOR_F[0] + DOOR_F[1]) / 2
door("Door_Genkan_L", "x", DOOR_F[0], DM, -PJ, YF, 0.15, 2.25, C_OPEN, "WoodDark", swing=1)
door("Door_Genkan_R", "x", DM, DOOR_F[1], -PJ, YF, 0.15, 2.25, C_OPEN, "WoodDark", swing=-1, hinge_end=True)
# glazed upper panels on the entrance doors
for nm in ("Door_Genkan_L", "Door_Genkan_R"):
    dob = bpy.data.objects[nm]; w = DM - DOOR_F[0] - 0.02
    gl = mesh_obj(nm + "_Glass", [(0.1, -0.03, 1.2, w - 0.1, 0.03, 1.95)], "Glass", C_OPEN, origin=None)
    gl.parent = dob
door("Door_1F_Toilet", "x", 0.45, 1.15, Y_HALL - H, Y_HALL + H, F1, 2.4, C_OPEN, swing=1)
door("Door_1F_Living", "x", 4.3, 5.1, Y_ST0 - H, Y_ST0 + H, F1, 2.4, C_OPEN, "DoorRed", swing=-1, hinge_end=True)
door("Door_2F_Nobita", "x", 2.6, 3.4, Y_N - H, Y_N + H, F2, 5.0, C_OPEN, swing=1, hinge_end=True)
door("Door_2F_Closet", "y", 3.9, 4.7, X_HALL0 - H, X_HALL0 + H, F2, 5.0, C_OPEN, swing=1, hinge_end=True)
door("Door_2F_Toilet", "y", 5.5, 6.2, X_HALL0 - H, X_HALL0 + H, F2, 5.0, C_OPEN, swing=-1)
door("Door_2F_Storage", "y", 4.6, 5.4, X_HALL1 - H, X_HALL1 + H, F2, 5.0, C_OPEN, "Fusuma", swing=-1)
door("Door_2F_Parents", "x", 1.0, 1.8, Y_LAND1 - H, Y_LAND1 + H, F2, 5.0, C_OPEN, swing=1)

# ---------- stairs: 13 risers x 0.20, 12 treads x 0.25, along the west wall ----------
treads, risers = [], []
for i in range(12):
    y0 = Y_ST0 + 0.25 * i; z = F1 + 0.2 * (i + 1)
    treads.append((T, y0 - 0.025, z - 0.035, 1.1, y0 + 0.25, z))
    risers.append((0.16, y0, z - 0.2, 1.09, y0 + 0.015, z - 0.035))
risers.append((T, Y_ST1 - 0.015, F1C, X_HOLE, Y_ST1, F2))
mesh_obj("Stairs_Treads", treads, "WoodFloor", C_FLOOR)
mesh_obj("Stairs_Risers", risers, "WoodLight", C_STRUCT)
poly_prism("Stairs_SidePanel", [(Y_ST0, F1), (Y_ST1, F1), (Y_ST1, F2 - 0.06), (Y_ST0, F1 + 0.14)], "y", 1.09, 1.11, "WallInt", C_STRUCT)
poly_prism("Stairs_Stringer", [(Y_ST0 - 0.02, F1 + 0.12), (Y_ST1, F2 - 0.08), (Y_ST1, F2 + 0.1), (Y_ST0 - 0.02, F1 + 0.3)], "y", 1.085, 1.125, "WoodDark", C_STRUCT)
poly_prism("Stairs_WallStringer", [(Y_ST0 - 0.02, F1), (Y_ST1, F2 - 0.08), (Y_ST1, F2 + 0.1), (Y_ST0 - 0.02, F1 + 0.3)], "y", T, T + 0.02, "WoodDark", C_STRUCT)
ramp = slab_quad("Collider_Stairs_Ramp-colonly", [(T, Y_ST0, F1), (1.1, Y_ST0, F1), (1.1, Y_ST1, F2), (T, Y_ST1, F2)], 0.05, "Glass", C_GAME)
ramp.display_type = "WIRE"; ramp.hide_render = True

def rod(name, p1, p2, r, m, col):
    p1, p2 = Vector(p1), Vector(p2)
    d = p2 - p1
    ob = cyl(name, 0, 0, 0, d.length, r, m, col, seg=16)
    ob.location = p1
    ob.rotation_mode = "QUATERNION"
    ob.rotation_quaternion = Vector((0, 0, 1)).rotation_difference(d.normalized())
    return ob
rod("Stair_Handrail", (1.12, Y_ST0, F1 + 0.9), (1.12, Y_ST1, F2 + 0.9), 0.025, "WoodDark", C_STRUCT)
cyl("Stair_Newel_Bottom", 1.12, Y_ST0 + 0.05, F1, F1 + 0.95, 0.04, "WoodDark", C_STRUCT)
for k in range(1, 6):
    y = Y_ST0 + 0.5 * k
    cyl("Stair_Baluster_%d" % k, 1.12, y, F1 + 0.4 * k, F1 + 0.4 * k + 0.9, 0.015, "WoodDark", C_STRUCT)

# ---------- roof: gable facing the street, ridge along Y ----------
XM = W / 2
def rz(x):
    return 5.65 + 0.4 * min(x, W - x)
O = 0.6
YA, YB = -O, D + O
slab_quad("Roof_Deck_West", [(-O, YA, rz(-O)), (XM, YA, rz(XM)), (XM, YB, rz(XM)), (-O, YB, rz(-O))], 0.12, "WoodDark", C_ROOF)
slab_quad("Roof_Deck_East", [(XM, YA, rz(XM)), (W + O, YA, rz(-O)), (W + O, YB, rz(-O)), (XM, YB, rz(XM))], 0.12, "WoodDark", C_ROOF)
tile_roof("Roof_Tiles_West", (-O, YA, rz(-O)), (-O, YB, rz(-O)), (XM + O, 0, rz(XM) - rz(-O)), C_ROOF)
tile_roof("Roof_Tiles_East", (W + O, YA, rz(-O)), (W + O, YB, rz(-O)), (-(XM + O), 0, rz(XM) - rz(-O)), C_ROOF)
R = rz(XM)
mesh_obj("Roof_Ridge_Noshi", [(XM - 0.24 + 0.03 * k, YA - 0.04, R - 0.02 + 0.055 * k, XM + 0.24 - 0.03 * k, YB + 0.04, R + 0.035 + 0.055 * k) for k in range(3)], "RoofRed", C_ROOF)
rod("Roof_Ridge_Cap", (XM, YA - 0.06, R + 0.2), (XM, YB + 0.06, R + 0.2), 0.11, "RoofRed", C_ROOF)
for nm, y0, y1 in (("Front", YA - 0.14, YA - 0.04), ("Back", YB + 0.04, YB + 0.14)):
    mesh_obj("Roof_Onigawara_" + nm, [(XM - 0.2, y0, R - 0.05, XM + 0.2, y1, R + 0.3)], "RoofRed", C_ROOF)
for side, xe in (("W", -O), ("E", W + O)):
    for nm, y in (("Front", YA + 0.07), ("Back", YB - 0.07)):
        rod("Roof_Barge_%s_%s" % (side, nm), (xe, y, rz(-O) + 0.06), (XM, y, R + 0.06), 0.075, "RoofRed", C_ROOF)
gable = [(0, TOP), (W, TOP), (W, rz(W)), (XM, rz(XM)), (0, rz(0))]
poly_prism("Gable_Front", gable, "x", 0, T, "WallExt", C_ROOF)
poly_prism("Gable_Back", gable, "x", YI, D, "WallExt", C_ROOF)
mesh_obj("Gable_Vent", [(XM - 0.35, -0.03, 5.85, XM + 0.35, 0.0, 6.2)], "WoodDark", C_ROOF)
slab_quad("Fascia_Front_W", [(-O, -O - 0.03, rz(-O)), (XM, -O - 0.03, rz(XM)), (XM, -O + 0.03, rz(XM)), (-O, -O + 0.03, rz(-O))], 0.2, "White", C_ROOF)
slab_quad("Fascia_Front_E", [(XM, -O - 0.03, rz(XM)), (W + O, -O - 0.03, rz(-O)), (W + O, -O + 0.03, rz(-O)), (XM, -O + 0.03, rz(XM))], 0.2, "White", C_ROOF)
# 1F eaves (hisashi): front over the entrance, back, and along the east (garden) side
# small front gable roof over the projecting ground floor (second gable on the facade)
FG_Y0, FG_EZ, FG_P = -PJ - 0.55, 3.0, 0.25          # eave line in front, eave height, pitch
def fz(x):
    return FG_EZ + FG_P * (min(x, W - x) + 0.4)
for nm, xe in (("W", -0.4), ("E", W + 0.4)):
    xr = XM
    slab_quad("FrontGable_Deck_" + nm, [(xe, FG_Y0, fz(xe)), (xr, FG_Y0, fz(xr)), (xr, 0.0, fz(xr)), (xe, 0.0, fz(xe))]
              if nm == "W" else [(xr, FG_Y0, fz(xr)), (xe, FG_Y0, fz(xe)), (xe, 0.0, fz(xe)), (xr, 0.0, fz(xr))], 0.08, "WoodDark", C_ROOF)
    tile_roof("FrontGable_Tiles_" + nm, (xe, FG_Y0, fz(xe)), (xe, 0.0, fz(xe)), (xr - xe, 0, fz(xr) - fz(xe)), C_ROOF)
fg = [(0, 2.9), (W, 2.9), (W, fz(W)), (XM, fz(XM)), (0, fz(0))]
poly_prism("FrontGable_Face", fg, "x", -PJ, YF, "WallExt", C_ROOF)
mesh_obj("FrontGable_Vent", [(XM - 0.3, -PJ - 0.03, 3.12, XM + 0.3, -PJ, 3.36)], "WoodDark", C_ROOF)
rod("FrontGable_Ridge", (XM, FG_Y0 - 0.05, fz(XM) + 0.09), (XM, -0.02, fz(XM) + 0.09), 0.08, "RoofRed", C_ROOF)
mesh_obj("FrontGable_Onigawara", [(XM - 0.14, FG_Y0 - 0.08, fz(XM) - 0.02, XM + 0.14, FG_Y0 - 0.02, fz(XM) + 0.2)], "RoofRed", C_ROOF)
for nm, xe in (("W", -0.4), ("E", W + 0.4)):
    slab_quad("FrontGable_Fascia_" + nm, [(xe, FG_Y0 - 0.03, fz(xe)), (XM, FG_Y0 - 0.03, fz(XM)), (XM, FG_Y0 + 0.03, fz(XM)), (xe, FG_Y0 + 0.03, fz(xe))], 0.16, "White", C_ROOF)
    rod("FrontGable_Barge_" + nm, (xe, FG_Y0 + 0.05, fz(xe) + 0.05), (XM, FG_Y0 + 0.05, fz(XM) + 0.05), 0.06, "RoofRed", C_ROOF)
slab_quad("Eave_1F_Back", [(-0.4, D, 3.4), (W + 0.4, D, 3.4), (W + 0.4, D + 0.75, 3.05), (-0.4, D + 0.75, 3.05)], 0.08, "WoodDark", C_ROOF)
slab_quad("Eave_1F_East", [(W, 0, 3.4), (W + 0.75, 0, 3.05), (W + 0.75, D, 3.05), (W, D, 3.4)], 0.08, "WoodDark", C_ROOF)
tile_roof("Eave_1F_Back_Tiles", (-0.4, D + 0.75, 3.05), (W + 0.4, D + 0.75, 3.05), (0, -0.75, 0.35), C_ROOF)
tile_roof("Eave_1F_East_Tiles", (W + 0.75, 0, 3.05), (W + 0.75, D, 3.05), (-0.75, 0, 0.35), C_ROOF)
mesh_obj("Eave_1F_Flashing", [(-0.4, -0.02, 3.38, W + 0.4, 0.0, 3.55), (-0.4, D, 3.38, W + 0.4, D + 0.02, 3.55),
                              (W, 0, 3.38, W + 0.02, D, 3.55)], "Concrete", C_ROOF)
mesh_obj("Gutters", [(-O, -O - 0.12, rz(-O) - 0.2, -O + 0.1, YB + 0.12, rz(-O) - 0.1),
                     (W + O - 0.1, -O - 0.12, rz(-O) - 0.2, W + O, YB + 0.12, rz(-O) - 0.1)], "Gutter", C_ROOF)
cyl("Downpipe_Front", W + 0.07, -0.3, 0, 3.0, 0.04, "Gutter", C_ROOF)
cyl("Downpipe_East", W + O - 0.05, D - 0.3, 0, rz(-O) - 0.15, 0.04, "Gutter", C_ROOF)
mesh_obj("Chimney", [(3.6, 7.4, 6.0, 4.1, 7.9, 7.2), (3.55, 7.35, 7.2, 4.15, 7.95, 7.28)], "White", C_ROOF)
cyl("Antenna_Mast", XM, 3.0, R, R + 2.0, 0.025, "Metal", C_ROOF)
mesh_obj("Antenna_Boom", [(XM - 0.02, 2.2, R + 1.8, XM + 0.02, 3.8, R + 1.83)], "Metal", C_ROOF)
mesh_obj("Antenna_Elements", [(XM - 0.4, 2.3 + 0.2 * k, R + 1.8, XM + 0.4, 2.32 + 0.2 * k, R + 1.82) for k in range(8)], "Metal", C_ROOF)
print("shell objects:", len(bpy.data.objects))
