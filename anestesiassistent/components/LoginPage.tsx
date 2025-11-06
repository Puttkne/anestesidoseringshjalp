import React from 'react';
import { Syringe, Eye, EyeOff } from 'lucide-react';

interface Props {
  onLogin: (username: string) => void;
}

export const LoginPage: React.FC<Props> = ({ onLogin }) => {
  const [username, setUsername] = React.useState('');
  const [password, setPassword] = React.useState('');
  const [showPassword, setShowPassword] = React.useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (username.trim()) {
      onLogin(username.trim());
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-background px-4">
      <div className="w-full max-w-sm space-y-6">
        <div className="text-center">
            <div className="inline-block bg-primary p-3 rounded-full mb-4">
              <Syringe className="text-white h-8 w-8" />
            </div>
          <h1 className="text-2xl font-bold text-foreground">
            Anestesi-assistent
          </h1>
        </div>

        <form onSubmit={handleSubmit} className="bg-white p-8 rounded-lg shadow-sm border space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium text-foreground mb-1">
              Användarnamn
            </label>
            <input
              id="username"
              type="text"
              placeholder="Ange ditt användarnamn"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary"
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-foreground mb-1">
              Lösenord
            </label>
            <div className="relative">
              <input
                id="password"
                type={showPassword ? "text" : "password"}
                placeholder="Ange ditt lösenord"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                className="w-full px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-primary pr-10"
              />
              <button
                type="button"
                onClick={() => setShowPassword(!showPassword)}
                className="absolute right-2 top-1/2 -translate-y-1/2 text-muted-foreground"
              >
                {showPassword ? <EyeOff className="h-5 w-5" /> : <Eye className="h-5 w-5" />}
              </button>
            </div>
          </div>

          <button type="submit" className="w-full bg-primary text-white py-2 rounded-md">
            Logga in
          </button>
        </form>

      </div>
    </div>
  );
};