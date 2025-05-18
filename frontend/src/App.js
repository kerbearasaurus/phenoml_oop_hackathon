import React, { useState, useRef, useEffect } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { PaperAirplaneIcon, MicrophoneIcon, DocumentTextIcon, MapPinIcon, CurrencyDollarIcon, CalendarIcon, HomeModernIcon, ListBulletIcon, ShoppingCartIcon, ArrowPathIcon } from '@heroicons/react/24/solid';
import { Routes, Route, Navigate, useNavigate } from 'react-router-dom';

import LoginScreen from './LoginScreen';
import MainAppUI from './MainAppUI';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(() => {
    return localStorage.getItem('isLoggedIn') === 'true';
  });

  const navigate = useNavigate();

  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  };

  const handleSubmit = async (e, inputValue) => {
    e.preventDefault();
    if (!inputValue.trim()) return;

    if (listening) {
      SpeechRecognition.stopListening();
    }

    const userMessage = inputValue;
    setMessages(prev => [...prev, { role: 'user', content: userMessage }]);
    setIsLoading(true);
    try {
      const response = await fetch('http://localhost:5000/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Access-Control-Allow-Origin': '*'
        },
        body: JSON.stringify({ message: userMessage }),
      });
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      const data = await response.json();
      setMessages(prev => [...prev, { role: 'assistant', content: data.response }]);
    } catch (error) {
      console.error('Error:', error);
      setMessages(prev => [...prev, { role: 'assistant', content: `Error: ${error.message}` }]);
    } finally {
      setIsLoading(false);
    }
  };

  const toggleListening = () => {
    if (listening) {
      SpeechRecognition.stopListening();
    } else {
      resetTranscript();
      SpeechRecognition.startListening({ continuous: true });
    }
  };

  const suggestionPairs = [
    {
      long: 'I need help getting directions to the pharmacy to pick up my brother\'s medications',
      short: 'Get directions to pharmacy',
      icon: MapPinIcon,
    },
    {
      long: "I need help scheduling a doctor's appointment for my brother",
      short: "Schedule doctor's appointment",
      icon: CalendarIcon,
    },
    // {
    //   long: 'I need help creating a home health appointment for my brother',
    //   short: 'Create home health appointment',
    //   icon: HomeModernIcon,
    // },
    {
      long: 'I need help pulling a list of all of my brother\'s medications',
      short: 'Generate medication List',
      icon: ListBulletIcon,
    },
    {
      long: 'I need help creating a grocery list for my brother',
      short: 'Create grocery list',
      icon: ShoppingCartIcon,
    },
    {
      long: 'I need help rescheduling a doctor\'s appointment for my brother',
      short: 'Reschedule appointment',
      icon: ArrowPathIcon,
    },
  ];

  const ProtectedRoute = ({ element }) => {
    return isLoggedIn ? element : <Navigate to="/login" replace />;
  };

  return (
    <div className="min-h-screen bg-[#e0e6e5] flex flex-col items-center font-sans">
      <div className="sticky top-0 z-20 bg-[#e0e6e5] w-full flex items-center justify-between px-6 pt-6 pb-2">
        <button className="p-2">
          <svg width="32" height="32" fill="none" viewBox="0 0 32 32">
            <rect y="7" width="32" height="2.5" rx="1.25" fill="#5b7d5a" />
            <rect y="15" width="32" height="2.5" rx="1.25" fill="#5b7d5a" />
            <rect y="23" width="32" height="2.5" rx="1.25" fill="#5b7d5a" />
          </svg>
        </button>

        <div className="flex items-center space-x-4">
          <img src="/static/hospital_logo.png" alt="University Hospital Logo" className="h-12 w-auto" />
          <img src="/static/carely_logo.png" alt="Carely App Logo" className="h-12 w-auto" />

          {isLoggedIn && (
            <h1 className="text-3xl md:text-4xl font-bold text-[#5b7d5a]">Hi, I am Carely.</h1>
          )}

        </div>

        <div className="w-8"></div>
      </div>

      <Routes>
        <Route path="/login" element={
          <LoginScreen onLogin={() => {
            setIsLoggedIn(true);
            localStorage.setItem('isLoggedIn', 'true');
            navigate('/');
          }} />
        } />
        <Route
          path="/"
          element={
            <ProtectedRoute
              element={
                <MainAppUI
                  messages={messages}
                  isLoading={isLoading}
                  messagesEndRef={messagesEndRef}
                  textareaRef={textareaRef}
                  suggestionPairs={suggestionPairs}
                  transcript={transcript}
                  listening={listening}
                  browserSupportsSpeechRecognition={browserSupportsSpeechRecognition}
                  handleSubmit={handleSubmit}
                  adjustTextareaHeight={adjustTextareaHeight}
                  toggleListening={toggleListening}
                />
              }
            />
          }
        />
        <Route path="*" element={<Navigate to={isLoggedIn ? "/" : "/login"} replace />} />
      </Routes>
    </div>
  );
}

export default App; 