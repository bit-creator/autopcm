import time
import os
import asyncio

class ProgressBar:
    def __init__(self, size, size2):
        self.length = os.get_terminal_size().columns
        self.progress = 0
        self.progress2 = 0
        self.percentBuffSize = 4
        self.size = size
        self.size2 = size2
        self.charDelay = 0.2
        self.symbol = '] / '
        self.start = time.perf_counter()
        self.current = time.perf_counter()
        self.static_line = "precompiling module "
        self.static_line2 = "compiling "
        self.multiplier = 0 if self.size2 == 0 else 1
        self.name = ""
        self.path = ""
        print('')
        print('')

        
    def increment(self, name):
        self.name = name
        self.progress = self.progress + 1

    def increment2(self, path):
        self.path = path
        self.progress2 = self.progress2 + 1

    def message(self, str):
        print(self.multiplier * ("\033[A") + "\033[A" +str + (self.length - len(str)) * " ")
        print('')
        print('')

    def draw(self):
        self.current = time.perf_counter()
        fill = self.length if self.size == 0 else int((self.progress * self.length) / self.size)
        fill2 = self.length if self.size2 == 0 else int((self.progress2 * self.length) / self.size2)
        timer_str = self.get_time()
        percent_str = self.get_percent()
        percent_str2 = self.get_percent2()
        buffer_size = self.length - len(timer_str) - len(percent_str) - len(self.symbol)
        bar = self.static_line + self.name
        bar2 = self.static_line2 + self.path
        if(len(bar) > buffer_size): bar = bar[0:buffer_size]
        else: bar = bar + (buffer_size - len(bar)) * '.'
        if(len(bar2) > buffer_size): bar = bar[0:buffer_size]
        else: bar2 = bar2 + (buffer_size - len(bar2)) * '.'
        bar = "\033[30m\033[47m" + bar[:fill] + "\033[0m\033[40m" + bar[fill:] + "\033[0m"
        bar2 = "\033[30m\033[47m" + bar2[:fill2] + "\033[0m\033[40m" + bar2[fill2:] + "\033[0m"
        all_line = self.multiplier * ("\033[A") + "\033[A" + percent_str + bar + self.symbol + timer_str
        all_line2 = percent_str2 + bar2 + self.symbol + timer_str
        print(all_line)
        if self.size2 != 0: print(all_line2)

    async def launch(self):
        print('\033[?25l', end="")
        self.start = time.perf_counter()
        while(self.progress != self.size or self.progress2 != self.size2):
            self.draw()
            await asyncio.sleep(0.01)
        self.current = time.perf_counter()
        self.symbol = '] '
        self.draw()
        print('\033[?25h', end="")

    async def update_symbol(self):
        while(self.progress != self.size or self.progress2 != self.size2):
            self.symbol = '] | '
            await asyncio.sleep(self.charDelay)
            self.symbol = '] / '
            await asyncio.sleep(self.charDelay)
            self.symbol = '] - '
            await asyncio.sleep(self.charDelay)
            self.symbol = '] \ '
            await asyncio.sleep(self.charDelay)

    def get_percent(self):
        if self.progress == self.size: return "100% ["
        percent = int((self.progress / self.size) * 100)
        if percent < 10: return "  " + str(percent) + "% ["
        else: return " " + str(percent) + "% ["

    def get_percent2(self):
        if self.progress2 == self.size2: return "100% ["
        percent = int((self.progress2 / self.size2) * 100)
        if percent < 10: return "  " + str(percent) + "% ["
        else: return " " + str(percent) + "% ["

    def get_time(self):
        return 'elapsed time: ' + f'{self.current - self.start:0.1f}' + 's'
