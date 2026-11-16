/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2006 Dan Everton
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

#include "config.h"
#include <stdio.h>
#include <stdbool.h>
#include <string.h>
#include "eq_menu.h"
#include "system.h"
#include "kernel.h"
#include "lcd.h"
#include "list.h"
#include "menu.h"
#include "action.h"
#include "settings.h"
#include "rbpaths.h"
#include "screens.h"
#include "icons.h"
#include "font.h"
#include "lang.h"
#include "talk.h"
#include "misc.h"
#include "sound.h"
#include "dsp_proc_settings.h"
#include "tree.h"
#include "screen_access.h"
#include "keyboard.h"
#include "gui/scrollbar.h"
#include "menu_common.h"
#include "viewport.h"
#include "exported_menus.h"
#include "pcmbuf.h"
#include "option_select.h"
#include "string-extra.h"

static void eq_apply(void);

/*
 * Utility functions
 */

const char* eq_q_format(char* buffer, size_t buffer_size, int value, const char* unit)
{
    snprintf(buffer, buffer_size, "%d.%d %s", value / EQ_USER_DIVISOR,
         value % EQ_USER_DIVISOR, unit);
    return buffer;
}

const char* eq_precut_format(char* buffer, size_t buffer_size, int value, const char* unit)
{
    snprintf(buffer, buffer_size, "%s%d.%d %s", value == 0 ? " " : "-",
        value / EQ_USER_DIVISOR, value % EQ_USER_DIVISOR, unit);
    return buffer;
}

void eq_enabled_option_callback(bool enabled)
{
    (void)enabled;
    eq_apply();
}

/*
 * Settings functions
 */
static void eq_apply(void)
{
    dsp_eq_enable(global_settings.eq_enabled);
    dsp_set_eq_precut(global_settings.eq_precut);
    /* Update all bands */
    for(int i = 0; i < EQ_NUM_BANDS; i++) {
        dsp_set_eq_coefs(i, &global_settings.eq_band_settings[i]);
    }
}

static int eq_setting_callback(int action,
                               const struct menu_item_ex *this_item,
                               struct gui_synclist *this_list)
{
    (void)this_list;
    switch (action)
    {
        case ACTION_ENTER_MENUITEM:
            action = lowlatency_callback(action, this_item, NULL);
            break;
        case ACTION_EXIT_MENUITEM:
            eq_apply();
            action = lowlatency_callback(action, this_item, NULL);
            break;
    }

    return action;
}
MENUITEM_SETTING(eq_enable, &global_settings.eq_enabled, eq_setting_callback);
MENUITEM_SETTING(eq_precut, &global_settings.eq_precut, eq_setting_callback);

static char* gainitem_get_name(int selected_item, void *data, char *buffer, size_t len)
{
    (void)data;
    snprintf(buffer, len, str(LANG_EQUALIZER_GAIN_ITEM),
            global_settings.eq_band_settings[selected_item].cutoff);

    return buffer;
}

static int gainitem_speak_item(int selected_item, void *data)
{
    (void)data;
    talk_number(global_settings.eq_band_settings[selected_item].cutoff, false);
    talk_id(LANG_EQUALIZER_GAIN_ITEM, true);
    return 0;
}

static enum themable_icons gainitem_get_icon(int selected_item, void * data)
{
    (void)selected_item;
    (void)data;

    return Icon_Menu_functioncall;
}

static const char* db_format(char* buffer, size_t buffer_size, int value,
                      const char* unit)
{
    int v = abs(value);

    snprintf(buffer, buffer_size, "%s%d.%d %s", value < 0 ? "-" : "",
             v / 10, v % 10, unit);
    return buffer;
}

static int32_t get_dec_talkid(int value, int unit)
{
    return TALK_ID_DECIMAL(value, 1, unit);
}

static const struct int_setting gain_int_setting = {
    .option_callback = NULL,
    .unit = UNIT_DB,
    .step = EQ_GAIN_STEP,
    .min = EQ_GAIN_MIN,
    .max = EQ_GAIN_MAX,
    .formatter = db_format,
    .get_talk_id = get_dec_talkid,
};

static const struct int_setting q_int_setting = {
    .option_callback = NULL,
    .unit = UNIT_INT,
    .step = EQ_Q_STEP,
    .min = EQ_Q_MIN,
    .max = EQ_Q_MAX,
    .formatter = eq_q_format,
    .get_talk_id = get_dec_talkid,
};

static const struct int_setting cutoff_int_setting = {
    .option_callback = NULL,
    .unit = UNIT_HERTZ,
    .step = EQ_CUTOFF_STEP,
    .min = EQ_CUTOFF_MIN,
    .max = EQ_CUTOFF_MAX,
    .formatter = NULL,
    .get_talk_id = NULL,
};

static const struct choice_setting type_choice_setting = {
    .option_callback = NULL,
    .count = 3,
    .cfg_vals = "low_shelf,peaking,high_shelf",
    {.desc = (const unsigned char*[]) {
        ID2P(LANG_EQUALIZER_BAND_LOW_SHELF),
        ID2P(LANG_EQUALIZER_BAND_PEAK),
        ID2P(LANG_EQUALIZER_BAND_HIGH_SHELF),
    }}
};

