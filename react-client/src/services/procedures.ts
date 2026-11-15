// Proposal only: no procedure endpoint or reviewed pilot records currently exist.
export type EvidenceStatus = "missing" | "stale" | "conflicting";
export interface Procedure {
  id: string;
  title: string;
  description: string;
  icon: string;
  evidenceStatus: EvidenceStatus;
  lastVerified: string | null;
  eligibility: string | null;
  documents: string[] | null;
  office: string | null;
  fee: string | null;
  hours: string | null;
  timeframe: string | null;
  sources: { title: string; url: string }[];
}
const unknown = {
  lastVerified: null,
  eligibility: null,
  documents: null,
  office: null,
  fee: null,
  hours: null,
  timeframe: null,
  sources: [],
};
export const procedures: Procedure[] = [
  {
    ...unknown,
    id: "driving-licence",
    icon: "↗",
    title: "ប័ណ្ណបើកបរ",
    description: "ស្វែងយល់ពីច្បាប់ និងត្រៀមសំណួរមុនដាក់ពាក្យ។",
    evidenceStatus: "missing",
  },
  {
    ...unknown,
    id: "business-registration",
    icon: "▦",
    title: "ការចុះបញ្ជីអាជីវកម្ម",
    description: "រៀបចំការស្រាវជ្រាវ និងបញ្ជីត្រៀមខ្លួនរបស់អ្នក។",
    evidenceStatus: "stale",
  },
  {
    ...unknown,
    id: "civil-registration",
    icon: "▤",
    title: "អត្រានុកូលដ្ឋាន",
    description: "ស្វែងយល់ពីព័ត៌មានដែលត្រូវសួរបញ្ជាក់បន្ថែម។",
    evidenceStatus: "conflicting",
  },
];
export const preparationSteps = [
  "ពិនិត្យប្រភពច្បាប់ដើមដែលពាក់ព័ន្ធ",
  "សួរបញ្ជាក់លក្ខខណ្ឌ និងឯកសារចាំបាច់",
  "សួរបញ្ជាក់ការិយាល័យ ថ្លៃសេវា និងរយៈពេល",
];
export const evidenceLabels: Record<EvidenceStatus, string> = {
  missing: "គំរូស្ថានភាព៖ ខ្វះប្រភព",
  stale: "គំរូស្ថានភាព៖ ប្រភពត្រូវពិនិត្យឡើងវិញ",
  conflicting: "គំរូស្ថានភាព៖ ប្រភពមិនស្របគ្នា",
};
