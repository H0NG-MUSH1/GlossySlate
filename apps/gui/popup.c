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

/* GlossySlate popups (docs/ipod6g-popups.md): a dark glossy panel like the
 * tiles, with a soft shadow, in the middle of the whole screen. The panel,
 * keys, bar and symbols are parts made by the designer
 * (popup_parts.h, RGB565 with 8 bit alpha), blended into the frame buffer
 * here with an ordered dither. What the popup covers is saved first and put
 * back when it closes, if nothing has drawn over the popup meanwhile. */

#include "config.h"
#include <stdio.h>
#include <string.h>
#include "system.h"
#include "kernel.h"
#include "lcd.h"
#include "font.h"
#include "screen_access.h"
#include "viewport.h"
#include "settings.h"
#include "lang.h"
#include "string-extra.h"
#include "rbunicode.h"
#include "popup.h"
#include "popup_parts.h"

#define SHADOW_L 12
#define SHADOW_T 9
#define SHADOW_R 12
#define SHADOW_B 16
#define PAD_X 14
#define PAD_Y 12
#define LINE_H 16
#define MAX_W 240
#define WRAP_W (MAX_W - 2 * PAD_X)
#define KEY_W 102
#define KEY_H 26
#define SYMBOL_SIZE 48
#define AREA_MAX_W (MAX_W + SHADOW_L + SHADOW_R)
#define AREA_MAX_H (128 + SHADOW_T + SHADOW_B)
#define MAX_LINES 5

#define TEXT_COLOUR LCD_RGBPACK(255, 255, 255)
#define HINT_COLOUR LCD_RGBPACK(0xc5, 0xcf, 0xdd)

static int popup_font = -1, hint_font = -1;

/* what the popup on the screen covers */
static fb_data saved_px[AREA_MAX_W * AREA_MAX_H];
static struct {
    int x, y, w, h;
    uint32_t sum;   /* of the area with the popup, to see if it is intact */
    bool valid;
} saved;
/* a popup was drawn over: the status bar skin must redraw completely */
static bool need_repaint;

static char text_buf[256];

/* The frame buffer of the screen itself. The pixels are read and written
 * here directly, not through the current viewport (FBADDR): the area must
 * be the screen, whatever viewport the caller has set, and
 * popup_screen_state(), which runs at every status bar update, must not
 * touch the current viewport. */
extern struct frame_buffer_t lcd_framebuffer_default;
static inline fb_data *screen_px(int x, int y)
{
    return (fb_data *)lcd_framebuffer_default.data + y * LCD_WIDTH + x;
}

/* 4 x 4 ordered dither, thresholds 0..255 (as skin_albumart_fx.c) */
static const unsigned char dither[4][4] = {
    {   8, 136,  40, 168 },
    { 200,  72, 232, 104 },
    {  56, 184,  24, 152 },
    { 248, 120, 216,  88 },
};

struct popup_line {
    const char *s;
    int len;
    int w;
};

/* ---------------------------------------------------------------- fonts */

static int load_font(int id, const unsigned char *name)
{
    char path[MAX_PATH];
    bool none = !name[0] || name[0] == '-';
    if (!none)
        snprintf(path, sizeof path, FONT_DIR "/%s.fnt", name);
    if (id >= 0 && (none || !font_filename_matches_loaded_id(id, path)))
    {
        font_unload(id);
        id = -1;
    }
    if (!none && id < 0)
    {
        int loaded = font_load_ex(path, 0, 160);
        id = loaded >= 0 ? loaded : -1;
    }
    return id;
}

void popup_fonts_apply(void)
{
    popup_font = load_font(popup_font, global_settings.popup_font_file);
    hint_font = load_font(hint_font, global_settings.popup_hint_font_file);
}

static int text_font(void)
{
    return popup_font >= 0 ? popup_font : FONT_UI;
}

static int small_font(void)
{
    return hint_font >= 0 ? hint_font : text_font();
}

/* --------------------------------------------------------------- pixels */

/* x / 255 for 0 <= x < 65535 without a division (the ARM9 of the iPod has
 * none, a division is a library call); exact for every value blend() makes
 * (checked for all channels, alphas and dither thresholds) */
static inline int div255(int x)
{
    return (x + 1 + (x >> 8)) >> 8;
}

static inline fb_data blend(unsigned under, unsigned over, unsigned a,
                            unsigned t)
{
    int ur = under >> 11, ug = (under >> 5) & 63, ub = under & 31;
    int vr = over >> 11, vg = (over >> 5) & 63, vb = over & 31;
    int r = div255(ur * 255 + (vr - ur) * (int)a + (int)t);
    int g = div255(ug * 255 + (vg - ug) * (int)a + (int)t);
    int b = div255(ub * 255 + (vb - ub) * (int)a + (int)t);
    return (fb_data)((r << 11) | (g << 5) | b);
}

/* columns col .. col + ncols of part p at screen position x, y; mirrored:
 * read from the right end (the right end of a panel) */
static void draw_part(const struct popup_part *p, int x, int y,
                      int col, int ncols, bool mirror)
{
    for (int r = 0; r < p->height; r++)
    {
        int sy = y + r;
        if (sy < 0 || sy >= LCD_HEIGHT)
            continue;
        fb_data *row = screen_px(0, sy);
        for (int c = 0; c < ncols; c++)
        {
            int sx = x + c;
            if (sx < 0 || sx >= LCD_WIDTH)
                continue;
            int pc = mirror ? p->width - 1 - (col + c) : col + c;
            int i = r * p->width + pc;
            unsigned a = p->alpha[i];
            if (a == 0)
                continue;
            row[sx] = (a == 255) ? p->rgb[i] :
                blend(row[sx], p->rgb[i], a, dither[sy & 3][sx & 3]);
        }
    }
}

/* the middle part m (1 px wide) repeated over w columns from x, y: a row
 * at a time, its pixel is the same in every column (vertical gradients) */
static void draw_middle(const struct popup_part *m, int x, int y, int w)
{
    int x0 = MAX(x, 0), x1 = MIN(x + w, LCD_WIDTH);
    if (x0 >= x1)
        return;
    for (int r = 0; r < m->height; r++)
    {
        int sy = y + r;
        if (sy < 0 || sy >= LCD_HEIGHT)
            continue;
        unsigned a = m->alpha[r];
        if (a == 0)
            continue;
        fb_data c = m->rgb[r];
        fb_data *px = screen_px(x0, sy);
        if (a == 255)
        {
            for (int sx = x0; sx < x1; sx++)
                *px++ = c;
        }
        else
        {
            const unsigned char *t = dither[sy & 3];
            for (int sx = x0; sx < x1; sx++, px++)
                *px = blend(*px, c, a, t[sx & 3]);
        }
    }
}

/* the panel w x h at x, y, with its shadow */
static void draw_panel(int x, int y, int w, int h)
{
    int k = 0;
    while (k < (int)ARRAYLEN(popup_panel_heights) - 1 &&
           popup_panel_heights[k] < h)
        k++;
    const struct popup_part *l = &popup_panel_left[k];
    const struct popup_part *m = &popup_panel_mid[k];
    draw_part(l, x - SHADOW_L, y - SHADOW_T, 0, l->width, false);
    draw_middle(m, x + PAD_X, y - SHADOW_T, w - 2 * PAD_X);
    draw_part(l, x + w - PAD_X, y - SHADOW_T, 0, l->width, true);
}

/* a horizontal piece of three parts (left, middle repeated, right) */
static void draw_three(const struct popup_part *parts, int x, int y, int w)
{
    int lw = parts[0].width, rw = parts[2].width;
    if (w < lw + rw)
    {
        draw_part(&parts[0], x, y, 0, MIN(w, lw), false);
        return;
    }
    draw_part(&parts[0], x, y, 0, lw, false);
    draw_middle(&parts[1], x + lw, y, w - lw - rw);
    draw_part(&parts[2], x + w - rw, y, 0, rw, false);
}

/* ------------------------------------------------------------------ text */

static int string_width(const char *s, int len, int font)
{
    int w = 0;
    font_getstringnsize((const unsigned char *)s, len, &w, NULL, font);
    return w;
}

/* Text needs a viewport. It is static, and its buffer is NULL before
 * viewport_set_fullscreen(): that function starts with init_viewport(),
 * which reads vp->buffer and writes through it when it is set. With an
 * uninitialised viewport on the stack that was a random pointer: memory got
 * overwritten, the iPod froze at once or later. (viewport_set_defaults()
 * clears the buffer for the same reason.) */
static void draw_text(int x, int y, const char *s, int len, int font,
                      unsigned colour)
{
    static struct viewport vp;
    struct screen *display = &screens[SCREEN_MAIN];
    vp.buffer = NULL;
    viewport_set_fullscreen(&vp, SCREEN_MAIN);
    vp.font = font;
    vp.drawmode = DRMODE_FG;
    vp.fg_pattern = colour;
    struct viewport *last = display->set_viewport_ex(&vp, 0);
    display->putsxyf(x, y, "%.*s", len, s);
    display->set_viewport_ex(last, 0);
}

/* splash text without its control characters (they break lines or act as
 * spaces in splash.c) */
static const char *clean_text(const char *text)
{
    size_t i = 0;
    if (*text == '\f')
        text++;
    for (; text[i] && i < sizeof(text_buf) - 1; i++)
        text_buf[i] = (text[i] == '\t' || text[i] == '\r' || text[i] == '\v' ||
                       text[i] == '\b' || text[i] == '\f') ? ' ' : text[i];
    text_buf[i] = '\0';
    return text_buf;
}

/* breaks text into lines of at most maxw pixels, at spaces and '\n' */
static int wrap(const char *text, int font, int maxw,
                struct popup_line *lines, int max_lines, int *widest)
{
    int n = 0;
    const char *p = text;
    while (*p && n < max_lines)
    {
        const char *end = strchr(p, '\n');
        if (!end)
            end = p + strlen(p);
        while (n < max_lines)
        {
            while (p < end && *p == ' ')
                p++;
            if (p >= end)
                break;
            const char *line_end = p, *q = p;
            int w = 0;
            while (q < end)
            {
                const char *word_end = q;
                while (word_end < end && *word_end != ' ')
                    word_end++;
                int ww = string_width(p, word_end - p, font);
                if (ww > maxw)
                {
                    if (line_end == p) /* one word wider than a line: cut it */
                    {
                        int fit = font_measurestring((const unsigned char *)p,
                                                     word_end - p, maxw,
                                                     &w, NULL, font);
                        if (fit <= 0) /* at least one whole character */
                            fit = utf8seek((const unsigned char *)p, 1);
                        line_end = p + MAX(fit, 1);
                        w = string_width(p, line_end - p, font);
                    }
                    break;
                }
                line_end = word_end;
                w = ww;
                q = word_end;
                while (q < end && *q == ' ')
                    q++;
            }
            lines[n].s = p;
            lines[n].len = line_end - p;
            lines[n].w = w;
            *widest = MAX(*widest, w);
            n++;
            p = line_end;
        }
        p = (*end == '\n') ? end + 1 : end;
    }
    return n;
}

static void draw_lines(int x, int y, int w, const struct popup_line *lines,
                       int n)
{
    for (int i = 0; i < n; i++)
        draw_text(x + (w - lines[i].w) / 2, y + i * LINE_H,
                  lines[i].s, lines[i].len, text_font(), TEXT_COLOUR);
}

/* ----------------------------------------------------------- the screen */

static uint32_t area_sum(void)
{
    uint32_t sum = 0;
    for (int r = 0; r < saved.h; r++)
    {
        const fb_data *row = screen_px(saved.x, saved.y + r);
        for (int c = 0; c < saved.w; c++)
            sum = sum * 33 + row[c];
    }
    return sum;
}

static void area_copy(bool save)
{
    for (int r = 0; r < saved.h; r++)
    {
        fb_data *row = screen_px(saved.x, saved.y + r);
        fb_data *buf = &saved_px[r * saved.w];
        if (save)
            memcpy(buf, row, saved.w * sizeof(fb_data));
        else
            memcpy(row, buf, saved.w * sizeof(fb_data));
    }
}

/* the area of an earlier popup that popup_begin() put back in the frame
 * buffer: it goes to the LCD with the new popup (w 0: none) */
