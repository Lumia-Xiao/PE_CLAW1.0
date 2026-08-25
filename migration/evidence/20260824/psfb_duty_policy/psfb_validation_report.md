# PSFB 专项验收报告

## 结论

PSFB 专项修复验收通过。`07_psfb_diode` 的 7 个工况全部执行成功，
原 `c02_low_input_full_load` duty boundary 已解决。该结论仅适用于 PSFB
专项，不代表全量 103 个工况的主迁移计划已完成。

## 结果

| 项目 | 修复前 | 修复后 |
| --- | ---: | ---: |
| 工况数 | 7 | 7 |
| executed | - | 7 |
| boundary failure | 1 | 0 |
| execution error | - | 0 |
| 硬件 checksum 数 | - | 1 |
| c02 状态 | boundary_failure | executed |

## Duty 口径

所有工况满足 `0 <= effective_duty <= command_duty <= 1`，且
`duty_loss = command_duty - effective_duty`。设计点 `*_nom` 字段保留，
工作点使用 operating duty policy；未使用静默 clamp。

低输入 c02 的 operating duty：

- `effective_duty = 0.780000`
- `duty_loss = 0.06156137156728873`
- `command_duty = 0.8415613715672887`
- 历史设计点 `command_duty_nom = 0.7293531886916502`

## 差异解释

c02 的状态变化归因于 operating duty policy 修复；其余工况的差异
归因于 operating duty、primary-current、waveform 和 stress refresh。
7 个工况的固定硬件 checksum 均与对应 c01 基线一致。

## 测试

- PSFB 回归和 duty policy：`13 passed`
- PSFB topology contract：`1 passed, 20 deselected`
- 编译检查：通过
- `git diff --check`：通过

## 限制

本步骤未重新运行全量 103 工况，历史 2.0/1.0 字段比较也未被 PSFB
专项证据替代。主迁移计划第 11、12 步继续保持 `in_progress`，仍需
完成全量 replay 和干净环境验收后才能关闭。

## 证据

- `psfb_replay_results.json`
- `psfb_duty_comparison.csv`
- `psfb_validation_report.json`
- `psfb_step4_regression_results.json`
