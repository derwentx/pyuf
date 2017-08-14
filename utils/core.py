import os
import re
import sys

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from uf.utils.log import logging

"""
Functions used by utilities.
"""

SIMPLE_RESPONSE_REGEX = r"ok V(?P<response>\S+)"

def send_cmd_sync_ok(swift, command, response_regex=None):
    """
    Send a command and wait for it to complete. Optionally parse the response.
    """
    logging.debug("sending command \"%s\"" % command)
    response = swift.send_cmd_sync(command)
    logging.debug("command response \"%s\"" % response)
    if not response.startswith("ok"):
        raise RuntimeError("command \"%s\" failed: %s" % (command, response))
    if response_regex:
        response_match = re.search(response_regex, response)
        if response_match and 'response' in response_match.groupdict():
            response = response_match.groupdict()['response']
        else:
            raise ValueError(
                "response \"%s\" for command \"%s\" did not match regex \"%s\"" %
                (response, command, response_regex)
            )
    return response
