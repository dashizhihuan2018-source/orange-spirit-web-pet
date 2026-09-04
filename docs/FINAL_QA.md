# 橙子精灵 V1.0.3 最终验收

## 模型

- Blender 源文件：`assets/source/OrangeSpirit-V1.0.3.blend`
- 网页模型：`assets/models/orange-spirit-V1.0.3.glb`
- GLB 大小：2,306,564 bytes
- 三角面：41,340
- 导出材质：6
- 动作：13 个，精确为 `Idle`、`Blink`、`Listen`、`Think`、`Speak`、`Wave`、`Celebrate`、`Error`、`Sleep`、`Bounce`、`Spin`、`Shy`、`Mischief`
- 橙皮：离散油胞颗粒法线贴图，不使用平滑塑料球效果或连续虫纹
- Blink：闭合高度为睁眼高度的 28%，眼睛保持可见
- Bounce：下蹲预备、腾空收脚、手叶跟随、落地缓冲、回弹、回位
- Mischief：侧身预备、单眼眨动、双臂与双叶错拍、回位

## 网页与 MCP

- 当前网页单元测试：13/13 通过
- 真实 Chrome：模型 HTTP 200，控制台错误 0，失败请求 0
- 自然眨眼只在可见 `Idle` 状态触发，并遵守 `prefers-reduced-motion`
- 旧动作的 `finished` 事件不会打断新动作
- 六个悬浮按钮位于角色画布下方，不覆盖脚部；关闭按钮位于最右
- MCP stdio 服务和本机 `127.0.0.1` SSE 桥支持动作、说话、状态、显示、隐藏及状态查询
- 介绍页桌面与 390 × 844 手机视口均无横向溢出；设计图、手机截图、演示视频和 Skill 下载全部加载成功
- 演示录屏为 H.264、960 × 720、30fps、9.97 秒，包含 Blink、Mischief、Bounce 和文字回应
- Skill ZIP 内置独立静态预览；从临时目录解压后运行 `scripts/preview.py`，桌面/手机布局、四类图片、视频播放和 Skill 链接均通过，控制台错误与失败请求为 0

## 最终哈希

- GLB SHA-256：`aa2927a72b1eb567577ba09a47b2911079cf2eced42d7710da30a8889f57cb92`
- BLEND SHA-256：`1fe8e8732cfcc1e295a920545766654b1e3f1f97319affff76fb4d70dc3bd61a`
- 演示录屏 SHA-256：`4658ed7636272e523eaa6d4c3c4ede7a30e341c2c3fd7429aa0731510f496425`
- 手机截图 SHA-256：`c5847c37b9f7dcc6717144256e0e62d95248448384e5e26e914cd14f3bafa963`
- Skill 压缩包 SHA-256：`41c0ffd71a8757a3453f05edcaee2fa555da67c91f62ffb4d7d26159c61c32da`

## 环境边界

浏览器语音识别依赖浏览器和系统支持。自动化已验证按钮、接口、状态流转和 SpeechSynthesis 调用；真实麦克风授权及扬声器听感仍需在目标设备现场确认。

Copyright © 2026 Nankong. 保留所有权利
