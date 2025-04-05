import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { registerUser } from '@/services/api';

function RegisterPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  // Optional: Add password confirmation field
  // const [confirmPassword, setConfirmPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);
  const navigate = useNavigate();

  const handleSubmit = async (event) => {
    event.preventDefault();
    // Optional: Add password confirmation validation
    // if (password !== confirmPassword) {
    //   setError("Passwords do not match.");
    //   return;
    // }
    if (!username || !password) {
      setError("Username and password are required.");
      return;
    }
    
    setIsLoading(true);
    setError(null);
    setSuccess(null);
    console.log('Register attempt with:', { username });

    try {
      const result = await registerUser(username, password);
      console.log("Registration API call successful:", result);
      setSuccess("Registration successful! Redirecting to login...");
      setUsername('');
      setPassword('');
      
      setTimeout(() => {
        navigate('/login');
      }, 2000);

    } catch (err) {
      const errorMessage = err.message || 'Registration failed. Please try again.';
      setError(errorMessage);
      console.error("Registration error:", err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex items-center justify-center min-h-screen bg-gray-100 dark:bg-gray-900">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle className="text-2xl">Register</CardTitle>
          <CardDescription>Create a new account.</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Choose a username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                placeholder="Choose a password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>
            {/* Optional: Add confirm password field here */}
            {error && <p className="text-sm text-red-500 dark:text-red-400">{error}</p>}
            {success && <p className="text-sm text-green-500 dark:text-green-400">{success}</p>}
            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? 'Registering...' : 'Register'}
            </Button>
          </form>
        </CardContent>
        <CardFooter className="text-sm flex justify-center">
          Already have an account?&nbsp;
          <Link to="/login" className="underline text-primary hover:text-primary/90">
            Login here
          </Link>
        </CardFooter>
      </Card>
    </div>
  );
}

export default RegisterPage; 