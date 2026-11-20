# Instructions for AI agents working in this repo

Goal of the repo: turn a character image into a rigged, animated Blender character
(walk → run → wave → V-jump) with Claude + Blender + MCP for Blender + TRELLIS/Hunyuan3D.
README.md is the full guide (Vietnamese). Follow it in order; this file is the short checklist.

## Setup checklist (do in order, verify each)
1. `python scripts/check_env.py` → decides **Case A** (local GPU ≥16 GB VRAM) or **Case B** (Hugging Face).
2. Blender installed, `uvx` works, MCP for Blender set up (`uvx mcp-for-blender setup`).
   Verify with the MCP tool `get_addon_status` (needs `up_to_date: true`). If MCP tools are missing,
   tell the user to fully restart Claude and open Blender; do not continue without them.
3. Case B: `HF_TOKEN` must be set by the USER in their environment. Never ask them to paste it in chat,
   never write it to a file, never print it. If they paste it anyway, use it only via an env var for the
   command and tell them to rotate it afterwards.
4. `python -m venv .venv` + `pip install -r requirements-hf.txt` (case B and image scripts).

## Working rules
- Put generated files in `out/` (git-ignored). Use absolute paths inside Blender.
- Blender scripts in `blender/` are run with `execute_blender_code`:
  `OVERRIDES = {...}; exec(open(r"<abs path>", encoding="utf-8").read())`
- **Look after every step** with the MCP `look` tool (angles front/right/back; frames through the camera).
  Most failures (wrong bone axis, feet in floor, arms melting the face, ground disc) are only visible in images.
- Read enum identifiers at runtime; look shader nodes up by `type`, not name (see MCP server instructions).
- Do not overwrite the user's existing .blend files: new scene or `save_as` to a new path.
- Quota errors from Hugging Face are final for the day — report the wait time, do not retry in a loop.
- Never commit secrets; check `git status` / `git diff --cached` before committing.

## Known-good parameters
- TRELLIS: multi-view (front/right/back/left), steps 30, simplify 0.90, texture 2048, algo multidiffusion.
- Character height 0.8 m for the chibi demo; joints in `blender/03_rig_biped.py` CONFIG.
- Bone axes after roll fix: limbs rot X+ = forward; upper_arm Z± = raise sideways; spine/head Y = twist;
  hips loc Y = up; root loc Y = forward (world −Y).
