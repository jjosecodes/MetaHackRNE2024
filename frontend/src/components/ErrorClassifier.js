// src/components/ErrorClassifier.js

import React, { useState } from 'react';
import axios from 'axios';

function ErrorClassifier() {
  const [inputText, setInputText] = useState('');
  const [recommendations, setRecommendations] = useState([]);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    try {
      const response = await axios.post('/classify_error', {
        error_message: inputText,
      });
      setRecommendations(response.data.recommendations);
      setError('');
    } catch (err) {
      setError('An error occurred while fetching data from the API.');
      setRecommendations([]);
    }
  };

  return (
    <div className="flex h-full">
      {/* Left Side Input */}
      <div className="w-1/2 p-4 border-r">
        <h2 className="text-xl font-bold mb-4">Input Error Message</h2>
        <form onSubmit={handleSubmit} className="h-full flex flex-col">
          <textarea
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Enter error message here..."
            className="flex-grow p-2 border rounded"
          />
          <button
            type="submit"
            className="mt-4 p-2 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            Submit
          </button>
        </form>
      </div>

      {/* Right Side Output */}
      <div className="w-1/2 p-4">
        <h2 className="text-xl font-bold mb-4">Recommendations</h2>
        {error ? (
          <p className="text-red-500">{error}</p>
        ) : (
          <ul className="list-disc pl-5">
            {recommendations.map((rec, index) => (
              <li key={index}>{rec}</li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}

export default ErrorClassifier;
