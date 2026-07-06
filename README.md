# 港口 GPE 方法谱系与分布比较

交互式可视化看板，展示 39 个主要港口 2011–2023 年多种 GPE 计算口径的分布、相关性与时间趋势。

## 在线访问

部署 GitHub Pages 后，公开链接为：

**https://\<你的GitHub用户名\>.github.io/gpe-methods-dashboard/**

## 本地预览

```bash
python3 -m http.server 8765 --directory .
```

浏览器打开：<http://localhost:8765/>

## 更新数据后重新发布

在项目根目录运行：

```bash
python3 web/gpe-dashboard/build.py
cd web/gpe-dashboard
git add index.html
git commit -m "Update dashboard data"
git push
```

首次构建前需下载行政边界 GeoJSON（约 4.3 MB，已缓存则跳过）：

```bash
mkdir -p web/gpe-dashboard/data
curl -fsSL "https://geo.datav.aliyun.com/areas_v3/bound/100000_full.json" \
  -o web/gpe-dashboard/data/china_provinces.json
curl -fsSL "https://geo.datav.aliyun.com/areas_v3/bound/100000_full_city.json" \
  -o web/gpe-dashboard/data/china_cities.json
```

## 首次部署到 GitHub Pages

1. 在 GitHub 新建 **Public** 仓库，名称建议 `gpe-methods-dashboard`（不要勾选 README）。
2. 在本目录执行：

```bash
git init
git add index.html README.md .gitignore
git commit -m "Publish GPE methods dashboard"
git branch -M main
git remote add origin https://github.com/<你的用户名>/gpe-methods-dashboard.git
git push -u origin main
```

3. 打开仓库 **Settings → Pages**，Source 选 **Deploy from a branch**，Branch 选 `main` / `/ (root)`，保存。
4. 等待 1–2 分钟后访问：`https://<你的用户名>.github.io/gpe-methods-dashboard/`
