

class TinyApi():
    def __init__(self, name, version):
        self.name = name
        self.version = version
        self.routes = {}
        self.middlewares = []
        self.websocket = None
        self.request = None
        self.response = None
        self._app = None
        self._loop = None
        self._server = None

    def __call__(self, environ, start_response):
        self.request = Request(environ)
        self.response = Response(start_response)
        self._app = self._loop.create_task(self._handle_request())
        return self.response

    def _add_route(self, method, path, handler):
        if path not in self.routes:
            self.routes[path] = {}
        self.routes[path][method] = handler

    # def _add_middleware(self, middleware):
    #     self.middlewares.append(middleware)

    # def _add_websocket(self, websocket):
    #     self.websocket = websocket

    def _run(self, host, port, loop):
        self._loop = loop
        self._server = loop.create_server(self, host, port)
        loop.run_until_complete(self._server)
        loop.run_forever()

    async def _handle_request(self):
        path = self.request.path
        method = self.request.method
        if path in self.routes:
            if method in self.routes[path]:
                handler = self.routes[path][method]
                for middleware in self.middlewares:
                    await middleware(self.request, self.response)
                await handler(self.request, self.response)
            else:
                self.response.status = 405
                self.response.body = b"Method Not Allowed"
        else:
            self.response.status = 404
            self.response.body = b"Not Found"
        if self.websocket:
            await self.websocket(self.request, self.response)
        self._app.cancel()
        self._loop.stop()
        self._server.close()
        await self._server.wait_closed()

    def route(self, path, method):
        def decorator(handler):
            self._add_route(method, path, handler)
            return handler
        return decorator

    def middleware(self, middleware):
        self._add_middleware(middleware)
        return middleware

    # def websocket(self, websocket):
    #     self._add_websocket(websocket)
    #     return websocket

    def run(self, host="", port=8000, loop=None):
        if loop is None:
            loop = asyncio.get_event_loop()
        self._run(host, port, loop)
        
