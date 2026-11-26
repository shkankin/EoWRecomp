// Tests for runtime/nxpkg.c: AES (FIPS-197, SP 800-38A CTR, IEEE 1619 XTS vectors), LZ4 (blocks made by the lz4
// Python module), and with a package: the program NCA's header, keys and first RomFS bytes (compare with
// tools/nca_extract.py). Build and run: tools/test_nxpkg.sh [prod.keys package]
// --update <prod.keys> <base package> <update NSP> <scratch dir>: nx_setup + nx_setup_update into the scratch dir,
// then the patched RomFS section checked against its own hash tree (IVFC: the SHA-256 of each data block is in the
// level above): sampled blocks across the section, read through the update's tables and the base package.
#include "../runtime/nxpkg.c"

static int fails;

// ---- SHA-256 (FIPS 180-4), for the IVFC check
static const uint32_t K256[64] = {
    0x428a2f98, 0x71374491, 0xb5c0fbcf, 0xe9b5dba5, 0x3956c25b, 0x59f111f1, 0x923f82a4, 0xab1c5ed5, 0xd807aa98,
    0x12835b01, 0x243185be, 0x550c7dc3, 0x72be5d74, 0x80deb1fe, 0x9bdc06a7, 0xc19bf174, 0xe49b69c1, 0xefbe4786,
    0x0fc19dc6, 0x240ca1cc, 0x2de92c6f, 0x4a7484aa, 0x5cb0a9dc, 0x76f988da, 0x983e5152, 0xa831c66d, 0xb00327c8,
    0xbf597fc7, 0xc6e00bf3, 0xd5a79147, 0x06ca6351, 0x14292967, 0x27b70a85, 0x2e1b2138, 0x4d2c6dfc, 0x53380d13,
    0x650a7354, 0x766a0abb, 0x81c2c92e, 0x92722c85, 0xa2bfe8a1, 0xa81a664b, 0xc24b8b70, 0xc76c51a3, 0xd192e819,
    0xd6990624, 0xf40e3585, 0x106aa070, 0x19a4c116, 0x1e376c08, 0x2748774c, 0x34b0bcb5, 0x391c0cb3, 0x4ed8aa4a,
    0x5b9cca4f, 0x682e6ff3, 0x748f82ee, 0x78a5636f, 0x84c87814, 0x8cc70208, 0x90befffa, 0xa4506ceb, 0xbef9a3f7,
    0xc67178f2};
#define ROR(x, n) ((x) >> (n) | (x) << (32 - (n)))
static void sha256_block(uint32_t h[8], const uint8_t *p) {
    uint32_t w[64], a[8];
    for (int i = 0; i < 16; i++) w[i] = (uint32_t)p[4 * i] << 24 | p[4 * i + 1] << 16 | p[4 * i + 2] << 8 | p[4 * i + 3];
    for (int i = 16; i < 64; i++) {
        uint32_t s0 = ROR(w[i - 15], 7) ^ ROR(w[i - 15], 18) ^ (w[i - 15] >> 3);
        uint32_t s1 = ROR(w[i - 2], 17) ^ ROR(w[i - 2], 19) ^ (w[i - 2] >> 10);
        w[i] = w[i - 16] + s0 + w[i - 7] + s1;
    }
    memcpy(a, h, 32);
    for (int i = 0; i < 64; i++) {
        uint32_t t1 = a[7] + (ROR(a[4], 6) ^ ROR(a[4], 11) ^ ROR(a[4], 25)) + ((a[4] & a[5]) ^ (~a[4] & a[6])) + K256[i] + w[i];
        uint32_t t2 = (ROR(a[0], 2) ^ ROR(a[0], 13) ^ ROR(a[0], 22)) + ((a[0] & a[1]) ^ (a[0] & a[2]) ^ (a[1] & a[2]));
        memmove(a + 1, a, 28);
        a[4] += t1, a[0] = t1 + t2;
    }
    for (int i = 0; i < 8; i++) h[i] += a[i];
}
static void sha256(const uint8_t *d, size_t n, uint8_t out[32]) {
    uint32_t h[8] = {0x6a09e667, 0xbb67ae85, 0x3c6ef372, 0xa54ff53a, 0x510e527f, 0x9b05688c, 0x1f83d9ab, 0x5be0cd19};
    size_t i = 0;
    for (; i + 64 <= n; i += 64) sha256_block(h, d + i);
    uint8_t t[128] = {0};
    size_t r = n - i;
    memcpy(t, d + i, r), t[r] = 0x80;
    size_t tl = r + 9 <= 64 ? 64 : 128;
    uint64_t bits = (uint64_t)n * 8;
    for (int k = 0; k < 8; k++) t[tl - 1 - k] = (uint8_t)(bits >> (8 * k));
    sha256_block(h, t);
    if (tl == 128) sha256_block(h, t + 64);
    for (int k = 0; k < 8; k++) out[4 * k] = h[k] >> 24, out[4 * k + 1] = h[k] >> 16, out[4 * k + 2] = h[k] >> 8, out[4 * k + 3] = h[k];
}

