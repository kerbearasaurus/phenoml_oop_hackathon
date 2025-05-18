import React, { useState, useRef, useEffect } from 'react';
import SpeechRecognition, { useSpeechRecognition } from 'react-speech-recognition';
import { PaperAirplaneIcon, MicrophoneIcon, DocumentTextIcon, MapPinIcon, CurrencyDollarIcon, CalendarIcon, HomeModernIcon, ListBulletIcon, ShoppingCartIcon, ArrowPathIcon } from '@heroicons/react/24/solid';

function App() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const textareaRef = useRef(null);

  const {
    transcript,
    listening,
    resetTranscript,
    browserSupportsSpeechRecognition
  } = useSpeechRecognition();

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const adjustTextareaHeight = () => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px';
    }
  };

  useEffect(() => {
    if (transcript) {
      setInput(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    adjustTextareaHeight();
  }, [input]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;

    // Stop listening when a message is sent
    if (listening) {
      SpeechRecognition.stopListening();
    }

    const userMessage = input;
    setInput('');
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

  // Suggested prompts (long and short forms)
  const suggestionPairs = [
    {
      long: 'I need help creating a plan after going home from the hospital',
      short: 'Create post-hospital plan',
      icon: DocumentTextIcon,
    },
    {
      long: 'I need help getting directions to the pharmacy to pick up my prescribed medications',
      short: 'Get directions to pharmacy',
      icon: MapPinIcon,
    },
    {
      long: 'I need help explaining my medical bills',
      short: 'Explain medical bills',
      icon: CurrencyDollarIcon,
    },
    {
      long: "I need help scheduling a doctor's appointment",
      short: "Schedule doctor's appointment",
      icon: CalendarIcon,
    },
    {
      long: 'I need help creating a home health appointment',
      short: 'Create home health appointment',
      icon: HomeModernIcon,
    },
    {
      long: 'I need help pulling a list of all of my grandma\'s medications',
      short: 'Generate medication List',
      icon: ListBulletIcon,
    },
    {
      long: 'I need help creating a grocery list for my grandma',
      short: 'Create grocery list',
      icon: ShoppingCartIcon,
    },
    {
      long: 'I need help rescheduling a doctor\'s appointment',
      short: 'Reschedule appointment',
      icon: ArrowPathIcon,
    },
  ];

  return (
    <div className="min-h-screen bg-[#e0e6e5] flex flex-col items-center font-sans">
      {/* Header */}
      <div className="sticky top-0 z-20 bg-[#e0e6e5] w-full flex items-center justify-between px-6 pt-6 pb-2">
        {/* Hamburger */}
        <button className="p-2">
          <svg width="32" height="32" fill="none" viewBox="0 0 32 32">
            <rect y="7" width="32" height="2.5" rx="1.25" fill="#5b7d5a" />
            <rect y="15" width="32" height="2.5" rx="1.25" fill="#5b7d5a" />
            <rect y="23" width="32" height="2.5" rx="1.25" fill="#5b7d5a" />
          </svg>
        </button>
        <h1 className="text-3xl md:text-4xl font-bold text-[#5b7d5a] text-center flex-1">Hi, I am Carely.</h1>
        {/* Logo */}
        <div className="w-14 h-14 flex items-center justify-center">
          <svg width="56" height="56" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="28" cy="28" r="28" fill="#dbeee0" />
            <path d="M28 40C28 40 38 32 38 22C38 15.3726 32.6274 10 26 10C19.3726 10 14 15.3726 14 22C14 32 28 40 28 40Z" fill="#7bb86f" />
            <path d="M28 40C28 40 18 32 18 22C18 15.3726 23.3726 10 30 10C36.6274 10 42 15.3726 42 22C42 32 28 40 28 40Z" fill="#a3d18d" />
          </svg>
        </div>
      </div>

      {/* Sub-header */}
      <div className="w-full max-w-xl px-8 mt-2 mb-8">
        <div className="text-[#5b7d5a] text-lg">Sally,</div>
        <div className="text-[#5b7d5a] text-2xl md:text-3xl font-bold leading-tight mt-1 mb-4">
          How can I help you<br />this afternoon?
        </div>
      </div>

      {/* Suggestions (long form, shown initially) */}
      {messages.length === 0 && (
        <div className="flex flex-col items-center w-full max-w-xl space-y-4 mb-8">
          {suggestionPairs.map((s, i) => (
            <button
              key={i}
              className="bg-gray-400 bg-opacity-60 text-white text-sm font-semibold rounded-xl px-6 py-3 shadow-md w-full text-left flex items-start hover:bg-gray-500 transition-all"
              style={{ textShadow: '0 1px 2px rgba(0,0,0,0.08)' }}
              onClick={() => setInput(s.long)}
            >
              {s.icon && <s.icon className="h-5 w-5 mr-2 flex-shrink-0" />}
              <span className="flex-1 whitespace-normal">{s.long}</span>
            </button>
          ))}
        </div>
      )}

      {/* Chat Container */}
      {messages.length > 0 && (
        <div className="flex-1 overflow-y-auto p-4 space-y-4 w-full max-w-xl mb-8">
          {messages.map((message, index) => (
            <div
              key={index}
              className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
            >
              <div
                className={`max-w-[70%] rounded-lg p-4 ${
                  message.role === 'user'
                    ? 'bg-[#5b7d5a] text-white'
                    : 'bg-white text-gray-800 shadow-md'
                }`}
              >
                <p className="whitespace-pre-wrap">{message.content}</p>
              </div>
            </div>
          ))}
          {isLoading && (
            <div className="flex justify-start">
              <div className="bg-white text-gray-800 rounded-lg p-4 shadow-md">
                <div className="flex space-x-2">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
                </div>
              </div>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>
      )}

      {/* Shorthand Suggestions Row (after chat starts) */}
      {messages.length > 0 && (
        <div className="w-full max-w-xl flex flex-wrap gap-2 justify-center mb-4 px-4">
          {suggestionPairs.map((s, i) => (
            <button
              key={i}
              className="bg-gray-200 text-[#5b7d5a] text-sm font-semibold rounded-lg px-3 py-1 shadow hover:bg-gray-300 transition-all border border-gray-300 flex items-center text-left whitespace-normal"
              onClick={() => setInput(s.long)}
              type="button"
            >
              {s.icon && <s.icon className="h-4 w-4 mr-1 flex-shrink-0" />}
              <span className="flex-1">{s.short}</span>
            </button>
          ))}
        </div>
      )}

      {/* Input Form */}
      <form onSubmit={handleSubmit} className="sticky bottom-0 z-20 bg-[#e0e6e5] w-full max-w-xl mt-auto mb-8">
        <div className="flex items-center bg-[#d3d6d6] rounded-2xl px-6 py-4 shadow-inner">
          {browserSupportsSpeechRecognition && (
            <button
              type="button"
              onClick={toggleListening}
              disabled={isLoading}
              className="mr-4 focus:outline-none"
            >
              <MicrophoneIcon className={`h-10 w-10 ${listening ? 'text-[#5b7d5a]' : 'text-gray-400'}`} />
            </button>
          )}
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => {
              setInput(e.target.value);
              adjustTextareaHeight();
            }}
            placeholder="Type a message or record a message here"
            className="flex-1 bg-transparent text-lg text-gray-700 placeholder-gray-500 focus:outline-none resize-none"
            disabled={isLoading}
          />
          <button
            type="submit"
            disabled={isLoading}
            className="ml-4 focus:outline-none"
          >
            <PaperAirplaneIcon className="h-10 w-10 text-gray-400 hover:text-[#5b7d5a] transition-all" />
          </button>
        </div>
      </form>
    </div>
  );
}

export default App; 