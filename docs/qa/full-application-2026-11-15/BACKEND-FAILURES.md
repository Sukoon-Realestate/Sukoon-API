# Original backend execution errors

Historical first-attempt evidence. Read [consolidated results](BACKEND-RESULTS.md) for the final status after socket-enabled and PostgreSQL reruns.

{"total": 6202, "skipped": 499, "failures": 12, "passed": 5691}

## core_apps.features.tests.test_full_cycle_http::test_complete_funded_cycle_over_http[direct]

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_full_cycle_http::test_complete_funded_cycle_over_http[marketplace]

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_full_cycle_http::test_complete_funded_cycle_over_http[group]

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_full_cycle_http::test_complete_funded_cycle_over_http[housing_request]

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_mobile_field_http::test_local_http_invoice_cancellation_and_owner_consent

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_mobile_field_http::test_local_http_rent_accounting_credit_and_deferral

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_mobile_field_http::test_local_http_maintenance_exact_cost_decision

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_mobile_field_http::test_local_http_settlement_comments

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_mobile_field_http::test_local_http_analytics_language

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_mobile_field_http::test_local_http_response_notes_reach_lease_timeline

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.features.tests.test_ongoing_cycle_http::test_paid_tenancy_month_end_extension_amendment_and_renewal_over_http

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```

## core_apps.properties.tests.test_post_visit_decision::test_complete_post_visit_journey_over_authenticated_http

```text
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/fixtures.py:577: in live_server
    server = live_server_helper.LiveServer(addr)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:56: in __init__
    self.start()
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/pytest_django/live_server_helper.py:70: in start
    raise error
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1779: in run
    self.httpd = self._create_server(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/test/testcases.py:1795: in _create_server
    return self.server_class(
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:92: in __init__
    super().__init__(*args, **kwargs)
../../Sukoon-API/backend/.venv/lib/python3.11/site-packages/django/core/servers/basehttp.py:77: in __init__
    super().__init__(*args, **kwargs)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:456: in __init__
    self.server_bind()
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/wsgiref/simple_server.py:50: in server_bind
    HTTPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/http/server.py:140: in server_bind
    socketserver.TCPServer.server_bind(self)
/opt/homebrew/Cellar/python@3.11/3.11.15_4/Frameworks/Python.framework/Versions/3.11/lib/python3.11/socketserver.py:472: in server_bind
    self.socket.bind(self.server_address)
E   PermissionError: [Errno 1] Operation not permitted
```
