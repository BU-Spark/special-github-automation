import { Box, Button } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { useEffect, useState } from "react";
import { API_URL } from "../../utils/uri";
import { useAuth } from "../../context/auth";

export default function Csv({ csvloading, csvrows, csvprojectsrows, callback }: any) {

    const { _fetch } = useAuth();

    const csvcolumns: GridColDef[] = [
        { field: 'id', headerName: 'ID', flex: .25 },
        {
            field: 'semester',
            headerName: 'semester',
            editable: false,
            flex: .9,
        },
        {
            field: 'course',
            headerName: 'course',
            editable: false,
            flex: 1,
        },
        {
            field: 'project',
            headerName: 'project',
            editable: false,
            flex: 1,
        },
        {
            field: 'organization',
            headerName: 'organization',
            editable: false,
            flex: 1,
        },
        {
            field: 'team',
            headerName: 'team',
            editable: false,
            flex: 1,
        },
        {
            field: 'role',
            headerName: 'role',
            editable: false,
            flex: 1,
        },
        {
            field: 'fname',
            headerName: 'fname',
            editable: false,
            flex: 1,
        },
        {
            field: 'lname',
            headerName: 'lname',
            editable: false,
            flex: 1,
        },
        {
            field: 'name',
            headerName: 'name',
            editable: false,
            flex: 1,
        },
        {
            field: 'email',
            headerName: 'email',
            editable: false,
            flex: 1,
        },
        {
            field: 'buid',
            headerName: 'buid',
            editable: false,
            flex: 1,
        },
        {
            field: 'github',
            headerName: 'github',
            flex: 1,
        },
        {
            field: 'project_github_url',
            headerName: 'project github url',
            editable: false,
            flex: 1,
        },
        {
            field: 'status',
            headerName: 'status',
            editable: false,
            minWidth: 400,
            flex: 1,
        },
    ];

    const csvprojectscolumns: GridColDef[] = [
        { field: 'id', headerName: 'ID', flex: .25 },
        {
            field: 'semester',
            headerName: 'semester',
            editable: false,
            flex: .9,
        },
        {
            field: 'project',
            headerName: 'project',
            editable: false,
            flex: 1,
        },
        {
            field: 'project_github_url',
            headerName: 'project github url',
            editable: false,
            flex: 1,
        },
        {
            field: 'status',
            headerName: 'status',
            editable: false,
            minWidth: 400,
            flex: 1,
        },
    ];

    const [locked, setLocked] = useState(true);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);

    // useEffect to load in previous results
    useEffect(() => {
        console.log('Loading previous results');
        async function load() {
            try {
                const response = await _fetch(`${API_URL}/get_results`, {
                    method: 'GET',
                });
                const result = await response.json();
                console.log('Result:', result);
                if (response.ok) {
                    const logs = result['results'].map((r: any, index: number) => r['result']);
                    console.log('Loaded previous results:', logs);
                    setResults(logs);
                } else throw new Error('Error loading previous results');
            } catch (error: any) {
                console.error('Error loading previous results:', error);
                setResults(['Error loading previous results ' + error.toString()]);
            }
        }
        load();
    }, []);

    async function process() {
        setLoading(true);
        console.log('Processing ingested data into github');
        try {
            const response = await _fetch(`${API_URL}/process`, {
                method: 'POST',
            });
            const result = await response.json();
            console.log('Result:', result);
            if (response.ok) {
                const logs = result['status'];
                console.log('Processed successfully:', logs);
                setResults(logs);
                callback();
            } else throw new Error('Error processing data');
        } catch (error: any) {
            console.error('Error processing data:', error);
            setResults([
                'Error processing data ' + error.toString()
            ]);
        }
        setLoading(false);
    }

    return (
        <>
            <Box sx={{ width: '100%', backgroundColor: "#242424", marginTop: 2, marginBottom: 2 }}>
                <h4>the CSV table</h4>  
                <DataGrid
                    rowHeight={28}
                    rows={csvrows}
                    columns={csvcolumns}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 25,
                            },
                        },
                    }}
                    pageSizeOptions={[25]}
                    disableRowSelectionOnClick
                    loading={csvloading}
                    style={
                        {
                            backgroundColor: '#fff',
                            color: 'black',
                        }
                    }
                />
            </Box>
            <Box sx={{ width: '100%', backgroundColor: "#242424", marginTop: 2, marginBottom: 2 }}>
                <h4>the CSV_PROJECTS table</h4>  
                <DataGrid
                    rowHeight={28}
                    rows={csvprojectsrows}
                    columns={csvprojectscolumns}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 25,
                            },
                        },
                    }}
                    pageSizeOptions={[25]}
                    disableRowSelectionOnClick
                    loading={csvloading}
                    style={
                        {
                            backgroundColor: '#fff',
                            color: 'black',
                        }
                    }
                />
            </Box>
            <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
                <Button onClick={()=>setLocked(!locked)}>{locked ? '🔒' : '🔓'}</Button>
                <Button variant='contained' color={locked ? 'error' : 'primary'} onClick={
                    () => {
                        if (!locked) process();
                        else setResults(['Unlock the table to process data (use the lock emoji)']);
                    }
                }>
                    process ingested data into github (add students to repos)
                </Button>
            </Box>
            <Box sx={{ width: '100%', backgroundColor: "#242424", marginTop: 2 }}>
                <h4>Results</h4>
                <DataGrid
                    rowHeight={28}
                    rows={results.map((result, index) => ({ id: index, result }))}
                    columns={[
                        { field: 'id', headerName: 'ID', flex: .25 },
                        { field: 'result', headerName: 'Result', flex: 1 }
                    ]}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 5,
                            },
                        },
                    }}
                    pageSizeOptions={[5]}
                    disableRowSelectionOnClick
                    loading={loading}
                    style={{
                            minHeight: 140,
                            backgroundColor: '#fff',
                            color: 'black',
                        }}
                />
            </Box>
        </>
    )
}