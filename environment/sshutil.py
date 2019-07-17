import paramiko
# 创建远程链接方法
def create_conn(host, user, passwd, port=22):
    s = paramiko.SSHClient()  #
    s.set_missing_host_key_policy(paramiko.AutoAddPolicy())  # 允许连接不在know_hosts文件中的主机。
    s.connect(hostname=host, port=port, username=user, password=passwd)
    return s


# 远程上传文件方法
def remote_upload(conn,sourceFile,targetFile):
    sftp = conn.open_sftp()
    sftp.put(sourceFile, targetFile)


# 远程执行命令方法
def remote_excu(conn, command):
    # stdin, stdout, stderr = conn.exec_command("source /etc/profile;source ~/.bashrc;"+command)
    stdin, stdout, stderr = conn.exec_command(command)
    stdin.write("Y")  # 一般来说，第一个连接，需要一个简单的交互
    result01 = stderr.read()
    result02 = stdout.read()
    try:
        result1 = result01.decode('gbk')
        result2 = result02.decode('gbk')
    except UnicodeDecodeError:
        result1 = result01.decode()
        result2 = result02.decode()

    if not result1:
        return result2.strip()
    return result1.strip()


# 根据执行信息返回结果,按行读取数据进行处理
def readline_execute(conn, command):
    stdin, stdout, stderr = conn.exec_command(command)
    result1 = stderr.readlines()
    result2 = stdout.readlines()
    if result1:
        return result1
    else:
        return result2

