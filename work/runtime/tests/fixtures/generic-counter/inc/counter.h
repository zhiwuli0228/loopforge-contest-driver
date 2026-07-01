#ifndef COUNTER_H
#define COUNTER_H

typedef struct counter_state { int value; } counter_state_t;
int counter_increment(counter_state_t *state, int amount);

#endif
