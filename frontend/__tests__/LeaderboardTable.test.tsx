import { render, screen, within } from "@testing-library/react";
import LeaderboardTable from "@/components/LeaderboardTable";
import type { LeaderboardRow } from "@/types";

const rows: LeaderboardRow[] = [
  { rank: 1, town: "Kinsale, Ireland", display_name: "Kinsale, County Cork", species_count: 40 },
  { rank: 2, town: "Bantry, Ireland", display_name: "Bantry, County Cork", species_count: 10 },
  { rank: 3, town: "Schull, Ireland", display_name: "Schull, County Cork", species_count: 5 },
  { rank: 4, town: "GhostTown", display_name: "GhostTown", species_count: null, error: "not found" },
];

describe("LeaderboardTable", () => {
  it("renders all rows", () => {
    render(<LeaderboardTable rows={rows} backDays={30} />);
    expect(screen.getByText("Kinsale, County Cork")).toBeInTheDocument();
    expect(screen.getByText("Bantry, County Cork")).toBeInTheDocument();
    expect(screen.getByText("Schull, County Cork")).toBeInTheDocument();
    expect(screen.getByText("GhostTown")).toBeInTheDocument();
  });

  it("renders species counts for found locations", () => {
    render(<LeaderboardTable rows={rows} backDays={30} />);
    expect(screen.getByText("40")).toBeInTheDocument();
    expect(screen.getByText("10")).toBeInTheDocument();
    expect(screen.getByText("5")).toBeInTheDocument();
  });

  it("shows medal emoji for top 3 ranks", () => {
    render(<LeaderboardTable rows={rows} backDays={30} />);
    expect(screen.getByText("🥇")).toBeInTheDocument();
    expect(screen.getByText("🥈")).toBeInTheDocument();
    expect(screen.getByText("🥉")).toBeInTheDocument();
  });

  it("shows rank number (4) for rows beyond top 3", () => {
    render(<LeaderboardTable rows={rows} backDays={30} />);
    expect(screen.getByText("4")).toBeInTheDocument();
  });

  it("displays error text for not-found rows", () => {
    render(<LeaderboardTable rows={rows} backDays={30} />);
    expect(screen.getByText("not found")).toBeInTheDocument();
  });

  it("rank 1 row has rank1 class applied", () => {
    const { container } = render(<LeaderboardTable rows={rows} backDays={30} />);
    const rank1Row = container.querySelector("tr.rank1");
    expect(rank1Row).not.toBeNull();
  });

  it("rank 2 row has rank2 class applied", () => {
    const { container } = render(<LeaderboardTable rows={rows} backDays={30} />);
    const rank2Row = container.querySelector("tr.rank2");
    expect(rank2Row).not.toBeNull();
  });

  it("rank 3 row has rank3 class applied", () => {
    const { container } = render(<LeaderboardTable rows={rows} backDays={30} />);
    const rank3Row = container.querySelector("tr.rank3");
    expect(rank3Row).not.toBeNull();
  });

  it("renders back days in subtitle", () => {
    render(<LeaderboardTable rows={rows} backDays={14} />);
    expect(screen.getByText(/last 14 days/i)).toBeInTheDocument();
  });

  it("rank 1 row appears first in the table body", () => {
    render(<LeaderboardTable rows={rows} backDays={30} />);
    const tableRows = screen.getAllByRole("row").slice(1); // skip header
    expect(tableRows[0]).toHaveTextContent("Kinsale");
  });
});
