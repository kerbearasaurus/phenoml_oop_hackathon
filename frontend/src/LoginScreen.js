import React, { useState } from 'react';

function LoginScreen({ onLogin }) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  React.useEffect(() => {
    localStorage.setItem('isLoggedIn', 'false');
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    // In a real app, you would validate credentials here
    // For this fake login, we just call onLogin
    onLogin();
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-[#e0e6e5]">
      <div className="bg-white p-8 rounded-lg shadow-md w-96">
        <h2 className="text-2xl font-bold text-center text-[#5b7d5a] mb-6">SSO Login</h2>
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label htmlFor="username" className="block text-gray-700 text-sm font-bold mb-2">Username</label>
            <input
              type="text"
              id="username"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
            />
          </div>
          <div className="mb-6">
            <label htmlFor="password" className="block text-gray-700 text-sm font-bold mb-2">Password</label>
            <input
              type="password"
              id="password"
              className="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 mb-3 leading-tight focus:outline-none focus:shadow-outline"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
          </div>
          <div className="flex items-center justify-between">
            <button
              type="submit"
              className="bg-[#5b7d5a] hover:bg-[#7bb86f] text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline w-full"
            >
              Sign In
            </button>
          </div>
          {/* Forgot password link */}
          <div className="text-center mt-4">
            <a href="#" className="inline-block align-baseline font-bold text-sm text-[#5b7d5a] hover:text-[#7bb86f]" onClick={(e) => e.preventDefault()}>
              Forgot your password?
            </a>
          </div>
        </form>
      </div>
    </div>
  );
}

export default LoginScreen; 