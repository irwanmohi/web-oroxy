# -*- coding: utf-8 -*-
"""
    proxy.py
    ~~~~~~~~
    ⚡⚡⚡ Fast, Lightweight, Pluggable, TLS interception capable proxy server focused on
    Network monitoring, controls & Application development, testing, debugging.

    :copyright: (c) 2013-present by Abhinav Singh and contributors.
    :license: BSD, see LICENSE for more details.
"""
import selectors
import unittest
from unittest import mock

from proxy.proxy import Proxy
from proxy.http.exception.proxy_auth_failed import ProxyAuthenticationFailed
from proxy.http.handler import HttpProtocolHandler
from proxy.core.connection import TcpClientConnection
from proxy.common.utils import build_http_request


class TestHttpProxyAuthFailed(unittest.TestCase):

    @mock.patch('selectors.DefaultSelector')
    @mock.patch('socket.fromfd')
    def setUp(self,
              mock_fromfd: mock.Mock,
              mock_selector: mock.Mock) -> None:
        self.mock_fromfd = mock_fromfd
        self.mock_selector = mock_selector

        self.fileno = 10
        self._addr = ('127.0.0.1', 54382)
        self.flags = Proxy.initialize(["--basic-auth", "user:pass"])
        self._conn = mock_fromfd.return_value
        self.protocol_handler = HttpProtocolHandler(
            TcpClientConnection(self._conn, self._addr),
            flags=self.flags)
        self.protocol_handler.initialize()

    @mock.patch('proxy.http.proxy.server.TcpServerConnection')
    def test_proxy_auth_fails_without_cred(self, mock_server_conn: mock.Mock) -> None:
        self._conn.recv.return_value = build_http_request(
            b'GET', b'http://upstream.host/not-found.html',
            headers={
                b'Host': b'upstream.host'
            })
        self.mock_selector.return_value.select.side_effect = [
            [(selectors.SelectorKey(
                fileobj=self._conn,
                fd=self._conn.fileno,
                events=selectors.EVENT_READ,
                data=None), selectors.EVENT_READ)], ]

        self.protocol_handler.run_once()
        mock_server_conn.assert_not_called()
        self.assertEqual(self.protocol_handler.client.has_buffer(), True)
        self.assertEqual(
            self.protocol_handler.client.buffer[0], ProxyAuthenticationFailed.RESPONSE_PKT)
        self._conn.send.assert_not_called()

    @mock.patch('proxy.http.proxy.server.TcpServerConnection')
    def test_proxy_auth_fails_with_invalid_cred(self, mock_server_conn: mock.Mock) -> None:
        self._conn.recv.return_value = build_http_request(
            b'GET', b'http://upstream.host/not-found.html',
            headers={
                b'Host': b'upstream.host',
                b'Proxy-Authorization': b'Basic hello',
            })
        self.mock_selector.return_value.select.side_effect = [
            [(selectors.SelectorKey(
                fileobj=self._conn,
                fd=self._conn.fileno,
                events=selectors.EVENT_READ,
                data=None), selectors.EVENT_READ)], ]

        self.protocol_handler.run_once()
        mock_server_conn.assert_not_called()
        self.assertEqual(self.protocol_handler.client.has_buffer(), True)
        self.assertEqual(
            self.protocol_handler.client.buffer[0], ProxyAuthenticationFailed.RESPONSE_PKT)
        self._conn.send.assert_not_called()

    @mock.patch('proxy.http.proxy.server.TcpServerConnection')
    def test_proxy_auth_works_with_valid_cred(self, mock_server_conn: mock.Mock) -> None:
        self._conn.recv.return_value = build_http_request(
            b'GET', b'http://upstream.host/not-found.html',
            headers={
                b'Host': b'upstream.host',
                b'Proxy-Authorization': b'Basic dXNlcjpwYXNz',
            })
        self.mock_selector.return_value.select.side_effect = [
            [(selectors.SelectorKey(
                fileobj=self._conn,
                fd=self._conn.fileno,
                events=selectors.EVENT_READ,
                data=None), selectors.EVENT_READ)], ]

        self.protocol_handler.run_once()
        mock_server_conn.assert_called_once()
        self.assertEqual(self.protocol_handler.client.has_buffer(), False)

    @mock.patch('proxy.http.proxy.server.TcpServerConnection')
    def test_proxy_auth_works_with_mixed_case_basic_string(self, mock_server_conn: mock.Mock) -> None:
        self._conn.recv.return_value = build_http_request(
            b'GET', b'http://upstream.host/not-found.html',
            headers={
                b'Host': b'upstream.host',
                b'Proxy-Authorization': b'bAsIc dXNlcjpwYXNz',
            })
        self.mock_selector.return_value.select.side_effect = [
            [(selectors.SelectorKey(
                fileobj=self._conn,
                fd=self._conn.fileno,
                events=selectors.EVENT_READ,
                data=None), selectors.EVENT_READ)], ]

        self.protocol_handler.run_once()
        mock_server_conn.assert_called_once()
        self.assertEqual(self.protocol_handler.client.has_buffer(), False)
