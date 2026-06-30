export interface Species {
  speciesCode: string;
  comName: string;
  sciName: string;
}

export interface PlaceResult {
  display_name: string;
  bbox: [number, number, number, number];
  center_lat: number;
  center_lon: number;
  geojson: Record<string, unknown> | null;
}

export interface SpeciesResult {
  town: string;
  species_count: number;
  species_list: Species[];
  bbox: [number, number, number, number];
  back_days: number;
}

export interface LeaderboardRow {
  rank: number;
  town: string;
  display_name: string;
  species_count: number | null;
  error?: string;
}

export interface LeaderboardResult {
  leaderboard: LeaderboardRow[];
  back_days: number;
}
