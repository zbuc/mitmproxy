import re, shlex, os
from argparse import Action, ArgumentTypeError
import version, filt

APP_HOST = "mitm.it"
APP_PORT = 80


def _parse_hook(s):
    sep, rem = s[0], s[1:]
    parts = rem.split(sep, 2)
    if len(parts) == 2:
        patt = ".*"
        a, b = parts
    elif len(parts) == 3:
        patt, a, b = parts
    else:
        raise ArgumentTypeError("Malformed hook specifier - too few clauses: %s"%s)

    if not a:
        raise ArgumentTypeError("Empty clause: %s"%str(patt))

    if not filt.parse(patt):
        raise ArgumentTypeError("Malformed filter pattern: %s"%patt)

    return patt, a, b


def parse_replace_hook(s, from_file=False):
    """
        Returns a (pattern, regex, replacement) tuple.

        The general form for a replacement hook is as follows:

            /patt/regex/replacement

        The first character specifies the separator. Example:

            :~q:foo:bar

        If only two clauses are specified, the pattern is set to match
        universally (i.e. ".*"). Example:

            /foo/bar/

        Clauses are parsed from left to right. Extra separators are taken to be
        part of the final clause. For instance, the replacement clause below is
        "foo/bar/":

            /one/two/foo/bar/

        Checks that pattern and regex are both well-formed. Raises
        ArgumentTypeError on error.
    """
    patt, regex, replacement = _parse_hook(s)
    try:
        re.compile(regex)
    except re.error, e:
        raise ArgumentTypeError("Malformed replacement regex: %s"%str(e.message))
    if from_file:
        try:
            with open(replacement, "rb") as f:
                replacement = f.read()
        except IOError:
            raise ArgumentTypeError("Could not read replace file: %s" % replacement)
    return patt, regex, replacement


def parse_setheader(s):
    """
        Returns a (pattern, header, value) tuple.

        The general form for a replacement hook is as follows:

            /patt/header/value

        The first character specifies the separator. Example:

            :~q:foo:bar

        If only two clauses are specified, the pattern is set to match
        universally (i.e. ".*"). Example:

            /foo/bar/

        Clauses are parsed from left to right. Extra separators are taken to be
        part of the final clause. For instance, the value clause below is
        "foo/bar/":

            /one/two/foo/bar/

        Checks that pattern and regex are both well-formed. Raises
        ArgumentTypeError on error.
    """
    return _parse_hook(s)


def parse_file_argument(expanduser=False, required_dir=False, required_file=False, makedirs=False):
    """
    Returns a function that processes a path string with the options.
    """
    def _parser(path):
        if expanduser:
            path = os.path.expanduser(path)
        if required_dir and not os.path.isdir(path):
            if makedirs and not os.path.exists(path):
                os.makedirs(path)
            else:
                raise ArgumentTypeError("Directory does not exist or is not a directory: %s" % path)
        if required_file and not os.path.isfile(path):
            raise ArgumentTypeError("File does not exist os is not a file: %s" % path)
        return path
    return _parser

def raiseIfNone(func):
    """
    Function wrapper that raises an ArgumentTypeError when the return value is None.
    Usage example:
        parser.add_argument( type=raiseIfNone(utils.parse_proxy_spec), ...)

    """
    def _check(val):
        r = func(val)
        if r is None:
            raise ArgumentTypeError("Invalid value: %s" % val)
        return r
    return _check


def lazy_const(func):
    """
    Sets the result of func() as argument value if the parameter is specified.
    This makes sure that proxy.get_transparent() only gets called when the -T switch
    has been supplied as it raises an error on windows.
    """
    class StoreLazyConstAction(Action):
        def __call__(self, parser, namespace, values, option_string=None):
            setattr(namespace, self.dest, func())
    return StoreLazyConstAction