// the patched RomFS section's data level against the hash level above it
static int test_update(const char *keys, const char *base, const char *update, const char *dir) {
    char why[256] = "", src[1200];
    uint64_t tid = 0;
    if (!nx_setup(base, keys, dir, &tid, why, sizeof why)) { printf("FAIL base setup: %s\n", why); return 1; }
    printf("ok   base %016llx\n", (unsigned long long)tid);
    if (!nx_setup_update(update, keys, dir, &tid, why, sizeof why)) { printf("FAIL update setup: %s\n", why); return 1; }
    printf("ok   update %016llx\n", (unsigned long long)tid);
    char mainp[1300];
    snprintf(mainp, sizeof mainp, "%s/exefs/main", dir);
    FILE *mf = fopen(mainp, "rb");
    uint8_t bid[8] = {0};
    if (mf) fseek(mf, 0x40, SEEK_SET), fread(bid, 1, 8, mf), fclose(mf);
    printf("     main build id ");
    for (int k = 0; k < 8; k++) printf("%02x", bid[k]);
    printf("\n");
    snprintf(src, sizeof src, "%s/romfs.src", dir);
    NxRomfs *r = nx_romfs_open(src, why, sizeof why);
    if (!r) { printf("FAIL open: %s\n", why); return 1; }
    printf("     indirect %d entries, ctrex %d entries, romfs image %llu bytes\n", r->nind, r->nx, (unsigned long long)r->size);
    // the patch's IVFC levels (its own fs header, the RomFS section's)
    Keys ks = {0};
    keys_load(keys, &ks);
    int fd = open(update, O_RDONLY);
    Nca nca;
    if (!nca_header(fd, r->pnca_base, &ks, &nca)) { printf("FAIL header\n"); return 1; }
    const uint8_t *fh = nca.hdr + 0x600;
    uint32_t levels;
    memcpy(&levels, fh + 0x8 + 0xC, 4);
    uint64_t hoff, hsize, doff, dsize;
    uint32_t dorder;
    memcpy(&hoff, fh + 0x8 + 0x10 + (levels - 3) * 0x18, 8), memcpy(&hsize, fh + 0x8 + 0x18 + (levels - 3) * 0x18, 8);
    memcpy(&doff, fh + 0x8 + 0x10 + (levels - 2) * 0x18, 8), memcpy(&dsize, fh + 0x8 + 0x18 + (levels - 2) * 0x18, 8);
    memcpy(&dorder, fh + 0x8 + 0x20 + (levels - 2) * 0x18, 4);
    uint64_t bs = 1ull << dorder, nblk = (dsize + bs - 1) / bs;
    printf("     ivfc: %u levels, data %llx+%llx, block %llu, hashes %llx+%llx\n", levels, (unsigned long long)doff,
           (unsigned long long)dsize, (unsigned long long)bs, (unsigned long long)hoff, (unsigned long long)hsize);
    uint8_t *blk = malloc(bs), want[32], got[32];
    int bad = 0, n = 0, from_base = 0, from_patch = 0;
    uint64_t step = nblk / 3000 ? nblk / 3000 : 1, rnd = 12345;
    for (uint64_t b = 0; b < nblk; b += step) {
        rnd = rnd * 6364136223846793005ull + 1442695040888963407ull;
        uint64_t i = b + (rnd >> 33) % step;
        if (i >= nblk) i = nblk - 1;
        uint64_t len = i == nblk - 1 ? dsize - i * bs : bs;
        memset(blk, 0, bs);
        if (!img_read(r, blk, doff + i * bs, len) || !img_read(r, want, hoff + i * 32, 32)) { bad++; continue; }
        sha256(blk, bs, got);  // (the last block hashed padded with zeros)
        bool same = !memcmp(got, want, 32);
        if (!same && len < bs) { sha256(blk, len, got); same = !memcmp(got, want, 32); }
        bad += !same, n++;
        int32_t lo = 0, hi = r->nind;
        while (hi - lo > 1) { int32_t m = (lo + hi) / 2; if ((uint64_t)r->ind[m].virt <= doff + i * bs) lo = m; else hi = m; }
        if (r->ind[lo].storage) from_patch++; else from_base++;
        if (!same && bad < 5) printf("     block %llu: hash mismatch (storage %d)\n", (unsigned long long)i, r->ind[lo].storage);
    }
    printf("%s ivfc %d sampled blocks (%d from the base game, %d from the update): %d bad\n", bad ? "FAIL" : "ok  ", n,
           from_base, from_patch, bad);
    uint64_t hdr = 0;
    nx_romfs_pread(r, &hdr, 8, 0);
    printf("%s romfs header size %llx\n", hdr == 0x50 ? "ok  " : "FAIL", (unsigned long long)hdr);
    nx_romfs_close(r);
    return bad || hdr != 0x50;
}
static void unhex_s(const char *s, uint8_t *o) { unhex(s, o, 512); }
static void check(const char *what, const uint8_t *got, const char *want_hex) {
    uint8_t w[256];
    size_t n = strlen(want_hex) / 2;
    unhex_s(want_hex, w);
    bool ok = !memcmp(got, w, n);
    printf("%s %s\n", ok ? "ok  " : "FAIL", what);
    fails += !ok;
}

