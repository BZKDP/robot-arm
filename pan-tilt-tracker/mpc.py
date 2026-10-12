#!/usr/bin/env python
# -*- coding: utf-8 -*-
# Nadyozhnyy kanal k mini-PC (paramiko, klyuch). Bez cmd-ekranirovaniya.
#   python mpc.py run  "<cmd.exe komanda>"
#   python mpc.py ps   "<powershell skript>"      (cherez -EncodedCommand)
#   python mpc.py put  <local> <remote>
#   python mpc.py putdir <localdir> <remotedir>
#   python mpc.py get  <remote> <local>
import sys, os, base64, posixpath
import paramiko

def p(*a):
    s=" ".join(str(x) for x in a)
    enc=(sys.stdout.encoding or "utf-8")
    sys.stdout.buffer.write(s.encode(enc,"replace")+b"\n"); sys.stdout.flush()

HOST="ROBOT_HOST"; USER="your_user"
KEY=r"PATH_TO_YOUR_SSH_KEY"

def conn():
    k=paramiko.Ed25519Key.from_private_key_file(KEY)
    c=paramiko.SSHClient(); c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    c.connect(HOST, username=USER, pkey=k, timeout=15)
    return c

def run(c, cmd, timeout=600):
    i,o,e=c.exec_command(cmd, timeout=timeout)
    out=o.read().decode("utf-8","replace"); err=e.read().decode("utf-8","replace")
    rc=o.channel.recv_exit_status()
    return rc,out,err

def run_ps(c, script, timeout=600):
    b64=base64.b64encode(script.encode("utf-16-le")).decode()
    return run(c, "powershell -NoProfile -ExecutionPolicy Bypass -EncodedCommand "+b64, timeout)

def put(c, local, remote):
    sftp=c.open_sftp()
    try: sftp.mkdir(posixpath.dirname(remote.replace("\\","/")))
    except Exception: pass
    sftp.put(local, remote); sftp.close()

def putdir(c, ld, rd):
    sftp=c.open_sftp()
    rd=rd.replace("\\","/")
    def mkd(p):
        try: sftp.mkdir(p)
        except Exception: pass
    mkd(rd)
    for root,dirs,files in os.walk(ld):
        rel=os.path.relpath(root, ld).replace("\\","/")
        rr=rd if rel=="." else rd+"/"+rel
        mkd(rr)
        for f in files:
            sftp.put(os.path.join(root,f), rr+"/"+f)
            print("put", rr+"/"+f)
    sftp.close()

if __name__=="__main__":
    cmd=sys.argv[1]; c=conn()
    if cmd=="run":
        rc,out,err=run(c," ".join(sys.argv[2:])); p(out)
        if err.strip(): p("[stderr]",err)
        p("[rc]",rc)
    elif cmd=="ps":
        rc,out,err=run_ps(c," ".join(sys.argv[2:])); p(out)
        if err.strip(): p("[stderr]",err)
        p("[rc]",rc)
    elif cmd=="put":
        put(c,sys.argv[2],sys.argv[3]); p("OK put")
    elif cmd=="putdir":
        putdir(c,sys.argv[2],sys.argv[3]); p("OK putdir")
    elif cmd=="psfile":
        script=open(sys.argv[2],encoding="utf-8").read()
        rc,out,err=run_ps(c,script,timeout=int(sys.argv[3]) if len(sys.argv)>3 else 600)
        p(out)
        if err.strip(): p("[stderr]",err)
        p("[rc]",rc)
    elif cmd=="get":
        s=c.open_sftp(); s.get(sys.argv[2],sys.argv[3]); s.close(); p("OK get")
    c.close()
