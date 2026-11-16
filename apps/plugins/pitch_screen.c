/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2002 Björn Stenberg
 *
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
#include "plugin.h"
#include "lib/icon_helper.h"
#include "lib/arg_helper.h"

#define ICON_BORDER 12 /* icons are currently 7x8, so add ~2 pixels  */
                       /*   on both sides when drawing */

#define PITCH_MAX         (200 * PITCH_SPEED_PRECISION)
#define PITCH_MIN         (50 * PITCH_SPEED_PRECISION)
#define PITCH_SMALL_DELTA (PITCH_SPEED_PRECISION / 10)      /* .1% */
#define PITCH_BIG_DELTA   (PITCH_SPEED_PRECISION)           /*  1% */
#define PITCH_NUDGE_DELTA (2 * PITCH_SPEED_PRECISION)       /*  2% */

#define SPEED_SMALL_DELTA (PITCH_SPEED_PRECISION / 10)      /* .1% */
#define SPEED_BIG_DELTA   (PITCH_SPEED_PRECISION)           /*  1% */

#define SEMITONE_SMALL_DELTA (PITCH_SPEED_PRECISION / 10)  /* 10 cents   */
#define SEMITONE_BIG_DELTA   PITCH_SPEED_PRECISION         /* 1 semitone */

#define PVAR_VERBOSE 0x01
#define PVAR_GUI     0x02
struct pvars
{
    int32_t speed;
    int32_t pitch;
    int32_t stretch;
    int32_t flags;
};
static struct pvars pitch_vars;

enum
{
    PITCH_TOP = 0,
    PITCH_MID,
    PITCH_BOTTOM,
    PITCH_ITEM_COUNT,
};

/* This is a table of semitone percentage values of the appropriate
   precision (based on PITCH_SPEED_PRECISION).  Note that these are
   all constant expressions, which will be evaluated at compile time,
   so no need to worry about how complex the expressions look.
   That's just to get the precision right.

   I calculated these values, starting from 50, as

   x(n) = 50 * 2^(n/12)

   All that math in each entry simply converts the float constant
   to an integer equal to PITCH_SPEED_PRECISION times the float value,
   with as little precision loss as possible (i.e. correctly rounding
   the last digit).
*/
#define TO_INT_WITH_PRECISION(x) \
    ( (unsigned short)(((x) * PITCH_SPEED_PRECISION * 10 + 5) / 10) )

static const unsigned short semitone_table[] =
{
    TO_INT_WITH_PRECISION(50.00000000), /* Octave lower */
    TO_INT_WITH_PRECISION(52.97315472),
    TO_INT_WITH_PRECISION(56.12310242),
    TO_INT_WITH_PRECISION(59.46035575),
    TO_INT_WITH_PRECISION(62.99605249),
    TO_INT_WITH_PRECISION(66.74199271),
    TO_INT_WITH_PRECISION(70.71067812),
    TO_INT_WITH_PRECISION(74.91535384),
    TO_INT_WITH_PRECISION(79.37005260),
    TO_INT_WITH_PRECISION(84.08964153),
    TO_INT_WITH_PRECISION(89.08987181),
    TO_INT_WITH_PRECISION(94.38743127),
    TO_INT_WITH_PRECISION(100.0000000), /* Normal sound */
    TO_INT_WITH_PRECISION(105.9463094),
    TO_INT_WITH_PRECISION(112.2462048),
    TO_INT_WITH_PRECISION(118.9207115),
    TO_INT_WITH_PRECISION(125.9921049),
    TO_INT_WITH_PRECISION(133.4839854),
    TO_INT_WITH_PRECISION(141.4213562),
    TO_INT_WITH_PRECISION(149.8307077),
    TO_INT_WITH_PRECISION(158.7401052),
    TO_INT_WITH_PRECISION(168.1792831),
    TO_INT_WITH_PRECISION(178.1797436),
    TO_INT_WITH_PRECISION(188.7748625),
    TO_INT_WITH_PRECISION(200.0000000)  /* Octave higher */
};

#define NUM_SEMITONES   ((int)(sizeof(semitone_table)/sizeof(semitone_table[0])))
#define SEMITONE_END    (NUM_SEMITONES/2)
#define SEMITONE_START  (-SEMITONE_END)

/* A table of values for approximating the cent curve with
   linear interpolation.  Multipy the next lowest semitone
   by this much to find the corresponding cent percentage.

   These values were calculated as
   x(n) = 100 * 2^(n * 20/1200)
*/

static const unsigned short cent_interp[] =
{
    TO_INT_WITH_PRECISION(100.0000000),
    TO_INT_WITH_PRECISION(101.1619440),
    TO_INT_WITH_PRECISION(102.3373892),
    TO_INT_WITH_PRECISION(103.5264924),
    TO_INT_WITH_PRECISION(104.7294123),
    /* this one's the next semitone but we have it here for convenience */
    TO_INT_WITH_PRECISION(105.9463094),
};

int viewport_get_nb_lines(const struct viewport *vp)
{
    return vp->height/rb->font_get(vp->font)->height;
}
#if 0 /* replaced with cbmp_get_icon(CBMP_Mono_7x8, Icon_ABCD, &w, &h) */
enum icons_7x8 {
    Icon_Plug,
    Icon_USBPlug,
    Icon_Mute,
    Icon_Play,
    Icon_Stop,
    Icon_Pause,
    Icon_FastForward,
    Icon_FastBackward,
    Icon_Record,
    Icon_RecPause,
    Icon_Radio,
    Icon_Radio_Mute,
    Icon_Repeat,
    Icon_RepeatOne,
    Icon_Shuffle,
    Icon_DownArrow,
    Icon_UpArrow,
    Icon_RepeatAB,
    Icon7x8Last
};

const unsigned char bitmap_icons_7x8[][7] =
{
    {0x08,0x1c,0x3e,0x3e,0x3e,0x14,0x14}, /* Power plug */
    {0x1c,0x14,0x3e,0x2a,0x22,0x1c,0x08}, /* USB plug */
    {0x01,0x1e,0x1c,0x3e,0x7f,0x20,0x40}, /* Speaker mute */
    {0x00,0x7f,0x7f,0x3e,0x1c,0x08,0x00}, /* Play */
    {0x7f,0x7f,0x7f,0x7f,0x7f,0x7f,0x7f}, /* Stop */
    {0x00,0x7f,0x7f,0x00,0x7f,0x7f,0x00}, /* Pause */
    {0x7f,0x3e,0x1c,0x7f,0x3e,0x1c,0x08}, /* Fast forward */
    {0x08,0x1c,0x3e,0x7f,0x1c,0x3e,0x7f}, /* Fast backward */
    {0x1c,0x3e,0x7f,0x7f,0x7f,0x3e,0x1c}, /* Record */
    {0x1c,0x3e,0x7f,0x00,0x7f,0x3e,0x1c}, /* Record pause */
    {0x40,0xa0,0xa0,0xa0,0x7f,0x02,0x02}, /* Radio on */
    {0x42,0xa4,0xa8,0xb0,0x7f,0x22,0x42}, /* Radio mute */
    {0x44,0x4e,0x5f,0x44,0x44,0x44,0x38}, /* Repeat playmode */
    {0x44,0x4e,0x5f,0x44,0x38,0x02,0x7f}, /* Repeat-one playmode */
    {0x3e,0x41,0x51,0x41,0x45,0x41,0x3e}, /* Shuffle playmode (dice) */
    {0x04,0x0c,0x1c,0x3c,0x1c,0x0c,0x04}, /* Down-arrow */
    {0x20,0x30,0x38,0x3c,0x38,0x30,0x20}, /* Up-arrow */
    {0x7f,0x04,0x4e,0x5f,0x44,0x38,0x7f}  /* Repeat-AB playmode */
};
#endif

/* Number of cents between entries in the cent_interp table */
#define CENT_INTERP_INTERVAL 20
#define CENT_INTERP_NUM      ((int)(sizeof(cent_interp)/sizeof(cent_interp[0])))

