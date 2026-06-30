import { render, waitFor } from "@testing-library/react";
import Map from "@/components/Map";

const L = require("leaflet");

const BBOX: [number, number, number, number] = [51.53, 51.57, -9.29, -9.21];
const GEOJSON = { type: "Polygon", coordinates: [[[0, 0], [1, 0], [1, 1], [0, 1], [0, 0]]] };

beforeEach(() => {
  jest.clearAllMocks();
});

describe("Map", () => {
  it("renders without crashing when bbox and geojson are null", () => {
    render(<Map bbox={null} geojson={null} />);
    expect(L.rectangle).not.toHaveBeenCalled();
    expect(L.geoJSON).not.toHaveBeenCalled();
  });

  it("draws rectangle when bbox is provided and geojson is null", async () => {
    render(<Map bbox={BBOX} geojson={null} />);
    await waitFor(() => expect(L.rectangle).toHaveBeenCalledTimes(1));
    expect(L.geoJSON).not.toHaveBeenCalled();
  });

  it("draws geoJSON layer when geojson is provided", async () => {
    render(<Map bbox={BBOX} geojson={GEOJSON} />);
    await waitFor(() => expect(L.geoJSON).toHaveBeenCalledTimes(1));
    expect(L.geoJSON).toHaveBeenCalledWith(
      GEOJSON,
      expect.objectContaining({ style: expect.any(Object) })
    );
    expect(L.rectangle).not.toHaveBeenCalled();
  });

  it("removes old layer before drawing new one", async () => {
    const { rerender } = render(<Map bbox={BBOX} geojson={null} />);
    await waitFor(() => expect(L.rectangle).toHaveBeenCalledTimes(1));

    const NEW_BBOX: [number, number, number, number] = [53.0, 53.5, -7.0, -6.0];
    rerender(<Map bbox={NEW_BBOX} geojson={null} />);
    await waitFor(() => expect(L.rectangle).toHaveBeenCalledTimes(2));
    expect(L.mockMapInstance.removeLayer).toHaveBeenCalled();
  });

  it("falls back to rectangle on both renders when geojson is always null", async () => {
    const { rerender } = render(<Map bbox={BBOX} geojson={null} />);
    await waitFor(() => expect(L.rectangle).toHaveBeenCalledTimes(1));

    const NEW_BBOX: [number, number, number, number] = [53.0, 53.5, -7.0, -6.0];
    rerender(<Map bbox={NEW_BBOX} geojson={null} />);
    await waitFor(() => expect(L.rectangle).toHaveBeenCalledTimes(2));
    expect(L.geoJSON).not.toHaveBeenCalled();
  });
});
