import socket
import select
from response.response import Response
from request.request import Request

# class coro:
#     def __init__(self, func):
#         self._callable = func
#
#     def __call__(self, *args, **kwargs):
#         func = self._callable(*args, **kwargs)
#         func.send(None)
#         return func

def coro(f):
    def func(*args, **kwargs):
        c = f(*args, **kwargs)
        c.send(None)
        return c

    return func


class Loop:
    def __init__(self):
        self._tasks = []

    def create_task(self, coro):
        self._tasks.append(coro)

    def _step(self):
        for task in self._tasks:
            try:
                print(f'task is {task}')
                next(task)
            except StopIteration:
                print(f'task complete {task}')
                self._tasks.remove(task)

    def run(self):
        while self._tasks:
            self._step()




class Server:
    def __init__(self, loop, host='0.0.0.0', port=3000, socket_opts=[socket.AF_INET, socket.SOCK_STREAM]):
        self._host = host
        self._port = port
        self._socket_opts = socket_opts
        self._loop: Loop = loop



    @coro
    def write_answer(self, con, req: Request):
        i = 0
        step = 1024
        resp = Response(status=200, )
        while i < len(resp.data):
            tosend = resp.data[i:i+step]
            print(f'to send: {tosend}')
            con.send(tosend)
            i+=step
            yield
        con.close()
        raise StopIteration



    @coro
    def add_connection(self, server: socket.socket, epoll=None):
        con, _ = server.accept()
        con.setblocking(0)
        # inputs.append(con)
        print(f'add conn {con}')
        # write.append(con)
        epoll.register(con.fileno(), select.EPOLLIN)
        while True:
            data = b''
            msg = b''
            try:
                #print("BEFORE DATA", con)
                data = con.recv(1024)
                #print(f"DATA {data}")
            except ConnectionResetError:
                print("Closed!")
                con.close()
                raise StopIteration
            except Exception as e:
                print("EXCEPTION:", e)
            if data:
                msg += data
                yield
            else:
                print("STOP ITER")
                req = Request(msg.decode('utf-8'))
                self._loop.create_task(self.write_answer(con, req))
                raise StopIteration

    @coro
    def start(self):
        server = socket.socket(*self._socket_opts)
        epoll = select.epoll()
        epoll.register(server.fileno(), select.EPOLLIN)
        server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server.bind((self._host, self._port))
        server.listen(5)
        server.setblocking(0)
        server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
        server_fd = server.fileno()

        # server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        # server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # server.setblocking(0)
        #
        # # Биндим сервер на нужный адрес и порт
        # server.bind((self._host, self._port))
        #
        # # Установка максимального количество подключений
        # server.listen(5)
        # INPUTS = []
        # INPUTS.append(server)
        # OUTPUTS=[]
        print("starting server at {}:{}".format(self._host, self._port))
        try:
            while True:
                events = epoll.poll(1)
                for fileno, event in events:
                    if fileno == server_fd:
                        print("WE HERE")
                        self._loop.create_task(self.add_connection(server, epoll))
                    elif event & select.EPOLLIN:
                        pass
                    elif event & select.EPOLLOUT:
                        pass
                # readables, writable, _ = select.select(INPUTS, OUTPUTS, INPUTS, 1)
                # for input in readables:
                #     if input is server:
                #         print("creating task", input)
                #         self._loop.create_task(self.add_connection(input, write=writable, inputs=INPUTS))
                # for w in writable:
                #     r = Response()
                #     w.send(r.data)
                yield
        except KeyboardInterrupt:
            print("server stop")
        finally:
            server.close()
            #epoll.unregister(server.fileno())
            #epoll.close()

    def stop(self):
        pass
