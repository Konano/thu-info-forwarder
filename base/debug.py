import logging
import traceback
from datetime import datetime
from typing import Optional

from base.log import logger


def exception_desc(e: Exception) -> str:
    """
    Return exception description.
    """
    if str(e) != '':
        return f'{e.__class__.__module__}.{e.__class__.__name__} ({e})'
    return f'{e.__class__.__module__}.{e.__class__.__name__}'


def eprint(e: Exception, level: int = logging.WARNING, msg: Optional[str] = None, stacklevel: int = 2) -> None:
    """
    Print exception with traceback.
    """
    if not (isinstance(level, int) and level in logging._levelToName):
        level = logging.WARNING

    if msg is not None:
        logger.log(level, msg, stacklevel=stacklevel)

    exception_str = f'Exception: {exception_desc(e)}'
    logger.log(level, exception_str, stacklevel=stacklevel)

    logger.debug(traceback.format_exc(), stacklevel=stacklevel)


def archive(url: str, content, suffix: str) -> None:
    now = str(datetime.now()).replace(' ', '_').replace(':', '-')
    filepath = f'log/archive/{now}.{suffix}'
    if isinstance(content, str):
        open(filepath, 'w').write(content)
    else:
        open(filepath, 'wb').write(content)
    logger.debug(f'{url = }')
    logger.debug(f'{filepath = }')
