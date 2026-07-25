const SHEET_ID = "1DwvZ2IRI126NXuitMS-kPsCZFVlp6VN5gDiJeXVMsQs";
const GID = "357143957";

export type PhotoSubmission = {
  rowIndex: number;
  timestamp: string;
  storeName: string;
  photoUrls: string[]; // direct-viewable image URLs, converted from Drive links
  submitterName: string;
  comment: string;
};

/** Minimal CSV parser that handles quoted fields containing commas/newlines. */
function parseCsv(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [];
  let field = "";
  let inQuotes = false;

  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (inQuotes) {
      if (c === '"') {
        if (text[i + 1] === '"') {
          field += '"';
          i++;
        } else {
          inQuotes = false;
        }
      } else {
        field += c;
      }
    } else if (c === '"') {
      inQuotes = true;
    } else if (c === ",") {
      row.push(field);
      field = "";
    } else if (c === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (c === "\r") {
      // skip, \n handles the line break
    } else {
      field += c;
    }
  }
  if (field.length > 0 || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

/** Converts a Google Drive "open"/"file" share link into a directly-viewable image URL. */
function driveLinkToImageUrl(link: string): string | null {
  const trimmed = link.trim();
  const match = trimmed.match(/[-\w]{25,}/); // Drive file IDs are long alphanumeric strings
  if (!match) return null;
  return `https://drive.google.com/thumbnail?id=${match[0]}&sz=w1000`;
}

export async function getPhotoSubmissions(): Promise<PhotoSubmission[]> {
  const url = `https://docs.google.com/spreadsheets/d/${SHEET_ID}/export?format=csv&gid=${GID}`;
  const res = await fetch(url, { next: { revalidate: 60 } });
  if (!res.ok) {
    throw new Error(`Failed to fetch response sheet: ${res.status}`);
  }
  const csv = await res.text();
  const rows = parseCsv(csv);
  if (rows.length <= 1) return [];

  // Header: タイムスタンプ, 店舗名, お店の写真・メニュー写真を..., お名前（インスタID等でもOK）, コメント・感想など（任意）
  const dataRows = rows.slice(1).filter((r) => r.some((cell) => cell.trim()));

  return dataRows.map((r, i) => {
    const [timestamp = "", storeName = "", photosCell = "", submitterName = "", comment = ""] = r;
    const photoUrls = photosCell
      .split(",")
      .map((link) => driveLinkToImageUrl(link))
      .filter((u): u is string => !!u);
    return {
      rowIndex: i,
      timestamp,
      storeName: storeName.trim(),
      photoUrls,
      submitterName: submitterName.trim(),
      comment: comment.trim(),
    };
  });
}
