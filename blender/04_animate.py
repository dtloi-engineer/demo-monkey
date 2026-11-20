"""STEP 4 (in Blender) - keyframe the demo sequence on a rig made by 03_rig_biped.py.

    OVERRIDES = {"RIG": "BabyMonkeyRig", "MESH": "BabyMonkey"}
    exec(open(r".../blender/04_animate.py", encoding="utf-8").read())

Sequence (24 fps, 212 frames ~ 8.8 s):
    1-49    walk, 2 cycles (arms swing opposite legs, bob, shoulder twist)
    49-97   run, 3 cycles (lean forward, bent elbows, flight phase)
    97-114  slow down and stop
    120-158 wave hello, head shaking with the wave
    168     crouch (anticipation)
    176-182 jump with arms in a V
    190-212 land, settle, rest
The root bone moves the character forward (world -Y) at a speed matched to the stride,
then the hips are re-keyed so the feet touch the ground (Z=0) whenever they should.
Pose numbers are degrees on the axes documented in 03_rig_biped.py; leg/arm amplitudes
are tuned for a chibi (big head, short limbs) - scale them down for realistic bodies.
"""
import math

import bpy

CONFIG = dict(RIG="CharacterRig", MESH="Character", CENTER_PATH=True)
CONFIG.update(globals().get("OVERRIDES", {}))
R = math.radians


def P(**kw):
    o = {}
    for k, v in kw.items():
        n = k.replace("_L", ".L").replace("_R", ".R")
        if n == "hips_up":
            o.setdefault("hips", [(0, 0, 0), (0, 0, 0)])[0] = (0, v, 0)
        else:
            o.setdefault(n, [(0, 0, 0), (0, 0, 0)])[1] = v
    return o


REST_ARMS = dict(upper_arm_L=(0, 0, 4), upper_arm_R=(0, 0, -4))


def walk(p, amp=1.0):
    c, s = math.cos(2 * math.pi * p / 24), math.sin(2 * math.pi * p / 24)
    th = 25 * amp
    swl, swr = max(0, -s), max(0, s)
    return P(thigh_L=(th * c, 0, 0), thigh_R=(-th * c, 0, 0),
             shin_L=(-8 - 45 * swl * amp, 0, 0), shin_R=(-8 - 45 * swr * amp, 0, 0),
             foot_L=(8 * c * amp + 12 * swl, 0, 0), foot_R=(-8 * c * amp + 12 * swr, 0, 0),
             hips_up=-0.004 + 0.008 * abs(s) * amp,
             spine=(3 * amp, 6 * c * amp, 0), head=(-2, -5 * c * amp, 0),
             upper_arm_L=(-22 * c * amp, 0, 4), upper_arm_R=(22 * c * amp, 0, -4),
             forearm_L=(10 * amp, 0, 0), forearm_R=(10 * amp, 0, 0))


def run(p):
    c, s = math.cos(2 * math.pi * p / 16), math.sin(2 * math.pi * p / 16)
    swl, swr = max(0, -s), max(0, s)
    return P(thigh_L=(40 * c + 10, 0, 0), thigh_R=(-40 * c + 10, 0, 0),
             shin_L=(-15 - 85 * swl, 0, 0), shin_R=(-15 - 85 * swr, 0, 0),
             foot_L=(10 * c + 15 * swl, 0, 0), foot_R=(-10 * c + 15 * swr, 0, 0),
             hips_up=0.012 * abs(s) - 0.006 + 0.02 * abs(math.sin(2 * math.pi * p / 8 + 0.6)),
             spine=(12, 9 * c, 0), head=(-10, -7 * c, 0),
             upper_arm_L=(-40 * c, 0, 10), upper_arm_R=(40 * c, 0, -10),
             forearm_L=(70, 0, 0), forearm_R=(70, 0, 0))


def wave(fa, hz, sp):
    return P(upper_arm_R=(0, 0, -82), forearm_R=(0, 0, fa), hand_R=(0, 0, -10),
             upper_arm_L=(0, 0, 6), head=(0, hz, -10), spine=(0, 0, sp))


def legs(d, k):
    return dict(hips_up=-d, thigh_L=(30 * k, 0, 0), thigh_R=(30 * k, 0, 0),
                shin_L=(-55 * k, 0, 0), shin_R=(-55 * k, 0, 0), foot_L=(25 * k, 0, 0), foot_R=(25 * k, 0, 0))


def build_keys():
    K = {}
    for i in range(0, 49, 3):
        K[1 + i] = walk(i % 24)
    for i in range(0, 49, 2):
        K[49 + i] = run(i % 16 if i < 48 else 0)
    K[103] = walk(0, 0.5)
    K[109] = P(**REST_ARMS, spine=(-3, 0, 0), head=(4, 0, 0))
    K[114] = P(**REST_ARMS)
    for fr, args in {120: (-70, 0, -4), 126: (-95, 8, -5), 132: (-55, -8, -4),
                     138: (-95, 8, -5), 144: (-55, -8, -4), 150: (-75, 0, -3)}.items():
        K[fr] = wave(*args)
    K[158] = P(**REST_ARMS, head=(2, 0, 0))
    K[168] = P(**legs(0.07, 1.2), spine=(14, 0, 0), head=(-10, 0, 0), upper_arm_L=(0, 0, -10), upper_arm_R=(0, 0, 10))
    K[176] = P(hips_up=0.20, spine=(-8, 0, 0), head=(-10, 0, 0), upper_arm_L=(0, 0, 60), upper_arm_R=(0, 0, -60),
               forearm_L=(0, 0, 22), forearm_R=(0, 0, -22), thigh_L=(55, 0, 0), shin_L=(-80, 0, 0),
               thigh_R=(20, 0, 0), shin_R=(-60, 0, 0), foot_L=(10, 0, 0), foot_R=(20, 0, 0))
    K[182] = P(hips_up=0.22, spine=(-6, 0, 0), head=(-8, 0, 0), upper_arm_L=(0, 0, 65), upper_arm_R=(0, 0, -65),
               forearm_L=(0, 0, 25), forearm_R=(0, 0, -25), thigh_L=(45, 0, 0), shin_L=(-70, 0, 0),
               thigh_R=(30, 0, 0), shin_R=(-70, 0, 0), foot_L=(10, 0, 0), foot_R=(10, 0, 0))
    K[190] = P(**legs(0.08, 1.3), spine=(12, 0, 0), head=(-6, 0, 0), upper_arm_L=(0, 0, 35), upper_arm_R=(0, 0, -35))
    K[198] = P(**legs(0.0, 0.1), spine=(-3, 0, 0), upper_arm_L=(0, 0, 10), upper_arm_R=(0, 0, -10), head=(-4, 0, 6))
    K[212] = P(**REST_ARMS, head=(2, 0, 4))
    return K


