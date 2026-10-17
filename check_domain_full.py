#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""dqquan.com 配置完整体检：注册 + DNS 各类记录 + HTTPS + 页面本体。只读。"""
import subprocess, ssl, socket, re, datetime

D = "dqquan.com"
AUTH = "@launch1.spaceship.net"


def sh(cmd, t=25):
    try:
        return subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=t).stdout.strip()
    except Exception as e:
        return "ERR:%s" % e


def dig(rtype, name, server=None):
    q = "dig +short %s %s %s" % (rtype, name, ("@" + server) if server else "")
    return [x for x in sh(q).splitlines() if x]


print("=" * 60)
print("① 注册状态（whois）")
w = sh("whois %s" % D, 40)
for k in ["Domain Name", "Registry Domain ID", "Creation Date", "Registry Expiry Date",
          "Registrar:", "Domain Status", "DNSSEC"]:
    for line in w.splitlines():
        if line.strip().lower().startswith(k.strip().lower()):
            print("   ", line.strip()[:110])

print("\n② 名称服务器（权威）")
print("    NS:", dig("NS", D, AUTH) or "（空）")

print("\n③ A 记录（apex）")
a = dig("A", D, AUTH)
print("    ", a or "（空）")
print("    期望 4 条 185.199.108~111.153 →",
      "✅ 齐" if sorted(a) == sorted(["185.199.108.153", "185.199.109.153",
                                     "185.199.110.153", "185.199.111.153"]) else "⚠️ 不齐")

print("\n④ AAAA（IPv6，可选）")
print("    ", dig("AAAA", D, AUTH) or "未配置（非必需）")

print("\n⑤ www")
print("     CNAME:", dig("CNAME", "www." + D, AUTH) or "（空）")

print("\n⑥ 邮件类记录（不收发信时留空是正常的）")
for t, n in [("MX", D), ("TXT", D), ("TXT", "_dmarc." + D), ("CAA", D)]:
    print("    %-6s %-22s %s" % (t, n, dig(t, n, AUTH) or "（空）"))

print("\n⑦ HTTPS / 跳转")
for u in ["https://dqquan.com", "http://dqquan.com", "https://www.dqquan.com"]:
    out = sh('curl -s -o /dev/null -w "%{http_code} %{redirect_url}" --max-time 15 ' + u, 25)
    print("    %-28s %s" % (u, out))

print("\n⑧ 证书")
try:
    ctx = ssl.create_default_context()
    with socket.create_connection((D, 443), timeout=15) as s:
        with ctx.wrap_socket(s, server_hostname=D) as ss:
            c = ss.getpeercert()
            sub = dict(x[0] for x in c["subject"])
            iss = dict(x[0] for x in c["issuer"])
            print("    CN=%s | 签发=%s | 到期=%s" % (sub.get("commonName"), iss.get("organizationName"), c["notAfter"]))
            print("    SAN:", ", ".join(x[1] for x in c.get("subjectAltName", []))[:90])
except Exception as e:
    print("    证书读取失败:", e)

print("\n⑨ 页面本体")
html = sh("curl -s --max-time 20 https://dqquan.com", 30)
print("    字节:", len(html))
print("    标题:", (re.search(r"<title>([^<]*)</title>", html) or [None, "?"])[1])
print("    viewport:", "✅" if "viewport" in html else "✗ 缺")
print("    外部依赖(会拖慢国内):", len(re.findall(r'(src|href)="https?://', html)), "处")
print("    favicon:", "有" if re.search(r'rel="icon"', html) else "✗ 未设置")
print("    描述 meta:", "有" if 'name="description"' in html else "✗")
print("\n⑩ 404 / robots / sitemap")
for p in ["/404.html", "/robots.txt", "/sitemap.xml", "/favicon.ico"]:
    code = sh('curl -s -o /dev/null -w "%{http_code}" --max-time 12 https://dqquan.com' + p, 20)
    print("    %-14s %s" % (p, code))
