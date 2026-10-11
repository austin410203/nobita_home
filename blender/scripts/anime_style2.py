# Anime background-art style v2 (exec AFTER anime_render.py; overrides toon_of / setup_render / anime_world).
#  - flat colour fills (textures only faintly kept, structured patterns a bit more)
#  - crisp 2-tone cel shading, cool shadow, warm light, contact-shadow AO
#  - clean ink: thick outline + thin inner detail lines, no wobble
#  - anime window glass (sky gradient + diagonal highlight streaks), shaded cumulus sky
import bpy, math, os
import numpy as np

# how much of the original texture survives on top of its flat average colour
TEX_KEEP = {"tatami": 0.55, "block": 0.55, "tile_white": 0.6, "tile_blue": 0.6, "stone_tile": 0.5,
            "roof_tile": 0.3, "wood_floor": 0.5, "fabric_tatamiedge": 0.2, "wood_light": 0.3, "wood_dark": 0.3}
SHADOW_COL = (0.64, 0.66, 0.86, 1)
LIT_COL = (1.0, 0.985, 0.95, 1)
_avg = {}

def _img_avg(img):
    if img.name not in _avg:
        a = np.empty(len(img.pixels), np.float32); img.pixels.foreach_get(a)
        m = a.reshape(-1, 4)[:, :3].mean(0)
        _avg[img.name] = tuple(float(c) ** 2.2 for c in m) + (1.0,)
    return _avg[img.name]

def toon_of(m):
    t = bpy.data.materials.get(m.name + "_Anime")
    if t:
        return t
    t = bpy.data.materials.new(m.name + "_Anime"); t.use_nodes = True
    nt = t.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    b = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None) if m.use_nodes else None
    col = tuple(_inp(b, "Base Color").default_value) if b else tuple(m.diffuse_color)
    alpha = _inp(b, "Alpha").default_value if b else 1.0
    img = next((n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image
                and n.image.colorspace_settings.name != "Non-Color"), None) if m.use_nodes else None
    out = N("ShaderNodeOutputMaterial")
    em = N("ShaderNodeEmission")

    if m.name == "Glass":
        # anime window: sky-blue gradient + white diagonal highlight streaks, mostly opaque
        tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], sep.inputs[0])
        g = N("ShaderNodeValToRGB"); L(sep.outputs["Z"], g.inputs[0])
        g.color_ramp.elements[0].color = (0.55, 0.74, 0.92, 1); g.color_ramp.elements[1].color = (0.88, 0.95, 1.0, 1)
        wv = N("ShaderNodeTexWave"); wv.wave_type = "BANDS"; wv.bands_direction = "DIAGONAL"
        _inp(wv, "Scale").default_value = 1.6; _inp(wv, "Distortion").default_value = 0.0
        L(tc.outputs["Generated"], _inp(wv, "Vector"))
        st = N("ShaderNodeValToRGB"); st.color_ramp.interpolation = "CONSTANT"
        st.color_ramp.elements[0].color = (0, 0, 0, 1); st.color_ramp.elements[1].position = 0.86
        st.color_ramp.elements[1].color = (1, 1, 1, 1)
        L(wv.outputs["Fac"], st.inputs[0])
        mx = N("ShaderNodeMix"); mx.data_type = "RGBA"; L(st.outputs["Color"], mx.inputs[0])
        L(g.outputs["Color"], mx.inputs[6]); mx.inputs[7].default_value = (1, 1, 1, 1)
        L(mx.outputs[2], em.inputs["Color"])
        tr = N("ShaderNodeBsdfTransparent"); ms = N("ShaderNodeMixShader"); ms.inputs[0].default_value = 0.8
        L(tr.outputs[0], ms.inputs[1]); L(em.outputs[0], ms.inputs[2]); L(ms.outputs[0], out.inputs["Surface"])
        for a, v in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try: setattr(t, a, v)
            except Exception: pass
        return t

    # ---- base colour: flat fill, optionally faint texture ----
    if m.name == "Leaf":
        img = None; col = (0.27, 0.58, 0.20, 1)
    if m.name == "Grass":
        img = None; col = (0.30, 0.62, 0.20, 1)
    flat = N("ShaderNodeRGB")
    if img:
        flat.outputs[0].default_value = _img_avg(img)
        tex = N("ShaderNodeTexImage"); tex.image = img
        key = os.path.basename(img.filepath).replace("_col.jpg", "")
        mx = N("ShaderNodeMix"); mx.data_type = "RGBA"; mx.inputs[0].default_value = TEX_KEEP.get(key, 0.12)
        L(flat.outputs[0], mx.inputs[6]); L(tex.outputs["Color"], mx.inputs[7])
        base = mx.outputs[2]
    else:
        flat.outputs[0].default_value = col
        base = flat.outputs[0]
    hsv = N("ShaderNodeHueSaturation"); _inp(hsv, "Saturation").default_value = 1.12; _inp(hsv, "Value").default_value = 1.03
    L(base, _inp(hsv, "Color"))
    # ---- crisp two-tone cel shading ----
    diff = N("ShaderNodeBsdfDiffuse"); s2r = N("ShaderNodeShaderToRGB"); bw = N("ShaderNodeRGBToBW")
    L(diff.outputs[0], s2r.inputs[0]); L(s2r.outputs["Color"], bw.inputs[0])
    ramp = N("ShaderNodeValToRGB"); ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].color = SHADOW_COL
    ramp.color_ramp.elements[1].position = 0.45; ramp.color_ramp.elements[1].color = LIT_COL
    L(bw.outputs[0], ramp.inputs["Fac"])
    # contact shadows in corners (like painted occlusion)
    ao = N("ShaderNodeAmbientOcclusion"); _inp(ao, "Distance").default_value = 0.45
    aom = N("ShaderNodeMapRange"); _inp(aom, "To Min").default_value = 0.72
    L(ao.outputs["AO"], _inp(aom, "Value"))
    m1 = N("ShaderNodeMix"); m1.data_type = "RGBA"; m1.blend_type = "MULTIPLY"; m1.inputs[0].default_value = 1
    L(hsv.outputs["Color"], m1.inputs[6]); L(ramp.outputs["Color"], m1.inputs[7])
    m2 = N("ShaderNodeMix"); m2.data_type = "RGBA"; m2.blend_type = "MULTIPLY"; m2.inputs[0].default_value = 1
    L(m1.outputs[2], m2.inputs[6]); L(aom.outputs[0], m2.inputs[7])
    L(m2.outputs[2], em.inputs["Color"])
    if alpha < 1:
        tr = N("ShaderNodeBsdfTransparent"); ms = N("ShaderNodeMixShader"); ms.inputs[0].default_value = 0.4
        L(tr.outputs[0], ms.inputs[1]); L(em.outputs[0], ms.inputs[2]); L(ms.outputs[0], out.inputs["Surface"])
        for a, v in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try: setattr(t, a, v)
            except Exception: pass
    else:
        L(em.outputs[0], out.inputs["Surface"])
    return t

