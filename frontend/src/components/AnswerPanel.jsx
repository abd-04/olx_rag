import ReactMarkdown from "react-markdown";
import { Bot, Sparkles } from "lucide-react";

export default function AnswerPanel({ answer, filters }) {
  return (
    <section className="answer-panel">
      <div className="answer-heading">
        <span className="icon-tile icon-tile--green">
          <Bot size={18} />
        </span>
        <div>
          <p className="eyebrow">Grounded assistant</p>
          <h2>What stood out</h2>
        </div>
      </div>

      {Object.keys(filters || {}).length > 0 && (
        <div className="filter-row" aria-label="Applied filters">
          {Object.entries(filters).map(([key, value]) => (
            <span className="filter-pill" key={key}>
              {formatFilter(key, value)}
            </span>
          ))}
        </div>
      )}

      <div className="answer-copy">
        <ReactMarkdown>{answer}</ReactMarkdown>
      </div>

      <p className="grounding-note">
        <Sparkles size={15} />
        Recommendations are grounded in the retrieved OLX listings.
      </p>
    </section>
  );
}

function formatFilter(key, value) {
  if (key === "max_price") return `Up to PKR ${Number(value).toLocaleString()}`;
  if (key === "min_price") return `From PKR ${Number(value).toLocaleString()}`;
  return String(value);
}
