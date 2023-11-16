# _*_ coding:UTF-8 _*_
import time
import functools


def retries(max_tries, delay=1, backoff=2, exceptions=(Exception,), hook=None):
    """
    Function decorator implementing logic to recover from fatal errors. If a function fails to call due to any
    fatal error, the decoration tries to call it again after given delay time.

    The call delay time is counted as follows:
    delay * backoff * number of attempts to call the function after its failure

    It is possible to specify the custom tuple of exception classes within the 'exceptions' parameter. Only if such
    exception is detected, the function retries to call itself again.

    It is also possible to specify a hook function (with number of remaining re-tries and exception instance) which
    will be called prior the retrying attempt. Using the hook function gives the possibility to log the failure.
    Hook function is not called after failures or when no attempts left.

    Args:
        max_tries: maximum number of attempts to call the function, the decorator will call the function up
                   to max_tries, if all attempts fails, then the exception is risen
        delay: parameter to count the sleep time
        backoff: parameter to count the sleep time
        exceptions: A tuple of exception classes; default (Exception,)
        hook: A function with the signature myhook(tries_remaining, exception);
              default value is None

    Raises:
        Exception class and subclasses by default

    Returns:
        wrapper

    """

    def dec(func):
        @functools.wraps(func)
        def f2(*args, **kwargs):
            mydelay = delay
            tries = range(max_tries)
            # support Python conver range obj to list obj
            tries = list(tries)

            tries.reverse()
            for tries_remaining in tries:
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if tries_remaining > 0:
                        if hook is not None:
                            hook(tries_remaining, e, mydelay)
                        time.sleep(mydelay)
                        mydelay = mydelay * backoff
                    else:
                        raise
                else:
                    break

        return f2

    return dec
