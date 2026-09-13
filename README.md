# 成都求职看板（方案二）

## 这是什么
一套"你手动更新表格 → GitHub 自动生成所有人的求职网站"的项目。
- `jobs.json`：岗位池（你每天更新的数据源）
- `users.json`：学生名单（加人只改这里）
- `render.py`：自动打分+批量生成网页
- `template.html`：看板模板
- `.github/workflows/build.yml`：上传后自动构建部署

## 本地预览
```
pip install jinja2
python render.py
```
生成的网页在 `output/` 目录，双击 `zhangshibo.html` 即可看效果。

## 上传 GitHub 后自动更新
1. 在 GitHub 新建仓库（建议公开），把本文件夹所有文件传上去；
2. 仓库 Settings → Pages → Source 选 "GitHub Actions"；
3. 以后每次更新岗位，只改 `jobs.json`（或 `users.json`），push 到 main 分支；
4. GitHub 自动重新打分、生成所有人网页并上线。
5. 访问地址：`https://你的用户名.github.io/仓库名/zhangshibo.html`

## 每天怎么更新
1. 把新岗位/旧岗位发给豆包，说"合并到 jobs.json"；
2. 用豆包给的新版 `jobs.json` 内容替换仓库里的同名文件；
3. 提交 push，网站自动更新。

## 注意
- 岗位 `expire_date` 到期后自动不展示；
- 专业不相关的岗位会自动过滤（匹配分<50 不展示）；
- 加新同学只在 `users.json` 加一行，不用改其他文件。
