import socket
from time import sleep

from .utils import transform_bindings
from .DNSPacket import DNSPacket
from .Record import ARecord

DEFAULT_ADDR = ('127.0.0.1',53)
DEFAULT_SLEEP = 0.01

class Server:
    """An abstract base class for other server types"""
    def __init__(self,bindings={},addr=DEFAULT_ADDR,debug=False):
        if not (hasattr(self,'create_sock') and hasattr(self,'accept') and hasattr(self,'reply')):
            raise RuntimeError('This server class doesn\'t implement necessary properties')
        self.stopped = True
        self.bindings = transform_bindings(bindings)
        self.addr = addr
        self.debug = debug

    def _create_sock(self,proto):
        sock = socket.socket(socket.AF_INET,proto)
        sock.settimeout(0.0)
        sock.bind(self.addr)
        return sock

    def start(self):
        self.stopped = False
        sock = self.create_sock()
        print('Listening on {0}:{1}'.format(self.addr[0],self.addr[1]))
        while not self.stopped:
            # Accept request
            try:
                data, addr = self.accept(sock)
            except (BlockingIOError,ConnectionResetError):
                try:
                    sleep(DEFAULT_SLEEP)
                except KeyboardInterrupt:
                    print('Shutting down...')
                    self.stopped = True
                    break
                continue
            print('Request from {0}'.format(addr))
            # Parse request
            req = DNSPacket.fromBytes(data)
            if self.debug:
                print(req)
            # Parse response
            if len(req.questions) > 0:
                answers = []
                for question in req.questions:
                    name = str(question.names)
                    if name in self.bindings:
                        answers.append(ARecord(question.names,self.bindings[name]))
                res = DNSPacket((req.id,1,req.opcode,req.authorative,req.truncated,req.recursive_desired,req.recursive_avail,0,req.rcode),req.questions,answers,[],[])
                if self.debug:
                    print(res)
                    print(data)
                    print(bytes(res))
                self.reply(sock,addr,bytes(res))

class UDPServer(Server):
    def create_sock(self):
        return self._create_sock(socket.SOCK_DGRAM)

    @staticmethod
    def accept(sock):
        return sock.recvfrom(1024)

    @staticmethod
    def reply(sock,addr,res):
        return sock.sendto(res,addr)