/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2005 Kevin Ferrare
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

#ifndef _GUI_SCROLLBAR_H_
#define _GUI_SCROLLBAR_H_
#include "screen_access.h"

enum orientation {
    VERTICAL          = 0x0000,   /* Vertical orientation     */
    HORIZONTAL        = 0x0001,   /* Horizontal orientation   */
    INVERTFILL        = 0x0002,   /* Invert the fill direction */
    INNER_NOFILL      = 0x0004,   /* Do not fill inner part */
    BORDER_NOFILL     = 0x0008,   /* Do not fill border part */
#ifdef HAVE_LCD_COLOR
    FOREGROUND        = 0x0020,   /* Do not clear background pixels */
    INNER_FILL        = 0x0040,   /* Fill inner part even if FOREGROUND */
    INNER_BGFILL      = 0x0080,   /* Fill inner part with background
                                     color even if FOREGROUND */
    INNER_FILL_MASK   = 0x00c0,
#endif
    DONT_CLEAR_EXCESS = 0x0100,   /* Don't clear the entire bar area */
};

/*
 * Draws a scrollbar on the given screen
 *  - screen : the screen to put the scrollbar on
 *  - x : x start position of the scrollbar
 *  - y : y start position of the scrollbar
 *  - width : you won't guess =(^o^)=
 *  - height : I won't tell you either !
 *  - items : total number of items on the screen
 *  - min_shown : index of the starting item on the screen
 *  - max_shown : index of the last item on the screen
 *  - orientation : either VERTICAL or HORIZONTAL
 */
extern void gui_scrollbar_draw(struct screen * screen, int x, int y,
                               int width, int height, int items,
                               int min_shown, int max_shown,
                               unsigned flags);
extern void gui_bitmap_scrollbar_draw(struct screen * screen, struct bitmap *bm,
                            int x, int y,
                            int width, int height, int items,
                            int min_shown, int max_shown,
                            unsigned flags);
extern void show_busy_slider(struct screen *s, int x, int y,
                            int width, int height);
#if defined(IPOD_6G) && defined(HAVE_LCD_COLOR) && !defined(DISABLE_ALPHA_BITMAP)
/* Gap between the knob of gui_scrollbar_draw_overlay() and the list edge.
 * Lists keep their text out of a strip as wide as knob and gap. */
#define GUI_SCROLLBAR_OVERLAY_GAP 2
/* Steps from the fully shown knob (0) to the hidden one */
#define GUI_SCROLLBAR_FADE_STEPS 7
/*
 * Draws a vertical scrollbar like that of the original iPod firmware on the
 * main screen: only a semi-transparent dark knob over what is already drawn
 * in the given area, at_right_edge says on which side of the area it sits.
 * The knob fills the width of the area less GUI_SCROLLBAR_OVERLAY_GAP.
 * fade makes the knob more transparent, from 0 (normal) to
 * GUI_SCROLLBAR_FADE_STEPS (not drawn). The other arguments are those of
 * gui_scrollbar_draw().
 */
extern void gui_scrollbar_draw_overlay(struct screen *screen, int x, int y,
                                       int width, int height, int items,
                                       int min_shown, int max_shown,
                                       bool at_right_edge, int fade);
#endif
#endif /* _GUI_SCROLLBAR_H_ */
