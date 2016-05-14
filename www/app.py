import logging; logging.basicConfig(level=logging.INFO)
import asyncio, os, json, time
from datetime import datetime
from aiohttp import web
from jinja2 import Environment, FileSystemLoader
import orm
from coroweb import add_routes, add_static
from config import configs

def init_jinja2(app, **kw):
    logging.info('init jinja2 ...')
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
    env = Environment(
            loader=FileSystemLoader(kw.get('path', path)),
            autoescape=kw.get('autoescape', True),
            block_start_string=kw.get('block_start_string', '{%'),
            block_end_string=kw.get('block_end_string', '%}'),
            variable_start_string=kw.get('variable_start_string', '{{'),
            variable_end_string=kw.get('variable_end_string', '}}'),
            auto_reload=kw.get('auto_reload', True)
            )
    filters = kw.get('filters', None)
    if filters is not None:
        for name, fn in filters.items():
            env.filters[name] = fn
    app['__templating__'] = env

async def logger_factory(app, handler):
    async def logger(request):
        logging.info('Request: %s %s' % (request.method, request.path))
        return await handler(request)
    return logger

async def response_factory(app, handler):
    async def response(request):
        logging.info('Response handler ...')
        r = await handler(request)
        if isinstance(r, web.StreamResponse):
            return r
        if isinstance(r, bytes):
            res = web.Response(body=r)
            res.content_type = 'application/octet-stream'
            return res
        if isinstance(r, str):
            res = web.Response(body=r.encode('utf-8'))
            res.content_type = 'text/html;charset=utf-8'
            return res
        if isinstance(r, dict):
            template = r.get('__template__')
            if template is None:
                res = web.Response(body=json.dumps(r, ensure_ascii=False).encode('utf-8'))
                res.content_type = 'application/json;charset=utf-8'
                return res
            else:
                res = web.Response(body=app['__templating__'].get_template(template).render(**r).encode('utf-8'))
                res.content_type = 'text/html;charset=utf-8'
                return res
        res = web.Response(body=str(r).encode('utf-8'))
        res.content_type = 'text/plain;charset=utf-8'
        return res
    return response

async def init(loop):
    await orm.create_pool(loop=loop, **configs)
    app = web.Application(loop=loop, middlewares=[
         logger_factory,
         response_factory
        ])
    init_jinja2(app)
    add_routes(app, 'handlers')
    add_static(app)
    srv = await loop.create_server(app.make_handler(), '127.0.0.1', 2333)
    logging.info('server started at http://127.0.0.1:2333...')
    return srv

loop = asyncio.get_event_loop()
loop.run_until_complete(init(loop))
loop.run_forever()