static struct { int x, y, w, h; } restored;

/* lcd_update_rect() takes the pixels from the buffer of the current
 * viewport: the screen's own one while the area goes to the LCD. With an
 * earlier popup put back, the LCD gets both areas: a smaller popup left
 * the shadow of the one before on the LCD (not in the frame buffer, so not
 * in a screen dump either). */
static void update_area(void)
{
    int x0 = saved.x, y0 = saved.y;
    int x1 = saved.x + saved.w, y1 = saved.y + saved.h;
    if (restored.w > 0)
    {
        x0 = MIN(x0, restored.x);
        y0 = MIN(y0, restored.y);
        x1 = MAX(x1, restored.x + restored.w);
        y1 = MAX(y1, restored.y + restored.h);
        restored.w = 0;
    }
    struct screen *display = &screens[SCREEN_MAIN];
    struct viewport *last = display->set_viewport_ex(NULL, 0);
    display->update_rect(x0, y0, x1 - x0, y1 - y0);
    display->set_viewport_ex(last, 0);
}

/* Before a popup of w x h at x, y (without shadow): an earlier popup that
 * is still intact goes first, then the area under the new one is saved.
 * Drawn again at the same place (progress, countdown), the restored area
 * is what the buffer holds already: no second copy. */
static void popup_begin(int x, int y, int w, int h)
{
    int ax = MAX(0, x - SHADOW_L);
    int ay = MAX(0, y - SHADOW_T);
    int aw = MIN(LCD_WIDTH, x + w + SHADOW_R) - ax;
    int ah = MIN(LCD_HEIGHT, y + h + SHADOW_B) - ay;
    bool kept = false;

    screens[SCREEN_MAIN].scroll_stop();

    if (saved.valid)
    {
        if (area_sum() == saved.sum)
        {
            area_copy(false);
            kept = saved.x == ax && saved.y == ay &&
                   saved.w == aw && saved.h == ah;
            if (!kept)
            {
                restored.x = saved.x;
                restored.y = saved.y;
                restored.w = saved.w;
                restored.h = saved.h;
            }
        }
        else
            need_repaint = true;
    }
    saved.x = ax;
    saved.y = ay;
    saved.w = aw;
    saved.h = ah;
    if (!kept)
        area_copy(true);
    saved.valid = true;
}

static void popup_end(void)
{
    saved.sum = area_sum();
    update_area();
}

void popup_close(void)
{
    if (!saved.valid)
        return;
    if (area_sum() == saved.sum)
    {
        area_copy(false);
        update_area();
    }
    else
        need_repaint = true;
    saved.valid = false;
}

enum popup_state popup_screen_state(void)
{
    if (saved.valid)
    {
        if (area_sum() == saved.sum)
            return POPUP_SHOWN;
        saved.valid = false;
        need_repaint = true;
    }
    if (need_repaint)
    {
        need_repaint = false;
        return POPUP_DISTURBED;
    }
    return POPUP_NONE;
}

/* --------------------------------------------------------------- popups */

/* the symbol of known messages, -1 for none ("Lesezeichen angelegt" has
 * none; the key lock shows no popup at all, see action.c) */
static int symbol_for(int lang_id)
{
    switch (lang_id)
    {
        case LANG_SETTINGS_SAVED:
        case LANG_RESET_DONE_CLEAR:
            return POPUP_SYM_DONE;
        case LANG_TAGCACHE_BUSY:
        case LANG_FAILED:
        case LANG_BOOKMARK_CREATE_FAILURE:
            return POPUP_SYM_WARNING;
        default:
            return -1;
    }
}

void popup_message(const char *text, int lang_id)
{
    struct popup_line lines[MAX_LINES];
    int widest = 0;
    int sym = symbol_for(lang_id);
    int n = wrap(clean_text(text), text_font(), WRAP_W, lines,
                 sym >= 0 ? 2 : MAX_LINES, &widest);
    if (n == 0)
        return;

    int w = MIN(MAX(widest + 2 * PAD_X, sym >= 0 ? 132 : 120), MAX_W);
    int h = sym >= 0 ? (n > 1 ? 120 : 104) : 2 * PAD_Y + LINE_H * n;
    int x = (LCD_WIDTH - w) / 2, y = (LCD_HEIGHT - h) / 2;

    popup_begin(x, y, w, h);
    draw_panel(x, y, w, h);
    if (sym >= 0)
    {
        draw_part(&popup_symbols[sym], x + (w - SYMBOL_SIZE) / 2, y + 16,
                  0, SYMBOL_SIZE, false);
        draw_lines(x, y + 74, w, lines, n);
    }
    else
        draw_lines(x, y + PAD_Y, w, lines, n);
    popup_end();
}

