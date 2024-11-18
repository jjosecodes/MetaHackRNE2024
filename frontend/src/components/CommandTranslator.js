// src/components/CommandTranslator.js

import React, { useState } from 'react';
import axios from 'axios';

function CommandTranslator() {
  const [sourceSystem, setSourceSystem] = useState('Cisco');
  const [targetSystem, setTargetSystem] = useState('Arista');
  const [sourceCommand, setSourceCommand] = useState('');
  const [translatedCommand, setTranslatedCommand] = useState('');
  const [error, setError] = useState('');

  const handleTranslate = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/translate_command', {
        source_system: sourceSystem,
        target_system: targetSystem,
        source_command: sourceCommand,
      });
      setTranslatedCommand(response.data.translated_command);
      setError('');
    } catch (err) {
      setError('Translation not found.');
      setTranslatedCommand('');
    }
  };

  return (
    <div className="flex h-full">
      {/* Left Side Input */}
      <div className="w-1/2 p-4 border-r">
        <h2 className="text-xl font-bold mb-4">Input Command</h2>
        <form onSubmit={handleTranslate} className="h-full flex flex-col">
          <div className="mb-2">
            <label className="block mb-1">Source System:</label>
            <select
              value={sourceSystem}
              onChange={(e) => setSourceSystem(e.target.value)}
              className="p-2 border rounded w-full"
            >
              <option value="Cisco">Cisco</option>
              <option value="Arista">Arista</option>
              {/* Add more options as needed */}
            </select>
          </div>
          <div className="mb-2">
            <label className="block mb-1">Target System:</label>
            <select
              value={targetSystem}
              onChange={(e) => setTargetSystem(e.target.value)}
              className="p-2 border rounded w-full"
            >
              <option value="Arista">Arista</option>
              <option value="Cisco">Cisco</option>
              {/* Add more options as needed */}
            </select>
          </div>
          <textarea
            value={sourceCommand}
            onChange={(e) => setSourceCommand(e.target.value)}
            placeholder="Enter source command..."
            className="flex-grow p-2 border rounded"
          />
          <button
            type="submit"
            className="mt-4 p-2 bg-green-500 text-white rounded hover:bg-green-600"
          >
            Translate
          </button>
        </form>
      </div>

      {/* Right Side Output */}
      <div className="w-1/2 p-4">
        <h2 className="text-xl font-bold mb-4">Translated Command</h2>
        {error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          <pre className="whitespace-pre-wrap">{translatedCommand}</pre>
        )}
      </div>
    </div>
  );
}

export default CommandTranslator;
