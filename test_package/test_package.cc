#include <stdio.h>
#include <glib.h>

int main()
{
    GList *list = g_list_append(NULL, (gpointer)"Successfully initialized glib.");
    printf("%s\n", g_list_first(list)->data);
	return 0;
}
