[English](README.md) | 中文

---

# 🖥️ Server-Mate | 轻量级服务器监控与 AI 运维

> 专为运行 Nginx 或 Apache 的 Linux 主机设计的双平面监控系统。

[![Version](https://img.shields.io/badge/version-1.1.2-blue.svg)]()
[![OpenClaw](https://img.shields.io/badge/OpenClaw-Skill-success.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Platform](https://img.shields.io/badge/Platform-CentOS%2FUbuntu%2FDebian-lightgrey.svg)](https://linux.org)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Web Server](https://img.shields.io/badge/Web%20Server-Nginx%2FApache-orange.svg)](https://nginx.org)

---

## 📖 项目简介

**Server-Mate** 是一个专为运行 Nginx 或 Apache 的 Linux 主机设计的轻量级服务器监控与 AI 运维工作流。

它将职责分为两个平面：
- **服务器代理**：Python 采集器，通过 `psutil` 采集主机指标和日志
- **AI 分析器**：OpenClaw 端聚合器，解释故障、回答问题、发送警报

### ✨ 核心特性

- 📊 **实时监控**：CPU、内存、磁盘、负载、网络 I/O（通过 `psutil`）
- 📝 **日志解析**：Nginx/Apache 访问日志和错误日志标准化
- 📈 **流量分析**：PV、UV、IP 统计、QPS、带宽、状态码分布
- 🕷️ **蜘蛛检测**：爬虫家族识别和流量分离
- ⚠️ **智能警报**：基于阈值的 Webhook 推送（钉钉、企业微信、ServerChan）
- 🤖 **AI 诊断**：自然语言错误解释和修复指导
- 📄 **自动报告**：日报/周报/月报 PDF，附带 AI 评论
- 🔒 **安全自动化**：可选的自动封禁和自动修复，带冷却时间和审计日志

### 🎯 使用场景

- 监控 Linux 服务器，无需替换现有栈
- 获取 AI 驱动的错误解释，而非原始日志转储
- 自动化日报/周报，包含流量趋势和安全洞察
- 检测可疑 IP、404 扫描爆发、5xx 错误峰值
- 安全的自动修复，带白名单、TTL 和审计追踪

---

## 🆕 v1.1.2 新功能

### 多站点监控

- **矩阵配置**：通过 `sites[]` 数组在同一主机上监控多个域名
- **系统指标**：专用的 `system_metrics` 部分用于宿主机全局资源（CPU、内存、磁盘、网络）
- **作用域分离**：宿主机全局指标与单站点流量聚合通过 `__host__` 作用域分离

### 加固的日志读取

- **日志轮转支持**：处理 inode 变化、文件截断和临时文件缺失
- **增量读取**：在日志轮转和重启之间稳健的状态追踪

### Guarded Automation（安全自动化）

- **干跑模式**：在启用真实操作前测试自动化策略
- **白名单感知自动封禁**：保护可信 IP 和已知蜘蛛（Googlebot、Bingbot、Baiduspider）
- **基于 TTL 的自动解封**：在可配置的 TTL 后自动解封（默认：24 小时）
- **冷却保护**：每个规则的冷却时间防止操作风暴
- **强制通知**：所有自动化操作都会记录并通知

### SQLite 审计追踪

- **`automation_actions` 表**：所有自动化事件的完整审计追踪
- **`banned_ips` 表**：追踪活跃封禁及其 TTL 和元数据

### 配置

- **`config.example.yaml`**：v1.1.2 的推荐起点，预配置多站点、system_metrics 和 Guarded Automation

---

## 🚀 快速开始

### 1. 安装

```bash
# 克隆仓库
git clone https://github.com/tankeito/server-mate.git
cd server-mate

# 安装依赖
python3 -m pip install psutil pyyaml matplotlib

# 可选：GeoIP 增强
python3 -m pip install geoip2
```

### 2. 配置

生成或编辑 `config.yaml`：

从 `1.1.2` 开始，建议优先复制 [`config.example.yaml`](config.example.yaml) 为 `config.yaml`。在 OpenClaw 中，请将 `config.yaml`、`metrics.db`、`logs/` 和 `reports/` 全部保留在当前工作目录 `./` 下。

```yaml
agent:
  host_id: web-01
  site: example.com
  timezone: Asia/Shanghai
  mode: once

logs:
  access_log: ./logs/access.log
  error_log: ./logs/error.log

storage:
  database_file: ./metrics.db
  rollup_minutes: [10, 60]

notifications:
  webhooks:
    dingtalk:
      enabled: true
      url: https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
  reports:
    report_language: zh
    report_export_dir: ./reports
    public_base_url: https://ops.example.com/reports
    daily:
      enabled: true
      push_time: "08:30"
      channels: [dingtalk]
```

### 3. 运行代理（手动测试）

```bash
# 单次采集
python3 scripts/server_agent.py --config config.yaml --once

# 查看采集的指标
python3 scripts/report_generator.py --config config.yaml daily --date 2026-03-26 --json
```

### 4. 使用 Cron 调度

```bash
crontab -e
```

添加以下内容：

```cron
# 每 10 分钟采集数据
*/10 * * * * /usr/bin/env bash -lc 'python3 ./scripts/server_agent.py --config ./config.yaml --once >> ./logs/server-mate-agent.log 2>&1'

# 每天 01:00 生成日报 PDF
0 1 * * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range daily --send >> ./logs/server-mate-report.log 2>&1'

# 每周一 01:10 生成周报 PDF
10 1 * * 1 /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range weekly --send >> ./logs/server-mate-report.log 2>&1'

# 每月 1 号 01:20 生成月报 PDF
20 1 1 * * /usr/bin/env bash -lc 'python3 ./scripts/report_generator.py --config ./config.yaml pdf --range monthly --send >> ./logs/server-mate-report.log 2>&1'
```

---

## 📋 架构设计

### 双平面设计

```
┌─────────────────────────────────────────────────────────────┐
│  服务器代理（CentOS 主机）                                   │
│  - psutil 指标（CPU、内存、磁盘、网络）                      │
│  - 日志跟踪器（Nginx/Apache 访问 + 错误）                    │
│  - JSON 事件发射器                                          │
│  - SQLite 聚合写入器                                        │
└─────────────────────────────────────────────────────────────┘
                          │
                          │ SQLite / JSON 事件
                          ▼
┌─────────────────────────────────────────────────────────────┐
│  AI 分析器（OpenClaw）                                       │
│  - 聚合与存储                                               │
│  - 自然语言查询处理器                                       │
│  - AI 错误诊断                                              │
│  - Webhook 警报（钉钉、企业微信、ServerChan）               │
│  - 安全的自动封禁/自动修复                                  │
│  - PDF 报告生成器（日报/周报/月报）                         │
└─────────────────────────────────────────────────────────────┘
```

### 组件流程

1. **代理采集** → `system_snapshot`、`access_event`、`error_event`
2. **SQLite 聚合** → 10 分钟和小时级数据桶
3. **报告生成器** → 读取聚合数据，生成 PDF/Markdown
4. **Webhook 中心** → 发送警报和报告
5. **AI 分析** → 可选的 LLM 驱动错误解释

---

## 📊 数据契约

### 核心事件类型

| 事件类型 | 用途 | 关键字段 |
|---------|------|---------|
| `system_snapshot` | 主机健康指标 | `cpu_pct`, `memory_pct`, `disk_free_bytes`, `load_1m` |
| `access_event` | 解析的访问日志 | `client_ip`, `uri`, `status`, `response_ms`, `user_agent` |
| `error_event` | 解析的错误日志 | `severity`, `component`, `category`, `fingerprint`, `message` |
| `action_event` | 审计追踪 | `action`, `target`, `reason`, `dry_run`, `result`, `ttl_seconds` |

### 指标定义

| 指标 | 定义 |
|------|------|
| **PV** | 选定窗口内的总请求数 |
| **UV** | 独立访客键（IP + user-agent 回退） |
| **IP 数** | 独立客户端 IP 数 |
| **QPS** | `request_count / window_seconds` |
| **慢请求** | `response_ms > threshold`（默认：2000ms） |
| **出站带宽** | 响应字节总和 |

---

## ⚙️ 配置参考

### `agent` 部分

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `host_id` | string | - | 警报/报告中使用的逻辑主机名 |
| `site` | string | - | 用于聚合的站点标识符 |
| `timezone` | string | `UTC` | 用于桶调度的本地时区 |
| `mode` | string | `once` | `once` 或 `daemon` |
| `poll_interval_seconds` | int | `60` | 代理循环间隔（守护进程模式） |

### `logs` 部分

| 字段 | 类型 | 说明 |
|------|------|------|
| `access_log` | string | Nginx/Apache 访问日志路径 |
| `error_log` | string | Nginx/Apache 错误日志路径 |

### `storage` 部分

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `database_file` | string | `./server_agent.sqlite3` | SQLite 数据库路径 |
| `rollup_minutes` | array | `[10, 60]` | 桶粒度 |

### `notifications.webhooks` 部分

| 渠道 | 字段 |
|------|------|
| `dingtalk` | `enabled`, `url`, `timeout_seconds`, `at_all` |
| `wecom` | `enabled`, `url`, `timeout_seconds` |
| `serverchan` | `enabled`, `sckey`, `timeout_seconds` |

### `notifications.reports` 部分

| 字段 | 类型 | 说明 |
|------|------|------|
| `report_language` | string | `zh` 或 `en` |
| `report_export_dir` | string | PDF 外部暴露目录 |
| `public_base_url` | string | 下载链接的 URL 前缀 |
| `daily.enabled` | boolean | 启用日报 |
| `daily.push_time` | string | `"08:30"` 格式 |
| `weekly.push_weekday` | int | `1-7`（1 = 周一） |
| `monthly.push_day` | int | `1-28` |

---

## 📄 报告类型

### 日报

**生成时间**：每天配置的 `push_time`

**内容**：
- 📊 过去 24 小时的 PV、UV、IP 总计
- 🔥 热门页面、IP、来源
- 🕷️ 蜘蛛流量分布
- 📈 状态码分布（2xx/3xx/4xx/5xx）
- ⚠️ 顶级错误和慢速端点
- 🤖 AI 健康评论（如启用）

### 周报

**生成时间**：每周一配置时间

**内容**：
- 📈 7 天流量趋势
- 🚫 被封禁 IP 趋势
- 🕷️ 爬虫流量模式
- ⚠️ 可疑路由集群
- 🔄 重复错误指纹
- 🤖 AI 周度总结

### 月报

**生成时间**：每月 1 号

**内容**：
- 📊 30 天流量和性能趋势
- 💾 磁盘增长分析
- 📈 带宽峰值检测
- ⚠️ 容量警告
- 🔧 修复总结
- 🤖 AI 月度审查

---

## 🚨 警报阈值

| 警报类型 | 默认阈值 | 窗口 |
|---------|---------|------|
| CPU 高 | `> 85%` | 连续 5 分钟 |
| 内存高 | `> 85%` | 连续 5 分钟 |
| 磁盘低 | `< 10%` 可用 | 即时 |
| 5xx 爆发 | `> 20` 错误 | 1 分钟 |
| 可疑 IP | `> 200` RPM | 1 分钟 |
| 404 扫描爆发 | 突然峰值 | 短窗口 |
| 慢速路由 | `> 2000ms` 平均 | 警报窗口 |

---

## 🔒 安全与自动化

### 自动封禁策略（可选）

**要求**：
- ✅ 支持可信 IP 白名单
- ✅ 滥用证据（非正常流量高峰）
- ✅ 冷却时间和每小时操作上限
- ✅ TTL（如 24 小时）
- ✅ 审计记录附带确切命令

**适用场景**：
- 单一 IP 重复突破请求速率限制
- 扫描器式 user-agent + 404 喷洒模式
- 针对管理路由的暴力破解

### 自动修复策略（保守）

**要求**：
- ✅ 重复 `502` 或上游故障证据
- ✅ 健康检查失败或辅助信号
- ✅ 每个冷却窗口一次重启尝试
- ✅ 操作后验证
- ✅ 重启失败时的升级路径

**推荐流程**：
1. 警报
2. 干跑建议
3. 对已证实故障服务的一次受控重启
4. 重新检查错误率和健康状态
5. 升级而非循环

---

## 📁 项目结构

```
server-mate/
├── SKILL.md                          # 技能定义和触发器
├── README.md                         # 英文文档
├── README_ZH.md                      # 中文文档
├── user-guide.md                     # 详细部署指南
├── agents/
│   └── openai.yaml                  # OpenAI 代理接口配置
├── references/
│   ├── architecture.md              # 系统设计和组件边界
│   ├── data-contracts.md            # 事件模式和指标定义
│   ├── ops-playbook.md              # 阈值、警报和自动化策略
│   └── sqlite-schema.md             # 数据库模式和查询模式
├── scripts/
│   ├── server_agent.py              # 主采集守护进程
│   ├── report_generator.py          # PDF/Markdown 报告生成器
│   └── webhook_center.py            # Webhook 推送服务
└── config.yaml                       # 配置文件（生成）
```

---

## 🔍 故障排查

### PDF 中中文显示为方块

**解决方案**：
```bash
# CentOS / Rocky / AlmaLinux
sudo yum install google-noto-sans-cjk-ttc-fonts

# Ubuntu / Debian
sudo apt-get update
sudo apt-get install fonts-noto-cjk

# 刷新字体缓存
fc-cache -fv
```

### Webhook 消息仅包含本地路径

**解决方案**：
1. 在配置中设置 `report_export_dir`
2. 在配置中设置 `public_base_url`
3. 通过 Nginx 或 Apache 暴露导出目录

### 报告无数据

**解决方案**：
1. 验证 `database_file` 路径
2. 确认代理正在写入聚合数据
3. 检查 `site` 和 `host_id` 与存储数据匹配

### 慢速路由或异常 IP 部分为空

**解决方案**：
- 确保最新代理版本已创建 `slow_request_rollups` 和 `suspicious_ip_rollups` 表

---

## 📞 技术支持

- **GitHub Issues**: https://github.com/tankeito/server-mate/issues
- **仓库**: https://github.com/tankeito/server-mate
- **邮箱**: tqd354@gmail.com

---

**Server-Mate** | 轻量级服务器监控与 AI 运维

**Developed by tankeito** | MIT License | 2026
