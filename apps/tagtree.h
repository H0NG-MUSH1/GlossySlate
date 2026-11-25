/***************************************************************************
 *             __________               __   ___.
 *   Open      \______   \ ____   ____ |  | _\_ |__   _______  ___
 *   Source     |       _//  _ \_/ ___\|  |/ /| __ \ /  _ \  \/  /
 *   Jukebox    |    |   (  <_> )  \___|    < | \_\ (  <_> > <  <
 *   Firmware   |____|_  /\____/ \___  >__|_ \|___  /\____/__/\_ \
 *                     \/            \/     \/    \/            \/
 *
 * Copyright (C) 2005 by Miika Pekkarinen
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
#ifdef HAVE_TAGCACHE
#ifndef _TAGTREE_H
#define _TAGTREE_H

#include "config.h"
#include "tagcache.h"
#include "tree.h"
#ifdef IPOD_6G
#include "albumart_list.h"
#endif

#define TAGNAVI_VERSION    "#! rockbox/tagbrowser/2.0"
#define TAGMENU_MAX_ITEMS  64
#ifdef IPOD_6G
/* Untranslated names of the tagnavi.config root menu items that the main
 * menu entries "Podcasts" and "Hörbücher" open directly */
#define TAGNAVI_PODCASTS   "Podcasts"
#define TAGNAVI_AUDIOBOOKS "Audiobooks"
#endif
#define TAGMENU_MAX_MENUS  32
#define TAGMENU_MAX_FMTS   32

int tagtree_export(void);
int tagtree_import(void);
void tagtree_init(void) INIT_ATTR;
bool tagtree_ready(void);
#ifdef IPOD_6G
bool tagtree_album_art_key(struct tree_context *c, int id,
                           struct albumart_list_key *key);
/* The fixed picture of entry id of an album list, or -1 for an album */
int tagtree_album_special_entry(struct tree_context *c, int id);
const char *tagtree_album_artist_name(struct tree_context *c, int id);
bool tagtree_in_root_entry(struct tree_context *c, const char *name);
bool tagtree_open_root_entry(struct tree_context *c, const char *name);
void tagtree_open_root(struct tree_context *c);
bool tagtree_has_item_marks(struct tree_context *c);
int tagtree_item_mark(struct tree_context *c, int id);
bool tagtree_can_mark_unheard(struct tree_context *c);
bool tagtree_mark_unheard(struct tree_context *c);
/* the selected entry opens a plugin ("%plugin" in tagnavi.config) */
bool tagtree_is_plugin_entry(struct tree_context *c);
/* fast scrolling (docs/ipod6g-fast-scroll.md): the list is a list of tag
 * values or tracks held in memory as a whole (only then it is sorted) */
bool tagtree_fast_scroll_ok(struct tree_context *c);
/* the first byte of the name of entry id, 0 for none or a menu text */
int tagtree_entry_initial(struct tree_context *c, int id);
#endif
int tagtree_enter(struct tree_context* c, bool is_visible);
void tagtree_exit(struct tree_context* c, bool is_visible);
int tagtree_load(struct tree_context* c);
char* tagtree_get_entry_name(struct tree_context *c, int id,
                                    char* buf, size_t bufsize);
bool tagtree_current_playlist_insert(int position, bool queue);
int tagtree_add_to_playlist(const char* playlist, bool new_playlist);
char *tagtree_get_title(struct tree_context* c);
int tagtree_get_attr(struct tree_context* c);
int tagtree_get_icon(struct tree_context* c);
int tagtree_get_filename(struct tree_context* c, char *buf, int buflen);
int tagtree_get_custom_action(struct tree_context* c);
bool tagtree_get_subentry_filename(char *buf, size_t bufsize);
bool tagtree_entries_iterate(struct tagcache_search *tcs,
                             bool (*action_cb)(const char *file_name),
                             char *buf, size_t buf_sz);

#endif
#endif
