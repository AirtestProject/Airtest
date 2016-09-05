#ifndef __minicap_dbg_h__
#define __minicap_dbg_h__

// These macros were originally from
// http://c.learncodethehardway.org/book/ex20.html

#include <stdio.h>
#include <errno.h>
#include <string.h>

#ifdef NDEBUG
#define MCDEBUG(M, ...)
#else
#define MCDEBUG(M, ...) fprintf(stderr, "DEBUG: %s:%d: " M "\n", __FILE__, __LINE__, ##__VA_ARGS__)
#endif

#define MCCLEAN_ERRNO() (errno == 0 ? "None" : strerror(errno))

#define MCERROR(M, ...) fprintf(stderr, "ERROR: (%s:%d: errno: %s) " M "\n", __FILE__, __LINE__, MCCLEAN_ERRNO(), ##__VA_ARGS__)

#define MCWARN(M, ...) fprintf(stderr, "WARN: (%s:%d: errno: %s) " M "\n", __FILE__, __LINE__, MCCLEAN_ERRNO(), ##__VA_ARGS__)

#define MCINFO(M, ...) fprintf(stderr, "INFO: (%s:%d) " M "\n", __FILE__, __LINE__, ##__VA_ARGS__)

#define MCCHECK(A, M, ...) if(!(A)) { MCERROR(M, ##__VA_ARGS__); errno=0; goto error; }

#define MCSENTINEL(M, ...)  { MCERROR(M, ##__VA_ARGS__); errno=0; goto error; }

#define MCCHECK_MEM(A) check((A), "Out of memory.")

#define MCCHECK_DEBUG(A, M, ...) if(!(A)) { MCDEBUG(M, ##__VA_ARGS__); errno=0; goto error; }

#endif
