import engineio
import socketio

sio = socketio.Client(logger=True, engineio_logger=True)


@sio.on("*")
def catch_all(*args, **kwargs):
    print("catch_all", args, kwargs)


@sio.on("join:success")
def join_success(data):
    print("success", data)


sio.connect(
    "wss://hamibot.com/socket.io/?token=x3xF4gG9oHbBnGhOE9TGgPjcDxc78DUn",
    transports=["websocket"],
)

sio.emit(
    "b:join",
    {
        "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvYmplY3QiOiJ1c2VyIiwidXNlcklkIjoiNjJiZTdhZjVmNjA5NjUyNGY5OWIwMjM4Iiwicm9sZSI6InVzZXIiLCJwbGFuIjoiZnJlZSIsImlhdCI6MTY1NjY1MDQ4NiwiZXhwIjoxNjY1MjkwNDg2fQ.gSH8-DwLy-QdjV1tnn_E7PoMANLFz_NShGTB9FA9gSY",
        "userId": "62be7af5f6096524f99b0238",
        "username": "observerss",
        "email": "jingchaohu@gmail.com",
        "avatarUrl": "https://avatars.githubusercontent.com/u/478194?v=4",
        "name": "Jingchao Hu",
        "balance": 10,
        "role": "user",
        "plan": "free",
        "referralCode": "ctfa",
        "referralCount": 0,
    },
)

sio.wait()
