import { useState } from 'react';
import { WizardProvider } from './app/WizardProvider';
import ReleaseWizard from './pages/ReleaseWizard';
import Dashboard from './pages/Dashboard';

function App() {
  const [currentPage, setCurrentPage] = useState<'wizard' | 'dashboard'>('wizard');

  return (
    <WizardProvider>
      <div className="min-h-screen bg-gray-50">
        {/* Navigation */}
        <nav className="bg-white shadow-sm border-b">
          <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div className="flex justify-between h-16">
              <div className="flex">
                <div className="flex-shrink-0 flex items-center">
                  <h1 className="text-xl font-bold text-gray-900">AP Studios</h1>
                </div>
                <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
                  <button
                    onClick={() => setCurrentPage('wizard')}
                    className={`${
                      currentPage === 'wizard'
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                  >
                    Nuevo Release
                  </button>
                  <button
                    onClick={() => setCurrentPage('dashboard')}
                    className={`${
                      currentPage === 'dashboard'
                        ? 'border-indigo-500 text-indigo-600'
                        : 'border-transparent text-gray-500 hover:border-gray-300 hover:text-gray-700'
                    } inline-flex items-center px-1 pt-1 border-b-2 text-sm font-medium`}
                  >
                    Dashboard
                  </button>
                </div>
              </div>
            </div>
          </div>
        </nav>

        {/* Main content */}
        <main>
          {currentPage === 'wizard' ? <ReleaseWizard /> : <Dashboard />}
        </main>
      </div>
    </WizardProvider>
  );
}

export default App;