static int simplelist_action_callback(int action, struct gui_synclist *lists)
{
    (void)lists;
    if (action == ACTION_STD_OK)
        return ACTION_STD_CANCEL;
    return action;
}

static int eq_do_simple_menu(void * param)
{
    (void)param;
    struct simplelist_info info;
    struct settings_list setting;
    char title[MAX_PATH];

    simplelist_info_init(&info, str(LANG_EQUALIZER_GAIN), EQ_NUM_BANDS, NULL);
    info.get_name = (list_get_name*)gainitem_get_name;
    if(global_settings.talk_menu)
        info.get_talk = gainitem_speak_item;
    info.get_icon = gainitem_get_icon;
    info.action_callback = simplelist_action_callback;
    info.selection = -1;
    info.title_icon = Icon_Submenu;
    setting.flags = F_BANFROMQS|F_INT_SETTING|F_T_INT|F_NO_WRAP;
    setting.lang_id = LANG_GAIN;
    setting.default_val.int_ = 0;
    setting.int_setting = &gain_int_setting;

    while (true)
    {
        simplelist_show_list(&info);
        if (info.selection < 0)
            break;
        pcmbuf_set_low_latency(true);
        setting.setting = &global_settings.eq_band_settings[info.selection].gain;
        option_screen(&setting, NULL, false,
                gainitem_get_name(info.selection, NULL, title, MAX_PATH));
        eq_apply();
        pcmbuf_set_low_latency(false);
    }
    return 0;
}
MENUITEM_FUNCTION(gain_menu, 0, ID2P(LANG_EQUALIZER_GAIN),
	              eq_do_simple_menu, NULL, Icon_Submenu);

static void selection_to_banditem(int selection, int expanded_band, int *band, int *item)
{
    int diff = selection - expanded_band;

    if (expanded_band < 0 || diff < 0)
    {
        *item = 0;
        *band = selection;
    }
    else if (diff < 5)
    {
        *item = selection - expanded_band;
        *band = expanded_band;
    }
    else
    {
        *item = 0;
        *band = expanded_band + diff - 4;
    }
}

static char *advancedmenu_item_get_name(int selected_item, void *data, char *buffer, size_t len)
{
    int band;
    int item;
    int lang = -1;

    selection_to_banditem(selected_item, *(intptr_t*)data, &band, &item);

    switch (item)
    {
    case 0: /* Band title */
        snprintf(buffer, len, str(LANG_EQUALIZER_BAND), band);
        return buffer;
    case 1: /* cutoff */
        if (global_settings.eq_band_settings[band].type == EQ_FILTER_PEAK)
            lang = LANG_EQUALIZER_BAND_CENTER;
        else
            lang = LANG_EQUALIZER_BAND_CUTOFF;
        break;
    case 2: /* Q */
        lang = LANG_EQUALIZER_BAND_Q;
        break;
    case 3: /* Gain */
        lang = LANG_GAIN;
        break;
    case 4: /* Type */
        lang = LANG_EQUALIZER_FILTER_TYPE;
        break;
    }

    if(lang < 0)
        buffer[0] = 0;
    else {
        buffer[0] = '\t';
        strmemccpy(&buffer[1], str(lang), len - 1);
    }

    return buffer;
}

static int advancedmenu_speak_item(int selected_item, void *data)
{
    (void)data;
    int band;
    int item;
    int lang = -1;

    selection_to_banditem(selected_item, *(intptr_t*)data, &band, &item);

    switch (item)
    {
    case 0: /* Band title */
        talk_id(LANG_EQUALIZER_BAND, false);
        talk_number(band, true);
        return -1;
    case 1: /* cutoff */
        if (global_settings.eq_band_settings[band].type == EQ_FILTER_PEAK)
            lang = LANG_EQUALIZER_BAND_CENTER;
        else
            lang = LANG_EQUALIZER_BAND_CUTOFF;
        break;
    case 2: /* Q */
        lang = LANG_EQUALIZER_BAND_Q;
        break;
    case 3: /* Gain */
        lang = LANG_GAIN;
        break;
    }
    talk_id(lang, true);
    return -1;
}

static enum themable_icons advancedmenu_get_icon(int selected_item, void * data)
{
    (void)data;
    int band;
    int item;

    selection_to_banditem(selected_item, *(intptr_t*)data, &band, &item);

    if (item == 0)
        return Icon_Submenu;
    else
        return Icon_Menu_setting;
}
extern struct eq_band_setting eq_defaults[EQ_NUM_BANDS];

