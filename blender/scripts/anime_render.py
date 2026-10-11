# Anime / manga style rendering (cel shading + Freestyle ink lines + painted sky).
# Game materials are swapped for toon copies only while rendering, then restored.
import bpy, math, os
from mathutils import Vector

sc = bpy.context.scene
OUT = os.path.abspath(os.path.join(os.path.dirname(LIB), "..", "renders"))
os.makedirs(OUT, exist_ok=True)

def _inp(node, ident):
    for s in node.inputs:
        if s.identifier == ident or s.name == ident:
            return s

SHADOW = [(0.0, (0.50, 0.48, 0.70)), (0.10, (0.70, 0.68, 0.86)), (0.42, (1.0, 1.0, 1.0))]

def toon_of(m):
    t = bpy.data.materials.get(m.name + "_Anime")
    if t:
        return t
    t = bpy.data.materials.new(m.name + "_Anime"); t.use_nodes = True
    nt = t.node_tree; nt.nodes.clear(); L = nt.links.new
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.use_nodes else None
    col = tuple(_inp(b, "Base Color").default_value) if b else tuple(m.diffuse_color)
    alpha = _inp(b, "Alpha").default_value if b else 1.0
    img = next((n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image
                and n.image.colorspace_settings.name != "Non-Color"), None) if m.use_nodes else None
    out = nt.nodes.new("ShaderNodeOutputMaterial"); out.location = (900, 0)
    diff = nt.nodes.new("ShaderNodeBsdfDiffuse"); diff.location = (-400, -200)
    s2r = nt.nodes.new("ShaderNodeShaderToRGB"); s2r.location = (-200, -200)
    ramp = nt.nodes.new("ShaderNodeValToRGB"); ramp.location = (0, -200)
    # watercolour: soft-ish bands whose edges are broken up by world-space noise
    ramp.color_ramp.interpolation = "LINEAR"
    els = ramp.color_ramp.elements
    deep, mid, lit = (*SHADOW[0][1], 1), (*SHADOW[1][1], 1), (*SHADOW[2][1], 1)
    els[0].position, els[0].color = 0.0, deep
    els[1].position, els[1].color = 0.46, lit
    for p, c in ((0.06, deep), (0.13, mid), (0.36, mid)):
        e = els.new(p); e.color = c
    geo = nt.nodes.new("ShaderNodeNewGeometry"); geo.location = (-800, -500)
    nz1 = nt.nodes.new("ShaderNodeTexNoise"); nz1.location = (-600, -500)
    _inp(nz1, "Scale").default_value = 1.1; _inp(nz1, "Detail").default_value = 4; _inp(nz1, "Roughness").default_value = 0.6
    L(geo.outputs["Position"], _inp(nz1, "Vector"))
    bw = nt.nodes.new("ShaderNodeRGBToBW")
    L(diff.outputs[0], s2r.inputs[0]); L(s2r.outputs["Color"], bw.inputs[0])
    sub = nt.nodes.new("ShaderNodeMath"); sub.operation = "SUBTRACT"; sub.inputs[1].default_value = 0.5
    L(nz1.outputs["Fac"], sub.inputs[0])
    mad = nt.nodes.new("ShaderNodeMath"); mad.operation = "MULTIPLY_ADD"; mad.inputs[1].default_value = 0.32
    L(sub.outputs[0], mad.inputs[0]); L(bw.outputs[0], mad.inputs[2])
    L(mad.outputs[0], ramp.inputs["Fac"])
    # pigment mottling (darker pools / lighter washes)
    nz2 = nt.nodes.new("ShaderNodeTexNoise"); nz2.location = (-600, -800)
    _inp(nz2, "Scale").default_value = 4.0; _inp(nz2, "Detail").default_value = 3
    L(geo.outputs["Position"], _inp(nz2, "Vector"))
    pig = nt.nodes.new("ShaderNodeMapRange")
    _inp(pig, "From Min").default_value = 0.3; _inp(pig, "From Max").default_value = 0.7
    _inp(pig, "To Min").default_value = 0.88; _inp(pig, "To Max").default_value = 1.06
    L(nz2.outputs["Fac"], _inp(pig, "Value"))
    # paper grain in screen space
    tcw = nt.nodes.new("ShaderNodeTexCoord")
    nz3 = nt.nodes.new("ShaderNodeTexNoise"); _inp(nz3, "Scale").default_value = 380; _inp(nz3, "Detail").default_value = 1
    L(tcw.outputs["Window"], _inp(nz3, "Vector"))
    pap = nt.nodes.new("ShaderNodeMapRange")
    _inp(pap, "From Min").default_value = 0.3; _inp(pap, "From Max").default_value = 0.7
    _inp(pap, "To Min").default_value = 0.93; _inp(pap, "To Max").default_value = 1.0
    L(nz3.outputs["Fac"], _inp(pap, "Value"))
    if m.name in ("Leaf",):
        img = None; col = (0.30, 0.60, 0.22, 1)
    if img:
        tex = nt.nodes.new("ShaderNodeTexImage"); tex.image = img; tex.location = (-400, 200)
        base = tex.outputs["Color"]
    else:
        rgb = nt.nodes.new("ShaderNodeRGB"); rgb.outputs[0].default_value = col; rgb.location = (-400, 200)
        base = rgb.outputs[0]
    hsv = nt.nodes.new("ShaderNodeHueSaturation"); hsv.location = (-150, 200)
    _inp(hsv, "Saturation").default_value = 1.18; _inp(hsv, "Value").default_value = 1.04
    L(base, _inp(hsv, "Color"))
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"; mix.blend_type = "MULTIPLY"; mix.location = (250, 100)
    mix.inputs[0].default_value = 1.0
    L(hsv.outputs["Color"], mix.inputs[6]); L(ramp.outputs["Color"], mix.inputs[7])
    last = mix.outputs[2]
    for fac_out in (pig.outputs[0], pap.outputs[0]):
        mm = nt.nodes.new("ShaderNodeMix"); mm.data_type = "RGBA"; mm.blend_type = "MULTIPLY"
        mm.inputs[0].default_value = 1.0
        L(last, mm.inputs[6]); L(fac_out, mm.inputs[7]); last = mm.outputs[2]
    em = nt.nodes.new("ShaderNodeEmission"); em.location = (500, 100)
    L(last, em.inputs["Color"])
    if alpha < 1:
        tr = nt.nodes.new("ShaderNodeBsdfTransparent"); ms = nt.nodes.new("ShaderNodeMixShader")
        ms.inputs[0].default_value = 0.35
        L(tr.outputs[0], ms.inputs[1]); L(em.outputs[0], ms.inputs[2]); L(ms.outputs[0], out.inputs["Surface"])
        for a, v in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try: setattr(t, a, v)
            except Exception: pass
    else:
        L(em.outputs[0], out.inputs["Surface"])
    return t

