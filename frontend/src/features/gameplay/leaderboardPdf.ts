import { jsPDF } from 'jspdf';
import type { Leaderboard } from '../../types/api';

type BoardKind = 'individual' | 'branch' | 'department';
const labels: Record<BoardKind, string> = { individual: 'INDIVIDUAL CHAMPIONSHIP', branch: 'BRANCH CHAMPIONSHIP', department: 'DEPARTMENT CHAMPIONSHIP' };
const number = new Intl.NumberFormat('en-IN');
const text = (value: unknown) => String(value ?? 'Unlisted competitor').replace(/[\r\n]+/g, ' ').replace(/[^\x20-\x7E]/g, '-').trim();
const title = (entry: Record<string, unknown>, kind: BoardKind) => kind === 'individual' ? text(entry.name ?? entry.user_id) : kind === 'branch' ? text(entry.location_name ?? entry.location_code) : text(entry.department);
const detail = (entry: Record<string, unknown>, kind: BoardKind) => kind === 'individual' ? `${text(entry.department)} / ${text(entry.location_code)}` : kind === 'branch' ? text(entry.outlet_type ?? entry.location_code) : `${text(entry.active_users)} active players`;
const score = (entry: Record<string, unknown>) => Number(entry.normalized_score ?? entry.leaderboard_xp ?? 0);
const scoreLabel = (entry: Record<string, unknown>) => entry.normalized_score !== undefined ? 'NORMALIZED SCORE' : 'VERIFIED XP';

function podium(doc: jsPDF, entry: Record<string, unknown> | undefined, kind: BoardKind, rank: number, x: number, y: number, width: number, height: number) {
  const tones: Record<number, [number, number, number]> = { 1: [233, 251, 107], 2: [111, 210, 255], 3: [255, 174, 83] }; const tone = tones[rank];
  doc.setFillColor(16, 24, 38); doc.roundedRect(x, y, width, height, 4, 4, 'F'); doc.setDrawColor(...tone); doc.setLineWidth(rank === 1 ? 1.1 : .5); doc.roundedRect(x, y, width, height, 4, 4, 'S');
  doc.setTextColor(...tone); doc.setFont('helvetica', 'bold'); doc.setFontSize(rank === 1 ? 22 : 17); doc.text(`#${rank}`, x + 8, y + 16);
  if (!entry) { doc.setTextColor(165, 178, 197); doc.setFontSize(9); doc.text('No verified ranking yet', x + 8, y + 29); return; }
  doc.setTextColor(239, 243, 251); doc.setFontSize(11); doc.text(doc.splitTextToSize(title(entry, kind), width - 16).slice(0, 2), x + 8, y + 30);
  doc.setTextColor(157, 173, 195); doc.setFont('helvetica', 'normal'); doc.setFontSize(7.5); doc.text(detail(entry, kind), x + 8, y + height - 17);
  doc.setTextColor(...tone); doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.text(number.format(score(entry)), x + 8, y + height - 7);
}