static int eq_do_advanced_menu(void * param)
{
    (void)param;
    struct simplelist_info info;
    struct settings_list setting;
    char title[MAX_PATH];
    int band, item;
    intptr_t selected_band = -1;

    simplelist_info_init(&info, str(LANG_EQUALIZER_ADVANCED),
            EQ_NUM_BANDS, &selected_band);
    info.get_name = (list_get_name*)advancedmenu_item_get_name;
    if(global_settings.talk_menu)
        info.get_talk = advancedmenu_speak_item;
    info.get_icon = advancedmenu_get_icon;
    info.action_callback = simplelist_action_callback;
    info.selection = -1;
    info.title_icon = Icon_EQ;

    while (true)
    {
        simplelist_show_list(&info);
        if (info.selection < 0)
            break;
        selection_to_banditem(info.selection, selected_band, &band, &item);
        switch (item)
        {
            case 0: /* title, do nothing */
            {
                int extra;
                if (selected_band == band)
                {
                    extra = 0;
                    selected_band = -1;
                }
                else
                {
                    extra = 4;
                    selected_band = band;
                }
                info.selection = band;
                info.count = EQ_NUM_BANDS + extra;
                continue;
            }
            case 1: /* cutoff */
                setting.flags = F_BANFROMQS|F_INT_SETTING|F_T_INT|F_NO_WRAP;
                if (global_settings.eq_band_settings[band].type != EQ_FILTER_PEAK)
                    setting.lang_id = LANG_EQUALIZER_BAND_CUTOFF;
                else
                    setting.lang_id = LANG_EQUALIZER_BAND_CENTER;
                setting.default_val.int_ = eq_defaults[band].cutoff;
                setting.int_setting = &cutoff_int_setting;
                setting.setting = &global_settings.eq_band_settings[band].cutoff;
                break;
            case 2: /* Q */
                setting.flags = F_BANFROMQS|F_INT_SETTING|F_T_INT|F_NO_WRAP;
                setting.lang_id = LANG_EQUALIZER_BAND_Q;
                setting.default_val.int_ = eq_defaults[band].q;
                setting.int_setting = &q_int_setting;
                setting.setting = &global_settings.eq_band_settings[band].q;
                break;
            case 3: /* Gain */
                setting.flags = F_BANFROMQS|F_INT_SETTING|F_T_INT|F_NO_WRAP;
                setting.lang_id = LANG_GAIN;
                setting.default_val.int_ = eq_defaults[band].gain;
                setting.int_setting = &gain_int_setting;
                setting.setting = &global_settings.eq_band_settings[band].gain;
                break;
            case 4: /* Type */
                setting.flags = F_BANFROMQS|F_CHOICE_SETTING|F_T_INT;
                setting.lang_id = LANG_EQUALIZER_FILTER_TYPE;
                setting.default_val.int_ = eq_defaults[band].type;
                setting.choice_setting = &type_choice_setting;
                setting.setting = &global_settings.eq_band_settings[band].type;
                break;
        }
        pcmbuf_set_low_latency(true);
        advancedmenu_item_get_name(info.selection, &selected_band, title, MAX_PATH);

        option_screen(&setting, NULL, false, title[0] == '\t' ? &title[1] : title);
        eq_apply();
        pcmbuf_set_low_latency(false);
    }
    return 0;
}
MENUITEM_FUNCTION(advanced_menu, 0, ID2P(LANG_EQUALIZER_ADVANCED),
                  eq_do_advanced_menu, NULL, Icon_EQ);

enum eq_slider_mode {
    TYPE,
    GAIN,
    CUTOFF,
    Q,
};

/* Draw the UI for a whole EQ band */
static int draw_eq_slider(struct screen * screen, int x, int y,
    int width, int cutoff, int q, int gain, bool selected,
    enum eq_slider_mode mode, int band, int scrollbar_size,
    enum eq_filter_type type)
{
    char buf[26];
    int steps, min_item, max_item;
    int abs_gain = abs(gain);
    int x1, x2, y1, total_height;
    int w, h;

    switch(mode) {
    case TYPE:
        steps = 5;
        min_item = (type * 2);
        max_item = (type * 2) + 1;
        break;
    case Q:
        steps = EQ_Q_MAX - EQ_Q_MIN;
        min_item = q - EQ_Q_STEP - EQ_Q_MIN;
        max_item = q + EQ_Q_STEP - EQ_Q_MIN;
        break;
    case CUTOFF:
        steps = EQ_CUTOFF_MAX - EQ_CUTOFF_MIN;
        min_item = cutoff - EQ_CUTOFF_FAST_STEP * 2;
        max_item = cutoff + EQ_CUTOFF_FAST_STEP * 2;
        break;
    case GAIN:
    default:
        steps = EQ_GAIN_MAX - EQ_GAIN_MIN;
        min_item = abs(EQ_GAIN_MIN) + gain - EQ_GAIN_STEP * 5;
        max_item = abs(EQ_GAIN_MIN) + gain + EQ_GAIN_STEP * 5;
        break;
    }

    /* Start two pixels in, one for border, one for margin */
    x1 = x + 2;
    y1 = y + 2;

    /* Print out the band label */
    if (mode == TYPE && selected)
        screen->set_drawmode(DRMODE_SOLID | DRMODE_INVERSEVID);
    else
        screen->set_drawmode(DRMODE_SOLID);
    if (type == EQ_FILTER_LOW_SHELF) {
        snprintf(buf, sizeof(buf),  "LS%d:", band);
        screen->putsxy(x1, y1, buf);
        /*screen->getstringsize("LS:", &w, &h); UNUSED*/
    } else if (type == EQ_FILTER_HIGH_SHELF) {
        snprintf(buf, sizeof(buf),  "HS%d:", band);
        screen->putsxy(x1, y1, buf);
        /*screen->getstringsize("HS:", &w, &h); UNUSED*/
    } else {
        snprintf(buf, sizeof(buf),  "PK%d:", band);
        screen->putsxy(x1, y1, buf);
        /*screen->getstringsize(buf, &w, &h); UNUSED*/
    }

