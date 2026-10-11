# Furniture & fixtures (all at real-world scale)
import bpy, math
exec(open(LIB).read())
init_materials()
root = coll("NobitaHouse")
C = coll("House_Furniture", root)
F1, F2 = 0.40, 3.00

def table(name, x1, y1, x2, y2, z, h, top="WoodLight", leg="WoodDark", lt=0.05):
    t = 0.03
    b = [(x1, y1, z + h - t, x2, y2, z + h, 0)]
    for (lx, ly) in ((x1, y1), (x2 - lt, y1), (x1, y2 - lt), (x2 - lt, y2 - lt)):
        b.append((lx, ly, z, lx + lt, ly + lt, z + h - t, 1))
    return mesh_obj(name, b, [top, leg], C)

def chair(name, x, y, z, face, seat="WoodLight", frame="WoodDark", sh=0.45):
    # face: direction the sitter looks: 'n','s','e','w'
    s = 0.21
    b = [(x - s, y - s, z + sh - 0.04, x + s, y + s, z + sh, 0)]
    for dx in (-s, s - 0.04):
        for dy in (-s, s - 0.04):
            b.append((x + dx, y + dy, z, x + dx + 0.04, y + dy + 0.04, z + sh - 0.04, 1))
    back = {"n": (x - s, y - s, x + s, y - s + 0.04), "s": (x - s, y + s - 0.04, x + s, y + s),
            "e": (x - s, y - s, x - s + 0.04, y + s), "w": (x + s - 0.04, y - s, x + s, y + s)}[face]
    b.append((back[0], back[1], z + sh, back[2], back[3], z + sh + 0.45, 0))
    return mesh_obj(name, b, [seat, frame], C)

def shelf(name, x1, y1, x2, y2, z, h, n, books=True, m="WoodLight", open_side="x-"):
    t = 0.025
    b = [(x1, y1, z, x2, y2, z + t), (x1, y1, z + h - t, x2, y2, z + h)]
    if open_side in ("x-", "x+"):
        b += [(x1, y1, z, x2, y1 + t, z + h), (x1, y2 - t, z, x2, y2, z + h)]
        bx = (x2 - t, y1, z, x2, y2, z + h) if open_side == "x-" else (x1, y1, z, x1 + t, y2, z + h)
    else:
        b += [(x1, y1, z, x1 + t, y2, z + h), (x2 - t, y1, z, x2, y2, z + h)]
        bx = (x1, y2 - t, z, x2, y2, z + h) if open_side == "y-" else (x1, y1, z, x2, y1 + t, z + h)
    b.append(bx)
    for i in range(1, n):
        zz = z + h * i / n
        b.append((x1, y1, zz, x2, y2, zz + t))
    bk = []
    if books:
        import random
        random.seed(hash(name) & 0xffff)
        for i in range(n):
            zz = z + h * i / n + t
            span = (y1 + t, y2 - t) if open_side in ("x-", "x+") else (x1 + t, x2 - t)
            p = span[0]
            while p < span[1] - 0.04:
                w = random.uniform(0.02, 0.05); hh = random.uniform(0.15, min(0.28, h / n - 0.05))
                mi = random.randint(1, 3)
                if random.random() < 0.85:
                    if open_side in ("x-", "x+"):
                        bk.append((x1 + 0.03, p, zz, x2 - 0.04, p + w, zz + hh, mi))
                    else:
                        bk.append((p, y1 + 0.03, zz, p + w, y2 - 0.04, zz + hh, mi))
                p += w + 0.003
    return mesh_obj(name, b + bk, [m, "Book1", "Book2", "Book3"], C)

def cushion(name, x, y, z, s=0.27, m="Cushion"):
    return mesh_obj(name, [(x - s, y - s, z, x + s, y + s, z + 0.08)], m, C)

