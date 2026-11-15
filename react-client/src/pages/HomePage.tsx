import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { procedures } from "../services/procedures";
import { readSaved } from "../services/saved";
export function HomePage() {
  const [query, setQuery] = useState("");
  const navigate = useNavigate();
  const saved = readSaved().items;
  function submit(e: FormEvent) {
    e.preventDefault();
    if (query.trim()) navigate("/chat?q=" + encodeURIComponent(query.trim()));
  }
  return (
    <section className="home">
      <div className="eyebrow">
        DOMROV WORKSPACE <span>សម្រាប់អ្នកទាំងអស់គ្នា</span>
      </div>
      <div className="hero">
        <div className="hero-symbol" aria-hidden="true">
          ដ
        </div>
        <p className="small-label">សួស្តី! សូមស្វាគមន៍មកកាន់ DOMROV</p>
        <h1>
          យល់ពីច្បាប់។
          <br />
          <span>ដឹងពីជំហានបន្ទាប់។</span>
        </h1>
        <p>
          ពីសំណួរច្បាប់ ទៅការត្រៀមសេវាសាធារណៈ
          <br className="desktop-break" /> ស្វែងយល់ដោយមានប្រភពយោងនៅកន្លែងតែមួយ។
        </p>
        <form className="question-box" onSubmit={submit}>
          <label htmlFor="home-question">តើថ្ងៃនេះ យើងអាចជួយអ្វីអ្នកបាន?</label>
          <textarea
            id="home-question"
            rows={2}
            placeholder="សួរសំណួររបស់អ្នកជាភាសាខ្មែរ…"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          <div>
            <span>ចម្លើយភ្ជាប់ជាមួយប្រភពយោង</span>
            <button className="primary" disabled={!query.trim()}>
              សួរ DOMROV ↗
            </button>
          </div>
        </form>
        <div className="examples">
          <span>សាកសួរ៖</span>
          {["តើអ្នកបើកបរត្រូវមានប័ណ្ណបើកបរឬទេ?", "ស្វែងរកមាត្រា ៨"].map((q) => (
            <button key={q} onClick={() => setQuery(q)}>
              {q} ↗
            </button>
          ))}
        </div>
      </div>
      <div className="section-heading">
        <div>
          <p className="small-label">ជំហានបន្ទាប់របស់អ្នក</p>
          <h2>ស្វែងយល់ពីសេវាសាធារណៈ</h2>
        </div>
        <Link to="/procedures">មើលទាំងអស់ →</Link>
      </div>
      <div className="service-grid">
        {procedures.map((p) => (
          <Link key={p.id} to={"/procedures/" + p.id} className="service-card">
            <span className="service-icon">{p.icon}</span>
            <span className="demo-label">គំរូ · មិនទាន់បានពិនិត្យ</span>
            <h3>{p.title}</h3>
            <p>{p.description}</p>
            <span className="card-action">
              មើលការត្រៀមខ្លួន <b>↗</b>
            </span>
          </Link>
        ))}
      </div>
      <div className="section-heading">
        <h2>ការងាររក្សាទុកថ្មីៗ</h2>
        <Link to="/saved">មើលការងារ →</Link>
      </div>
      <div className="recent-panel">
        {saved.length ? (
          saved.slice(-3).map((s) => (
            <Link key={s.id} to={"/procedures/" + s.procedureId}>
              {s.title} →
            </Link>
          ))
        ) : (
          <>
            <span className="service-icon">☆</span>
            <div>
              <h3>ចាប់ផ្តើមការងារដំបូងរបស់អ្នក</h3>
              <p>រក្សាទុកបញ្ជីត្រៀមខ្លួន ដើម្បីបន្តនៅលើឧបករណ៍នេះ។</p>
            </div>
            <Link to="/procedures">មើលសេវា →</Link>
          </>
        )}
      </div>
    </section>
  );
}
