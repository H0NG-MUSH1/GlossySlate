/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2010 Jonathan Gordon
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
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include <stdbool.h>
#include <ctype.h>
#include "strlcat.h"

#include "config.h"
#include "core_alloc.h"
#include "kernel.h"
#include "appevents.h"
#ifdef HAVE_ALBUMART
#include "albumart.h"
#endif
#include "settings.h"
#include "skin_display.h"
#include "skin_engine.h"
#include "skin_parser.h"
#include "tag_table.h"
#include "skin_scan.h"
#if CONFIG_TUNER
#include "radio.h"
#endif
#include "viewport.h"
#ifdef IPOD_6G
#include "statusbar-skinned.h"
#endif
#include "cuesheet.h"
#include "language.h"
#include "playback.h"
#include "playlist.h"
#include "root_menu.h"
#include "misc.h"
#include "list.h"
#include "wps.h"
#include "strmemccpy.h"

#define MAX_LINE 1024

struct skin_draw_info {
    struct gui_wps *gwps;
    struct skin_viewport *skin_vp;
    int line_number;
    unsigned long refresh_type;
    struct line_desc line_desc;

    char* cur_align_start;
    struct align_pos align;
    bool no_line_break;
    bool line_scrolls;
    bool force_redraw;

    char *buf;
    size_t buf_size;

    int offset; /* used by the playlist viewer */

    /* Bars of the current line, drawn by draw_line_bars() after the line
     * is written: write_line() clears the whole line and would wipe out a
     * bar drawn before it, e.g. when a conditional switches to a branch
     * with a bar (the bar then flashed as an empty line). */
    struct progressbar *line_bars[4];
    int nb_line_bars;
};

extern void sb_set_info_vp(enum screen_type screen, OFFSETTYPE(char*) label);

/* Draws the bars that the current line collected, see line_bars */
static void draw_line_bars(struct skin_draw_info *info)
{
    for (int i = 0; i < info->nb_line_bars; i++)
        draw_progressbar(info->gwps, info->skin_vp, info->line_number,
                         info->line_bars[i]);
    info->nb_line_bars = 0;
}

typedef bool (*skin_render_func)(struct skin_element* alternator, struct skin_draw_info *info);
bool skin_render_alternator(struct skin_element* alternator, struct skin_draw_info *info);

static void skin_render_playlistviewer(struct playlistviewer* viewer,
                                       struct gui_wps *gwps,
                                       struct skin_viewport* skin_viewport,
                                       unsigned long refresh_type);

static char* skin_buffer;
/* A disappearing viewport can cover viewports that were rendered earlier.
 * Repaint them before the completed frame is sent to the LCD. */
static bool hidden_viewport_cleared;
static bool repainting_after_hide;
#ifdef IPOD_6G
/* Hiding a %VB viewport fills its area of the backdrop buffer with the
 * background colour, and a hidden foreground viewport is cleared with the
 * backdrop buffer. When the backdrop viewport is hidden first, the
 * foreground ones take that background colour onto the screen, and a newly
 * shown backdrop viewport never reaches those areas (they are not drawn
 * again). So the repaint after hiding draws the backdrop layer first, then
 * clears the areas of all viewports hidden in this frame from the finished
 * backdrop, then draws the foreground. */
#define MAX_HIDDEN_AREAS 24
static struct viewport hidden_areas[MAX_HIDDEN_AREAS];
static int nb_hidden_areas;
static bool hidden_areas_overflow;
/* which viewports skin_render() draws: 1 backdrop layer, 2 the others */
static int render_layers = 3;

/* Copies the backdrop buffer to the screen around the UI viewport ui
 * (everywhere if there is none or it is the hidden 1 x 1 one): the areas
 * where the UI does not draw itself. */
static void backdrop_around(struct screen *display, const struct viewport *ui)
{
    static struct viewport v;
    const int W = display->lcdwidth, H = display->lcdheight;
    int r[4][4], n = 0;

    if (!ui || ui->width <= 1 || ui->height <= 1)
    {
        r[n][0] = 0; r[n][1] = 0; r[n][2] = W; r[n++][3] = H;
    }
    else
    {
        const int x1 = ui->x + ui->width, y1 = ui->y + ui->height;
        r[n][0] = 0; r[n][1] = 0; r[n][2] = W; r[n++][3] = ui->y;
        r[n][0] = 0; r[n][1] = y1; r[n][2] = W; r[n++][3] = H - y1;
        r[n][0] = 0; r[n][1] = ui->y; r[n][2] = ui->x; r[n++][3] = ui->height;
        r[n][0] = x1; r[n][1] = ui->y; r[n][2] = W - x1; r[n++][3] = ui->height;
    }
    viewport_set_fullscreen(&v, display->screen_type);
    for (int i = 0; i < n; i++)
    {
        if (r[i][2] <= 0 || r[i][3] <= 0)
            continue;
        v.x = r[i][0]; v.y = r[i][1]; v.width = r[i][2]; v.height = r[i][3];
        display->set_viewport_ex(&v, VP_FLAG_VP_SET_CLEAN);
        display->clear_viewport();
    }
}

/* the UI viewport of the skin of gwps */
static struct viewport *skin_ui_viewport(struct gui_wps *gwps,
                                         struct wps_data *data)
{
    enum screen_type screen = gwps->display->screen_type;
    if (gwps == skin_get_gwps(CUSTOM_STATUSBAR, screen))
        return sb_skin_peek_info_vp(screen);
    struct skin_viewport *svp =
        skin_find_item(VP_DEFAULT_LABEL_STRING, SKIN_FIND_UIVP, data);
    return svp ? &svp->vp : NULL;
}
#endif

static inline struct skin_element*
get_child(OFFSETTYPE(struct skin_element**) children, int child)
{
    OFFSETTYPE(struct skin_element*) *kids = SKINOFFSETTOPTR(skin_buffer, children);
    return SKINOFFSETTOPTR(skin_buffer, kids[child]);
}


#ifdef IPOD_6G
/* skinlist_draw() draws the rows of a skinned list (%Lb) onto a cleared
 * area, one after the other with the same skin elements. A line is only
 * written when its conditionals changed since the element was rendered
 * last, i.e. since the row before. After a wrap from the last item to the
 * first, the first row was selected like the last one drawn before it, and
 * its lines without text (the ends of the selection bar, the check mark)
 * stayed empty. So every line is written while this is on. */
