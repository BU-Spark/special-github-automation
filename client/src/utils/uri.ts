export const API_URL: string = process.env.NODE_ENV === 'production'
        ? 'https://special-github-automation-production.up.railway.app'
        : 'http://localhost:5000';