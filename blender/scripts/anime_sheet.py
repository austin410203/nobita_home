# Renders every panel of the anime setting sheet. Call run(group) with group in
# "main", "elev", "vignette", "detail"  (split so each Blender call stays short).
import bpy, math
from mathutils import Vector
exec(open(LIB.replace("lib.py", "anime_render.py"), encoding="utf-8-sig").read())
exec(open(LIB.replace("lib.py", "anime_style2.py"), encoding="utf-8-sig").read())
SHEET_FRAME = 44   # animation test timeline: doors / windows / fusuma open, drawers closed

HOUSE = Vector((2.8, 5.5, 0.0))       # footprint centre (5.6 x 11.0 house)
LOT = Vector((4.5, 4.5, 4.2))         # lot centre for elevations
DOLL_DIR = Vector((1.0, -0.45, 0.78)).normalized()   # seen from the east side, front (street) to the left

def set_sun(yaw):
    sun = bpy.data.objects.get("Sun")
    if sun:
        sun.rotation_euler = (math.radians(52), 0, math.radians(yaw - 38))

_hid = []
def hide(pred):
    for ob in bpy.data.objects:
        if ob.type in ("MESH", "FONT") and not ob.hide_render and pred(ob):
            ob.hide_render = True; _hid.append(ob)

def unhide():
    for ob in _hid: ob.hide_render = False
    _hid.clear()

def only(prefixes):
    hide(lambda o: not o.name.startswith(tuple(prefixes)))

NOT_SITE = ("BD_", "Wire", "UtilityPole", "Street", "ScaleRef", "Collider_")
ROOF = lambda o: "House_Roof" in {c.name for c in o.users_collection}

def run(group):
    backdrop()
    bpy.data.collections["Render_Backdrop"].hide_viewport = False
    game_world = bpy.data.worlds.get("World")
    sc.world = anime_world()
    lumpy_leaves(True); swap_to_toon(); watercolor_comp(False); sc.frame_set(SHEET_FRAME)
    sc.render.film_transparent = False
    out = []
    try:
        if group == "main":
            setup_render(1600, 1100); set_sun(0)
            cam("Cam_Anime_Exterior", (-1.6, -9.6, 1.35), (2.9, -0.6, 3.6), lens=22)
            out.append(render("anime_exterior"))
            # dollhouse cutaway like the reference (both floors visible)
            set_sun(70)
            hide(dollhouse_pred)
            c = HOUSE + Vector((0.2, 0, 2.6))
            cam("Cam_Anime_Dollhouse", c + DOLL_DIR * 40, c, ortho=14.0)
            out.append(render("anime_cutaway_dollhouse")); unhide()
            set_sun(0)
            d = Vector((1.0, -0.45, 1.25)).normalized()
            section_cut(4.15, 2.85, 5.2)
            cam("Cam_Anime_Cutaway2F", HOUSE + Vector((0, 0, 3.0)) + d * 40, HOUSE + Vector((0, 0, 3.0)), ortho=13.0)
            out.append(render("anime_cutaway_2F")); uncut()
            section_cut(1.75, -0.1, 2.75)
            cam("Cam_Anime_Cutaway1F", HOUSE + Vector((0, 0, 0.4)) + d * 40, HOUSE + Vector((0, 0, 0.4)), ortho=13.0)
            out.append(render("anime_cutaway_1F")); uncut()
            setup_render(1600, 1000)
            hide(ROOF); hide(lambda o: o.name.startswith("ScaleRef"))
            # same composition as the reference room sheet: window wall left, bookshelf + door ahead, oshiire right
            cam("Cam_Anime_NobitaRoom", (2.9, 0.3, 4.4), (2.6, 3.4, 3.85), lens=14)
            out.append(render("anime_nobita_room"))
        elif group == "elev":
            setup_render(1200, 800); sc.render.film_transparent = True
            hide(lambda o: o.name.startswith(NOT_SITE))
            for name, d, yaw, osc in (("elev_front", (0, -1, 0), 0, 16), ("elev_back", (0, 1, 0), 180, 16),
                                      ("elev_left", (-1, 0, 0), -90, 19.5), ("elev_right", (1, 0, 0), 90, 19.5)):
                set_sun(yaw + 25)
                cam("Cam_" + name, LOT + Vector(d) * 45, LOT, ortho=osc)
                out.append(render(name))
        elif group == "vignette":
            setup_render(1000, 780); sc.render.film_transparent = True; set_sun(0)
            V = [("vig_gate", ("Gate_", "Nameplate_Text", "BlockWall_Front"), (1.3, -9.0, 2.4), (3.9, -3.9, 0.8), 4.6),
                 ("vig_genkan", ("Door_Genkan", "Porch", "ExtWall_Front_1F", "BaseBand", "Eave_1F_Front", "Gutters", "Win_Front_2"),
                  (1.6, -6.0, 2.2), (3.9, 0.0, 1.5), 4.2),
                 ("vig_wall", ("BlockWall_Front", "BlockWall_Openwork", "Shrub_"), (4.4, -11.0, 2.6), (7.0, -3.9, 0.7), 4.8),
                 ("vig_bike", ("Carport_", "Bicycle_"), (14.5, -8.5, 5.5), (9.6, -2.1, 1.0), 5.2)]
            for name, keep, loc, tgt, scale in V:
                only(keep)
                cam("Cam_" + name, loc, tgt, ortho=scale)
                out.append(render(name)); unhide()
            hide(lambda o: o.name.startswith(NOT_SITE))
            d = Vector((-1.0, -1.25, 1.15)).normalized()
            cam("Cam_vig_iso", LOT + d * 60, LOT - Vector((0, 0, 1.0)), ortho=23)
            out.append(render("vig_iso"))
        elif group == "detail":
            setup_render(1000, 640); set_sun(0)
            hide(ROOF); hide(lambda o: o.name.startswith("ScaleRef"))
            D = [("det_desk", (2.1, 2.3, 4.35), (0.45, 1.2, 3.6), 20),
                 ("det_bookshelf", (2.3, 1.2, 4.2), (1.75, 3.4, 3.85), 20),
                 ("det_oshiire", (2.6, 1.5, 4.3), (5.2, 2.7, 3.8), 18),
                 ("det_futon", (3.0, 2.8, 4.6), (4.9, 1.0, 3.15), 20)]
            for name, loc, tgt, lens in D:
                cam("Cam_" + name, loc, tgt, lens=lens)
                out.append(render(name))
    finally:
        unhide(); uncut()
        watercolor_comp(False); restore_materials(); lumpy_leaves(False)
        sc.world = game_world; sc.render.film_transparent = False; sc.frame_set(0)
        bpy.data.collections["Render_Backdrop"].hide_viewport = True
    return out
