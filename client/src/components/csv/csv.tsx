import { Box, Button } from "@mui/material";
import { DataGrid, GridColDef } from "@mui/x-data-grid";
import { useState } from "react";
import { API_URL } from "../../utils/uri";

export default function Csv({ csvloading, csvrows, callback }: any) {

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

    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any[]>([]);
    async function process() {
        setLoading(true);
        console.log('Processing ingested data into github');
        try {
            const response = await fetch(`${API_URL}/process`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
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
            <Box sx={{ height: 400, width: '100%', backgroundColor: "#242424", marginTop: 2, marginBottom: 2 }}>
                <DataGrid
                    rows={csvrows}
                    columns={csvcolumns}
                    initialState={{
                        pagination: {
                            paginationModel: {
                                pageSize: 5,
                            },
                        },
                    }}
                    pageSizeOptions={[5]}
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
            <Box sx={{ display: 'flex', gap: 2 }}>
                <Button variant='contained' color='primary' onClick={process}>
                    process ingested data into github (add students to repos)
                </Button>
            </Box>
            <Box sx={{ width: '100%', backgroundColor: "#242424", marginTop: 2 }}>
                <DataGrid
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