# demo-monkey — Ảnh nhân vật → Model 3D → Rig → Animation bằng AI + Blender

Repo này hướng dẫn **từ máy trắng** đến khi có một nhân vật 3D biết **đi → chạy → vẫy tay → nhảy**,
chỉ bằng: **Claude (Opus) + Blender + MCP for Blender + một AI tạo 3D (TRELLIS / Hunyuan3D)**.

> **Dành cho AI agent (Claude Code, v.v.):** đọc hết file này và [CLAUDE.md](CLAUDE.md), rồi làm lần lượt
> mục 2 → 3 → (4 hoặc 5) → 6. Mỗi bước có lệnh kiểm tra; chỉ đi tiếp khi kiểm tra đạt.

Kết quả demo nằm sẵn trong [assets/baby_monkey/](assets/baby_monkey/):

| File | Là gì |
|---|---|
| `character_sheet.png` | Bảng thiết kế nhân vật (đầu vào) |
| `views/front.png, right.png, back.png, left.png` | 4 góc nhìn đã cắt ra từ bảng thiết kế |
| `baby_monkey_trellis.glb` | Model 3D có texture do TRELLIS tạo (chưa xử lý) |
| `baby_monkey.blend` | File Blender hoàn chỉnh: model + đuôi + rig 28 xương + animation 212 frame + sân khấu + camera |

Mở `baby_monkey.blend` bằng Blender → bấm **Space** để xem animation.

---

