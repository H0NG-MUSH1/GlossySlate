/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * This program is free software; you can redistribute it and/or
 * modify it under the terms of the GNU General Public License
 * as published by the Free Software Foundation; either version 2
 * of the License, or (at your option) any later version.
 *
 * This software is distributed on an "AS IS" basis, WITHOUT WARRANTY OF ANY
 * KIND, either express or implied.
 *
 ****************************************************************************/

/*
 * Album art effects of %Cd(tilt, perspective, reflection height,
 * reflection opacity, corner radius) on the iPod 6G, like the cover of the
 * original firmware:
 *
 *   - the cover turned about its vertical middle by tilt degrees (positive:
 *     the right edge goes back), seen from perspective pixels away
 *   - rounded corners of radius pixels, which turn with the cover
 *   - a mirrored copy below it, refl_height pixels high, which fades from
 *     refl_opacity percent at the cover to nothing
 *
 * The picture is made once per cover (album art handle) into a buffer that
 * the parser reserved in the skin buffer for the %Cl box, as RGB565 pixels
 * with 8 bit coverage. Drawing blends it row by row with the backdrop under
 * it, with an ordered dither to RGB565: the 4 bit alpha of the skin engine
 * left a reflection of 34 % only 5 steps, broad visible bands. Integer
 * maths only: 16.16 fixed point, sin and cos with 14 fractional bits.
 */

#include "config.h"
#if defined(IPOD_6G) && defined(HAVE_ALBUMART) && !defined(__PCTOOL__)
#include <stdint.h>
#include <string.h>
#include "system.h"
#include "lcd.h"
#include "screen_access.h"
#include "fixedpoint.h"
#include "wps_internals.h"
#include "skin_albumart_fx.h"

#define ONE 65536

#if LCD_STRIDEFORMAT == VERTICAL_STRIDE
#error "skin_aa_fx_draw() reads the backdrop by rows"
#endif

/* perspective scale d / (d + x sin) at x (16.16) from the middle of the
 * cover, 16.16; 0 if x is behind the eye */
static int64_t fx_scale(const struct skin_aa_fx *fx, int64_t x16)
{
    if (fx->tilt == 0)
        return ONE;
    int64_t d14 = (int64_t)fx->perspective * 16384;
    int64_t den = d14 + ((x16 * fp14_sin(fx->tilt)) >> 16);
    if (den <= 0)
        return 0;
    return (d14 << 16) / den;
}

/* pixels the turned cover reaches beyond its box at each side (mx) and
 * above and below (over) */
static void fx_margins(const struct skin_aa_fx *fx, int w, int h,
                       int *mx, int *over)
{
    int64_t s = MAX(fx_scale(fx, -((int64_t)w << 15)),
                    fx_scale(fx, (int64_t)w << 15));
    if (s <= 0)
        s = ONE;
    int64_t half_w = ((((int64_t)w << 15) * fp14_cos(fx->tilt)) >> 14) * s
                     >> 16;
    int64_t half_h = ((int64_t)h << 15) * s >> 16;
    *mx = MAX(0, (int)((half_w - ((int64_t)w << 15) + ONE - 1) >> 16));
    *over = MAX(0, (int)((half_h - ((int64_t)h << 15) + ONE - 1) >> 16));
}

static void fx_layout(const struct skin_aa_fx *fx, int w, int h,
                      int *mx, int *over, int *pw, int *ph,
                      size_t *alpha_offset, size_t *size)
{
    fx_margins(fx, w, h, mx, over);
    *pw = w + 2 * *mx;
    *ph = h + 2 * *over + fx->refl_height;
    *alpha_offset = ALIGN_UP(*pw * *ph * sizeof(fb_data), 4);
    *size = *alpha_offset + *pw * *ph; /* one byte of coverage per pixel */
}

