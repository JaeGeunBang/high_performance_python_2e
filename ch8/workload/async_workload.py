import asyncio
import aiohttp
import time
import random
import string
import uvloop
import bcrypt


def save_result_aiohttp(client_session):
    sem = asyncio.Semaphore(100)

    async def saver(result):
        nonlocal sem, client_session
        url = f"http://127.0.0.1:8080/add"
        async with sem:
            async with client_session.post(url, data=result) as response:
                return await response.json()

    return saver


async def calculate_task_aiohttp(num_iter, task_difficulty):
    tasks = []
    async with aiohttp.ClientSession() as client_session:
        saver = save_result_aiohttp(client_session)
        for i in range(num_iter):
            result = do_task(i, task_difficulty)
            task = asyncio.create_task(saver(result))  # <1> 데이터베이스에 저장시 즉시 await하지 않고, 이벤트 루프에 데이터베이스 저장요청을 넣고 함수가 끝나기 전 작업이 완료됐는지 확인함.
            tasks.append(task)
            await asyncio.sleep(0)  # <2> 이벤트 루프가 실행을 기다리는 작업을 처리할수 있도록 주 함수를 일시 중단한다. 이부분이 없다면 큐에 들어간 작업은 프로그램이 끝날때까지 실행되지 않는다.
        await asyncio.wait(tasks)  # <3> 완료되지 않은 작업을 기다린다.

def do_task(i, difficulty):
    passwd = "".join(random.sample(string.ascii_lowercase, 10)).encode("utf8")
    salt = bcrypt.gensalt(difficulty)
    result = bcrypt.hashpw(passwd, salt)
    return result.decode("utf8")

data = {
            "async": [],
            "serial": [],
            "no IO": [],
            "file IO": [],
            "batches": [],
            "async+uvloop": [],
        }

#for difficulty, num_iter in ((8, 600), (10, 1400), (11, 1400), (12, 1400)):
#for difficulty, num_iter in ((8, 1400), (10, 1400), (11, 1400)):
for difficulty, num_iter in ((10, 10000), (8, 1)):
    print(f"Difficulty: {difficulty}")
    _uvloop = uvloop.new_event_loop()
    start = time.perf_counter()
    task = calculate_task_aiohttp(num_iter, difficulty)
    _uvloop.run_until_complete(task)
    t = time.perf_counter() - start
    print("Serial code took: {} {}s".format(num_iter, t))
    data["async"].append((num_iter, difficulty, t))