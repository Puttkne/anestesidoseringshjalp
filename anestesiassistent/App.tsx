import { useState } from "react";
import { LoginPage } from "./components/LoginPage";
import { Dashboard } from "./components/Dashboard";
import { Toaster } from "./components/ui/sonner";

interface User {
  username: string;
  isAdmin: boolean;
}

export default function App() {
  const [user, setUser] = useState<User | null>(null);

  const handleLogin = (username: string) => {
    // Mock admin check - in real app this would be validated by backend
    const isAdmin = username.toLowerCase().includes("admin");
    
    setUser({
      username,
      isAdmin,
    });
  };

  const handleLogout = () => {
    setUser(null);
  };

  return (
    <>
      {user ? (
        <Dashboard
          username={user.username}
          isAdmin={user.isAdmin}
          onLogout={handleLogout}
        />
      ) : (
        <LoginPage onLogin={handleLogin} />
      )}
      <Toaster />
    </>
  );
}
