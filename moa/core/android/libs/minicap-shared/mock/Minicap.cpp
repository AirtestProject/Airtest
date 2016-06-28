// The only purpose of this file is to make the project build without any
// complaints about missing libraries (which exist on the device side).
// While we could also use one of the actual built libs, they might depend
// on other shared libraries, making this right here the easiest way to
// enable interoperability.

#include "Minicap.hpp"

int
minicap_try_get_display_info(int32_t displayId, Minicap::DisplayInfo* info) {
  return 0;
}

Minicap*
minicap_create(int32_t displayId) {
  return NULL;
}

void
minicap_free(Minicap* mc) {
}

void
minicap_start_thread_pool() {
}
