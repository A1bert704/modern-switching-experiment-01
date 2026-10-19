# 实验一报告

姓名：胡春池  学号：2024280554  GitHub：待填写  提交编号：待填写

## 实验目的

在相同到达序列、链路容量、缓存容量和观察时长下，比较固定时隙电路交换与共享 FIFO 分组交换。重点观察固定资源预留、统计复用和分组包头开销如何影响有效载荷利用率、时延、丢失和积压。

## 原理和模型

电路模型每 tick 只服务 `tick % users` 对应的用户，空闲时隙不能借给其他用户；分组模型使用共享 FIFO，包头随记录发送，较大的分组可跨 tick 续传但不能与队首分组交错。两种模型都按未完成记录的原始 payload 预留缓存，只有记录完整交付后才释放。

仿真使用 256 个 tick，每 tick 1 ms，线路预算为 128 bit/tick，默认包头为 32 bit。结果只统计 `[0, 256)` 窗口，不追加排空时间。因此窗口末未完成记录属于积压，不属于丢失。有效载荷利用率只计完整交付的 payload，线路忙碌率还包含包头和未完成记录已经发送的部分。

本实验的比较链路是 128 kbit/s 抽象单链路。附带 PCM 示例的 32 时隙、8 bit、8000 帧/s 对应 2.048 Mbit/s，是不同的教学模型，不能直接当作同一链路速率。

## 手工推演

设 2 个用户、2 个 tick，`slot_bits=8`、`header_bits=2`，缓存足够大。tick 0 同时到达两条记录：用户 0 和用户 1 各有一条 6 bit payload；分组线速长度各为 8 bit。

预期：电路交换在 tick 0 只服务用户 0，发送 6 bit 并完成；tick 1 服务用户 1，再发送 6 bit 并完成。分组交换按共享 FIFO 先后发送两条 8 bit 记录，每个 tick 完成一条。两种方式均交付 12 bit payload、无丢失、无积压；payload 利用率为 `12/(2×8)=0.75`。电路线路忙碌率为 `12/16=0.75`，分组线路忙碌率为 `16/16=1.0`。完成时延分别为电路 1 ms、2 ms，分组也为 1 ms、2 ms。

## 实验结果

![指标比较](results/comparison_metrics.png)
![队列占用](results/queue_occupancy.png)
![PCM示例](results/pcm_frame_view.png)

| 业务 | 模式 | Payload 利用率 | 平均时延 (ms) | 最大时延 (ms) | 丢失率 | 积压 (bit) |
|---|---|---:|---:|---:|---:|---:|
| continuous | circuit | 1.000 | 2.500 | 4.000 | 0.000 | 0 |
| continuous | packet | 0.797 | 26.147 | 40.000 | 0.090 | 3712 |
| staggered_burst | circuit | 0.492 | 45.095 | 127.000 | 0.184 | 3936 |
| staggered_burst | packet | 0.750 | 1.000 | 1.000 | 0.000 | 0 |
| synchronized_burst | circuit | 0.340 | 12.707 | 24.000 | 0.000 | 1152 |
| synchronized_burst | packet | 0.328 | 15.357 | 32.000 | 0.000 | 1536 |
| light_random | circuit | 0.211 | 3.111 | 10.000 | 0.000 | 0 |
| light_random | packet | 0.211 | 1.097 | 2.000 | 0.000 | 0 |

错峰突发时，分组方式的 payload 利用率为 0.750，而电路方式为 0.492；电路方式还有 0.184 的 payload 丢失率和 3936 bit 积压。反过来，在连续业务下，电路方式交付全部 payload，利用率为 1.000；分组方式受包头占用线路预算影响，利用率降至 0.797，并产生丢失和积压。同步突发下两者也没有简单的全面胜负：电路方式 payload 利用率略高，分组方式线路忙碌率更高，但其完成时延和积压也更高。

## 自拟反例

`student_tests/test_my_case.py::test_packet_at_observation_window_end_is_backlog` 使用 1 tick 观察窗口、128 bit/tick 线路和 200 bit payload。分组加 32 bit 包头后需发送 232 bit，首 tick 只能发送 128 bit。预期是交付 0、丢失 0、积压 200 bit、线路忙碌率 1.0，且没有完成记录所以时延为 `None`。测试断言这些结果，能发现把未完成 payload 错算成丢失、积压、完整交付或零时延的问题。

## 参数扫描与分析

将包头从 32 bit 改为 64 bit，其他配置和随机种子保持不变，结果记录在 `results/extra/header_64_comparison.csv`。分组方式在连续业务中的 payload 利用率由 0.797 降至 0.664，丢失率由 0.090 升至 0.219，积压由 3712 bit 升至 3840 bit；错峰突发的利用率由 0.750 降至 0.598，并出现 0.039 的丢失率和 4032 bit 积压。同步突发也出现利用率下降、时延上升和积压增加。轻载随机场景的 payload 利用率仍为 0.211，但分组线路忙碌率增加、平均时延由 1.097 ms 升至 2.125 ms。

因此，统计复用是否有优势取决于业务形态和包头开销。突发错峰、线路有可共享空隙时，分组方式能减少固定时隙浪费；持续高负载或包头占比较大时，额外线路开销可能明显降低有效吞吐。平均时延只统计成功完成记录，不能代替积压和丢失一起分析；未完成记录不能当成丢包。本结果是有限观察窗口下的仿真，不代表无限长稳态性能，也未模拟传播、重传、误码和多跳时延。

## AI使用说明

协作过程、手算预期和测试验证记录见 [AI_LOG.md](AI_LOG.md)。电路发送逻辑按时隙选择用户并扣减剩余预算；分组发送逻辑只处理共享队首，`remaining_wire_bits` 已含包头，跨 tick 续传时不重复增加包头；指标逻辑以完整完成记录计入 payload，并检查生成、完成、丢失和积压的守恒关系。

## 参考资料

- 本实验 [README.md](README.md) 与 [materials/teacher_lab_guide.md](materials/teacher_lab_guide.md)
- 本地仿真结果：[results/comparison.json](results/comparison.json)、[results/comparison.csv](results/comparison.csv)