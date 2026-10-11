# Background job: renders every anime-sheet panel.  blender -b NobitaHouse.blend --python scripts/render_sheet_bg.py
import os
S = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(S, "lib.py")
exec(open(os.path.join(S, "anime_sheet.py"), encoding="utf-8-sig").read())
for g in ("main", "elev", "vignette", "detail"):
    run(g)
    print("GROUP DONE", g, flush=True)
print("ALL DONE", flush=True)