    w = screen->getstringsize("A", NULL, &h);

    x1 += 5*w; /* 4 chars for label + 1 space = 5 */

    /* Print out gain part of status line (left justify after label) */
    if (mode == GAIN && selected)
        screen->set_drawmode(DRMODE_SOLID | DRMODE_INVERSEVID);
    else
        screen->set_drawmode(DRMODE_SOLID);

    snprintf(buf, sizeof(buf), "%s%2d.%d%s", gain < 0 ? "-" : " ",
        abs_gain / EQ_USER_DIVISOR, abs_gain % EQ_USER_DIVISOR,
        screen->lcdwidth >= 160 ? "dB" : "");
    screen->putsxy(x1, y1, buf);
    w = screen->getstringsize(buf, NULL, NULL);
    x1 += w;

    /* Print out Q part of status line (right justify) */
    if (mode == Q && selected)
        screen->set_drawmode(DRMODE_SOLID | DRMODE_INVERSEVID);
    else
        screen->set_drawmode(DRMODE_SOLID);

    snprintf(buf, sizeof(buf), "%d.%d%s", q / EQ_USER_DIVISOR,
             q % EQ_USER_DIVISOR, screen->lcdwidth >= 160 ? " Q" : "");
    w = screen->getstringsize(buf, NULL, NULL);
    x2 = x + width - w - 2;
    screen->putsxy(x2, y1, buf);

    /* Print out cutoff part of status line (center between gain & Q) */
    if (mode == CUTOFF && selected)
        screen->set_drawmode(DRMODE_SOLID | DRMODE_INVERSEVID);
    else
        screen->set_drawmode(DRMODE_SOLID);

    snprintf(buf, sizeof(buf),  "%5d%s", cutoff,
             screen->lcdwidth >= 160 ? "Hz" : "");
    w = screen->getstringsize(buf, NULL, NULL);
    x1 = x1 + (x2 - x1 - w)/2;
    screen->putsxy(x1, y1, buf);

    /* Draw selection box */
    total_height = 3 + h + 1 + scrollbar_size + 3;
    screen->set_drawmode(DRMODE_SOLID);
    if (selected) {
        screen->drawrect(x, y, width, total_height);
    }

    /* Draw horizontal slider. Reuse scrollbar for this */
    gui_scrollbar_draw(screen, x + 3, y1 + h + 1, width - 6, scrollbar_size,
                       steps, min_item, max_item, HORIZONTAL);

    return total_height;
}

/* Draw's all the EQ sliders. Returns the total height of the sliders drawn */
static void draw_eq_sliders(struct screen * screen, int x, int y,
                            int nb_eq_sliders, int start_item,
                            int current_band, enum eq_slider_mode mode, int scrollbar_size)
{
    int height = y;

    start_item = MIN(start_item, EQ_NUM_BANDS - nb_eq_sliders);

    for (int i = 0; i < EQ_NUM_BANDS; i++) {
        struct eq_band_setting *setting = &global_settings.eq_band_settings[i];
        int cutoff = setting->cutoff;
        int q      = setting->q;
        int gain   = setting->gain;
        enum eq_filter_type type = setting->type;

        if (i == start_item + nb_eq_sliders)
            break;

        if (i >= start_item) {
            height += draw_eq_slider(screen, x, height, screen->lcdwidth - x - 1,
                                     cutoff, q, gain, i == current_band, mode,
                                     i, scrollbar_size, type);
            /* add a margin */
            height++;
        }
    }

    if (nb_eq_sliders != EQ_NUM_BANDS)
        gui_scrollbar_draw(screen, 0, y, scrollbar_size - 1,
                           screen->lcdheight - y, EQ_NUM_BANDS,
                           start_item, start_item + nb_eq_sliders,
                           VERTICAL);
    return;
}

/* Provides a graphical means of editing the EQ settings */
#ifdef IPOD_6G
#include "plugin.h"                 /* plugin_get_buffer() */
#include "bmp.h"                    /* read_bmp_file() */
/* GlossySlate: the graphical equaliser as designed (GlossySlate/DESIGN.md
 * 5.13), in the style of the quick menu: the ten bands side by side as
 * vertical faders, the filter type of the selected band in a capsule at the
 * top, its gain, frequency and Q on three keys below. The parts are bitmaps
 * of the theme in .rockbox/wps/<status bar skin>/eq/ (tools/build_eq.py),
 * loaded into the plugin buffer while the screen is open, like the skin
 * parser uses it: nothing is taken from the playback buffer. The field is
 * the dithered gradient of the quick menu, the fonts are the theme's,
 * shared with the skin. Without the parts, or while a plugin stays loaded,
 * the screen is drawn as before. Values, steps and keys are unchanged. */