def anime_world():
    w = bpy.data.worlds.get("AnimeSky2") or bpy.data.worlds.new("AnimeSky2")
    w.use_nodes = True; nt = w.node_tree; nt.nodes.clear(); N = nt.nodes.new; L = nt.links.new
    tc = N("ShaderNodeTexCoord"); sep = N("ShaderNodeSeparateXYZ"); L(tc.outputs["Generated"], sep.inputs[0])
    mr = N("ShaderNodeMapRange"); _inp(mr, "From Max").default_value = 0.65; L(sep.outputs["Z"], _inp(mr, "Value"))
    grad = N("ShaderNodeValToRGB"); L(mr.outputs[0], grad.inputs[0])
    grad.color_ramp.elements[0].color = (0.82, 0.92, 1.0, 1); grad.color_ramp.elements[1].color = (0.20, 0.50, 0.93, 1)
    vm = N("ShaderNodeVectorMath"); vm.operation = "MULTIPLY"; vm.inputs[1].default_value = (1.0, 1.0, 3.0)
    L(tc.outputs["Generated"], vm.inputs[0])
    nz = N("ShaderNodeTexNoise"); _inp(nz, "Scale").default_value = 1.3
    _inp(nz, "Detail").default_value = 8; _inp(nz, "Roughness").default_value = 0.55
    L(vm.outputs[0], _inp(nz, "Vector"))
    mask = N("ShaderNodeMapRange"); _inp(mask, "From Min").default_value = 0.52; _inp(mask, "From Max").default_value = 0.555
    L(nz.outputs["Fac"], _inp(mask, "Value"))
    band = N("ShaderNodeMapRange"); _inp(band, "From Min").default_value = 0.0; _inp(band, "From Max").default_value = 0.1
    L(sep.outputs["Z"], _inp(band, "Value"))
    top = N("ShaderNodeMapRange"); _inp(top, "From Min").default_value = 0.55; _inp(top, "From Max").default_value = 0.4
    L(sep.outputs["Z"], _inp(top, "Value"))
    mul = N("ShaderNodeMath"); mul.operation = "MULTIPLY"; L(mask.outputs[0], mul.inputs[0]); L(band.outputs[0], mul.inputs[1])
    mul2 = mul
    # cloud body shading: dense cores white, thin/lower parts lavender-grey
    core = N("ShaderNodeMapRange"); _inp(core, "From Min").default_value = 0.53; _inp(core, "From Max").default_value = 0.63
    L(nz.outputs["Fac"], _inp(core, "Value"))
    ccol = N("ShaderNodeMix"); ccol.data_type = "RGBA"; L(core.outputs[0], ccol.inputs[0])
    ccol.inputs[6].default_value = (0.76, 0.80, 0.93, 1); ccol.inputs[7].default_value = (1, 1, 1, 1)
    sky = N("ShaderNodeMix"); sky.data_type = "RGBA"; L(mul2.outputs[0], sky.inputs[0])
    L(grad.outputs["Color"], sky.inputs[6]); L(ccol.outputs[2], sky.inputs[7])
    bgc = N("ShaderNodeBackground"); L(sky.outputs[2], bgc.inputs["Color"])
    bga = N("ShaderNodeBackground"); bga.inputs["Color"].default_value = (0.66, 0.72, 0.85, 1); bga.inputs["Strength"].default_value = 0.5
    lp = N("ShaderNodeLightPath"); ms = N("ShaderNodeMixShader")
    L(lp.outputs["Is Camera Ray"], ms.inputs[0]); L(bga.outputs[0], ms.inputs[1]); L(bgc.outputs[0], ms.inputs[2])
    o = N("ShaderNodeOutputWorld"); L(ms.outputs[0], o.inputs["Surface"])
    return w

