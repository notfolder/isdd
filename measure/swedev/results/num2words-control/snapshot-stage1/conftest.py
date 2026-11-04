# conftest.py
import os
import sys
from collections import deque
from hunter import trace, Q

log_stream = None
tracer = None
stack_printer = None  # <<< 在这里保存自定义的stack_printer实例

class CustomStackPrinter:
    def __init__(self, stream, prefix="CALL: ", buffer_size=100, max_depth=10):
        self.stream = stream
        self.prefix = prefix
        self.buffer_size = buffer_size
        self.buffer = deque()
        self.max_depth = max_depth
        self.exclude_fnames = ['/site-packages', '/miniconda', '>', '/usr/lib/', '/usr/local']

    def __call__(self, event):
        # 只追踪 call, 避免 return
        if event.kind != 'call':
            return

        # 构建调用链
        frames = []
        frame = event.frame
        depth = 0
        while frame and depth < self.max_depth:
            filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            function = frame.f_code.co_name

            rel_filename = os.path.relpath(filename, start=os.path.abspath(os.getcwd()))
            if any(exclude in rel_filename for exclude in self.exclude_fnames):
                frame = frame.f_back
                continue
            frames.append(f"{rel_filename}:{lineno}:{function}")
            frame = frame.f_back
            depth += 1

        if len(frames) <= 1:
            return

        call_chain = ' <= '.join(reversed(frames))
        self.buffer.append(f"{self.prefix}{call_chain}\n")

        # 达到 buffer size 刷新一次
        if len(self.buffer) >= self.buffer_size:
            self.flush()

    def flush(self):
        if self.buffer:
            self.stream.writelines(self.buffer)
            self.buffer.clear()

    def close(self):
        """在测试会话结束时调用，确保缓冲内容写入并关闭流。"""
        self.flush()
        if not self.stream.closed:
            self.stream.close()

def pytest_sessionstart(session):
    global log_stream, tracer, stack_printer
    trace_dir = os.environ.get("TRACE_DIR")
    if not trace_dir:
        print("TRACE_DIR not set, skipping tracing.")
        return

    if not os.path.isdir(trace_dir):
        print(f"{trace_dir} is not a directory, skipping tracing.")
        return

    trace_dir_abs = os.path.abspath(trace_dir)
    log_file_path = os.path.abspath('trace.log')
    print(f"[TRACE] Writing log to: {log_file_path}")

    # 行缓冲
    log_stream = open(log_file_path, 'w', buffering=1)

    # 保存到全局变量
    stack_printer = CustomStackPrinter(
        stream=log_stream, 
        prefix="CALL: ", 
        buffer_size=100, 
        max_depth=10
    )

    # 如果还想追踪返回，可以把 Q(kind='call') 改成 (Q(kind='call')|Q(kind='return'))
    tracer = trace(
        (
            Q(filename_startswith=trace_dir_abs) &
            Q(kind='call')
        ),
        action=stack_printer
    )

def pytest_sessionfinish(session, exitstatus):
    global log_stream, tracer, stack_printer
    if tracer:
        tracer.stop()
        tracer = None

    # 手动调用 stack_printer.close()
    if stack_printer:
        stack_printer.close()
        stack_printer = None

    # 保险起见，可以判断一下 log_stream 是否还在打开状态
    if log_stream and not log_stream.closed:
        log_stream.close()
    log_stream = None
