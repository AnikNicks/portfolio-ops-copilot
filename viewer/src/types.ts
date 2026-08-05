// Mirrors the Pydantic models in pipeline/schemas.py (ActionItem, ActionMemo). Kept as plain
// interfaces, not generated, so this file also documents the JSON contract on the TS side of
// the fence - if the Python schema changes shape, this file needs a matching edit, which is
// the same "schemas are the contract" discipline the pipeline itself applies (see CLAUDE.md).

export interface ActionItem {
  problem: string;
  solution: string;
  tradeoffs: string;
  success_metrics: string;
  dollar_impact_low: number;
  dollar_impact_high: number;
  priority_rank: number;
}

export interface ActionMemo {
  company: string;
  summary: string;
  action_items: ActionItem[];
}

export interface Manifest {
  companies: string[];
}