static bool write_all_lines;
void skin_render_write_all_lines(bool on)
{
    write_all_lines = on;
}
#endif

#if defined(IPOD_6G) && !defined(__PCTOOL__)
/* A %dr gradient from the 24 bit colours of the skin, dithered to RGB565
 * (4 x 4, anchored to the screen). The firmware gradient interpolates the
 * RGB565 end colours and truncates every row: on a flat gradient the
 * channels then step at different rows, white to #F4F6F8 shows a pink band
 * and ends bluish. Drawn a row at a time into the current viewport (the
 * backdrop layer for %VB). */
static void draw_gradient_dithered(struct screen *display, struct viewport *vp,
                                   const struct draw_rectangle *rect)
{
    static const unsigned char bayer[4][4] = {
        {   8, 136,  40, 168 }, { 200,  72, 232, 104 },
        {  56, 184,  24, 152 }, { 248, 120, 216,  88 },
    };
    static fb_data row[LCD_WIDTH];
    int x0 = rect->x, w = rect->width, h = rect->height;
    if (x0 < 0)
    {
        w += x0;
        x0 = 0;
    }
    w = MIN(w, MIN(vp->width - x0, LCD_WIDTH));
    if (w <= 0 || h <= 0)
        return;

    int sr = (rect->start_rgb >> 16) & 0xff, er = (rect->end_rgb >> 16) & 0xff;
    int sg = (rect->start_rgb >> 8) & 0xff, eg = (rect->end_rgb >> 8) & 0xff;
    int sb = rect->start_rgb & 0xff, eb = rect->end_rgb & 0xff;
    for (int i = 0; i < h; i++)
    {
        int y = rect->y + i;
        if (y < 0 || y >= vp->height)
            continue;
        /* colour in the middle of the row, in 1/256 of an RGB565 step */
        int num = 2 * i + 1, den = 2 * h;
        int r = ((sr * den + (er - sr) * num) * 31 * 256) / (255 * den);
        int g = ((sg * den + (eg - sg) * num) * 63 * 256) / (255 * den);
        int b = ((sb * den + (eb - sb) * num) * 31 * 256) / (255 * den);
        int ay = vp->y + y;
        for (int k = 0; k < w; k++)
        {
            int t = bayer[ay & 3][(vp->x + x0 + k) & 3];
            row[k] = (fb_data)((MIN((r + t) >> 8, 31) << 11) |
                               (MIN((g + t) >> 8, 63) << 5) |
                                MIN((b + t) >> 8, 31));
        }
        display->bitmap_part(row, 0, 0, w, x0, y, w, 1);
    }
}
#endif

static bool do_non_text_tags(struct gui_wps *gwps, struct skin_draw_info *info,
                             struct skin_element *element)
{
    struct wps_token *token = (struct wps_token *)SKINOFFSETTOPTR(skin_buffer, element->data);
    if (!token) return false;
    struct skin_viewport *skin_vp = info->skin_vp;
    struct wps_data *data = gwps->data;
    bool do_refresh = (element->tag->flags & info->refresh_type) > 0;