/* This stores whether the pitch and speed are at their own limits */
/* or that of the timestretching algorithm                         */
static bool at_limit = false;

/*
 *
 * The pitchscreen is divided into 3 viewports (each row is a viewport)
 * Then each viewport is again divided into 3 colums, each showsing some infos
 * Additionally, on touchscreen, each cell represents a button
 *
 * Below a sketch describing what each cell will show (what's drawn on it)
 * --------------------------
 * |      |        |        | <-- pitch up in the middle (text and button)
 * |      |        |        | <-- arrows for mode toggling on the sides for touchscreen
 * |------------------------|
 * |      |        |        | <-- semitone/speed up/down on the sides
 * |      |        |        | <-- reset pitch&speed in the middle
 * |------------------------|
 * |      |        |        | <-- pitch down in the middle
 * |      |        |        | <-- Two "OK" for exit on the sides for touchscreen
 * |------------------------|
 *
 *
 */

#ifdef IPOD_6G
/* GlossySlate: the tempo screen as designed (GlossySlate/DESIGN.md 5.12), in
 * the style of the quick menu. The parts are bitmaps of the theme in
 * .rockbox/wps/<status bar skin>/tempo/ (tools/build_tempo.py), loaded into
 * the plugin buffer while the screen is open; the field is the dithered
 * gradient of the quick menu, the texts are set with the theme's fonts,
 * shared with the skin (font_load_ex() with the skin's glyph cache, so no
 * font is loaded a second time). Without the parts (another theme) the
 * screen is drawn as before. Keys, values and speech are unchanged. */
enum gs_part {
    GS_CAP_L, GS_CAP_M, GS_CAP_R, GS_ICON_MODE, GS_KEY_100, GS_KEY_BACK,
    GS_DIVIDER, GS_FIELD, GS_SLOWER, GS_FASTER, GS_TRACK, GS_FILL, GS_KNOB,
    GS_MARK, GS_KEY, GS_KEY_HELD, GS_ARR_L, GS_ARR_R, GS_ARR_L_W, GS_ARR_R_W,
    GS_WHEEL, GS_ICON_PITCH, GS_ICON_SPEED, GS_PART_COUNT
};
static const char *const gs_part_names[GS_PART_COUNT] = {
    "capsule_left", "capsule_middle", "capsule_right", "icon_mode", "key_100",
    "key_back", "divider", "value_field", "icon_slower", "icon_faster",
    "slider_track", "slider_fill", "slider_knob", "slider_mark", "key",
    "key_held", "arrow_left", "arrow_right", "arrow_left_white",
    "arrow_right_white", "icon_wheel", "icon_pitch", "icon_speed",
};
static struct bitmap gs_bm[GS_PART_COUNT];

enum gs_font { GS_F13, GS_F11, GS_F17, GS_F14, GS_F12, GS_FONT_COUNT };
static const char *const gs_font_names[GS_FONT_COUNT] = {
    FONT_DIR "/16-GlossySlate-Bold13.fnt", FONT_DIR "/14-GlossySlate-Bold11.fnt",
    FONT_DIR "/20-GlossySlate-Bold17.fnt", FONT_DIR "/24-GlossySlate-Bold14.fnt",
    FONT_DIR "/16-GlossySlate-Bold12.fnt",
};
#define GS_FONT_GLYPHS 160          /* the glyph cache the skin loads them with */
static int gs_fonts[GS_FONT_COUNT];
static bool gs_font_loaded[GS_FONT_COUNT];   /* to give back with font_unload() */

static fb_data *gs_field;           /* the background, LCD_WIDTH x LCD_HEIGHT */
static bool gs_active;
static int gs_held;                 /* key held: -1 left, 1 right, 0 none */

#define GS_DARK   LCD_RGBPACK(0x2e, 0x36, 0x44)
#define GS_GREY   LCD_RGBPACK(0x5b, 0x63, 0x71)
#define GS_BLACK  LCD_RGBPACK(0x14, 0x17, 0x1c)
#define GS_RED    LCD_RGBPACK(0xb8, 0x28, 0x1c)
#define GS_WHITE  LCD_RGBPACK(0xff, 0xff, 0xff)
#define GS_WHITE88 LCD_RGBPACK(0xe4, 0xec, 0xf8)  /* white 88 % on the blue key */
#define GS_MINUS  "\xe2\x88\x92"    /* U+2212 */

/* the field: #F7F8FA -> #EDEFF3 over rows 0-131, -> #DFE3E9 over 132-239,
 * dithered to RGB565 exactly as the skin's %dr (draw_gradient_dithered()),
 * so it is the field of the quick menu */
static void gs_make_field(void)
{
    static const unsigned char bayer[4][4] = {
        {   8, 136,  40, 168 }, { 200,  72, 232, 104 },
        {  56, 184,  24, 152 }, { 248, 120, 216,  88 },
    };
    static const struct { int y, h; unsigned long c0, c1; } bands[2] = {
        { 0, 132, 0xf7f8fa, 0xedeff3 }, { 132, 108, 0xedeff3, 0xdfe3e9 },
    };
    for (int b = 0; b < 2; b++)
    {
        int h = bands[b].h;
        int sr = (bands[b].c0 >> 16) & 0xff, er = (bands[b].c1 >> 16) & 0xff;
        int sg = (bands[b].c0 >> 8) & 0xff, eg = (bands[b].c1 >> 8) & 0xff;
        int sb = bands[b].c0 & 0xff, eb = bands[b].c1 & 0xff;
        for (int i = 0; i < h; i++)
        {
            int y = bands[b].y + i;
            int num = 2 * i + 1, den = 2 * h;
            int r = ((sr * den + (er - sr) * num) * 31 * 256) / (255 * den);
            int g = ((sg * den + (eg - sg) * num) * 63 * 256) / (255 * den);
            int bl = ((sb * den + (eb - sb) * num) * 31 * 256) / (255 * den);
            fb_data *row = gs_field + y * LCD_WIDTH;
            for (int x = 0; x < LCD_WIDTH; x++)
            {
                int t = bayer[y & 3][x & 3];
                row[x] = FB_RGBPACK_LCD(MIN((r + t) >> 8, 31),
                                        MIN((g + t) >> 8, 63),
                                        MIN((bl + t) >> 8, 31));
            }
        }
    }
}

static void gs_unload(void)
{
    for (int i = 0; i < GS_FONT_COUNT; i++)
    {
        /* a shared font (also the UI font) only loses this reference */
        if (gs_font_loaded[i])
            rb->font_unload(gs_fonts[i]);
        gs_font_loaded[i] = false;
        gs_fonts[i] = FONT_UI;
    }
}

/* parts and fonts of the theme; false: draw the screen as before */
static bool gs_load(void)
{
    char path[MAX_PATH];
    size_t size;
    unsigned char *buf = rb->plugin_get_buffer(&size);
    const char *skin = (const char *)rb->global_settings->sbs_file;

    for (int i = 0; i < GS_FONT_COUNT; i++)
    {
        gs_fonts[i] = FONT_UI;
        gs_font_loaded[i] = false;
    }
    if (!buf || !skin[0] || skin[0] == '-')
        return false;

    size_t field = LCD_WIDTH * LCD_HEIGHT * sizeof(fb_data);
    if (size < field)
        return false;
    gs_field = (fb_data *)buf;
    buf += field;
    size -= field;

    for (int i = 0; i < GS_PART_COUNT; i++)
    {
        rb->snprintf(path, sizeof(path), WPS_DIR "/%s/tempo/%s.bmp",
                     skin, gs_part_names[i]);
        gs_bm[i].data = buf;
        int n = rb->read_bmp_file(path, &gs_bm[i], size,
                                  FORMAT_NATIVE | FORMAT_TRANSPARENT, NULL);
        if (n <= 0)
            return false;
        n = ALIGN_UP(n, 4);
        if ((size_t)n > size)
            return false;
        buf += n;
        size -= n;
    }

    for (int i = 0; i < GS_FONT_COUNT; i++)
    {
        int id = rb->font_load_ex(gs_font_names[i], 0, GS_FONT_GLYPHS);
        gs_font_loaded[i] = id >= 0;
        gs_fonts[i] = id >= 0 ? id : FONT_UI;
    }
    gs_make_field();
    return true;
}

