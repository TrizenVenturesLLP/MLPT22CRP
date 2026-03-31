import { useState } from "react";
import HotspotDetection from "@/components/HotspotDetection";
import Navbar from "@/components/Navbar";
import TreeVisualization from "@/components/TreeVisualization";
import MapSection from "@/components/MapSection";

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
  ranges: {
    High: string;
    Medium: string;
    Low: string;
  };
  message: string;
  state: string;
}

const HotspotDetectionPage = () => {
  const [results, setResults] = useState<HotspotResults | null>(null);

  return (
    <div className="min-h-screen bg-white py-12 px-4 pt-24 pb-24">
      <Navbar />
      <div className="max-w-5xl mx-auto">
        <div className="space-y-12">
          <HotspotDetection onResult={setResults} />
          
          <div className="grid lg:grid-cols-2 gap-12 items-start">
            <TreeVisualization results={results} />
            <MapSection results={results} />
          </div>
        </div>
      </div>
    </div>
  );
};

export default HotspotDetectionPage;
