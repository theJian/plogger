#!/usr/bin/python3
#-*- coding: utf-8 -*-

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio, markdown2

from aiohttp import web

from coroweb import get, post

from models import User, Comment, Blog, next_id

from config import configs

COOKIE_NAME = 'cutecutecat'
_COOKIE_KEY = configs['secret']

def have_permission(request):
    return request.__user__ and request.__user__.admin


def escaped_text(text):
    lines = map(lambda s: '<p>%s</p>' % s.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'), filter(lambda s: s.strip() != '', text.split('\n')))
    return ''.join(lines)

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

@get('/manage')
async def manage(request):
    return web.HTTPFound('/manage/blogs')

@get('/manage/blogs')
async def manage_blogs(request):
    return {
        '__template__': 'manage_blogs.html'
        }

@get('/manage/users')
async def manage_users(request):
    return {
        '__template__': 'manage_users.html'
        }

@get('/manage/comments')
async def manage_comments(request):
    return {
        '__template__': 'manage_comments.html'
        }

@get('/manage/blogs/editor')
async def create_blog(request, *, id=None):
    return {
        '__template__': 'editor.html',
        'id': id
        }

@get('/blog/{id}')
async def get_blog(request, *, id):
    blog = await Blog.find(id)
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = markdown2.markdown(c.content)
    blog.html_content = markdown2.markdown(blog.content)
    return {
        '__template__': 'blog.html',
        'comments': comments,
        'blog': blog
        }

@get('/api/users')
async def api_get_users(*, page=1, page_size=10):
    page = int(page)
    user_count = await User.findNumber('count(*)')
    users = await User.findAll(orderBy='created_at desc', limit=((page-1)*page_size, page_size))
    for u in users:
        u.passwd = '******'
    page_count = user_count // page_size + int(user_count % page_size > 0)
    return dict(page=page, page_size=page_size, page_count=page_count, user_count=user_count, users=users)

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

@get('/api/blogs/{id}')
async def api_get_blog_by_id(*, id):
    blog = await Blog.find(id)
    return blog

@get('/api/blogs')
async def api_blogs(*, page=1, page_size=10):
    page = int(page)
    blog_count = await Blog.findNumber('count(*)')
    blogs = await Blog.findAll(orderBy='created_at desc', limit=((page-1)*page_size, page_size))
    page_count = blog_count // page_size + int(blog_count % page_size > 0)
    return dict(page=page, page_size=page_size, page_count=page_count, blog_count=blog_count, blogs=blogs)

@post('/api/blogs')
async def api_create_blog(request, *, name, summary, content):
    if not have_permission(request):
        raise Exception('permission denied')
    if not name.strip():
        raise Exception('blog name can\' be empty')
    if not summary.strip():
        raise Exception('blog summary can\' be empty')
    if not content.strip():
        raise Exception('blog content can\'t be empty')
    blog = Blog(user_id=request.__user__.id, user_name=request.__user__.name, user_image=request.__user__.image, name=name.strip(), summary=summary.strip(), content=content.strip())
    await blog.save()
    return blog

@post('/api/blogs/delete')
async def api_delete_blog(request, *, id):
    if not have_permission(request):
        raise Exception('permission denied')
    if not id:
        raise Exception('blog id required')
    blog = await Blog.find(id)
    if blog:
        await blog.remove()
    return blog

@post('/api/blogs/update')
async def api_update_blog(request, *, id, name, summary, content):
    if not have_permission(request):
        raise Exception('permission denied')
    if not id:
        raise Exception('blog id required')
    if not name.strip():
        raise Exception('blog name can\'t be empty')
    if not summary.strip():
        raise Exception('blog summary can\'t be empty')
    if not content.strip():
        raise Exception('blog content can\'t be empty')
    blog = await Blog.find(id)
    if blog:
        blog.name = name.strip()
        blog.summary = summary.strip()
        blog.content = content.strip()
        await blog.update()
    return blog

# @get('/api/test/add-blogs')
# async def api_create_blog(request, *, count=100):
#     for i in range(count):
#         blog = Blog(user_id="001463818576693a6425b8db6c2418795eede6d6dd6eb02000", user_name="thejian", user_image="blank:about", name="test"+str(i), summary="It's summary", content="It's content")
#         await blog.save()
#     return 'success'
