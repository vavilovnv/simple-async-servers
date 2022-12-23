from servers import http_server, tcp_server


if __name__ == '__main__':

    while True:
        serv = int(input('Выберите сервер для запуска (1 - http, 2 - tcp): '))
        if serv == 1:
            # запускаем http-сервер на исполнение
            http_server.serve()
            break
        elif serv == 2:
            # запускаем tcp-сервер на исполнение
            tcp_server.serve()
            break