static void gs_bmp(const struct bitmap *bm, int x, int y)
{
    rb->lcd_bmp_part(bm, 0, 0, x, y, bm->width, bm->height);
}

static int gs_width(int font, const char *s)
{
    int w = 0;
    rb->font_getstringsize((const unsigned char *)s, &w, NULL, font);
    return w;
}

static void gs_text(int font, unsigned colour, int x, int y, const char *s)
{
    rb->lcd_setfont(font);
    rb->lcd_set_foreground(colour);
    rb->lcd_putsxy(x, y, (const unsigned char *)s);
}

static void gs_text_centred(int font, unsigned colour, int x, int w, int y,
                            const char *s)
{
    gs_text(font, colour, x + (w - gs_width(font, s)) / 2, y, s);
}

/* a capsule of the given width from the three parts; the middle part is 4 px
 * wide (one dither period) and repeated */
static void gs_capsule(int x, int y, int w)
{
    const struct bitmap *l = &gs_bm[GS_CAP_L], *m = &gs_bm[GS_CAP_M],
                        *r = &gs_bm[GS_CAP_R];
    int mx = x + l->width, end = x + w - r->width;
    gs_bmp(l, x, y);
    while (mx < end)
    {
        int part = MIN(m->width, end - mx);
        rb->lcd_bmp_part(m, 0, 0, mx, y, part, m->height);
        mx += part;
    }
    gs_bmp(r, end, y);
}

/* log2(v / 100 %) in 1/1000, for the slider (logarithmic, 100 % in the middle) */
static int gs_log2_permille(int32_t v)
{
    int64_t x = ((int64_t)v << 16) / PITCH_SPEED_100;
    int64_t result = 0;
    if (x <= 0)
        return -1000;
    while (x >= (2 << 16)) { x >>= 1; result += 65536; }
    while (x < (1 << 16))  { x <<= 1; result -= 65536; }
    for (int b = 32768; b; b >>= 1)
    {
        x = (x * x) >> 16;
        if (x >= (2 << 16))
        {
            x >>= 1;
            result += b;
        }
    }
    return (int)((result * 1000) >> 16);
}

/* place of a value on the slider in 1/1000: 50 % .. 200 % or -12 .. +12 semitones */
static int gs_slider_place(int32_t pitch_or_speed, int32_t semitone, bool semi)
{
    int p = semi ? 500 + (int)(((int64_t)semitone * 1000) / (24 * PITCH_SPEED_PRECISION))
                 : 500 + gs_log2_permille(pitch_or_speed) / 2;
    return MAX(0, MIN(1000, p));
}

static void gs_slider(int x, int y, int mark_y, int place)
{
    const struct bitmap *track = &gs_bm[GS_TRACK];
    int fill = place * track->width / 1000;
    gs_bmp(&gs_bm[GS_MARK], x + track->width / 2 - 1, mark_y);
    gs_bmp(track, x, y);
    if (fill > 0)
        rb->lcd_bmp_part(&gs_bm[GS_FILL], 0, 0, x, y, fill, gs_bm[GS_FILL].height);
    gs_bmp(&gs_bm[GS_KNOB], x + fill - gs_bm[GS_KNOB].width / 2, y - 5);
}

/* "112,0 %" (one decimal) */
static void gs_format_percent(char *buf, size_t size, int32_t v)
{
    rb->snprintf(buf, size, "%ld%s%ld %%", (long)(v / PITCH_SPEED_PRECISION),
                 rb->str(LANG_DECIMAL_SEPARATOR),
                 (long)((v % PITCH_SPEED_PRECISION) / (PITCH_SPEED_PRECISION / 10)));
}

/* "+2,71" semitones (two decimals), a real minus */
static void gs_format_semitone(char *buf, size_t size, int32_t s)
{
    rb->snprintf(buf, size, "%s%d%s%02d", s < 0 ? GS_MINUS : "+",
                 abs(s / PITCH_SPEED_PRECISION), rb->str(LANG_DECIMAL_SEPARATOR),
                 abs((s % PITCH_SPEED_PRECISION) / (PITCH_SPEED_PRECISION / 100)));
}

/* one of the two keys at the bottom (left: side -1, right: 1) */
static void gs_key(int side, const char *label, const char *value)
{
    bool held = gs_held == side;
    int x = side < 0 ? 13 : 177;          /* picture with its shadow */
    int ex = x + 1, ew = 128;             /* the key itself */
    gs_bmp(&gs_bm[held ? GS_KEY_HELD : GS_KEY], x, 176);
    if (side < 0)
        gs_bmp(&gs_bm[held ? GS_ARR_L_W : GS_ARR_L], 23, 193);
    else
        gs_bmp(&gs_bm[held ? GS_ARR_R_W : GS_ARR_R], 292, 193);
    gs_text_centred(gs_fonts[GS_F11], held ? GS_WHITE88 : GS_GREY, ex, ew, 180, label);
    gs_text_centred(gs_fonts[GS_F14], held ? GS_WHITE : GS_BLACK, ex, ew, 192, value);
}

static void gs_draw(int32_t pitch, int32_t semitone, int32_t speed)
{
    char buf[32];
    bool semi = rb->global_settings->pitch_mode_semitone;
    bool stretch = rb->global_settings->pitch_mode_timestretch &&
                   rb->dsp_timestretch_available();

    rb->lcd_set_viewport(NULL);
    rb->lcd_bitmap(gs_field, 0, 0, LCD_WIDTH, LCD_HEIGHT);
    rb->lcd_set_drawmode(DRMODE_FG);

    /* top row: mode capsule (play switches it), timestretch capsule, the
     * round keys 100 % (hold select) and close (menu), divider */
    const char *mode = semi ? rb->str(LANG_SEMITONE) : rb->str(LANG_TEMPO_PERCENT);
    int cw = 31 + gs_width(gs_fonts[GS_F13], mode) + 11;
    gs_capsule(14, 14, cw);
    gs_bmp(&gs_bm[GS_ICON_MODE], 25, 21);
    gs_text(gs_fonts[GS_F13], GS_DARK, 45, 18, mode);
    if (stretch)
    {
        const char *ts = rb->str(LANG_TEMPO_TIMESTRETCH);
        int tx = 14 + cw + 8;
        gs_capsule(tx, 14, 10 + gs_width(gs_fonts[GS_F13], ts) + 10);
        gs_text(gs_fonts[GS_F13], GS_DARK, tx + 10, 18, ts);
    }
    gs_bmp(&gs_bm[GS_KEY_100], 250, 14);
    gs_bmp(&gs_bm[GS_KEY_BACK], 282, 14);
    gs_bmp(&gs_bm[GS_DIVIDER], 14, 58);

    if (!stretch)
    {
        /* field with the rate, slider between tortoise and hare */
        gs_bmp(&gs_bm[GS_FIELD], 80, 72);
        gs_text_centred(gs_fonts[GS_F11], GS_GREY, 80, 160, 80,
                        rb->str(LANG_PLAYBACK_RATE));
        if (semi)
            gs_format_semitone(buf, sizeof(buf), semitone);
        else
            gs_format_percent(buf, sizeof(buf), pitch);
        gs_text_centred(gs_fonts[GS_F17], GS_BLACK, 80, 160, 95, buf);
        gs_bmp(&gs_bm[GS_SLOWER], 22, 139);
        gs_bmp(&gs_bm[GS_FASTER], 276, 138);
        gs_slider(55, 142, 155, gs_slider_place(pitch, semitone, semi));

        /* keys: hold for -2 % / +2 %, the wheel between them */
        const char *hold = rb->str(LANG_TEMPO_HOLD);
        gs_key(-1, hold, GS_MINUS "2 %");
        gs_key(1, hold, "+2 %");
        gs_bmp(&gs_bm[GS_WHEEL], 148, 185);
    }
    else
    {
        /* two rows like the quick menu: pitch (wheel), speed (left/right) */
        gs_bmp(&gs_bm[GS_ICON_PITCH], 14, 74);
        gs_slider(40, 78, 89, gs_slider_place(pitch, semitone, semi));
        if (semi)
            gs_format_semitone(buf, sizeof(buf), semitone);
        else
            gs_format_percent(buf, sizeof(buf), pitch);
        gs_text(gs_fonts[GS_F12], GS_DARK, 306 - gs_width(gs_fonts[GS_F12], buf), 74, buf);

        gs_bmp(&gs_bm[GS_ICON_SPEED], 14, 110);
        gs_slider(40, 114, 125, gs_slider_place(speed, 0, false));
        gs_format_percent(buf, sizeof(buf), speed);
        gs_text(gs_fonts[GS_F12], at_limit ? GS_RED : GS_DARK,
                306 - gs_width(gs_fonts[GS_F12], buf), 110, buf);
        if (at_limit)
        {
            const char *lim = rb->str(LANG_STRETCH_LIMIT);
            gs_text(gs_fonts[GS_F11], GS_RED, 306 - gs_width(gs_fonts[GS_F11], lim), 125, lim);
        }

        const char *spd = rb->str(LANG_SPEED);
        gs_key(-1, spd, rb->str(LANG_PITCH_DOWN));
        gs_key(1, spd, rb->str(LANG_PITCH_UP));
    }

    rb->lcd_set_drawmode(DRMODE_SOLID);
    rb->lcd_setfont(FONT_UI);
    rb->lcd_update();
}
#endif /* IPOD_6G */

