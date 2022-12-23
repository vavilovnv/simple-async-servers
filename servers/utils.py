import logging
import sys

HOST, PORT1, PORT2 = '127.0.0.1', 8888, 8889


def get_logger():
    logging.basicConfig(
        level=logging.INFO,
        stream=sys.stdout,
        format='%(name)s - %(asctime)s - %(levelname)s - %(message)s',
    )
    return logging.getLogger('server')
