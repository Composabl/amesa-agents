# AgentTeacher Overview

`AgentTeacher` is the base class for ML-trained agents. A teacher defines:

- reward (`compute_reward`)
- success criteria (`compute_success_criteria`)
- termination criteria (`compute_termination`)
- done signal combining both (`is_compute_done`)
- action post-processing (`transform_action`)
- custom policy action space (`get_custom_action_space`)
- action masking (`compute_action_mask`)
- sensor preprocessing (`transform_sensors`)
- which sensors are used (`filtered_sensor_space`)
- scenario association (`add_scenario`)

Use it when the policy should be learned (PPO), not hard-coded.
