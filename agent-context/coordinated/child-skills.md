# Managing Child Skills

`SkillCoordinatedSet` and `SkillCoordinatedPopulation` manage child skills with explicit registration.

## Common operations

```python
coordinated.add_skill(child_skill)
coordinated.get_skills()
coordinated.get_skill_names()
```

## Registration rule

Child names must match the keys returned by `SkillCoach.compute_reward(...)`.

## Population variant

`SkillCoordinatedPopulation` extends coordinated training with per-skill population counts while preserving coach/key alignment.
