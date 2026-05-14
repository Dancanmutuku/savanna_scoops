import logging
import traceback

from django.db import OperationalError, ProgrammingError


class DatabaseLogHandler(logging.Handler):
    def emit(self, record):
        try:
            from .models import SystemLog

            request = getattr(record, 'request', None)
            path = getattr(request, 'path', '') if request else ''
            exc_text = ''
            if record.exc_info:
                exc_text = ''.join(traceback.format_exception(*record.exc_info))

            SystemLog.objects.create(
                level=record.levelname.lower(),
                logger_name=record.name[:150],
                message=self.format(record),
                module=(record.module or '')[:100],
                function=(record.funcName or '')[:100],
                path=path[:300],
                traceback=exc_text,
            )
        except (OperationalError, ProgrammingError):
            pass
        except Exception:
            pass
