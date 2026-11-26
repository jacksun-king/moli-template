# -*- coding: utf-8 -*-
"""模力盒 · Cloudflare 一键部署

把本地 Python 服务通过 Cloudflare Tunnel 暴露为公网 HTTPS 地址。
不改动 server.py，不需要公网 IP，不需要配置防火墙。

用法：
    python deploy_cloudflare.py                     # 快速隧道：随机 trycloudflare.com 地址，零配置
    python deploy_cloudflare.py --token <TOKEN>      # 命名隧道：绑定你自己的域名（Cloudflare 后台创建隧道后拿到 token）
    python deploy_cloudflare.py --port 9000          # 指定本地端口
    python deploy_cloudflare.py --no-server          # 本地服务已在运行时用这个
    python deploy_cloudflare.py --reinstall          # 强制重新下载 cloudflared

Windows 用户也可以直接双击 deploy-cloudflare.bat。
按 Ctrl+C 停止，脚本会自动关闭它启动的本地服务和隧道。
"""
import os, re, sys, ssl, json, time, shutil, socket, tarfile, subprocess, argparse, urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
BIN_DIR = os.path.join(ROOT, 'bin')
URL_FILE = os.path.join(ROOT, 'data', 'cloudflare_url.txt')
PY = sys.executable
BASE_URL = 'https://github.com/cloudflare/cloudflared/releases/latest/download'


def info(msg):
    print('[deploy] ' + str(msg), flush=True)


def fail(msg):
    print('[deploy] 错误: ' + str(msg), flush=True)
    sys.exit(1)


def local_alive(port):
    """本地服务是否已就绪且是本项目的服务。"""
    try:
        ctx = ssl._create_unverified_context()
        with urllib.request.urlopen('http://127.0.0.1:%d/api/categories' % port, timeout=2, context=ctx) as r:
            d = json.loads(r.read().decode('utf-8'))
            return isinstance(d.get('categories'), list)
    except Exception:
        return False


def port_open(port):
    s = socket.socket(); s.settimeout(0.5)
    try:
        s.connect(('127.0.0.1', port)); return True
    except OSError:
        return False
    finally:
        s.close()


def cloudflared_name():
    system = sys.platform
    machine = os.uname().machine.lower() if hasattr(os, 'uname') else os.environ.get('PROCESSOR_ARCHITECTURE', 'AMD64').lower()
    if machine in ('x86_64', 'amd64', 'x64'):
        arch = 'amd64'
    elif machine in ('aarch64', 'arm64'):
        arch = 'arm64'
    else:
        fail('不支持的 CPU 架构: %s' % machine)
    if system.startswith('win'):
        return 'cloudflared-windows-%s.exe' % arch
    if system == 'darwin':
        return 'cloudflared-darwin-%s.tgz' % arch
    if system.startswith('linux'):
        return 'cloudflared-linux-%s' % ('arm64' if arch == 'arm64' else 'amd64')
    fail('不支持的操作系统: %s' % system)


def find_cloudflared():
    p = shutil.which('cloudflared')
    if p:
        return p
    name = cloudflared_name()
    local = os.path.join(BIN_DIR, 'cloudflared.exe' if name.endswith('.exe') else 'cloudflared')
    if os.path.isfile(local):
        return local
    return None


