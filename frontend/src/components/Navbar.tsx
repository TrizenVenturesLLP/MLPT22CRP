import { useNavigate, useLocation } from "react-router-dom";
import { Brain } from "lucide-react";

interface NavbarProps {
  onScrollToTools?: () => void;
}

const Navbar = ({ onScrollToTools }: NavbarProps) => {
  const navigate = useNavigate();
  const location = useLocation();
  const isHome = location.pathname === "/";

  const handleNavClick = (id: string) => {
    if (!isHome) {
      navigate(`/#${id}`);
    } else {
      const element = document.getElementById(id);
      if (element) {
        element.scrollIntoView({ behavior: "smooth" });
      }
    }
  };

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 bg-white/80 backdrop-blur-md border-b border-slate-100">
      <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
        <div 
          className="flex items-center gap-2 cursor-pointer" 
          onClick={() => navigate("/")}
        >
          <div className="w-8 h-8 rounded-lg bg-blue-600 flex items-center justify-center">
            <Brain className="w-5 h-5 text-white" />
          </div>
          <span className="font-bold text-slate-900 tracking-tight">CrimeWatch</span>
        </div>
        
        <div className="hidden md:flex items-center gap-8 text-sm font-medium text-slate-600">
          <button onClick={() => handleNavClick("features")} className="hover:text-blue-600 transition-colors">Features</button>
          <button onClick={() => handleNavClick("how-it-works")} className="hover:text-blue-600 transition-colors">How It Works</button>
          <button onClick={() => handleNavClick("tech-stack")} className="hover:text-blue-600 transition-colors">Tech Stack</button>
        </div>

        <button 
          onClick={isHome ? onScrollToTools : () => navigate("/")}
          className="text-sm font-semibold text-blue-600 border border-blue-600 px-5 py-2 rounded-full hover:bg-blue-50 transition-all"
        >
          {isHome ? "Launch Tools" : "Return Home"}
        </button>
      </div>
    </nav>
  );
};

export default Navbar;
