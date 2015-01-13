#!/usr/bin/env python3

from sqlalchemy import *
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relation

'''
开发期间使用这里的 mysql 连接定义
使用pymysql模块驱动
'''

engine = create_engine('mysql+pymysql://root:root@127.0.0.1:3306/trf_db?charset=utf8')
DeclarativeBase = declarative_base()
metadata = DeclarativeBase.metadata
metadata.bind = engine


class CoeOption(DeclarativeBase):
    __tablename__ = 'coe_option'

    __table_args__ = {}

    option_name = Column('option_name', VARCHAR(length=255), nullable=False,primary_key=True)
    option_value = Column('option_value', VARCHAR(length=255), nullable=False)
    option_desc = Column('option_desc', VARCHAR(length=255), nullable=True)



class CoeUser(DeclarativeBase):
    __tablename__ = 'coe_user'

    __table_args__ = {}

    user_id = Column('user_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)
    username = Column('username', VARCHAR(length=32), nullable=False,unique=True)
    password = Column('password', VARCHAR(length=255), nullable=False)
    nickname = Column('nickname', VARCHAR(length=64), nullable=True)
    realname = Column('realname',VARCHAR(length=64),nullable=True)
    sex = Column('sex', INTEGER(), nullable=True)
    city = Column('city', VARCHAR(length=128), nullable=True)
    country = Column('country', VARCHAR(length=64), nullable=True)    
    province = Column('province', VARCHAR(length=64), nullable=True)
    signature = Column("signature",VARCHAR(length=512),nullable=True)
    email = Column('email', VARCHAR(length=255), nullable=False)
    headurl = Column('headurl', VARCHAR(length=255), nullable=True)
    created = Column('create_time', VARCHAR(length=19), nullable=False)
    credit = Column('credit', INTEGER(),nullable=False)
    actived = Column('actived', INTEGER(),nullable=False)
    is_ignore =  Column('is_ignore', INTEGER(),nullable=False)
    active_code = Column('active_code', VARCHAR(length=64), nullable=True)
    invite_code = Column('invite_code', VARCHAR(length=32), nullable=True)


class CoeNode(DeclarativeBase):
    __tablename__ = 'coe_node'
    __table_args__ = {}

    node_id = Column('node_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)
    node_name = Column('node_name', VARCHAR(length=32), nullable=False,unique=True)
    node_desc = Column("node_desc",VARCHAR(length=512),nullable=True)
    node_intro = Column("node_intro",VARCHAR(length=1024),nullable=True)
    created = Column('created', VARCHAR(length=19), nullable=False)
    is_top = Column('is_top', INTEGER(),nullable=False)
    is_hide = Column('is_hide', INTEGER(),nullable=False)
    topic_count = Column('topic_count', INTEGER(),nullable=False)

class CoePost(DeclarativeBase):
    __tablename__ = 'coe_post'
    __table_args__ = {}

    post_id = Column('post_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)
    node_name = Column('node_name', VARCHAR(length=32), nullable=False)
    username = Column('username', VARCHAR(length=64), nullable=False)
    topic = Column('topic', VARCHAR(length=255), nullable=False)
    content = Column('content',Text)
    tags = Column('tags', VARCHAR(length=255), nullable=True)
    imgurl = Column('imgurl', VARCHAR(length=255), nullable=True)
    created = Column('created', VARCHAR(length=19), nullable=False)
    reply_count = Column('reply_count', INTEGER(),nullable=False)
    is_ignore =  Column('is_ignore', INTEGER(),nullable=False)
    last_reply_user = Column('last_reply_user', VARCHAR(length=32), nullable=True)
    last_reply_time = Column('last_reply_time', VARCHAR(length=19), nullable=True)

class CoePostAppend(DeclarativeBase):
    __tablename__ = "coe_post_append"
    __table_args__ = {}

    append_id = Column('append_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)
    post_id = Column('post_id', INTEGER(),nullable=False)
    content = Column('content',Text)
    created = Column('created', VARCHAR(length=19), nullable=False)

class CoeReply(DeclarativeBase):
    __tablename__ = "coe_reply"
    __table_args__ = {}

    reply_id = Column('reply_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)
    post_id = Column('post_id', INTEGER(),nullable=False)
    username = Column('username', VARCHAR(length=64), nullable=False)
    content = Column('content',Text)
    is_ignore =  Column('is_ignore', INTEGER(),nullable=False)
    created = Column('created', VARCHAR(length=19), nullable=False)
  

class CoeCreditLog(DeclarativeBase):
    __tablename__ = "coe_credit_log"
    __table_args__ = {}

    log_id = Column('log_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)    
    username = Column('username', VARCHAR(length=64), nullable=False)
    op_type = Column('op_type', VARCHAR(length=64), nullable=False)
    op_desc = Column('op_desc', VARCHAR(length=512), nullable=False)
    credit_val =  Column('credit_val', INTEGER(),nullable=False)
    balance = Column('balance', INTEGER(),nullable=False)
    created = Column('created', VARCHAR(length=19), nullable=False)

class CoeInvite(DeclarativeBase):
    __tablename__ = "coe_invite"
    __table_args__ = {}

    invite_id = Column('invite_id', INTEGER(), primary_key=True,autoincrement=1,nullable=False)  
    username = Column('username', VARCHAR(length=64), nullable=False)
    invite_code = Column('invite_code', VARCHAR(length=32), nullable=False)
    invite_hit = Column('invite_hit', INTEGER(),nullable=False)
    invite_total = Column('invite_total', INTEGER(),nullable=False)
    created = Column('created', VARCHAR(length=19), nullable=False)

class CoeUserPost(DeclarativeBase):
    __tablename__ = 'coe_user_post'

    __table_args__ = {}
    username = Column('username', VARCHAR(length=32), primary_key=True,nullable=False)
    post_id = Column('post_id', INTEGER(),primary_key=True,autoincrement=False)
    is_collect =  Column('is_collect', INTEGER(),nullable=False)
    is_ignore =  Column('is_ignore', INTEGER(),nullable=False)



class CoeUserRalation(DeclarativeBase):
    __tablename__ = 'coe_user_ralation'

    __table_args__ = {}
    username = Column('username', VARCHAR(length=32), primary_key=True,nullable=False)
    target_user =  Column('target_user', VARCHAR(length=32), primary_key=True,nullable=False)
    is_follow =  Column('is_follow', INTEGER(),nullable=False)
    is_block =  Column('is_block', INTEGER(),nullable=False)

class CoeUserPostReply(DeclarativeBase):
    __tablename__ = 'coe_user_post_reply'

    __table_args__ = {}
    username = Column('username', VARCHAR(length=32),primary_key=True, nullable=False)
    reply_id = Column('reply_id', INTEGER(),primary_key=True,autoincrement=False)
    is_ignore =  Column('is_ignore', INTEGER(),nullable=False)



def build_db():
    metadata.create_all(engine,checkfirst=True)

def rebuild_db():
    metadata.drop_all(engine)
    metadata.create_all(engine,checkfirst=True)    

def init_db():
    from sqlalchemy.orm import scoped_session, sessionmaker
    db = scoped_session(sessionmaker(bind=engine, autocommit=False, autoflush=True))()


    

if __name__ == '__main__':
    action = input("is rebuild?[n]")
    if action == 'y':
        rebuild_db()
    else:
        build_db()

    action = input("init_db ?[n]")
    if action == 'y':
        init_db()    