_saved = []
def swap_to_toon():
    _saved.clear()
    for m in [m for m in bpy.data.materials if m.name.endswith("_Anime") and m.users == 0]:
        bpy.data.materials.remove(m)   # rebuild toon copies so script changes apply
    for ob in bpy.data.objects:
        if ob.type in ("MESH", "FONT"):
            for i, sl in enumerate(ob.material_slots):
                if sl.material and not sl.material.name.endswith("_Anime"):
                    _saved.append((ob, i, sl.material))
                    sl.material = toon_of(sl.material)

def restore_materials():
    for ob, i, m in _saved:
        ob.material_slots[i].material = m
    _saved.clear()

def anime_world():
    w = bpy.data.worlds.get("AnimeSky") or bpy.data.worlds.new("AnimeSky")
    w.use_nodes = True; nt = w.node_tree; nt.nodes.clear(); L = nt.links.new
    tc = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], sep.inputs[0])
    mr = nt.nodes.new("ShaderNodeMapRange"); _inp(mr, "From Min").default_value = 0.0; _inp(mr, "From Max").default_value = 0.7
    L(sep.outputs["Z"], _inp(mr, "Value"))
    grad = nt.nodes.new("ShaderNodeValToRGB")
    grad.color_ramp.elements[0].color = (0.80, 0.90, 0.98, 1); grad.color_ramp.elements[1].color = (0.22, 0.50, 0.90, 1)
    L(mr.outputs[0], grad.inputs[0])
    # flattened cumulus clouds
    vm = nt.nodes.new("ShaderNodeVectorMath"); vm.operation = "MULTIPLY"; vm.inputs[1].default_value = (1.0, 1.0, 2.6)
    L(tc.outputs["Generated"], vm.inputs[0])
    nz = nt.nodes.new("ShaderNodeTexNoise"); _inp(nz, "Scale").default_value = 1.3
    _inp(nz, "Detail").default_value = 7; _inp(nz, "Roughness").default_value = 0.58
    L(vm.outputs[0], _inp(nz, "Vector"))
    cr = nt.nodes.new("ShaderNodeValToRGB"); cr.color_ramp.interpolation = "EASE"
    cr.color_ramp.elements[0].position = 0.52; cr.color_ramp.elements[1].position = 0.58
    L(nz.outputs["Fac"], cr.inputs[0])
    band = nt.nodes.new("ShaderNodeMapRange"); _inp(band, "From Min").default_value = 0.0; _inp(band, "From Max").default_value = 0.12
    L(sep.outputs["Z"], _inp(band, "Value"))
    mul = nt.nodes.new("ShaderNodeMath"); mul.operation = "MULTIPLY"
    L(cr.outputs["Color"], mul.inputs[0]); L(band.outputs[0], mul.inputs[1])
    mix = nt.nodes.new("ShaderNodeMix"); mix.data_type = "RGBA"
    L(mul.outputs[0], mix.inputs[0]); L(grad.outputs["Color"], mix.inputs[6]); mix.inputs[7].default_value = (0.99, 0.99, 1.0, 1)
    bg_cam = nt.nodes.new("ShaderNodeBackground"); L(mix.outputs[2], bg_cam.inputs["Color"])
    bg_amb = nt.nodes.new("ShaderNodeBackground"); bg_amb.inputs["Color"].default_value = (0.62, 0.68, 0.80, 1)
    bg_amb.inputs["Strength"].default_value = 0.5
    lp = nt.nodes.new("ShaderNodeLightPath"); msh = nt.nodes.new("ShaderNodeMixShader")
    L(lp.outputs["Is Camera Ray"], msh.inputs[0]); L(bg_amb.outputs[0], msh.inputs[1]); L(bg_cam.outputs[0], msh.inputs[2])
    o = nt.nodes.new("ShaderNodeOutputWorld"); L(msh.outputs[0], o.inputs["Surface"])
    return w

