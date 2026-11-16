/***************************************************************************
*             __________               __   ___.
*   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
*   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
*   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
*   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
*                     \/            \/     \/    \/            \/
*
* Copyright (C) 2007 Jonathan Gordon
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
#ifndef __ROOT_MENU_H__
#define __ROOT_MENU_H__

#include "config.h"
#include "gcc_extensions.h"

void root_menu(void) NORETURN_ATTR;
struct menu_table {
    char *string;
    const struct menu_item_ex *item;
};

struct menu_table *root_menu_get_options(int *nb_options);

enum {
    /* from old menu api, but still required*/
    MENU_ATTACHED_USB = -10,
    MENU_SELECTED_EXIT = -9,

    GO_TO_ROOTITEM_CONTEXT = -5,
    GO_TO_PREVIOUS_MUSIC = -4,
    GO_TO_PREVIOUS_BROWSER = -3,
    GO_TO_PREVIOUS = -2,
    GO_TO_ROOT = -1,
    GO_TO_FILEBROWSER = 0,
#ifdef HAVE_TAGCACHE
    GO_TO_DBBROWSER,
#endif
    GO_TO_WPS,
    GO_TO_MAINMENU,
#ifdef HAVE_RECORDING
    GO_TO_RECSCREEN,
#endif
#if CONFIG_TUNER
    GO_TO_FM,
#endif
    GO_TO_RECENTBMARKS,
    GO_TO_PLUGIN,
    /* Do Not add any items above here unless you want it to be able to 
       be the "start screen" after a boot up. The setting in settings_list.c
       will need editing if this is the case. */
    GO_TO_BROWSEPLUGINS,
    GO_TO_TIMESCREEN,
    GO_TO_PLAYLISTS_SCREEN,
    GO_TO_PLAYLIST_VIEWER,
    GO_TO_SYSTEM_SCREEN,
    GO_TO_SHORTCUTMENU,
    /* The database categories "Podcasts" and "Audiobooks" */
    GO_TO_PODCASTS,
    GO_TO_AUDIOBOOKS,
};
#ifndef PLUGIN
extern struct menu_item_ex root_menu_;

/* For the sidebar of the main menu (skin tag %Mc): how many albums of
 * music, podcasts and audiobooks the database has, how many playlists the
 * playlist directory, how many bookmarks "Recent Bookmarks", how many
 * recordings the recording directory and how many entries "Shortcuts" has.
 * -1 while not known. */
enum media_count {
    MEDIA_COUNT_ALBUMS = 0,
    MEDIA_COUNT_PODCASTS,
    MEDIA_COUNT_AUDIOBOOKS,
    MEDIA_COUNT_PLAYLISTS,
    MEDIA_COUNT_BOOKMARKS,
    MEDIA_COUNT_RECORDINGS,  /* audio files in the recording directory */
    MEDIA_COUNT_SHORTCUTS,   /* entries of "Shortcuts" */
};
int root_menu_media_count(int which);
#ifdef IPOD_6G
/* Playlists or bookmarks (enum media_count, -1 both) may have changed */
void root_menu_media_count_changed(int which);
#endif

void root_menu_load_from_cfg(void* setting, char *value);
char* root_menu_write_to_cfg(void* setting, char*buf, int buf_len);
void root_menu_set_default(void* setting, void* defaultval);
bool root_menu_is_changed(void* setting, void* defaultval);
#endif


#endif /* __ROOT_MENU_H__ */
