import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { Button, PdfLink, StatePanel } from "../components/common/UI";
import {
  evidenceLabels,
  preparationSteps,
  procedures,
} from "../services/procedures";
import { readSaved, writeSaved } from "../services/saved";
const unknown = "មិនទាន់បានផ្ទៀងផ្ទាត់";
export function ProcedureCatalog() {
  return (
    <section className="page-stack">
      <p className="small-label">PUBLIC SERVICES</p>
      <h1>សេវាសាធារណៈ</h1>
      <StatePanel
        title="បញ្ជីសេវាគំរូ · មិនទាន់មានកំណត់ត្រាដែលបានពិនិត្យ"
        description="ព័ត៌មាននីតិវិធីមិនទាន់ភ្ជាប់ API។ ស្ថានភាពភស្តុតាងខាងក្រោមសម្រាប់បង្ហាញការរចនាប៉ុណ្ណោះ។"
        tone="warning"
      />
      <div className="service-grid">
        {procedures.map((p) => (
          <Link className="service-card" key={p.id} to={"/procedures/" + p.id}>
            <span className="service-icon">{p.icon}</span>
            <h2>{p.title}</h2>
            <p>{p.description}</p>
            <span className="demo-label">
              {evidenceLabels[p.evidenceStatus]}
            </span>
            <p className="card-action">មើលព័ត៌មាន →</p>
          </Link>
        ))}
      </div>
    </section>
  );
}
export function ProcedurePage() {
  const { id } = useParams();
  const p = procedures.find((x) => x.id === id);
  const initial = readSaved();
  const [checked, setChecked] = useState(
    initial.items.find((x) => x.procedureId === id)?.checked ??
      preparationSteps.map(() => false),
  );
  const [status, setStatus] = useState(initial.error);
  if (!p) return <StatePanel title="រកមិនឃើញសេវា" />;
  function save() {
    if (!p) return;
    const current = readSaved();
    if (current.error) {
      setStatus(current.error);
      return;
    }
    const error = writeSaved([
      ...current.items.filter((x) => x.procedureId !== id),
      { id: p.id, procedureId: p.id, title: p.title, checked },
    ]);
    setStatus(error || "បានរក្សាទុកលើឧបករណ៍នេះ។");
  }
  return (
    <section className="page-stack procedure-detail">
      <Link to="/procedures">← សេវាសាធារណៈ</Link>
      <p className="small-label">គំរូនីតិវិធី · DEMO</p>
      <h1>{p.title}</h1>
      <p>{p.description}</p>
      <StatePanel
        tone="warning"
        title={evidenceLabels[p.evidenceStatus]}
        description="ស្ថានភាពសាកល្បង មិនមែនជាការវាយតម្លៃសេវាផ្លូវការទេ។ មិនអាចប្រើបញ្ជីនេះជាលក្ខខណ្ឌដាក់ពាក្យបានទេ។"
      />
      <div className="detail-grid">
        <div className="page-stack">
          <section className="panel">
            <h2>លក្ខខណ្ឌ និងឯកសារ</h2>
            <dl>
              <dt>អ្នកមានសិទ្ធិ</dt>
              <dd>{p.eligibility ?? unknown}</dd>
              <dt>ឯកសារចាំបាច់</dt>
              <dd>{p.documents?.join(" · ") ?? unknown}</dd>
            </dl>
          </section>
          <section className="panel">
            <h2>បញ្ជីត្រៀមខ្លួនផ្ទាល់ខ្លួន</h2>
            <p>ជំហានស្រាវជ្រាវទូទៅ មិនមែនជាជំហានដាក់ពាក្យផ្លូវការ។</p>
            <ol className="checklist">
              {preparationSteps.map((step, i) => (
                <li key={step}>
                  <label>
                    <input
                      type="checkbox"
                      checked={checked[i] ?? false}
                      onChange={(e) =>
                        setChecked(
                          checked.map((v, n) =>
                            n === i ? e.target.checked : v,
                          ),
                        )
                      }
                    />
                    <span>
                      {i + 1}. {step}
                    </span>
                  </label>
                </li>
              ))}
            </ol>
            <p className="privacy-note">
              រក្សាទុកតែបញ្ជីនេះលើកម្មវិធីរុករករបស់ឧបករណ៍នេះ។ អ្នកប្រើឧបករណ៍ដូចគ្នាអាចមើលបាន។
              អាចលុបនៅទំព័រការងាររក្សាទុក។
            </p>
            <div className="actions no-print">
              <Button onClick={save}>រក្សាទុកបញ្ជី</Button>
              <Button variant="secondary" onClick={() => window.print()}>
                បោះពុម្ព / PDF
              </Button>
              <Link to="/saved">មើលការងាររក្សាទុក →</Link>
            </div>
            <p role="status">{status}</p>
          </section>
        </div>
        <aside className="page-stack">
          <section className="panel">
            <h2>ព័ត៌មានសេវា</h2>
            <dl>
              {[
                ["ការិយាល័យ / បណ្តាញ", p.office],
                ["ថ្លៃសេវាផ្លូវការ", p.fee],
                ["ម៉ោងសេវា", p.hours],
                ["រយៈពេល", p.timeframe],
                ["ផ្ទៀងផ្ទាត់ចុងក្រោយ", p.lastVerified],
              ].map(([label, value]) => (
                <div key={label}>
                  <dt>{label}</dt>
                  <dd>{value ?? unknown}</dd>
                </div>
              ))}
            </dl>
          </section>
          <section className="panel">
            <h2>ប្រភព និងមូលដ្ឋានច្បាប់</h2>
            {p.sources.length ? (
              p.sources.map((s) => (
                <PdfLink key={s.url} url={s.url} label={s.title} />
              ))
            ) : (
              <p>មិនទាន់មានប្រភពនីតិវិធីដែលបានពិនិត្យ។</p>
            )}
            <Link to={"/search?q=" + encodeURIComponent(p.title)}>
              ស្វែងរកមូលដ្ឋានច្បាប់ →
            </Link>
          </section>
        </aside>
      </div>
    </section>
  );
}
export function SavedPage() {
  const initial = readSaved();
  const [items, setItems] = useState(initial.items);
  const [status, setStatus] = useState(initial.error);
  function remove(id?: string) {
    const next = id ? items.filter((x) => x.id !== id) : [];
    const error = writeSaved(next);
    setStatus(error || "បានលុបទិន្នន័យ។");
    if (!error) setItems(next);
  }
  return (
    <section className="page-stack">
      <p className="small-label">YOUR LOCAL WORK</p>
      <h1>ការងាររក្សាទុក</h1>
      <p>
        បញ្ជីត្រូវបានរក្សាទុកលើឧបករណ៍នេះប៉ុណ្ណោះ។ គ្មានការធ្វើសមកាលកម្មលើ cloud។
        សន្ទនាមិនត្រូវបានរក្សាទុកទេ និងបាត់នៅពេលចាកចេញពីទំព័រ។
      </p>
      <Button variant="secondary" onClick={() => remove()}>
        លុបបញ្ជីទាំងអស់
      </Button>
      {items.length ? (
        <>
          {items.map((s) => (
            <article className="panel" key={s.id}>
              <h2>
                <Link to={"/procedures/" + s.procedureId}>{s.title} →</Link>
              </h2>
              <p>
                គំរូ · {s.checked.filter(Boolean).length}/
                {preparationSteps.length} ជំហានត្រៀមខ្លួន
              </p>
              <Button variant="ghost" onClick={() => remove(s.id)}>
                លុបបញ្ជីនេះ
              </Button>
            </article>
          ))}
        </>
      ) : (
        <StatePanel
          title="មិនទាន់មានការងាររក្សាទុក"
          description="បើកសេវាគំរូ ដើម្បីបង្កើតបញ្ជីត្រៀមខ្លួន។"
        />
      )}
      <p role="status">{status}</p>
      <Link to="/procedures">ស្វែងយល់ពីសេវា →</Link>
    </section>
  );
}
