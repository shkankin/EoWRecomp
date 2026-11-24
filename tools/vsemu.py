"""Run a translated vertex shader on the CPU over a dumped draw: which vertices land where, and why.

Usage: vsemu.py <vsdump dir> <shader.glsl> [--trace N] [--half]

<vsdump dir>: what EOWRECOMP_VS_DUMP=<vs>[:<count>] wrote (with EOWRECOMP_DEBUG_FRAME): meta.txt, vbuf<s>.bin,
idx.bin, cb<k>.bin. <shader.glsl>: the same program's GLSL (EOWRECOMP_SAVE_MSL=1 -> build/glsl/<vs>_vs.glsl).
The GLSL main() is compiled as C++ (the translator's output is integer / float code over uint registers) with this
file's prelude in place of the GLSL helpers, and run once per vertex the indices use. Prints each vertex's clip
position and the ones far outside the view; --trace N writes vertex N's register file after every instruction.
--half rounds HADD2 / HMUL2 / HFMA2 results to fp16 as Maxwell computes them (the GLSL keeps fp32).
Needs build/zig-full/zig (c++).
"""
import argparse
import os
import re
import struct
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

PRELUDE = r'''
#include <cmath>
#include <cstdint>
#include <cstdio>
#include <cstring>
#include <algorithm>
namespace sh {
typedef uint32_t uint;
struct vec2 { float x, y; vec2() : x(0), y(0) {} vec2(float a) : x(a), y(a) {} vec2(float a, float b) : x(a), y(b) {}
  float &operator[](int i) { return i ? y : x; } };
static vec2 operator+(vec2 a, vec2 b) { return vec2(a.x + b.x, a.y + b.y); }
static vec2 operator-(vec2 a, vec2 b) { return vec2(a.x - b.x, a.y - b.y); }
static vec2 operator*(vec2 a, vec2 b) { return vec2(a.x * b.x, a.y * b.y); }
static vec2 operator-(vec2 a) { return vec2(-a.x, -a.y); }
struct vec4 { float v[4]; vec4() { v[0] = v[1] = v[2] = 0; v[3] = 1; } vec4(float a, float b, float c, float d) { v[0] = a; v[1] = b; v[2] = c; v[3] = d; }
  float &operator[](int i) { return v[i]; } };
struct uvec4 { uint v[4]; uint &operator[](int i) { return v[i]; } };
static uint as_u(float x) { uint u; memcpy(&u, &x, 4); return u; }
static uint as_u(uint x) { return x; }
static uint as_u(int x) { return (uint)x; }
static float as_f(uint x) { float f; memcpy(&f, &x, 4); return f; }
static float as_f(int x) { return as_f((uint)x); }
static float as_f(float x) { return x; }
static int as_i(uint x) { return (int)x; }
static int as_i(float x) { return (int)as_u(x); }
static uint floatBitsToUint(float x) { return as_u(x); }
static int floatBitsToInt(float x) { return (int)as_u(x); }
static float uintBitsToFloat(uint x) { return as_f(x); }
static float intBitsToFloat(int x) { return as_f((uint)x); }
static uint min(uint a, uint b) { return a < b ? a : b; }
static uint max(uint a, uint b) { return a > b ? a : b; }
static int min(int a, int b) { return a < b ? a : b; }
static int max(int a, int b) { return a > b ? a : b; }
static float min(float a, float b) { return std::fmin(a, b); }
static float max(float a, float b) { return std::fmax(a, b); }
static float clamp(float x, float a, float b) { return std::fmin(std::fmax(x, a), b); }
static float abs(float x) { return std::fabs(x); }
static int abs(int x) { return x < 0 ? -x : x; }
static float fma(float a, float b, float c) { return std::fma(a, b, c); }
static vec2 fma(vec2 a, vec2 b, vec2 c) { return vec2(std::fma(a.x, b.x, c.x), std::fma(a.y, b.y, c.y)); }
static float inversesqrt(float x) { return 1.0f / std::sqrt(x); }
static bool isnan(float x) { return std::isnan(x); }
static float floor(float x) { return std::floor(x); }
static int bitfieldExtract(int v, int off, int bits) { if (!bits) return 0; return (int)(((int64_t)v << (64 - off - bits)) >> (64 - bits)); }
static uint bitfieldExtract(uint v, int off, int bits) { if (!bits) return 0; return (uint)((v >> off) & (bits == 32 ? 0xFFFFFFFFu : ((1u << bits) - 1))); }
static uint bitfieldInsert(uint base, uint ins, int off, int bits) { uint m = (bits == 32 ? 0xFFFFFFFFu : ((1u << bits) - 1)) << off; return (base & ~m) | ((ins << off) & m); }
static uint bitfieldReverse(uint v) { uint r = 0; for (int i = 0; i < 32; i++) r |= ((v >> i) & 1u) << (31 - i); return r; }
static int findMSB(uint v) { return v ? 31 - __builtin_clz(v) : -1; }
static int findMSB(int v) { return findMSB((uint)(v < 0 ? ~v : v)); }
static int bitCount(uint v) { return __builtin_popcount(v); }
static void umulExtended(uint a, uint b, uint &hi, uint &lo) { uint64_t p = (uint64_t)a * b; hi = (uint)(p >> 32); lo = (uint)p; }
static void imulExtended(int a, int b, int &hi, int &lo) { int64_t p = (int64_t)a * b; hi = (int)(p >> 32); lo = (int)p; }
static int sx8(uint v) { return (int8_t)v; } static int sx8(int v) { return (int8_t)v; }
static int sx16(uint v) { return (int16_t)v; } static int sx16(int v) { return (int16_t)v; }
static float mw_saturate(float x) { return isnan(x) ? 0.0f : clamp(x, 0.0f, 1.0f); }
static float mw_fmin(float a, float b) { return isnan(a) ? b : (isnan(b) ? a : std::fmin(a, b)); }
static float mw_fmax(float a, float b) { return isnan(a) ? b : (isnan(b) ? a : std::fmax(a, b)); }
static uint mw_clz(uint v) { return v == 0u ? 32u : (uint)__builtin_clz(v); }
static uint mw_popcount(uint v) { return (uint)__builtin_popcount(v); }
static uint mw_mulhi(uint a, uint b) { return (uint)(((uint64_t)a * b) >> 32); }
static int mw_mulhi(int a, int b) { return (int)(((int64_t)a * b) >> 32); }
static uint brev32(uint v) { return bitfieldReverse(v); }
static uint flo_sh(uint msb) { return msb == 0xFFFFFFFFu ? msb : 31u - msb; }
static uint bfe_u(uint v, uint ctl) { uint pos = ctl & 0xFFu, len = (ctl >> 8) & 0xFFu; if (len == 0u || pos >= 32u) return 0u; return bitfieldExtract(v, (int)pos, (int)min(len, 32u - pos)); }
static uint bfe_s(uint v, uint ctl) { uint pos = ctl & 0xFFu, len = (ctl >> 8) & 0xFFu; if (len == 0u) return 0u; if (pos >= 32u) return ((int)v < 0) ? 0xFFFFFFFFu : 0u; uint l = min(len, 32u - pos); return (uint)(((int64_t)(int)v << (64 - pos - l)) >> (64 - l)); }
static uint bfi(uint ins, uint ctl, uint base) { uint pos = ctl & 0xFFu, len = (ctl >> 8) & 0xFFu; if (len == 0u || pos >= 32u) return base; return bitfieldInsert(base, ins, (int)pos, (int)min(len, 32u - pos)); }
static uint prmt(uint a, uint b, uint sel) { uint r = 0u; for (uint i = 0u; i < 4u; i++) { uint s = (sel >> (i * 4u)) & 7u; uint bt = s < 4u ? (a >> (s * 8u)) & 0xFFu : (b >> ((s - 4u) * 8u)) & 0xFFu; r |= bt << (i * 8u); } return r; }
// fp16
static float h2f(uint h) { uint s = (h & 0x8000u) << 16, e = (h >> 10) & 0x1Fu, m = h & 0x3FFu; if (e == 0u) { float d = (float)m * 5.9604644775390625e-8f; return s ? -d : d; } if (e == 31u) return as_f(s | 0x7F800000u | (m << 13)); return as_f(s | ((e + 112u) << 23) | (m << 13)); }
static uint f2h(float f) {  // round to nearest even, overflow -> inf (packHalf2x16)
  uint x = as_u(f), s = (x >> 16) & 0x8000u; int e = (int)((x >> 23) & 0xFF) - 127 + 15; uint m = x & 0x7FFFFFu;
  if (((x >> 23) & 0xFF) == 0xFF) return s | 0x7C00u | (m ? 0x200u : 0u);
  if (e >= 31) return s | 0x7C00u;
  if (e <= 0) { if (e < -10) return s; m |= 0x800000u; uint sh = (uint)(14 - e); uint r = m >> sh, rem = m & ((1u << sh) - 1), half = 1u << (sh - 1); if (rem > half || (rem == half && (r & 1))) r++; return s | r; }
  uint r = m >> 13, rem = m & 0x1FFFu; uint h = s | ((uint)e << 10) | r; if (rem > 0x1000u || (rem == 0x1000u && (r & 1))) h++; return h; }
static bool g_half;  // --half: HADD2 / HMUL2 / HFMA2 results rounded to fp16
static float hq(float f) { return g_half ? h2f(f2h(f)) : f; }
static vec2 unpack_h2(uint v) { return vec2(h2f(v & 0xFFFFu), h2f(v >> 16)); }
static vec2 hx(uint v, uint swz) { if (swz == 1u) return vec2(as_f(v)); vec2 h = unpack_h2(v); return swz == 2u ? vec2(h.x, h.x) : (swz == 3u ? vec2(h.y, h.y) : h); }
static uint packHalf2x16(vec2 v) { return f2h(v.x) | (f2h(v.y) << 16); }
static uint hpack(vec2 r, uint merge, uint old) { if (merge == 1u) return as_u(hq(r.x)); uint lo = f2h(r.x), hi = f2h(r.y); if (merge == 2u) return (old & 0xFFFF0000u) | lo; if (merge == 3u) return (old & 0xFFFFu) | (hi << 16); return lo | (hi << 16); }
static float fswzadd(float a, float b, uint swz, uint lane) { uint m = (swz >> ((lane & 3u) * 2u)) & 3u; float ma = m == 1u ? -1.0f : (m == 3u ? 0.0f : 1.0f); float mb = m == 2u ? -1.0f : 1.0f; return a * ma + b * mb; }
'''


