"""Offline check of the unit-index / threshold byte path on DISPATCH's shipped UE4.27 shaders (round 008).

Not a UE run. It replays, in float32, the vertex-colour path that DISPATCH's own compiled Slate material vertex shader
uses (constants copied bit-exactly from the shipped DXBC of M_SubtitlePrinting, ShaderArchive-Dispatch_Chunk0, shader map
3210ff19..., VS #3) and the decode the Arabic reveal material performs:

    CPU   row colour L = srgb_to_linear(b/255)  ->  FColor byte via the engine quantizer (4.27 floor(x*255.999) or 5.x round)
    GPU   v = byte/255 ; v = max(v, 6.1035e-5) ; lin = v > 0.04045 ? exp2(2.4*log2(v*0.9478673+0.0521327)) : v*0.0773993
    MAT   s = lin <= 0.0031308 ? lin*12.92 : 1.055*pow(lin, 1/2.4) - 0.055 ; decoded = floor(s*255 + 0.5)

GPU log2/exp2 are approximate (D3D11 allows ~2^-21 relative error) and the interpolated colour of a constant-colour quad
can move by a couple of ULPs, so every pow result and the interpolant are perturbed by up to +-1e-5 relative (about
20x the spec) and +-4 ULP. Pass = every byte 0..255 decodes to itself under every perturbation and both quantizers.

usage: python -I sim_427_vertex_path.py [out.json]
"""
import json
import sys

import numpy as np

f32 = np.float32
# Bit-exact immediates from the shipped DISPATCH vertex shader (D3DDisassemble with hex literals).
VS_MIN = np.frombuffer(bytes.fromhex("06008038"), "<f4")[0]   # 0x38800006
VS_MUL = np.frombuffer(bytes.fromhex("6ea7723f"), "<f4")[0]   # 0x3f72a76e = 1/1.055
VS_ADD = np.frombuffer(bytes.fromhex("1989553d"), "<f4")[0]   # 0x3d558919 = 0.055/1.055
VS_POW = np.frombuffer(bytes.fromhex("9a991940"), "<f4")[0]   # 0x4019999a = 2.4
VS_THR = np.frombuffer(bytes.fromhex("e6ae253d"), "<f4")[0]   # 0x3d25aee6 = 0.04045
VS_LIN = f32(1.0) / f32(12.92)


def srgb_to_lin(s):
    s = f32(s)
    return s / f32(12.92) if s <= f32(0.04045) else f32(((s + f32(0.055)) / f32(1.055)) ** f32(2.4))


def quant_427(lin):
    """FLinearColor::ToFColor(true) as in UE4.x: exact sRGB, then floor(x * 255.999)."""
    x = min(max(f32(lin), f32(0)), f32(1))
    s = x * f32(12.92) if x <= f32(0.0031308) else f32(1.055) * f32(x ** f32(1 / 2.4)) - f32(0.055)
    return int(np.floor(f32(s) * f32(255.999)))


def quant_round(lin):
    """Round-to-nearest quantizer (UE5's stb table targets this result)."""
    x = min(max(f32(lin), f32(0)), f32(1))
    s = x * f32(12.92) if x <= f32(0.0031308) else f32(1.055) * f32(x ** f32(1 / 2.4)) - f32(0.055)
    return int(np.floor(f32(s) * f32(255) + f32(0.5)))


def gpu_vs(byte, rel, ulps):
    v = max(f32(byte) / f32(255), VS_MIN)
    if v > VS_THR:
        lin = f32(np.exp2(VS_POW * np.log2(v * VS_MUL + VS_ADD))) * f32(1 + rel)
    else:
        lin = v * VS_LIN
    for _ in range(abs(ulps)):  # interpolation of a constant across the quad
        lin = np.nextafter(lin, f32(np.inf) if ulps > 0 else f32(-np.inf), dtype=f32)
    return f32(lin)


def mat_decode(lin, rel):
    s = lin * f32(12.92) if lin <= f32(0.0031308) else f32(1.055) * f32(f32(lin ** f32(1 / 2.4)) * f32(1 + rel)) - f32(0.055)
    return s * f32(255) + f32(0.5), int(np.floor(s * f32(255) + f32(0.5)))


def r8b_check(k=10.5, units=37):
    """Fallback R8b: reuse DISPATCH's shipped M_SubtitlePrinting, whose compiled PS computes
    opacity = saturate((VC.b - 0.1) * 1.11). Row colour B = k^-i, Border tint B = k^t, product packed once."""
    wrong = []
    for i in range(units):
        for t in range(-1, units):
            prod = f32(f32(k) ** f32(-i)) * f32(f32(k) ** f32(t)) if t >= 0 else f32(0)
            for r1 in (-1e-5, 0.0, 1e-5):
                b = gpu_vs(quant_427(prod), r1, 0)
                opacity = min(max((float(b) - 0.1) * 1.11, 0.0), 1.0)
                if (opacity > 0.99) != (t >= i) or (t < i and opacity > 0.0):
                    wrong.append({"i": i, "t": t, "opacity": opacity})
    return {"k": k, "units": units, "max_tint_b": float(f32(k) ** f32(units - 1)), "wrong": len(wrong), "pass": not wrong}


def main():
    rels = (-1e-5, 0.0, 1e-5)
    bad, worst_margin = [], 1.0
    for q_name, q in (("ue4_floor_255.999", quant_427), ("round", quant_round)):
        for b in range(256):
            byte = q(srgb_to_lin(b / 255))
            if byte != b:
                bad.append({"quantizer": q_name, "byte": b, "packed": byte})
                continue
            for r1 in rels:
                for u in (-4, 0, 4):
                    lin = gpu_vs(byte, r1, u)
                    for r2 in rels:
                        raw, dec = mat_decode(lin, r2)
                        worst_margin = min(worst_margin, 0.5 - abs(float(raw) - 0.5 - b))
                        if dec != b:
                            bad.append({"quantizer": q_name, "byte": b, "decoded": dec, "rel_vs": r1, "ulps": u, "rel_mat": r2})
    # Colour compensation Col / max(VC, 1e-6) * VC at the smallest possible vertex colour (byte 0 -> VS floor, byte 1).
    comp = {}
    for b in (0, 1):
        vc = gpu_vs(b, 0.0, 0)
        comp[str(b)] = {"vc_linear": float(vc), "col_1_over_vc": float(f32(1) / max(vc, f32(1e-6))),
                        "roundtrip_error": float(abs(f32(f32(1) / max(vc, f32(1e-6))) * vc - f32(1)))}
    out = {
        "label": "OFFLINE SIMULATION of DISPATCH 4.27 shader constants - not a UE run, not in-game",
        "bytes_checked": 256, "quantizers": ["ue4_floor_255.999", "round"],
        "perturbations": {"pow_relative": list(rels), "interpolant_ulps": [-4, 0, 4]},
        "failures": bad, "worst_decode_margin_in_byte_units": worst_margin, "compensation": comp,
        "r8b_fallback_b_channel": r8b_check(),
    }
    out["pass"] = not bad and worst_margin > 0.4 and out["r8b_fallback_b_channel"]["pass"]
    if len(sys.argv) > 1:
        with open(sys.argv[1], "w", encoding="utf-8") as fh:
            json.dump(out, fh, indent=1)
    print(json.dumps({k: v for k, v in out.items() if k != "failures"}, indent=1), "failures:", len(bad))
    assert out["pass"], bad[:5]


if __name__ == "__main__":
    main()
