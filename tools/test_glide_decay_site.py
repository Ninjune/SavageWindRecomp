"""tools/patches.py's glide OverSpeedDec decay patch without game files: the site's four guest words are synthesized,
the patch takes its exact fsub word and emits an rt_glide_overspeed_dec call, and a wrong opcode is refused.

The words below are the 1.9.0 pattern at 0x7000c866e8 (task 05): ldr x / ldr s / fsub s0,s0,s1 / str s. A tiny fake
NSO holds just those words, so no extracted main module is needed.

Usage: uv run --no-project --with lz4 --with capstone --with unicorn python tools/test_glide_decay_site.py
"""
import struct
import sys
from types import SimpleNamespace

import game_sites as gs
import patches

CHECKS = 0

SITE_ADDRESS = 0x7000c866e8  # base of the four-word pattern
FSUB_ADDRESS = 0x7000c866f0  # the fsub the patch replaces (pattern index 2)
WORDS = (0xf9403668, 0xbd400101, 0x1e213800, 0xbd181e80)
FSUB = 0x1e213800  # fsub s0, s0, s1
WRONG = 0xd503201f  # nop: a deliberately wrong opcode at the same address


def check(cond, what):
    global CHECKS
    if not cond:
        sys.exit(f'FAIL: {what}')
    CHECKS += 1


def fake_gen(words):
    """Just enough of gen for patches._word: the four little-endian words at the site base."""
    return SimpleNamespace(base=SITE_ADDRESS, nso=SimpleNamespace(image=struct.pack('<4I', *words)))


def main():
    # The registered site matches the synthesized words and points at the fsub.
    site = next((s for s in gs.SITES if s.name == 'glide_overspeed_dec'), None)
    check(site is not None, 'glide_overspeed_dec site is registered')
    check(site.pattern == 'f9403668 bd400101 1e213800 bd181e80', 'site pattern is the exact guest words')
    check(site.at == 2, 'site points at the third word (fsub s0,s0,s1)')
    check(gs.KNOWN['1.9.0'].get('glide_overspeed_dec') == FSUB_ADDRESS, 'site resolves to the 1.9.0 fsub address')
    check(WORDS[site.at] == FSUB, 'synthesized fsub word is 1e213800')

    code = patches.PATCHES['glide_overspeed_dec'](fake_gen(WORDS), FSUB_ADDRESS)
    check('rt_glide_overspeed_dec' in code, 'emitted C references rt_glide_overspeed_dec')
    check(f'{FSUB_ADDRESS:#x}' in code, 'emitted C marks the guest site')
    check('c->v[0]' in code and 'c->v[1]' in code, 'emitted C passes s0 (v) and s1 (dec) through v0/v1')

    # A wrong opcode at the same address is refused loudly.
    wrong_words = list(WORDS)
    wrong_words[site.at] = WRONG
    try:
        patches.PATCHES['glide_overspeed_dec'](fake_gen(wrong_words), FSUB_ADDRESS)
        check(False, 'a wrong opcode is refused')
    except AssertionError as e:
        check(hex(WRONG) in str(e), 'wrong opcode refused with its word in the message')
    print(f'ok: {CHECKS} checks')


if __name__ == '__main__':
    main()
