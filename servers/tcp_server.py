import asyncio
from datetime import datetime

from utils import get_logger, HOST, PORT2

logger = get_logger()


class Server(asyncio.Protocol):
    """Сервер обрабатывающий клиентские подключения."""

    CLIENTS_COUNT = 0  # количество клиентских подключений

    def __init__(self):
        Server.CLIENTS_COUNT += 1
        self.client_info = None  # данные о подключении
        self._closed = False  # статус соединения
        self._conn_time = 0  # время простоя

    def do_something(self):
        """
        Обработка текущего соединения. Каждые 2 секунды клиенту возвращается
        время и количество активных подключений. Если время простоя более 5
        сек. возвращается предупреждение с обратным отсчетом. Если время
        простоя превысит 10 сек. соединение разрывается."""

        if self._closed:
            return
        self._conn_time += 1
        if self._conn_time > 0 and self._conn_time % 2 == 0:
            msg = f'time: {datetime.now().strftime("%H:%M:%S")} clints: {Server.CLIENTS_COUNT}\n'
            self.transport.write(msg.encode())
        if self._conn_time > 5:
            msg = f'disconnect in: {10 - self._conn_time} sec.\n'
            self.transport.write(msg.encode())
        if self._conn_time >= 10:
            logger.info("connection_timeout: %s", self.client_info)
            self._closed = True
            self.transport.close()
            Server.CLIENTS_COUNT -= 1
        asyncio.get_running_loop().call_later(1, self.do_something)

    def connection_made(self, transport):
        """Обработка нового соединения."""

        self.transport = transport
        self.client_info = self.transport.get_extra_info("peername")
        logger.info(f"connection_made from: {self.client_info}")
        asyncio.get_running_loop().call_soon(self.do_something)

    def connection_lost(self, reason):
        """Обработка потери соединения."""

        self._closed = True
        logger.info("connection_lost: %s | %s" % (self.client_info, reason))

    def data_received(self, data):
        """Обработка полученной информации."""

        self._conn_time = 0
        logger.info("Received: %s", data.decode().strip())
        self.transport.write(data)


def serve(host: str = HOST, port: int = PORT2):

    # создаем цикл событий (устарело с версии 3.10)
    loop = asyncio.get_event_loop()

    # создаем сервер
    coro = loop.create_server(Server, host, port)

    # запускаем сервер на исполнение
    server = loop.run_until_complete(coro)
    logger.info('Server started on port %s', port)
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        logger.info('Stop server')
    finally:
        server.close()
        loop.close()