    switch (token->type)
    {
#if (LCD_DEPTH > 1) || (defined(HAVE_REMOTE_LCD) && (LCD_REMOTE_DEPTH > 1))
        case SKIN_TOKEN_VIEWPORT_BGCOLOUR:
        case SKIN_TOKEN_VIEWPORT_FGCOLOUR:
        {
            struct viewport_colour *col = SKINOFFSETTOPTR(skin_buffer, token->value.data);
            if (!col) return false;
            if (token->type == SKIN_TOKEN_VIEWPORT_FGCOLOUR)
                skin_vp->vp.fg_pattern = col->colour;
            else
                skin_vp->vp.bg_pattern = col->colour;
            skin_vp->fgbg_changed = true;
        }
        break;
        case SKIN_TOKEN_VIEWPORT_TEXTSTYLE:
        {
            struct line_desc *data = SKINOFFSETTOPTR(skin_buffer, token->value.data);
            struct line_desc *linedes = &info->line_desc;
            if (!data || !linedes) return false;
            /* gradient colors are handled with a separate tag
             * (SKIN_TOKEN_VIEWPORT_GRADIENT_SETUP, see below). since it may
             * come before the text style tag color fields need to be preserved */
            if (data->style & STYLE_GRADIENT)
            {
                unsigned tc  = linedes->text_color,
                         lc  = linedes->line_color,
                         lec = linedes->line_end_color;
                *linedes = *data;
                linedes->text_color     = tc;
                linedes->line_color     = lc;
                linedes->line_end_color = lec;
            }
            else
                *linedes = *data;
        }
        break;
#endif
#ifdef HAVE_LCD_COLOR
        case SKIN_TOKEN_VIEWPORT_GRADIENT_SETUP:
        {
            struct gradient_config *cfg = SKINOFFSETTOPTR(skin_buffer, token->value.data);
            struct line_desc *linedes = &info->line_desc;
            if (!cfg || !linedes) return false;
            linedes->text_color     = cfg->text;
            linedes->line_color     = cfg->start;
            linedes->line_end_color = cfg->end;
        }
        break;
#endif
        case SKIN_TOKEN_VIEWPORT_ENABLE:
        {
            char *label = SKINOFFSETTOPTR(skin_buffer, token->value.data);
            char temp = VP_DRAW_HIDEABLE;
            struct skin_element *viewport = SKINOFFSETTOPTR(skin_buffer, gwps->data->tree);
            while (viewport)
            {
                struct skin_viewport *skinvp = SKINOFFSETTOPTR(skin_buffer, viewport->data);

                if (skinvp) {
                    char *vplabel = SKINOFFSETTOPTR(skin_buffer, skinvp->label);
                    if (skinvp->label == VP_DEFAULT_LABEL)
                        vplabel = VP_DEFAULT_LABEL_STRING;
                    if (vplabel && !skinvp->is_infovp &&
#if defined(IPOD_6G) && !defined(__PCTOOL__)
                        /* labels interned at load (skin_parser.c) */
                        (skinvp->label == VP_DEFAULT_LABEL ?
                         !strcmp(vplabel, label) :
                         skinvp->label == token->value.data))
#else
                        !strcmp(vplabel, label))
#endif
                    {
                        if (skinvp->hidden_flags&VP_DRAW_HIDDEN)
                        {
                            temp |= VP_DRAW_WASHIDDEN;
                        }
                        skinvp->hidden_flags = temp;
                    }
                }
                viewport = SKINOFFSETTOPTR(skin_buffer, viewport->next);
            }
        }
        break;
        case SKIN_TOKEN_LIST_ITEM_CFG:
            skinlist_set_cfg(gwps->display->screen_type,
                                SKINOFFSETTOPTR(skin_buffer, token->value.data));
            break;
        case SKIN_TOKEN_UIVIEWPORT_ENABLE:
            sb_set_info_vp(gwps->display->screen_type, token->value.data);
            break;
        case SKIN_TOKEN_PEAKMETER:
            data->peak_meter_enabled = true;
            if (do_refresh)
                draw_peakmeters(gwps, info->line_number, &skin_vp->vp);
            break;
        case SKIN_TOKEN_DRAWRECTANGLE:
            if (do_refresh)
            {
                struct draw_rectangle *rect =
                        SKINOFFSETTOPTR(skin_buffer, token->value.data);
                if (!rect) break;
#if defined(IPOD_6G) && !defined(__PCTOOL__)
                if (rect->start_rgb != rect->end_rgb &&
                    gwps->display->screen_type == SCREEN_MAIN)
                {
                    draw_gradient_dithered(gwps->display, &skin_vp->vp, rect);
                }
                else
#endif
#ifdef HAVE_LCD_COLOR
                if (rect->start_colour != rect->end_colour &&
                    gwps->display->screen_type == SCREEN_MAIN)
                {
                    gwps->display->gradient_fillrect(rect->x, rect->y, rect->width,
                        rect->height, rect->start_colour, rect->end_colour);
                }
                else
#endif
                {
#if LCD_DEPTH > 1
                    unsigned backup = skin_vp->vp.fg_pattern;
                    skin_vp->vp.fg_pattern = rect->start_colour;
#endif
                    gwps->display->fillrect(rect->x, rect->y, rect->width,
                        rect->height);
#if LCD_DEPTH > 1
                    skin_vp->vp.fg_pattern = backup;
#endif
                }
            }
            break;
        case SKIN_TOKEN_PEAKMETER_LEFTBAR:
        case SKIN_TOKEN_PEAKMETER_RIGHTBAR:
            data->peak_meter_enabled = true;
            /* fall through to the progressbar code */
        case SKIN_TOKEN_VOLUMEBAR:
        case SKIN_TOKEN_BATTERY_PERCENTBAR:
        case SKIN_TOKEN_PLAYLIST_PERCENTBAR:
        case SKIN_TOKEN_SETTINGBAR:
        case SKIN_TOKEN_PROGRESSBAR:
        case SKIN_TOKEN_PLAYLIST_PROGRESSBAR:
        case SKIN_TOKEN_TUNER_RSSI_BAR:
        case SKIN_TOKEN_LIST_SCROLLBAR:
        {
            struct progressbar *bar = (struct progressbar*)SKINOFFSETTOPTR(skin_buffer, token->value.data);
            if (do_refresh)
            {
                if (info->nb_line_bars < (int)ARRAYLEN(info->line_bars))
                    info->line_bars[info->nb_line_bars++] = bar;
                else
                    draw_progressbar(gwps, info->skin_vp, info->line_number, bar);
            }
        }
        break;
        case SKIN_TOKEN_IMAGE_DISPLAY:
        {
            struct gui_img *img = SKINOFFSETTOPTR(skin_buffer, token->value.data);
            if (img && img->loaded && do_refresh)
                img->display = 0;
        }
        break;
        case SKIN_TOKEN_IMAGE_DISPLAY_LISTICON:
        case SKIN_TOKEN_IMAGE_PRELOAD_DISPLAY:
        case SKIN_TOKEN_IMAGE_DISPLAY_9SEGMENT:
        {
            struct image_display *id = SKINOFFSETTOPTR(skin_buffer, token->value.data);
            if (!id) break;
            const char* label = SKINOFFSETTOPTR(skin_buffer, id->label);
            struct gui_img *img = skin_find_item(label,SKIN_FIND_IMAGE, data);
            if (img && img->loaded)
            {
                if (SKINOFFSETTOPTR(skin_buffer, id->token) == NULL)
                {
                    img->display = id->subimage;
                }
                else
                {
                    char buf[16];
                    const char *out;
                    int a = img->num_subimages;
                    out = get_token_value(gwps, SKINOFFSETTOPTR(skin_buffer, id->token),
                            info->offset, buf, sizeof(buf), &a);

                    /* NOTE: get_token_value() returns values starting at 1! */
                    if (a == -1)
                        a = (out && *out) ? 1 : 2;
                    if (token->type == SKIN_TOKEN_IMAGE_DISPLAY_LISTICON)
                        a -= 2; /* 2 is added in statusbar-skinned.c! */
                    else
                        a--;
                    a += id->offset;

                    /* Clear the image, as in conditionals */
                    clear_image_pos(gwps, img);

                    /* If the token returned a value which is higher than
                     * the amount of subimages, don't draw it. */
                    if (a >= 0 && a < img->num_subimages)
                    {
                        img->display = a;
                    }
                }
            }
            break;
        }
#ifdef HAVE_ALBUMART
        case SKIN_TOKEN_ALBUMART_DISPLAY:
        {
            /* now draw the AA */
            if (do_refresh)
            {
                struct skin_albumart *aa = SKINOFFSETTOPTR(skin_buffer, data->albumart);
                if (aa)
                {
                    int handle = playback_current_aa_hid(data->playback_aa_slot);
#if CONFIG_TUNER
                    if (in_radio_screen() || (get_radio_status() != FMRADIO_OFF))
                    {
                        struct dim dim = {aa->width, aa->height};
                        handle = radio_get_art_hid(&dim);
                    }
#endif
                    aa->draw_handle = handle;
#ifdef IPOD_6G
                    aa->draw_fx = token->value.data;
#endif
                }
            }
            break;
        }
#endif
        case SKIN_TOKEN_DRAW_INBUILTBAR:
            gui_statusbar_draw(&(statusbars.statusbars[gwps->display->screen_type]),
                               info->refresh_type == SKIN_REFRESH_ALL,
                               SKINOFFSETTOPTR(skin_buffer, token->value.data));
            break;
        case SKIN_TOKEN_VIEWPORT_CUSTOMLIST:
            if (do_refresh)
                skin_render_playlistviewer(SKINOFFSETTOPTR(skin_buffer, token->value.data), gwps,
                                           info->skin_vp, info->refresh_type);
            break;
#ifdef HAVE_SKIN_VARIABLES
        case SKIN_TOKEN_VAR_SET:
            {
                struct skin_var_changer *data = SKINOFFSETTOPTR(skin_buffer, token->value.data);
                struct skin_var *var = SKINOFFSETTOPTR(skin_buffer, data->var);
                if (data->direct)
                    var->value = data->newval;
                else
                {
                    var->value += data->newval;
                    if (data->max)
                    {
                        if (var->value > data->max)
                            var->value = 1;
                        else if (var->value < 1)
                            var->value = data->max;
                    }
                }
                if (var->value < 1)
                    var->value = 1;
                var->last_changed = current_tick;
            }
            break;
#endif
        default:
            return false;
    }
    return true;
}

