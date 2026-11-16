/***************************************************************************
 * Small, persistent album thumbnails for the iPod Classic database browser.
 * Copyright (C) 2026 Rockbox contributors
 *
 * This program is free software; you can redistribute it and/or modify it
 * under the terms of the GNU General Public License, version 2 or later.
 ***************************************************************************/

/* The thumbnails live in two files in ART_DIR:
 *
 *   covers.dat  every distinct cover once (an album list and the album lists
 *               of each album artist usually share it), ALBUMART_LIST_SIZE
 *               square, RGB565
 *   index.dat   album keys sorted for a binary search, each with the number
 *               of its cover in covers.dat
 *
 * The keys are tag seeks, which a database commit moves, so index.dat
 * records the database it was made for and is ignored for any other.
 * A refresh builds both files anew next to the old ones and then replaces
 * them; everything else in ART_DIR is deleted, so no old thumbnails remain.
 * Covers whose source (image file or track with embedded art) did not
 * change are copied from the old covers.dat instead of being decoded.
 * Browsing only reads; covers are decoded by the background refresh. It
 * runs after every database update or rebuild (tagcache.c), which also
 * catches new or changed image files, and when an album list is opened and
 * the files do not match the database or the album art setting. */

#include "config.h"
#ifdef IPOD_6G
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "string-extra.h"
#include "albumart_list.h"
#include "albumart.h"
#include "bmp.h"
#include "jpeg_load.h"
#include "metadata.h"
#include "settings.h"
#include "audio.h"
#include "tagcache.h"
#include "kernel.h"
#include "thread.h"
#include "lcd.h"
#include "button.h"
#include "file.h"
#include "dir.h"
#include "usb.h"
#include "system.h"
#include "misc.h"
#include "pcmbuf.h"

#define ART_DIR ROCKBOX_DIR "/album-list-art"
#define ART_COVERS_NAME "covers.dat"
#define ART_INDEX_NAME "index.dat"
#define ART_COVERS ART_DIR "/" ART_COVERS_NAME
#define ART_INDEX ART_DIR "/" ART_INDEX_NAME
#define ART_COVERS_NEW ART_DIR "/covers.new"
#define ART_INDEX_NEW ART_DIR "/index.new"
#define ART_ENTRIES ART_DIR "/entries.tmp"
#define ART_KEYS ART_DIR "/keys.tmp"
#define ART_SIDE ALBUMART_LIST_SIZE
#define ART_PIXELS (ART_SIDE * ART_SIDE)
/* Thumbnails kept in RAM: an album list shows four rows at a time */
#define ART_SLOTS 24
#define ART_PENDING 16
/* Covers whose source is remembered during a refresh, to share and reuse */
#define ART_SOURCES 1024
#define ART_COVERS_MAGIC 0x414c4331u /* ALC1 */
#define ART_INDEX_MAGIC 0x414c4931u  /* ALI1 */
#define ART_DECODE_BUFFER (256 * 1024)

#include "albumart_list_default.h"
#include "albumart_list_special.h"

enum { ART_REQUEST = 1, ART_REFRESH };

struct art_source {
    uint32_t hash;
    uint32_t mtime;
    uint32_t size;
};
struct covers_header {
    uint32_t magic;
    int32_t side;
    int32_t count;
    int32_t reserved;
};
struct cover_record {
    struct art_source source;
    fb_data pixels[ART_PIXELS];
};
struct index_header {
    uint32_t magic;
    int32_t preference;
    int32_t commitid;
    int32_t entries;
    int32_t datasize;
    int32_t count;
};
struct index_entry {
    struct albumart_list_key key;
    int32_t cover;
};
struct art_slot {
    struct albumart_list_key key;
    bool valid;
    bool missing;
    int preference;
    fb_data pixels[ART_PIXELS];
};

static struct art_slot slots[ART_SLOTS];
static struct albumart_list_key pending[ART_PENDING];
static int pending_count;
static int next_slot;
static bool art_ready;
static bool active_key_valid;
static bool redraw_queued;
static struct albumart_list_key active_key;
static struct mutex art_mutex;
static struct event_queue art_queue;
static long art_stack[(DEFAULT_STACK_SIZE + 0x4000) / sizeof(long)];
/* The JPEG and BMP decoders write fb_data halfwords into this buffer.
 * On ARM an unaligned byte array can silently swap pixel bytes. At the end
 * of a refresh it holds the index entries for sorting. */
