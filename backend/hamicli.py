#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
A Websocket Client to Hamibot Console

需要定期更新Cookie

1. 先访问 https://hamibot.com/dashboard/robots 拿到基本信息
"""
import functools
import re
import time
from typing import List

import pyjson5
import socketio
import requests

from schemas import UserInfo, RobotInfo, ScriptInfo, InstallationInfo
from logger import logger
from utils import logs_error


URL_ROBOTS = "https://hamibot.com/dashboard/robots"
URL_WEBSOCKET = "wss://hamibot.com/socket.io/?token=x3xF4gG9oHbBnGhOE9TGgPjcDxc78DUn"


def get_user_info(cookie: str) -> UserInfo:
    """获取用户信息"""
    resp = requests.get(URL_ROBOTS, headers={"Cookie": cookie})
    m = re.compile(r"return ({.*})\((null.*)\)\)").search(resp.text)
    res = m.group(1)
    for i, val in enumerate(m.group(2).split(",")):
        res = res.replace(f':{chr(ord("a") + i)},', ":" + val + ",")
        res = res.replace(f':{chr(ord("a") + i)}}}', ":" + val + "}")
    info = pyjson5.decode(res[:-1])
    return UserInfo(**info["state"]["auth"]["user"])


class HamiCli:
    def __init__(
        self,
        cookie: str | None = None,
        user_info: UserInfo | None = None,
        fetch: bool = True,
        timeout: float = 5,
    ):
        if not cookie and not user_info:
            raise RuntimeError("should provide either `cookie` or `user_info`")

        if not user_info:
            user_info = get_user_info(cookie)

        self.user = user_info
        self.robots: List[RobotInfo] = []
        self.scripts: List[ScriptInfo] = []
        self.installations: List[InstallationInfo] = []

        self.sio = socketio.Client(reconnection=False, engineio_logger=True)

        try:
            self.connect(user_info=user_info, fetch=fetch, timeout=timeout)
        except Exception as e:
            if self.sio.connected:
                self.sio.disconnect()
            raise e

    def connect(self, user_info: UserInfo, timeout: float = 5, fetch: bool = True):
        """
        连接WebSocket

        连上后等待获取robot/script/installation信息后返回
        超时或验证失败则抛出异常RuntimeError/TimeoutError
        """
        sio = self.sio

        script_page = 1
        installation_page = 1
        ROBOT_LIST = 0
        SCRIPT_LIST = 1
        INSTALLATION_LIST = 2
        if fetch:
            successes = [False, False, False]
        else:
            successes = [False]

        @sio.on("connect_error")
        def connect_error(msg):
            logger.error(f"failed to connnet websocket: {msg}")

        @sio.on("connect")
        def connect():
            # 登录'聊天室'
            sio.emit("b:join", user_info.dict(by_alias=True))

        @sio.on("join:success")
        def join_success(msg):
            logger.info(f"{user_info.username} joined: {msg}")

            if fetch:
                # 查看自有脚本列表
                sio.emit("b:script:list", {"page": script_page})

                # 查看已安装脚本列表
                sio.emit(
                    "b:installation:list", {"page": installation_page, "hasRecently": 0}
                )

        @sio.on("join:conflict")
        def join_conflict(msg):
            sio.disconnect()
            logger.info(f"{user_info.username} joined elsewhere: {msg}")

        def join_failed(msg):
            sio.disconnect()
            logger.error(f"connect failed: {msg}")

        sio.on("join:unauthorized", join_failed)
        sio.on("join_failed", join_failed)

        @sio.on("robot:list")
        @logs_error
        def robot_list(msg):
            """
            收到robot:list消息

            该消息在连接成功后会推送
            Example::
            {
                "items": [
                    {
                        "_id": "62e213120e4a4558984af087",
                        "online": true,
                        "tags": [],
                        "version": "12",
                        "brand": "Xiaomi",
                        "model": "M2007J1SC",
                        "appVersionCode": 114,
                        "name": "Bot01",
                    }
                ]
            }
            """
            robots = []
            for item in msg["items"]:
                ri = RobotInfo(**item)
                ri.user_id = user_info.user_id
                robots.append(ri)
            self.robots = robots

            logger.info(f"found {len(msg['items'])} robots")
            successes[ROBOT_LIST] = True

        @sio.on("script:list:success")
        @logs_error
        def script_list(msg):
            """
            b:script:list的回复消息

            Example::
            {
                "items": [
                    {
                        "_id": "62e2182e0e4a4558984b73df",
                        "configuration": {
                        },
                        "obfuscate": false,
                        "useMessage": false,
                        "name": "飞书打卡",
                        "updatedAt": "2022-07-29T11:50:33.858Z",
                        "listingSlug": "73NeY",
                    }
                ],
                "total": 1,
                "pageSize": 10,
            }
            """
            for item in msg["items"]:
                si = ScriptInfo(**item)
                si.user_id = user_info.user_id
                sio.emit("b:script:pull", {"_id": si.id})
                self.scripts.append(si)

            if len(msg["items"]) == msg["pageSize"]:
                script_page += 1
                sio.emit("b:script:list", {"page": script_page})

            logger.info(f"found {len(msg['items'])} scripts")
            successes[SCRIPT_LIST] = True

        @sio.on("script:pull:success")
        @logs_error
        def script_detail(msg):
            """
            b:script:pull的回复消息

            Example::
            {
                "_id": "62e2182e0e4a4558984b73df",
                "files": [
                    {
                        "object": "file",
                        "_id": "62e2182e0e4a4558984b73e0",
                        "filename": "index.js",
                        "type": "application/javascript",
                        "size": 5991,
                        "dir": "",
                        "path": "",
                        "text": "...",
                    }
                ],
                "configuration": {},
                "name": "飞书打卡",
            }
            """
            for script_info in self.scripts:
                if script_info.id == msg["_id"]:
                    script_info.configuration = msg["configuration"]
                    script_info.files = msg["files"]
                    break

        @sio.on("installation:list:success")
        @logs_error
        def installation_list(msg):
            """
            b:installation:list的回复消息

            Example::
            {
                "items": [
                    {
                        "_id": "62e37ef9da4dcb7369c7daf4",
                        "configuration": {
                        },
                        "plan": {"_id": "62e37ef9da4dcb7369c7daf3"},
                        "hasUpdate": false,
                        "settings": {"autoUpdate": false, "autoRenew": false},
                        "slug": "XufO7",
                        "name": "钉钉自动打卡",
                        "version": "2022.07.28.540",
                        "icon": "https://usercontent.hamibot.com/avatars/mlc/22/b2/225dcc05c5c8d148215fa471d91bfeb2",
                        "useForTask": false,
                    },
                ],
                "total": 2,
                "pageSize": 10,
                "recently": [
                    {
                        "_id": "627f16a932ed68743d2514da",
                        "name": "叮咚嗨选(新农人2.0)，每天7个广告获取积分，当前积分每个7元",
                        "slug": "kAi2q",
                        "icon": "https://usercontent.hamibot.com/avatars/mlc/bc/25/bc3a6a2b9c3cbf18d7bd20ab9f905625",
                        "developer": {
                            "username": "lao8",
                            "avatarUrl": "https://usercontent.hamibot.com/avatars/uc/02/ed/024508a6d8cca9366c8f551ca25eeded",
                            "name": "老八，微信jiaming20131227",
                            "developer": true,
                        },
                        "version": "2022.08.02.10",
                    },
                ],
            }
            """
            for item in msg["items"]:
                ii = InstallationInfo(**item)
                ii.user_id = user_info.user_id
                self.installations.append(ii)

            if len(msg["items"]) == msg["pageSize"]:
                installation_page += 1
                sio.emit(
                    "b:installation:list", {"page": installation_page, "hasRecently": 0}
                )

            logger.info(f"found {len(msg['items'])} installations")
            successes[INSTALLATION_LIST] = True

        sio.connect(URL_WEBSOCKET, transports=["websocket"])

        # 等待全部列表信息返回
        start_time = time.time()
        interval = 0.008
        while sum(successes) != len(successes):
            time.sleep(interval)
            interval += min(interval, 0.5)
            if time.time() - start_time > timeout:
                raise TimeoutError(
                    f"failed to connect to websocket, timed out in {timeout} seconds"
                )

    def close(self):
        if self.sio.connected:
            self.sio.disconnect()

    def run_script(self, script_id: str, robot: RobotInfo):
        """
        运行自己的脚本

        # ["b:script:run",{"scriptId":"62e2182e0e4a4558984b73df",
        # "robots":[{"robotId":"62e213120e4a4558984af087","robotName":"Bot01","version":"12","appVersionCode":114}]}]
        """
        self.sio.emit(
            "b:script:run",
            {
                "scriptId": script_id,
                "robots": [
                    {
                        "robotId": robot.id,
                        "robotName": robot.name,
                        "version": robot.version,
                        "appVersionCode": robot.app_version_code,
                    }
                ],
            },
        )

    def run_installation(self, script_id: str, robot: RobotInfo):
        """
        运行安装的脚本

        # ["b:installation:run",{"scriptId":"62e37ef9da4dcb7369c7daf4",
        # "robots":[{"robotId":"62e213120e4a4558984af087","robotName":"Bot01","version":"12","appVersionCode":114}]}]
        """
        self.sio.emit(
            "b:installation:run",
            {
                "scriptId": script_id,
                "robots": [
                    {
                        "robotId": robot.id,
                        "robotName": robot.name,
                        "version": robot.version,
                        "appVersionCode": robot.app_version_code,
                    }
                ],
            },
        )


def test_cli():
    pass


if __name__ == "__main__":
    test_cli()
