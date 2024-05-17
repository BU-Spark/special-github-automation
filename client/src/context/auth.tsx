import { Box, Button, CircularProgress, Input } from '@mui/material';
import React, { createContext, useState, useContext, useCallback, ReactNode, useEffect } from 'react';
import { API_URL } from '../utils/uri';

interface AuthContextType {
    credentials: { username: string, password: string };
    authenticate: () => void;
    _fetch: (url: string, options: { method: string, body?: any }) => Promise<any>;
    authenticated: boolean;
}

const AuthContext = createContext<AuthContextType>({
    credentials: { username: '', password: '' },
    authenticate: () => {},
    _fetch: async () => {},
    authenticated: false,
});

export const useAuth = () => useContext(AuthContext);

export function AuthProvider({ children }: { children: ReactNode }) {
    const [loading, setLoading] = useState(true);
    const [credentials, setCredentials] = useState({ username: '', password: '' });
    const [authenticated, setAuthenticated] = useState(false);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        setLoading(true);
        const authenticated = localStorage.getItem('authenticated');
        const username = localStorage.getItem('username');
        const password = localStorage.getItem('password');
        if (authenticated === 'true' && username && password) {
            setCredentials({ username, password });
            setAuthenticated(true);
        }
        setLoading(false);
    });

    async function authenticate() {
        if (!credentials.username || !credentials.password) {
            setError('Please enter your username and password');
            return;
        }

        let result = _fetch(`${API_URL}/authenticate`, {
            method: 'POST',
        }).then(() => {
            setAuthenticated(true);
            // update local storage LOL insecure
            localStorage.setItem('authenticated', 'true');
            localStorage.setItem('username', credentials.username);
            localStorage.setItem('password', credentials.password);
        }).catch((error) => {
            setError(error.message);
        });
    };

    const _fetch = useCallback(async (url: string, options: { method: string, body?: any }) => {
        const headers = new Headers({
            'Authorization': 'Basic ' + btoa(credentials.username + ":" + credentials.password),
            'Content-Type': 'application/json'
        });
    
        const config = {
            method: options.method,
            headers: headers,
            body: options.body ? options.body : null,
        };
    
        console.log('fetching', url, config);
    
        try {
            const response = await fetch(url, config);
            if (!response.ok) {
                const errorResponse = await response.text();
                throw new Error('Request failed: ' + errorResponse);
            }
            console.log('response', response);
            return await response;
        } catch (error) {
            console.error('Error:', error);
            throw error;
        }
    }, [credentials]);
    

    return (
        <AuthContext.Provider value={{ authenticate, _fetch, authenticated, credentials }}>
            { loading ? <CircularProgress /> : (
                authenticated ? children :
                <Box sx={{ width: '100%', display: 'flex', flexDirection: 'column' }}>
                    <h1>SPARK! AUTOMATIONS</h1>
                    <h4>authenticate to use automations</h4>
                    <Input 
                        placeholder="username" 
                        value={credentials.username}
                        color='primary'
                        
                        sx={{
                            color: 'white',
                            '&::before': { borderBottom: '1px solid white' },
                            width: '400px',
                        }}
                        onChange={e => setCredentials({ ...credentials, username: e.target.value })}
                    />
                    <Input 
                        placeholder="password" 
                        value={credentials.password}
                        color='primary'
                        sx={{
                            color: 'white',
                            '&::before': { borderBottom: '1px solid white' },
                            width: '400px',
                            marginTop: 2
                        }}
                        onChange={e => setCredentials({ ...credentials, password: e.target.value })}
                    />
                    <Button 
                        variant='contained' 
                        color='primary'
                        sx={{ width: '400px', marginTop: 2 }}
                        onClick={authenticate}
                    > 
                        authenticate
                    </Button>
                    { error && <h4 style={{ color: 'red' }}>{error}</h4> }
                </Box>
            )}
        </AuthContext.Provider>
    );
};
