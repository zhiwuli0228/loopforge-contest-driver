typedef struct counter_state { int value; } counter_state_t;

static int checked_add(int value, int amount) { return value + amount; }
int counter_increment(counter_state_t *state, int amount) {
    state->value = checked_add(state->value, amount);
    return state->value;
}
