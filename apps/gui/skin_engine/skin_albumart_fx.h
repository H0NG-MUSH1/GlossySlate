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
#ifndef _SKIN_ALBUMART_FX_H_
#define _SKIN_ALBUMART_FX_H_

#if defined(IPOD_6G) && defined(HAVE_ALBUMART) && !defined(__PCTOOL__)
/* Bytes of the picture of fx for a cover of width x height */
size_t skin_aa_fx_size(const struct skin_aa_fx *fx, int width, int height);

/* Draws the cover of album art handle (bitmap bmp, w x h of it at x, y)
 * with the effects of fx, or clears the area of the picture. buf is the
 * buffer of fx. False if the picture does not fit its buffer; the caller
 * then draws the plain cover. */
bool skin_aa_fx_draw(struct screen *display, struct skin_aa_fx *fx,
                     unsigned char *buf, const struct bitmap *bmp,
                     int handle, int x, int y, int w, int h, bool clear);
#endif

#endif
