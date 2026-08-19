# Quality and Maintenance

## Idempotence

The factory manifest distinguishes generated ownership from user ownership. A later run compares the desired system to the manifest and repository evidence. It updates factory-owned files, preserves user-owned files, and reports conflicts.

## Drift review

Regenerate or review the ecosystem when:

- architecture boundaries change;
- new public contracts or migration paths appear;
- CI or validation strategy changes materially;
- project documentation moves;
- tooling conventions change;
- repeated workflow failures expose missing ownership or gates.

## Lean-context review

Remove duplication before adding more rules. Keep `SKILL.md` procedural. Move long stable reference material into skill references. Delete no user-owned file automatically.

## Success measures

A mature ecosystem should improve:

- correct task routing;
- visibility of assumptions and blockers;
- architecture-review consistency;
- validation evidence quality;
- planner actionability;
- documentation alignment;
- recovery from rejected designs.

Agent count and prompt length are not success measures.