int main(int argc, char **argv) {
    if (argc == 6 && !strcmp(argv[1], "--update")) return test_update(argv[2], argv[3], argv[4], argv[5]);
    uint8_t key[32], b[512];
    unhex_s("000102030405060708090a0b0c0d0e0f", key);
    unhex_s("00112233445566778899aabbccddeeff", b);
    uint8_t rk[176];
    aes_expand(key, rk);
    aes_encrypt_block(rk, b);
    check("aes encrypt (FIPS-197 C.1)", b, "69c4e0d86a7b0430d8cdb78070b4c55a");
    nx_aes128_ecb_decrypt(key, b, 16);
    check("aes decrypt", b, "00112233445566778899aabbccddeeff");

    uint8_t iv[16];
    unhex_s("2b7e151628aed2a6abf7158809cf4f3c", key);
    unhex_s("f0f1f2f3f4f5f6f7f8f9fafbfcfdfeff", iv);
    unhex_s("6bc1bee22e409f96e93d7e117393172aae2d8a571e03ac9c9eb76fac45af8e5130c81c46a35ce411e5fbc1191a0a52ef", b);
    nx_aes128_ctr(key, iv, b, 45);  // (a partial last block)
    check("aes ctr (SP 800-38A F.5.1)", b, "874d6191b620e3261bef6864990db6ce9806f66b7970fdff8617187bb9fffdff5ae4df3edbd5d35e5b4f0902");

    memset(key, 0, 32);
    memset(b, 0, sizeof b);
    unhex_s("917cf69ebd68b2ec9b9fe9a3eadda692cd43d2f59598ed858c02c2652fbf922e", b);
    aes_xts_decrypt(key, b, 0x200, 0);
    check("aes xts (IEEE 1619 vector 1)", b, "0000000000000000000000000000000000000000000000000000000000000000");

    for (int i = 1; i + 1 < argc && !strcmp(argv[i], "--lz4"); i += 2) {  // --lz4 <file>: [u32 raw size][raw][block]
        FILE *f = fopen(argv[i + 1], "rb");
        uint32_t rn, cn;
        fread(&rn, 4, 1, f), fread(&cn, 4, 1, f);
        uint8_t *raw = malloc(rn), *comp = malloc(cn), *out = malloc(rn);
        fread(raw, 1, rn, f), fread(comp, 1, cn, f);
        fclose(f);
        int n = nx_lz4_decompress(comp, (int)cn, out, (int)rn);
        bool ok = n == (int)rn && !memcmp(raw, out, rn);
        printf("%s lz4 %s (%u -> %u)\n", ok ? "ok  " : "FAIL", argv[i + 1], cn, rn);
        fails += !ok;
        free(raw), free(comp), free(out);
    }

    if (argc >= 3 && strcmp(argv[1], "--lz4")) {  // <prod.keys> <package>: header, key, first RomFS bytes
        Keys ks = {0};
        keys_load(argv[1], &ks);
        int fd = open(argv[2], O_RDONLY);
        Entries files = {0};
        read_fs0(fd, 0, &files);
        for (int i = 0; i < files.n; i++) {
            Nca nca;
            if (!nca_header(fd, files.e[i].off, &ks, &nca)) { printf("     %s: not decrypted\n", files.e[i].name); continue; }
            uint64_t tid;
            memcpy(&tid, nca.hdr + 0x210, 8);
            printf("     %s: NCA3 type %d title %016llx\n", files.e[i].name, nca.hdr[0x205], (unsigned long long)tid);
            if (nca.hdr[0x205] != 0) continue;
            int gen = nca.hdr[0x206] > nca.hdr[0x220] ? nca.hdr[0x206] : nca.hdr[0x220];
            char kn[48];
            snprintf(kn, sizeof kn, "key_area_key_application_%02x", gen ? gen - 1 : 0);
            uint8_t area[0x40];
            memcpy(area, nca.hdr + 0x300, 0x40);
            nx_aes128_ecb_decrypt(key_get(&ks, kn, 16), area, 0x40);
            Section s;
            section_info(&nca, 1, &s);
            uint8_t first[32];
            section_read(fd, nca.base, &s, area + 0x20, first, s.data_off, 32);
            printf("     romfs section at %llx, data %llx, first bytes: ", (unsigned long long)s.off, (unsigned long long)s.data_off);
            for (int k = 0; k < 32; k++) printf("%02x", first[k]);
            printf("\n");
        }
    }
    printf(fails ? "%d FAILED\n" : "all passed\n", fails);
    return fails != 0;
}
