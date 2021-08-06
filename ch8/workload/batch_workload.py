import asyncio
import aiohttp
import time
import random
import string

import bcrypt
import requests


class AsyncBatcher(object):
    def __init__(self, batch_size):
        self.batch_size = batch_size
        self.batch = []
        self.client_session = None
        self.url = f"http://127.0.0.1:8080/add"

    def __enter__(self):
        return self

    def __exit__(self, *args, **kwargs):
        self.flush()

    def save(self, result):
        self.batch.append(result)
        if len(self.batch) == self.batch_size:
            self.flush()

    def flush(self):
        loop = asyncio.get_event_loop()
        loop.run_until_complete(self.__flush()) # <1> 비동기 함수 하나만 실행하려고 이벤트 루프를 시작할수 있다. 이후 코드는 일반적인 코드처럼 실행한다.

    async def __flush(self): # <2> 앞서 살펴본 aiohttp 예제와 비슷
        async with aiohttp.ClientSession() as session:
            tasks = [self.fetch(result, session) for result in self.batch]
            for task in asyncio.as_completed(tasks):
                await task
        self.batch.clear()

    async def fetch(self, result, session):
        async with session.post(self.url, data=result) as response:
            return await response.json()

def calculate_task_batch(num_iter, task_difficulty):
    batcher = AsyncBatcher(100) # 결과 100개를 하나로 묶어서 데이터베이스에 비동기적으로 한번에 넣는다.
    for i in range(num_iter):
        result = do_task(i, task_difficulty)
        batcher.save(result)
    batcher.flush()

data = {
            "async": [],
            "serial": [],
            "no IO": [],
            "file IO": [],
            "batches": [],
            "async+uvloop": [],
        }

def do_task(i, difficulty):
    passwd = "".join(random.sample(string.ascii_lowercase, 10)).encode("utf8")
    salt = bcrypt.gensalt(difficulty) # <2> difficulty를 조정함으로써 암호 생성의 난이도를 높일수 있다.
    result = bcrypt.hashpw(passwd, salt)
    return result.decode("utf8")


#for difficulty, num_iter in ((8, 600), (10, 400), (11, 400), (12, 400)):
#for difficulty, num_iter in ((8, 1400), (10, 1400), (11, 1400)):
for difficulty, num_iter in ((10, 10000), (8, 1)):
    print(f"Difficulty: {difficulty}")
    start = time.perf_counter()
    calculate_task_batch(num_iter, difficulty)
    t = time.perf_counter() - start
    print("Serial code took: {} {}s".format(num_iter, t))
    data["serial"].append((num_iter, difficulty, t))