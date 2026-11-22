import asyncio

from .observer import Subscriber

HEARTBEAT_SECONDS = 15


class LiveNotifications(Subscriber):
    def __init__(self):
        self._subscribers = {}

    def subscribe(self, user_id, is_admin):
        queue = asyncio.Queue()
        self._subscribers[queue] = (user_id, is_admin)
        return queue

    def unsubscribe(self, queue):
        self._subscribers.pop(queue, None)

    async def on_event(self, event):
        for queue, (user_id, is_admin) in self._subscribers.items():
            if (event.recipient_id is None and is_admin) or (
                event.recipient_id == user_id
            ):
                queue.put_nowait(event.type)

    def signal_admins(self):
        for queue, (_, is_admin) in self._subscribers.items():
            if is_admin:
                queue.put_nowait("changed")

    async def stream(self, user_id, is_admin):
        queue = self.subscribe(user_id, is_admin)
        try:
            yield ": connected\n\n"
            while True:
                try:
                    await asyncio.wait_for(queue.get(), HEARTBEAT_SECONDS)
                    yield "event: changed\ndata: {}\n\n"
                except TimeoutError:
                    yield ": ping\n\n"
        finally:
            self.unsubscribe(queue)


live_notifications = LiveNotifications()