def futon(name, x1, y1, x2, y2, z, cover="FabricBlue"):
    mesh_obj(name, [(x1, y1, z, x2, y2, z + 0.09)], "FabricWhite", C)                                   # shikibuton
    mesh_obj(name + "_Kakebuton", [(x1 - 0.03, y1 + 0.45, z + 0.09, x2 + 0.03, y2 + 0.03, z + 0.17)], cover, C)
    return mesh_obj(name + "_Pillow", [(x1 + 0.22, y1 + 0.07, z + 0.09, x2 - 0.22, y1 + 0.4, z + 0.2)], "FabricWhite", C)

def tatami_room(name, x1, y1, x2, y2, z):
    """Lay 0.9 x 1.8 m mats in alternating courses, with dark cloth borders (heri) on the long edges."""
    b = []; g = 0.004; hw = 0.035
    rows = int(math.ceil((y2 - y1) / 0.9 - 1e-6))
    for r in range(rows):
        ya, yb = y1 + 0.9 * r, min(y1 + 0.9 * (r + 1), y2)
        xa = x1 - (0.9 if r % 2 else 0)
        while xa < x2 - 1e-6:
            xb = min(xa + 1.8, x2); xs = max(xa, x1)
            b.append((xs + g, ya + g, z - 0.012, xb - g, yb - g, z + 0.006, 0))
            b.append((xs + g, ya + g, z + 0.006, xb - g, ya + g + hw, z + 0.008, 1))
            if yb - ya > 0.5:
                b.append((xs + g, yb - g - hw, z + 0.006, xb - g, yb - g, z + 0.008, 1))
            xa += 1.8
    return mesh_obj(name, b, ["Tatami", "TatamiEdge"], coll("House_Floors_Walkable", root))

def ceiling_light(name, x, y, zc):
    cyl(name, x, y, zc - 0.12, zc, 0.25, "White", C, seg=24)
    L = bpy.data.lights.new(name + "_Light", "POINT"); L.energy = 250; L.shadow_soft_size = 0.3
    ob = bpy.data.objects.new(name + "_Light", L); ob.location = (x, y, zc - 0.3); C.objects.link(ob)


# ---------------------------------------------------------------------------------------------
# Layout matched to the reference cutaway (see build_shell.py for the plan lines)
# ---------------------------------------------------------------------------------------------
W, D, T = 5.6, 11.0, 0.15
XI, YI = W - T, D - T

def sofa_facing_minus_y(name, x1, x2, y1, y2, z):
    a = 0.15
    b = [(x1 + a, y1, z + 0.08, x2 - a, y2, z + 0.3, 0), (x1 + a, y2 - 0.18, z + 0.3, x2 - a, y2, z + 0.62, 0),
         (x1, y1, z + 0.08, x1 + a, y2, z + 0.62, 0), (x2 - a, y1, z + 0.08, x2, y2, z + 0.62, 0)]
    b += [(x, y, z, x + 0.04, y + 0.04, z + 0.08, 1) for x in (x1 + 0.03, x2 - 0.07) for y in (y1 + 0.03, y2 - 0.07)]
    mesh_obj(name, b, ["SofaGreen", "WoodDark"], C)
    n = 3; w = (x2 - x1 - 2 * a) / n
    cu = [(x1 + a + w * k, y1 + 0.02, z + 0.3, x1 + a + w * (k + 1) - 0.01, y2 - 0.18, z + 0.44) for k in range(n)]
    cu += [(x1 + a + w * k, y2 - 0.34, z + 0.44, x1 + a + w * (k + 1) - 0.01, y2 - 0.18, z + 0.86) for k in range(n)]
    mesh_obj(name + "_Cushions", cu, "SofaGreen", C)

