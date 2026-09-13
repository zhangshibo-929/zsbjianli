# -*- coding: utf-8 -*-
"""
求职看板批量渲染脚本
读取 jobs.json（岗位池）+ users.json（学生池），自动按专业/城市/学历打分，
为每个学生生成独立 HTML 看板到 output/ 目录，并生成索引页 index.html。
"""
import json, os, sys, datetime
from jinja2 import Template

BASE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

TODAY = datetime.date.today().isoformat()

def load(name):
    with open(os.path.join(BASE, name), "r", encoding="utf-8") as f:
        return json.load(f)

def score_job(user, job):
    """根据学生情况给岗位打分，返回 0-100 分"""
    s = 0
    # 城市匹配 30
    if user["city"] in job["city"] or "全国各地" in job["city"]:
        s += 30
    # 专业匹配 40（明确对口）/ 20（不限专业可投但非对口）/ 0（不相关）
    majors = job.get("majors", [])
    if user["major"] in majors:
        s += 40
    elif "不限" in majors:
        s += 20
    else:
        # 相关专业关键词模糊匹配
        for m in majors:
            if m and (m in user["major"] or user["major"] in m):
                s += 30
                break
    # 学历匹配 15
    deg = job.get("degree", "")
    if "不限" in deg or user["degree"] in deg:
        s += 15
    elif "大专" in deg and user["degree"] in ("本科", "硕士"):
        s += 12
    # 学生身份偏好实习/校招 15
    if "实习" in job.get("type", "") or "秋招" in job.get("type", "") or "校招" in job.get("type", ""):
        s += 15
    return min(s, 100)

def tier(score):
    if score >= 85: return ("P1", "立即投递", "#b5652a")
    if score >= 70: return ("P2", "重点投递", "#4a6b5a")
    return ("P3", "补充投递", "#9a938a")

def main():
    jobs_data = load("jobs.json")
    users_data = load("users.json")
    all_jobs = jobs_data["jobs"]

    with open(os.path.join(BASE, "template.html"), "r", encoding="utf-8") as f:
        tpl = Template(f.read())

    today = datetime.date.today()
    index_rows = []

    for u in users_data["users"]:
        # 筛选：城市匹配 + 未过期
        matched = []
        for j in all_jobs:
            # 过期过滤
            try:
                exp = datetime.date.fromisoformat(j["expire_date"])
                if exp < today:
                    continue
            except Exception:
                pass
            # 城市过滤：严格只保留地点里明确写了学生期望城市的岗位
            if u["city"] not in j["city"]:
                continue
            # 专业相关性硬过滤：完全不相关专业的岗位直接跳过（只留对口+不限专业）
            majors = j.get("majors", [])
            if u["major"] not in majors and "不限" not in majors:
                related = False
                for m in majors:
                    if m and (m in u["major"] or u["major"] in m):
                        related = True
                        break
                if not related:
                    continue
            sc = score_job(u, j)
            if sc < 50:
                continue
            t, label, color = tier(sc)
            # 标记：相关专业对口 vs 不限专业
            majors_set = j.get("majors", [])
            is_related = (u["major"] in majors_set) or any(
                m and (m in u["major"] or u["major"] in m) for m in majors_set)
            major_group = "对口" if is_related else "不限"
            matched.append({
                "company": j["company"], "title": j["title"], "city": j["city"],
                "salary": j["salary"], "url": j["url"], "type": j["type"],
                "tags": j.get("tags", []), "score": sc, "tier": t,
                "tier_label": label, "tier_color": color,
                "major_group": major_group
            })
        matched.sort(key=lambda x: -x["score"])

        # 统计
        cities = {}
        types = {}
        for m in matched:
            cities[m["city"]] = cities.get(m["city"], 0) + 1
            types[m["type"]] = types.get(m["type"], 0) + 1
        p1 = sum(1 for m in matched if m["tier"] == "P1")
        p2 = sum(1 for m in matched if m["tier"] == "P2")
        p3 = sum(1 for m in matched if m["tier"] == "P3")

        html = tpl.render(
            name=u["name"], school=u["school"], major=u["major"],
            degree=u["degree"], graduation=u["graduation"], city=u["city"],
            skills=u.get("skills",[]), weaknesses=u.get("weaknesses", u.get("weakness",[])), tagline=u.get("tagline",""),
            update_date=TODAY, jobs=matched[:200], total=len(matched),
            t1=p1, t2=p2, t3=p3,
            city_dist=json.dumps([{"name":k,"value":v} for k,v in sorted(cities.items(),key=lambda x:-x[1])[:10]], ensure_ascii=False),
            type_dist=json.dumps([{"name":k,"value":v} for k,v in sorted(types.items(),key=lambda x:-x[1])], ensure_ascii=False),
        )
        out_path = os.path.join(OUT, u["slug"] + ".html")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(html)
        index_rows.append({"slug": u["slug"], "name": u["name"], "major": u["major"],
                           "city": u["city"], "total": len(matched), "p1": p1})
        print("OK %s -> %d jobs" % (u["name"], len(matched)))

    # 索引页
    idx = """<!DOCTYPE html><html lang="zh-CN"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>求职看板索引</title>
<style>body{font-family:-apple-system,"PingFang SC",sans-serif;background:#f4f1ea;padding:40px;color:#2b2b28}
a{display:block;background:#fff;padding:18px 22px;margin:10px 0;border-radius:10px;text-decoration:none;color:#2b2b28;box-shadow:0 1px 3px rgba(0,0,0,.05)}
a:hover{border-left:4px solid #b5652a}h1{font-size:22px}</style></head><body>
<h1>成都求职看板 · 索引</h1>
<p>数据更新：""" + TODAY + """</p>
"""
    for r in index_rows:
        idx += '<a href="{}"><b>{}</b>（{} · {}）— 匹配岗位 {} 个，P1 {}</a>'.format(
            r["slug"]+".html", r["name"], r["major"], r["city"], r["total"], r["p1"])
    idx += "</body></html>"
    with open(os.path.join(OUT, "index.html"), "w", encoding="utf-8") as f:
        f.write(idx)
    print("ALL DONE, output:", OUT)

if __name__ == "__main__":
    main()