enum eqgs_part {
    EQGS_CAP_L, EQGS_CAP_M, EQGS_CAP_R, EQGS_CAPA_L, EQGS_CAPA_M, EQGS_CAPA_R,
    EQGS_LOW, EQGS_PEAK, EQGS_HIGH, EQGS_LOW_W, EQGS_PEAK_W, EQGS_HIGH_W,
    EQGS_KEY_BACK, EQGS_DIVIDER, EQGS_ZERO, EQGS_BAND_SEL, EQGS_TRACK,
    EQGS_FILL, EQGS_KNOB, EQGS_KEY, EQGS_KEY_ACTIVE, EQGS_PART_COUNT
};
static const char *const eqgs_part_names[EQGS_PART_COUNT] = {
    "capsule_left", "capsule_middle", "capsule_right", "capsule_active_left",
    "capsule_active_middle", "capsule_active_right", "icon_low_shelf",
    "icon_peak", "icon_high_shelf", "icon_low_shelf_white", "icon_peak_white",
    "icon_high_shelf_white", "key_back", "divider", "zero_line",
    "band_selected", "fader_track", "fader_fill", "knob", "key", "key_active",
};
static struct bitmap eqgs_bm[EQGS_PART_COUNT];

enum eqgs_font { EQGS_F13, EQGS_F11, EQGS_F14, EQGS_FONT_COUNT };
static const char *const eqgs_font_names[EQGS_FONT_COUNT] = {
    FONT_DIR "/16-GlossySlate-Bold13.fnt", FONT_DIR "/14-GlossySlate-Bold11.fnt",
    FONT_DIR "/24-GlossySlate-Bold14.fnt",
};
static int eqgs_fonts[EQGS_FONT_COUNT];
static bool eqgs_font_loaded[EQGS_FONT_COUNT];
static fb_data *eqgs_field;

#define EQGS_DARK    LCD_RGBPACK(0x2e, 0x36, 0x44)
#define EQGS_GREY    LCD_RGBPACK(0x5b, 0x63, 0x71)
#define EQGS_BLACK   LCD_RGBPACK(0x14, 0x17, 0x1c)
#define EQGS_WHITE   LCD_RGBPACK(0xff, 0xff, 0xff)
#define EQGS_WHITE88 LCD_RGBPACK(0xe4, 0xec, 0xf8)
#define EQGS_MINUS   "\xe2\x88\x92"  /* U+2212 */
#define EQGS_ZERO_Y  104             /* 0 dB */
#define EQGS_RANGE   44              /* px from 0 dB to +-24 dB */

/* the field of the quick menu, dithered as the skin's %dr does it */
static void eqgs_make_field(void)
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
            fb_data *row = eqgs_field + y * LCD_WIDTH;
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

static void eqgs_unload(void)
{
    for (int i = 0; i < EQGS_FONT_COUNT; i++)
    {
        if (eqgs_font_loaded[i])
            font_unload(eqgs_fonts[i]);
        eqgs_font_loaded[i] = false;
        eqgs_fonts[i] = FONT_UI;
    }
}

static bool eqgs_load(void)
{
    char path[MAX_PATH];
    size_t size;
    unsigned char *buf = plugin_get_buffer(&size);
    const char *skin = (const char *)global_settings.sbs_file;

    for (int i = 0; i < EQGS_FONT_COUNT; i++)
    {
        eqgs_fonts[i] = FONT_UI;
        eqgs_font_loaded[i] = false;
    }
    /* less than the whole buffer: a plugin stays loaded and owns it */
    if (!buf || size < PLUGIN_BUFFER_SIZE || !skin[0] || skin[0] == '-')
        return false;

    size_t field = LCD_WIDTH * LCD_HEIGHT * sizeof(fb_data);
    eqgs_field = (fb_data *)buf;
    buf += field;
    size -= field;
    for (int i = 0; i < EQGS_PART_COUNT; i++)
    {
        snprintf(path, sizeof(path), WPS_DIR "/%s/eq/%s.bmp", skin, eqgs_part_names[i]);
        eqgs_bm[i].data = buf;
        int n = read_bmp_file(path, &eqgs_bm[i], size,
                              FORMAT_NATIVE | FORMAT_TRANSPARENT, NULL);
        if (n <= 0)
            return false;
        n = ALIGN_UP(n, 4);
        if ((size_t)n > size)
            return false;
        buf += n;
        size -= n;
    }
    for (int i = 0; i < EQGS_FONT_COUNT; i++)
    {
        int id = font_load_ex(eqgs_font_names[i], 0, 160);   /* as the skin */
        eqgs_font_loaded[i] = id >= 0;
        eqgs_fonts[i] = id >= 0 ? id : FONT_UI;
    }
    eqgs_make_field();
    return true;
}

static void eqgs_bmp(int part, int x, int y)
{
    const struct bitmap *bm = &eqgs_bm[part];
    lcd_bmp_part(bm, 0, 0, x, y, bm->width, bm->height);
}

static int eqgs_width(int font, const char *s)
{
    int w = 0;
    font_getstringsize((const unsigned char *)s, &w, NULL, font);
    return w;
}

static void eqgs_text(int font, unsigned colour, int x, int y, const char *s)
{
    lcd_setfont(font);
    lcd_set_foreground(colour);
    lcd_putsxy(x, y, (const unsigned char *)s);
}

