# Coordinated Job JSON Schema

Coordinated entries are serialized in `skills_coordinated[]` (e.g., `SkillCoordinatedSchema`-style blocks).

## Core shape

```json
{
  "name": "team-skill",
  "type": "SkillCoordinatedSet",
  "config": {
    "remote_address": null,
    "impl_cls": { "cls_name": "MyCoach", "cls_module": "my_agent.coach", "cls_src": "<base64-pickle>", "cls_deps": [] },
    "skills": [],
    "scenarios": []
  }
}
```

## Key meaning

- `type`: `"SkillCoordinatedSet"` or `"SkillCoordinatedPopulation"`.
- `impl_cls`: serialized coach.
- `skills`: child skill metadata list.
- `scenarios`: coordinated scenario list.