static void speak_pitch_mode(bool enqueue)
{
    bool timestretch_mode = rb->global_settings->pitch_mode_timestretch && rb->dsp_timestretch_available();
    if (timestretch_mode)
        rb->talk_id(VOICE_PITCH_TIMESTRETCH_MODE, enqueue);
    if (rb->global_settings->pitch_mode_semitone)
        rb->talk_id(VOICE_PITCH_SEMITONE_MODE, timestretch_mode ? true : enqueue);
    else
        rb->talk_id(VOICE_PITCH_ABSOLUTE_MODE, timestretch_mode ? true : enqueue);
    return;
}

/*
 * Fixes the viewports so they represent the 3 rows, and adds a little margin
 * on all sides for the icons (which are drawn outside of the grid
 *
 * The modified viewports need to be passed to the touchscreen handling function
 **/
static void pitchscreen_fix_viewports(struct viewport *parent,
        struct viewport pitch_viewports[PITCH_ITEM_COUNT])
{
    int i, font_height;
    font_height = rb->font_get(parent->font)->height;
    for (i = 0; i < PITCH_ITEM_COUNT; i++)
    {
        pitch_viewports[i] = *parent;
        pitch_viewports[i].height = parent->height / PITCH_ITEM_COUNT;
        pitch_viewports[i].x += ICON_BORDER;
        pitch_viewports[i].width -= 2*ICON_BORDER;
    }
    pitch_viewports[PITCH_TOP].y      += ICON_BORDER;
    pitch_viewports[PITCH_TOP].height -= ICON_BORDER;

    if(pitch_viewports[PITCH_MID].height < font_height * 2)
        pitch_viewports[PITCH_MID].height = font_height * 2;

    pitch_viewports[PITCH_MID].y = pitch_viewports[PITCH_TOP].y
                                 + pitch_viewports[PITCH_TOP].height;

    pitch_viewports[PITCH_BOTTOM].y = pitch_viewports[PITCH_MID].y
                                    + pitch_viewports[PITCH_MID].height;

    pitch_viewports[PITCH_BOTTOM].height -= ICON_BORDER;
}

/* must be called before pitchscreen_draw, or within
 * since it neither clears nor updates the display */
static void pitchscreen_draw_icons(struct screen *display,
                                   struct viewport *parent)
{

    display->set_viewport(parent);
    int w, h;
    const unsigned char* uparrow = cbmp_get_icon(CBMP_Mono_7x8, Icon_UpArrow, &w, &h);
    if (uparrow)
        display->mono_bitmap(uparrow, parent->width/2 - 3, 2, w, h);

    const unsigned char* dnarrow = cbmp_get_icon(CBMP_Mono_7x8, Icon_DownArrow, &w, &h);
    if (dnarrow)
        display->mono_bitmap(dnarrow, parent->width /2 - 3, parent->height - 10, w, h);

    const unsigned char* fastfwd = cbmp_get_icon(CBMP_Mono_7x8, Icon_FastForward, &w, &h);
    if (fastfwd)
        display->mono_bitmap(fastfwd, parent->width - 10, parent->height /2 - 4, 7, 8);

    const unsigned char* fastrew = cbmp_get_icon(CBMP_Mono_7x8, Icon_FastBackward, &w, &h);
    if (fastrew)
        display->mono_bitmap(fastrew, 2, parent->height /2 - 4, w, h);

    display->update_viewport();

}