static void eqgs_capsule(bool active, int x, int y, int w)
{
    int l = active ? EQGS_CAPA_L : EQGS_CAP_L;
    const struct bitmap *m = &eqgs_bm[l + 1];
    int mx = x + eqgs_bm[l].width, end = x + w - eqgs_bm[l + 2].width;
    eqgs_bmp(l, x, y);
    while (mx < end)
    {
        int part = MIN(m->width, end - mx);
        lcd_bmp_part(m, 0, 0, mx, y, part, m->height);
        mx += part;
    }
    eqgs_bmp(l + 2, end, y);
}

/* "+3,5 dB", "-2,0 dB" (real minus), "0,0 dB" */
static void eqgs_format_gain(char *buf, size_t size, int gain)
{
    snprintf(buf, size, "%s%d%s%d dB",
             gain > 0 ? "+" : gain < 0 ? EQGS_MINUS : "",
             abs(gain) / EQ_USER_DIVISOR, str(LANG_DECIMAL_SEPARATOR),
             abs(gain) % EQ_USER_DIVISOR);
}

/* under the band: "125", "1k", "3,5k", "16k" */
static void eqgs_format_freq_short(char *buf, size_t size, int hz)
{
    if (hz < 1000)
        snprintf(buf, size, "%d", hz);
    else if ((hz % 1000) / 100)
        snprintf(buf, size, "%d%s%dk", hz / 1000, str(LANG_DECIMAL_SEPARATOR),
                 (hz % 1000) / 100);
    else
        snprintf(buf, size, "%dk", hz / 1000);
}

/* fader of a band: track, the fill from the 0 dB line to the gain (the top
 * of the fill picture above the line, its bottom below), the knob only on
 * the selected band */
static void eqgs_band(int i, bool selected)
{
    const struct eq_band_setting *s = &global_settings.eq_band_settings[i];
    const struct bitmap *fill = &eqgs_bm[EQGS_FILL];
    int mid = 29 + 29 * i;
    int gain = MAX(EQ_GAIN_MIN, MIN(EQ_GAIN_MAX, s->gain));
    int y = EQGS_ZERO_Y - (gain * EQGS_RANGE + (gain >= 0 ? EQ_GAIN_MAX / 2 : -EQ_GAIN_MAX / 2))
                          / EQ_GAIN_MAX;
    char buf[16];

    eqgs_bmp(EQGS_TRACK, mid - 5, 60);
    if (y < EQGS_ZERO_Y)
        lcd_bmp_part(fill, 0, 0, mid - 5, y, fill->width, EQGS_ZERO_Y - y);
    else if (y > EQGS_ZERO_Y)
        lcd_bmp_part(fill, 0, fill->height - (y - EQGS_ZERO_Y), mid - 5, EQGS_ZERO_Y,
                     fill->width, y - EQGS_ZERO_Y);
    if (selected)
        eqgs_bmp(EQGS_KNOB, mid - 10, y - 9);

    eqgs_format_freq_short(buf, sizeof(buf), s->cutoff);
    eqgs_text(eqgs_fonts[EQGS_F11], selected ? EQGS_BLACK : EQGS_GREY,
              mid - eqgs_width(eqgs_fonts[EQGS_F11], buf) / 2, 154, buf);
}

static void eqgs_key(int k, bool active, const char *label, const char *value)
{
    int x = 13 + 100 * k;                   /* picture with its shadow */
    eqgs_bmp(active ? EQGS_KEY_ACTIVE : EQGS_KEY, x, 180);
    int lw = eqgs_width(eqgs_fonts[EQGS_F11], label);
    int vw = eqgs_width(eqgs_fonts[EQGS_F14], value);
    eqgs_text(eqgs_fonts[EQGS_F11], active ? EQGS_WHITE88 : EQGS_GREY,
              x + 1 + (92 - lw) / 2, 185, label);
    eqgs_text(eqgs_fonts[EQGS_F14], active ? EQGS_WHITE : EQGS_BLACK,
              x + 1 + (92 - vw) / 2, 196, value);
}

