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
async def index(request, *, page=1):
    page = int(page)
    page_size = 10
    blog_count = await Blog.findNumber('count(*)')
    page_count = blog_count // page_size + int(blog_count % page_size > 0)
    blogs = await Blog.findAll(orderBy='created_at desc', limit=((page-1)*page_size, page_size))
    blogs = [Blog(id=blog.id, user_name=blog.user_name, name=blog.name, summary=blog.summary, created_at=blog.created_at, clicked=blog.clicked) for blog in blogs]
    for blog in blogs:
        blog.comment_count = await Comment.findNumber('count(*)', 'blog_id="%s"' % blog.id)
    return {
        '__template__': 'index.html',
        'blogs': blogs,
        'user': request.__user__,
        'prev_page': (page - 1) if page > 1 else None,
        'next_page': (page + 1) if page < page_count else None
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

@get('/profile')
async def profile(request):
    if not request.__user__:
        return web.HTTPFound('/login')
    return {
        '__template__': 'profile.html',
        'user': request.__user__
        }

@get('/manage')
async def manage(request):
    return web.HTTPFound('/manage/blogs')

@get('/manage/blogs')
async def manage_blogs(request):
    return {
        '__template__': 'manage_blogs.html',
        'user': request.__user__
        }

@get('/manage/users')
async def manage_users(request):
    return {
        '__template__': 'manage_users.html',
        'user': request.__user__
        }

@get('/manage/comments')
async def manage_comments(request):
    return {
        '__template__': 'manage_comments.html',
        'user': request.__user__
        }

@get('/manage/blogs/editor')
async def create_blog(request, *, id=None):
    return {
        '__template__': 'editor.html',
        'id': id,
        'user': request.__user__
        }

@get('/blog/{id}')
async def get_blog(request, *, id):
    blog = await Blog.find(id)
    if blog:
        blog.clicked = blog.clicked + 1
        await blog.update()
    comments = await Comment.findAll('blog_id=?', [id], orderBy='created_at desc')
    for c in comments:
        c.html_content = markdown2.markdown(c.content, safe_mode=True)
    blog.html_content = markdown2.markdown(blog.content, safe_mode=True)
    return {
        '__template__': 'blog.html',
        'comments': comments,
        'blog': blog,
        'user': request.__user__
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

@post('/api/users/update')
async def api_update_user(request, *, id, email=None, name=None, passwd=None, new_passwd=None):
    if not id:
        raise Exception('user ID is required')
    if not passwd:
        raise Exception('passwd is required')
    user = await User.find(id)
    should_update = False
    if not user or user.id != request.__user__.id:
        raise Exception('permisson denied')
    sha1_passwd = '%s:%s' % (user.id, passwd)
    if user.passwd != hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest():
        raise Exception('wrong password')
    if new_passwd:
        if not _RE_SHA1.match(new_passwd):
            raise Exception('illegal passwd')
        sha1_passwd = '%s:%s' % (user.id, new_passwd)
        user.passwd = hashlib.sha1(sha1_passwd.encode('utf-8')).hexdigest()
        should_update = True
    if email and email.strip() != user.email:
        if not _RE_EMAIL.match(email):
            raise Exception('illegal email address')
        if not new_passwd:
            raise Exception('new email found but new password not found')
        user.email = email.strip()
        should_update = True
    if name and name.strip() != user.name:
        user.name = name.strip()
        should_update = True
    if should_update:
        await user.update()
    r = web.Response()
    r.set_cookie(COOKIE_NAME, user2cookie(user, 60*60*24), max_age=60*60*24, httponly=True)
    user.passwd = '******'
    r.content_type= 'application/json'
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

@post('/api/comments')
async def api_create_comments(request, *, blog_id, content):
    if not request.__user__:
        raise Exception('user not found')
    if not blog_id:
        raise Exception('blog id not found')
    comment = Comment(blog_id=blog_id, user_id=request.__user__.id, user_name=request.__user__.name, user_image='blank:about', content=content)
    await comment.save()
    comment.html_content = markdown2.markdown(comment.content, safe_mode=True)
    return comment

