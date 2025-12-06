import React, { useContext, useState } from 'react';
import { useGoogleLogin } from '@react-oauth/google';
import axios from 'axios';
import { AuthContext } from '../context/AuthContext';

export default function LoginButton() {
  const { login } = useContext(AuthContext);
  const [error, setError] = useState('');
  const clientId = import.meta.env.VITE_GOOGLE_CLIENT_ID || '';

  // Check if Google OAuth is properly configured
  const isOAuthConfigured = clientId && clientId !== 'placeholder';

  // Always call the hook (hooks must be called unconditionally)
  // But only use it if OAuth is configured
  const loginAction = useGoogleLogin({
    onSuccess: async (tokenResponse) => {
      if (!isOAuthConfigured) {
        setError('OAuth not configured');
        return;
      }
      try {
        const res = await axios.get('https://www.googleapis.com/oauth2/v3/userinfo', {
          headers: { Authorization: `Bearer ${tokenResponse.access_token}` },
        });
        login(res.data);
        setError('');
      } catch (err) {
        console.error('Error fetching user info: ', err);
        setError('Login Failed');
      }
    },
    onError: () => setError('Login Failed'),
  });

  const handleClick = () => {
    if (!isOAuthConfigured) {
      setError('OAuth not configured. Please set VITE_GOOGLE_CLIENT_ID in .env');
      return;
    }
    loginAction();
  };

  return (
    <div>
      <button
        onClick={handleClick}
        disabled={!isOAuthConfigured}
        className={`w-full mt-2 px-3 py-1.5 rounded text-sm transition-colors ${
          isOAuthConfigured
            ? 'bg-teal-600 hover:bg-teal-700'
            : 'bg-gray-600 text-gray-400 cursor-not-allowed'
        }`}
      >
        {isOAuthConfigured ? 'Login / Sign Up' : 'OAuth Not Configured'}
      </button>
      {error && <p className="text-red-400 text-xs mt-1">{error}</p>}
    </div>
  );
}