static unsigned char decode_buffer[ART_DECODE_BUFFER]
    __attribute__((aligned(32)));
static fb_data rendered[ART_PIXELS];
static char source_path[MAX_PATH];

/* the published files, opened by the art thread when needed */
static int pub_index = -1, pub_covers = -1;
static struct index_header pub_header;

/* a refresh in progress */
static bool building;
static bool published_valid; /* the published files serve lookups meanwhile */
static int new_covers = -1, new_entries = -1, old_covers = -1;
static int new_count, old_count, entry_count;
static int decoded;      /* covers decoded instead of copied */
static int index_count;  /* entries of the new index.dat */
static struct index_header build_header;
static struct art_source new_sources[ART_SOURCES];
static struct art_source old_sources[ART_SOURCES];

/* the database for which a refresh was started by itself */
static bool auto_started;
static struct index_header auto_header;

static bool same_key(const struct albumart_list_key *a,
                     const struct albumart_list_key *b)
{
    return a->album_seek == b->album_seek &&
           a->parent_tag == b->parent_tag &&
           a->parent_seek == b->parent_seek;
}

static int compare_keys(const struct albumart_list_key *a,
                        const struct albumart_list_key *b)
{
    if (a->album_seek != b->album_seek)
        return a->album_seek < b->album_seek ? -1 : 1;
    if (a->parent_tag != b->parent_tag)
        return a->parent_tag < b->parent_tag ? -1 : 1;
    if (a->parent_seek != b->parent_seek)
        return a->parent_seek < b->parent_seek ? -1 : 1;
    return 0;
}

static int compare_entries(const void *a, const void *b)
{
    return compare_keys(&((const struct index_entry *)a)->key,
                        &((const struct index_entry *)b)->key);
}

static bool same_source(const struct art_source *a,
                        const struct art_source *b)
{
    return a->hash == b->hash && a->mtime == b->mtime && a->size == b->size;
}

static bool same_database(const struct index_header *a,
                          const struct index_header *b)
{
    return a->preference == b->preference && a->commitid == b->commitid &&
           a->entries == b->entries && a->datasize == b->datasize;
}

static uint32_t hash_string(const char *s)
{
    uint32_t hash = 2166136261u;
    while (*s)
        hash = (hash ^ (unsigned char)*s++) * 16777619u;
    return hash;
}

/* The database and album art setting the thumbnails must match; false while
 * the database cannot be used */
static bool current_database(struct index_header *h)
{
    if (!tagcache_is_usable() || tagcache_get_commit_step() != 0)
        return false;
    memset(h, 0, sizeof(*h));
    h->magic = ART_INDEX_MAGIC;
    h->preference = global_settings.album_art;
    tagcache_get_db_id(&h->commitid, &h->entries, &h->datasize);
    return true;
}

static bool usable(void)
{
    return !usb_inserted() && tagcache_is_usable() &&
           tagcache_get_commit_step() == 0;
}

/* Rockbox's directory API gives the modification time on native targets. */
static bool source_info(const char *path, uint32_t *mtime, uint32_t *size)
{
    char parent[MAX_PATH];
    char base[MAX_PATH];
    strmemccpy(parent, path, sizeof(parent));
    char *slash = strrchr(parent, '/');
    if (!slash)
        return false;
    strmemccpy(base, slash + 1, sizeof(base));
    if (slash == parent)
        slash[1] = '\0';
    else
        *slash = '\0';
    DIR *dir = opendir(parent);
    if (!dir)
        return false;
    bool found = false;
    struct dirent *entry;
    while ((entry = readdir(dir)))
    {
        if (!strcmp(entry->d_name, base))
        {
            struct dirinfo info = dir_get_info(dir, entry);
            *mtime = info.mtime;
            *size = info.size;
            found = true;
            break;
        }
    }
    closedir(dir);
    return found;
}

/* Path and modification time (from the database) of track idx_id. The
 * search is closed again at once: a live search holds tagcache's write
 * lock and would delay a commit for the whole refresh. */