static void pitchscreen_draw(struct screen *display, int max_lines,
                             struct viewport pitch_viewports[PITCH_ITEM_COUNT],
                             int32_t pitch, int32_t semitone
                             ,int32_t speed
                             )
{
    const char* ptr;
    char buf[32];
    int w, h;
    bool show_lang_pitch;
    struct viewport *last_vp = NULL;

     /* "Pitch up/Pitch down" - hide for a small screen,
      * the text is drawn centered automatically
      *
      * note: this assumes 5 lines always fit on a touchscreen (should be
      * reasonable) */
    if (max_lines >= 5)
    {
        int w, h;
        struct viewport *vp = &pitch_viewports[PITCH_TOP];
        last_vp = display->set_viewport(vp);
        display->clear_viewport();
#ifdef HAVE_TOUCHSCREEN
        /* two arrows in the top row, left and right column */
        char *arrows[] = { "<", ">"};
        display->getstringsize(arrows[0], &w, &h);
        display->putsxy(0, vp->height/2 - h/2, arrows[0]);
        display->putsxy(vp->width - w, vp->height/2 - h/2, arrows[1]);
#endif
        /* UP: Pitch Up */
        if (rb->global_settings->pitch_mode_semitone)
            ptr = rb->str(LANG_PITCH_UP_SEMITONE);
        else
            ptr = rb->str(LANG_PITCH_UP);

        display->getstringsize(ptr, &w, NULL);
        /* draw text */
        display->putsxy(vp->width/2 - w/2, 0, ptr);
        display->update_viewport();

        /* DOWN: Pitch Down */
        vp = &pitch_viewports[PITCH_BOTTOM];
        display->set_viewport(vp);
        display->clear_viewport();

#ifdef HAVE_TOUCHSCREEN
        ptr = rb->str(LANG_KBD_OK);
        display->getstringsize(ptr, &w, &h);
        /* one OK in the middle first column of the vp (at half height) */
        display->putsxy(vp->width/6 - w/2, vp->height/2 - h/2, ptr);
        /* one OK in the middle of the last column of the vp (at half height) */
        display->putsxy(5*vp->width/6 - w/2, vp->height/2 - h/2, ptr);
#endif
        if (rb->global_settings->pitch_mode_semitone)
            ptr = rb->str(LANG_PITCH_DOWN_SEMITONE);
        else
            ptr = rb->str(LANG_PITCH_DOWN);
        display->getstringsize(ptr, &w, &h);
        /* draw text */
        display->putsxy(vp->width/2 - w/2, vp->height - h, ptr);
        display->update_viewport();
    }

    /* Middle section */
    display->set_viewport(&pitch_viewports[PITCH_MID]);
    display->clear_viewport();
    int width_used = 0;

    /* Middle section upper line - hide for a small screen */
    if ((show_lang_pitch = (max_lines >= 3)))
    {
        if(rb->global_settings->pitch_mode_timestretch)
        {
            /* Pitch:XXX.X% */
            if(rb->global_settings->pitch_mode_semitone)
            {
                rb->snprintf(buf, sizeof(buf), "%s: %s%d.%02d", rb->str(LANG_PITCH),
                         semitone >= 0 ? "+" : "-",
                         abs(semitone / PITCH_SPEED_PRECISION),
                         abs((semitone % PITCH_SPEED_PRECISION) /
                                         (PITCH_SPEED_PRECISION / 100))
                        );
            }
            else
            {
                rb->snprintf(buf, sizeof(buf), "%s: %ld.%ld%%", rb->str(LANG_PITCH),
                         pitch / PITCH_SPEED_PRECISION,
                         (pitch % PITCH_SPEED_PRECISION) /
                         (PITCH_SPEED_PRECISION / 10));
            }
        }
        else
        {
            /* Rate */
            rb->snprintf(buf, sizeof(buf), "%s:", rb->str(LANG_PLAYBACK_RATE));
        }
        display->getstringsize(buf, &w, &h);
        display->putsxy((pitch_viewports[PITCH_MID].width  / 2) - (w / 2),
                        (pitch_viewports[PITCH_MID].height / 2) - h, buf);
        if (w > width_used)
            width_used = w;
    }

    /* Middle section lower line */
    /* "Speed:XXX%" */
    if(rb->global_settings->pitch_mode_timestretch)
    {
        rb->snprintf(buf, sizeof(buf), "%s: %ld.%ld%%", rb->str(LANG_SPEED),
                 speed / PITCH_SPEED_PRECISION,
                 (speed % PITCH_SPEED_PRECISION) / (PITCH_SPEED_PRECISION / 10));
    }
    else
    {
        if(rb->global_settings->pitch_mode_semitone)
        {
            rb->snprintf(buf, sizeof(buf), "%s%d.%02d",
                     semitone >= 0 ? "+" : "-",
                     abs(semitone / PITCH_SPEED_PRECISION),
                     abs((semitone % PITCH_SPEED_PRECISION) /
                                     (PITCH_SPEED_PRECISION / 100))
                    );
        }
        else
        {
            rb->snprintf(buf, sizeof(buf), "%ld.%ld%%",
                     pitch / PITCH_SPEED_PRECISION,
                     (pitch  % PITCH_SPEED_PRECISION) / (PITCH_SPEED_PRECISION / 10));
        }
    }

    display->getstringsize(buf, &w, &h);
    display->putsxy((pitch_viewports[PITCH_MID].width / 2) - (w / 2),
        show_lang_pitch ? (pitch_viewports[PITCH_MID].height / 2) :
                          (pitch_viewports[PITCH_MID].height / 2) - (h / 2),
        buf);
    if (w > width_used)
        width_used = w;

    /* "limit" and "timestretch" labels */
    if (max_lines >= 7)
    {
        if(at_limit)
        {
            const char * const p = rb->str(LANG_STRETCH_LIMIT);
            display->getstringsize(p, &w, &h);
            display->putsxy((pitch_viewports[PITCH_MID].width / 2) - (w / 2),
                            (pitch_viewports[PITCH_MID].height / 2) + h, p);
            if (w > width_used)
                width_used = w;
        }
    }

    /* Middle section left/right labels */
    const char *leftlabel = "-2%";
    const char *rightlabel = "+2%";
    if (rb->global_settings->pitch_mode_timestretch)
    {
        leftlabel = "<<";
        rightlabel = ">>";
    }

    /* Only display if they fit */
    display->getstringsize(leftlabel, &w, &h);
    width_used += w;
    display->getstringsize(rightlabel, &w, &h);
    width_used += w;

    if (width_used <= pitch_viewports[PITCH_MID].width)
    {
        display->putsxy(0, (pitch_viewports[PITCH_MID].height / 2) - (h / 2),
                        leftlabel);
        display->putsxy((pitch_viewports[PITCH_MID].width - w),
                        (pitch_viewports[PITCH_MID].height / 2) - (h / 2),
                        rightlabel);
    }
    display->update_viewport();
    display->set_viewport(last_vp);
}

static int32_t pitch_increase(int32_t pitch, int32_t pitch_delta, bool allow_cutoff
                          /* need this to maintain correct pitch/speed caps */
                          , int32_t speed
                          )
{
    int32_t new_pitch;
    int32_t new_stretch;
    at_limit = false;

    if (pitch_delta < 0)
    {
        /* for large jumps, snap up to whole numbers */
        if(allow_cutoff && pitch_delta <= -PITCH_SPEED_PRECISION &&
           (pitch + pitch_delta) % PITCH_SPEED_PRECISION != 0)
        {
            pitch_delta += PITCH_SPEED_PRECISION - ((pitch + pitch_delta) % PITCH_SPEED_PRECISION);
        }

        new_pitch = pitch + pitch_delta;

        if (new_pitch < PITCH_MIN)
        {
            if (!allow_cutoff)
            {
                return pitch;
            }
            new_pitch = PITCH_MIN;
            at_limit = true;
        }
    }
    else if (pitch_delta > 0)
    {
        /* for large jumps, snap down to whole numbers */
        if(allow_cutoff && pitch_delta >= PITCH_SPEED_PRECISION &&
           (pitch + pitch_delta) % PITCH_SPEED_PRECISION != 0)
        {
            pitch_delta -= (pitch + pitch_delta) % PITCH_SPEED_PRECISION;
        }

        new_pitch = pitch + pitch_delta;

        if (new_pitch > PITCH_MAX)
        {
            if (!allow_cutoff)
                return pitch;
            new_pitch = PITCH_MAX;
            at_limit = true;
        }
    }
    else
    {
        /* pitch_delta == 0 -> no real change */
        return pitch;
    }
    if (rb->dsp_timestretch_available())
    {
        /* increase the multiple to increase precision of this calculation */
        new_stretch = GET_STRETCH(new_pitch, speed);
        if(new_stretch < STRETCH_MIN)
        {
            /* we have to ignore allow_cutoff, because we can't have the */
            /* stretch go higher than STRETCH_MAX                        */
            new_pitch = GET_PITCH(speed, STRETCH_MIN);
        }
        else if(new_stretch > STRETCH_MAX)
        {
            /* we have to ignore allow_cutoff, because we can't have the */
            /* stretch go higher than STRETCH_MAX                        */
            new_pitch = GET_PITCH(speed, STRETCH_MAX);
        }

        if(new_stretch >= STRETCH_MAX ||
           new_stretch <= STRETCH_MIN)
        {
            at_limit = true;
        }
    }

    rb->sound_set_pitch(new_pitch);

    return new_pitch;
}

static int32_t get_semitone_from_pitch(int32_t pitch)
{
    int semitone = 0;
    int32_t fractional_index = 0;

    while(semitone < NUM_SEMITONES - 1 &&
          pitch >= semitone_table[semitone + 1])
    {
        semitone++;
    }


    /* now find the fractional part */
    while(pitch > (cent_interp[fractional_index + 1] *
                   semitone_table[semitone] / PITCH_SPEED_100))
    {
        /* Check to make sure fractional_index isn't too big */
        /* This should never happen. */
        if(fractional_index >= CENT_INTERP_NUM - 1)
        {
            break;
        }
        fractional_index++;
    }

    int32_t semitone_pitch_a = cent_interp[fractional_index] *
                               semitone_table[semitone] /
                               PITCH_SPEED_100;
    int32_t semitone_pitch_b = cent_interp[fractional_index + 1] *
                               semitone_table[semitone] /
                               PITCH_SPEED_100;
    /* this will be the integer offset from the cent_interp entry */
    int32_t semitone_frac_ofs = (pitch - semitone_pitch_a) * CENT_INTERP_INTERVAL /
                            (semitone_pitch_b - semitone_pitch_a);
    semitone = (semitone + SEMITONE_START) * PITCH_SPEED_PRECISION +
                     fractional_index * CENT_INTERP_INTERVAL +
                     semitone_frac_ofs;

    return semitone;
}

