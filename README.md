# 微生物学做题练习

一个基于 WebView 的 Android 微生物学刷题 APP，题库涵盖 1081 道题目。

## 题型

| 题型 | 数量 | 答题方式 |
|------|:----:|------|
| 选择题 | 298 | 单选 |
| 判断题 | 376 | 正确/错误 |
| 填空题 | 200 | 输入答案，对比标准答案 |
| 名词解释 | 119 | 看题→显示答案→自评 |
| 问答题 | 88 | 看题→显示答案→自评 |

## 功能

- 按题型/章节筛选
- 随机/顺序模式
- 错题自动记录，支持错题重练
- **选题练习**：勾选特定题目精练
- 统计分析（本地 + 云端 Supabase）
- 数据后台（密码保护）
- 应用内更新提示

## 技术栈

- Android WebView（minSdk 21）
- 纯 HTML/CSS/JS 单文件应用
- Supabase 云数据库
- GitHub Pages 托管更新和后台

## 构建

需要 Java JRE 17+ 和 Android Build Tools 33.0.0。

```bash
python app/build_apk.py
```

构建脚本会自动完成：aapt2 资源编译 → ecj Java 编译 → d8 dex 转换 → APK 打包 → zipalign → 签名。

## 部署

1. Fork 本仓库
2. 修改 `admin/index.html` 中的 `PASSWORD`
3. 替换 `MainActivity.java` 中的 Supabase URL 和 Key
4. 更新 `version.json` 中的版本信息
5. GitHub Pages 设置为仓库根目录

## 许可

MIT