def setup_render(w=1600, h=1100):
    r = sc.render
    try: r.engine = "BLENDER_EEVEE"
    except TypeError: r.engine = "BLENDER_EEVEE_NEXT"
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    try: sc.eevee.taa_render_samples = 32
    except Exception: pass
    for vt in ("Standard",):
        try: sc.view_settings.view_transform = vt
        except TypeError: pass
    sc.view_settings.look = "None"
    sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    # ink lines
    r.use_freestyle = True; r.line_thickness_mode = "ABSOLUTE"; r.line_thickness = 1.0
    vl = bpy.context.view_layer; vl.use_freestyle = True
    fs = vl.freestyle_settings; fs.crease_angle = math.radians(160)
    ls = fs.linesets[0] if fs.linesets else fs.linesets.new("Ink")
    ls.select_by_visibility = True; ls.select_by_edge_types = True
    ls.select_silhouette = ls.select_border = ls.select_crease = True
    ls.select_external_contour = True
    # trees/shrubs: outline only (no inner crease lines)
    noink = bpy.data.collections.get("_NoInk") or bpy.data.collections.new("_NoInk")
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ("_Leaves" in ob.name or ob.name.startswith("Shrub")) and ob.name not in noink.objects:
            noink.objects.link(ob)
    ls.select_by_collection = True; ls.collection = noink; ls.collection_negation = "EXCLUSIVE"
    ls2 = fs.linesets.get("InkTrees") or fs.linesets.new("InkTrees")
    ls2.select_by_visibility = True; ls2.select_by_edge_types = True
    ls2.select_silhouette = ls2.select_external_contour = True
    ls2.select_crease = ls2.select_border = False
    ls2.select_by_collection = True; ls2.collection = noink; ls2.collection_negation = "INCLUSIVE"
    for l in (ls, ls2):
        st = l.linestyle
        st.color = (0.12, 0.08, 0.07); st.thickness = 2.2; st.alpha = 1.0
    st = ls.linestyle
    st.color = (0.12, 0.08, 0.07); st.thickness = 2.2; st.alpha = 1.0
    st.chaining = "PLAIN"; st.use_same_object = True
    for l in (ls, ls2):
        hand_drawn(l.linestyle)

