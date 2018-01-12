from datetime import timedelta
import enum
import hashlib
import json
import logging
import os

__all__ = ["AlertLevel", "Alert", "AlertSource", "FilePresenceAlertSource", "ThreadedAlertSource",
           "AlertService", "ThreadedAlertService", "ProThreadedAlertService",
           "format_alerts", "ellipsis"]

logger = logging.getLogger(__name__)

undefined = object()


class AlertLevel(enum.Enum):
    INFO = 20
    WARNING = 30
    CRITICAL = 50


class Alert:
    def __init__(self, title=None, args=None, source=None, key=undefined, datetime=None, level=None, dismissed=None):
        self.title = title
        self.args = args

        self.source = source
        if key is not undefined:
            self.key = key
        else:
            self.key = self.formatted
        self.datetime = datetime
        self.level = level
        self.dismissed = dismissed

    def __repr__(self):
        return repr(self.__dict__)

    @property
    def level_name(self):
        return AlertLevel(self.level).name

    @property
    def formatted(self):
        if self.args:
            try:
                return self.title % self.args
            except Exception:
                logger.error("Error formatting alert: %r, %r", self.title, self.args, exc_info=True)

        return self.title


class AlertSource:
    level = NotImplemented
    title = NotImplemented

    hardware = False

    onetime = False
    interval = timedelta()

    def __init__(self, middleware):
        self.middleware = middleware

    @property
    def name(self):
        return self.__class__.__name__.replace("AlertSource", "")

    async def check(self):
        raise NotImplementedError


class FilePresenceAlertSource(AlertSource):
    path = NotImplementedError

    async def check(self):
        if os.path.exists(self.path):
            return Alert()


class ThreadedAlertSource(AlertSource):
    async def check(self):
        return await self.middleware.run_in_thread(self.check_sync)

    def check_sync(self):
        raise NotImplementedError


class AlertService:
    title = NotImplementedError

    schema = NotImplementedError

    def __init__(self, middleware, attributes):
        self.middleware = middleware
        self.attributes = attributes

        self.logger = logging.getLogger(self.__class__.__name__)

    @classmethod
    def name(cls):
        return cls.__name__.replace("AlertService", "")

    @classmethod
    def validate(cls, attributes):
        cls.schema.validate(attributes)

    async def send(self, alerts, gone_alerts, new_alerts):
        raise NotImplementedError

    def _alert_id(self, alert):
        return hashlib.sha256(json.dumps([alert.source, alert.key]).encode("utf-8")).hexdigest()


class ThreadedAlertService(AlertService):
    async def send(self, alerts, gone_alerts, new_alerts):
        return await self.middleware.run_in_thread(self.send_sync, alerts, gone_alerts, new_alerts)

    def send_sync(self, alerts, gone_alerts, new_alerts):
        raise NotImplementedError


class ProThreadedAlertService(ThreadedAlertService):
    def send_sync(self, alerts, gone_alerts, new_alerts):
        exc = None

        for alert in gone_alerts:
            try:
                self.delete_alert(alert)
            except Exception as e:
                self.logger.warning("An exception occurred while deleting alert", exc_info=True)
                exc = e

        for alert in new_alerts:
            try:
                self.create_alert(alert)
            except Exception as e:
                self.logger.warning("An exception occurred while creating alert", exc_info=True)
                exc = e

        if exc is not None:
            raise exc

    def create_alert(self, alert):
        raise NotImplementedError

    def delete_alert(self, alert):
        raise NotImplementedError


def format_alerts(alerts, gone_alerts, new_alerts):
    text = ""

    if new_alerts:
        text += "New alerts:\n" + "".join([f"* {alert.formatted}\n" for alert in new_alerts]) + "\n"

    if gone_alerts:
        text += "Gone alerts:\n" + "".join([f"* {alert.formatted}\n" for alert in gone_alerts]) + "\n"

    if alerts:
        text += "Alerts:\n" + "".join([f"* {alert.formatted}\n" for alert in new_alerts]) + "\n"

    return text


def ellipsis(s, l):
    if len(s) <= l:
        return s

    return s[:(l - 1)] + "…"