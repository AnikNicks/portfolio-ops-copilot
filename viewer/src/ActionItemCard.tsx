import type { ActionItem } from "./types";
import { formatDollarRange } from "./formatting";

export function ActionItemCard({ item }: { item: ActionItem }) {
  return (
    <article className="action-card">
      <header className="action-card__header">
        <span className="action-card__rank">#{item.priority_rank}</span>
        <span className="action-card__impact">
          {formatDollarRange(item.dollar_impact_low, item.dollar_impact_high)}
        </span>
      </header>
      <dl className="action-card__body">
        <dt>Problem</dt>
        <dd>{item.problem}</dd>
        <dt>Solution</dt>
        <dd>{item.solution}</dd>
        <dt>Trade-offs</dt>
        <dd>{item.tradeoffs}</dd>
        <dt>Success metrics</dt>
        <dd>{item.success_metrics}</dd>
      </dl>
    </article>
  );
}
