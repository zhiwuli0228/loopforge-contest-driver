#include <assert.h>
int counter_increment(void *state, int amount);
int main(void) { assert(counter_increment((void *)0, 1) == 1); return 0; }
