# Final pass: UVs for every mesh, smoothing, bevels (rounded edges), export.
import bpy, math, os
exec(open(LIB).read())

SOFT = ("Futon", "Kakebuton", "Pillow", "Zabuton", "Sofa", "Cushion")
def bevel_for(ob):
    n = ob.name
    cols = {c.name for c in ob.users_collection}
    if n.startswith(("Collider_", "ScaleRef")) or "Glass" in n or n.startswith(("Roof_Tiles", "Eave_1F_Front_Tiles", "Eave_1F_Back_Tiles")):
        return 0, 0
    if any(s in n for s in SOFT):
        return 0.035, 4
    if n.startswith(("Leaves", "Shrub", "Wire", "Tree_")):
        return 0, 0
    if n.startswith("Tatami_"):
        return 0.006, 2
    if n.startswith(("Stairs_Treads",)):
        return 0.008, 3
    if "House_Furniture" in cols:
        return 0.01, 3
    if "House_Doors_Windows" in cols:
        return 0.005, 2
    if n.startswith(("BlockWall", "Gate_Pillars", "Path_Stones", "Porch", "Chimney", "Roof_Onigawara", "Roof_Ridge_Noshi",
                     "Genkan", "Carport_Posts", "Gable_Vent", "UtilityPole")):
        return 0.012, 3
    return 0, 0

n_bev = 0
for ob in bpy.data.objects:
    if ob.type != "MESH":
        continue
    if ob.data.users > 1:
        ob.data = ob.data.copy()
    uv_box(ob)
    w, s = bevel_for(ob)
    finish(ob, w, s)
    n_bev += w > 0

# nameplate text -> keep as text but give it a little bevel
for ob in bpy.data.objects:
    if ob.type == "FONT":
        ob.data.bevel_depth = 0.001

tris = 0
dg = bpy.context.evaluated_depsgraph_get()
for ob in bpy.data.objects:
    if ob.type == "MESH":
        e = ob.evaluated_get(dg); me = e.to_mesh()
        tris += sum(len(p.vertices) - 2 for p in me.polygons)
        e.to_mesh_clear()
print("bevelled objects:", n_bev, " total triangles:", tris)