static bool track_info(int idx_id, char *path, size_t path_size,
                       uint32_t *mtime)
{
    struct tagcache_search search;
    if (!tagcache_search(&search, tag_filename))
        return false;
    bool found = tagcache_retrieve(&search, idx_id, tag_filename,
                                   path, path_size);
    if (found)
    {
        search.idx_id = idx_id;
        *mtime = tagcache_get_numeric(&search, tag_mtime);
    }
    tagcache_search_finish(&search);
    return found;
}

/* The artwork of track idx_id, the first track of an album list key */
static bool choose_source(int idx_id, struct art_source *source,
                          struct mp3_albumart *embedded)
{
    char track[MAX_PATH];
    uint32_t track_mtime;
    struct mp3entry id3;
    if (!track_info(idx_id, track, sizeof(track), &track_mtime) ||
        !get_metadata(&id3, -1, track))
        return false;

    bool has_embedded = id3.has_embedded_albumart &&
        (id3.albumart.type & AA_CLEAR_FLAGS_MASK) == AA_TYPE_JPG;
    struct dim size = { ART_SIDE, ART_SIDE };
    bool has_file = false;
    if (global_settings.album_art != AA_PREFER_EMBEDDED || !has_embedded)
        has_file = find_albumart(&id3, source_path, sizeof(source_path), &size);
    if (!has_file && has_embedded)
    {
        /* Embedded artwork changes with the track, whose time the database
         * knows: no directory scan needed. */
        strmemccpy(source_path, track, sizeof(source_path));
        *embedded = id3.albumart;
        source->hash = hash_string(source_path);
        source->mtime = track_mtime;
        source->size = embedded->size;
        return true;
    }
    else if (!has_file)
        return false;

    source->hash = hash_string(source_path);
    return source_info(source_path, &source->mtime, &source->size);
}

static bool decode_source(const struct mp3_albumart *embedded)
{
    struct bitmap bm = {
        .width = ART_SIDE, .height = ART_SIDE,
        .data = decode_buffer
    };
    int format = FORMAT_NATIVE | FORMAT_RESIZE | FORMAT_KEEP_ASPECT;
    int result;
    if (embedded->type != AA_TYPE_UNKNOWN)
    {
        int fd = open(source_path, O_RDONLY);
        if (fd < 0)
            return false;
        lseek(fd, embedded->pos, SEEK_SET);
        cpu_boost(true);
        result = clip_jpeg_fd(fd, embedded->type, embedded->size, &bm,
                              sizeof(decode_buffer), format, NULL);
        cpu_boost(false);
        close(fd);
    }
    else
    {
        const char *ext = strrchr(source_path, '.');
        cpu_boost(true);
        if (ext && !strcasecmp(ext, ".bmp"))
            result = read_bmp_file(source_path, &bm, sizeof(decode_buffer),
                                   format, NULL);
        else
            result = read_jpeg_file(source_path, &bm, sizeof(decode_buffer),
                                    format, NULL);
        cpu_boost(false);
    }
    if (result <= 0 || bm.width < 1 || bm.height < 1 ||
        bm.width > ART_SIDE || bm.height > ART_SIDE)
        return false;
    memset(rendered, 0, sizeof(rendered));
    int left = (ART_SIDE - bm.width) / 2;
    int top = (ART_SIDE - bm.height) / 2;
    for (int row = 0; row < bm.height; row++)
        memcpy(&rendered[(top + row) * ART_SIDE + left],
               &((fb_data *)bm.data)[row * bm.width], bm.width * sizeof(fb_data));
    return true;
}

/* ---- the files ---- */

static bool read_at(int fd, off_t offset, void *buf, size_t size)
{
    return lseek(fd, offset, SEEK_SET) == offset &&
           read(fd, buf, size) == (ssize_t)size;
}

static off_t cover_offset(int cover)
{
    return sizeof(struct covers_header) +
           (off_t)cover * sizeof(struct cover_record);
}

static bool read_cover(int fd, int cover, fb_data *pixels)
{
    return read_at(fd, cover_offset(cover) + sizeof(struct art_source),
                   pixels, sizeof(rendered));
}

