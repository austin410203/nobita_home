# blender -b --factory-startup --python scripts/concat_clips.py   -> joins renders/anim/*.mp4 into one test video
import bpy, os, glob
S = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.abspath(os.path.join(S, "..", "renders"))
clips = sorted(glob.glob(os.path.join(OUT, "anim", "[0-9][0-9]_*.mp4")))
cs = bpy.context.scene
cs.render.resolution_x, cs.render.resolution_y, cs.render.resolution_percentage, cs.render.fps = 1280, 720, 100, 30
ed = cs.sequence_editor_create()
coll = ed.strips if hasattr(ed, "strips") else ed.sequences
f = 1
for i, p in enumerate(clips):
    st = coll.new_movie("clip%d" % i, p, 1, f)
    f += st.frame_final_duration
cs.frame_start, cs.frame_end = 1, f - 1
s = cs.render.image_settings
try: s.media_type = "VIDEO"
except Exception: pass
s.file_format = "FFMPEG"
cs.render.ffmpeg.format = "MPEG4"; cs.render.ffmpeg.codec = "H264"
try: cs.render.ffmpeg.constant_rate_factor = "HIGH"
except Exception: pass
cs.render.use_sequencer = True
cs.render.filepath = os.path.join(OUT, "NobitaHouse_OpenCloseTest.mp4")
bpy.ops.render.render(animation=True)
print("ALL DONE", len(clips), "clips,", f - 1, "frames ->", cs.render.filepath, flush=True)
