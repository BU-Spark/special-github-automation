import React, { createContext, useState, useContext, useCallback, ReactNode } from 'react';
import { API_URL } from "../utils/uri";
import { useAuth } from './auth';
interface FxnContextType {
    _info: () => Promise<any>;
    _csv: () => Promise<any>;
    _csv_projects: () => Promise<any>;
    _projects: () => Promise<any>;
    _git_repos: () => Promise<any>;
}

export const FxnContext = createContext<FxnContextType>({
    _info: async () => {},
    _csv: async () => {},
    _csv_projects: async () => {},
    _projects: async () => {},
    _git_repos: async () => {},
});

export const useFxns = () => useContext(FxnContext);

export function FxnProvider({ children }: { children: React.ReactNode }) {

    const { _fetch } = useAuth();

    async function _info() {
        const rows = [];
        const response = await _fetch(`${API_URL}/get_info`, { method: 'GET' });
        const data = await response.json();
        //console.log(data);

        const info = data['info'];
        for (const i in info) {
            //console.log(info[i]);
            const row = {
                id: i,
                buid: info[i]['buid'],
                name: info[i]['name'],
                email: info[i]['email'],
                github: info[i]['github'],
                semester: info[i]['semester'],
                project: info[i]['project_name'],
                github_url: info[i]['github_url'],
                status: info[i]['status'],
            };
            rows.push(row);
        }
        return rows;
    }

    async function _csv() {
        const rows = [];
        const response = await _fetch(`${API_URL}/get_csv`, { method: 'GET' });
        const data = await response.json();
        //console.log(data);

        const info = data['csv'];
        
        for (const i in info) {
            //console.log(info[i]);
            const row = {
                id: i,
                semester: info[i]['semester'],
                course: info[i]['course'],
                project: info[i]['project'],
                organization: info[i]['organization'],
                team: info[i]['team'],
                role: info[i]['role'],
                fname: info[i]['fname'],
                lname: info[i]['lname'],
                name: info[i]['name'],
                email: info[i]['email'],
                buid: info[i]['buid'],
                github: info[i]['github'],
                status: info[i]['status'],
                project_github_url: info[i]['project_github_url'],
            };
            rows.push(row);
        }
        return rows;
    }

    async function _csv_projects() {
        const rows = [];
        const response = await _fetch(`${API_URL}/get_csv_projects`, { method: 'GET' });
        const data = await response.json();
        console.log(data);

        const info = data['csv_projects'];
        for (const i in info) {
            console.log(info[i]);
            const row = {
                id: i,
                project: info[i]['project'],
                semester: info[i]['semester'],
                project_github_url: info[i]['project_github_url'],
                status: info[i]['status'],
            };
            rows.push(row);
        }
        return rows;
    }

    async function _projects() {
        console.log('getting projects');    
        const rows = [];
        const response = await _fetch(`${API_URL}/get_projects`, { method: 'GET' });
        const data = await response.json();
        console.log(data);

        const info = data['projects'];
        for (const i in info) {
            console.log(info[i]);
            const row = {
                id: i,
                name: info[i]['name'],
                semester: info[i]['semester'],
                github_url: info[i]['github_url'],
            };
            rows.push(row);
        }
        return rows;
    }

    async function _git_repos() {
        const rows = [];
        const response = await _fetch(`${API_URL}/git/get_all_repos`, { method: 'GET' });
        const data = await response.json();
        console.log(data);

        const info = data['repos'];
        for (const i in info) {
            const row = {
                id: i,
                name: info[i][0],
                github_url: info[i][1]
            };
            rows.push(row);
        }
        return rows;
    }

    return (
        <FxnContext.Provider value={{ _info, _csv, _csv_projects, _projects, _git_repos }}>
            {children}
        </FxnContext.Provider>
    );
}