size_t skin_aa_fx_size(const struct skin_aa_fx *fx, int width, int height)
{
    int mx, over, pw, ph;
    size_t alpha_offset, size;
    if (width <= 0 || height <= 0)
        return 0;
    fx_layout(fx, width, height, &mx, &over, &pw, &ph, &alpha_offset, &size);
    return size;
}

static uint32_t isqrt64(uint64_t v)
{
    uint64_t res = 0, bit = (uint64_t)1 << 62;
    while (bit > v)
        bit >>= 2;
    while (bit)
    {
        if (v >= res + bit)
        {
            v -= res + bit;
            res = (res >> 1) + bit;
        }
        else
            res >>= 1;
        bit >>= 2;
    }
    return (uint32_t)res;
}

/* coverage (16.16) of the cover at source point u, v by its round corners */
static int32_t fx_corner(const struct skin_aa_fx *fx, int w, int h,
                         int32_t u, int32_t v)
{
    if (fx->radius <= 0)
        return ONE;
    int32_t r = fx->radius << 16, du = 0, dv = 0;
    if (u < r)
        du = r - u;
    else if (u > (w << 16) - r)
        du = u - ((w << 16) - r);
    if (v < r)
        dv = r - v;
    else if (v > (h << 16) - r)
        dv = v - ((h << 16) - r);
    if (du <= 0 || dv <= 0)
        return ONE;
    int32_t dist = isqrt64((uint64_t)du * du + (uint64_t)dv * dv);
    return MIN(ONE, MAX(0, r - dist + ONE / 2));
}

/* bilinear sample of the source at u, v (16.16, pixel middles at .5) */
static fb_data fx_sample(const fb_data *src, int stride, int w, int h,
                         int32_t u, int32_t v)
{
    int32_t fu = u - ONE / 2, fv = v - ONE / 2;
    int x0 = fu >> 16, y0 = fv >> 16;
    int ax = (fu >> 8) & 0xff, ay = (fv >> 8) & 0xff;
    int x1 = x0 + 1, y1 = y0 + 1;
    x0 = MIN(MAX(x0, 0), w - 1);
    x1 = MIN(MAX(x1, 0), w - 1);
    y0 = MIN(MAX(y0, 0), h - 1);
    y1 = MIN(MAX(y1, 0), h - 1);
    unsigned p[4] = { src[y0 * stride + x0], src[y0 * stride + x1],
                      src[y1 * stride + x0], src[y1 * stride + x1] };
    int wt[4] = { (256 - ax) * (256 - ay), ax * (256 - ay),
                  (256 - ax) * ay, ax * ay };
    unsigned r = 0, g = 0, b = 0;
    for (int i = 0; i < 4; i++)
    {
        r += (p[i] >> 11) * wt[i];
        g += ((p[i] >> 5) & 0x3f) * wt[i];
        b += (p[i] & 0x1f) * wt[i];
    }
    r = (r + 32768) >> 16;
    g = (g + 32768) >> 16;
    b = (b + 32768) >> 16;
    return (fb_data)((r << 11) | (g << 5) | b);
}

