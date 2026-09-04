export interface WardRef {
  ward: string
  district: string
  lat: number
  lng: number
  population: number
}

export const WARDS: WardRef[] = [
  { ward: "Ward 12 - Green Park", district: "South Delhi", lat: 28.5588, lng: 77.2064, population: 42000 },
  { ward: "Ward 14 - Malviya Nagar", district: "South Delhi", lat: 28.5285, lng: 77.2124, population: 51000 },
  { ward: "Ward 9 - Saket", district: "South Delhi", lat: 28.5245, lng: 77.2107, population: 38500 },
  { ward: "Ward 21 - Hauz Khas", district: "South Delhi", lat: 28.5494, lng: 77.2001, population: 33200 },
  { ward: "Ward 33 - Lajpat Nagar", district: "South East Delhi", lat: 28.5677, lng: 77.2431, population: 47800 },
  { ward: "Ward 5 - Kalkaji", district: "South East Delhi", lat: 28.5355, lng: 77.2588, population: 55600 },
  { ward: "Ward 41 - Vasant Kunj", district: "South West Delhi", lat: 28.5203, lng: 77.1588, population: 61200 },
  { ward: "Ward 18 - Dwarka Sector 12", district: "South West Delhi", lat: 28.5921, lng: 77.0460, population: 72300 },
]
