// src/App.js

import React, { useState } from 'react';
import ErrorClassifier from './components/ErrorClassifier';
import CommandTranslator from './components/CommandTranslator';

function App() {
  const [selectedTool, setSelectedTool] = useState('classifier');

  return (
    <div className="h-screen flex flex-col">
      {/* Navigation Bar */}
      <nav className="bg-gray-800 text-white p-4 flex justify-center">
        <button
          onClick={() => setSelectedTool('classifier')}
          className={`mx-2 px-4 py-2 rounded ${
            selectedTool === 'classifier' ? 'bg-blue-600' : 'bg-gray-700'
          }`}
        >
          Error Classifier
        </button>
        <button
          onClick={() => setSelectedTool('translator')}
          className={`mx-2 px-4 py-2 rounded ${
            selectedTool === 'translator' ? 'bg-blue-600' : 'bg-gray-700'
          }`}
        >
          Command Translator
        </button>
        {/* Add more tools as needed */}
      </nav>

      {/* Content */}
      <div className="flex-grow">
        {selectedTool === 'classifier' && <ErrorClassifier />}
        {selectedTool === 'translator' && <CommandTranslator />}
      </div>
    </div>
  );
}

export default App;
