# icourse

### 如何下载:

1. 执行下面的命令

```bash
git clone https://github.com/H4ckF0rFun/Fuck-Lesson.git
```

2. 安装python3 依赖库

```bash
python3 -m pip install -r requirement.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 食用方法:

1. 先在网站上把要选的课加进收藏列表
2. 执行下面的命令

```bash
python3 ./icourse.py username password batch_id [ loop (optional)]
```

### 参数说明:

1. username : 你的账号
2. password : 你的密码
3. batch_id : 选课批次, 就是在网站刚登录进去的时候弹出的那个选课批次，一般情况下写0就行
4. loop: 指的是如果都抢到了的话，就重新登录继续再抢，一直循环 (正常情况下是 直接退出了。主要是为了防止服务器重新刷新数据，导致已经选择的课都没了)

### 具体的例子:

```bash
python3 ./icourse.py 21210000 aaaaaaaa 0 
```

---
如果你觉得有用,请给我一个小小的star ❤❤❤