static int32_t get_pitch_from_semitone(int32_t semitone)
{
    int32_t adjusted_semitone = semitone - SEMITONE_START * PITCH_SPEED_PRECISION;

    /* Find the index into the semitone table */
    int32_t semitone_index = (adjusted_semitone / PITCH_SPEED_PRECISION);

    /* set pitch to the semitone's integer part value */
    int32_t pitch = semitone_table[semitone_index];
    /* get the range of the cent modification for future calculation */
    int32_t pitch_mod_a =
        cent_interp[(adjusted_semitone % PITCH_SPEED_PRECISION) /
                    CENT_INTERP_INTERVAL];
    int32_t pitch_mod_b =
        cent_interp[(adjusted_semitone % PITCH_SPEED_PRECISION) /
                    CENT_INTERP_INTERVAL + 1];
    /* figure out the cent mod amount based on the semitone fractional value */
    int32_t pitch_mod = pitch_mod_a + (pitch_mod_b - pitch_mod_a) *
                   (adjusted_semitone % CENT_INTERP_INTERVAL) / CENT_INTERP_INTERVAL;

    /* modify pitch based on the mod amount we just calculated */
    return (pitch * pitch_mod  + PITCH_SPEED_100 / 2) / PITCH_SPEED_100;
}

static int32_t pitch_increase_semitone(int32_t pitch,
                                       int32_t current_semitone,
                                       int32_t semitone_delta
                                       , int32_t speed
                                      )
{
    int32_t new_semitone = current_semitone;

    /* snap to the delta interval */
    if(current_semitone % semitone_delta != 0)
    {
        if(current_semitone > 0 && semitone_delta > 0)
            new_semitone += semitone_delta;
        else if(current_semitone < 0 && semitone_delta < 0)
            new_semitone += semitone_delta;

        new_semitone -= new_semitone % semitone_delta;
    }
    else
        new_semitone += semitone_delta;

    /* clamp the pitch so it doesn't go beyond the pitch limits */
    if(new_semitone < (SEMITONE_START * PITCH_SPEED_PRECISION))
    {
        new_semitone = SEMITONE_START * PITCH_SPEED_PRECISION;
        at_limit = true;
    }
    else if(new_semitone > (SEMITONE_END * PITCH_SPEED_PRECISION))
    {
        new_semitone = SEMITONE_END * PITCH_SPEED_PRECISION;
        at_limit = true;
    }

    int32_t new_pitch = get_pitch_from_semitone(new_semitone);

    int32_t new_stretch = GET_STRETCH(new_pitch, speed);

    /* clamp the pitch so it doesn't go beyond the stretch limits */
    if( new_stretch > STRETCH_MAX)
    {
        new_pitch = GET_PITCH(speed, STRETCH_MAX);
        new_semitone = get_semitone_from_pitch(new_pitch);
        at_limit = true;
    }
    else if (new_stretch < STRETCH_MIN)
    {
        new_pitch = GET_PITCH(speed, STRETCH_MIN);
        new_semitone = get_semitone_from_pitch(new_pitch);
        at_limit = true;
    }

    pitch_increase(pitch, new_pitch - pitch, false
                   , speed
                   );

    return new_semitone;
}

#ifdef HAVE_TOUCHSCREEN
/*
 * Check for touchscreen presses as per sketch above in this file
 *
 * goes through each row of the, checks whether the touchscreen
 * was pressed in it. Then it looks the columns of each row for specific actions
 */
static int pitchscreen_do_touchscreen(struct viewport vps[])
{
    short x, y;
    struct viewport *this_vp = &vps[PITCH_TOP];
    int ret;
    static bool wait_for_release = false;
    ret = rb->action_get_touchscreen_press_in_vp(&x, &y, this_vp);

    /* top row */
    if (ret > ACTION_UNKNOWN)
    {   /* press on top row, left or right column
         * only toggle mode if released */
        int column = this_vp->width / 3;
        if ((x < column || x > (2*column)) && (ret == BUTTON_REL))
            return ACTION_PS_TOGGLE_MODE;


        else if (x >= column && x <= (2*column))
        {   /* center column pressed */
            if (ret == BUTTON_REPEAT)
                return ACTION_PS_INC_BIG;
            else if (ret & BUTTON_REL)
                return ACTION_PS_INC_SMALL;
        }
        return ACTION_NONE;
    }

    /* now the center row */
    this_vp = &vps[PITCH_MID];
    ret = rb->action_get_touchscreen_press_in_vp(&x, &y, this_vp);

    if (ret > ACTION_UNKNOWN)
    {
        int column = this_vp->width / 3;

        if (x < column)
        {   /* left column */
            if (ret & BUTTON_REL)
            {
                wait_for_release = false;
                return ACTION_PS_NUDGE_LEFTOFF;
            }
            else if (ret & BUTTON_REPEAT)
                return ACTION_PS_SLOWER;
            if (!wait_for_release)
            {
                wait_for_release = true;
                return ACTION_PS_NUDGE_LEFT;
            }
        }
        else if (x > (2*column))
        {   /* right column */
            if (ret & BUTTON_REL)
            {
                wait_for_release = false;
                return ACTION_PS_NUDGE_RIGHTOFF;
            }
            else if (ret & BUTTON_REPEAT)
                return ACTION_PS_FASTER;
            if (!wait_for_release)
            {
                wait_for_release = true;
                return ACTION_PS_NUDGE_RIGHT;
            }
        }
        else
            /* center column was pressed */
            return ACTION_PS_RESET;
    }

    /* now the bottom row */
    this_vp = &vps[PITCH_BOTTOM];
    ret = rb->action_get_touchscreen_press_in_vp(&x, &y, this_vp);

    if (ret > ACTION_UNKNOWN)
    {
        int column = this_vp->width / 3;

        /* left or right column is exit */
        if ((x < column || x > (2*column)) && (ret == BUTTON_REL))
            return ACTION_PS_EXIT;
        else if (x >= column && x <= (2*column))
        {   /* center column was pressed */
            if (ret & BUTTON_REPEAT)
                return ACTION_PS_DEC_BIG;
            else if (ret & BUTTON_REL)
                return ACTION_PS_DEC_SMALL;
        }
        return ACTION_NONE;
    }
    return ACTION_NONE;
}

#endif
/*
    returns:
    0 on exit
    1 if USB was connected
*/

