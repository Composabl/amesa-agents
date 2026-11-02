# AgentTeacher Overview

`AgentTeacher` is the base class for ML-trained agents. A teacher defines:

- reward (`compute_reward`)
- success criteria (`compute_success_criteria`)
- termination criteria (`compute_termination`)
- curriculum thresholds for advancing scenarios (`compute_scenario_advancement`)
- per-episode state reset (`reset`)
- legacy combined done signal (`is_compute_done`, not called by the V2 trainer)
- action post-processing (`transform_action`)
- custom policy action space (`get_custom_action_space`)
- action masking (`compute_action_mask`)
- sensor preprocessing (`transform_sensors`)
- which sensors are used (`filtered_sensor_space`)
- scenario association (`add_scenario`)

Import: `from amesa_core import AgentTeacher` (defined in
`amesa_core/orchestration/agent/agent_teacher.py`). All hooks except `add_scenario` are `async`.

Use it when the policy should be learned (PPO), not hard-coded.

A teacher published as code can also receive UI guidance: Succeed clauses replace
`compute_success_criteria`, Terminate clauses replace `compute_termination`, and other goal clauses
replace `compute_reward`; hooks without guidance keep the code
(`amesa_core/orchestration/agent/guidance_overrides.py`).
