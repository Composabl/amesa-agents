# SkillTeacher Overview

`SkillTeacher` is the base class for ML-trained skills. A teacher defines:

- reward (`compute_reward`)
- success criteria (`compute_success_criteria`)
- termination criteria (`compute_termination`)
- action post-processing (`transform_action`)
- which sensors are used (`filtered_sensor_space`)

Use it when the policy should be learned (PPO), not hard-coded.