static int open_covers(const char *path)
{
    struct covers_header header;
    int fd = open(path, O_RDONLY);
    if (fd < 0)
        return -1;
    if (!read_at(fd, 0, &header, sizeof(header)) ||
        header.magic != ART_COVERS_MAGIC || header.side != ART_SIDE)
    {
        close(fd);
        return -1;
    }
    return fd;
}

static void close_published(void)
{
    if (pub_index >= 0)
        close(pub_index);
    if (pub_covers >= 0)
        close(pub_covers);
    pub_index = pub_covers = -1;
}

/* Opens index.dat and covers.dat if they belong to the current database */
static bool open_published(void)
{
    struct index_header wanted;
    if (!current_database(&wanted))
    {
        close_published();
        return false;
    }
    if (pub_index >= 0)
    {
        if (same_database(&pub_header, &wanted))
            return true;
        close_published();
    }
    pub_index = open(ART_INDEX, O_RDONLY);
    if (pub_index < 0)
        return false;
    if (!read_at(pub_index, 0, &pub_header, sizeof(pub_header)) ||
        pub_header.magic != ART_INDEX_MAGIC ||
        !same_database(&pub_header, &wanted) ||
        (pub_covers = open_covers(ART_COVERS)) < 0)
    {
        close_published();
        return false;
    }
    return true;
}

/* Binary search in an index file */
static int find_published(const struct albumart_list_key *key)
{
    int low = 0, high = pub_header.count - 1;
    while (low <= high)
    {
        int middle = (low + high) / 2;
        struct index_entry entry;
        if (!read_at(pub_index, sizeof(struct index_header) +
                     (off_t)middle * sizeof(entry), &entry, sizeof(entry)))
            return -1;
        int order = compare_keys(&entry.key, key);
        if (order == 0)
            return entry.cover;
        if (order < 0)
            low = middle + 1;
        else
            high = middle - 1;
    }
    return -1;
}

/* Linear search in the entries a refresh has written so far */
static int find_building(const struct albumart_list_key *key)
{
    struct index_entry entries[32];
    ssize_t got;
    if (lseek(new_entries, 0, SEEK_SET) != 0)
        return -1;
    while ((got = read(new_entries, entries, sizeof(entries))) > 0)
    {
        for (int i = 0; i < got / (int)sizeof(entries[0]); i++)
            if (same_key(&entries[i].key, key))
                return entries[i].cover;
    }
    return -1;
}

/* The cover of an album list row. Lists below other tags than the album
 * artist (e.g. the canonical artist) show the cover of the album itself. */
static bool lookup(const struct albumart_list_key *key, fb_data *pixels)
{
    const struct albumart_list_key album = { key->album_seek, 0, 0 };
    const bool below_parent = key->parent_tag || key->parent_seek;
    int cover;
    if (building && !published_valid)
    {
        cover = find_building(key);
        if (cover < 0 && below_parent)
            cover = find_building(&album);
        return cover >= 0 && read_cover(new_covers, cover, pixels);
    }
    if (!open_published())
        return false;
    cover = find_published(key);
    if (cover < 0 && below_parent)
        cover = find_published(&album);
    return cover >= 0 && read_cover(pub_covers, cover, pixels);
}

/* ---- thumbnails in RAM ---- */

static void put_slot(const struct albumart_list_key *key,
                     const fb_data *pixels)
{
    mutex_lock(&art_mutex);
    int slot = -1;
    for (int i = 0; i < ART_SLOTS; i++)
    {
        if (slots[i].valid && same_key(&slots[i].key, key))
        {
            slot = i;
            break;
        }
    }
    if (slot < 0)
        slot = next_slot++ % ART_SLOTS;
    slots[slot].key = *key;
    slots[slot].preference = global_settings.album_art;
    slots[slot].missing = pixels == NULL;
    if (pixels)
        memcpy(slots[slot].pixels, pixels, sizeof(slots[slot].pixels));
    slots[slot].valid = true;
    bool post_redraw = !redraw_queued;
    redraw_queued = true;
    mutex_unlock(&art_mutex);
    /* UI drawing belongs to the main thread. */
    if (post_redraw)
        button_queue_post(BUTTON_REDRAW, 0);
}

