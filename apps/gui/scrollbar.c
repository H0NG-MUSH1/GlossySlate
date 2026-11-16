/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) Markus Braun (2002)
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

#include "scrollbar.h"
#include "config.h"
#include "limits.h"
#include "bmp.h"

/* calculates the start and size of the knob */
static void scrollbar_helper(int min_shown, int max_shown, int items,
                             int inner_len, int *size, int *start)
{
    int min, max, range;

    /* min should be min */
    if(min_shown < max_shown) {
        min = min_shown;
        max = max_shown;
    }
    else {
        min = max_shown;
        max = min_shown;
    }

    /* limit min and max */
    if(min < 0)
        min = 0;
    if(min > items)
        min = items;

    if(max < 0)
        max = 0;
    if(max > items)
        max = items;

    range = max - min;

    /* avoid overflows */
    while (items > (INT_MAX / inner_len)) {
        items >>= 1;
        range >>= 1;
    }

    /* calc start and end of the knob */
    if (items > 0 && items > range) {
        *size = inner_len * range / items;
        if (*size == 0) { /* width of knob is null */
            *size = 1;
            *start = (inner_len - 1) * min / items;
        } else {
            *start = (inner_len - *size) * min / (items - range);
        }
    } else {  /* if null draw full bar */
        *size = inner_len;
        *start = 0;
    }

    return;
}

void gui_scrollbar_draw(struct screen * screen, int x, int y,
                        int width, int height, int items,
                        int min_shown, int max_shown,
                        unsigned flags)
{
    int inner_x, inner_y, inner_wd, inner_ht, inner_len;
    int start, size;
#ifdef HAVE_LCD_COLOR
    int infill;
#endif

    if (flags & INVERTFILL)
    {
        min_shown = items - max_shown;
        max_shown = items;
    }

    if (flags & BORDER_NOFILL)
    {
        inner_x  = x;
        inner_y  = y;
        inner_wd = width;
        inner_ht = height;
    }
    else
    {
        inner_x  = x + 1;
        inner_y  = y + 1;
        inner_wd = width  - 2;
        inner_ht = height - 2;
    }
    /* Boundary check to make sure that height is reasonable, otherwise nothing
     *  to do 
     */
    if ((inner_wd | inner_ht) < 0)
        return;

    if (flags & HORIZONTAL)
        inner_len = inner_wd;
    else
        inner_len = inner_ht;

    scrollbar_helper(min_shown, max_shown, items, inner_len, &size, &start);

    /* draw box */
    if (!(flags & BORDER_NOFILL))
    {
#ifdef HAVE_LCD_COLOR
        /* must avoid corners if case of (flags & FOREGROUND) */
        screen->hline(inner_x, x + inner_wd, y);
        screen->hline(inner_x, x + inner_wd, y + height - 1);
        screen->vline(x, inner_y, y + inner_ht);
        screen->vline(x + width - 1, inner_y, y + inner_ht);
#else
        screen->drawrect(x, y, width, height);
#endif
    }
    screen->set_drawmode(DRMODE_SOLID | DRMODE_INVERSEVID);

#ifdef HAVE_LCD_COLOR
    infill = flags & (screen->depth > 1 ? INNER_FILL_MASK : INNER_FILL);

    if (!(flags & FOREGROUND))
    {
#endif
        /* clear corner pixels */
        screen->drawpixel(x, y);
        screen->drawpixel(x + width - 1, y);
        screen->drawpixel(x, y + height - 1);
        screen->drawpixel(x + width - 1, y + height - 1);

#ifdef HAVE_LCD_COLOR
        if (infill != INNER_BGFILL)
            infill = INNER_FILL;
    }

    if (infill == INNER_FILL)
#endif
    {
        /* clear pixels in progress bar */
        screen->fillrect(inner_x, inner_y, inner_wd, inner_ht);
    }

    screen->set_drawmode(DRMODE_SOLID);

    if (flags & INNER_NOFILL)
        return;

#ifdef HAVE_LCD_COLOR
    if (infill == INNER_BGFILL)
    {
        /* fill inner area with current background color */
        unsigned fg = screen->get_foreground();
        screen->set_foreground(screen->get_background());
        screen->fillrect(inner_x, inner_y, inner_wd, inner_ht);
        screen->set_foreground(fg);
    }
#endif

    if (flags & HORIZONTAL)
    {
        inner_x += start;
        inner_wd = size;
    }
    else
    {
        inner_y += start;
        inner_ht = size;
    }

    screen->fillrect(inner_x, inner_y, inner_wd, inner_ht);
}

