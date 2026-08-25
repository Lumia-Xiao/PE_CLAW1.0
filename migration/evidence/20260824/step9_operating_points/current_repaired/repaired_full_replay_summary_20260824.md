# 修复后全量 103 工况回放摘要

## 执行范围

- 目标工程：PE-Claw 1.0
- 对照输入：`C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw\design_requests`
- 覆盖：17 个设计请求矩阵、103 个工况、19 个注册拓扑对应的迁移输入
- 运行时拓扑 ID：16 个；LLC 全桥和半桥共享一个运行时族 ID
- 回放代码：修复后的 PSFB duty policy 代码

## 回放命令

```text
python scripts\validate_step9_operating_points.py --source-root C:\Users\Lumia\Documents\PE_Claw\PE_Claw260517_1_extracted\PE_Claw --output-dir Plan\active\operating_points_20260824_repaired
```

## 回放结果

| 指标 | 结果 |
| --- | ---: |
| 工况总数 | 103 |
| 成功执行 | 103 |
| 执行错误 | 0 |
| boundary failure | 0 |
| new design | 19 |
| fixed hardware refresh | 84 |
| `run_full_pipeline` | 19 |
| `run_operating_point_refresh` | 84 |

PSFB `07_psfb_diode` 的 7 个工况全部为 `executed`，包括此前失败的
`c02_low_input_full_load`；该工况已不再产生 duty boundary failure。

## 后续验证

结构化输出重新生成结果：

- PE-Claw 2.0：103/103 valid
- PE-Claw 1.0：103/103 valid
- 修复后回放快照 Schema：103/103 valid，0 invalid

字段级对比结果：

- 对比工况：103/103
- execution error：0
- boundary：0
- 差异总数：3412
- 未解释差异：0
- 所有工况 verdict：`explained_difference`

差异分类：

- `simulation_numerical_difference`：1934
- `ordering_difference`：638
- `formula_difference`：389
- `field_semantic_difference`：358
- `input_mapping_error`：93

专项回归测试：`27 passed in 13.62s`。

## 证据文件

- `operating_point_migration_validation.json`
- `operating_point_replay_matrix.csv`
- `fixed_hardware_snapshots.json`
- `structured_output_snapshots.json`
- `structured_output_validation.json`
- `..\structured_outputs_20260824_repaired\structured_output_migration_validation.json`
- `..\final_comparison_20260824_repaired\comparison_final.json`
- `..\final_comparison_20260824_repaired\comparison_final.csv`
- `..\final_comparison_20260824_repaired\unexplained_difference_ledger.md`

本次修复后全量回放已完成。主迁移计划的最终关闭仍需结合完整测试环境记录和最终验收文档统一确认。
