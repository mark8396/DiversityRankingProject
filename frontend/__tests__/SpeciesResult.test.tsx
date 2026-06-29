import { render, screen } from "@testing-library/react";
import SpeciesResult from "@/components/SpeciesResult";
import type { SpeciesResult as SpeciesResultType } from "@/types";

const baseResult: SpeciesResultType = {
  town: "Skibbereen, County Cork, Ireland",
  species_count: 3,
  back_days: 30,
  bbox: [51.53, 51.57, -9.29, -9.21],
  species_list: [
    { speciesCode: "mallard", comName: "Mallard", sciName: "Anas platyrhynchos" },
    { speciesCode: "hoopoe", comName: "Hoopoe", sciName: "Upupa epops" },
    { speciesCode: "commoo", comName: "Common Moorhen", sciName: "Gallinula chloropus" },
  ],
};

describe("SpeciesResult", () => {
  it("renders the species count prominently", () => {
    render(<SpeciesResult result={baseResult} />);
    expect(screen.getByText("3")).toBeInTheDocument();
  });

  it("renders the back_days in the label", () => {
    render(<SpeciesResult result={baseResult} />);
    expect(screen.getByText(/last 30 days/i)).toBeInTheDocument();
  });

  it("uses singular 'day' for back_days=1", () => {
    render(<SpeciesResult result={{ ...baseResult, back_days: 1 }} />);
    expect(screen.getByText(/last 1 day\b/i)).toBeInTheDocument();
  });

  it("renders the town name", () => {
    render(<SpeciesResult result={baseResult} />);
    expect(screen.getByText(/Skibbereen/i)).toBeInTheDocument();
  });

  it("renders a collapsible species list when count > 0", () => {
    render(<SpeciesResult result={baseResult} />);
    expect(screen.getByRole("group")).toBeInTheDocument();
    expect(screen.getByText(/show all 3 species/i)).toBeInTheDocument();
  });

  it("does not render species list when count is 0", () => {
    render(<SpeciesResult result={{ ...baseResult, species_count: 0, species_list: [] }} />);
    expect(screen.queryByText(/show all/i)).not.toBeInTheDocument();
  });

  it("renders species common names in the list", () => {
    render(<SpeciesResult result={baseResult} />);
    expect(screen.getByText("Mallard")).toBeInTheDocument();
    expect(screen.getByText("Hoopoe")).toBeInTheDocument();
  });

  it("renders scientific names in the list", () => {
    render(<SpeciesResult result={baseResult} />);
    expect(screen.getByText("Anas platyrhynchos")).toBeInTheDocument();
  });

  it("displays '0' when count is zero", () => {
    render(<SpeciesResult result={{ ...baseResult, species_count: 0, species_list: [] }} />);
    expect(screen.getByText("0")).toBeInTheDocument();
  });
});