static void do_tags_in_hidden_conditional(struct skin_element* branch,
                                          struct skin_draw_info *info)
{
    struct gui_wps *gwps = info->gwps;
    struct wps_data *data = gwps->data;

    /* Tags here are ones which need to be "turned off" or cleared
     * if they are in a conditional branch which isnt being used */
    if (branch->type == LINE_ALTERNATOR)
    {
        int i;
        for (i=0; i<branch->children_count; i++)
        {
            do_tags_in_hidden_conditional(get_child(branch->children, i), info);
        }
    }
    else if (branch->type == LINE && branch->children_count)
    {
        struct skin_element *child = get_child(branch->children, 0);
        struct wps_token *token;
        while (child)
        {
            if (child->type == CONDITIONAL)
            {
                int i;
                for (i=0; i<child->children_count; i++)
                {
                    do_tags_in_hidden_conditional(get_child(child->children, i), info);
                }
                goto skip;
            }
            else if (child->type != TAG || !SKINOFFSETTOPTR(skin_buffer, child->data))
            {
                goto skip;
            }

            token = (struct wps_token *)SKINOFFSETTOPTR(skin_buffer, child->data);

            /* clear all pictures in the conditional and nested ones */
            if (token->type == SKIN_TOKEN_IMAGE_PRELOAD_DISPLAY)
            {
                struct image_display *id = SKINOFFSETTOPTR(skin_buffer, token->value.data);
                if (!id) goto skip;

                struct gui_img *img = skin_find_item(SKINOFFSETTOPTR(skin_buffer, id->label),
                                                     SKIN_FIND_IMAGE, data);
                clear_image_pos(gwps, img);
            }
            else if (token->type == SKIN_TOKEN_PEAKMETER)
            {
                data->peak_meter_enabled = false;
            }
            else if (token->type == SKIN_TOKEN_VIEWPORT_ENABLE)
            {
                char *label = SKINOFFSETTOPTR(skin_buffer, token->value.data);
                struct skin_element *viewport;
                for (viewport = SKINOFFSETTOPTR(skin_buffer, data->tree);
                     viewport;
                     viewport = SKINOFFSETTOPTR(skin_buffer, viewport->next))
                {
                    struct skin_viewport *skin_viewport = SKINOFFSETTOPTR(skin_buffer, viewport->data);
                    if (!skin_viewport) continue;
                    char *vplabel = SKINOFFSETTOPTR(skin_buffer, skin_viewport->label);
                    if (skin_viewport->label == VP_DEFAULT_LABEL)
                        vplabel = VP_DEFAULT_LABEL_STRING;
#if defined(IPOD_6G) && !defined(__PCTOOL__)
                    /* labels interned at load (skin_parser.c) */
                    if (vplabel && (skin_viewport->label == VP_DEFAULT_LABEL ?
                                    strcmp(vplabel, label) != 0 :
                                    skin_viewport->label != token->value.data))
                        continue;
#else
                    if (vplabel && strcmp(vplabel, label))
                        continue;
#endif
                    if (skin_viewport->hidden_flags&VP_NEVER_VISIBLE)
                    {
                        continue;
                    }
                    if (skin_viewport->hidden_flags&VP_DRAW_HIDEABLE)
                    {
                        if (skin_viewport->hidden_flags&VP_DRAW_HIDDEN)
                            skin_viewport->hidden_flags |= VP_DRAW_WASHIDDEN;
                        else
                        {
#if (LCD_DEPTH > 1) || (defined(HAVE_REMOTE_LCD) && (LCD_REMOTE_DEPTH > 1))
                            if (skin_viewport->output_to_backdrop_buffer)
                            {
                                skin_backdrop_set_buffer(data->backdrop_id, skin_viewport);
                                skin_backdrop_show(-1);
                            }

                            gwps->display->set_viewport_ex(&skin_viewport->vp, VP_FLAG_VP_SET_CLEAN);
                            gwps->display->clear_viewport();
                            gwps->display->set_viewport_ex(&info->skin_vp->vp, VP_FLAG_VP_SET_CLEAN);

                            if (skin_viewport->output_to_backdrop_buffer)
                            {
                                skin_backdrop_set_buffer(-1, skin_viewport);
                                skin_backdrop_show(data->backdrop_id);
                            }
#else
                            gwps->display->set_viewport_ex(&skin_viewport->vp, VP_FLAG_VP_SET_CLEAN);
                            gwps->display->clear_viewport();
                            gwps->display->set_viewport_ex(&info->skin_vp->vp, VP_FLAG_VP_SET_CLEAN);
#endif
                            hidden_viewport_cleared = true;
#ifdef IPOD_6G
                            if (nb_hidden_areas < MAX_HIDDEN_AREAS)
                            {
                                /* its area on the screen, not in the
                                 * backdrop buffer */
                                hidden_areas[nb_hidden_areas] = skin_viewport->vp;
                                hidden_areas[nb_hidden_areas++].buffer = NULL;
                            }
                            else
                                hidden_areas_overflow = true;
#endif
                            skin_viewport->hidden_flags |= VP_DRAW_HIDDEN;
                        }
                    }
                }
            }
#ifdef HAVE_ALBUMART
            else if (token->type == SKIN_TOKEN_ALBUMART_DISPLAY && data->albumart)
            {
#ifdef IPOD_6G
                struct skin_albumart *aa =
                    SKINOFFSETTOPTR(skin_buffer, data->albumart);
                aa->draw_fx = token->value.data;
#endif
                draw_album_art(gwps,
                        playback_current_aa_hid(data->playback_aa_slot), true);
            }
#endif
        skip:
            child = SKINOFFSETTOPTR(skin_buffer, child->next);
        }
    }
}

