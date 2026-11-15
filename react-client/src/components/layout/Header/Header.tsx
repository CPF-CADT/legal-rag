import { Link, NavLink } from "react-router-dom";
const links = [
  ["/", "⌂", "ទំព័រដើម"],
  ["/chat", "↗", "សួរ DOMROV"],
  ["/search", "⌕", "ស្វែងរកច្បាប់"],
  ["/procedures", "▤", "សេវាសាធារណៈ"],
  ["/saved", "☆", "ការងាររក្សាទុក"],
];
export function Header() {
  return (
    <aside className="sidebar">
      <Link className="brand" to="/">
        <span className="brand-mark">ដ</span>
        <span>
          DOMROV<small>ច្បាស់លាស់ រាល់ជំហាន</small>
        </span>
      </Link>
      <p className="nav-caption">កន្លែងធ្វើការរបស់អ្នក</p>
      <nav aria-label="ការរុករកចម្បង">
        {links.map(([to, icon, label]) => (
          <NavLink
            key={to}
            to={to}
            end={to === "/"}
            className={({ isActive }) =>
              isActive ? "nav-item active" : "nav-item"
            }
          >
            <span aria-hidden="true">{icon}</span>
            {label}
          </NavLink>
        ))}
      </nav>
      <div className="sidebar-note">
        <span className="small-label">ចាប់ផ្តើមដោយមានប្រភព</span>
        <p>យល់ពីច្បាប់។ ត្រៀមខ្លួនសម្រាប់ជំហានបន្ទាប់។</p>
        <Link to="/procedures">ស្វែងយល់ពីសេវា →</Link>
      </div>
      <div className="local-note">
        ◉ កន្លែងធ្វើការផ្ទាល់ខ្លួន<small>គ្មានគណនី ឬការរក្សាទុកលើ cloud</small>
      </div>
    </aside>
  );
}
