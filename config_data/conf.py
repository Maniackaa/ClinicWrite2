import logging.config
from dataclasses import dataclass

import pytz
import structlog
from environs import Env
from pathlib import Path

from structlog.contextvars import merge_contextvars

BASE_DIR = Path(__file__).resolve().parent.parent
LOG_PATH = BASE_DIR / 'logs'

timestamper = structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False)
pre_chain = [
    structlog.stdlib.add_log_level,
    structlog.stdlib.ExtraAdder(),
    timestamper,
]
def extract_from_record(_, __, event_dict):
    """
    Extract thread and process names and add them to the event dict.
    """
    # record = event_dict["_record"]
    # event_dict["thread_name"] = record.threadName
    # event_dict["process_name"] = record.processName
    # print(event_dict)
    # event = event_dict.get('event', '')
    return event_dict
handlers = {
    "console": {
        "level": f"DEBUG",
        "class": "logging.StreamHandler",
        "formatter": "colored",
    },
    "file": {
        "level": "DEBUG",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOG_PATH / "file.log",
        'encoding': 'utf-8',
        "formatter": "plain",
        'when': 'h',
        'interval': 6,
        'backupCount': 7
    },
    "file_color": {
        "level": "DEBUG",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOG_PATH / "file_color.log",
        'encoding': 'utf-8',
        "formatter": "colored",
        'when': 'h',
        'interval': 6,
        'backupCount': 7
    },
    "file_json": {
        "level": "DEBUG",
        "class": "logging.handlers.TimedRotatingFileHandler",
        "filename": LOG_PATH / "file_json.log",
        'encoding': 'utf-8',
        "formatter": "plain_json",
        'when': 'h',
        'interval': 6,
        'backupCount': 7
    },
}

loggers = {"": {"handlers": ["console", "file", "file_color", "file_json"],
                "level": f"DEBUG",
                "propagate": False,
                },
           }

logging.config.dictConfig(
    {
        "version": 1,
        "disable_existing_loggers": True,
        "formatters": {
            "plain": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    # structlog.dev.ConsoleRenderer(colors=False),
                    structlog.dev.ConsoleRenderer(colors=False)
                ],
                "foreign_pre_chain": pre_chain,
            },
            "plain_json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    # structlog.dev.ConsoleRenderer(colors=False),
                    structlog.processors.JSONRenderer(ensure_ascii=False)
                ],
                "foreign_pre_chain": pre_chain,
            },
            "colored": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    extract_from_record,
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                    structlog.dev.ConsoleRenderer(colors=True),
                ],
                "foreign_pre_chain": pre_chain,
            },
        },
        "handlers": handlers,
        "loggers": loggers,

    }
)


def add_phone_name(a, b, event_dict):

    if 'phone_name' in event_dict.keys():
        phone_label = f"-{event_dict.get('phone_name', ''):2}-"
        if event_dict.get('event'):
            event_dict['event'] = f"{phone_label} {event_dict['event']}"
    return event_dict


def filter_f(_, __, event_dict):
    if "Using proactor: IocpProactor" == event_dict.get("event"):
        raise structlog.DropEvent
    return event_dict


structlog.configure(
    processors=[
        merge_contextvars,
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        # structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        # structlog.processors.TimeStamper(fmt="iso"),
        # If the "stack_info" key in the event dict is true, remove it and
        # render the current stack trace in the "stack" key.
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        # If some value is in bytes, decode it to a Unicode str.
        # structlog.processors.UnicodeDecoder(encoding='utf-8'),
        # structlog.processors.UnicodeEncoder(encoding='utf-8'),
        # Add callsite parameters.
        filter_f,
        structlog.processors.CallsiteParameterAdder(
            {
                structlog.processors.CallsiteParameter.FILENAME,
                structlog.processors.CallsiteParameter.FUNC_NAME,
                structlog.processors.CallsiteParameter.LINENO,
                # structlog.processors.CallsiteParameter.PATHNAME ,
                # structlog.processors.CallsiteParameter.MODULE,
                # structlog.processors.CallsiteParameter.PROCESS,
                # structlog.processors.CallsiteParameter.PROCESS_NAME,
                # structlog.processors.CallsiteParameter.THREAD,
                # structlog.processors.CallsiteParameter.THREAD_NAME
            }
        ),
        # structlog.processors.JSONRenderer(),
        structlog.stdlib.ExtraAdder(),
        add_phone_name,
        structlog.dev.ConsoleRenderer(colors=False),
        # structlog.processors.JSONRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    # wrapper_class=AsyncBoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger: structlog.stdlib.BoundLogger = structlog.get_logger('file')
logger.debug('Логгер debug')
logger.info('Логгер OK')

@dataclass
class PostgresConfig:
    database: str  # Название базы данных
    db_host: str  # URL-адрес базы данных
    db_port: str  # URL-адрес базы данных
    db_user: str  # Username пользователя базы данных
    db_password: str  # Пароль к базе данных


@dataclass
class RedisConfig:
    redis_db_num: str  # Название базы данных
    redis_host: str  # URL-адрес базы данных
    REDIS_PORT: str  # URL-адрес базы данных
    REDIS_PASSWORD: str


@dataclass
class TgBot:
    token: str  # Токен для доступа к телеграм-боту
    admin_ids: list[str]  # Список id администраторов бота
    base_dir = BASE_DIR
    TIMEZONE: pytz.timezone
    GROUP_ID: int  # ID канала для уведомлений о заявках
    price_file_id: str = None  # File ID прайса для отправки по ID


@dataclass
class Logic:
    pass


@dataclass
class Config:
    tg_bot: TgBot
    db: PostgresConfig
    logic: Logic


def load_config(path) -> Config:
    env: Env = Env()
    env.read_env(path)

    return Config(tg_bot=TgBot(token=env('BOT_TOKEN'),
                               admin_ids=list(map(str, env.list('ADMIN_IDS'))),
                               TIMEZONE=pytz.timezone(env('TIMEZONE')),
                               GROUP_ID=int(env('GROUP_ID')),
                               price_file_id=env('PRICE_FILE_ID', default=None),
                               ),
                  db=PostgresConfig(
                      database=env('POSTGRES_DB'),
                      db_host=env('DB_HOST'),
                      db_port=env('DB_PORT'),
                      db_user=env('POSTGRES_USER'),
                      db_password=env('POSTGRES_PASSWORD'),
                      ),
                  logic=Logic(),
                  )


conf = load_config('.env')
conf.db.db_url = f"postgresql+psycopg2://{conf.db.db_user}:{conf.db.db_password}@{conf.db.db_host}:{conf.db.db_port}/{conf.db.database}"

tz = conf.tg_bot.TIMEZONE