def load_meta(d):
    meta = {'attr': {}, 'vbuf': {}}
    for line in open(os.path.join(d, 'meta.txt')):
        f = line.split()
        if f[0] == 'attr':
            meta['attr'][int(f[1])] = dict(fmt=int(f[3], 16), stream=int(f[5]), offset=int(f[7]), stride=int(f[9]))
        elif f[0] == 'vbuf':
            meta['vbuf'][int(f[1])] = int(f[3])
        else:
            meta[f[0]] = f[1]
    return meta


def snorm(v, bits):
    m = (1 << (bits - 1)) - 1
    if v >= 1 << (bits - 1):
        v -= 1 << bits
    return max(v / m, -1.0)


def decode(fmt, b):
    """(4 components, is_int) of one attribute value; (0, 0, 0, 1) for an unbound one."""
    if fmt == 0:
        return (0.0, 0.0, 0.0, 1.0), False
    if fmt == 0x22:  # RGB32F
        return struct.unpack_from('<3f', b) + (1.0,), False
    if fmt == 0x2E:
        return struct.unpack_from('<4f', b), False
    if fmt == 0x16:
        return struct.unpack_from('<2f', b) + (0.0, 1.0), False
    if fmt == 0x0A:
        return struct.unpack_from('<f', b) + (0.0, 0.0, 1.0), False
    if fmt == 0x13:  # RG16 SNORM
        x, y = struct.unpack_from('<2H', b)
        return (snorm(x, 16), snorm(y, 16), 0.0, 1.0), False
    if fmt == 0x12:  # RG16 UNORM
        x, y = struct.unpack_from('<2H', b)
        return (x / 65535, y / 65535, 0.0, 1.0), False
    if fmt == 0x2A:  # RGBA16 UNORM
        return tuple(c / 65535 for c in struct.unpack_from('<4H', b)), False
    if fmt == 0x2B:  # RGBA16 SNORM
        return tuple(snorm(c, 16) for c in struct.unpack_from('<4H', b)), False
    if fmt == 0x24:  # RGBA8 UNORM
        return tuple(c / 255 for c in b[:4]), False
    if fmt == 0x11:  # RG16F
        return tuple(struct.unpack_from('<2e', b)) + (0.0, 1.0), False
    if fmt == 0x29:
        return tuple(struct.unpack_from('<4e', b)), False
    if fmt == 0x69:  # RGB10A2 SNORM
        v = struct.unpack_from('<I', b)[0]
        return (snorm(v & 0x3FF, 10), snorm((v >> 10) & 0x3FF, 10), snorm((v >> 20) & 0x3FF, 10), snorm(v >> 30, 2)), False
    if fmt == 0x03:  # R8UI
        return (b[0], 0, 0, 1), True
    if fmt == 0x27:  # RGBA8UI
        return tuple(b[:4]), True
    raise SystemExit(f'attribute format {fmt:#x}: add it to decode()')


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('dump')
    ap.add_argument('glsl')
    ap.add_argument('--trace', type=int, default=-1)
    ap.add_argument('--half', action='store_true')
    ap.add_argument('--far', type=float, default=1.0, help='|ndc| that counts as off the view')
    a = ap.parse_args()
    meta = load_meta(a.dump)
    src = open(a.glsl).read()
    # declarations the body uses: inputs, cbufs, gmem
    decls, ins = [], []
    for m in re.finditer(r'uniform CB(\d+) \{ uvec4 cb\d+\[(\d+)\]; \};', src):
        decls.append(f'static uvec4 cb{m[1]}[{m[2]}];')
    for m in re.finditer(r'layout\(location = (\d+)\) in (u?)vec4 a\d+;', src):
        ins.append((int(m[1]), m[2] == 'u'))
        decls.append(f'static {"uvec4" if m[2] else "vec4"} a{m[1]};')
    outs = [int(m[1]) for m in re.finditer(r'layout\(location = (\d+)\) out vec4 v\d+;', src)]
    decls += [f'static vec4 v{o};' for o in outs]
    body = src[src.index('void main()'):]
    body = body.replace('void main()', 'static void run(FILE *trace)', 1)
    body = re.sub(r'#define cbr.*', '', body)
    body = re.sub(r'\b(gl_Position|v\d+)\.([xyzw])\b', lambda m: f'{m[1]}[{"xyzw".index(m[2])}]', body)
    if a.trace >= 0:  # register file after each instruction
        body = re.sub(r'(\n    // pc ([0-9a-f]+): [0-9a-f]+\n)',
                      lambda m: m[1] + f'    if (trace) dump_regs(trace, 0x{m[2]});\n', body)
    nreg = max(int(r) for r in re.findall(r'\buint r(\d+) = 0u;', body)) + 1
    regs = ', '.join(f'r{i}' for i in range(nreg))
    dump_regs = ('#define dump_regs(f, pc) do { uint rr_[] = {' + regs + '}; fprintf(f, "%llx", (unsigned long long)(pc)); '
                 'for (unsigned i_ = 0; i_ < sizeof rr_ / 4; i_++) fprintf(f, " %08x", rr_[i_]); fprintf(f, "\\n"); } while (0)\n')
    cpp = PRELUDE + '\n#define cbr(cb, off) cb[min((uint)((off) >> 4), (uint)(sizeof(cb) / 16 - 1))].v[((off) >> 2) & 3u]\n'
    cpp += '\n'.join(decls) + '\nstatic struct { uint w[1]; } gmem_;\nstatic vec4 gl_Position; static int gl_InstanceIndex, gl_VertexIndex;\n'
    cpp += dump_regs + body + '\n}  // namespace sh\nusing namespace sh;\n'
    # driver: read cbufs + per-vertex inputs from files, run, print outputs
    cpp += r'''
static void load(void *dst, size_t cap, const char *path) { FILE *f = fopen(path, "rb"); if (!f) return; fread(dst, 1, cap, f); fclose(f); }
int main(int argc, char **argv) {
  g_half = argc > 4 && argv[4][0] == '1';
  char p[1024];
'''
    for m in re.finditer(r'uniform CB(\d+) \{', src):
        cpp += f'  snprintf(p, sizeof p, "%s/cb{m[1]}.bin", argv[1]); load(cb{m[1]}, sizeof cb{m[1]}, p);\n'
    cpp += '  FILE *in = fopen(argv[2], "rb"); int tv = atoi(argv[3]); float buf[64]; int vi;\n'
    cpp += '  while (fread(&vi, 4, 1, in) == 1 && fread(buf, 4, ' + str(4 * len(ins)) + ', in) == ' + str(4 * len(ins)) + ') {\n'
    for k, (loc, is_u) in enumerate(ins):
        for c in range(4):
            if is_u:
                cpp += f'    a{loc}[{c}] = (uint)buf[{4 * k + c}];\n'
            else:
                cpp += f'    a{loc}[{c}] = buf[{4 * k + c}];\n'
    cpp += '    gl_VertexIndex = vi; gl_InstanceIndex = 0; FILE *tr = vi == tv ? stdout : NULL;\n'
    cpp += '    run(tr);\n    printf("v %d %.6g %.6g %.6g %.6g\\n", vi, gl_Position[0], gl_Position[1], gl_Position[2], gl_Position[3]);\n  }\n  return 0;\n}\n'
    work = os.path.join(a.dump, 'emu')
    os.makedirs(work, exist_ok=True)
    open(os.path.join(work, 'vs.cpp'), 'w').write(cpp.replace('#include <cmath>', '#include <cmath>\n#include <cstdlib>', 1))
    exe = os.path.join(work, 'vs')
    zig = os.path.join(ROOT, 'build', 'zig-full', 'zig')
    r = subprocess.run([zig, 'c++', '-O0' if a.trace >= 0 else '-O1', '-w', '-ffp-contract=off', '-o', exe, os.path.join(work, 'vs.cpp')],
                       capture_output=True, text=True)
    if r.returncode:
        sys.exit(r.stderr[:4000])
    # the vertices the indices use, decoded
    vb = {s: open(os.path.join(a.dump, f'vbuf{s}.bin'), 'rb').read() for s in meta['vbuf']}
    count, itype = int(meta['count']), int(meta['itype'])
    if meta['indexed'] == '1':
        ib = open(os.path.join(a.dump, 'idx.bin'), 'rb').read()
        idx = struct.unpack_from('<%d%s' % (count, 'H' if itype == 1 else 'I' if itype == 2 else 'B'), ib)
    else:
        idx = range(count)
    used = sorted(set(idx))
    with open(os.path.join(work, 'in.bin'), 'wb') as f:
        for v in used:
            f.write(struct.pack('<i', v))
            for loc, is_u in ins:
                at = meta['attr'].get(loc, dict(fmt=0, stream=0, offset=0, stride=0))
                off = v * at['stride'] + at['offset']
                comps, _ = decode(at['fmt'], vb.get(at['stream'], b'')[off:off + 16] if at['fmt'] else b'')
                f.write(struct.pack('<4f', *[float(c) for c in comps]))
    out = subprocess.run([exe, a.dump, os.path.join(work, 'in.bin'), str(a.trace), '1' if a.half else '0'],
                         capture_output=True, text=True).stdout
    pos = {}
    for line in out.splitlines():
        if line.startswith('v '):
            _, v, x, y, z, w = line.split()
            pos[int(v)] = tuple(map(float, (x, y, z, w)))
        elif a.trace >= 0:
            print(line)
    far = [(v, p) for v, p in pos.items() if not (p[3] > 1e-6 and all(abs(p[i] / p[3]) < a.far for i in range(2)))]
    print(f'{len(pos)} vertices run, {len(far)} land far outside the view (|ndc| >= {a.far}, w <= 0 or NaN)')
    for v, p in far[:12]:
        print(f'  v{v}: clip {p[0]:.4g} {p[1]:.4g} {p[2]:.4g} {p[3]:.4g}')
    if pos:
        ok = [p for p in pos.values() if p[3] > 1e-6]
        if ok:
            print('ndc x %.3f..%.3f  y %.3f..%.3f' % (min(p[0] / p[3] for p in ok), max(p[0] / p[3] for p in ok),
                                                     min(p[1] / p[3] for p in ok), max(p[1] / p[3] for p in ok)))


if __name__ == '__main__':
    main()
