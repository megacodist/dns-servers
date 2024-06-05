#
# 
#


from collections import namedtuple
import queue


def Func_a(a: int, b: int) -> int:
    return a + b


def Func_b(a: int) -> int:
    return a + 10


def main() -> None:
    from utils.async_ops import AsyncOp
    from concurrent.futures import ThreadPoolExecutor
    from queue import Queue
    q = Queue()
    w = ThreadPoolExecutor()
    a = AsyncOp(w, q,
            start_cb=Func_a,
            start_args=(),
            start_kwargs=None,
            cancel_cb=Func_b)


if __name__ == '__main__':
    main()
