/* Synthetic check of the task-05 glide-decay decision logic. The real helper lives in runtime/hle/framepace.c and
 * drags in the whole runtime, so its option and its subtraction are mirrored here; keep the two in sync with
 * rt_glide_overspeed_dec. No game files, generated code or saves are needed. */
#include <assert.h>
#include <stdio.h>

static int glide_option;
static float frame_ratio;

/* Mirrors rt_glide_overspeed_dec (runtime/hle/framepace.c). */
static float glide_overspeed_dec(float v, float dec) {
    return glide_option ? v - dec * frame_ratio : v - dec;
}

static void reset(float ratio, int option) {
    frame_ratio = ratio;
    glide_option = option;
}

int main(void) {
    const float v = 10.0f, dec = 4.0f;
    /* Option off: the guest subtraction happens at every frame rate. */
    const float ratios[] = {0.125f, 0.25f, 0.5f, 0.75f, 1.0f, 1.25f, 1.5f};
    for (unsigned i = 0; i < sizeof ratios / sizeof ratios[0]; i++) {
        reset(ratios[i], 0);
        assert(glide_overspeed_dec(v, dec) == v - dec);
    }

    /* Option on at 30 fps (ratio 1): still the guest subtraction. */
    reset(1.0f, 1);
    assert(glide_overspeed_dec(v, dec) == v - dec);

    /* Above 30 fps: the subtraction scales with the frame's length in console frames. */
    reset(0.5f, 1);
    assert(glide_overspeed_dec(v, dec) == v - 0.5f * dec);
    reset(0.125f, 1);
    assert(glide_overspeed_dec(v, dec) == v - 0.125f * dec);

    puts("Glide decay decision logic: PASS (in-game effect unverified)");
    return 0;
}