static bool is_resident(const struct albumart_list_key *key)
{
    bool found = false;
    mutex_lock(&art_mutex);
    for (int i = 0; i < ART_SLOTS && !found; i++)
        found = slots[i].valid && same_key(&slots[i].key, key);
    mutex_unlock(&art_mutex);
    return found;
}

static void forget_slots(void)
{
    mutex_lock(&art_mutex);
    for (int i = 0; i < ART_SLOTS; i++)
        slots[i].valid = false;
    mutex_unlock(&art_mutex);
    button_queue_post(BUTTON_REDRAW, 0);
}

static void start_refresh_by_itself(void)
{
    struct index_header wanted;
    if (building || usb_inserted() || !current_database(&wanted) ||
        (auto_started && same_database(&auto_header, &wanted)))
        return;
    auto_started = true;
    auto_header = wanted;
    queue_post(&art_queue, ART_REFRESH, 0);
}

static void serve_request(const struct albumart_list_key *key)
{
    bool found = lookup(key, rendered);
    put_slot(key, found ? rendered : NULL);
    if (!building && !open_published())
        start_refresh_by_itself();
}

static void serve_pending(void)
{
    while (true)
    {
        struct albumart_list_key key;
        mutex_lock(&art_mutex);
        if (pending_count == 0)
        {
            mutex_unlock(&art_mutex);
            return;
        }
        key = pending[--pending_count];
        active_key = key;
        active_key_valid = true;
        mutex_unlock(&art_mutex);
        if (!usb_inserted())
            serve_request(&key);
        mutex_lock(&art_mutex);
        active_key_valid = false;
        mutex_unlock(&art_mutex);
    }
}

/* ---- refresh ---- */

/* Deletes everything in ART_DIR but the published files: thumbnails of the
 * old format (one file per key), files of an interrupted refresh */
static bool purge_directory(void)
{
    DIR *dir = opendir(ART_DIR);
    if (!dir)
        return true;
    struct dirent *entry;
    char path[MAX_PATH];
    while (usable() && (entry = readdir(dir)))
    {
        const char *name = entry->d_name;
        if (!strcmp(name, ".") || !strcmp(name, "..") ||
            !strcmp(name, ART_COVERS_NAME) || !strcmp(name, ART_INDEX_NAME) ||
            (dir_get_info(dir, entry).attribute & ATTR_DIRECTORY))
            continue;
        snprintf(path, sizeof(path), ART_DIR "/%s", name);
        remove(path);
        serve_pending();
        yield();
    }
    closedir(dir);
    return usable();
}

/* Remembers the sources of the old covers, to copy unchanged ones */
static void load_old_sources(void)
{
    struct covers_header header;
    old_count = 0;
    old_covers = open_covers(ART_COVERS);
    if (old_covers < 0 || !read_at(old_covers, 0, &header, sizeof(header)))
        return;
    int count = MIN(header.count, ART_SOURCES);
    while (old_count < count &&
           read_at(old_covers, cover_offset(old_count),
                   &old_sources[old_count], sizeof(old_sources[0])))
        old_count++;
}

static int find_source(const struct art_source *list, int count,
                       const struct art_source *source)
{
    for (int i = 0; i < count; i++)
        if (same_source(&list[i], source))
            return i;
    return -1;
}

static int append_cover(const struct art_source *source)
{
    if (lseek(new_covers, 0, SEEK_END) < 0 ||
        write(new_covers, source, sizeof(*source)) != sizeof(*source) ||
        write(new_covers, rendered, sizeof(rendered)) != sizeof(rendered))
        return -1;
    if (new_count < ART_SOURCES)
        new_sources[new_count] = *source;
    return new_count++;
}

static bool append_entry(const struct albumart_list_key *key, int cover)
{
    struct index_entry entry = { *key, cover };
    if (lseek(new_entries, 0, SEEK_END) < 0 ||
        write(new_entries, &entry, sizeof(entry)) != sizeof(entry))
        return false;
    entry_count++;
    return true;
}

/* One record of ART_KEYS: an album list key and its first track */
struct key_track {
    struct albumart_list_key key;
    int32_t idx_id;
};

/* The cover chosen for each first track of this refresh (-1: none). Most
 * album artist keys share the first track of their album, so their
 * artwork is not looked up again. */
