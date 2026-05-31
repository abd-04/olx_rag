import { ExternalLink, Fuel, Gauge, MapPin, Settings2, Tag, CalendarDays } from "lucide-react";

const rankLabels = ["Best match", "Strong match", "Worth a look", "Alternative", "Alternative"];

export default function ListingCard({ listing, index }) {
  return (
    <article className="listing-card">
      <div className="listing-card__topline">
        <span className="rank-pill">{rankLabels[index] || `Match ${index + 1}`}</span>
        <span className="listing-number">0{index + 1}</span>
      </div>

      <div>
        <h3>{listing.title || "Untitled OLX listing"}</h3>
        <p className="listing-price">{listing.price_lakh || "Price unavailable"}</p>
      </div>

      <div className="listing-meta">
        <Meta icon={MapPin} label={listing.city || "Location unavailable"} />
        <Meta icon={CalendarDays} label={listing.year || "Year unavailable"} />
        <Meta icon={Gauge} label={listing.km_driven ? `${listing.km_driven} km` : "Mileage unavailable"} />
        <Meta icon={Settings2} label={listing.transmission || "Gearbox unavailable"} />
        <Meta icon={Fuel} label={listing.fuel || "Fuel unavailable"} />
        <Meta icon={Tag} label={listing.vehicle_type || "Vehicle"} />
      </div>

      <a className="listing-link" href={listing.url} target="_blank" rel="noreferrer">
        View verified listing
        <ExternalLink size={16} />
      </a>
    </article>
  );
}

function Meta({ icon: Icon, label }) {
  return (
    <span>
      <Icon size={15} />
      {label}
    </span>
  );
}