def _style(name, color, thick, alpha=1.0):
    st = bpy.data.linestyles.get(name) or bpy.data.linestyles.new(name)
    st.color = color; st.thickness = thick; st.alpha = alpha
    st.chaining = "PLAIN"; st.use_same_object = True; st.caps = "ROUND"
    for m in list(st.thickness_modifiers): st.thickness_modifiers.remove(m)
    for m in list(st.alpha_modifiers): st.alpha_modifiers.remove(m)
    for m in list(st.geometry_modifiers):
        if m.type != "SAMPLING": st.geometry_modifiers.remove(m)
    tm = st.thickness_modifiers.new("Taper", "ALONG_STROKE"); tm.mapping = "CURVE"; tm.value_min, tm.value_max = 0.75, 1.05; tm.blend = "MULTIPLY"
    return st

def setup_render(w=1600, h=1100):
    r = sc.render
    try: r.engine = "BLENDER_EEVEE"
    except TypeError: r.engine = "BLENDER_EEVEE_NEXT"
    r.resolution_x, r.resolution_y, r.resolution_percentage = w, h, 100
    try: sc.eevee.taa_render_samples = 32
    except Exception: pass
    try: sc.view_settings.view_transform = "Standard"
    except TypeError: pass
    sc.view_settings.look = "None"; sc.view_settings.exposure = 0; sc.view_settings.gamma = 1
    r.use_freestyle = True; r.line_thickness_mode = "ABSOLUTE"; r.line_thickness = 1.0
    vl = bpy.context.view_layer; vl.use_freestyle = True
    fs = vl.freestyle_settings; fs.crease_angle = math.radians(160)
    for ls in list(fs.linesets): fs.linesets.remove(ls)
    noink = bpy.data.collections.get("_NoInk") or bpy.data.collections.new("_NoInk")
    for ob in bpy.data.objects:
        if ob.type == "MESH" and ("_Leaves" in ob.name or ob.name.startswith("Shrub")) and ob.name not in noink.objects:
            noink.objects.link(ob)
    o = fs.linesets.new("Outline")
    o.select_by_visibility = o.select_by_edge_types = True
    o.select_silhouette = o.select_external_contour = o.select_border = True; o.select_crease = False
    o.linestyle = _style("Ink_Outline", (0.24, 0.15, 0.11), 2.6)
    d = fs.linesets.new("Detail")
    d.select_by_visibility = d.select_by_edge_types = True
    d.select_crease = True; d.select_silhouette = d.select_border = d.select_external_contour = False
    d.select_by_collection = True; d.collection = noink; d.collection_negation = "EXCLUSIVE"
    d.linestyle = _style("Ink_Detail", (0.32, 0.22, 0.17), 1.25, 0.9)
    sun = bpy.data.objects.get("Sun")
    if sun:
        sun.data.energy = 3.2; sun.data.angle = math.radians(1.0)
        sun.rotation_euler = (math.radians(52), 0, math.radians(-38))
