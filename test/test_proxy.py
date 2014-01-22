from libmproxy import proxy, flow, cmdline
import tutils
import socket
from libpathod import test
from netlib import http, tcp
import mock


def test_proxy_error():
    p = proxy.ProxyError(111, "msg")
    assert str(p)


class TestServerConnection:
    def setUp(self):
        self.d = test.Daemon()

    def tearDown(self):
        self.d.shutdown()

    def test_simple(self):
        sc = proxy.ServerConnection(tutils.toptions(), "http", self.d.IFACE, self.d.port, "host.com")
        sc.connect()
        r = tutils.treq()
        r.path = "/p/200:da"
        sc.send(r)
        assert http.read_response(sc.rfile, r.method, 1000)
        assert self.d.last_log()

        r.content = flow.CONTENT_MISSING
        tutils.raises("incomplete request", sc.send, r)

        sc.terminate()

    def test_terminate_error(self):
        sc = proxy.ServerConnection(tutils.toptions(), "http", self.d.IFACE, self.d.port, "host.com")
        sc.connect()
        sc.connection = mock.Mock()
        sc.connection.flush = mock.Mock(side_effect=tcp.NetLibDisconnect)
        sc.terminate()


class TestProxyOptions:
    def p(self, *args):
        parser = tutils.MockParser()
        cmdline.add_common_arguments(parser)
        return parser.parse_args(args=args)

    def assert_err(self, err, *args):
        tutils.raises(err, self.p, *args)

    def assert_noerr(self, *args):
        p = self.p(*args)
        assert p
        return p

    def test_simple(self):
        assert self.p()

    def test_cert(self):
        self.assert_noerr("--cert", tutils.test_data.path("data/testkey.pem"))
        self.assert_err("does not exist", "--cert", "nonexistent")

    def test_confdir(self):
        with tutils.tmpdir() as confdir:
            self.assert_noerr("--confdir", confdir)

    @mock.patch("libmproxy.platform.resolver", None)
    def test_no_transparent(self):
        self.assert_err("transparent mode not supported", "-T")

    @mock.patch("libmproxy.platform.resolver")
    def test_transparent_reverse(self, o):
        self.assert_err("not allowed with argument", "-P", "http://reverse", "-T")
        self.assert_noerr("-T")
        assert o.call_count == 1
        self.assert_err("invalid value: reverse", "-P", "reverse")
        self.assert_noerr("-P", "http://localhost")

    def test_certs(self):
        with tutils.tmpdir() as confdir:
            self.assert_noerr("--client-certs", confdir)
            self.assert_err("directory does not exist", "--client-certs", "nonexistent")

    def test_auth(self):
        p = self.assert_noerr("--nonanonymous")
        assert p.authenticator

        p = self.assert_noerr("--htpasswd", tutils.test_data.path("data/htpasswd"))
        assert p.authenticator
        self.assert_err("invalid htpasswd file", "--htpasswd", tutils.test_data.path("data/htpasswd.invalid"))

        p = self.assert_noerr("--singleuser", "test:test")
        assert p.authenticator
        self.assert_err("invalid single-user specification", "--singleuser", "test")


class TestDummyServer:
    def test_simple(self):
        d = proxy.DummyServer(None)
        d.start_slave()
        d.shutdown()


class TestProxyServer:
    @tutils.SkipWindows # binding to 0.0.0.0:1 works without special permissions on Windows
    def test_err(self):
        tutils.raises("error starting proxy server", proxy.ProxyServer, tutils.toptions(), 1)

    def test_err2(self):
        tutils.raises("error starting proxy server", proxy.ProxyServer, tutils.toptions(), 80, "!")

class TestProxyFactory:
    def test_dummyserver(self):
        p = proxy.get_server(tutils.toptions("-n"))
        assert isinstance(p, proxy.DummyServer)

    def test_proxyserver(self):
        p = proxy.get_server(tutils.toptions())
        assert isinstance(p, proxy.ProxyServer)