def download_cloudflared():
    name = cloudflared_name()
    os.makedirs(BIN_DIR, exist_ok=True)
    url = BASE_URL + '/' + name
    info('未找到 cloudflared，正在下载: ' + url)
    archive = name.endswith('.tgz')
    target = os.path.join(BIN_DIR, 'cloudflared.exe' if (archive or sys.platform.startswith('win')) else 'cloudflared')
    tmp = os.path.join(BIN_DIR, name)
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=180) as resp, open(tmp, 'wb') as f:
            total = int(resp.headers.get('Content-Length') or 0)
            got = 0
            while True:
                chunk = resp.read(1 << 18)
                if not chunk:
                    break
                f.write(chunk); got += len(chunk)
                if total:
                    print('\r[deploy] 下载进度 %d/%d KB' % (got // 1024, total // 1024), end='', flush=True)
        print('', flush=True)
        if archive:
            with tarfile.open(tmp, 'r:gz') as tf:
                member = next((m for m in tf.getmembers() if m.name.endswith('cloudflared') or m.name.endswith('cloudflared.exe')), None)
                if not member:
                    fail('压缩包中找不到 cloudflared 可执行文件')
                data = tf.extractfile(member).read()
                with open(target, 'wb') as f:
                    f.write(data)
            os.remove(tmp)
        else:
            os.replace(tmp, target)
        if not sys.platform.startswith('win'):
            os.chmod(target, 0o755)
        info('cloudflared 已就绪: ' + target)
        return target
    except Exception as e:
        fail('下载 cloudflared 失败: %s\n  可手动下载 %s 放到项目 bin/ 目录，或安装后重试。' % (e, url))


def start_server(port):
    if local_alive(port):
        info('本地服务已在运行: http://127.0.0.1:%d' % port)
        return None
    if port_open(port):
        fail('端口 %d 已被其他程序占用，但不是模力盒服务。请用 --port 换一个端口。' % port)
    env = os.environ.copy(); env['PORT'] = str(port)
    log = open(os.path.join(ROOT, 'data', 'server.log'), 'ab', buffering=0)
    proc = subprocess.Popen([PY, os.path.join(ROOT, 'server.py')], cwd=ROOT, env=env,
                            stdout=log, stderr=subprocess.STDOUT)
    for _ in range(40):
        if local_alive(port):
            info('本地服务已启动: http://127.0.0.1:%d (PID %d)' % (port, proc.pid))
            return proc
        if proc.poll() is not None:
            fail('本地服务启动失败，请查看 data/server.log')
        time.sleep(0.25)
    proc.terminate()
    fail('本地服务启动超时，请查看 data/server.log')


def run_tunnel(binary, origin, token, port):
    # 国内网络对 QUIC/UDP 常有限制，默认走 HTTP/2（TCP 443），可用性更高
    if token:
        cmd = [binary, 'tunnel', 'run', '--protocol', 'http2', '--token', token]
        info('启动命名隧道（绑定域名由 Cloudflare 后台配置）...')
    else:
        cmd = [binary, 'tunnel', '--no-autoupdate', '--protocol', 'http2', '--url', origin]
        info('启动快速隧道（零配置临时地址，HTTP/2 模式）...')
    info('命令: ' + ' '.join(cmd[:3] + ['...'] if token else cmd))
    proc = subprocess.Popen(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, encoding='utf-8', errors='replace', bufsize=1)
    pattern = re.compile(r'https://[a-z0-9-]+\.trycloudflare\.com')
    found = False
    for line in proc.stdout:
        line = line.rstrip()
        if line:
            print('  ' + line, flush=True)
        m = pattern.search(line)
        if m and not found:
            found = True
            url = m.group(0)
            os.makedirs(os.path.dirname(URL_FILE), exist_ok=True)
            with open(URL_FILE, 'w', encoding='utf-8') as f:
                f.write(url + '\n')
            print('\n' + '=' * 68, flush=True)
            print('  公网地址: ' + url, flush=True)
            print('  地址已保存到 data/cloudflare_url.txt', flush=True)
            print('  提示：快速隧道地址是临时的，进程停止后会变化。', flush=True)
            print('=' * 68 + '\n', flush=True)
    return proc, found


def main():
    ap = argparse.ArgumentParser(description='模力盒 Cloudflare 一键部署')
    ap.add_argument('--port', type=int, default=int(os.environ.get('PORT', '8765')), help='本地端口，默认 8765')
    ap.add_argument('--token', default=os.environ.get('CLOUDFLARE_TUNNEL_TOKEN', ''), help='Cloudflare 命名隧道 Token')
    ap.add_argument('--no-server', action='store_true', help='不自动启动本地服务')
    ap.add_argument('--reinstall', action='store_true', help='强制重新下载 cloudflared')
    args = ap.parse_args()

    binary = find_cloudflared()
    if not binary or args.reinstall:
        binary = download_cloudflared()

    server_proc = None
    tunnel_proc = None
    try:
        if not args.no_server:
            server_proc = start_server(args.port)
        elif not local_alive(args.port):
            fail('本地服务未运行，请先执行 python server.py')
        tunnel_proc, ok = run_tunnel(binary, 'http://127.0.0.1:%d' % args.port, args.token, args.port)
        if not ok and not args.token:
            fail('未能获取公网地址，请检查网络后重试。')
        print('服务运行中，按 Ctrl+C 停止。', flush=True)
        while tunnel_proc.poll() is None:
            time.sleep(0.5)
        info('隧道进程已退出，退出码 %d' % tunnel_proc.returncode)
    except KeyboardInterrupt:
        info('收到中断信号，正在清理进程...')
    finally:
        for p in (tunnel_proc, server_proc):
            if p and p.poll() is None:
                try:
                    p.terminate(); p.wait(timeout=5)
                except Exception:
                    p.kill()
        info('已停止，本地服务与隧道均已关闭。')


if __name__ == '__main__':
    main()
