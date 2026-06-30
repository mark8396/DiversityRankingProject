import { render, screen } from "@testing-library/react";
import Navbar from "@/components/Navbar";

jest.mock("next/navigation", () => ({
  usePathname: jest.fn(),
}));

import { usePathname } from "next/navigation";
const mockUsePathname = usePathname as jest.Mock;

describe("Navbar", () => {
  it("renders Search, Leaderboard and Compare links", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /search/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /leaderboard/i })).toBeInTheDocument();
    expect(screen.getByRole("link", { name: /compare/i })).toBeInTheDocument();
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

  it("Compare link points to /compare", () => {
    mockUsePathname.mockReturnValue("/");
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /compare/i })).toHaveAttribute("href", "/compare");
  });

  it("applies active class to Compare link when on /compare", () => {
    mockUsePathname.mockReturnValue("/compare");
    render(<Navbar />);
    const compareLink = screen.getByRole("link", { name: /compare/i });
    expect(compareLink.className).toMatch(/active/);
  });

  it("does not apply active class to Search or Leaderboard when on /compare", () => {
    mockUsePathname.mockReturnValue("/compare");
    render(<Navbar />);
    expect(screen.getByRole("link", { name: /search/i }).className).not.toMatch(/active/);
    expect(screen.getByRole("link", { name: /leaderboard/i }).className).not.toMatch(/active/);
  });
});
