# Selector Quirks

- Selector package type names (`selector-teacher`, `selector-controller`) differ from runtime JSON type names (`SkillSelector`, `SkillSelectorController`).
- Selector action space is derived from children count (`Discrete(n)`), so child list order directly defines index semantics.
- Selectors require at least one child; empty `children` fails at initialization.
- Teacher selector masks must match child count; mismatched shapes break routing.
- Runtime output is the selected child's action, not the selector index itself.