static int32_t memo_track[ART_SOURCES], memo_cover[ART_SOURCES];
static int memo_count;

static bool memo_find(int idx_id, int *cover)
{
    for (int i = memo_count - 1; i >= 0; i--)
    {
        if (memo_track[i] == idx_id)
        {
            *cover = memo_cover[i];
            return true;
        }
    }
    return false;
}

static void memo_add(int idx_id, int cover)
{
    if (memo_count < ART_SOURCES)
    {
        memo_track[memo_count] = idx_id;
        memo_cover[memo_count++] = cover;
    }
}

/* Decoding a large JPEG keeps the CPU for a while and Rockbox only switches
 * threads when one gives way, so start it only while enough audio is
 * buffered for the codec to catch up afterwards. */
static void wait_for_audio(void)
{
    while (usable() && pcmbuf_is_lowdata())
        sleep(HZ / 10);
}

/* Returns true if it looked up artwork (and so is worth a pause) */
static bool sweep_key(const struct key_track *kt)
{
    int cover;
    bool worked = false, have_pixels = false;
    if (!memo_find(kt->idx_id, &cover))
    {
        struct art_source source;
        struct mp3_albumart embedded = { .type = AA_TYPE_UNKNOWN };
        worked = true;
        cover = -1;  /* no artwork: the list shows the default cover */
        if (choose_source(kt->idx_id, &source, &embedded))
        {
            cover = find_source(new_sources, MIN(new_count, ART_SOURCES),
                                &source);
            if (cover < 0)
            {
                int old = find_source(old_sources, old_count, &source);
                if (old >= 0 && read_cover(old_covers, old, rendered))
                    have_pixels = true;
                else
                {
                    wait_for_audio();
                    if (decode_source(&embedded))
                    {
                        have_pixels = true;
                        decoded++;
                    }
                }
                cover = have_pixels ? append_cover(&source) : -1;
            }
        }
        memo_add(kt->idx_id, cover);
    }
    if (cover < 0 || !append_entry(&kt->key, cover))
        return worked;
    /* a visible row gets its new cover now */
    if (is_resident(&kt->key) &&
        (have_pixels || read_cover(new_covers, cover, rendered)))
        put_slot(&kt->key, rendered);
    return worked;
}

/* Keys of one pass: the distinct (album, parent) pairs of the database,
 * each with its first track, from a single pass over the master index.
 * The pairs seen so far are kept in decode_buffer (open addressing, album
 * seek + 1 so that 0 marks a free slot). */
struct collect_state {
    int fd;
    int parent_tag;
    uint32_t *seen;
    unsigned capacity; /* power of two */
    bool okay;
};

static bool collect_entry(int idx_id, int32_t album, int32_t parent,
                          void *data)
{
    struct collect_state *st = data;
    if (!st->parent_tag)
        parent = 0;
    uint32_t a = (uint32_t)album + 1, p = (uint32_t)parent;
    uint32_t h = a * 2654435761u ^ p * 40503u;
    for (unsigned n = 0; n < st->capacity; n++)
    {
        uint32_t *slot = &st->seen[2 * ((h + n) & (st->capacity - 1))];
        if (slot[0] == 0)
        {
            slot[0] = a;
            slot[1] = p;
            struct key_track kt = { { album, st->parent_tag, parent }, idx_id };
            st->okay = write(st->fd, &kt, sizeof(kt)) == sizeof(kt);
            return st->okay && !usb_inserted();
        }
        if (slot[0] == a && slot[1] == p)
            return true; /* a later track of a known key */
    }
    st->okay = false;
    return false;
}

static int compare_key_tracks(const void *a, const void *b)
{
    return compare_keys(&((const struct key_track *)a)->key,
                        &((const struct key_track *)b)->key);
}

/* parent_tag 0: the albums themselves. Album lists below the album artist
 * have keys of their own (tagtree_album_art_key()). The keys are sorted by
 * album, so covers.dat follows the order of the album list. */
