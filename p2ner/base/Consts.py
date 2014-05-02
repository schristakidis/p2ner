# -*- coding: utf-8 -*-
#   Copyright 2012 Loris Corazza, Sakis Christakidis
#
#   Licensed under the Apache License, Version 2.0 (the "License");
#   you may not use this file except in compliance with the License.
#   You may obtain a copy of the License at
#
#       http://www.apache.org/licenses/LICENSE-2.0
#
#   Unless required by applicable law or agreed to in writing, software
#   distributed under the License is distributed on an "AS IS" BASIS,
#   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
#   See the License for the specific language governing permissions and
#   limitations under the License.


class MessageCodes(object):
    '''
    Message codes
    '''
    ACK=90
    CLIENT_STARTED=1
    CLIENT_STOPPED=2
    SERVER_STARTED=3
    SERVER_STOPPED=4
    BUFFER=5
    SEND_IP_LIST=6
    REQUEST_IP_LIST=7
    CLIENT_STATISTICS=8
    PUBLISH_STREAM=9
    REQUEST_STREAMS=10
    SEND_STREAM_LIST=11
    STREAM=12
    REQUEST_STREAM=13
    STREAM_ID=14
    PING=15
    PONG=16
    SERVER_LPB=17
    REMOVE_NEIGHBOURS=18
    SEEDING=19
    CHECK_CONTENTS=20
    GET_CONTENTS=21
    TOKEN=22
    REQUEST_BLOCK=23
    CONTENTS=42
    START_REMOTE=43
    CHECK_PORT=44
    SEND_IP_LIST_PRODUCER=45
    REMOVE_NEIGHBOURS_PRODUCER=46
    RETRANSMIT=47
    RTT=48
    HOLE_PUNCH=49
    PUNCH_REPLY=50
    KEEP_ALIVE=51
    GET_XPORT=52
    ECHO=53
    PECHO=54
    DPECHO=55
    LECHO=56
    CONNECT=57
    STARTH=58
    UPNP=59
    REGISTER=60
    CHATTER_MSG=61
    CHAT_MSG=62
    PUNCH_SERVER=63
    START_PUNCH=64
    ADD_NEIGH=65
    REMOVE_NEIGH=66
    ADD_PRODUCER=67
    ASK_SWAP=80
    REJECT_SWAP=81
    ACCEPT_SWAP=82
    INIT_SWAP_TABLE=83
    ASK_LOCK=84
    ANS_LOCK=85
    SEND_UPDATED_SWAP_TABLE=86
    SEND_FINAL_SWAP_TABLE=87
    UPDATE_SATELITE=88
    ADDNEIGH_RTT=99
    GET_NEIGHS=100
    RETURN_NEIGHS=101
    SUGGEST_NEW_PEER=102
    SUGGEST=103
    ASK_INIT_NEIGHS=104
    CONFIRM_NEIGH=105
    PING_SWAP=106
    ACK_UPDATE=107
    CLEAN_SATELITE=108
