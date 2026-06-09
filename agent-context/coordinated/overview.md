# Coordinated Skills Overview

Coordinated skills orchestrate multiple child skills under a coach.

Core types:

- `SkillCoach`: reward/success/termination coordinator
- `SkillCoordinatedSet`: fixed set of child skills
- `SkillCoordinatedPopulation`: child skills with population counts

Use coordinated skills when sub-policies should learn independently but act jointly.