static void fix_line_alignment(struct skin_draw_info *info, struct skin_element *element)
{
    struct align_pos *align = &info->align;
    char *cur_pos = info->cur_align_start + strlen(info->cur_align_start);
    char *next_pos = cur_pos + 1;
    switch (element->tag->type)
    {
        case SKIN_TOKEN_ALIGN_LEFT:
            align->left = next_pos;
            break;
        case SKIN_TOKEN_ALIGN_LEFT_RTL:
            if (UNLIKELY(lang_is_rtl()))
                align->right = next_pos;
            else
                align->left = next_pos;
            break;
        case SKIN_TOKEN_ALIGN_CENTER:
            align->center = next_pos;
            break;
        case SKIN_TOKEN_ALIGN_RIGHT:
            align->right = next_pos;
            break;
        case SKIN_TOKEN_ALIGN_RIGHT_RTL:
            if (UNLIKELY(lang_is_rtl()))
                align->left = next_pos;
            else
                align->right = next_pos;
            break;
        default:
            return;
    }
    info->cur_align_start = next_pos;
    *cur_pos = '\0';
    *next_pos = '\0';
}

/* Draw a LINE element onto the display */
static bool skin_render_line(struct skin_element* line, struct skin_draw_info *info)
{
    bool needs_update = false;

    int last_value, value;

    if (line->children_count == 0)
        return false; /* empty line, do nothing */

    struct skin_element *child = get_child(line->children, 0);
    struct conditional *conditional;
    skin_render_func func = skin_render_line;
    int old_refresh_mode = info->refresh_type;
    while (child)
    {
        switch (child->type)
        {
            case CONDITIONAL:
                conditional = SKINOFFSETTOPTR(skin_buffer, child->data);
                if (!conditional) break;
                last_value = conditional->last_value;
                value = evaluate_conditional(info->gwps, info->offset,
                                             conditional, child->children_count);
                conditional->last_value = value;
                if (child->children_count == 1)
                {
                    /* special handling so
                     * %?aa<true> and %?<true|false> need special handlng here */

                    if (value == -1) /* tag is false */
                    {
                        /* we are in a false branch of a %?aa<true> conditional */
                        if (last_value == 0)
                        {
                            do_tags_in_hidden_conditional(get_child(child->children, 0), info);
#ifdef IPOD_6G
                            /* its text has gone: write the line again, or
                             * the old text stays (e.g. "-44 dB" under the
                             * sidebar tile after going from Volume one menu
                             * level up to Sound Settings) */
                            needs_update = true;
                            info->force_redraw = true;
#endif
                        }
                        break;
                    }
                }
                else
                {
                    if (last_value >= 0 && value != last_value && last_value < child->children_count)
                        do_tags_in_hidden_conditional(get_child(child->children, last_value), info);
                }

                struct skin_element* se_child =  get_child(child->children, value);
                if (se_child->type == LINE_ALTERNATOR)
                {
                    func = skin_render_alternator;
                }
                else if (se_child->type == LINE)
                    func = skin_render_line;

                if (value != last_value)
                {
                    info->refresh_type = SKIN_REFRESH_ALL;
                    info->force_redraw = true;
                }

                if (func(se_child, info))
                    needs_update = true;
                else
                    needs_update = needs_update || (last_value != value);

                info->refresh_type = old_refresh_mode;
                break;
            case TAG:
                if (child->tag->flags & NOBREAK)
                    info->no_line_break = true;
                if (child->tag->type == SKIN_TOKEN_SUBLINE_SCROLL)
                    info->line_scrolls = true;

                fix_line_alignment(info, child);

                if (!SKINOFFSETTOPTR(skin_buffer, child->data))
                {
                    break;
                }

                if (!do_non_text_tags(info->gwps, info, child))
                {
                    size_t used = strlen(info->cur_align_start);
                    char *bufstart = info->cur_align_start + used;
                    size_t bufsz = info->buf_size - used;

                    const char *valuestr = get_token_value(info->gwps,
                                               SKINOFFSETTOPTR(skin_buffer, child->data),
                                               info->offset, bufstart, bufsz, NULL);
                    if (valuestr)
                    {
#if CONFIG_RTC
                        if (child->tag->flags&SKIN_RTC_REFRESH)
                            needs_update = needs_update || info->refresh_type&SKIN_REFRESH_DYNAMIC;
#endif
                        needs_update = needs_update ||
                                ((child->tag->flags&info->refresh_type)!=0);
                        if (valuestr != bufstart)
                        {
                            strmemccpy(bufstart, valuestr, bufsz);
                        }
                    }
                    else
                    {
                        bufstart[0] = '\0';
#ifdef IPOD_6G
                        /* an empty result is a change too: without this the
                         * line was not rewritten and its old text stayed
                         * (e.g. the value of the previous setting under the
                         * sidebar tile after moving to one without) */
                        needs_update = needs_update ||
                                ((child->tag->flags&info->refresh_type)!=0);
#endif
                    }
                }
                break;
            case TEXT:
                strlcat(info->cur_align_start, SKINOFFSETTOPTR(skin_buffer, child->data),
                        info->buf_size - (info->cur_align_start-info->buf));
                needs_update = needs_update ||
                                (info->refresh_type&SKIN_REFRESH_STATIC) != 0;
                break;
            case COMMENT:
            default:
                break;
        }

        child = SKINOFFSETTOPTR(skin_buffer, child->next);
    }
    return needs_update;
}

