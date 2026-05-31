import { useState } from "react";
import { ArrowRight, CarFront, Search, ShieldCheck, SlidersHorizontal } from "lucide-react";
import { askVehicleFinder } from "./api";
import AnswerPanel from "./components/AnswerPanel";
import ListingCard from "./components/ListingCard";
import LoadingSkeleton from "./components/LoadingSkeleton";

const prompts = [
  "Family car under 30 lakh in Lahore",
  "Automatic petrol car in Karachi",
  "Reliable daily-use car with low mileage",
];

export default function App() {
  const [question, setQuestion] = useState("");
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  async function submitSearch(event, suggestedQuestion) {
    event?.preventDefault();
    const nextQuestion = (suggestedQuestion || question).trim();
    if (!nextQuestion || loading) return;

    setQuestion(nextQuestion);
    setLoading(true);
    setError("");

    try {
      setResult(await askVehicleFinder(nextQuestion));
    } catch (requestError) {
      setError(requestError.message);
    } finally {
      setLoading(false);
    }
  }

  return (
    <main>
      <header className="site-header">
        <a className="brand" href="/" aria-label="OLX Vehicle Finder home">
          <span className="brand-mark"><CarFront size={22} /></span>
          <span>
            <strong>Vehicle Finder</strong>
            <small>OLX Pakistan listings</small>
          </span>
        </a>

        <span className="header-note">
          <ShieldCheck size={16} />
          Grounded recommendations
        </span>
      </header>

      <section className="hero">
        <p className="eyebrow">Multilingual vehicle discovery</p>
        <h1>Find the right ride.<br /><em>Skip the endless scroll.</em></h1>
        <p className="hero-copy">
          Ask naturally in English or Roman Urdu. We combine structured filters
          with semantic search across verified OLX listings.
        </p>

        <form className="search-box" onSubmit={submitSearch}>
          <Search size={21} />
          <input
            value={question}
            onChange={(event) => setQuestion(event.target.value)}
            placeholder="Try: family car under 30 lakh in Lahore"
            aria-label="Search vehicle listings"
          />
          <button type="submit" disabled={loading || !question.trim()}>
            {loading ? "Searching" : "Search"}
            <ArrowRight size={18} />
          </button>
        </form>

        <div className="prompt-row">
          <span><SlidersHorizontal size={14} /> Try a search</span>
          {prompts.map((prompt) => (
            <button type="button" key={prompt} onClick={(event) => submitSearch(event, prompt)}>
              {prompt}
            </button>
          ))}
        </div>
      </section>

      {error && <p className="error-banner">{error}</p>}

      <section className="content-shell">
        {loading && <LoadingSkeleton />}

        {!loading && result && (
          <>
            <AnswerPanel answer={result.answer} filters={result.filters} />
            <div className="results-heading">
              <div>
                <p className="eyebrow">Retrieved from OLX</p>
                <h2>Top matches</h2>
              </div>
              <span>{result.listings.length} verified listings</span>
            </div>
            {result.listings.length > 0 ? (
              <div className="results-grid">
                {result.listings.map((listing, index) => (
                  <ListingCard listing={listing} index={index} key={listing.id} />
                ))}
              </div>
            ) : (
              <p className="empty-state">No listing matched those filters. Try widening your search.</p>
            )}
          </>
        )}

        {!loading && !result && (
          <div className="feature-grid">
            <Feature number="01" title="Meaning-aware" copy="Search by intent, not only exact keywords." />
            <Feature number="02" title="Filter-aware" copy="Price, city, fuel, type, and gearbox stay precise." />
            <Feature number="03" title="Source-backed" copy="Every recommendation links to a verified OLX listing." />
          </div>
        )}
      </section>
    </main>
  );
}

function Feature({ number, title, copy }) {
  return (
    <article className="feature-card">
      <span>{number}</span>
      <h2>{title}</h2>
      <p>{copy}</p>
    </article>
  );
}
