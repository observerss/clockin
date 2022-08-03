# clockin server

## 安装和运行

requires python >= 3.10

```bash
pip install -r requirements.txt
```

启动服务端

```bash
cd backend
unvicorn main:app
```

## 执行任务

```python
cd backend
inv  --list
```

~~~~
Available tasks:

  add-plan      添加用户定时任务
  del-plan      删除定时任务
  add-user      添加用户(By Cookie), 并以此更新用户的连接信息
  list-plans    列表所有的定时任务
  update-user   更新用户Cookie, 并以此更新用户的连接信息
~~~~


### 添加/更新用户


```bash
inv add-user --cookie="auth.strategy=local; auth._token.local=Bearer%20eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvYmplY3QiOiJ1c2VyIiwidXNlcklkIjoiNjJiZTdhZjVmNjA5NjUyNGY5OWIwMjM4Iiwicm9sZSI6InVzZXIiLCJwbGFuIjoiZnJlZSIsImlhdCI6MTY1NjY1MDQ4NiwiZXhwIjoxNjY1MjkwNDg2fQ.gSH8-DwLy-QdjV1tnn_E7PoMANLFz_NShGTB9FA9gSY; auth._token_expiration.local=1665290486000"
```


### 添加计划

```bash
inv add-plan -u observerss -r Bot01 -s 飞书打卡
```

### 删除计划


## 打包和部署

### 做镜像、打包、加载

```bash
docker build -t clockin .
docker save clockin -o clockin.tar

gzip clockin.tar
scp clockin.tar.gz HOST:/data/clockin/
ssh HOST:PATH

cd /data/clockin
docker load -i clockin.tar
```

### 初始化数据库

```bash
mkdir db logs
alias clockinv="docker run -it --rm -v `pwd`/db:/app/db clockin inv"
clockinv init-db
clockinv add-user --cookie="auth.strategy=local; auth._token.local=Bearer%20eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJvYmplY3QiOiJ1c2VyIiwidXNlcklkIjoiNjJiZTdhZjVmNjA5NjUyNGY5OWIwMjM4Iiwicm9sZSI6InVzZXIiLCJwbGFuIjoiZnJlZSIsImlhdCI6MTY1NjY1MDQ4NiwiZXhwIjoxNjY1MjkwNDg2fQ.gSH8-DwLy-QdjV1tnn_E7PoMANLFz_NShGTB9FA9gSY; auth._token_expiration.local=1665290486000"
clockinv add-plan -u observerss -r Bot01 -s 飞书打卡
```

### 运行服务端

```bash
docker run -dit --name=clockin --restart=always -v `pwd`/db:/app/db -v `pwd`/logs:/app/logs -p 11811:8000 clockin
```