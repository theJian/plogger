#!/usr/bin/python3
#-*- coding: utf-8 -*-

'url handlers'

import re, time, json, logging, hashlib, base64, asyncio

from coroweb import get, post

from models import User, Comment, Blog, next_id

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
        'blogs': blogs
        }

@get('/api/users')
async def api_get_users(request):
    users = await User.findAll(orderBy='created_at desc')
    print('*******************************')
    print(users)
    for u in users:
        u.passwd = '******'
    return dict(users=users)
