# Web / three.js export of the manga-style house:
#   * bakes "flat colour + faint pattern" toon textures (same look as anime_style2) into textures_toon/
#   * swaps every material for a simple glTF-friendly toon material (base colour only, no normal maps)
#   * writes Chinese label / description custom props (-> glTF extras -> three.js userData)
#   * exports a Draco-compressed GLB with all "<name>_Open" animations
import bpy, os, json
import numpy as np

SD = os.path.dirname(LIB)
TEXDIR = os.path.abspath(os.path.join(SD, "..", "textures"))
TOONDIR = os.path.abspath(os.path.join(SD, "..", "textures_toon"))
os.makedirs(TOONDIR, exist_ok=True)

TEX_KEEP = {"tatami": 0.55, "block": 0.55, "tile_white": 0.6, "tile_blue": 0.6, "stone_tile": 0.5,
            "roof_tile": 0.3, "wood_floor": 0.5, "fabric_tatamiedge": 0.2, "wood_light": 0.3, "wood_dark": 0.3}
FLAT = {"Leaf": (0.27, 0.58, 0.20), "Grass": (0.30, 0.62, 0.20)}

def bake_toon_texture(key):
    out = os.path.join(TOONDIR, key + ".jpg")
    img = bpy.data.images.load(os.path.join(TEXDIR, key + "_col.jpg"), check_existing=False)
    n = img.size[0]
    a = np.empty(n * n * 4, np.float32); img.pixels.foreach_get(a); a = a.reshape(n, n, 4)
    rgb = a[..., :3]
    avg = rgb.reshape(-1, 3).mean(0)
    keep = TEX_KEEP.get(key, 0.12)
    t = avg + (rgb - avg) * keep
    lum = t.mean(-1, keepdims=True)
    t = np.clip((lum + (t - lum) * 1.12) * 1.03, 0, 1)
    a[..., :3] = t
    img.pixels.foreach_set(a.ravel())
    size = 1024 if key in TEX_KEEP else 128            # flat textures need almost no resolution
    if size != n:
        img.scale(size, size)
    img.filepath_raw = out; img.file_format = "JPEG"
    try: img.save(filepath=out, quality=88)
    except TypeError: img.save()
    bpy.data.images.remove(img)
    return out

def _inp(node, ident):
    for s in node.inputs:
        if s.identifier == ident or s.name == ident:
            return s

