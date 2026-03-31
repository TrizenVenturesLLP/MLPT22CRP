const Footer = () => {
  return (
    <footer className="py-12 px-4 border-t border-slate-100 bg-white">
      <div className="max-w-6xl mx-auto flex flex-col md:flex-row justify-between items-center gap-6">
        <p className="text-slate-400 text-sm">
          © 2026 CrimeWatch Analytics. All rights reserved.
        </p>
        <div className="flex gap-8 text-sm text-slate-400">
          <a href="#" className="hover:text-blue-600 transition-colors">Privacy Policy</a>
          <a href="#" className="hover:text-blue-600 transition-colors">Terms of Service</a>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