static bool collect_keys(int parent_tag, int fd)
{
    struct collect_state st = {
        .fd = fd, .parent_tag = parent_tag, .seen = (uint32_t *)decode_buffer,
        .capacity = sizeof(decode_buffer) / (2 * sizeof(uint32_t)), .okay = true
    };
    memset(decode_buffer, 0, sizeof(decode_buffer));
    if (!tagcache_for_each_entry(tag_album, parent_tag ? parent_tag : -1,
                                 collect_entry, &st) || !st.okay || !usable())
        return false;

    struct key_track *keys = (struct key_track *)decode_buffer;
    off_t size = lseek(fd, 0, SEEK_END);
    int count = size / sizeof(keys[0]);
    if (size < 0 || (size_t)size > sizeof(decode_buffer))
        return size >= 0; /* too many to sort here; the order is optional */
    if (lseek(fd, 0, SEEK_SET) != 0 || read(fd, keys, size) != size)
        return false;
    qsort(keys, count, sizeof(keys[0]), compare_key_tracks);
    return lseek(fd, 0, SEEK_SET) == 0 && write(fd, keys, size) == size;
}

static bool refresh_pass(int parent_tag)
{
    int fd = open(ART_KEYS, O_CREAT | O_TRUNC | O_RDWR, 0666);
    if (fd < 0)
        return false;
    bool okay = collect_keys(parent_tag, fd);
    lseek(fd, 0, SEEK_SET);
    struct key_track kt;
    while (okay && usable() && read(fd, &kt, sizeof(kt)) == sizeof(kt))
    {
        /* A newly opened album list takes priority over the sweep. */
        serve_pending();
        /* pause after real work, longer while music plays */
        if (sweep_key(&kt))
            sleep((audio_status() & AUDIO_STATUS_PLAY) ? HZ / 10 : 1);
        else
            yield();
    }
    close(fd);
    remove(ART_KEYS);
    return okay && usable();
}

/* Writes the sorted entries to ART_INDEX_NEW */
static bool write_index(void)
{
    struct index_entry *entries = (struct index_entry *)decode_buffer;
    int count = MIN(entry_count,
                    (int)(sizeof(decode_buffer) / sizeof(entries[0])));
    if (lseek(new_entries, 0, SEEK_SET) != 0 ||
        read(new_entries, entries, count * sizeof(entries[0])) !=
            (ssize_t)(count * sizeof(entries[0])))
        return false;
    qsort(entries, count, sizeof(entries[0]), compare_entries);
    int unique = 0;
    for (int i = 0; i < count; i++)
        if (unique == 0 || compare_keys(&entries[unique - 1].key,
                                        &entries[i].key) != 0)
            entries[unique++] = entries[i];

    struct index_header header = build_header;
    header.count = index_count = unique;
    int fd = open(ART_INDEX_NEW, O_CREAT | O_TRUNC | O_WRONLY, 0666);
    if (fd < 0)
        return false;
    bool written = write(fd, &header, sizeof(header)) == sizeof(header) &&
        write(fd, entries, unique * sizeof(entries[0])) ==
            (ssize_t)(unique * sizeof(entries[0]));
    close(fd);
    return written;
}

static bool begin_refresh(void)
{
    mkdir(ART_DIR);
    new_count = entry_count = decoded = index_count = memo_count = 0;
    if (!current_database(&build_header) || !purge_directory())
        return false;
    published_valid = open_published();
    load_old_sources();
    new_covers = open(ART_COVERS_NEW, O_CREAT | O_TRUNC | O_RDWR, 0666);
    new_entries = open(ART_ENTRIES, O_CREAT | O_TRUNC | O_RDWR, 0666);
    struct covers_header header = { ART_COVERS_MAGIC, ART_SIDE, 0, 0 };
    if (new_covers < 0 || new_entries < 0 ||
        write(new_covers, &header, sizeof(header)) != sizeof(header))
        return false;
    building = true;
    return true;
}

