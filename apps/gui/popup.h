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
#ifndef _GUI_POPUP_H_
#define _GUI_POPUP_H_

/* GlossySlate popups (IPOD_6G): splash(), splash_progress() and the yes/no
 * prompt drawn as a dark glossy panel in the middle of the whole screen,
 * see docs/ipod6g-popups.md */
#ifdef IPOD_6G
#include <stdbool.h>

/* 1 = GlossySlate popups, 0 = the Rockbox splashes (for tests). After
 * changing it touch splash.c, yesno.c and statusbar-skinned.c: the make
 * dependencies do not know popup.h. */
#define GS_POPUPS 1

/* loads the fonts of the theme settings "popup font" and "popup hint font" */
void popup_fonts_apply(void);

/* a message; lang_id (or -1) picks a symbol for known messages */
void popup_message(const char *text, int lang_id);
/* a message with a progress bar */
void popup_progress(const char *text, int current, int total);
/* the question of a yes/no prompt; seconds >= 0 counts down on the
 * default answer (yes_is_default) */
void popup_yesno(const char *const *lines, int nb_lines,
                 int seconds, bool yes_is_default);
/* puts back what the popup covered, if nothing has drawn over it since */
void popup_close(void);

/* for the status bar skin: whether a popup is on the screen untouched (the
 * skin must not draw over it), or was drawn over since the last call (the
 * skin must redraw completely, the rest of the popup lies on it) */
enum popup_state { POPUP_NONE, POPUP_SHOWN, POPUP_DISTURBED };
enum popup_state popup_screen_state(void);
#endif

#endif /* _GUI_POPUP_H_ */