def hand_drawn(st):
    """Sketchy pen: tapered, wobbly strokes that overshoot corners, with uneven pressure."""
    st.chaining = "SKETCHY"; st.rounds = 2; st.use_same_object = True
    st.caps = "ROUND"
    for m in list(st.thickness_modifiers): st.thickness_modifiers.remove(m)
    for m in list(st.geometry_modifiers):
        if m.type != "SAMPLING": st.geometry_modifiers.remove(m)
    if not st.geometry_modifiers:
        st.geometry_modifiers.new("Sampling", "SAMPLING")
    st.geometry_modifiers[0].sampling = 2.0
    bb = st.geometry_modifiers.new("Overshoot", "BACKBONE_STRETCHER"); bb.backbone_length = 3.5
    p1 = st.geometry_modifiers.new("Wobble", "PERLIN_NOISE_1D"); p1.frequency = 30; p1.amplitude = 0.8; p1.octaves = 2
    p2 = st.geometry_modifiers.new("Tremor", "PERLIN_NOISE_1D"); p2.frequency = 4; p2.amplitude = 0.6; p2.seed = 7
    tm = st.thickness_modifiers.new("Taper", "ALONG_STROKE"); tm.mapping = "CURVE"; tm.value_min, tm.value_max = 0.45, 1.35
    tn = st.thickness_modifiers.new("Pressure", "NOISE"); tn.amplitude = 0.9; tn.period = 30; tn.blend = "ADD"
    am = st.alpha_modifiers.get("Ink") or st.alpha_modifiers.new("Ink", "NOISE")
    am.amplitude = 0.15; am.period = 40

def watercolor_comp(on=True, size=5):
    """Painterly post-process (anisotropic Kuwahara) to merge brush-like colour areas."""
    if not on:
        sc.compositing_node_group = None; return
    ng = bpy.data.node_groups.get("WatercolorComp")
    if ng is None:
        ng = bpy.data.node_groups.new("WatercolorComp", "CompositorNodeTree")
        ng.interface.new_socket("Image", in_out="OUTPUT", socket_type="NodeSocketColor")
        rl = ng.nodes.new("CompositorNodeRLayers")
        kw = ng.nodes.new("CompositorNodeKuwahara")
        out = ng.nodes.new("NodeGroupOutput")
        ng.links.new(rl.outputs["Image"], kw.inputs[0]); ng.links.new(kw.outputs[0], out.inputs[0])
    kw = next(n for n in ng.nodes if n.bl_idname == "CompositorNodeKuwahara")
    for s in kw.inputs:
        if s.name == "Size": s.default_value = size
        if s.name in ("Uniformity",): s.default_value = 4
        if s.name in ("Sharpness",): s.default_value = 0.5
        if s.name in ("Eccentricity",): s.default_value = 1.0
        if s.name in ("High Precision",): s.default_value = False
    try: kw.variation = "ANISOTROPIC"
    except Exception: pass
    for s in kw.inputs:
        if s.name == "Type":
            try: s.default_value = "Anisotropic"
            except Exception: pass
    sc.compositing_node_group = ng
    sun = bpy.data.objects.get("Sun")
    if sun:
        sun.data.energy = 3.2; sun.data.angle = math.radians(1.0)
        sun.rotation_euler = (math.radians(52), 0, math.radians(-38))