static void end_refresh(bool okay)
{
    struct index_header now;
    building = false;
    okay = okay && current_database(&now) &&
           same_database(&now, &build_header);
    if (okay)
    {
        struct covers_header header = {
            ART_COVERS_MAGIC, ART_SIDE, new_count, 0
        };
        okay = lseek(new_covers, 0, SEEK_SET) == 0 &&
               write(new_covers, &header, sizeof(header)) == sizeof(header) &&
               write_index();
    }
    if (old_covers >= 0)
        close(old_covers);
    if (new_covers >= 0)
        close(new_covers);
    if (new_entries >= 0)
        close(new_entries);
    old_covers = new_covers = new_entries = -1;
    /* Nothing changed, e.g. after a database update without new artwork:
     * keep the old files instead of writing the same data again. */
    bool unchanged = okay && published_valid && decoded == 0 &&
                     new_count == old_count && index_count == pub_header.count;
    if (okay && !unchanged)
    {
        /* the new files replace the old ones */
        close_published();
        remove(ART_INDEX);
        remove(ART_COVERS);
        okay = rename(ART_COVERS_NEW, ART_COVERS) == 0 &&
               rename(ART_INDEX_NEW, ART_INDEX) == 0;
    }
    remove(ART_COVERS_NEW);
    remove(ART_INDEX_NEW);
    remove(ART_ENTRIES);
    remove(ART_KEYS);
    if (!okay && usb_inserted())
        auto_started = false; /* try again after the USB connection */
    /* rows reload their covers from the new files */
    if (!unchanged)
        forget_slots();
}

static void refresh_all(void)
{
    /* Complete the directly browsed album list first: it is useful while
     * the album artist lists are still being swept. */
    bool okay = begin_refresh() && refresh_pass(0) &&
                refresh_pass(tag_albumartist);
    end_refresh(okay);
}

static void art_thread(void)
{
    struct queue_event event;
    while (true)
    {
        queue_wait(&art_queue, &event);
        if (event.id == SYS_USB_CONNECTED)
        {
            close_published();
            usb_acknowledge(SYS_USB_CONNECTED_ACK, event.data);
            usb_wait_for_disconnect(&art_queue);
        }
        else if (event.id == ART_REQUEST)
            serve_pending();
        else if (event.id == ART_REFRESH && !building)
            refresh_all();
    }
}

void albumart_list_init(void)
{
    mutex_init(&art_mutex);
    queue_init(&art_queue, true);
    create_thread(art_thread, art_stack, sizeof(art_stack), 0,
                  "album art" IF_PRIO(, PRIORITY_BACKGROUND) IF_COP(, CPU));
    art_ready = true;
}

void albumart_list_refresh(void)
{
    if (art_ready)
        queue_post(&art_queue, ART_REFRESH, 0);
}

void albumart_list_draw_special(enum albumart_list_special which, int x, int y)
{
    static const fb_data * const pictures[] = {
        [ALBUMART_LIST_BY_ALBUM] = albumart_list_by_album,
        [ALBUMART_LIST_ALL_TRACKS] = albumart_list_all_tracks,
        [ALBUMART_LIST_RANDOM] = albumart_list_random,
    };
    if ((unsigned)which < ARRAYLEN(pictures))
        lcd_bitmap(pictures[which], x, y, ART_SIDE, ART_SIDE);
}

void albumart_list_draw(const struct albumart_list_key *key, int x, int y)
{
    bool drawn = false;
    bool known = false;
    mutex_lock(&art_mutex);
    redraw_queued = false;
    for (int i = 0; i < ART_SLOTS; i++)
    {
        if (slots[i].valid &&
            slots[i].preference == global_settings.album_art &&
            same_key(&slots[i].key, key))
        {
            known = true;
            if (!slots[i].missing)
            {
                lcd_bitmap(slots[i].pixels, x, y, ART_SIDE, ART_SIDE);
                drawn = true;
            }
            break;
        }
    }
    if (!known)
    {
        bool queued = active_key_valid && same_key(&active_key, key);
        for (int i = 0; i < pending_count; i++)
            queued |= same_key(&pending[i], key);
        if (!queued)
        {
            bool wake = pending_count == 0;
            if (pending_count == ART_PENDING)
            {
                /* Drop the oldest request when a quick scroll moves beyond
                 * the pending window.  The most recent rows matter first. */
                memmove(pending, pending + 1,
                        (ART_PENDING - 1) * sizeof(pending[0]));
                pending_count--;
            }
            pending[pending_count++] = *key;
            if (wake)
                queue_post(&art_queue, ART_REQUEST, 0);
        }
    }
    mutex_unlock(&art_mutex);
    if (!drawn)
        lcd_bitmap(albumart_list_default, x, y, ART_SIDE, ART_SIDE);
}
#endif /* IPOD_6G */