# ======================= 1F =======================
# Genkan (tiled doma on the east side, front door in the street wall)
mesh_obj("Genkan_ShoeCabinet", [(5.0, -0.7, 0.15, 5.43, 0.6, 1.05)], "WoodLight", C)
mesh_obj("Genkan_StepBoard", [(3.0, 1.1, 0.15, 4.9, 1.4, 0.28)], "WoodDark", C)
mesh_obj("Genkan_Umbrella", [(4.7, -0.7, 0.15, 4.9, -0.5, 0.65)], "Metal", C)
ceiling_light("Genkan_Lamp", 3.9, 0.2, 2.8)
ceiling_light("Hall_1F_Lamp", 2.0, 2.5, 2.8)
# Toilet (front-west)
mesh_obj("Toilet_1F", [(0.6, -0.73, F1, 1.0, -0.25, F1 + 0.42), (0.58, -0.74, F1 + 0.42, 1.02, -0.56, F1 + 0.85)], "White", C)
mesh_obj("Toilet_1F_Washbasin", [(0.17, 0.5, F1, 0.6, 1.25, F1 + 0.8, 0), (0.22, 0.6, F1 + 0.8, 0.55, 1.15, F1 + 0.82, 1),
                                 (0.16, 0.6, F1 + 1.0, 0.18, 1.15, F1 + 1.6, 2)], ["White", "Metal", "Glass"], C)
# Living room: TV against the hall wall, green sofa facing it, coffee table on a rug, sideboard in the stair nook
mesh_obj("Living_Rug", [(1.6, 4.4, F1, 4.3, 6.3, F1 + 0.012)], "Rug", C)
drawer_chest("Living_TVStand", 1.7, 3.58, 3.4, 4.05, F1, 0.45, 1, "+y", C, m="WoodDark", plinth=0.04)
mesh_obj("Living_TV", [(2.05, 3.75, F1 + 0.45, 3.05, 3.84, F1 + 1.08), (2.45, 3.7, F1 + 0.45, 2.65, 3.9, F1 + 0.5)], "Black", C)
table("Living_CoffeeTable", 2.3, 4.85, 3.4, 5.5, F1, 0.4)
sofa_facing_minus_y("Living_Sofa", 1.8, 3.9, 5.9, 6.75, F1)
drawer_chest("Living_Sideboard", 0.2, 6.6, 1.1, 7.1, F1, 0.8, 2, "+y", C, m="WoodDark")
ceiling_light("Living_CeilingLamp", 3.0, 5.2, 2.8)
# Dining-kitchen: counter along the west wall, fridge in the back corner, table with 4 chairs
mesh_obj("Kitchen_Counter", [(T, 7.5, F1, 0.8, 9.9, F1 + 0.85, 0),
                             (0.25, 8.0, F1 + 0.85, 0.7, 8.7, F1 + 0.86, 1),     # sink
                             (0.25, 9.1, F1 + 0.85, 0.7, 9.7, F1 + 0.87, 2)],    # stove
         ["White", "Metal", "Black"], C)
mesh_obj("Kitchen_Hood", [(T, 9.05, F1 + 1.75, 0.6, 9.75, F1 + 2.3)], "Metal", C)
mesh_obj("Kitchen_UpperCabinet", [(T, 7.5, F1 + 1.6, 0.5, 7.75, F1 + 2.3)], "WoodLight", C)
mesh_obj("Kitchen_Fridge", [(T, 10.1, F1, 0.85, YI - 0.02, F1 + 1.75)], "TileBlue", C)
drawer_chest("Kitchen_Cabinet", 4.9, 10.2, 5.43, YI - 0.02, F1, 0.9, 3, "-x", C)
table("Dining_Table", 2.2, 8.2, 3.6, 9.2, F1, 0.72)
chair("Dining_Chair_1", 2.55, 7.85, F1, "n"); chair("Dining_Chair_2", 3.25, 7.85, F1, "n")
chair("Dining_Chair_3", 2.55, 9.55, F1, "s"); chair("Dining_Chair_4", 3.25, 9.55, F1, "s")
ceiling_light("Dining_CeilingLamp", 2.9, 8.7, 2.8)
ceiling_light("Kitchen_Lamp", 1.0, 8.8, 2.8)

