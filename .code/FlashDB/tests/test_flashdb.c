#include "flashdb.h"

/*
 * Scenario inventory for the Rust migration:
 * 1. creating an empty database starts with count == 0
 * 2. setting and getting a key returns the stored value
 * 3. overwriting a key preserves uniqueness and exposes the new value
 * 4. deleting a key removes it and decreases the entry count
 */