export function exportLeaderboardPdf(board: Leaderboard, kind: BoardKind) {
  const doc = new jsPDF({ orientation: 'landscape', unit: 'mm', format: 'a4' }); const width = 297; const entries = board.entries; const scope = board.scope.toUpperCase(); const generated = new Date().toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
  doc.setFillColor(8, 13, 23); doc.rect(0, 0, width, 210, 'F'); doc.setFillColor(18, 32, 52); doc.rect(0, 0, width, 42, 'F'); doc.setFillColor(233, 251, 107); doc.rect(0, 0, 8, 42, 'F');
  doc.setTextColor(233, 251, 107); doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.text('CARVERSE DRIVE / VERIFIED LEAGUES', 16, 15); doc.setTextColor(244, 247, 252); doc.setFontSize(24); doc.text(labels[kind], 16, 29);
  doc.setTextColor(167, 184, 204); doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.text(`${scope} VIEW | GENERATED ${generated}`, 16, 36); doc.setTextColor(233, 251, 107); doc.setFont('helvetica', 'bold'); doc.setFontSize(12); doc.text(`${number.format(board.dealership_score)} DEALERSHIP SCORE`, 278, 20, { align: 'right' }); doc.setFontSize(7); doc.setTextColor(167, 184, 204); doc.text('VERIFIED PERFORMANCE ONLY', 278, 28, { align: 'right' });
  doc.setTextColor(167, 184, 204); doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.text('PODIUM / TOP VERIFIED PERFORMERS', 18, 50);
  const leaders = [entries[1], entries[0], entries[2]]; [{ rank: 2, x: 18, y: 61, h: 39 }, { rank: 1, x: 105, y: 51, h: 49 }, { rank: 3, x: 192, y: 65, h: 35 }].forEach((position, index) => podium(doc, leaders[index], kind, position.rank, position.x, position.y, 69, position.h));
  const drawHeader = (y: number) => { doc.setDrawColor(47, 62, 84); doc.line(18, y - 9, 279, y - 9); doc.setTextColor(149, 165, 185); doc.setFont('helvetica', 'normal'); doc.setFontSize(7); doc.text('Rank', 18, y); doc.text(kind === 'individual' ? 'Player' : kind === 'branch' ? 'Branch' : 'Department', 40, y); doc.text('Context', 142, y); doc.text('Performance', 278, y, { align: 'right' }); doc.line(18, y + 4, 279, y + 4); };
  const drawRows = (rows: Array<Record<string, unknown>>, startY: number) => rows.forEach((entry, index) => { const y = startY + index * 10; const rank = Number(entry.rank ?? 0); const tone: [number, number, number] = rank === 1 ? [233, 251, 107] : rank === 2 ? [111, 210, 255] : rank === 3 ? [255, 174, 83] : [205, 216, 231]; doc.setFillColor(rank <= 3 ? 21 : 13, rank <= 3 ? 32 : 18, rank <= 3 ? 49 : 30); doc.rect(18, y - 5.5, 261, 8.5, 'F'); doc.setTextColor(...tone); doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.text(`#${rank}`, 18, y); doc.setTextColor(238, 243, 251); doc.text(title(entry, kind).slice(0, 38), 40, y); doc.setTextColor(151, 168, 190); doc.setFont('helvetica', 'normal'); doc.setFontSize(7.2); doc.text(detail(entry, kind).slice(0, 42), 142, y); doc.setTextColor(...tone); doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.text(`${number.format(score(entry))} ${scoreLabel(entry)}`, 278, y, { align: 'right' }); });
  let offset = 0; let first = true; while (offset < entries.length) { const capacity = first ? 6 : 15; if (!first) { doc.addPage(); doc.setFillColor(8, 13, 23); doc.rect(0, 0, width, 210, 'F'); doc.setTextColor(233, 251, 107); doc.setFont('helvetica', 'bold'); doc.setFontSize(10); doc.text(`CARVERSE DRIVE / ${labels[kind]}`, 18, 16); doc.setTextColor(167, 184, 204); doc.setFont('helvetica', 'normal'); doc.setFontSize(8); doc.text(`${scope} VIEW - FULL GRID`, 18, 23); drawHeader(40); } else { doc.setTextColor(233, 251, 107); doc.setFont('helvetica', 'bold'); doc.setFontSize(8); doc.text('FULL GRID', 18, 121); drawHeader(130); } const slice = entries.slice(offset, offset + capacity); drawRows(slice, first ? 143 : 53); offset += slice.length; first = false; }
  const pages = doc.getNumberOfPages(); for (let page = 1; page <= pages; page += 1) { doc.setPage(page); doc.setTextColor(117, 133, 153); doc.setFont('helvetica', 'normal'); doc.setFontSize(6.5); doc.text('CarVerse Drive - traceable rankings from verified operational events', 18, 202); doc.text(`PAGE ${page} / ${pages}`, 279, 202, { align: 'right' }); }
  doc.save(`carverse-${kind}-leaderboard-${board.scope}.pdf`);
}