void popup_progress(const char *text, int current, int total)
{
    struct popup_line lines[3];
    int widest = 0;
    int n = wrap(clean_text(text), text_font(), WRAP_W, lines, 3, &widest);

    int w = MIN(MAX(widest + 2 * PAD_X, 208), MAX_W);
    int h = 2 * PAD_Y + LINE_H * n + 16;
    int x = (LCD_WIDTH - w) / 2, y = (LCD_HEIGHT - h) / 2;
    int bar_w = w - 2 * PAD_X;
    int fill = 0;
    if (total > 0)
        fill = (int)((long long)bar_w * MAX(0, MIN(current, total)) / total);

    popup_begin(x, y, w, h);
    draw_panel(x, y, w, h);
    draw_lines(x, y + PAD_Y, w, lines, n);
    int bar_y = y + PAD_Y + LINE_H * n + 8;
    draw_three(popup_track, x + PAD_X, bar_y, bar_w);
    if (fill > 0)
        draw_three(popup_fill, x + PAD_X, bar_y, fill);
    popup_end();
}

static void draw_key(const struct popup_part *parts, int x, int y,
                     const char *label)
{
    int len = strlen(label);
    int font = text_font();
    draw_three(parts, x, y, KEY_W);
    draw_text(x + (KEY_W - string_width(label, len, font)) / 2,
              y + (KEY_H - font_get(font)->height) / 2, label, len, font,
              TEXT_COLOUR);
}

static void draw_hint(int x, int y, const char *hint, int seconds)
{
    char buf[64];
    int font = small_font();
    int len = seconds >= 0 ? snprintf(buf, sizeof buf, "%s (%d)", hint, seconds)
                           : snprintf(buf, sizeof buf, "%s", hint);
    len = MIN(len, (int)sizeof(buf) - 1);
    draw_text(x + (KEY_W - string_width(buf, len, font)) / 2, y, buf, len,
              font, HINT_COLOUR);
}

void popup_yesno(const char *const *lines_in, int nb_lines, int seconds,
                 bool yes_is_default)
{
    static char question[256];
    struct popup_line lines[3];
    int widest = 0, n = 0;

    /* each line of the question breaks on its own */
    question[0] = '\0';
    for (int i = 0; i < nb_lines; i++)
    {
        if (i)
            strlcat(question, "\n", sizeof question);
        strlcat(question, lines_in[i], sizeof question);
    }
    strmemccpy(question, clean_text(question), sizeof question);
    n = wrap(question, text_font(), WRAP_W, lines, 3, &widest);
    if (n == 0) /* one empty line: the panel heights are 96, 112, 128 */
    {
        lines[0].s = "";
        lines[0].len = lines[0].w = 0;
        n = 1;
    }

    int w = MAX_W;
    int h = 80 + LINE_H * n;
    int x = (LCD_WIDTH - w) / 2, y = (LCD_HEIGHT - h) / 2;
    int key_y = y + PAD_Y + LINE_H * n + 12;

    popup_begin(x, y, w, h);
    draw_panel(x, y, w, h);
    draw_lines(x, y + PAD_Y, w, lines, n);
    draw_key(popup_key_yes, x + PAD_X, key_y, str(LANG_SET_BOOL_YES));
    draw_key(popup_key_no, x + 124, key_y, str(LANG_SET_BOOL_NO));
    draw_hint(x + PAD_X, key_y + 30, str(LANG_POPUP_YES_HINT),
              yes_is_default ? seconds : -1);
    draw_hint(x + 124, key_y + 30, str(LANG_POPUP_NO_HINT),
              yes_is_default ? -1 : seconds);
    popup_end();
}
