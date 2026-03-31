import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import { MapPin } from "lucide-react";
import { MapContainer, TileLayer, Marker, Popup, useMap } from "react-leaflet";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

// Fix for default marker icons in Leaflet with React/Vite
import icon from "leaflet/dist/images/marker-icon.png";
import iconShadow from "leaflet/dist/images/marker-shadow.png";

let DefaultIcon = L.icon({
  iconUrl: icon,
  shadowUrl: iconShadow,
  iconSize: [25, 41],
  iconAnchor: [12, 41],
});

L.Marker.prototype.options.icon = DefaultIcon;

interface DistrictData {
  District: string;
  "Crime Count": number;
  lat: number;
  lng: number;
}

interface HotspotResults {
  High: DistrictData[];
  Medium: DistrictData[];
  Low: DistrictData[];
  state: string;
}

interface MapSectionProps {
  results: HotspotResults | null;
}

// Helper to create custom colored icons
const createIcon = (color: string) => {
  return L.divIcon({
    className: "custom-div-icon",
    html: `<div style="background-color: ${color}; width: 12px; height: 12px; border-radius: 50%; border: 2px solid white; box-shadow: 0 0 10px ${color}80;"></div>`,
    iconSize: [12, 12],
    iconAnchor: [6, 6],
  });
};

const icons = {
  high: createIcon("#ef4444"),
  medium: createIcon("#f59e0b"),
  low: createIcon("#10b981"),
};

// Component to handle map view updates
const MapUpdater = ({ center }: { center: [number, number] }) => {
  const map = useMap();
  useEffect(() => {
    map.flyTo(center, 7, { animate: true, duration: 1.5 });
  }, [center, map]);
  return null;
};

const MapSection = ({ results }: MapSectionProps) => {
  const [center, setCenter] = useState<[number, number]>([20.5937, 78.9629]); // India center

  useEffect(() => {
    if (results) {
      const allDistricts = [...results.High, ...results.Medium, ...results.Low];
      if (allDistricts.length > 0) {
        const avgLat = allDistricts.reduce((sum, d) => sum + d.lat, 0) / allDistricts.length;
        const avgLng = allDistricts.reduce((sum, d) => sum + d.lng, 0) / allDistricts.length;
        setCenter([avgLat, avgLng]);
      }
    }
  }, [results]);

  return (
    <motion.div
      initial={{ opacity: 0, y: 30 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
      className="p-8 rounded-3xl bg-white border border-slate-100 shadow-sm min-h-[500px]"
    >
      <div className="flex items-center gap-4 mb-8">
        <div className="w-12 h-12 rounded-2xl bg-blue-50 flex items-center justify-center">
          <MapPin className="w-6 h-6 text-blue-600" />
        </div>
        <h3 className="text-2xl font-bold text-slate-900">Crime Hotspot Map</h3>
      </div>

      <div className="relative w-full aspect-[4/3] bg-slate-50 border border-slate-100 rounded-2xl overflow-hidden mb-8 z-0">
        {!results ? (
          <div className="absolute inset-0 flex flex-col items-center justify-center text-slate-400 bg-slate-50/50">
            <MapPin className="w-10 h-10 mb-4 opacity-20" />
            <p className="text-sm font-medium">Analyze hotspots to visualize on map</p>
          </div>
        ) : (
          <MapContainer 
            center={center} 
            zoom={6} 
            style={{ height: "100%", width: "100%" }}
            zoomControl={false}
          >
            <TileLayer
              attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
              url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
            />
            <MapUpdater center={center} />
            
            {results.High.map((d) => (
              <Marker key={d.District} position={[d.lat, d.lng]} icon={icons.high}>
                <Popup>
                  <div className="text-center">
                    <div className="text-sm font-bold">{d.District}</div>
                    <div className="text-[10px] text-red-500 font-bold uppercase tracking-wider">High Risk</div>
                  </div>
                </Popup>
              </Marker>
            ))}
            {results.Medium.map((d) => (
              <Marker key={d.District} position={[d.lat, d.lng]} icon={icons.medium}>
                <Popup>
                  <div className="text-center">
                    <div className="text-sm font-bold">{d.District}</div>
                    <div className="text-[10px] text-amber-500 font-bold uppercase tracking-wider">Medium Risk</div>
                  </div>
                </Popup>
              </Marker>
            ))}
            {results.Low.map((d) => (
              <Marker key={d.District} position={[d.lat, d.lng]} icon={icons.low}>
                <Popup>
                  <div className="text-center">
                    <div className="text-sm font-bold">{d.District}</div>
                    <div className="text-[10px] text-emerald-500 font-bold uppercase tracking-wider">Low Risk</div>
                  </div>
                </Popup>
              </Marker>
            ))}
          </MapContainer>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center justify-center gap-8 text-[10px] font-bold uppercase tracking-widest bg-slate-50 py-3 rounded-xl border border-slate-100">
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-red-500 shadow-[0_0_8px_rgba(239,68,68,0.4)]" />
          <span className="text-slate-500">High</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-amber-500 shadow-[0_0_8px_rgba(245,158,11,0.4)]" />
          <span className="text-slate-500">Medium</span>
        </div>
        <div className="flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.4)]" />
          <span className="text-slate-500">Low</span>
        </div>
      </div>
    </motion.div>
  );
};

export default MapSection;
