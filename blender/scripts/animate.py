# Open/close animation for every object tagged with custom prop "openable" (hinge / slide / drawer).
#  * Each object gets ONE clean action "<name>_Open" (frame 0 = closed -> frame L = open) for the game engine
#    (play forward to open, backwards to close).
#  * A test sequence is laid out with NLA strips: SHOTS cycles of open -> hold -> close.
import bpy, math
from mathutils import Vector

OPEN_LEN = {"hinge": 30, "slide": 24, "drawer": 20}
DELAY = {"hinge": 0, "slide": 10, "drawer": 35}     # stagger inside each cycle
SHOT = 150                                          # frames per test cycle
SHOT_NAMES = ["Exterior", "Dollhouse", "Cutaway_2F", "NobitaRoom_A", "NobitaRoom_B"]
SHEET_FRAME = 44                                    # doors/windows/fusuma open, drawers still closed

sc = bpy.context.scene

def openables():
    return [o for o in bpy.data.objects if o.get("openable")]

def build_open_actions():
    sc.frame_set(0)
    for ob in openables():
        kind = ob["openable"]
        ad = ob.animation_data_create()
        while ad.nla_tracks:
            ad.nla_tracks.remove(ad.nla_tracks[0])
        ad.action = None
        old = bpy.data.actions.get(ob.name + "_Open")
        if old:
            bpy.data.actions.remove(old)
        L = OPEN_LEN[kind]
        if kind == "hinge":
            z0 = ob["closed_rot_z"]
            ob.rotation_euler.z = z0
            ob.keyframe_insert("rotation_euler", index=2, frame=0)
            ob.rotation_euler.z = z0 + math.radians(ob["open_angle"])
            ob.keyframe_insert("rotation_euler", index=2, frame=L)
            ob.rotation_euler.z = z0
        else:
            p0 = Vector(ob.get("closed_loc", ob.location[:]))
            ob["closed_loc"] = tuple(p0)
            ob.location = p0
            ob.keyframe_insert("location", frame=0)
            ob.location = p0 + Vector(ob["open_offset"])
            ob.keyframe_insert("location", frame=L)
            ob.location = p0
        act = ad.action
        act.name = ob.name + "_Open"
        act.use_fake_user = True
        ob["anim_open_action"] = act.name
        ob["anim_open_frames"] = L

def build_test_nla(n_shots=len(SHOT_NAMES)):
    n = 0
    for ob in openables():
        ad = ob.animation_data
        act = bpy.data.actions[ob["anim_open_action"]]
        slot = getattr(ad, "action_slot", None)
        ad.action = None
        tr = ad.nla_tracks.new(); tr.name = "TestSequence"
        d = DELAY[ob["openable"]]
        for s in range(n_shots):
            for k, (t, rev) in enumerate(((s * SHOT + 10 + d, False), (s * SHOT + 85 + d, True))):
                st = tr.strips.new("%s_%d_%s" % (ob.name, s, "close" if rev else "open"), int(t), act)
                if slot is not None and hasattr(st, "action_slot") and st.action_slot is None:
                    try: st.action_slot = slot
                    except Exception: pass
                st.use_reverse = rev
                st.extrapolation = "HOLD" if (s == 0 and k == 0) else "HOLD_FORWARD"
                st.blend_in = st.blend_out = 0
        n += 1
    sc.frame_start, sc.frame_end = 1, SHOT * n_shots
    sc.render.fps = 30
    for i, nm in enumerate(SHOT_NAMES[:n_shots]):
        mk = sc.timeline_markers.get(nm) or sc.timeline_markers.new(nm, frame=i * SHOT + 1)
        mk.frame = i * SHOT + 1
    return n

def summary():
    from collections import Counter
    c = Counter(o["openable"] for o in openables())
    return dict(c)