def fcurves(action):
    if hasattr(action, "fcurves") and len(action.fcurves):
        return list(action.fcurves)
    out = []  # Blender 4.4+/5.x layered actions
    for layer in action.layers:
        for strip in layer.strips:
            for cb in strip.channelbags:
                out += list(cb.fcurves)
    return out


def min_z(sc, obj, f):
    sc.frame_set(f)
    dg = bpy.context.evaluated_depsgraph_get()
    e = obj.evaluated_get(dg)
    me = e.to_mesh()
    z = min((obj.matrix_world @ v.co).z for v in me.vertices)
    e.to_mesh_clear()
    return z


def main():
    sc = bpy.context.scene
    rig = bpy.data.objects[CONFIG["RIG"]]
    mesh = bpy.data.objects[CONFIG["MESH"]]
    pb = rig.pose.bones
    rig.animation_data_clear()
    for b in pb:
        b.rotation_mode = "XYZ"
        b.rotation_euler = (0, 0, 0)
        b.location = (0, 0, 0)
    body = [b.name for b in pb if not b.name.startswith("tail") and b.name != "root"]
    K = build_keys()
    for fr in sorted(K):
        for n in body:
            loc, rot = K[fr].get(n, [(0, 0, 0), (0, 0, 0)])
            pb[n].location = loc
            pb[n].rotation_euler = tuple(R(x) for x in rot)
            pb[n].keyframe_insert("location", frame=fr)
            pb[n].keyframe_insert("rotation_euler", frame=fr)

    # forward travel on the root bone, speed matched to stride length
    thigh = rig.data.bones["thigh.L"]
    leg = (thigh.head_local - rig.data.bones["shin.L"].tail_local).length
    vw = 2 * leg * math.sin(R(25)) / 12
    vr = 2 * leg * math.sin(R(40)) / 8 * 1.15
    d = 0.0
    pb["root"].location = (0, 0, 0)
    pb["root"].keyframe_insert("location", frame=1)
    for fr in range(2, 113):
        if fr <= 49:
            v = vw
        elif fr <= 57:
            v = vw + (vr - vw) * (fr - 49) / 8
        elif fr <= 97:
            v = vr
        else:
            v = vr * max(0, (112 - fr) / 15) ** 1.5
        d += v
        if fr % 2 == 1 or fr == 112:
            pb["root"].location = (0, d, 0)
            pb["root"].keyframe_insert("location", frame=fr)
    for fc in fcurves(rig.animation_data.action):
        if fc.data_path.startswith('pose.bones["root"]'):
            for k in fc.keyframe_points:
                k.interpolation = "LINEAR"
    if CONFIG["CENTER_PATH"]:
        rig.location.y = d / 2

    # tail wag with travelling phase
    tails = sorted((b for b in pb if b.name.startswith("tail")), key=lambda b: b.name)
    for fr in range(1, 213, 4):
        speed = 1.8 if 49 <= fr <= 100 else (2.2 if 118 <= fr <= 152 else 1.0)
        jump = 1.0 if 170 <= fr <= 188 else 0.0
        for i, b in enumerate(tails):
            ph = fr / 24 * 2 * math.pi * 0.9 * speed - i * 0.55
            b.rotation_euler = (math.sin(ph) * R(9 + i * 1.2), 0, R(-6 * jump - (8 if 49 <= fr <= 100 else 0)))
            b.keyframe_insert("rotation_euler", frame=fr)

    sc.frame_start, sc.frame_end = 1, 212
    sc.render.fps = 24

    # feet on the ground: shift hips keys by the measured penetration
    fc = next(c for c in fcurves(rig.animation_data.action)
              if c.data_path == 'pose.bones["hips"].location' and c.array_index == 1)
    for _ in range(2):
        for k in fc.keyframe_points:
            f = int(round(k.co[0]))
            if f in (176, 182):
                continue
            z = min_z(sc, mesh, f)
            if (49 < f < 98 and z < 0) or (not 49 < f < 98 and abs(z) > 0.002):
                k.co[1] -= z
                k.handle_left[1] -= z
                k.handle_right[1] -= z
        fc.update()
    for f in range(1, 213, 2):  # catch dips between keys
        z = min_z(sc, mesh, f)
        if z < -0.006 and not (170 < f < 190):
            pb["hips"].location[1] -= z
            pb["hips"].keyframe_insert("location", index=1, frame=f)
    sc.frame_set(1)
    print(f"animated 1-212, travel {d:.2f} m")


main()
