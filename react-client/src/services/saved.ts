import { preparationSteps, procedures } from "./procedures";

export interface SavedChecklist {
  id: string;
  procedureId: string;
  title: string;
  checked: boolean[];
}
const key = "domrov.checklists.v1";
export function readSaved(): { items: SavedChecklist[]; error: string } {
  try {
    const raw: unknown = JSON.parse(localStorage.getItem(key) ?? "[]");
    if (
      !Array.isArray(raw) ||
      !raw.every(
        (x) =>
          x &&
          typeof x.id === "string" &&
          typeof x.procedureId === "string" &&
          procedures.some(p => p.id === x.procedureId) &&
          typeof x.title === "string" &&
          Array.isArray(x.checked) &&
          x.checked.length === preparationSteps.length &&
          x.checked.every((b: unknown) => typeof b === "boolean"),
      )
    )
      throw Error();
    return { items: raw, error: "" };
  } catch {
    return {
      items: [],
      error: "មិនអាចអានទិន្នន័យលើឧបករណ៍បានទេ។ សូមពិនិត្យការកំណត់កម្មវិធីរុករក។",
    };
  }
}
export function writeSaved(items: SavedChecklist[]) {
  try {
    if (items.length) localStorage.setItem(key, JSON.stringify(items));
    else localStorage.removeItem(key);
    return "";
  } catch {
    return "មិនអាចរក្សាទុក ឬលុបទិន្នន័យបានទេ។ សូមពិនិត្យការកំណត់កម្មវិធីរុករក។";
  }
}