# ======================= 2F: Nobita's room (matches the reference room sheet) =======================
#   left (west) wall: window with green curtains, desk under it | back wall: poster, bookshelf, door, chest
#   right (east) wall: oshiire (Doraemon sleeps on the upper shelf) | front-right corner: low bed with blue futon
tatami_room("Tatami_2F_Nobita", T, T, XI, 3.4, F2)
mesh_obj("Nobita_Desk", [(0.17, 0.55, F2 + 0.7, 0.82, 1.95, F2 + 0.74), (0.17, 1.9, F2, 0.82, 1.95, F2 + 0.7),
                         (0.17, 1.12, F2 + 0.55, 0.82, 1.9, F2 + 0.57)], "WoodLight", C)
drawer_chest("Nobita_Desk_Pedestal", 0.17, 0.55, 0.82, 1.08, F2, 0.7, 3, "+x", C, plinth=0.03)
drawer_chest("Nobita_Desk_CenterDrawer", 0.3, 1.12, 0.82, 1.88, F2 + 0.58, 0.12, 1, "+x", C, plinth=0.0)
mesh_obj("Nobita_DeskLamp", [(0.25, 1.5, F2 + 0.74, 0.4, 1.65, F2 + 0.76), (0.3, 1.55, F2 + 0.76, 0.34, 1.59, F2 + 1.15),
                             (0.3, 1.3, F2 + 1.12, 0.6, 1.62, F2 + 1.18)], "Teal", C)
chair("Nobita_Chair", 1.2, 1.3, F2, "w", seat="Teal", frame="Metal")
mesh_obj("Nobita_Curtains", [(0.17, 0.42, F2 + 0.75, 0.24, 0.72, F2 + 2.2), (0.17, 2.28, F2 + 0.75, 0.24, 2.58, F2 + 2.2),
                             (0.18, 0.35, F2 + 2.2, 0.21, 2.65, F2 + 2.23, 1)], ["SofaGreen", "Metal"], C)
mesh_obj("Nobita_Poster", [(0.5, 3.385, F2 + 0.95, 1.0, 3.395, F2 + 1.65)], "Blue", C)
mesh_obj("Nobita_Calendar", [(0.55, 3.385, F2 + 0.5, 0.95, 3.395, F2 + 0.9)], "White", C)
shelf("Nobita_Bookshelf", 1.2, 3.05, 2.3, 3.39, F2, 1.8, 5, open_side="y-")
sphere("Nobita_Globe", 2.05, 3.22, F2 + 1.95, 0.13, "Blue", C)
drawer_chest("Nobita_Chest", 3.55, 3.0, 4.4, 3.39, F2, 0.8, 3, "-y", C)
# oshiire on the east wall: carcass, middle shelf with Doraemon's futon, two sliding fusuma (front one opens)
OX0, OX1, OY0, OY1 = 4.6, XI, 2.0, 3.4
mesh_obj("Nobita_Oshiire", [(OX0, OY0, F2, OX1, OY1, F2 + 0.05), (OX0, OY0, F2 + 0.75, OX1, OY1, F2 + 0.8),
                            (OX0, OY0, F2 + 1.85, OX1, OY1, 5.4), (OX0, OY0 - 0.04, F2, OX1, OY0, 5.4)], "WoodLight", C)
futon("Oshiire_Doraemon_Futon", 4.68, 2.05, 5.4, 2.95, F2 + 0.8, cover="FabricRed")
mesh_obj("Nobita_Oshiire_Fusuma_Back", [(4.6, 2.68, F2 + 0.05, 4.632, 3.37, F2 + 1.85, 0),
                                        (4.597, 2.68, F2 + 0.75, 4.636, 3.37, F2 + 0.85, 1)], ["Fusuma", "Blue"], C)
