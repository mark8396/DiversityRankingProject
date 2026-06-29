import { render, screen } from "@testing-library/react";
import Navbar from "@/components/Navbar";

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(),
}));

import { usePathname } from "next/navigation";
const mockUsePathname = usePathname as jest.Mock;

describe("Navbar", () => {
  it("renders Search and Leaderboard links", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /search/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /leaderboard/i })).toBeInTheDocument();
  });

  it("applies active class to Search link when on /", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    const searchLink = screen.getByRole("link", { name: /search/i });
    expect(searchLink.className).toMatch(/active/);
  });

  it("does not apply active class to Leaderboard link when on /", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    const lbLink = screen.getByRole("link", { name: /leaderboard/i });
    expect(lbLink.className).not.toMatch(/active/);
  });

  it("applies active class to Leaderboard link when on /leaderboard", () => {
    mockUsePathname.mockReturnValue("/leaderboard");
    render(<Navbar />);
    const lbLink = screen.getByRole("link", { name: /leaderboard/i });
    expect(lbLink.className).toMatch(/active/);
  });

  it("does not apply active class to Search link when on /leaderboard", () => {
    mockUsePathname.mockReturnValue("/leaderboard");
    render(<Navbar />);
    const searchLink = screen.getByRole("link", { name: /search/i });
    expect(searchLink.className).not.toMatch(/active/);
  });

  it("Search link points to /", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /search/i })).toHaveAttribute("href", "/");
  });

  it("Leaderboard link points to /leaderboard", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /leaderboard/i })).toHaveAttribute("href", "/leaderboard");
  });
});
