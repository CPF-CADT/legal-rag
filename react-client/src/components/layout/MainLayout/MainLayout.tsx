import { Outlet } from "react-router-dom";
import { Header } from "../Header/Header";
import { isDemo } from "../../../services/api";
export function MainLayout() {
  return (
    <div className="workspace">
      <a className="skip-link" href="#main">
        រំលងទៅមាតិកា
      </a>
      <Header />
      <div className="workspace-body">
        <div className="topbar">
          <span>ច្បាប់ និងសេវាសាធារណៈ</span>
          <span className="status-pill">
            {isDemo ? "ទិន្នន័យគំរូ · DEMO" : "ភ្ជាប់ API · Live"}
          </span>
        </div>
        <main id="main" tabIndex={-1}>
          <div className="mode-notice">
            {isDemo
              ? "ទិន្នន័យគំរូសម្រាប់សាកល្បង។ មិនមែនជាការណែនាំផ្លូវការដែលបានផ្ទៀងផ្ទាត់ទេ។"
              : "សូមពិនិត្យប្រភពដើម។ ការភ្ជាប់ API មិនបញ្ជាក់ថាទិន្នន័យត្រូវបានផ្ទៀងផ្ទាត់ទេ។"}
          </div>
          <Outlet />
        </main>
        <footer>
          DOMROV · ព័ត៌មានសម្រាប់ជំនួយ មិនមែនជាដំបូន្មានផ្នែកច្បាប់។
          ប្រភពយោងអាចចូលមើលដោយឥតគិតថ្លៃ។
        </footer>
      </div>
    </div>
  );
}