int gui_syncpitchscreen_run(void)
{
    int button;
    int32_t pitch = rb->sound_get_pitch();
    int32_t semitone;

    int32_t new_pitch;
    int32_t pitch_delta;
    bool nudged = false;
    int i, updated = 4, decimals = 0;
    bool exit = false;
    /* should maybe be passed per parameter later, not needed for now */
    struct viewport parent[NB_SCREENS];
    struct viewport pitch_viewports[NB_SCREENS][PITCH_ITEM_COUNT];
    int max_lines[NB_SCREENS];

    //push_current_activity(ACTIVITY_PITCHSCREEN);

    int32_t new_speed = 0, new_stretch;

    /* the speed variable holds the apparent speed of the playback */
    int32_t speed;
    if (rb->dsp_timestretch_available())
    {
        speed = GET_SPEED(pitch, rb->dsp_get_timestretch());
    }
    else
    {
        speed = pitch;
    }



    /* Count decimals for speaking */
    for (i = PITCH_SPEED_PRECISION; i >= 10; i /= 10)
        decimals++;

    /* set the semitone index based on the current pitch */
    semitone = get_semitone_from_pitch(pitch);

#ifdef IPOD_6G
    gs_held = 0;
    gs_active = gs_load();
#endif
    /* initialize pitchscreen vps */
    FOR_NB_SCREENS(i)
    {
        rb->viewport_set_defaults(&parent[i], i);
        max_lines[i] = viewport_get_nb_lines(&parent[i]);
        pitchscreen_fix_viewports(&parent[i], pitch_viewports[i]);
#ifdef IPOD_6G
        if (gs_active)
            continue;
#endif
        rb->screens[i]->set_viewport(&parent[i]);
        rb->screens[i]->clear_viewport();

        /* also, draw the icons now, it's only needed once */
        pitchscreen_draw_icons(rb->screens[i], &parent[i]);
    }


    while (!exit)
    {
#ifdef IPOD_6G
        if (gs_active)
            gs_draw(pitch, semitone, speed);
        else
#endif
        FOR_NB_SCREENS(i)
            pitchscreen_draw(rb->screens[i], max_lines[i],
                              pitch_viewports[i], pitch, semitone
                              , speed
                              );
        pitch_delta = 0;
        new_speed = 0;

        if (rb->global_settings->talk_menu && updated)
        {
            rb->talk_shutup();
            switch (updated)
            {
            case 1:
                if (rb->global_settings->pitch_mode_semitone)
                    rb->talk_value_decimal(semitone, UNIT_SIGNED, decimals, false);
                else
                    rb->talk_value_decimal(pitch, UNIT_PERCENT, decimals, false);
                break;
            case 2:
                rb->talk_value_decimal(speed, UNIT_PERCENT, decimals, false);
                break;
            case 3:
                speak_pitch_mode(false);
                break;
            case 4:
                if (rb->global_settings->pitch_mode_timestretch && rb->dsp_timestretch_available())
                    rb->talk_id(LANG_PITCH, false);
                else
                    rb->talk_id(LANG_PLAYBACK_RATE, false);
                rb->talk_value_decimal(pitch, UNIT_PERCENT, decimals, true);
                if (rb->global_settings->pitch_mode_timestretch && rb->dsp_timestretch_available())
                {
                    rb->talk_id(LANG_SPEED, true);
                    rb->talk_value_decimal(speed, UNIT_PERCENT, decimals, true);
                }
                speak_pitch_mode(true);
                break;
            default:
                break;
            }
        }
        updated = 0;

        button = rb->get_action(CONTEXT_PITCHSCREEN, HZ);

#ifdef HAVE_TOUCHSCREEN
        if (button == ACTION_TOUCHSCREEN)
        {
            FOR_NB_SCREENS(i)
                button = pitchscreen_do_touchscreen(pitch_viewports[i]);
        }
#endif
        switch (button)
        {
            case ACTION_PS_INC_SMALL:
                if(rb->global_settings->pitch_mode_semitone)
                    pitch_delta = SEMITONE_SMALL_DELTA;
                else
                    pitch_delta = PITCH_SMALL_DELTA;
                updated = 1;
                break;

            case ACTION_PS_INC_BIG:
                if(rb->global_settings->pitch_mode_semitone)
                    pitch_delta = SEMITONE_BIG_DELTA;
                else
                    pitch_delta = PITCH_BIG_DELTA;
                updated = 1;
                break;

            case ACTION_PS_DEC_SMALL:
                if(rb->global_settings->pitch_mode_semitone)
                    pitch_delta = -SEMITONE_SMALL_DELTA;
                else
                    pitch_delta = -PITCH_SMALL_DELTA;
                updated = 1;
                break;

            case ACTION_PS_DEC_BIG:
                if(rb->global_settings->pitch_mode_semitone)
                    pitch_delta = -SEMITONE_BIG_DELTA;
                else
                    pitch_delta = -PITCH_BIG_DELTA;
                updated = 1;
                break;

            case ACTION_PS_NUDGE_RIGHT:
#ifdef IPOD_6G
                gs_held = 1;
#endif
                if (!rb->global_settings->pitch_mode_timestretch)
                {
                    new_pitch = pitch_increase(pitch, PITCH_NUDGE_DELTA, false
                                               , speed
                        );
                    nudged = (new_pitch != pitch);
                    pitch = new_pitch;
                    semitone = get_semitone_from_pitch(pitch);
                    speed = pitch;
                    updated = nudged ? 1 : 0;
                    break;
                }
                else
                {
                    new_speed = speed + SPEED_SMALL_DELTA;
                    at_limit = false;
                    updated = 2;
                }
                break;

            case ACTION_PS_FASTER:
                if (rb->global_settings->pitch_mode_timestretch)
                {
                    new_speed = speed + SPEED_BIG_DELTA;
                    /* snap to whole numbers */
                    if(new_speed % PITCH_SPEED_PRECISION != 0)
                        new_speed -= new_speed % PITCH_SPEED_PRECISION;
                    at_limit = false;
                    updated = 2;
                }
                break;

            case ACTION_PS_NUDGE_RIGHTOFF:
#ifdef IPOD_6G
                gs_held = 0;
#endif
                if (nudged)
                {
                    pitch = pitch_increase(pitch, -PITCH_NUDGE_DELTA, false
                                           , speed
                        );
                    speed = pitch;
                    semitone = get_semitone_from_pitch(pitch);
                    nudged = false;
                    updated = 1;
                }
                break;

            case ACTION_PS_NUDGE_LEFT:
#ifdef IPOD_6G
                gs_held = -1;
#endif
                if (!rb->global_settings->pitch_mode_timestretch)
                {
                    new_pitch = pitch_increase(pitch, -PITCH_NUDGE_DELTA, false
                                               , speed
                        );
                    nudged = (new_pitch != pitch);
                    pitch = new_pitch;
                    semitone = get_semitone_from_pitch(pitch);
                    speed = pitch;
                    updated = nudged ? 1 : 0;
                    break;
                }
                else
                {
                    new_speed = speed - SPEED_SMALL_DELTA;
                    at_limit = false;
                    updated = 2;
                }
                break;

            case ACTION_PS_SLOWER:
                if (rb->global_settings->pitch_mode_timestretch)
                {
                    new_speed = speed - SPEED_BIG_DELTA;
                    /* snap to whole numbers */
                    if(new_speed % PITCH_SPEED_PRECISION != 0)
                        new_speed += PITCH_SPEED_PRECISION - speed % PITCH_SPEED_PRECISION;
                    at_limit = false;
                    updated = 2;
                }
                break;

            case ACTION_PS_NUDGE_LEFTOFF:
#ifdef IPOD_6G
                gs_held = 0;
#endif
                if (nudged)
                {
                    pitch = pitch_increase(pitch, PITCH_NUDGE_DELTA, false
                                           , speed
                        );
                    speed = pitch;
                    semitone = get_semitone_from_pitch(pitch);
                    nudged = false;
                    updated = 1;
                }
                break;

            case ACTION_PS_RESET:
                pitch = PITCH_SPEED_100;
                rb->sound_set_pitch(pitch);
                speed = PITCH_SPEED_100;
                if (rb->dsp_timestretch_available())
                {
                    rb->dsp_set_timestretch(PITCH_SPEED_100);
                    at_limit = false;
                }
                semitone = get_semitone_from_pitch(pitch);
                updated = 4;
                break;

            case ACTION_PS_TOGGLE_MODE:
                rb->global_settings->pitch_mode_semitone = !rb->global_settings->pitch_mode_semitone;

                if (rb->dsp_timestretch_available() && !rb->global_settings->pitch_mode_semitone)
                {
                    rb->global_settings->pitch_mode_timestretch = !rb->global_settings->pitch_mode_timestretch;
                    if(!rb->global_settings->pitch_mode_timestretch)
                    {
                        /* no longer in timestretch mode.  Reset speed */
                        speed = pitch;
                        rb->dsp_set_timestretch(PITCH_SPEED_100);
                    }
                }
                rb->settings_save();
                updated = 3;
                break;

            case ACTION_PS_EXIT:
                exit = true;
                break;

            default:
                if (rb->default_event_handler(button) == SYS_USB_CONNECTED)
                {
#ifdef IPOD_6G
                    gs_unload();
#endif
                    return 1;
                }
                break;
        }
        if (pitch_delta)
        {
            if (rb->global_settings->pitch_mode_semitone)
            {
                semitone = pitch_increase_semitone(pitch, semitone, pitch_delta
                                                , speed
                );
                pitch = get_pitch_from_semitone(semitone);
            }
            else
            {
                pitch = pitch_increase(pitch, pitch_delta, true
                                       , speed
                );
                semitone = get_semitone_from_pitch(pitch);
            }
            if (rb->global_settings->pitch_mode_timestretch)
            {
                /* do this to make sure we properly obey the stretch limits */
                new_speed = speed;
            }
            else
            {
                speed = pitch;
            }
        }

        if(new_speed)
        {
            new_stretch = GET_STRETCH(pitch, new_speed);

            /* limit the amount of stretch */
            if(new_stretch > STRETCH_MAX)
            {
                new_stretch = STRETCH_MAX;
                new_speed = GET_SPEED(pitch, new_stretch);
            }
            else if(new_stretch < STRETCH_MIN)
            {
                new_stretch = STRETCH_MIN;
                new_speed = GET_SPEED(pitch, new_stretch);
            }

            new_stretch = GET_STRETCH(pitch, new_speed);
            if(new_stretch >= STRETCH_MAX ||
               new_stretch <= STRETCH_MIN)
            {
                at_limit = true;
            }

            /* set the amount of stretch */
            rb->dsp_set_timestretch(new_stretch);

            /* update the speed variable with the new speed */
            speed = new_speed;

            /* Reset new_speed so we only call dsp_set_timestretch */
            /* when needed                                         */
            new_speed = 0;
        }
        rb->yield();
    }

    //pop_current_activity();
#ifdef IPOD_6G
    gs_unload();
#endif

    /* Clean up */
    FOR_NB_SCREENS(i)
    {
        rb->screens[i]->set_viewport(NULL);
    }

    return 0;
}

