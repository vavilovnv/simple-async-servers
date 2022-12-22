import logging
import selectors
import socket
import sys
import time

# любой ip, порт 8888
HOST, PORT = '', 8888


logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.addHandler(logging.StreamHandler(stream=sys.stdout))


def send_message(selector: selectors.BaseSelector, sock: socket.socket):
    """Отправка приветственного сообщения."""

    data = sock.recv(2048)
    if data == 'hi':
        # отправка данных
        sock.send(b'Welcome!')
    elif data == 'time':
        sock.send(time.ctime().encode(encodings='UTF-8'))
    else:
        logger.info('closing connection %s', sock)
        selector.unregister(sock)
        sock.close()


def new_connection(selector: selectors.BaseSelector, sock: socket.socket):
    """
    Получение нового соединения для регистрации метода обработки события ОС.
    """

    new_conn, address = sock.accept()
    logger.info('accepted new_conn from %s', address)
    new_conn.setblocking(False)

    # передача на обработку события ОС
    selector.register(new_conn, selectors.EVENT_READ, send_message)
    # selector.register(new_conn, selectors.EVENT_READ, read_callback)


def read_callback(selector: selectors.BaseSelector, sock: socket.socket):
    """Чтение и отправка данных."""

    # получение данных
    data = sock.recv(1024)
    if data:
        # отправка данных
        sock.send(data)
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


def serve_forever():
    """Основной код echo-сервера."""

    # Запускаем сервер на прослушивание новых сообщений
    with selectors.SelectSelector() as selector:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:

            # включаем переиспользование портов
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, True)

            # создаем серверный сокет для обмена данными между процессами
            server_socket.bind((HOST, PORT))

            # переводим сокет в режим прослушки запросов
            server_socket.listen()

            # Делаем сокет не блокирующим
            server_socket.setblocking(False)
            logger.info('Server started on port %s', PORT)

            # Регистрация события для вызова new_connection
            selector.register(server_socket, selectors.EVENT_READ, new_connection)

            while True:
                run_iteration(selector)


if __name__ == '__main__':

    # запускаем сервер на исполнение
    serve_forever()