static int get_subline_timeout(struct gui_wps *gwps, struct skin_element* line)
{
    struct skin_element *element=line;
    struct wps_token *token = NULL;
    int retval = DEFAULT_SUBLINE_TIME_MULTIPLIER*TIMEOUT_UNIT;
    if (element->type == LINE)
    {
        if (element->children_count == 0)
            return retval; /* empty line, so force redraw */
        element = get_child(element->children, 0);
    }
    while (element)
    {
        int type = element->type;
        if (type == TAG && element->tag->type == SKIN_TOKEN_SUBLINE_TIMEOUT)
        {
            token = SKINOFFSETTOPTR(skin_buffer, element->data);
            if (token)
            {
                if (token->type == SKIN_TOKEN_SUBLINE_TIMEOUT_HIDE)
                {
                    struct wps_subline_timeout *st;
                    st = SKINOFFSETTOPTR(skin_buffer, token->value.data);
                    retval = st->show * TIMEOUT_UNIT;
                    if (st->hide != 0)
                    {
                        if(TIME_BEFORE(current_tick, st->next_tick))
                            retval = 0; /* don't display yet.. */
                        else
                            st->next_tick = current_tick + st->hide * TIMEOUT_UNIT;
                    }
                }
                else
                    retval = token->value.i;
            }
        }
        else if (type == CONDITIONAL)
        {
            struct conditional *conditional = SKINOFFSETTOPTR(skin_buffer, element->data);
            int val = evaluate_conditional(gwps, 0, conditional, element->children_count);

            if (val >= 0 || (token && token->type == SKIN_TOKEN_SUBLINE_TIMEOUT_HIDE))
            {/* only need tmoval in false case if SKIN_TOKEN_SUBLINE_TIMEOUT_HIDE */
                int tmoval = get_subline_timeout(gwps, get_child(element->children, val));
                if (tmoval >= 0)
                    return MAX(retval, tmoval); /* Bugfix %t()%?CONDITIONAL tmo ignored */
            }
        }
        else if (type == COMMENT)
        {
            retval = 0; /* don't display this item */
        }
        element = SKINOFFSETTOPTR(skin_buffer, element->next);
    }
    return retval;
}

bool skin_render_alternator(struct skin_element* element, struct skin_draw_info *info)
{
    bool changed_lines = false;
    struct line_alternator *alternator = SKINOFFSETTOPTR(skin_buffer, element->data);
    unsigned old_refresh = info->refresh_type;

    if (info->refresh_type == SKIN_REFRESH_ALL)
    {
        alternator->current_line = element->children_count-1;
        changed_lines = true;
    }
    else if (TIME_AFTER(current_tick, alternator->next_change_tick))
    {
        changed_lines = true;
    }

    if (changed_lines)
    {
        struct skin_element *current_line;
        int start = alternator->current_line;
        int try_line = start;
        bool suitable = false;
        int rettimeout = DEFAULT_SUBLINE_TIME_MULTIPLIER*TIMEOUT_UNIT;

        /* find a subline which has at least one token in it,
         * and that line doesnt have a timeout set to 0 through conditionals */
        do {
            try_line++;
            if (try_line >= element->children_count)
                try_line = 0;

            struct skin_element* child =  get_child(element->children, try_line);
            if (child->children_count != 0)
            {
                current_line = child;
                rettimeout = get_subline_timeout(info->gwps,
                                    get_child(current_line->children, 0));
                if (rettimeout > 0)
                {
                    suitable = true;
                }
            }
        }
        while (try_line != start && !suitable);

        if (info->refresh_type == SKIN_REFRESH_ALL
            || try_line != alternator->current_line)
        {
            info->force_redraw = true;
        }
        info->refresh_type = SKIN_REFRESH_ALL;

        if (suitable)
        {
            alternator->current_line = try_line;
            alternator->next_change_tick = current_tick + rettimeout;
        }
    }
    bool ret = skin_render_line(get_child(element->children, alternator->current_line), info);
    info->refresh_type = old_refresh;
    return changed_lines || ret;
}

void skin_render_viewport(struct skin_element* viewport, struct gui_wps *gwps,
                        struct skin_viewport* skin_viewport, unsigned long refresh_type)
{
    struct screen *display = gwps->display;
    char linebuf[MAX_LINE];
    skin_render_func func = skin_render_line;
    struct skin_element* line = viewport;
    struct skin_draw_info info = {
        .gwps = gwps,
        .buf = linebuf,
        .buf_size = sizeof(linebuf),
        .line_number = 0,
        .no_line_break = false,
        .line_scrolls = false,
        .refresh_type = refresh_type,
        .skin_vp = skin_viewport,
        .offset = 0,
        .line_desc = LINE_DESC_DEFINIT,
    };

    struct align_pos * align = &info.align;
    bool needs_update, update_all = false;
#ifdef IPOD_6G
    bool lines_written = false;
    update_all = write_all_lines;
#endif
    skin_buffer = get_skin_buffer(gwps->data);
    /* Set images to not to be displayed */
    struct skin_token_list *imglist = SKINOFFSETTOPTR(skin_buffer, gwps->data->images);
    while (imglist)
    {
        struct wps_token *token = SKINOFFSETTOPTR(skin_buffer, imglist->token);
        if (token) {
            struct gui_img *img = (struct gui_img *)SKINOFFSETTOPTR(skin_buffer, token->value.data);
        if (img)
                img->display = -1;
        }
        imglist = SKINOFFSETTOPTR(skin_buffer, imglist->next);
    }

    /* fix font ID's */
    if (skin_viewport->parsed_fontid == 1)
        skin_viewport->vp.font = display->getuifont();

