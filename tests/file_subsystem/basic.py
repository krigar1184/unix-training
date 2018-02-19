import os
import sys
import socket
import pytest
import multiprocessing as mp
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
@pytest.mark.parametrize('data', [
    'input',
    1,
    'pewpew'
])
def test_fifo(request, path, data):
    request.addfinalizer(lambda: os.remove(abspath))

    abspath = '{}/{}'.format(TMPDIR, path)
    os.mkfifo(abspath)
    assert os.path.exists(abspath)

    def writer():
        fd = open(abspath, 'w')
        fd.write(str(data))
        fd.close()

    def reader():
        fd = open(abspath, 'r')
        assert fd.read() == str(data)

    writer_proc = mp.Process(target=writer)
    reader_proc = mp.Process(target=reader)
    reader_proc.daemon = True
    reader_proc.start()
    writer_proc.start()
    writer_proc.join()
    reader_proc.join()


@pytest.mark.parametrize(('filepath', 'linkpath'), [
    ('file', 'link')
])
def test_hardlink(request, filepath, linkpath):
    request.addfinalizer(lambda: os.remove(filepath))

    filepath = '{}/{}'.format(TMPDIR, filepath)
    linkpath = '{}/{}'.format(TMPDIR, linkpath)

    os.mknod(filepath)

    with open(filepath, 'w') as fd:
        fd.write('content')

    os.link(src=filepath, dst=linkpath)

    assert os.path.exists(linkpath)

    with open(linkpath, 'r') as fd:
        assert fd.read() == 'content'

    os.unlink(linkpath)
    assert not os.path.exists(linkpath)
    assert os.path.exists(filepath)


@pytest.mark.parametrize(('filepath', 'linkpath'), [
    ('file', 'link')
])
def test_symlink(request, filepath, linkpath):
    request.addfinalizer(lambda: os.unlink(filepath))

    filepath = '{}/{}'.format(TMPDIR, filepath)
    linkpath = '{}/{}'.format(TMPDIR, linkpath)

    os.mknod(filepath)

    with open(filepath, 'w') as fd:
        fd.write('content')

    os.symlink(src=filepath, dst=linkpath)

    assert os.path.exists(linkpath)

    with open(linkpath, 'r') as fd:
        assert fd.read() == 'content'

    os.unlink(linkpath)

    assert not os.path.exists(linkpath)
    assert os.path.exists(filepath)


@pytest.mark.parametrize('data', [
    b'content'
])
def test_inet_socket(request, data):
    def server():
        sock = socket.socket()

        try:
            sock.bind(('127.0.0.1', 14900))
        except OSError:
            print('Address already in use\n')
            sock.close()
            return

        sock.listen(10)
        conn, addr = sock.accept()
        print('Listening on local port 14900...\n')
        request_data = conn.recv(len(data))
        assert request_data == data
        print('Accepted connection from {}, data received: {}\n'.format(
            addr,
            request_data
        ))
        sock.close()

    def client():
        sock = socket.socket()

        try:
            sock.connect(('127.0.0.1', 14900))
            print('Connected to 127.0.0.1\n')
        except ConnectionRefusedError:
            print('Connection refused')
            sock.close()
            return

        sock.send(data)
        sock.close()

    server_proc = mp.Process(target=server)
    client_proc = mp.Process(target=client)

    server_proc.start()
    sleep(1)
    client_proc.start()
    client_proc.join()
    server_proc.join()