def cam(name, loc, tgt, lens=24, ortho=None):
    c = bpy.data.objects.get(name)
    if not c:
        c = bpy.data.objects.new(name, bpy.data.cameras.new(name)); sc.collection.objects.link(c)
    c.location = loc; c.data.lens = lens; c.data.clip_end = 300
    c.rotation_euler = (Vector(tgt) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    if ortho:
        c.data.type = "ORTHO"; c.data.ortho_scale = ortho
    else:
        c.data.type = "PERSP"
    sc.camera = c
    return c

def render(name):
    sc.render.filepath = os.path.join(OUT, name + ".png")
    bpy.ops.render.render(write_still=True)
    return sc.render.filepath

# ---- section cut helpers for cutaway views ----
_cut = []
def section_cut(z_cut, zmin, hide_above, skip_cols=()):
    """Boolean-cut walls/doors between zmin and z_cut; hide everything that starts above hide_above."""
    box = bpy.data.objects.get("_SectionCutter")
    if not box:
        me = bpy.data.meshes.new("_SectionCutter")
        import bmesh
        bm = bmesh.new(); bmesh.ops.create_cube(bm, size=1); bm.to_mesh(me); bm.free()
        box = bpy.data.objects.new("_SectionCutter", me); sc.collection.objects.link(box)
    box.scale = (60, 60, 20); box.location = (4, 4, z_cut + 10)
    box.hide_render = True; box.hide_viewport = True
    for ob in bpy.data.objects:
        if ob.type not in ("MESH", "FONT") or ob is box or ob.hide_render:
            continue
        bb = [ob.matrix_world @ Vector(c) for c in ob.bound_box]
        lo, hi = min(v.z for v in bb), max(v.z for v in bb)
        cols = {c.name for c in ob.users_collection}
        if lo >= min(hide_above, z_cut) - 1e-3 or ob.name.startswith("BD_") or "House_Roof" in cols or ob.name.startswith(("Wire", "UtilityPole", "Tree_")):
            ob.hide_render = True; _cut.append(("hide", ob))
        elif ob.type == "MESH" and lo >= zmin - 0.15 and hi > z_cut and not (cols & set(skip_cols)) and lo < z_cut:
            md = ob.modifiers.new("_Section", "BOOLEAN"); md.operation = "DIFFERENCE"; md.object = box
            try: md.solver = "EXACT"; md.use_self = True
            except Exception: pass
            _cut.append(("mod", ob))
    for n in [o.name for o in bpy.data.objects if o.name.startswith("ScaleRef") or o.name.startswith("Collider_")]:
        o = bpy.data.objects[n]
        if not o.hide_render:
            o.hide_render = True; _cut.append(("hide", o))

def uncut():
    for kind, ob in _cut:
        if kind == "hide": ob.hide_render = False
        else:
            md = ob.modifiers.get("_Section")
            if md: ob.modifiers.remove(md)
    _cut.clear()

# ---- render-only backdrop: neighbourhood houses, trees, far ground (not exported to the game) ----
def backdrop():
    exec(open(LIB).read(), globals())
    init_materials()
    mat("NeighborWall", (0.86, 0.84, 0.80), 0.9, tex="plaster_int", tile=2.0)
    mat("NeighborWall2", (0.80, 0.86, 0.90), 0.9, tex="plaster_int", tile=2.0)
    mat("NeighborRoof", (0.35, 0.42, 0.55), 0.5)
    mat("NeighborRoof2", (0.55, 0.30, 0.22), 0.5)
    C = coll("Render_Backdrop")
    if C.objects:
        return C
    mesh_obj("BD_FarGround", [(-90, -60, -0.2, 100, 90, -0.16)], "Concrete", C)
    mesh_obj("BD_Lawn", [(-12, -3.99, -0.15, -2.05, 27, -0.02), (11.05, -3.99, -0.15, 30, 27, -0.02), (-2.05, 13.05, -0.15, 11.05, 27, -0.02)], "Grass", C)
    def house(n, x1, y1, x2, y2, h, wm, rm, ridge_x=True):
        mesh_obj(n + "_Body", [(x1, y1, 0, x2, y2, h)], wm, C)
        o = 0.5
        if ridge_x:
            ym = (y1 + y2) / 2; rh = h + (y2 - y1) * 0.35
            slab_quad(n + "_RoofA", [(x1 - o, y1 - o, h - 0.2), (x2 + o, y1 - o, h - 0.2), (x2 + o, ym, rh), (x1 - o, ym, rh)], 0.12, rm, C)
            slab_quad(n + "_RoofB", [(x1 - o, ym, rh), (x2 + o, ym, rh), (x2 + o, y2 + o, h - 0.2), (x1 - o, y2 + o, h - 0.2)], 0.12, rm, C)
            poly_prism(n + "_GableA", [(y1, h), (y2, h), (ym, rh - 0.1)], "y", x1, x1 + 0.1, wm, C)
            poly_prism(n + "_GableB", [(y1, h), (y2, h), (ym, rh - 0.1)], "y", x2 - 0.1, x2, wm, C)
        else:
            xm = (x1 + x2) / 2; rh = h + (x2 - x1) * 0.35
            slab_quad(n + "_RoofA", [(x1 - o, y1 - o, h - 0.2), (xm, y1 - o, rh), (xm, y2 + o, rh), (x1 - o, y2 + o, h - 0.2)], 0.12, rm, C)
            slab_quad(n + "_RoofB", [(xm, y1 - o, rh), (x2 + o, y1 - o, h - 0.2), (x2 + o, y2 + o, h - 0.2), (xm, y2 + o, rh)], 0.12, rm, C)
            poly_prism(n + "_GableA", [(x1, h), (x2, h), (xm, rh - 0.1)], "x", y1, y1 + 0.1, wm, C)
            poly_prism(n + "_GableB", [(x1, h), (x2, h), (xm, rh - 0.1)], "x", y2 - 0.1, y2, wm, C)
        # a few windows
        for k in range(2):
            for fl in (1.2, 4.0):
                xs = x1 + (x2 - x1) * (0.25 + 0.4 * k)
                mesh_obj("%s_Win%d_%.0f" % (n, k, fl), [(xs - 0.6, y1 - 0.03, fl, xs + 0.6, y1, fl + 1.1)], "Glass", C)
    house("BD_HouseL", -11.5, 1.0, -4.5, 9.0, 5.6, "NeighborWall", "NeighborRoof", ridge_x=False)
    house("BD_HouseR", 13.0, 0.0, 20.0, 8.0, 5.8, "NeighborWall2", "NeighborRoof", ridge_x=True)
    house("BD_HouseB1", -1.0, 15.5, 7.0, 22.5, 6.0, "NeighborWall", "NeighborRoof2")
    house("BD_HouseB2", 9.0, 16.0, 17.0, 23.0, 5.6, "NeighborWall2", "NeighborRoof", ridge_x=False)
    house("BD_HouseFar", -20.0, 6.0, -13.5, 13.0, 8.5, "NeighborWall2", "NeighborRoof")
    import random
    random.seed(11)
    for i, (x, y, h) in enumerate([(-3.5, 14.5, 6), (12.5, 13.5, 5.5), (-14, 1, 6.5), (22, 3, 7), (5, 24, 8), (-8, 18, 7), (19, 14, 6)]):
        cyl("BD_Tree%d_Trunk" % i, x, y, 0, h * 0.5, 0.18, "Trunk", C, seg=12)
        for k in range(8):
            a = random.uniform(0, 6.28); d = random.uniform(0.3, 1.2)
            sphere("BD_Tree%d_Leaves%d" % (i, k), x + d * math.cos(a), y + d * math.sin(a), h * 0.6 + random.uniform(0, h * 0.35),
                   random.uniform(0.9, 1.5), "Leaf", C, sz=0.8)
    # curb & sidewalk strip on the street side
    mesh_obj("BD_Curb", [(-40, -4.3, -0.03, 60, -4.0, 0.08)], "Concrete", C)
    mesh_obj("BD_FarStreet", [(-40, -12, -0.15, -10, -4.3, -0.03), (20, -12, -0.15, 60, -4.3, -0.03)], "Asphalt", C)
    for ob in C.objects:
        if ob.type == "MESH":
            uv_box(ob); finish(ob)
    return C

_disp = []
def lumpy_leaves(on=True):
    """Displace leaf spheres into cloud-like anime clumps (render only)."""
    tex = bpy.data.textures.get("_LeafClouds") or bpy.data.textures.new("_LeafClouds", "CLOUDS")
    tex.noise_scale = 0.35; tex.noise_depth = 2
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ("_Leaves" in ob.name or ob.name.startswith("Shrub")):
            if on and "_Lumps" not in ob.modifiers:
                md = ob.modifiers.new("_Lumps", "DISPLACE"); md.texture = tex; md.strength = 0.35; md.mid_level = 0.5
                md.texture_coords = "GLOBAL"
            elif not on and "_Lumps" in ob.modifiers:
                ob.modifiers.remove(ob.modifiers["_Lumps"])

# ---- "dollhouse" cutaway like the reference sheet: east wall, east roof half and 2F ceiling removed ----
DOLL_PREFIX = ("ExtWall_East", "Win_East", "Roof_Deck_East", "Roof_Tiles_East", "Roof_Barge_E", "Eave_1F_East",
               "Slab_2F_Ceiling", "Downpipe_East", "Gutters", "Fascia_Front_E", "Tree_East", "Carport_", "Bicycle_",
               "BlockWall_East", "Shrub_8", "Wire", "UtilityPole", "BD_", "ScaleRef", "Collider_", "Antenna", "Chimney", "Roof_Onigawara", "Eave_1F_Flashing")
def dollhouse_pred(o):
    return o.name.startswith(DOLL_PREFIX) or (o.name.endswith("CeilingLamp") is False and o.name.startswith("Roof_Ridge"))
