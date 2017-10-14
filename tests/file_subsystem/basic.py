import os
import pytest
import threading as thr
from datetime import datetime
from time import sleep


TMPDIR = '/tmp'


@pytest.mark.parametrize('path', [
    'test_file1',
    '-asdads-',
    123
])
def test_create_file(request, path):
    abspath = '{}/{}'.format(TMPDIR, path)
    os.mknod(abspath)
    assert os.path.exists(abspath)

    request.addfinalizer(lambda: os.remove(abspath))


@pytest.mark.parametrize('path', [
    'test_dir',
    'another_test_dir',
    666
])
def test_create_directory(request, path):
    abspath = '{}/{}'.format(TMPDIR, path)
    os.mkdir(abspath)
    assert os.path.exists(abspath)

    request.addfinalizer(lambda: os.rmdir(abspath))


@pytest.mark.parametrize('path', [
    'test_fifo',
    'another_fifo',
    111
])
def test_fifo(request, path):
    request.addfinalizer(lambda: os.remove(abspath))

    abspath = '{}/{}'.format(TMPDIR, path)
    os.mkfifo(abspath)
    assert os.path.exists(abspath)

    def receiver(fd, event_to_wait, event_to_set):
        # event_to_wait.wait()
        line = os.read(fd, 1)
        print('Read %s' % line)
        os.close(fd)

    def sender(fd, event_to_wait, event_to_set):
        for i in range(10):
            print('Written %i' % i)
            os.write(fd, str(i))
             #event_to_set.set()

        os.close(fd)


    write_event = thr.Event()
    read_event = thr.Event()

    fout = os.open(abspath, os.O_RDONLY | os.O_NONBLOCK)
    fin = os.open(abspath, os.O_WRONLY | os.O_NONBLOCK)

    write_thr = thr.Thread(target=sender, args=(fin, read_event, write_event))
    read_thr = thr.Thread(target=receiver, args=(fout, write_event, read_event))

    write_thr.start()
    read_thr.start()

    write_thr.join()
    read_thr.join()

