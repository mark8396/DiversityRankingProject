const mockMapInstance = {
  setView: jest.fn().mockReturnThis(),
  removeLayer: jest.fn(),
  fitBounds: jest.fn(),
};

const mockLayerInstance = {
  addTo: jest.fn().mockReturnThis(),
  getBounds: jest.fn().mockReturnValue([[51.5, -9.3], [51.6, -9.2]]),
};

const L = {
  map: jest.fn(() => mockMapInstance),
  tileLayer: jest.fn(() => ({ addTo: jest.fn() })),
  rectangle: jest.fn(() => mockLayerInstance),
  geoJSON: jest.fn(() => mockLayerInstance),
  // exposed so tests can assert on map/layer calls without re-importing
  mockMapInstance,
  mockLayerInstance,
};

module.exports = L;
