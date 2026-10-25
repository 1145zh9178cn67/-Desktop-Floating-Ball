# -*- coding: utf-8 -*-
"""Cloudflare Workers AI 一键配置脚本（用户手动运行）
读取本机 wrangler 的 OAuth refresh_token，刷新后写入悬浮球配置。
所有密钥仅在本机处理，不经过任何第三方。
"""
import json, os, sys, time, requests

TOML = os.path.expanduser(r"~\.wrangler\config\default.toml")
CFG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "ball_config.json")
CLIENT_ID = "54d11594-84e4-41aa-b438-e81b8fa78ee7"
ACCOUNT_ID = "86f663b79381317187df1b99613ce695"

# 1) 读取 wrangler 的 refresh_token
if not os.path.exists(TOML):
    sys.exit("未找到 %s，请先运行 npx wrangler login 授权" % TOML)
rt = ""
for line in open(TOML, encoding="utf-8"):
    if line.startswith("refresh_token"):
        rt = line.split("=", 1)[1].strip().strip('"')
        break
if not rt:
    sys.exit("default.toml 里没有 refresh_token，请重新运行 npx wrangler login")
print("找到 refresh_token，正在刷新...")

# 2) 刷新
r = requests.post("https://dash.cloudflare.com/oauth2/token",
                  data={"grant_type": "refresh_token", "refresh_token": rt,
                        "client_id": CLIENT_ID}, timeout=30)
d = r.json()
if "access_token" not in d:
    sys.exit("刷新失败：%s\n请重新运行 npx wrangler login" % r.text[:200])
new_rt = d.get("refresh_token", rt)
at = d["access_token"]
print("刷新成功，access_token 有效期 %s 秒" % d.get("expires_in"))

# 3) 验证 Workers AI 可用
base = "https://api.cloudflare.com/client/v4/accounts/%s/ai/v1" % ACCOUNT_ID
H = {"Authorization": "Bearer " + at, "Content-Type": "application/json"}
r = requests.post(base + "/chat/completions", headers=H,
                  json={"model": "@cf/zai-org/glm-4.7-flash",
                        "messages": [{"role": "user", "content": "reply: OK"}],
                        "max_tokens": 10}, timeout=60)
print("对话模型测试:", r.status_code, r.text[:100].replace("\n", " "))
if r.status_code != 200:
    print("提示：如果是 403，说明该模型已改为付费档，可换免费模型（见悬浮球 AI 设置备注）")

# 4) 写入悬浮球配置
cfg = {}
if os.path.exists(CFG_PATH):
    cfg = json.load(open(CFG_PATH, encoding="utf-8"))
cfg["api_base"] = base
cfg["chat_model"] = "@cf/zai-org/glm-4.7-flash"
cfg["vision_model"] = "@cf/google/gemma-4-26b-a4b-it"
cfg["api_key"] = ""
cfg["cf_refresh_token"] = new_rt
json.dump(cfg, open(CFG_PATH, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
print("悬浮球配置已写入：%s" % CFG_PATH)

# 5) 回写 wrangler toml（保持 wrangler 正常）
lines = []
for line in open(TOML, encoding="utf-8"):
    s = line.strip()
    if s.startswith("oauth_token"):
        lines.append('oauth_token = "%s"\n' % at)
    elif s.startswith("expiration_time"):
        lines.append('expiration_time = "%s"\n' % time.strftime(
            "%Y-%m-%dT%H:%M:%S.000Z",
            time.gmtime(time.time() + int(d.get("expires_in", 3600)))))
    elif s.startswith("refresh_token"):
        lines.append('refresh_token = "%s"\n' % new_rt)
    else:
        lines.append(line)
open(TOML, "w", encoding="utf-8").write("".join(lines))
print("wrangler 配置已更新")
print("\n全部完成！重启悬浮球即可使用 Cloudflare Workers AI。")
