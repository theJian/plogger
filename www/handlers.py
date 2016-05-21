#!/usr/bin/python3
#-*- coding: utf-8 -*-

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

from aiohttp import web

from coroweb import get, post

from models import User, Comment, Blog, next_id

from config import configs

COOKIE_NAME = 'cutecutecat'
_COOKIE_KEY = configs['secret']

def user2cookie(user, max_age):
    expires = str(int(time.time() + max_age))
    s = '%s-%s-%s-%s' % (user.id, user.passwd, expires, _COOKIE_KEY)
    L = [user.id, expires, hashlib.sha1(s.encode('utf-8')).hexdigest()]
    return '-'.join(L)

async def cookie2user(cookie_str):
    if not cookie_str:
        return None
    L = cookie_str.split('-')
    uid, expires, sha1 = L
    if int(expires) < time.time():
        return None
    user = await User.find(uid)
    if not user:
        return None
    s = '%s-%s-%s-%s' % (uid, user.passwd, expires, _COOKIE_KEY)
    if sha1 != hashlib.sha1(s.encode('utf-8')).hexdigest():
        logging.info('invalid cookie')
        return None
    user.passwd = '******'
    return user

@get('/')
async def index(request):
    summary = 'Amet id magni animi in harum corporis labore. Illum aperiam ducimus sapiente distinctio vitae! Autem harum nesciunt officia aspernatur ipsam maxime, ab consequatur quibusdam soluta? Quasi quaerat beatae consequuntur odit?'
    blogs = [
        Blog(id=1, name='Article1', summary=summary, created_at=time.time()-60),
        Blog(id=2, name='Article2', summary=summary, created_at=time.time()-300),
        Blog(id=3, name='Article3', summary=summary, created_at=time.time()-3600)
        ]
    return {
        '__template__': 'blog.html',
        'blogs': blogs,
        'user': request.__user__
        }

@get('/register')
async def register(request):
    return {
        '__template__': 'register.html'
        }

@get('/login')
async def login(request):
    return {
        '__template__': 'login.html'
        }

@get('/logout')
async def logout(request):
    r = web.HTTPFound('/')
    r.set_cookie(COOKIE_NAME, '-deleted-', max_age=0, httponly=True)
    logging.info('user logged out.')
    return r

@get('/manage/blogs/create')
async def create_blog(request):
    return {
        '__template__': 'editor.html'
        }

@get('/api/users')
async def api_get_users(request):
    users = await User.findAll(orderBy='created_at desc')
    for u in users:
        u.passwd = '******'
    return dict(users=users)

_RE_EMAIL = re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)")
_RE_SHA1 = re.compile(r"^[0-9a-f]{40}")

@post('/api/users')
async def api_register_user(*, email, name, passwd):
    if not email and not name and not passwd:
        raise Exception('missing arguments for register')
    if not _RE_EMAIL.match(email):
        raise Exception('illegal email')
    if not _RE_SHA1.match(passwd):
        raise Exception('illegal passwd')
    users = await User.findAll('email=?', [email])
    if len(users) > 0:
        raise Exception('email existed')
    uid = next_id()
    sha1_passwd = '%s:%s' % (uid , passwd)
    user = User(id=uid, email=email, name=name.strip(), passwd=hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest(), image="blank:about", created_at=time.time())
    await user.save()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 60*60*24), max_age=60*60*24, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@post('/api/auth')
async def auth(*, email, passwd):
    if not email or not passwd:
        raise Exception('missing arguments for register')
    users = await User.findAll('email=?', [email])
    if len(users) == 0:
        raise Exception('wrong email address or password')
    user = users[0]
    sha1_passwd = '%s:%s' % (user.id, passwd)
    if user.passwd != hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest():
        raise Exception('wrong email address or password')
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 60*60*24), max_age=60*60*24, httponly=True)
    user.passwd = '******'
    r.content_type = 'application/json'
    r.body = json.dumps(user, ensure_ascii=False).encode('utf-8')
    return r

@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    if not request.__user__ or not request.__user__.admin:
        raise Exception('permission not allow')
    if not name.strip():
        raise Exception('blog name can\' be empty')
    if not summary.strip():
        raise Exception('blog summary can\' be empty')
    if not content.strip():
        raise Exception('blog content can\'t be empty')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog
