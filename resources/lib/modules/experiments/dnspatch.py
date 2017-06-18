from requests.packages.urllib3.connection import HTTPConnection

def patched_new_conn_new():
    extra_kw = {}
    if self.source_address:
        extra_kw['source_address'] = self.source_address

    if self.socket_options:
        extra_kw['socket_options'] = self.socket_options

    try:
        conn = connection.create_connection(
            (self.host, self.port), self.timeout, **extra_kw)

    except SocketTimeout as e:
        raise ConnectTimeoutError(
            self, "Connection to %s timed out. (connect timeout=%s)" %
                  (self.host, self.timeout))

    except SocketError as e:
        raise NewConnectionError(
            self, "Failed to establish a new connection: %s" % e)

    return conn

def patched_new_conn(self):
    """ Establish a socket connection and set nodelay settings on it

    :return: a new socket connection
    """
    # resolve hostname to an ip address; use your own
    # resolver here, as otherwise the system resolver will be used.
    hostname = myResolver(self.host)
    try:
        conn = socket.create_connection(
            (hostname, self.port),
            self.timeout,
            self.source_address,
        )
    except AttributeError: # Python 2.6
        conn = socket.create_connection(
            (hostname, self.port),
            self.timeout,
        )
    conn.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY,
                    self.tcp_nodelay)
    return conn

def myResolver(host, dnssrv):
    r = dns.resolver.Resolver()
    r.nameservers = dnssrv
    answers = r.query(host, 'A')

    for rdata in answers:
        return str(rdata)

HTTPConnection._new_conn = patched_new_conn