    while (line)
    {
        linebuf[0] = '\0';
        info.no_line_break = false;
        info.line_scrolls = false;
        info.force_redraw = false;
#if (LCD_DEPTH > 1) || (defined(HAVE_REMOTE_LCD) && (LCD_REMOTE_DEPTH > 1))
        skin_viewport->fgbg_changed = false;
#ifdef HAVE_LCD_COLOR
        if (info.line_desc.style&STYLE_GRADIENT)
        {
            if (++info.line_desc.line > info.line_desc.nlines)
                info.line_desc.style = STYLE_DEFAULT;
        }
#endif
#endif
        info.cur_align_start = info.buf;
        align->left = info.buf;
        align->center = NULL;
        align->right = NULL;

        if (line->type == LINE_ALTERNATOR)
            func = skin_render_alternator;
        else if (line->type == LINE)
            func = skin_render_line;

        needs_update = func(line, &info);
#if (LCD_DEPTH > 1) || (defined(HAVE_REMOTE_LCD) && (LCD_REMOTE_DEPTH > 1))
        if (skin_viewport->fgbg_changed)
        {
            /* if fg/bg changed due to a conditional tag the colors
             * need to be set (2bit displays requires set_{fore,back}ground
             * for this. the rest of the viewport needs to be redrawn
             * to get the new colors */
            display->set_foreground(skin_viewport->vp.fg_pattern);
            display->set_background(skin_viewport->vp.bg_pattern);
            if (needs_update)
                update_all = true;
        }
#endif
        /* only update if the line needs to be, and there is something to write */
        if (refresh_type && (needs_update || update_all))
        {
            if (info.force_redraw)
            {
                int h = display->getcharheight();
                display->scroll_stop_viewport_rect(&skin_viewport->vp,
                    0, info.line_number*h, skin_viewport->vp.width, h);
            }
            write_line(display, align, info.line_number,
                    info.line_scrolls, &info.line_desc);
#ifdef IPOD_6G
            lines_written = true;
#endif
        }
        draw_line_bars(&info);
        if (!info.no_line_break)
            info.line_number++;
        line = SKINOFFSETTOPTR(skin_buffer, line->next);
    }
#ifdef IPOD_6G
    if (skin_viewport->output_to_backdrop_buffer)
    {
        /* backdrop layer: after a clear the images go over the fills and
         * images before them. In between the layer keeps them; drawing them
         * again would blend them a second time (darker edges), so only if a
         * line was rewritten (it cleared its area), as before. Images whose
         * frame a tag picks change with the next full update then. */
        if ((refresh_type & SKIN_REFRESH_ALL) == SKIN_REFRESH_ALL)
            wps_display_images_over(gwps, &skin_viewport->vp);
        else if (lines_written)
            wps_display_images(gwps, &skin_viewport->vp);
        return;
    }
#endif
    wps_display_images(gwps, &skin_viewport->vp);
}

void skin_render(struct gui_wps *gwps, unsigned refresh_mode)
{
    const int vp_is_appearing = (VP_DRAW_WASHIDDEN|VP_DRAW_HIDEABLE);
    struct wps_data *data = gwps->data;
    struct screen *display = gwps->display;

    struct skin_element* viewport;
    struct skin_viewport* skin_viewport;
    char *label;

    int old_refresh_mode = refresh_mode;
#ifdef IPOD_6G
    /* The screen shows the backdrop buffer only where a viewport clears
     * itself; elsewhere it keeps what was there: after another screen, a
     * clear without backdrop or (WPS) a copy of the backdrop made before
     * this update drew it. So a full update of a skin with a backdrop ends
     * with the finished backdrop on the screen around its UI viewport, and
     * the foreground drawn again over it. */
    const bool layered_full = !repainting_after_hide &&
        (refresh_mode&SKIN_REFRESH_ALL) == SKIN_REFRESH_ALL &&
        data->backdrop_id >= 0;
#endif
    if (!repainting_after_hide)
    {
        hidden_viewport_cleared = false;
#ifdef IPOD_6G
        nb_hidden_areas = 0;
        hidden_areas_overflow = false;
#endif
    }
    skin_buffer = get_skin_buffer(gwps->data);

    /* Framebuffer is likely dirty */
    if ((refresh_mode&SKIN_REFRESH_ALL) == SKIN_REFRESH_ALL)
    {
        /* should already be the default buffer */
        struct viewport * first_vp = display->set_viewport_ex(NULL, 0);
        if ((first_vp->flags & VP_FLAG_VP_SET_CLEAN) == VP_FLAG_VP_DIRTY &&
            get_current_activity() == ACTIVITY_WPS) /* only clear if in WPS */
        {
            display->clear_viewport();
        }
    }

    viewport = SKINOFFSETTOPTR(skin_buffer, data->tree);
    if (!viewport) return;
    skin_viewport = SKINOFFSETTOPTR(skin_buffer, viewport->data);
    if (!skin_viewport) return;
    label = SKINOFFSETTOPTR(skin_buffer, skin_viewport->label);
    if (skin_viewport->label == VP_DEFAULT_LABEL)
        label = VP_DEFAULT_LABEL_STRING;
    if (label && SKINOFFSETTOPTR(skin_buffer, viewport->next) &&
        !strcmp(label,VP_DEFAULT_LABEL_STRING))
        refresh_mode = 0;

    for (viewport = SKINOFFSETTOPTR(skin_buffer, data->tree);
         viewport;
         viewport = SKINOFFSETTOPTR(skin_buffer, viewport->next))
    {

        /* SETUP */
        skin_viewport = SKINOFFSETTOPTR(skin_buffer, viewport->data);
        if (!skin_viewport) continue;
#ifdef IPOD_6G
        if (!(render_layers &
              (skin_viewport->output_to_backdrop_buffer ? 1 : 2)))
            continue;
#endif
        unsigned vp_refresh_mode = refresh_mode;
#if (LCD_DEPTH > 1) || (defined(HAVE_REMOTE_LCD) && LCD_REMOTE_DEPTH > 1)
        if (skin_viewport->output_to_backdrop_buffer)
        {
            skin_backdrop_set_buffer(data->backdrop_id, skin_viewport);
            skin_backdrop_show(-1);
        }
        else
        {
            skin_backdrop_set_buffer(-1, skin_viewport);
            skin_backdrop_show(data->backdrop_id);
        }
#endif

        /* dont redraw the viewport if its disabled */
        if (skin_viewport->hidden_flags&VP_NEVER_VISIBLE)
        {   /* don't draw anything into this one */
            vp_refresh_mode = 0;
        }
        else if ((skin_viewport->hidden_flags&VP_DRAW_HIDDEN))
        {
            skin_viewport->hidden_flags |= VP_DRAW_WASHIDDEN;
            continue;
        }
        else if ((skin_viewport->hidden_flags & vp_is_appearing) == vp_is_appearing)
        {
            vp_refresh_mode = SKIN_REFRESH_ALL;
            skin_viewport->hidden_flags = VP_DRAW_HIDEABLE;
#ifdef IPOD_6G
            /* An appearing %VB viewport draws only into the backdrop
             * buffer: copy its area to the screen after this frame, like
             * the area of a hidden one. (At boot the first full update ran
             * before the list had a selection, no sidebar was shown; the
             * sidebar that appeared next stayed white except for the text
             * lines.) */
            if (skin_viewport->output_to_backdrop_buffer &&
                !repainting_after_hide)
            {
                hidden_viewport_cleared = true;
                if (nb_hidden_areas < MAX_HIDDEN_AREAS)
                {
                    hidden_areas[nb_hidden_areas] = skin_viewport->vp;
                    hidden_areas[nb_hidden_areas++].buffer = NULL;
                }
                else
                    hidden_areas_overflow = true;
            }
#endif
        }

        display->set_viewport_ex(&skin_viewport->vp, VP_FLAG_VP_SET_CLEAN);

        if ((vp_refresh_mode&SKIN_REFRESH_ALL) == SKIN_REFRESH_ALL)
        {
            display->clear_viewport();
        }
        /* render */
        if (viewport->children_count)
            skin_render_viewport(get_child(viewport->children, 0), gwps,
                                 skin_viewport, vp_refresh_mode);
        refresh_mode = old_refresh_mode;
    }
    if (hidden_viewport_cleared && !repainting_after_hide)
    {
        hidden_viewport_cleared = false;
        repainting_after_hide = true;
#ifdef IPOD_6G
        /* the backdrop layer, then the hidden areas from it, then the rest */
        render_layers = 1;
        skin_render(gwps, SKIN_REFRESH_ALL);
        skin_backdrop_set_buffer(-1, skin_viewport);
        skin_backdrop_show(data->backdrop_id);
        if (hidden_areas_overflow)
        {
            display->set_viewport_ex(NULL, VP_FLAG_VP_SET_CLEAN);
            display->clear_viewport();
        }
        else if (layered_full)
            backdrop_around(display, skin_ui_viewport(gwps, data));
        else
        {
            for (int i = 0; i < nb_hidden_areas; i++)
            {
                display->set_viewport_ex(&hidden_areas[i], VP_FLAG_VP_SET_CLEAN);
                display->clear_viewport();
            }
        }
        nb_hidden_areas = 0;
        hidden_areas_overflow = false;
        render_layers = 2;
        skin_render(gwps, SKIN_REFRESH_ALL);
        render_layers = 3;
#else
        skin_render(gwps, SKIN_REFRESH_ALL);
#endif
        repainting_after_hide = false;
        return;
    }
#if (LCD_DEPTH > 1) || (defined(HAVE_REMOTE_LCD) && (LCD_REMOTE_DEPTH > 1))
    skin_backdrop_set_buffer(-1, skin_viewport);
    skin_backdrop_show(data->backdrop_id);
#endif
#ifdef IPOD_6G
    if (layered_full)
    {
        backdrop_around(display, skin_ui_viewport(gwps, data));
        repainting_after_hide = true;
        render_layers = 2;
        skin_render(gwps, SKIN_REFRESH_ALL);
        render_layers = 3;
        repainting_after_hide = false;
        return;
    }
#endif

    if (((refresh_mode&SKIN_REFRESH_ALL) == SKIN_REFRESH_ALL))
    {
        /* If this is the UI viewport then let the UI know
         * to redraw itself */
        send_event(GUI_EVENT_NEED_UI_UPDATE, NULL);
    }
    /* Restore the default viewport */
    display->set_viewport_ex(NULL, VP_FLAG_VP_SET_CLEAN);
}

