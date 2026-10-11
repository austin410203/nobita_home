# Background job: renders the open/close animation test (5 camera shots) and joins them into one MP4.
# Run:  blender -b NobitaHouse.blend --python scripts/render_anim.py
import bpy, os, math
from mathutils import Vector

S = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(S, "lib.py")
exec(open(os.path.join(S, "anime_render.py"), encoding="utf-8-sig").read())   # cam(), section_cut(), uncut()
ANIM = os.path.join(OUT, "anim"); os.makedirs(ANIM, exist_ok=True)
SHOT = 150

sc = bpy.context.scene
r = sc.render
try: r.engine = "BLENDER_EEVEE"
except TypeError: r.engine = "BLENDER_EEVEE_NEXT"
r.resolution_x, r.resolution_y, r.resolution_percentage = 1280, 720, 100
r.fps = 30
r.use_freestyle = False
try: sc.eevee.taa_render_samples = 16
except Exception: pass
sc.compositing_node_group = None
sc.world = bpy.data.worlds.get("World")
bd = bpy.data.collections.get("Render_Backdrop")
if bd:
    bd.hide_render = True
for o in bpy.data.objects:
    if o.name.startswith(("ScaleRef", "Collider_")):
        o.hide_render = True
r.use_stamp = True
for a in ("use_stamp_date", "use_stamp_time", "use_stamp_render_time", "use_stamp_camera", "use_stamp_lens",
          "use_stamp_scene", "use_stamp_filename", "use_stamp_memory", "use_stamp_hostname", "use_stamp_marker"):
    try: setattr(r, a, False)
    except Exception: pass
r.use_stamp_frame = True; r.use_stamp_note = True; r.stamp_font_size = 22

roof = [o for o in bpy.data.objects if "House_Roof" in {c.name for c in o.users_collection}]
HOUSE = Vector((2.8, 5.5, 0.0))
dd = Vector((1.0, -0.45, 1.25)).normalized()
doll = Vector((1.0, -0.45, 0.78)).normalized()
SHOTS = [
    ("Exterior",     lambda: cam("Cam_T_Ext", (1.0, -9.2, 1.7), (3.9, 0.0, 1.5), lens=22), None),
    ("Dollhouse",    lambda: cam("Cam_T_Doll", HOUSE + Vector((0.2, 0, 2.6)) + doll * 40, HOUSE + Vector((0.2, 0, 2.6)), ortho=14.0), "doll"),
    ("Cutaway_2F",   lambda: cam("Cam_T_2F", HOUSE + Vector((0, 0, 3.0)) + dd * 40, HOUSE + Vector((0, 0, 3.0)), ortho=13.0), (4.15, 2.85, 5.2)),
    ("NobitaRoom_A", lambda: cam("Cam_T_RA", (2.9, 0.3, 4.4), (2.6, 3.4, 3.85), lens=14), "roof"),
    ("NobitaRoom_B", lambda: cam("Cam_T_RB", (1.4, 3.0, 4.45), (5.0, 0.9, 3.6), lens=15), "roof"),
]
doll_hidden = []
def set_movie(path):
    s = r.image_settings
    try: s.media_type = "VIDEO"
    except Exception: pass
    s.file_format = "FFMPEG"
    r.ffmpeg.format = "MPEG4"; r.ffmpeg.codec = "H264"
    try: r.ffmpeg.constant_rate_factor = "HIGH"
    except Exception: pass
    r.filepath = path

def set_png(path):
    s = r.image_settings
    try: s.media_type = "IMAGE"
    except Exception: pass
    s.file_format = "PNG"
    r.filepath = path

clips = []
for i, (name, setcam, cut) in enumerate(SHOTS):
    setcam()
    if isinstance(cut, tuple):
        section_cut(*cut)
    elif cut == "roof":
        for o in roof: o.hide_render = True
    elif cut == "doll":
        for o in bpy.data.objects:
            if o.type == "MESH" and not o.hide_render and dollhouse_pred(o):
                o.hide_render = True; doll_hidden.append(o)
    r.stamp_note_text = "Open/Close test  -  %s" % name
    f0 = i * SHOT + 1
    # stills for checking: closed / everything open
    for tag, fr in (("closed", f0 + 4), ("open", f0 + 64)):
        sc.frame_set(fr); set_png(os.path.join(ANIM, "%s_%s.png" % (name, tag)))
        bpy.ops.render.render(write_still=True)
    sc.frame_start, sc.frame_end = f0, f0 + SHOT - 1
    path = os.path.join(ANIM, "%02d_%s.mp4" % (i + 1, name))
    set_movie(path)
    bpy.ops.render.render(animation=True)
    clips.append(path)
    uncut()
    for o in roof: o.hide_render = False
    for o in doll_hidden: o.hide_render = False
    doll_hidden.clear()
    print("SHOT DONE", name, flush=True)

print("ALL DONE", flush=True)