static int arg_callback(char argchar, const char **parameter, void *userdata)
{
    (void)userdata;
    int ret;
    long num, dec;
    bool bret;
    //rb->splashf(100, "Arg: %c", argchar);
    while (*parameter[0] > '/' && ispunct(*parameter[0])) (*parameter)++;
    switch (tolower(argchar))
    {
        case 'q' :
            pitch_vars.flags &= ~PVAR_VERBOSE;
            break;
        case 'g' :
            pitch_vars.flags |= PVAR_GUI;
            break;
        case 'p' :
            ret = longnum_parse(parameter, &num, &dec);
            if (ret)
            {
                dec /= (ARGPARSE_FRAC_DEC_MULTIPLIER / PITCH_SPEED_PRECISION);
                if (num < 0)
                    dec = -dec;
                pitch_vars.pitch = (num * PITCH_SPEED_PRECISION + (dec % PITCH_SPEED_PRECISION));
            }
            break;
        case 'k' :
            ret = bool_parse(parameter, &bret);
            if (ret)
            {
                if(!bret && rb->dsp_timestretch_available())
                {
                    /* no longer in timestretch mode.  Reset speed */
                    rb->dsp_set_timestretch(PITCH_SPEED_100);
                }
                rb->dsp_timestretch_enable(bret);
                if ((pitch_vars.flags & PVAR_VERBOSE) == PVAR_VERBOSE)
                    rb->splashf(HZ, "Timestretch: %s", bret ? "true" : "false");
                int n = 10; /* 1 second */
                while (bret && n-- > 0 && !rb->dsp_timestretch_available())
                {
                    rb->sleep(HZ / 10);
                }
            }
            break;
        case 's' :
            ret = longnum_parse(parameter, &num, &dec);
            if (ret && rb->dsp_timestretch_available())
            {
                dec /= (ARGPARSE_FRAC_DEC_MULTIPLIER / PITCH_SPEED_PRECISION);
                if (num < 0)
                    break;
                pitch_vars.speed = (num * PITCH_SPEED_PRECISION + (dec % PITCH_SPEED_PRECISION));

            }
            break;
        default :
            rb->splashf(HZ, "Unknown switch '%c'",argchar);
            //return 0;
    }

    return 1;
}

void fill_pitchvars(struct pvars *pv)
{
    if (!pv)
        return;
    pv->pitch = rb->sound_get_pitch();

    /* the speed variable holds the apparent speed of the playback */
    if (rb->dsp_timestretch_available())
    {
        pv->speed = GET_SPEED(pv->pitch, rb->dsp_get_timestretch());
    }
    else
    {
        pv->speed = pv->pitch;
    }

    pv->stretch = GET_STRETCH(pv->pitch, pv->speed);
    pv->flags |= PVAR_VERBOSE;

}
/* plugin entry point */
enum plugin_status plugin_start(const void* parameter)
{
 /* pitch_screen
 *  accepts args -q, -g, -p=, -s=, -k=; (= sign is optional)
 * -q silences output splash
 * -g runs the gui (DEFAULT)
 * -p100 would set pitch to 100%
 * -s=90 sets speed to 90% if timestrech is enabled
 * -k=true -k1 enables time stretch -k0 -kf-kn disables
*/
    enum plugin_status ret = PLUGIN_OK;
    bool gui = false;
    rb->pcmbuf_set_low_latency(true);

    /* Figure out whether to be in timestretch mode */
    if (parameter == NULL) /* gui mode */
    {
        if (rb->global_settings->pitch_mode_timestretch && !rb->dsp_timestretch_available())
        {
            rb->global_settings->pitch_mode_timestretch = false;
            rb->settings_save();
        }
        gui = true;
    }
    else
    {
        struct pvars cur;
        fill_pitchvars(&cur);
        fill_pitchvars(&pitch_vars);
        argparse((const char*) parameter, -1, NULL, &arg_callback);
        if (pitch_vars.pitch != cur.pitch)
        {
            rb->sound_set_pitch(pitch_vars.pitch);
            pitch_vars.pitch = rb->sound_get_pitch();
            if ((pitch_vars.flags & PVAR_VERBOSE) == PVAR_VERBOSE)
                rb->splashf(HZ, "pitch: %ld.%02ld%%",
                            pitch_vars.pitch / PITCH_SPEED_PRECISION,
                            pitch_vars.pitch % PITCH_SPEED_PRECISION);
        }
        if (pitch_vars.speed != cur.speed)
        {
                pitch_vars.stretch = GET_STRETCH(pitch_vars.pitch, pitch_vars.speed);

                /* limit the amount of stretch */
                if(pitch_vars.stretch > STRETCH_MAX)
                {
                    pitch_vars.stretch = STRETCH_MAX;
                    pitch_vars.speed = GET_SPEED(pitch_vars.pitch, pitch_vars.stretch);
                }
                else if(pitch_vars.stretch < STRETCH_MIN)
                {
                    pitch_vars.stretch = STRETCH_MIN;
                    pitch_vars.speed = GET_SPEED(pitch_vars.pitch, pitch_vars.stretch);
                }

                pitch_vars.stretch = GET_STRETCH(pitch_vars.pitch, pitch_vars.speed);
                if ((pitch_vars.flags & PVAR_VERBOSE) == PVAR_VERBOSE)
                    rb->splashf(HZ, "speed: %ld.%02ld%%",
                                pitch_vars.speed / PITCH_SPEED_PRECISION,
                                pitch_vars.speed % PITCH_SPEED_PRECISION);
                /* set the amount of stretch */
                rb->dsp_set_timestretch(pitch_vars.stretch);
        }
        gui = ((pitch_vars.flags & PVAR_GUI) == PVAR_GUI);
        if ((pitch_vars.flags & PVAR_VERBOSE) == PVAR_VERBOSE)
            rb->splashf(HZ, "GUI: %d", gui);

    }

    if (gui && gui_syncpitchscreen_run() == 1)
        ret = PLUGIN_USB_CONNECTED;
    rb->pcmbuf_set_low_latency(false);
    return ret;
}
