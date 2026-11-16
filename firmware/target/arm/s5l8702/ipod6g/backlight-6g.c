/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2009 by Dave Chapman
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
#include <stdbool.h>

#include "config.h"
#include "kernel.h"
#include "backlight.h"
#include "backlight-target.h"
#include "pmu-target.h"
#include "lcd-target.h"

static struct semaphore frame_ready;
static volatile bool waiting_for_frame;
static int current_brightness = DEFAULT_BRIGHTNESS_SETTING;
static long fade_out_start;
static bool fade_out_pending;

#define BACKLIGHT_DIMSTEP 0x14

#ifdef HAVE_LCD_SLEEP
bool lcd_active(void);
void lcd_awake(void);
void lcd_update(void);
#endif

void backlight_hw_brightness(int brightness)
{
    current_brightness = brightness;
    pmu_write(0x28, brightness);
}

void backlight_hw_hold_screen(bool hold)
{
    lcd_hold_frame_for_backlight(hold);
}

void backlight_hw_on(void)
{
    bool woke_lcd = false;
    fade_out_pending = false;
#ifdef HAVE_LCD_SLEEP
    if (!lcd_active())
    {
        woke_lcd = true;
        semaphore_wait(&frame_ready, TIMEOUT_NOBLOCK);
        waiting_for_frame = true;
        lcd_awake();
    }
#endif
    if (woke_lcd)
    {
        /* Wait briefly for the first complete post-wake LCD frame. */
        semaphore_wait(&frame_ready, HZ / 10);
        waiting_for_frame = false;
    }
    /* lcd_sleep() can stop the LED without the PMU dimming ramp. Restore
     * normal transitions only after the panel has woken up. */
    pmu_write(0x2b, BACKLIGHT_DIMSTEP);
    pmu_write(0x29, 1);
}

void backlight_hw_frame_ready(void)
{
    if (waiting_for_frame)
        semaphore_release(&frame_ready);
}

bool backlight_hw_frame_pending(void)
{
    return waiting_for_frame;
}

void backlight_hw_off(void)
{
    pmu_write(0x29, 0);
    fade_out_start = current_tick;
    fade_out_pending = true;
}

void backlight_hw_wait_for_fade_out(void)
{
#ifndef BOOTLOADER
    if (fade_out_pending)
    {
        /* PMU dimstep time is 16 * register / 32768 seconds for each
         * brightness step. Let the normal off ramp finish before the LCD
         * enters sleep; otherwise the panel can flash white. */
        int fade_ticks = (current_brightness * 16 * BACKLIGHT_DIMSTEP * HZ +
                          32767) / 32768;
        long elapsed = current_tick - fade_out_start;
        if (elapsed < fade_ticks)
            sleep(fade_ticks - elapsed);
    }
#endif
    fade_out_pending = false;
}

bool backlight_hw_init(void)
{
    semaphore_init(&frame_ready, 1, 0);
    /* LEDCTL: overvoltage protection enabled, OCP limit is 500mA */
    pmu_write(0x2a, 0x05);

    pmu_write(0x2b, BACKLIGHT_DIMSTEP);  /* T_dimstep = 16 * value / 32768 */
    backlight_hw_brightness(DEFAULT_BRIGHTNESS_SETTING);

    backlight_hw_on();

    return true;
}

/* Kill the backlight, instantly. */
void backlight_hw_kill(void)
{
    fade_out_pending = false;
    pmu_write(0x2b, 0);  /* T_dimstep = 0 */
    backlight_hw_off();
    fade_out_pending = false;
}
