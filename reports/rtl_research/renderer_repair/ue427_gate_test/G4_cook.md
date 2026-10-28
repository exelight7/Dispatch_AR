# G4: Cook / shader delivery (editor side)

**UE 5.8.4: G4_EDITOR_COOK_PASS_UE58. UE4.27: G4_NOT_RUN.** The 5.8 packages cannot be loaded by DISPATCH (4.27 custom branch; different package versions). This only shows what the cook produces.

## Cook A: shared shader code (DISPATCH flags)
- `-run=cook -targetplatform=Windows`, `bShareMaterialShaderCode=True`, `bUseIoStore=False`.
- Result: Success, 0 errors. 503 packages cooked. One unrelated warning (bUseZenStore with IoStore off).
- `M_ArabicReveal.uexp` is 12,000 bytes and holds no shader code.
- The material's shaders live in `ShaderArchive-RevealTest-PCD3D_SM5-PCD3D_SM5.ushaderbytecode` (3,688,575 bytes, the project-wide library). `ShaderAssetInfo` maps shadermap `681C1CD2E846DBA3` → `/Game/ArabicReveal/M_ArabicReveal`.
- The MICs (1,357 B uexp) carry no shaders; they use the parent's shadermap.
- **Consequence for DISPATCH:** with shared shader code, a mod material needs its own shader archive that the game opens, or the game's library would have to contain it. Opening an extra library on pak mount is NOT_PROVEN for DISPATCH's build.

## Cook B: inline shader code
- `bShareMaterialShaderCode=False`, `bSharedMaterialNativeLibraries=False`.
- Result: Success. `M_ArabicReveal.uexp` grows to **33,861 bytes** (inline shader map). No `.ushaderbytecode` is produced.
- This is round 004's Option A. Whether DISPATCH (shared-library project) accepts an inline shader map in a mod package is NOT_PROVEN.

## Test paks (UnrealPak 5.8, not for installation)
| Pak | SHA256 | Contents |
|---|---|---|
| `RevealAR_shared_P.pak` | `6891e962e686e1aa31f4daf0e29b642e6329b02f384b89dfb289cf4e79083158` | 20 ArabicReveal files + project shader archive, mount `../../../RevealTest/Content/` |
| `RevealAR_inline_P.pak` | `4d0155c0bb63e98ca247e4010538b3fe246bcee21f056949083c644086a79422` | 20 ArabicReveal files, inline shaders |

Listings: `cook/pak_list_shared.txt`, `cook/pak_list_inline.txt`. Shader asset map: `cook/ShaderAssetInfo-RevealTest-PCD3D_SM5-PCD3D_SM5.assetinfo.json`.
The paks stay in `tools/ue427_stock_reveal_test/Saved/` and were **not** copied anywhere near the game.

## Dependencies (from construction)
- `DT_ArabicReveal[_Shadow]` → `F_ArabicReveal` → `FF_Roboto_Regular`, `FF_NotoNaskhArabicUI_Regular`
- `DT_ArabicReveal[_Shadow]` → `MI_ArabicReveal_FG/_Shadow` → `M_ArabicReveal` → `RT_ArabicReveal` (default texture parameter)

## Sizes to note
Each DataTable cooks to 1,375,282 bytes: 256 rows, each with a full `FTextBlockStyle`. Pool-slot × variant tables would multiply this.
