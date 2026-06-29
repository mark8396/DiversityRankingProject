const L = {
  map: () => ({
    setView: () => ({ on: () => {} }),
    removeLayer: () => {},
    fitBounds: () => {},
  }),
  tileLayer: () => ({ addTo: () => {} }),
  rectangle: () => ({ addTo: () => {} }),
};

module.exports = L;
