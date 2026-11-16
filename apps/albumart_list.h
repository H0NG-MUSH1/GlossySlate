#ifndef ROCKBOX_ALBUMART_LIST_H
#define ROCKBOX_ALBUMART_LIST_H

#ifdef IPOD_6G
/* Side of the square covers in album lists. It is the album row height with
 * the font of GlossySlate (two 24 px text lines plus 4 px), so a cover fills
 * its row; smaller fonts centre the text in the row. The cache files store
 * it and are made anew when it changes. tools/ipod6g_albumart_header.py
 * reads it for the default cover and the pictures of the special entries. */
#define ALBUMART_LIST_SIZE 52

struct albumart_list_key {
    int album_seek;
    int parent_tag;
    int parent_seek;
};

void albumart_list_init(void);
void albumart_list_refresh(void);
void albumart_list_draw(const struct albumart_list_key *key, int x, int y);

/* Fixed pictures of the entries at the top of album lists */
enum albumart_list_special {
    ALBUMART_LIST_BY_ALBUM,    /* all tracks sorted by album */
    ALBUMART_LIST_ALL_TRACKS,
    ALBUMART_LIST_RANDOM,
};
void albumart_list_draw_special(enum albumart_list_special which, int x, int y);
#endif

#endif