static void fx_render(const struct skin_aa_fx *fx, unsigned char *buf,
                      const fb_data *src, int stride, int w, int h)
{
    int mx, over, pw, ph;
    size_t alpha_offset, size;
    fx_layout(fx, w, h, &mx, &over, &pw, &ph, &alpha_offset, &size);

    fb_data *pix = (fb_data *)buf;
    unsigned char *alpha = buf + alpha_offset;
    const int64_t c = fp14_cos(fx->tilt), s = fp14_sin(fx->tilt);
    const int64_t d = fx->perspective;
    const int32_t refl = fx->refl_height << 16;
    const int32_t refl_op = fx->refl_opacity * ONE / 100;
    const int32_t mid_h = h << 15;
    /* refl_op * n / refl for every reflection pixel without a 64 bit
     * division (a library call on the ARM9): multiply by the reciprocal,
     * then correct the result up to the exact quotient (checked against the
     * division for all heights 1..64 and opacities 0..100 %) */
    const uint64_t refl_recip = refl > 0 ?
        ((uint64_t)refl_op << 32) / (uint64_t)refl : 0;

    memset(pix, 0, alpha_offset);
    memset(alpha, 0, size - alpha_offset); /* all transparent */

    for (int px = 0; px < pw; px++)
    {
        /* middle of the column from the middle of the cover, on screen */
        int64_t x = ((int64_t)(px - mx) << 16) + ONE / 2 - ((int64_t)w << 15);
        /* the point of the cover there: x = X d / (d cos - X sin) */
        int64_t xc = x;
        if (fx->tilt)
        {
            int64_t den = d * c - ((x * s) >> 16);
            if (den <= 0)
                continue;
            xc = x * d * 16384 / den;
        }
        int64_t scale = fx_scale(fx, xc);
        if (scale <= 0)
            continue;
        int32_t u = (int32_t)(xc + ((int64_t)w << 15));
        int32_t cov_x = MIN(u, (w << 16) - u) + ONE / 2;
        if (cov_x <= 0)
            continue;
        cov_x = MIN(cov_x, ONE);
        /* source rows per screen row, and the edges of the column */
        int64_t step = ((int64_t)ONE << 16) / scale;
        int32_t half = (int32_t)(((int64_t)mid_h * scale) >> 16);
        int32_t top = mid_h - half, bottom = mid_h + half;

        for (int py = 0; py < ph; py++)
        {
            int32_t y0 = (py - over) << 16; /* top of the row in the box */
            int32_t ym = y0 + ONE / 2;
            int32_t op = 0;
            fb_data colour = 0;

            int32_t cov = MIN(y0 + ONE, bottom) - MAX(y0, top);
            if (cov > 0)
            {
                int32_t yin = MIN(MAX(ym, top), bottom);
                int32_t v = (int32_t)((((int64_t)(yin - mid_h)) * step) >> 16)
                            + mid_h;
                v = MIN(MAX(v, 0), h << 16);
                op = (int32_t)(((int64_t)MIN(cov, ONE) * cov_x) >> 16);
                op = (int32_t)(((int64_t)op * fx_corner(fx, w, h, u, v)) >> 16);
                colour = fx_sample(src, stride, w, h, u, v);
            }
            if (refl > 0 && ym > bottom && ym - bottom < refl)
            {
                int32_t e = ym - bottom;
                int32_t v = (h << 16) - (int32_t)(((int64_t)e * step) >> 16);
                if (v > 0)
                {
                    uint64_t n = (uint64_t)(refl - e);
                    uint64_t prod = (uint64_t)refl_op * n;
                    uint64_t q = (n * refl_recip) >> 32;
                    while ((q + 1) * (uint64_t)refl <= prod)
                        q++;
                    int32_t rop = (int32_t)q;
                    rop = (int32_t)(((int64_t)rop * cov_x) >> 16);
                    rop = (int32_t)(((int64_t)rop *
                                     fx_corner(fx, w, h, u, v)) >> 16);
                    rop = (int32_t)(((int64_t)rop * (ONE - op)) >> 16);
                    if (op == 0)
                        colour = fx_sample(src, stride, w, h, u, v);
                    op += rop;
                }
            }
            if (op <= 0)
                continue;
            int a = (int)(((int64_t)MIN(op, ONE) * 255 + ONE / 2) >> 16);
            if (a == 0)
                continue;
            pix[py * pw + px] = colour;
            alpha[py * pw + px] = a;
        }
    }
}

/* 4 x 4 ordered dither, thresholds 0..255 */
static const unsigned char fx_dither[4][4] = {
    {   8, 136,  40, 168 },
    { 200,  72, 232, 104 },
    {  56, 184,  24, 152 },
    { 248, 120, 216,  88 },
};

/* x / 255 without a division, exact for every value fx_blend() makes (as
 * in gui/popup.c, checked for all channels, alphas and thresholds) */
static inline int fx_div255(int x)
{
    return (x + 1 + (x >> 8)) >> 8;
}