fu = mesh_obj("Nobita_Oshiire_Fusuma_Front", [(4.566, 2.0, F2 + 0.05, 4.598, 2.72, F2 + 1.85, 0),
                                              (4.562, 2.0, F2 + 0.75, 4.6, 2.72, F2 + 0.85, 1)], ["Fusuma", "Blue"], C)
fu["openable"] = "slide"; fu["open_offset"] = (0.0, 0.64, 0.0)
# low bed with futon in the front-right corner
mesh_obj("Nobita_Bed", [(4.42, 0.2, F2, 5.42, 1.95, F2 + 0.28), (4.42, 0.17, F2, 5.42, 0.22, F2 + 0.55)], "WoodLight", C)
futon("Nobita_Futon", 4.47, 0.26, 5.37, 1.9, F2 + 0.28, cover="FabricBlue")
cushion("Nobita_Zabuton", 2.6, 1.7, F2)
cyl("Nobita_WasteBasket", 0.4, 2.45, F2, F2 + 0.35, 0.14, "Blue", C)
sphere("Nobita_Ball", 1.75, 2.75, F2 + 0.11, 0.11, "White", C)
mesh_obj("Nobita_Comics", [(2.0, 2.3, F2, 2.25, 2.48, F2 + 0.06), (2.08, 2.38, F2 + 0.06, 2.3, 2.55, F2 + 0.1)], ["Book1"], C)
ceiling_light("Nobita_CeilingLamp", 2.8, 1.8, 5.4)

# ======================= 2F: hall, toilet, closet, storage, parents' room =======================
mesh_obj("Toilet_2F", [(1.6, 5.95, F2, 2.0, 6.43, F2 + 0.42), (1.58, 6.25, F2 + 0.42, 2.02, 6.43, F2 + 0.85)], "White", C)
shelf("Closet_2F_Shelves", 1.27, 3.55, 2.3, 3.9, F2, 2.0, 4, books=False, open_side="y+")
mesh_obj("Storage_Boxes", [(3.75, 6.9, F2, 5.4, 7.55, F2 + 1.2), (4.9, 3.55, F2, 5.4, 4.6, F2 + 0.9),
                           (3.8, 3.55, F2, 4.5, 3.95, F2 + 0.5)], "WoodLight", C)
ceiling_light("Hall_2F_Lamp", 2.4, 7.1, 5.4)
ceiling_light("Storage_Lamp", 4.55, 5.5, 5.4)
# parents' room: western double bed (pink), desk under the back window, dresser, wardrobe
mesh_obj("Parents_Bed", [(2.8, 8.75, F2, 4.6, 10.8, F2 + 0.35, 0), (2.8, 10.7, F2, 4.6, 10.83, F2 + 0.95, 0)], ["WoodLight"], C)
mesh_obj("Parents_Bed_Mattress", [(2.85, 8.8, F2 + 0.35, 4.55, 10.7, F2 + 0.55)], "FabricWhite", C)
mesh_obj("Parents_Bed_Cover", [(2.82, 8.75, F2 + 0.55, 4.58, 10.0, F2 + 0.62)], "FabricRed", C)
mesh_obj("Parents_Bed_Pillows", [(2.95, 10.2, F2 + 0.55, 3.6, 10.6, F2 + 0.68), (3.8, 10.2, F2 + 0.55, 4.45, 10.6, F2 + 0.68)], "FabricRed", C)
table("Parents_Desk", 1.0, 10.3, 2.4, 10.83, F2, 0.72)
chair("Parents_Desk_Chair", 1.7, 9.95, F2, "n")
drawer_chest("Parents_Dresser", 0.17, 7.85, 0.6, 8.35, F2, 0.75, 3, "+x", C, m="WoodDark")
mesh_obj("Parents_Wardrobe", [(4.85, 9.6, F2, 5.43, YI - 0.02, F2 + 2.0)], "WoodLight", C)
ceiling_light("Parents_CeilingLamp", 2.8, 9.3, 5.4)
print("furniture done", len(C.objects))
