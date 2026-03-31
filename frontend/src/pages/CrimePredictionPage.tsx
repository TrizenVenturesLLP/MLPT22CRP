import CrimePrediction from "@/components/CrimePrediction";
import Navbar from "@/components/Navbar";

const CrimePredictionPage = () => {
  return (
    <div className="min-h-screen bg-white py-12 px-4 pt-24">
      <Navbar />
      <div className="max-w-5xl mx-auto">
        <div className="space-y-12">
          <CrimePrediction />
        </div>
      </div>
    </div>
  );
};

export default CrimePredictionPage;