static void eqgs_draw(int band, enum eq_slider_mode mode)
{
    static const int type_names[3] = {
        LANG_EQUALIZER_BAND_LOW_SHELF, LANG_EQUALIZER_BAND_PEAK,
        LANG_EQUALIZER_BAND_HIGH_SHELF,
    };
    const struct eq_band_setting *s = &global_settings.eq_band_settings[band];
    int type = MAX(EQ_FILTER_LOW_SHELF, MIN(EQ_FILTER_HIGH_SHELF, s->type));
    bool type_mode = mode == TYPE;
    char buf[24];

    lcd_set_viewport(NULL);
    lcd_bitmap(eqgs_field, 0, 0, LCD_WIDTH, LCD_HEIGHT);
    lcd_set_drawmode(DRMODE_FG);

    /* top: filter type of the selected band (blue while it is edited), close */
    const char *name = str(type_names[type]);
    eqgs_capsule(type_mode, 14, 14, 39 + eqgs_width(eqgs_fonts[EQGS_F13], name) + 11);
    eqgs_bmp((type_mode ? EQGS_LOW_W : EQGS_LOW) + type, 25, 20);
    eqgs_text(eqgs_fonts[EQGS_F13], type_mode ? EQGS_WHITE : EQGS_DARK, 53, 18, name);
    eqgs_bmp(EQGS_KEY_BACK, 282, 14);
    eqgs_bmp(EQGS_DIVIDER, 14, 46);

    /* the bands: the selected one on its column, the 0 dB line behind the faders */
    eqgs_bmp(EQGS_BAND_SEL, 29 + 29 * band - 14, 52);
    eqgs_bmp(EQGS_ZERO, 14, EQGS_ZERO_Y);
    for (int i = 0; i < EQ_NUM_BANDS; i++)
        if (i != band)
            eqgs_band(i, false);
    eqgs_band(band, true);

    /* gain, frequency and Q of the selected band; the edited one is blue */
    eqgs_format_gain(buf, sizeof(buf), s->gain);
    eqgs_key(0, mode == GAIN, str(LANG_GRAPHICAL_EQ_GAIN), buf);
    snprintf(buf, sizeof(buf), "%d Hz", s->cutoff);
    eqgs_key(1, mode == CUTOFF, str(LANG_GRAPHICAL_EQ_FREQUENCY), buf);
    snprintf(buf, sizeof(buf), "%d%s%d", s->q / EQ_USER_DIVISOR,
             str(LANG_DECIMAL_SEPARATOR), s->q % EQ_USER_DIVISOR);
    eqgs_key(2, mode == Q, str(LANG_EQUALIZER_BAND_Q), buf);

    lcd_set_drawmode(DRMODE_SOLID);
    lcd_setfont(FONT_UI);
    lcd_update();
}
#endif /* IPOD_6G */

int eq_menu_graphical(void)
{
    bool exit_request = false;
    bool result = true;
    bool has_changed = false;
    int button;
    int *setting;
    int current_band, x, y, step, fast_step, min, max;
    enum eq_slider_mode mode;
    int h, height, start_item, nb_eq_sliders[NB_SCREENS];
    int scrollbar_size[NB_SCREENS];

    FOR_NB_SCREENS(i)
        viewportmanager_theme_enable(i, false, NULL);
#ifdef IPOD_6G
    bool gs = eqgs_load();
    const bool draw = !gs;
#else
    const bool draw = true;
#endif

    FOR_NB_SCREENS(i) {
        screens[i].set_viewport(NULL);
        if (draw)
            screens[i].clear_display();

        /* Figure out how many sliders can be drawn on the screen */
        h = screens[i].getcharheight();
        scrollbar_size[i] = h * 3 / 4;
        if (scrollbar_size[i] < 6)
            scrollbar_size[i] = 6;

        /* Total height includes margins (1), text, slider, and line selector (1) */
        height = 3 + h + 1 + scrollbar_size[i] + 3;
        nb_eq_sliders[i] = screens[i].lcdheight / height;

        /* Make sure the "Edit Mode" text fits too */
        height = nb_eq_sliders[i]*height + h + 2;
        if (height > screens[i].lcdheight)
            nb_eq_sliders[i]--;

        if (nb_eq_sliders[i] > EQ_NUM_BANDS)
            nb_eq_sliders[i] = EQ_NUM_BANDS;
    }

    y = h + 1;

    /* Start off editing gain on the first band */
    mode = GAIN;
    current_band = 0;

    while (!exit_request) {
        FOR_NB_SCREENS(i)
        {
            if (draw)
                screens[i].clear_display();

            /* Set pointer to the band data currently editable */
            if (mode == TYPE) {
                /* type */
                setting = (int*) &global_settings.eq_band_settings[current_band].type;

                step = 1;
                fast_step = 1;
                min = EQ_FILTER_LOW_SHELF;
                max = EQ_FILTER_HIGH_SHELF;

                if (draw)
                    screens[i].putsxyf(0, 0, str(LANG_SYSFONT_EQUALIZER_EDIT_MODE),
                             str(LANG_EQUALIZER_FILTER_TYPE), "");
            } else if (mode == GAIN) {
                /* gain */
                setting = &global_settings.eq_band_settings[current_band].gain;

                step = EQ_GAIN_STEP;
                fast_step = EQ_GAIN_FAST_STEP;
                min = EQ_GAIN_MIN;
                max = EQ_GAIN_MAX;

                if (draw)
                    screens[i].putsxyf(0, 0, str(LANG_SYSFONT_EQUALIZER_EDIT_MODE),
                             str(LANG_GAIN), "(dB)");
            } else if (mode == CUTOFF) {
                /* cutoff */
                setting = &global_settings.eq_band_settings[current_band].cutoff;

                step = EQ_CUTOFF_STEP;
                fast_step = EQ_CUTOFF_FAST_STEP;
                min = EQ_CUTOFF_MIN;
                max = EQ_CUTOFF_MAX;

                if (draw)
                    screens[i].putsxyf(0, 0, str(LANG_SYSFONT_EQUALIZER_EDIT_MODE),
                             str(LANG_SYSFONT_EQUALIZER_BAND_CUTOFF), "(Hz)");
            } else {
                /* Q */
                setting = &global_settings.eq_band_settings[current_band].q;

                step = EQ_Q_STEP;
                fast_step = EQ_Q_FAST_STEP;
                min = EQ_Q_MIN;
                max = EQ_Q_MAX;

                if (draw)
                    screens[i].putsxyf(0, 0, str(LANG_SYSFONT_EQUALIZER_EDIT_MODE),
                             str(LANG_EQUALIZER_BAND_Q), "");
            }

            /* Draw scrollbar if needed */
            if (nb_eq_sliders[i] != EQ_NUM_BANDS)
            {
                if (current_band == 0) {
                    start_item = 0;
                } else if (current_band == EQ_NUM_BANDS - 1) {
                    start_item = EQ_NUM_BANDS - nb_eq_sliders[i];
                } else {
                    start_item = current_band - 1;
                }
                x = scrollbar_size[i];
            } else {
                x = 1;
                start_item = 0;
            }
            /* Draw equalizer band details */
            if (draw)
            {
                draw_eq_sliders(&screens[i], x, y, nb_eq_sliders[i], start_item,
                                current_band, mode, scrollbar_size[i]);

                screens[i].update();
            }
        }
#ifdef IPOD_6G
        if (gs)
            eqgs_draw(current_band, mode);
#endif

        button = get_action(CONTEXT_SETTINGS_EQ,TIMEOUT_BLOCK);

        switch (button) {
        case ACTION_SETTINGS_DEC:
        case ACTION_SETTINGS_DECREPEAT:
            *(setting) -= step;
            has_changed = true;
            if (*(setting) < min)
                *(setting) = min;
            break;

        case ACTION_SETTINGS_INC:
        case ACTION_SETTINGS_INCREPEAT:
            *(setting) += step;
            has_changed = true;
            if (*(setting) > max)
                *(setting) = max;
            break;

        case ACTION_SETTINGS_INCBIGSTEP:
            *(setting) += fast_step;
            has_changed = true;
            if (*(setting) > max)
                *(setting) = max;
            break;

        case ACTION_SETTINGS_DECBIGSTEP:
            *(setting) -= fast_step;
            has_changed = true;
            if (*(setting) < min)
                *(setting) = min;
            break;

        case ACTION_STD_PREV:
        case ACTION_STD_PREVREPEAT:
            current_band--;
            if (current_band < 0)
                current_band = EQ_NUM_BANDS - 1; /* wrap around */
            break;

        case ACTION_STD_NEXT:
        case ACTION_STD_NEXTREPEAT:
            current_band = (current_band + 1) % EQ_NUM_BANDS;
            break;

        case ACTION_STD_OK:
            mode++;
            if (mode > Q)
                mode = TYPE; /* wrap around */
            break;

        case ACTION_STD_CANCEL:
            exit_request = true;
            result = false;
            break;
        default:
            if(default_event_handler(button) == SYS_USB_CONNECTED) {
                exit_request = true;
                result = true;
            }
            break;
        }

        /* Update the filter if the user changed something */
        if (has_changed) {
            dsp_set_eq_coefs(current_band,
                &global_settings.eq_band_settings[current_band]);
            has_changed = false;
        }
    }

#ifdef IPOD_6G
    if (gs)
        eqgs_unload();
#endif
    /* Reset screen settings */
    FOR_NB_SCREENS(i)
    {
        screens[i].clear_display();
        screens[i].set_viewport(NULL);
        viewportmanager_theme_undo(i, false);
    }
    return (result) ? 1 : 0;
}