static __attribute__((noinline))
void skin_render_playlistviewer(struct playlistviewer* viewer,
                                struct gui_wps *gwps,
                                struct skin_viewport* skin_viewport,
                                unsigned long refresh_type)
{
    struct screen *display = gwps->display;
    char linebuf[MAX_LINE];
    skin_render_func func = skin_render_line;
    struct skin_element* line;
    struct skin_draw_info info = {
        .gwps = gwps,
        .buf = linebuf,
        .buf_size = sizeof(linebuf),
        .line_number = 0,
        .no_line_break = false,
        .line_scrolls = false,
        .refresh_type = refresh_type,
        .skin_vp = skin_viewport,
        .offset = viewer->start_offset,
        .line_desc = LINE_DESC_DEFINIT,
    };

    struct align_pos * align = &info.align;
    bool needs_update;
    int cur_pos, start_item, max;
    int nb_lines = viewport_get_nb_lines(&skin_viewport->vp);
#if CONFIG_TUNER
    if (get_current_activity() == ACTIVITY_FM)
    {
        cur_pos = radio_current_preset();
        start_item = cur_pos + viewer->start_offset;
        max = start_item+radio_preset_count();
    }
    else
#endif
    {
        struct wps_state *state = get_wps_state();
        struct cuesheet *cue = state->id3 ? state->id3->cuesheet : NULL;
        cur_pos = playlist_get_display_index();
        max = playlist_amount()+1;
        if (cue)
            max += cue->track_count;
        start_item = MAX(0, cur_pos + viewer->start_offset);
    }
    if (max-start_item > nb_lines)
        max = start_item + nb_lines;

    line = SKINOFFSETTOPTR(skin_buffer, viewer->line);
    while (start_item < max)
    {
        linebuf[0] = '\0';
        info.no_line_break = false;
        info.line_scrolls = false;
        info.force_redraw = false;

        info.cur_align_start = info.buf;
        align->left = info.buf;
        align->center = NULL;
        align->right = NULL;


        if (line->type == LINE_ALTERNATOR)
            func = skin_render_alternator;
        else if (line->type == LINE)
            func = skin_render_line;

        needs_update = func(line, &info);

        /* only update if the line needs to be, and there is something to write */
        if (refresh_type && needs_update)
        {
            struct viewport *vp = &skin_viewport->vp;
            if (!info.force_redraw)
            {
                int h = display->getcharheight();
                display->scroll_stop_viewport_rect(vp,
                    0, info.line_number*h, vp->width, h);
            }
            write_line(display, align, info.line_number,
                    info.line_scrolls, &info.line_desc);
        }
        draw_line_bars(&info);
        info.line_number++;
        info.offset++;
        start_item++;
    }
}