def toon_material(m):
    t = bpy.data.materials.get(m.name + "_Toon")
    if t:
        return t
    t = bpy.data.materials.new(m.name + "_Toon"); t.use_nodes = True
    nt = t.node_tree; b = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    src = next((n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED"), None)
    col = tuple(_inp(src, "Base Color").default_value) if src else (0.8, 0.8, 0.8, 1)
    alpha = _inp(src, "Alpha").default_value if src else 1.0
    img = next((n.image for n in m.node_tree.nodes if n.type == "TEX_IMAGE" and n.image
                and n.image.colorspace_settings.name != "Non-Color"), None)
    _inp(b, "Roughness").default_value = 1.0
    _inp(b, "Metallic").default_value = 0.0
    if m.name in FLAT:
        _inp(b, "Base Color").default_value = (*FLAT[m.name], 1)
    elif img:
        key = os.path.basename(img.filepath).replace("_col.jpg", "")
        path = os.path.join(TOONDIR, key + ".jpg")
        if not os.path.exists(path):
            bake_toon_texture(key)
        tx = nt.nodes.new("ShaderNodeTexImage"); tx.image = bpy.data.images.load(path, check_existing=True)
        nt.links.new(tx.outputs["Color"], _inp(b, "Base Color"))
    else:
        _inp(b, "Base Color").default_value = col
    if alpha < 1:
        _inp(b, "Alpha").default_value = 0.45
        for a_, v in (("surface_render_method", "BLENDED"), ("blend_method", "BLEND")):
            try: setattr(t, a_, v)
            except Exception: pass
    t["toon_outline"] = 0 if (alpha < 1 or m.name in ("Leaf",)) else 1
    return t

# ---------------- labels (zh-TW name + description) ----------------
LABELS = [
    # openables
    ("Door_Genkan", "玄關大門", "木製雙開門，從這裡進出野比家。按 E 開關。"),
    ("Door_1F_Toilet", "一樓廁所門", "通往一樓廁所兼洗手間。"),
    ("Door_1F_Living", "客廳門", "從玄關走廊進入客廳的門。"),
    ("Door_2F_Nobita", "大雄房間的門", "大雄的房間就在門後，常常有人哭著衝進來。"),
    ("Door_2F_Closet", "走廊收納櫃門", "二樓走廊的收納空間。"),
    ("Door_2F_Toilet", "二樓廁所門", "二樓的廁所。"),
    ("Door_2F_Storage", "儲藏室拉門", "堆放雜物的儲藏室。"),
    ("Door_2F_Parents", "爸媽房間的門", "野比爸爸和媽媽的寢室。"),
    ("Gate_Side", "側門", "通往駐輪場的小鐵門。"),
    ("Gate_Nameplate", "門牌", "寫著「野比」的門牌。"),
    ("Gate_Mailbox", "信箱", "野比家的信箱。"),
    ("Gate_Pillars", "門柱", "大門兩側的門柱。"),
    ("Gate_", "大門鐵門", "野比家的鐵製雙開大門。"),
    ("Nobita_Oshiire_Fusuma_Front", "壁櫥紙拉門", "拉開就能看到哆啦A夢睡覺的地方。"),
    ("Nobita_Desk_Pedestal_Drawer", "書桌抽屜", "大雄書桌的抽屜……時光機的入口就在這裡！"),
    ("Nobita_Desk_CenterDrawer_Drawer", "書桌中央抽屜", "時光機的入口！拉開看看。"),
    ("Nobita_Chest_Drawer", "大雄的五斗櫃抽屜", "放衣服和漫畫的抽屜。"),
    ("Parents_Dresser_Drawer", "梳妝台抽屜", "媽媽的梳妝台。"),
    ("Living_TVStand_Drawer", "電視櫃抽屜", "放遙控器和雜物。"),
    ("Living_Sideboard_Drawer", "餐具櫃抽屜", "樓梯旁的小櫃子。"),
    ("Kitchen_Cabinet_Drawer", "廚房收納抽屜", "放鍋碗瓢盆的收納櫃。"),
    ("Win_", "推拉窗", "日式雙軌推拉窗，按 E 打開或關上。"),
    # furniture / fixtures
    ("Nobita_DeskLamp", "檯燈", "書桌上的檯燈。"),
    ("Nobita_Desk", "大雄的書桌", "大雄寫功課（和睡午覺）的地方。"),
    ("Nobita_Chair", "書桌椅", "大雄的藍色書桌椅。"),
    ("Nobita_Bookshelf", "書櫃", "塞滿漫畫的書櫃。"),
    ("Nobita_Bed", "大雄的床", "大雄最愛的地方——睡午覺！"),
    ("Nobita_Futon", "被褥", "藍色的被褥。"),
    ("Nobita_Oshiire", "壁櫥", "哆啦A夢的臥室，上層鋪著被褥。"),
    ("Oshiire_Doraemon_Futon", "哆啦A夢的被褥", "哆啦A夢每晚睡在壁櫥上層。"),
    ("Nobita_Chest", "五斗櫃", "大雄的衣物收納櫃。"),
    ("Nobita_Zabuton", "坐墊", "榻榻米上的藍色坐墊。"),
    ("Nobita_Poster", "哆啦A夢海報", "貼在牆上的海報。"),
    ("Nobita_Calendar", "月曆", "記著考試日期（大雄大概沒在看）。"),
    ("Nobita_Globe", "地球儀", "書櫃上的地球儀。"),
    ("Nobita_WasteBasket", "垃圾桶", "裡面可能有零分的考卷……"),
    ("Nobita_Ball", "棒球", "和胖虎他們打棒球用的球。"),
    ("Nobita_Comics", "漫畫", "散落在地上的漫畫。"),
    ("Nobita_Curtains", "窗簾", "綠色的窗簾。"),
    ("Living_Sofa", "沙發", "客廳的綠色沙發，爸爸看電視的地方。"),
    ("Living_TVStand", "電視櫃", "放電視的矮櫃。"),
    ("Living_TV", "電視", "全家一起看電視。"),
    ("Living_CoffeeTable", "茶几", "客廳的茶几。"),
    ("Living_Rug", "地毯", "客廳的地毯。"),
    ("Living_Sideboard", "餐具櫃", "樓梯旁的小櫃子。"),
    ("Dining_Table", "餐桌", "一家人吃飯的餐桌。"),
    ("Dining_Chair", "餐椅", "餐桌的椅子。"),
    ("Kitchen_Counter", "流理台", "媽媽做飯的地方，有水槽和瓦斯爐。"),
    ("Kitchen_Fridge", "冰箱", "說不定有銅鑼燒？"),
    ("Kitchen_Cabinet", "廚房收納櫃", "放餐具的櫃子。"),
    ("Kitchen_Hood", "抽油煙機", "瓦斯爐上方的抽油煙機。"),
    ("Toilet_1F_Washbasin", "洗手台", "一樓的洗手台。"),
    ("Toilet_", "馬桶", "廁所。"),
    ("Genkan_ShoeCabinet", "鞋櫃", "玄關的鞋櫃，進門要脫鞋喔。"),
    ("Genkan_StepBoard", "玄關踏板", "從玄關踏上室內地板的台階。"),
    ("Genkan_Umbrella", "傘架", "玄關的傘架。"),
    ("Stairs_", "樓梯", "通往二樓的樓梯。"),
    ("Stair_", "樓梯扶手", "樓梯的扶手。"),
    ("Parents_Bed", "雙人床", "爸爸媽媽的床。"),
    ("Parents_Desk", "書桌", "爸爸在家工作用的書桌。"),
    ("Parents_Dresser", "梳妝台", "媽媽的梳妝台。"),
    ("Parents_Wardrobe", "衣櫃", "爸媽的衣櫃。"),
    ("Storage_Boxes", "雜物箱", "儲藏室裡的箱子。"),
    ("Closet_2F_Shelves", "收納架", "走廊收納櫃裡的架子。"),
    ("Bicycle_", "腳踏車", "淑女車，大雄常騎著去找靜香。"),
    ("Carport_", "駐輪場", "放腳踏車的棚子。"),
    ("Nameplate_Text", "門牌", "寫著「野比」的門牌。"),
    ("BlockWall", "水泥磚牆", "圍繞野比家的水泥磚圍牆，有鏤空花磚。"),
    ("Planter_", "路邊植栽", "圍牆外的小樹。"),
    ("UtilityPole", "電線桿", "街角的電線桿。"),
    ("Tree_", "庭院樹木", "院子裡的樹。"),
]
ROOMS = [
    ("Floor_1F_Genkan_Doma", "玄關"), ("Floor_1F_Toilet", "一樓廁所・洗手間"), ("Floor_1F_Hall", "一樓走廊"),
    ("Floor_1F_UnderStairs", "樓梯下"), ("Floor_1F_Living", "客廳"), ("Floor_1F_Dining_Kitchen", "餐廳・廚房"),
    ("Tatami_2F_Nobita", "大雄的房間"), ("Floor_2F_NobitaRoom", "大雄的房間"), ("Floor_2F_Hall", "二樓走廊"),
    ("Floor_2F_Closet", "收納櫃"), ("Floor_2F_Toilet", "二樓廁所"), ("Floor_2F_Storage", "儲藏室"),
    ("Floor_2F_ParentsRoom", "爸媽的房間"), ("Stairs_Treads", "樓梯"), ("Collider_Stairs", "樓梯"),
    ("Ground_Lot", "院子"), ("Path_Stones", "院子"), ("Porch", "玄關前"), ("Carport_Slab", "駐輪場"), ("Street", "街道"),
]

def apply_labels():
    for ob in bpy.data.objects:
        for k in ("label", "desc", "room"):
            if k in ob: del ob[k]
        for pre, name, desc in LABELS:
            if ob.name.startswith(pre):
                ob["label"] = name; ob["desc"] = desc
                break
        for pre, room in ROOMS:
            if ob.name.startswith(pre):
                ob["room"] = room
                break

def export_toon_glb(path):
    sc = bpy.context.scene
    sc.frame_set(0)
    apply_labels()
    swapped = []
    for ob in bpy.data.objects:
        if ob.type in ("MESH", "FONT"):
            for i, sl in enumerate(ob.material_slots):
                if sl.material and not sl.material.name.endswith(("_Toon", "_Anime")):
                    swapped.append((ob, i, sl.material)); sl.material = toon_material(sl.material)
    ops = [o for o in bpy.data.objects if o.get("openable")]
    for o in ops:
        ad = o.animation_data
        for t in ad.nla_tracks: t.mute = True
        ad.action = bpy.data.actions[o["anim_open_action"]]
        if hasattr(ad, "action_slot") and ad.action_slot is None and ad.action.slots:
            ad.action_slot = ad.action.slots[0]
    sc.frame_set(0)
    bd = bpy.data.collections.get("Render_Backdrop")
    if bd: bd.hide_viewport = False
    bpy.ops.object.select_all(action="DESELECT")
    for ob in bpy.data.objects:
        if ob.type in ("MESH", "FONT", "EMPTY") and not ob.name.startswith(("ScaleRef", "_Section")) and ob.visible_get():
            ob.select_set(True)
    try:
        bpy.ops.export_scene.gltf(filepath=path, export_format="GLB", use_selection=True, export_extras=True,
                                  export_apply=True, export_image_format="JPEG", export_jpeg_quality=85,
                                  export_animations=True, export_animation_mode="ACTIONS",
                                  export_draco_mesh_compression_enable=True, export_draco_mesh_compression_level=6,
                                  export_tangents=False, export_normals=True)
    finally:
        for ob, i, m in swapped:
            ob.material_slots[i].material = m
        for o in ops:
            ad = o.animation_data; ad.action = None
            for t in ad.nla_tracks: t.mute = False
        if bd: bd.hide_viewport = True
        sc.frame_set(0)
    return path
