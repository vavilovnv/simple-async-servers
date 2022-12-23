import selectors
import socket
import time

from psutil import cpu_count, disk_usage, virtual_memory
from utils import HOST, PORT1, get_logger

logger = get_logger()


def new_connection(selector: selectors.BaseSelector, sock: socket.socket):
    """
    Получение нового соединения для регистрации метода обработки события.
    """

    new_conn, address = sock.accept()
    logger.info('accepted new_conn from %s', address)
    new_conn.setblocking(False)

    # передача на обработку события ОС
    selector.register(new_conn, selectors.EVENT_READ, read_callback)


def read_callback(selector: selectors.BaseSelector, sock: socket.socket):
    """Обработка команд."""

    mb_in_gb = 1048576

    # получение данных
    data = sock.recv(1024)
    # обработка данных
    if isinstance(data, bytes):
        command = data.decode(encoding='UTF-8').strip()
        if command == 'hi':
            logger.info('sending greetings')
            sock.send(b'Welcome!\n')
        elif command == 'time':
            sock.send(time.ctime().encode())
        elif command == 'echo':
            logger.info('sending echo %s', command)
            sock.send(data)
        elif command == 'info':
            memory = virtual_memory().total // mb_in_gb
            disk_space = disk_usage("/").total // mb_in_gb
            cpu = cpu_count()
            info = f'CPU count: {cpu} mem: {memory} disk: {disk_space}\n'
            logger.info('sending info %s', info.strip())
            sock.send(info.encode())
        elif command == 'quit':
            logger.info('closing connection %s', sock)
            selector.unregister(sock)
            sock.close()
        else:
            logger.info('unknowing command received %s', command)
            sock.send(b'Command unknown!\n')
    else:
        logger.info('closing connection %s', sock)
        selector.unregister(sock)
        sock.close()


def run_iteration(selector: selectors.BaseSelector):
    """Получение и передача на обработку событий ОС."""

    events = selector.select()  # ждем получение события

    # key - SelectorKey
    #   data - параметр содержит данные, которые передали при регистрации
    #          в нашем случае это функция new_connection для обработки события
    #   fileobj - сокет
    # mask - Информация о событии:
    #   0 — не произошло ни одного из событий;
    #   1 — произошло событие EVENT_READ;
    #   2 — произошло событие EVENT_WRITE;
    #   3 — произошли оба события: и EVENT_READ, и EVENT_WRITE
    for key, mask in events:
        callback = key.data  # получаем функцию new_connection
        callback(selector, key.fileobj)  # вызываем функцию


def serve(host: str = HOST, port: int = PORT1):
    """Основной код echo-сервера."""

    # Запускаем сервер на прослушивание новых сообщений
    with selectors.SelectSelector() as selector:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:

            # включаем переиспользование портов
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

            # создаем серверный сокет для обмена данными между процессами
            server.bind((host, port))

            # переводим сокет в режим прослушки запросов
            server.listen()

            # Делаем сокет не блокирующим
            server.setblocking(False)
            logger.info('Server started on port %s', port)

            # Регистрация события для вызова new_connection
            selector.register(server, selectors.EVENT_READ, new_connection)

            while True:
                try:
                    run_iteration(selector)
                except KeyboardInterrupt:
                    logger.info('Stop server')
