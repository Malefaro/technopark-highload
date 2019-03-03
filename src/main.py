from server.server import *

@coro
def f(a, b, name):
    for i in range(10):
        # print("f loop")
        print(f"[step {i}]{name}: a={a}, b={b}")
        yield (a, b)


loop = Loop()
# c1 = f(1, 2, "c1")
# c2 = f(3, 4, "c2")
# loop.create_task(c1)
# loop.create_task(c2)
server = Server(loop=loop)
loop.create_task(server.start())
loop.run()