#include <stdio.h>
#include <stdlib.h>
#include "skin_parser.h"
#include "skin_debug.h"
static int count_nodes(struct skin_element *e, int depth, int *maxdepth) {
    int n = 0;
    while (e) {
        n++;
        if (depth > *maxdepth) *maxdepth = depth;
        for (int i = 0; i < e->children_count; i++)
            n += count_nodes(e->children[i], depth + 1, maxdepth);
        e = e->next;
    }
    return n;
}
int main(int argc, char **argv) {
    FILE *f = fopen(argv[1], "rb"); fseek(f, 0, SEEK_END); long n = ftell(f); fseek(f, 0, SEEK_SET);
    char *buf = malloc(n + 1); fread(buf, 1, n, f); buf[n] = 0; fclose(f);
    struct skin_element *tree = skin_parse(buf);
    if (!tree) {
        printf("PARSE ERROR line %d col %d: %s\n", skin_error_line(), skin_error_col(), skin_error_message());
        return 1;
    }
    int md = 0; int nodes = count_nodes(tree, 0, &md);
    printf("OK: %d elements, depth %d\n", nodes, md);
    if (argc > 2) skin_debug_tree(tree);
    return 0;
}