void gui_bitmap_scrollbar_draw(struct screen * screen, struct bitmap *bm, int x, int y,
                        int width, int height, int items,
                        int min_shown, int max_shown,
                        unsigned flags)
{
    int start;
    int size;
    int inner_len;
    int startx = 0, starty = 0;

    screen->set_drawmode(DRMODE_SOLID|DRMODE_INVERSEVID);

    /* clear pixels in progress bar */
    if ((flags&DONT_CLEAR_EXCESS) == 0)
        screen->fillrect(x, y, width, height);

    screen->set_drawmode(DRMODE_SOLID);

    if (flags & INNER_NOFILL)
        return;

    if (flags & INVERTFILL)
    {
        min_shown = items - max_shown;
        max_shown = items;
    }

    if (flags & HORIZONTAL)
        inner_len = width;
    else
        inner_len = height;

    scrollbar_helper(min_shown, max_shown, items, inner_len, &size, &start);

    if (flags & HORIZONTAL) {
        x += start;
        width = size;
        if (flags & INVERTFILL)
            startx = start;
    } else {
        y += start;
        height = size;
        if (flags & INVERTFILL)
            starty = start;
    }

    if (bm->width < startx)
        width = 0;
    else if (bm->width < startx + width)
        width = bm->width - startx;
    if (bm->height < starty)
        height = 0;
    else if (bm->height < starty + height)
        height = bm->height - starty;

    screen->bmp_part(bm, startx, starty, x, y, width, height);
}

void show_busy_slider(struct screen *s, int x, int y, int width, int height)
{
    static int start = 0, dir = 1;
    gui_scrollbar_draw(s, x, y, width, height, 100,
                           start, start+20, HORIZONTAL);
#if NB_SCREENS > 1
    if (s->screen_type == SCREEN_MAIN)
#endif
    {
        start += (dir*2);
        if (start > 79)
            dir = -1;
        else if (start < 1)
            dir = 1;
    }
}

#if defined(IPOD_6G) && defined(HAVE_LCD_COLOR) && !defined(DISABLE_ALPHA_BITMAP)
/* Not exported by lcd.h; used by the font renderer for anti-aliasing. */
extern void lcd_alpha_bitmap_part(const unsigned char *src, int src_x,
                                  int src_y, int stride, int x, int y,
                                  int width, int height);

/* The knob of the original iPod firmware: a dark bar with softened ends,
 * semi-transparent over the list rows, without a visible track. */
#define OVERLAY_END_GAP      3  /* pixels above and below the knob's range */
/* Transparency of the black knob, 0 (opaque) .. 15 (invisible). Over white
 * the knob is grey, over a blue selection bar dark blue. */
#define OVERLAY_KNOB_ALPHA   8
#define OVERLAY_CORNER_ALPHA 13
#define OVERLAY_MASK_STRIDE  32 /* pixels per mask row, even, >= knob */

/* alpha faded towards 15 (invisible) by fade steps */
static int overlay_alpha(int alpha, int fade)
{
    return alpha + (15 - alpha) * fade / GUI_SCROLLBAR_FADE_STEPS;
}

void gui_scrollbar_draw_overlay(struct screen *screen, int x, int y,
                                int width, int height, int items,
                                int min_shown, int max_shown,
                                bool at_right_edge, int fade)
{
    /* one row for the ends of the knob, one for its middle */
    static unsigned char mask[2][OVERLAY_MASK_STRIDE / 2]
        __attribute__((aligned(4)));
    int gap = MIN(GUI_SCROLLBAR_OVERLAY_GAP, width - 1);
    int knob_w = MIN(width - gap, OVERLAY_MASK_STRIDE);
    int len = height - 2 * OVERLAY_END_GAP;
    int knob_alpha = overlay_alpha(OVERLAY_KNOB_ALPHA, fade);
    int corner_alpha = overlay_alpha(OVERLAY_CORNER_ALPHA, fade);
    int knob_x, start, size;

    if (screen->screen_type != SCREEN_MAIN || knob_w <= 0 || len <= 0 ||
        fade >= GUI_SCROLLBAR_FADE_STEPS)
        return;

    scrollbar_helper(min_shown, max_shown, items, len, &size, &start);
    /* keep a short knob visible with both ends */
    if (size < 2 * knob_w)
    {
        int grow = MIN(2 * knob_w, len) - size;
        size += grow;
        start = MAX(0, MIN(start - grow / 2, len - size));
    }
    knob_x = at_right_edge ? x + width - gap - knob_w : x + gap;

    for (int i = 0; i < OVERLAY_MASK_STRIDE / 2; i++)
        mask[0][i] = mask[1][i] = 0;
    for (int col = 0; col < knob_w; col++)
    {
        int shift = (col & 1) * 4; /* the first pixel is the lower nibble */
        bool side = knob_w > 2 && (col == 0 || col == knob_w - 1);
        mask[0][col / 2] |= (side ? corner_alpha : knob_alpha) << shift;
        mask[1][col / 2] |= knob_alpha << shift;
    }

    unsigned fg = screen->get_foreground();
    screen->set_foreground(LCD_BLACK);
    screen->set_drawmode(DRMODE_FG);
    y += OVERLAY_END_GAP + start;
    for (int row = 0; row < size; row++)
    {
        bool end = (row == 0 || row == size - 1);
        lcd_alpha_bitmap_part(mask[end ? 0 : 1], 0, 0, OVERLAY_MASK_STRIDE,
                              knob_x, y + row, knob_w, 1);
    }
    screen->set_drawmode(DRMODE_SOLID);
    screen->set_foreground(fg);
}
#endif
