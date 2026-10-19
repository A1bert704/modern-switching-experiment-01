# AI协作记录

工具与模型：VS Code 中的 GitHub Copilot。

## 一项真实协作过程

需求与输入：按实验 README 依次补全固定时隙电路发送、共享 FIFO 分组发送和指标统计三个 TODO；要求沿用框架接口，并通过教师测试。

AI建议：电路发送先按 `tick % users` 选定唯一服务队列，再在 `slot_bits` 预算内按 FIFO 扣减剩余线速比特，完成后才移除记录。分组发送使用共享队列队首，包头已包含在 `remaining_wire_bits` 中，跨 tick 只续传余量。指标统计根据完整交付记录计算 payload 利用率和时延，对 generated、delivered、dropped 和 backlog 做守恒检查。

我的手算与测试：两用户、两 tick 的小例子中，`slot_bits=8`、`header_bits=2`，两用户在 tick 0 各到达一条 6 bit payload。预期电路方式依次在 tick 0 和 tick 1 发送两条 payload；分组方式依次发送两条各 8 bit 的线路记录。两种方式均交付 12 bit payload，payload 利用率为 0.75，且没有丢失或积压。代码修改后，`grading/test_circuit.py` 的 4 项、`grading/test_packet.py` 的 4 项、`grading/test_metrics.py` 的 3 项和 `grading/test_integration.py` 的 3 项均通过。

边界验证：自拟测试 `student_tests/test_my_case.py::test_packet_at_observation_window_end_is_backlog` 用 1 tick 窗口检查 200 bit 分组 payload。发送 128 bit 线路数据后记录仍未完成；实际结果为交付 0、丢失 0、积压 200 bit、线路忙碌率 1.0、时延为 `None`，测试通过。

参数验证：将包头从 32 bit 改为 64 bit重新运行四种业务。连续业务中分组 payload 利用率由 0.796875 降至 0.6640625，丢失率由 0.08984375 升至 0.21875；附加指标保存在 `results/extra/header_64_comparison.csv`。

修正或采纳理由：三个实现均按框架的 `Pending` 状态和仿真顺序原地更新，没有修改教师测试或框架。首次实现通过相应定向测试；之后的窗口末积压测试和包头扫描用于验证关键边界与结论适用条件。

我能解释的核心逻辑：电路方式不能让其他用户借用当前空时隙；分组方式只发送共享 FIFO 队首，记录未发完时保留 `remaining_wire_bits`，因此既不交错也不重复加包头。指标只把完整交付的记录算入 delivered，未完成记录仍占 payload 缓存并计入 backlog。