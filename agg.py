import aioudp
import asyncio
import time
import sys

def log(x):
    print(time.time(), x)
    sys.stdout.flush()

async def in_or_nothing(reader, duration = 1):
    if reader == None:
        return None
    try:
        return await asyncio.wait_for(reader.read(2048), duration)
    except asyncio.TimeoutError:
        return None

async def tcp_logger(reader, writer):
    peer = writer.get_extra_info('peername')[0:2]
    port = writer.get_extra_info('sockname')[1]
    resp = await in_or_nothing(reader)
    writer.close()
    log(('tcp',(port, (resp, peer))))

class Logger(object):
    def __init__(self, loop = None):
        if loop == None:
            loop = asyncio.get_event_loop()
        self.loop = loop
        self.listeners_udp = [None]
        self.listeners_tcp = []

    async def monitor_udp(self, max_port=1024):
        for port in range(1,max_port):
            try:
                listener = await aioudp.open_local_endpoint(port=port, loop=self.loop)
            except OSError as e:
                print(e)
            self.listeners_udp.append(listener)
        while True:
            results = await asyncio.gather(*[in_or_nothing(l) for l in self.listeners_udp])
            actual_results = [x for x in enumerate(results) if x[1] != None]
            for result in actual_results:
                if result != None:
                    log(('udp', result))

    async def monitor_tcp(self, max_port=1024):
        for port in range(1,max_port):
            try:
                listener = await asyncio.start_server(tcp_logger, port=port, reuse_port=True)
                self.listeners_tcp.append(listener)
            except OSError as e:
                print(e)

if __name__ == "__main__":
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    asyncio.ensure_future(Logger(loop).monitor_udp())
    asyncio.ensure_future(Logger(loop).monitor_tcp())
    loop.run_forever()