def add_common_arguments(parser):
    parser.add_argument(
        "--version",
        action='version', version=version.NAMEVERSION
    )
    parser.add_argument(
        "-b",
        action="store", type=str, dest="addr", default='',
        help="Address to bind proxy to (defaults to all interfaces)"
    )
    parser.add_argument(
        "--anticache",
        action="store_true", dest="anticache", default=False,
        help="Strip out request headers that might cause the server to return 304-not-modified."
    )
    parser.add_argument(
        "--confdir", dest="confdir", default=os.path.expanduser('~/.mitmproxy'),
        action="store", type=parse_file_argument(expanduser=True, required_dir=True, makedirs=True),
        help="Configuration directory. (~/.mitmproxy)"
    )
    parser.add_argument(
        "-e",
        action="store_true", dest="eventlog",
        help="Show event log."
    )
    parser.add_argument(
        "-n",
        action="store_true", dest="no_server",
        help="Don't start a proxy server."
    )
    parser.add_argument(
        "-p",
        action="store", type=int, dest="port", default=8080,
        help="Proxy service port."
    )
    parser.add_argument(
        "-w",
        action="store", dest="wfile", default=None,
        help="Write flows to file."
    )
    parser.add_argument(
        "-r",
        action="store", dest="rfile", default=None,
        help="Read flows from file."
    )
    parser.add_argument(
        "-s",
        action="append", type=str, dest="scripts", default=[],
        metavar='"script.py --bar"',
        help="Run a script. Surround with quotes to pass script arguments. Can be passed multiple times."
    )

    import proxy
    proxy.add_arguments(parser)

    parser.add_argument(
        "-t",
        action="store", dest="stickycookie", default=None, metavar="FILTER",
        help="Set sticky cookie filter. Matched against requests."
    )

    parser.add_argument(
        "-u",
        action="store", dest="stickyauth", default=None, metavar="FILTER",
        help="Set sticky auth filter. Matched against requests."
    )
    mgroup = parser.add_mutually_exclusive_group()
    mgroup.add_argument(
        "-v",
        action="count", dest="verbosity", default=1,
        help="Increase verbosity. Can be passed multiple times."
    )
    mgroup.add_argument(
        "-q",
        action='store_const', dest="verbosity", const=0,
        help="Quiet."
    )
    parser.add_argument(
        "-z",
        action="store_true", dest="anticomp", default=False,
        help="Try to convince servers to send us un-compressed data."
    )
    parser.add_argument(
        "--host",
        action="store_true", dest="showhost", default=False,
        help="Use the Host header to construct URLs for display."
    )

    group = parser.add_argument_group("Web App")
    group.add_argument(
        "-a",
        action="store_false", dest="app", default=True,
        help="Disable the mitmproxy web app."
    )
    group.add_argument(
        "--app-host",
        action="store", dest="app_host", default=APP_HOST, metavar="host",
        help="Domain to serve the app from. For transparent mode, use an IP when\
                a DNS entry for the app domain is not present. Default: %s"%APP_HOST

    )
    group.add_argument(
        "--app-port",
        action="store", dest="app_port", default=APP_PORT, type=int, metavar="80",
        help="Port to serve the app from."
    )
    group.add_argument(
        "--app-external",
        action="store_true", dest="app_external",
        help="Serve the app outside of the proxy."
    )
    parser.add_argument(
        "--app-readonly",
        action="store_true", dest="app_readonly",
        help="Don't allow web clients to modify files on disk (e.g. report scripts)"
    )
    # None: Generate random auth token. False: Disable Auth. str: Use as auth.
    parser.add_argument(
        "--app-auth",
        action="store", dest="app_auth", default=None,
        type=(lambda x: False if str(x).lower() == "no_auth" else x),
        help='Authentication string for the API. Use "NO_AUTH" to disable authentication.'
    )

    group = parser.add_argument_group("Client Replay")
    group.add_argument(
        "-c",
        action="store", dest="client_replay", default=None, metavar="PATH",
        help="Replay client requests from a saved file."
    )

    group = parser.add_argument_group("Server Replay")
    group.add_argument(
        "-S",
        action="store", dest="server_replay", default=None, metavar="PATH",
        help="Replay server responses from a saved file."
    )
    group.add_argument(
        "-k",
        action="store_true", dest="kill", default=False,
        help="Kill extra requests during replay."
    )
    group.add_argument(
        "--rheader",
        action="append", dest="rheaders", type=str,
        help="Request headers to be considered during replay. "
        "Can be passed multiple times."
    )
    group.add_argument(
        "--norefresh",
        action="store_false", dest="refresh_server_playback",
        help="Disable response refresh, "
        "which updates times in cookies and headers for replayed responses."
    )
    group.add_argument(
        "--no-pop",
        action="store_true", dest="nopop", default=False,
        help="Disable response pop from response flow. "
        "This makes it possible to replay same response multiple times."
    )

    group = parser.add_argument_group(
        "Replacements",
        """
            Replacements are of the form "/pattern/regex/replacement", where
            the separator can be any character. Please see the documentation
            for more information.
        """.strip()
    )
    group.add_argument(
        "--replace",
        action="append", type=parse_replace_hook, dest="replacements",
        metavar="PATTERN",
        help="Replacement pattern."
    )
    group.add_argument(
        "--replace-from-file",
        action="append", type=lambda x: parse_replace_hook(x, True), dest="replacements",
        metavar="PATH",
        help="Replacement pattern, where the replacement clause is a path to a file."
    )

    group = parser.add_argument_group(
        "Set Headers",
        """
            Header specifications are of the form "/pattern/header/value",
            where the separator can be any character. Please see the
            documentation for more information.
        """.strip()
    )
    group.add_argument(
        "--setheader",
        action="append", type=parse_setheader, dest="setheaders", default=[],
        metavar="PATTERN",
        help="Header set pattern."
    )