## Mục lục
1. [Tổng quan quy trình](#1-tổng-quan-quy-trình)
2. [Yêu cầu & chọn case](#2-yêu-cầu--chọn-case)
3. [Setup chung (mọi máy)](#3-setup-chung-mọi-máy)
4. [Case A — Tạo 3D trên GPU của máy](#4-case-a--tạo-3d-trên-gpu-của-máy-đủ-vram)
5. [Case B — Tạo 3D trên Hugging Face (không cần GPU)](#5-case-b--tạo-3d-trên-hugging-face-không-cần-gpu)
6. [Pipeline trong Blender (rig + animation)](#6-pipeline-trong-blender-rig--animation)
7. [Prompt mẫu cho Claude](#7-prompt-mẫu-cho-claude)
8. [Lỗi thường gặp](#8-lỗi-thường-gặp)
9. [Cấu trúc repo](#9-cấu-trúc-repo)
10. [Bảo mật](#10-bảo-mật)

---

## 1. Tổng quan quy trình

```
Ảnh / bảng thiết kế ──► cắt 4 góc nhìn ──► AI tạo 3D (.glb) ──► Blender: dọn mesh, scale
                                             │                      │
                              Case A: GPU máy │                      ▼
                              Case B: HF Space│            dựng xương + weight (+ đuôi)
                                                                   │
                                                                   ▼
                                    animation (đi/chạy/vẫy/nhảy) ──► sân khấu + camera ──► render MP4
```

| Thành phần | Vai trò |
|---|---|
| **Claude Code + model Opus** | "Đạo diễn": chạy lệnh, viết/chạy code trong Blender, **nhìn ảnh render để tự phát hiện lỗi và sửa** |
| **Blender** (≥ 4.2, đã test 5.3) | Dựng scene, rig, animation, render |
| **MCP for Blender** ([ahujasid/mcp-for-blender](https://github.com/ahujasid/mcp-for-blender)) | Cầu nối để Claude điều khiển Blender (chạy Python, chụp ảnh viewport/render) |
| **TRELLIS** (Microsoft) / **Hunyuan3D** (Tencent) | AI tạo model 3D có texture từ ảnh |
| **Python 3.10+** | Chạy script cắt ảnh, gọi AI tạo 3D |

**Bài học quan trọng nhất:** chất lượng phụ thuộc chủ yếu vào **ảnh đầu vào**.
- Tốt: nhân vật đơn giản (chibi/cartoon), **bảng thiết kế có 4 góc nhìn** (trước/sau/trái/phải), nền trơn, đứng thẳng tay buông (A-pose/T-pose).
- Xấu: nhiều chi tiết mỏng bay lượn (áo choàng, lông vũ, ruy băng), cầm vũ khí dài vắt ngang người, chỉ có 1 góc nhìn → AI phải đoán mặt sau, vũ khí dính vào tay, rig rất khó.

---

## 2. Yêu cầu & chọn case

### 2.1 Tài khoản & phần mềm

| Thứ cần | Bắt buộc? | Ghi chú |
|---|---|---|
| **Claude** gói trả phí, dùng **Opus** | Có | Khuyến nghị Opus (vd. Claude Opus 5.5). Sonnet làm được bước đơn giản nhưng hay sai ở rig/animation (phải tự nhìn ảnh, tự sửa nhiều vòng). Haiku không đủ. |
| **Claude Code** (desktop app hoặc CLI) | Có | https://claude.com/claude-code |
| **Blender** 4.2+ | Có | https://www.blender.org/download/ (đã test 5.3) |
| **uv** (trình quản lý Python của Astral) | Có | Dùng để chạy MCP server |
| **Git** | Có | Clone/push repo |
| **Python** 3.10+ | Có | Chạy script trong `scripts/` |
| **Tài khoản Hugging Face** + token Read | Case B | Miễn phí: https://huggingface.co/join |
| **GPU NVIDIA ≥ 16 GB VRAM** + CUDA | Case A | Xem bảng 2.2 |

### 2.2 Chọn case — chạy công cụ kiểm tra

```bash
python scripts/check_env.py
```

Nó in ra GPU/VRAM, Blender, uv, git, `HF_TOKEN` (chỉ báo *set/NOT set*, không in giá trị) và **khuyến nghị case**.

| VRAM GPU NVIDIA | Làm được gì trên máy | Case |
|---|---|---|
| ≥ 24 GB | TRELLIS, Hunyuan3D-2/2.1 đầy đủ, thoải mái | **A** |
| 16 GB | TRELLIS (hình + texture), Hunyuan3D-2 hình + texture | **A** |
| 6–12 GB | Chỉ Hunyuan3D-2mini **tạo hình, không texture** | **B** (hoặc A không texture) |
| < 6 GB / không có NVIDIA / Mac | Không chạy local được | **B** |

> Con số VRAM là ước lượng theo README của từng dự án tại thời điểm viết — kiểm tra lại trang gốc trước khi mua phần cứng.
> CPU-only: không khả thi (quá chậm hoặc không hỗ trợ).

---

## 3. Setup chung (mọi máy)

### 3.1 Clone repo
```bash
git clone https://github.com/dtloi-engineer/demo-monkey.git
cd demo-monkey
```

### 3.2 Cài Blender
- Windows: tải installer ở blender.org, hoặc `winget install --id BlenderFoundation.Blender -e`
- macOS: `brew install --cask blender`
- Linux: `sudo snap install blender --classic`

Kiểm tra: `blender --version` (Windows có thể không có trên PATH — không sao, `check_env.py` vẫn tìm thấy).

### 3.3 Cài uv
- Windows: `winget install --id=astral-sh.uv -e` (rồi **mở terminal mới**)
- macOS/Linux: `curl -LsSf https://astral.sh/uv/install.sh | sh`

⚠️ Dùng installer chính thức, **không** `pip install uv`. Kiểm tra: `uvx --version`.

### 3.4 Cài MCP for Blender (cầu nối Claude ↔ Blender)

**Cách nhanh (khuyến nghị)** — tự cấu hình Claude Code/Claude Desktop và cài addon vào Blender:
```bash
uvx mcp-for-blender setup
```

**Cách thủ công:**
```bash
# 1) đăng ký MCP server với Claude Code
claude mcp add blender uvx mcp-for-blender
# 2) cài + bật addon trong Blender
uvx mcp-for-blender install-addon
```
Claude Desktop (không phải Claude Code): Settings → Developer → Edit Config, thêm:
```json
{ "mcpServers": { "blender": { "command": "uvx", "args": ["mcp-for-blender"] } } }
```
Nếu báo `spawn uvx ENOENT`: dùng đường dẫn đầy đủ của uvx (`where uvx` trên Windows) làm `"command"`.

Sau đó: **thoát hẳn và mở lại** Claude (Windows: thoát cả ở khay hệ thống), mở Blender.

**Kiểm tra kết nối:**
1. Trong Blender: rê chuột vào khung 3D → bấm **N** → tab **MCP for Blender** → phải thấy *Connected on localhost:9876* (nếu chưa, bấm **Start MCP Server**).
2. Trong Claude, hỏi: *"gọi get_addon_status của blender"* → phải trả về `blender_version` và `up_to_date: true`.

### 3.5 Môi trường Python cho script
```bash
python -m venv .venv
# Windows
.venv\Scripts\activate
# macOS/Linux
source .venv/bin/activate

pip install -r requirements-hf.txt
```

---

## 4. Case A — Tạo 3D trên GPU của máy (đủ VRAM)

Yêu cầu: NVIDIA GPU (xem bảng 2.2), driver mới, **CUDA 11.8 hoặc 12.x**, `conda` (Miniconda).
TRELLIS chính thức hỗ trợ **Linux**; trên Windows nên dùng **WSL2 (Ubuntu)** để đỡ lỗi build.

### 4.1 Chuẩn bị ảnh
```bash
python scripts/crop_turnaround.py assets/baby_monkey/character_sheet.png out/views --blank-top front=40
# xem out/views/contact_sheet.png: mỗi ô phải là 1 góc nhìn sạch
```
Với ảnh khác: mở ảnh, đọc toạ độ khung từng góc nhìn và truyền `--box name=x0,y0,x1,y1` (xem docstring của script).
Chỉ có 1 ảnh chính diện thì bỏ bước này, dùng thẳng ảnh đó.

### 4.2 TRELLIS (khuyến nghị — ra GLB có texture, hỗ trợ đa góc nhìn)
```bash
git clone --recurse-submodules https://github.com/microsoft/TRELLIS.git
cd TRELLIS
. ./setup.sh --new-env --basic --xformers --flash-attn --diffoctreerast --spconv --mipgaussian --kaolin --nvdiffrast
conda activate trellis
# chạy từ trong thư mục TRELLIS để import được package "trellis"
python ../demo-monkey/scripts/gen_local_trellis.py --views-dir ../demo-monkey/out/views --out ../demo-monkey/out/model.glb
```
Lệnh `setup.sh` lấy từ README gốc của TRELLIS — nếu lỗi, làm theo README mới nhất của họ.
Lần chạy đầu tự tải weight `microsoft/TRELLIS-image-large` (~vài GB).

### 4.3 Hunyuan3D-2 (thay thế; có bản mini cho VRAM thấp)
```bash
git clone https://github.com/Tencent/Hunyuan3D-2.git
cd Hunyuan3D-2
pip install -r requirements.txt
pip install -e .
# texture cần build 2 extension:
cd hy3dgen/texgen/custom_rasterizer && python setup.py install && cd ../../..
cd hy3dgen/texgen/differentiable_renderer && python setup.py install && cd ../../..

python ../demo-monkey/scripts/gen_local_hunyuan.py --image ../demo-monkey/out/views/front.png --out ../demo-monkey/out/model_hy.glb
# VRAM ~6 GB: chỉ tạo hình, không texture
python ../demo-monkey/scripts/gen_local_hunyuan.py --image ... --out ... --mini --no-texture
# đa góc nhìn
python ../demo-monkey/scripts/gen_local_hunyuan.py --views-dir ../demo-monkey/out/views --out ... --mv
```

Thông số chất lượng cao (đã dùng cho demo): **30–50 bước**, **texture 2048**, **simplify 0.90** (ít rút gọn).

Xong → sang [mục 6](#6-pipeline-trong-blender-rig--animation).

---

## 5. Case B — Tạo 3D trên Hugging Face (không cần GPU)

Chạy trên GPU miễn phí của Hugging Face (ZeroGPU). **Có giới hạn mỗi ngày.**

### 5.1 Tạo token
1. Đăng ký https://huggingface.co/join
2. https://huggingface.co/settings/tokens → **Create new token** → loại **Read** → copy.
3. Đặt vào biến môi trường (**tự làm, không dán token vào chat với AI, không commit**):

Windows (PowerShell) — lưu vĩnh viễn, mở terminal/app mới để có hiệu lực:
```powershell
setx HF_TOKEN "hf_xxx_token_cua_ban"
```
macOS/Linux:
```bash
echo 'export HF_TOKEN="hf_xxx_token_cua_ban"' >> ~/.bashrc && source ~/.bashrc
```
Kiểm tra: `python scripts/check_env.py` → dòng `HF_TOKEN : set`.

### 5.2 Quota (đọc kỹ)
| Loại | ZeroGPU mỗi ngày | Đủ cho |
|---|---|---|
| Ẩn danh (không token) | rất ít | ~1 lần chạy rồi hết |
| Tài khoản free + token | vài phút | ~1–2 model chất lượng cao/ngày |
| **HF PRO** (~9 USD/tháng) | ~40 phút | thoải mái |

Hết quota sẽ báo `You have exceeded your ZeroGPU quota (…s requested vs. …s left). Try again in HH:MM:SS` → chờ hồi (24h) hoặc nâng PRO. Mọi Space ZeroGPU dùng **chung** quota của tài khoản.

### 5.3 Chạy
```bash
# (đã activate .venv và pip install -r requirements-hf.txt)
python scripts/crop_turnaround.py assets/baby_monkey/character_sheet.png out/views --blank-top front=40

# TRELLIS đa góc nhìn — cách đã ra model demo (~120 s quota)
python scripts/gen_hf_trellis.py --views-dir out/views --out out/model.glb

# 1 ảnh
python scripts/gen_hf_trellis.py --front path/to/image.png --out out/model.glb

# Hunyuan3D-2.1 (cần ~270 s quota/lần → chạy đầu ngày hoặc dùng PRO)
python scripts/gen_hf_hunyuan.py --image out/views/front.png --out out/model_hy.glb
python scripts/gen_hf_hunyuan.py --list-api   # nếu Space đổi API
```

Tình trạng các Space khi viết (11/2026):
| Space | Kết quả |
|---|---|
| `trellis-community/TRELLIS` | ✅ ổn định — dùng cho demo |
| `tencent/Hunyuan3D-2.1` | ⚠️ chạy được nhưng cần 270 s/lần |
| `tencent/Hunyuan3D-2` | ❌ lỗi texture phía server (`texgen_worker is not defined`) |

Các lựa chọn khác đã thử và **không** dùng được miễn phí: Meshy (gen free nhưng **tải về phải trả phí**), key dùng thử Hyper3D Rodin trong addon (đã hết lượt).

Xong → sang [mục 6](#6-pipeline-trong-blender-rig--animation).

---

## 6. Pipeline trong Blender (rig + animation)

Các bước chạy **trong Blender** qua MCP (`execute_blender_code`). Mỗi script có khối `CONFIG` ở đầu;
ghi đè bằng biến `OVERRIDES` trước khi `exec`. **Dùng đường dẫn tuyệt đối.**

| Bước | Script | Làm gì |
|---|---|---|
| 1 | `blender/01_import_cleanup.py` | Import GLB, gộp đỉnh, **tự xoá "đĩa" bóng đổ**, scale theo chiều cao, chân chạm Z=0 |
| 2 | `blender/02_render_reference.py` + `scripts/grid_overlay.py` | Render chính diện/bên hông có lưới để đo vị trí khớp (chỉ cần với nhân vật mới) |
| 3 | `blender/03_rig_biped.py` | Dựng 18 xương người + (tuỳ chọn) đuôi xoắn 10 đốt, gắn weight |
| 4 | `blender/04_animate.py` | Đi → chạy → dừng → vẫy tay → nhảy chữ V → tiếp đất (212 frame), chân không lún sàn |
| 5 | `blender/05_stage_camera.py` | Sân khấu, 3 đèn, camera bám theo nhân vật, Eevee |
| 6 | `blender/06_render_video.py` | Render MP4 |

Ví dụ chạy toàn bộ với model demo (Claude gửi từng khối qua `execute_blender_code`, sửa `D:/path/demo-monkey` thành đường dẫn thật):
```python
OVERRIDES = {"GLB": r"D:/path/demo-monkey/assets/baby_monkey/baby_monkey_trellis.glb",
             "NAME": "BabyMonkey", "HEIGHT": 0.8, "NEW_SCENE": "BabyMonkey"}
exec(open(r"D:/path/demo-monkey/blender/01_import_cleanup.py", encoding="utf-8").read())
```
```python
OVERRIDES = {"MESH": "BabyMonkey", "RIG": "BabyMonkeyRig"}   # khớp xương mặc định = khỉ con 0.8 m
exec(open(r"D:/path/demo-monkey/blender/03_rig_biped.py", encoding="utf-8").read())
```
```python
OVERRIDES = {"RIG": "BabyMonkeyRig", "MESH": "BabyMonkey"}
exec(open(r"D:/path/demo-monkey/blender/04_animate.py", encoding="utf-8").read())
OVERRIDES = {"RIG": "BabyMonkeyRig", "HEIGHT": 0.8}
exec(open(r"D:/path/demo-monkey/blender/05_stage_camera.py", encoding="utf-8").read())
```
```python
OVERRIDES = {"OUT": r"D:/path/demo-monkey/out/monkey.mp4", "PERCENT": 50}
exec(open(r"D:/path/demo-monkey/blender/06_render_video.py", encoding="utf-8").read())
```
Pipeline này đã được chạy lại từ đầu trên `baby_monkey_trellis.glb` và cho kết quả giống file `.blend` demo.

### 6.1 Nhân vật mới (không phải khỉ con)
1. Bước 1 với `HEIGHT` phù hợp. **Nhìn** model (công cụ `look` của MCP, các góc front/right/back) — xoá phần thừa nếu còn.
2. Bước 2 → `python scripts/grid_overlay.py out/ref_front.png out/ref_side.png` → đọc pixel các khớp
   (cằm, vai, khuỷu, cổ tay, hông, gối, cổ chân) → đổi ra mét theo công thức script in ra.
3. Bước 3 với `OVERRIDES["JOINTS"]` mới (cùng tên khoá như mặc định), `HEAD_LOCK_Z` = độ cao cằm,
   `TAIL_POINTS=None` nếu không có đuôi.
4. Đặt **tư thế thử** (vẫy tay, ngồi xuống) và **nhìn** trước khi làm animation — xem bảng trục bên dưới.
5. Bước 4–6. Nhân vật tỉ lệ người thật thì giảm biên độ chân/tay trong `04_animate.py`.

### 6.2 Quy ước trục xương (sau `calculate_roll GLOBAL_NEG_Y`)
| Xương | Trục | Ý nghĩa |
|---|---|---|
| thigh / shin / upper_arm / forearm | rot **X+** | đưa về **phía trước** (shin X− = gập gối) |
| upper_arm.L / .R | rot **Z+ / Z−** | giơ tay sang ngang |
| spine / head | rot X / Y / Z | cúi về trước / **xoay (vặn)** / nghiêng ngang |
| hips | location **Y** | lên/xuống |
| root | location **Y** | tiến về phía trước (world −Y) |
| tail.* | rot X / Z | vẫy ngang / cuộn |

---

## 7. Prompt mẫu cho Claude

Sau khi setup xong, mở Claude Code trong thư mục repo:

```
Đọc README.md và CLAUDE.md. Kiểm tra môi trường bằng scripts/check_env.py và get_addon_status.
Dùng ảnh <đường dẫn ảnh> để tạo model 3D (chọn case A hay B theo check_env),
rồi import vào Blender, rig, làm animation đi → chạy → vẫy tay → nhảy, dựng sân khấu và camera.
Nhìn kết quả sau mỗi bước, sửa lỗi nếu thấy, cuối cùng lưu file .blend vào out/.
```

Mẹo: yêu cầu Claude **luôn nhìn ảnh** (`look`) sau mỗi bước — đó là cách duy nhất để bắt lỗi như trục xương sai, chân lún, tay kéo méo mặt.

---

## 8. Lỗi thường gặp

| Triệu chứng | Nguyên nhân | Cách xử lý |
|---|---|---|
| `exceeded your ZeroGPU quota` | Hết quota HF ngày | Chờ thời gian báo trong lỗi, dùng token, hoặc HF PRO |
| `API_INSUFFICIENT_FUNDS` (Hyper3D) | Key dùng thử chung của addon đã hết | Dùng TRELLIS trên HF hoặc key Rodin riêng |
| Meshy "Subscribe to download" | Gói free không cho tải | Dùng TRELLIS/Hunyuan |
| `texgen_worker is not defined` | Space Hunyuan3D-2 hỏng phía server | Dùng TRELLIS hoặc Hunyuan3D-2.1 |
| Có cái đĩa phẳng dưới chân model | AI hiểu bóng đổ là vật thể | `01_import_cleanup.py` tự xoá (`REMOVE_DISC`) |
| `Bone Heat Weighting: failed to find solution` | Mesh nhỏ/hở (AI mesh) | `03_rig_biped.py` đã xử lý bằng scale ×10 tạm thời |
| Giơ tay làm méo má/tai | Weight tay lan lên đầu | `HEAD_LOCK_Z` (đầu theo 100% xương head) + giảm biên độ giơ tay |
| Nhân vật nghiêng thay vì vặn người | Xoay sai trục | Xem bảng 6.2: vặn người = trục **Y** của spine/head |
| Chân lún xuống sàn khi ngồi | Hạ hông nhiều hơn độ gập chân | `04_animate.py` tự đo và bù hông |
| Vũ khí/gậy bị kéo méo | Gậy dính vào tay (1 khối mesh) | Gán cả gậy + cẳng tay cho 1 xương; tốt nhất tránh ảnh có vũ khí |
| `spawn uvx ENOENT` | App GUI không thấy PATH | Dùng đường dẫn đầy đủ của uvx trong config |
| Ảnh `look` bị đen | Scene mới chưa có đèn/world | Bình thường — chạy bước 5 hoặc dùng shading `material` |
| Model ra "xấu" | Ảnh nhiều chi tiết, 1 góc nhìn, ít bước | Dùng bảng 4 góc nhìn, 30+ bước, texture 2048, simplify 0.90 |

---

## 9. Cấu trúc repo

```
demo-monkey/
├── README.md                 # file này
├── CLAUDE.md                 # chỉ dẫn ngắn cho AI agent
├── requirements-hf.txt       # gradio_client, pillow (case B + script ảnh)
├── scripts/                  # chạy bằng Python thường
│   ├── check_env.py          # kiểm tra máy, khuyến nghị case A/B
│   ├── crop_turnaround.py    # cắt bảng thiết kế thành 4 góc nhìn
│   ├── grid_overlay.py       # vẽ lưới lên ảnh tham chiếu để đo khớp
│   ├── gen_hf_trellis.py     # Case B: TRELLIS trên Hugging Face
│   ├── gen_hf_hunyuan.py     # Case B: Hunyuan3D trên Hugging Face
│   ├── gen_local_trellis.py  # Case A: TRELLIS trên GPU máy
│   └── gen_local_hunyuan.py  # Case A: Hunyuan3D-2 trên GPU máy
├── blender/                  # chạy TRONG Blender (qua MCP hoặc Text Editor)
│   ├── 01_import_cleanup.py
│   ├── 02_render_reference.py
│   ├── 03_rig_biped.py
│   ├── 04_animate.py
│   ├── 05_stage_camera.py
│   └── 06_render_video.py
├── assets/baby_monkey/       # demo đầu vào + kết quả
└── out/                      # (git bỏ qua) kết quả bạn tự tạo
```

---

## 10. Bảo mật

- **Không bao giờ** commit token (`HF_TOKEN`, API key). Script đọc token từ biến môi trường, `.gitignore` chặn `.env`.
- **Không dán token vào khung chat với AI**: nó nằm lại trong lịch sử hội thoại. Lỡ dán → vào https://huggingface.co/settings/tokens **xoá token đó và tạo token mới**.
- Addon MCP mở socket `localhost:9876` không mã hoá/không xác thực — chỉ dùng trên máy cá nhân; có thể bật `BLENDER_MCP_SAFE_MODE=1` để chặn code rủi ro.
- Model tạo từ ảnh nhân vật có bản quyền (game/phim) chỉ nên dùng cá nhân/học tập.

---

*Công cụ bên thứ ba: MCP for Blender (MIT, Siddharth Ahuja), TRELLIS (Microsoft), Hunyuan3D (Tencent), Blender (GPL). Kiểm tra giấy phép từng dự án trước khi dùng thương mại.*