/* under + (over - under) * a / 255 per channel, rounded by the dither
 * threshold of the screen pixel */
static inline fb_data fx_blend(unsigned under, unsigned over, unsigned a,
                               unsigned t)
{
    int ur = under >> 11, ug = (under >> 5) & 63, ub = under & 31;
    int vr = over >> 11, vg = (over >> 5) & 63, vb = over & 31;
    int r = fx_div255(ur * 255 + (vr - ur) * (int)a + (int)t);
    int g = fx_div255(ug * 255 + (vg - ug) * (int)a + (int)t);
    int b = fx_div255(ub * 255 + (vb - ub) * (int)a + (int)t);
    return (fb_data)((r << 11) | (g << 5) | b);
}

bool skin_aa_fx_draw(struct screen *display, struct skin_aa_fx *fx,
                     unsigned char *buf, const struct bitmap *bmp,
                     int handle, int x, int y, int w, int h, bool clear)
{
    int mx, over, pw, ph;
    size_t alpha_offset, size;

    if (!buf || w <= 0 || h <= 0)
        return false;
    fx_layout(fx, w, h, &mx, &over, &pw, &ph, &alpha_offset, &size);
    if (size > fx->size)
        return false;

    if (clear)
    {
        display->set_drawmode(DRMODE_SOLID | DRMODE_INVERSEVID);
        display->fillrect(x - mx, y - over, pw, ph);
        display->set_drawmode(DRMODE_SOLID);
        return true;
    }

    if (fx->handle != handle || fx->cover_w != w || fx->cover_h != h)
    {
        /* once per cover; at 54 MHz it blocked the UI for a while. No
         * yield() inside: the cover lies in the buffering buffer, which may
         * move while another thread runs. Boosted it is over 4 x sooner. */
#ifdef HAVE_ADJUSTABLE_CPU_FREQ
        cpu_boost(true);
#endif
        fx_render(fx, buf, (const fb_data *)bmp->data,
                  STRIDE_MAIN(bmp->width, bmp->height), w, h);
#ifdef HAVE_ADJUSTABLE_CPU_FREQ
        cpu_boost(false);
#endif
        fx->handle = handle;
        fx->cover_w = w;
        fx->cover_h = h;
    }

    /* blend with the backdrop under the picture (without one with the
     * background colour, as the skin engine does), clipped to the viewport,
     * and draw it a row at a time */
    const fb_data *pix = (const fb_data *)buf;
    const unsigned char *alpha = buf + alpha_offset;
    struct viewport *vp = *display->current_viewport;
    const fb_data *bd = display->screen_type == SCREEN_MAIN ?
                        lcd_get_backdrop() : NULL;
    static fb_data row[LCD_WIDTH];
    int x0 = x - mx, y0 = y - over;
    int sx = MAX(0, -x0), sy = MAX(0, -y0);
    int ex = MIN(pw, MIN(vp->width, LCD_WIDTH - vp->x) - x0);
    int ey = MIN(ph, MIN(vp->height, LCD_HEIGHT - vp->y) - y0);
    if (sx >= ex || sy >= ey)
        return true;

    for (int py = sy; py < ey; py++)
    {
        int ay = vp->y + y0 + py;
        const fb_data *under = bd ? &bd[ay * LCD_FBWIDTH] : NULL;
        for (int px = sx; px < ex; px++)
        {
            int ax = vp->x + x0 + px;
            unsigned a = alpha[py * pw + px];
            unsigned u = under ? under[ax] : vp->bg_pattern;
            if (a == 0)
                row[px - sx] = u;
            else if (a == 255)
                row[px - sx] = pix[py * pw + px];
            else
                row[px - sx] = fx_blend(u, pix[py * pw + px], a,
                                        fx_dither[ay & 3][ax & 3]);
        }
        display->bitmap_part(row, 0, 0, ex - sx, x0 + sx, y0 + py, ex - sx, 1);
    }
    return true;
}
#endif