static int eq_save_preset(void)
{
    /* make sure that the eq is enabled for setting saving */
    bool enabled = global_settings.eq_enabled;
    global_settings.eq_enabled = true;

    bool result = settings_save_config(SETTINGS_SAVE_EQPRESET);

    global_settings.eq_enabled = enabled;

    return (result) ? 1 : 0;
}
/* Allows browsing of preset files */
static struct browse_folder_info eqs = { EQS_DIR, SHOW_CFG };

static void eq_reset_defaults(void)
{
    for (int i = 0; i < EQ_NUM_BANDS; i++) {
        global_settings.eq_band_settings[i].type = eq_defaults[i].type;
        global_settings.eq_band_settings[i].cutoff = eq_defaults[i].cutoff;
        global_settings.eq_band_settings[i].q = eq_defaults[i].q;
        global_settings.eq_band_settings[i].gain = eq_defaults[i].gain;
    }
    eq_apply();
}

MENUITEM_FUNCTION(eq_graphical, 0, ID2P(LANG_EQUALIZER_GRAPHICAL),
                  eq_menu_graphical, lowlatency_callback, Icon_EQ);
MENUITEM_FUNCTION(eq_save, 0, ID2P(LANG_EQUALIZER_SAVE),
                  eq_save_preset, NULL, Icon_NOICON);
MENUITEM_FUNCTION(eq_reset, 0, ID2P(LANG_RESET_EQUALIZER),
                  eq_reset_defaults, NULL, Icon_NOICON);
MENUITEM_FUNCTION_W_PARAM(eq_browse, 0, ID2P(LANG_EQUALIZER_BROWSE),
                          browse_folder, (void*)&eqs,
                          lowlatency_callback, Icon_NOICON);

MAKE_MENU(equalizer_menu, ID2P(LANG_EQUALIZER), NULL, Icon_EQ,
        &eq_enable, &eq_graphical, &eq_precut, &gain_menu,
        &advanced_menu, &eq_save, &eq_browse, &eq_reset);
